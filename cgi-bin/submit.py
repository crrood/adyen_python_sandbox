#!/Users/colinr/miniconda3/bin/python3

# general utilities
import json, os, datetime

# HMAC
import base64, binascii, hmac, hashlib
from collections import OrderedDict

# HTTP parsing
from urllib.parse import parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# browser control
import webbrowser

##################################
##		HARDCODED VALUES		##
##################################

LOCAL_ADDRESS = "http://localhost:8000"
READ_CREDENTIALS_FROM_FILE = False

##############################
##		AUTHENTICATION		##
##############################

# NOTE
# there are two options for how to store authentication credentials:
# the more secure is to hardcode them here in the server
# for ease of committing to github I have also included the option to read from a local file
# production environments should always use hardcoded values

# hardcoded authentication values
WS_USERNAME = "ws_306326@Company.AdyenTechSupport"
WS_PASSWORD = "7UuQQEmR=2Qq9ByCt4<3r2zq^"
CHECKOUT_API_KEY = "AQEyhmfxLIrIaBdEw0m/n3Q5qf3VaY9UCJ1+XWZe9W27jmlZilETQsVk1ULvYgY9gREbDhYQwV1bDb7kfNy1WIxIIkxgBw==-CekguSzLVE/iCTVQQWGILQK0x8Lo88FEQ/VHTZuAoP0=-dqZewkA79CPfNISf"
HMAC_KEY = "BE1C271E9CD9D2F6611D2C7064FE9EE314DA58539195E92BF5AC706209A514DB" # may be overwritten by client

# authentication read from local file
if READ_CREDENTIALS_FROM_FILE:
	with open("api_credentials.txt") as f:
		 WS_USERNAME = f.readline().strip()
		 WS_PASSWORD = f.readline().strip()
		 CHECKOUT_API_KEY = f.readline().strip()
		 HMAC_KEY = f.readline().strip() # may be overwritten by client

##############################
##		HELPER METHODS		##
##############################

# send request to server and return bytecode response
def send_request(url, data, headers, data_type="json"):

	# encode data
	if data_type == "formdata":
		formatted_data = urlencode(data).encode("utf8")
	elif data_type == "json":
		formatted_data = json.dumps(data).encode("utf8")
	else:
		formatted_data = data

	# create request object
	request = Request(url, formatted_data, headers)

	# handle errors in response from server
	try:
		return urlopen(request).read()
	except HTTPError as e:
		return "{}".format(e).encode("utf8")
	except:
		return "error sending request".encode("utf8")

# respond with result
def send_response(result, content_type="text/html", skipHeaders=False):
	if not skipHeaders:
		print("Content-type:{}\r\n".format(content_type), end="")
		print("Content-length:{}\r\n".format(len(result)), end="")
		print("\r\n", end="")

	if type(result) is bytes:
		print("{}\r\n".format(result.decode("utf8")), end="")
	elif type(result) is str:
		print("{}\r\n".format(result), end="")

# respond with raw data
def send_debug(data, content_type="text/plain", duplicate=False):
	if not duplicate:
		print("Content-type:{}\r\n".format(content_type))
	print(data)
	
	if content_type == "text/html":
		print("<br><br>")
	else:
		print("\r\n\r\n")

# reformat amount data into indented object for Adyen
def reformat_amount(data):
	data["amount"] = {}
	data["amount"]["value"] = data["value"]
	data["amount"]["currency"] = data["currency"]
	del data["value"]
	del data["currency"]

	return data

# create basic auth header
def create_basic_auth(user, WS_PASSWORD):
	combined_string = "{}:{}".format(user, WS_PASSWORD)
	return base64.b64encode(combined_string.encode("utf8")).decode("utf8")


##############################
##		CHECKOUT API		##
##############################

# javascript checkout SDK
def checkout_setup(data):

	# URL and headers
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/setup"
	headers = {
		"Content-Type": "application/json",
		"x-api-key": CHECKOUT_API_KEY
	}

	# static fields
	data["html"] = "true"
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = LOCAL_ADDRESS
	data["reference"] = "Localhost checkout"

	data = reformat_amount(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

##############################
##		HMAC SIGNATURE		##
##############################

# escape un-allowed characters
def escape(val):
	if isinstance(val,int):
		return val
	if val is None:
		return ""
	return val.replace('\\', '\\\\').replace(':', '\\:')

# calculate signature
def generate_HMAC(pairs, key):

	# sort and escape data
	sorted_pairs = OrderedDict(sorted(pairs.items(), key=lambda t: t[0]))
	escaped_pairs = OrderedDict(map(lambda t: (t[0], escape(t[1])), sorted_pairs.items()))
	signing_string = ":".join(escaped_pairs.keys()) + ":" + ":".join(escaped_pairs.values())

	# generate key
	binary_hmac_key = binascii.a2b_hex(key)
	binary_hmac = hmac.new(binary_hmac_key, signing_string.encode("utf8"), hashlib.sha256)
	signature = base64.b64encode(binary_hmac.digest())

	return signature

# pull key from raw data and send signature to HTTP response
def HMAC_signature(data, respond=True):

	# get HMAC key
	try:
		# move key from data to own variable
		key = data["hmacKey"]
		del data["hmacKey"]
	except:
		# use hardcoded key if not found in data
		key = HMAC_KEY

	if "submit" in data.keys():
		del data["submit"]

	# calculate signature
	signature = generate_HMAC(data, key)

	# send response
	if respond:
		send_response("raw:\t\t{}\nencoded:\t{}".format(signature, urlencode({ "merchantSig": signature })), "text/plain")
	else:
		return signature

######################################
##		CLIENT SIDE ENCRYPTION		##
######################################

# get encrypted card data blob and send to Adyen
def CSE(data):

	# set request outline
	url = "https://pal-test.adyen.com/pal/servlet/Payment/authorise"
	headers = {
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD)),
		"Content-Type": "application/json"
	}
	data["reference"] = "Localhost CSE"

	# move value and currency into indented object
	data = reformat_amount(data)

	# check if recurring
	if "shopperReference" in data.keys():
		data["recurring"] = {
			"contract": "ONECLICK"
		}

	# move encrypted card data into additionalData container
	data["additionalData"] = {}
	data["additionalData"]["card.encrypted.json"] = data["encryptedData"]
	del data["encryptedData"]

	# display request object for debugging
	send_debug(data)

	# send to Adyen and display result
	result = send_request(url, data, headers)
	send_response(result, skipHeaders=True)

######################################
##		HOSTED PAYMENT PAGES		##
######################################

# get setup data from client and send to Adyen
def HPP(data):

	# craft request to Adyen server
	url = "https://test.adyen.com/hpp/pay.shtml"
	headers = {
		"Content-Type": "application/x-www-form-urlencoded"
	}

	# server side fields
	data["sessionValidity"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"
	data["shipBeforeData"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"
	data["resURL"] = "http://localhost:8000/cgi-bin/submit.py?endpoint=result_page"

	# generate HMAC signature
	data["merchantSig"] = HMAC_signature(data, False).decode("utf8")
	
	# redirect to HPP page in new window
	send_response("Redirected in another window\n\nRequest:\n{}".format("{}?{}".format(url, urlencode(data))), "text/plain")
	webbrowser.open_new("{}?{}".format(url, urlencode(data)))

##################################
##		DIRECTORY LOOKUP		##
##################################

# get parameters and return available payment methods
def directory_lookup(data):

	# get API version
	if data["version"] == "V2":
		url = "https://test.adyen.com/hpp/directory/v2.shtml"
	else:
		url = "https://test.adyen.com/hpp/directory.shtml"
	del data["version"]
	
	# set request outline
	headers = {
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD)),
		"Content-Type": "application/json"
	}

	# generate HMAC signature
	data["merchantSig"] = HMAC_signature(data, False).decode("utf8")

	# display request object for debugging
	send_debug(urlencode(data))

	# send to Adyen and display result
	result = send_request("{}?{}".format(url, urlencode(data)), {}, headers)
	send_response(result, skipHeaders=True)

##############################
##		SKIP DETAILS		##
##############################

# bypass the HPP and go straight to the specified payment method
def skip_details(data):

	# skipDetails endpoint
	url = "https://test.adyen.com/hpp/skipDetails.shtml"
	
	# set request outline
	headers = {
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD)),
		"Content-Type": "application/json"
	}

	# session validity
	data["sessionValidity"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"

	# populate empty but apparently mandatory fields
	data["allowedMethods"] = ""
	data["blockedMethods"] = ""
	if "issuerId" not in data.keys():
		data["issuerId"] = ""

	data["resURL"] = "http://localhost:8000/cgi-bin/submit.py?endpoint=result_page"

	# generate HMAC signature
	data["merchantSig"] = HMAC_signature(data, False).decode("utf8")

	# send to Adyen and display result
	# result = send_request("{}?{}".format(url, urlencode(data)), {}, headers)
	# send_response(result, "text/html")

	# redirect to HPP
	send_response("Redirected in another window\n\nRequest:\n{}".format("{}?{}".format(url, urlencode(data))), "text/plain")
	webbrowser.open("{}?{}".format(url, urlencode(data)))

##############################
##		SECURED FIELDS		##
##############################

# adyen-hosted iframes for card data entry
def secured_fields_setup(data):

	# request info
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/v32/setup"
	headers = {
		"Content-Type": "application/json",
		"X-API-Key": CHECKOUT_API_KEY
	}

	# static fields
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = LOCAL_ADDRESS

	# move amount data into parent object
	data = reformat_amount(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

##########################
##		RESULT PAGE		##
##########################

# landing page for complete transactions
def result_page(data):
	send_debug("Response from HPP:")
	send_debug(data, duplicate=True)

##############################
##		ROUTER METHOD		##
##############################

# parse payment data from URL params 
request_data = parse_qs(os.environ["QUERY_STRING"])
data = {}
for param in request_data.keys():
	data[param] = request_data[param][0]

# map data["endpoint"] value to server methods
router = {
	"HPP": HPP,
	"checkout_setup": checkout_setup,
	"hmac_signature": HMAC_signature,
	"CSE": CSE,
	"directory_lookup": directory_lookup,
	"secured_fields_setup": secured_fields_setup,
	"skip_details": skip_details,
	"result_page": result_page
}

try:
	# parse endpoing from request
	endpoint = data["endpoint"]
	del data["endpoint"]

except:
	send_debug("endpoint value missing in request data:")
	send_debug(data, duplicate=True)
	exit(1)

try:
	# send to proper method
	router[endpoint](data)
	
except KeyError as e:
	# in case of errors echo data back to client
	send_debug("Method not found: \n{}".format(e))
	send_debug("\n{}".format(data), duplicate=True)
