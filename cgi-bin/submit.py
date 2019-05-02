#!/usr/local/adyen/python3/bin/python3
import json, os, sys, datetime, configparser
import time, logging

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
RETURN_URL = "{}/cgi-bin/submit.py?endpoint=result_page".format(LOCAL_ADDRESS)
THREEDS_RETURN_URL = "{}/cgi-bin/submit.py?endpoint=threeds2_result_page".format(LOCAL_ADDRESS)

######################
##		LOGGING		##
######################

class CustomLogger(logging.Logger):

	def debug(self, msg, *args, **kwargs):
		super().debug(self.format_msg(msg), *args, **kwargs)

	def info(self, msg, *args, **kwargs):
		super().info(self.format_msg(msg), *args, **kwargs)

	def warn(self, msg, *args, **kwargs):
		super().warn(self.format_msg(msg), *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		super().error(self.format_msg(msg), *args, **kwargs)

	def critical(self, msg, *args, **kwargs):
		super().critical(self.format_msg(msg), *args, **kwargs)

	def format_msg(self, msg):
		return "[{}] {}".format(self.log_date_time_string(), msg)

	def log_date_time_string(self):
		"""Return the current time formatted for logging."""
		monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
					'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
		now = time.time()
		year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
		s = "%02d/%3s/%04d %02d:%02d:%02d" % (
			day, monthname[month], year, hh, mm, ss)
		return s

logging.basicConfig(
	level=logging.DEBUG,
	format='%(asctime)s %(name)s:%(levelname)s %(message)s',
	datefmt='[%d/%m/%Y %X %Z]')
logger = logging.getLogger("CGI")

##############################
##		AUTHENTICATION		##
##############################
'''
load credentials from config.ini

see example_config.ini for file format
'''
config = configparser.ConfigParser()
config.read("config.ini")
credentials = config["credentials"]

MERCHANT_ACCOUNT = credentials["merchantAccount"]
WS_USERNAME = credentials["wsUser"]
WS_PASSWORD = credentials["wsPass"]
API_KEY = credentials["apiKey"]
HMAC_KEY = credentials["hmacKey"]
SKIN_CODE = credentials["skinCode"]

JSON_HEADER_OBJ = {
	"Content-Type": "application/json",
	"X-API-Key": API_KEY
}

##############################
##		NETWORK METHODS		##
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

	# logging
	logger.info("")
	logger.info("sending outgoing request to {}".format(url))
	logger.info("request data: {}".format(data))

	# create request object
	request = Request(url, formatted_data, headers)

	# handle response from server
	try:
		response = urlopen(request)
		result = response.read()

		# see if the response is JSON
		if "application/json" in response.getheader("content-type"):
			return json.loads(result.decode("utf8"))
		else:
			return result
	except HTTPError as e:
		return "{}".format(e).encode("utf8")
	except:
		return "error sending request".encode("utf8")

# respond with result
def send_response(result, content_type="text/html", skipHeaders=False):
	if not skipHeaders:
		print("Content-type:{}\r\n".format(content_type), end="")
		print("\r\n", end="")

	if type(result) is bytes:
		formatted_result = "{}\r\n".format(result.decode("utf8"))
	elif type(result) is str:
		formatted_result = "{}\r\n".format(result)
	elif type(result) is dict:
		formatted_result = "{}\r\n".format(json.dumps(result))
	else:
		logger.error("Invalid data type in send_response")
		logger.error(type(result))
		return

	logger.info("")
	logger.info("responding to client with data: {}".format(formatted_result))
	print(formatted_result, end="")

# respond with raw data
def send_debug(data, content_type="text/plain", duplicate=False):
	if not duplicate:
		print("Content-type:{}\r\n".format(content_type))
	print(data)

	if content_type == "text/html":
		print("<br><br>")
	else:
		print("\r\n\r\n")

# respond with redirect
def redirect(location):
	print("Content-Type: text/html")
	print("Location: {}".format(location))
	print("\r\n")

	html = '''
		<html>
			<head>
				<meta http-equiv="refresh" content="0;{location}" />
			</head>
			<body>
				Redirecting...
			</body>
		</html>
	'''.format(location=location)
	print(html)

# convert FieldStorage to dict
# NOTE this can only be called once per request
def get_dict_from_fieldstorage():
	content_length = int(os.environ["CONTENT_LENGTH"])
	raw_request = sys.stdin.read(content_length)
	form = parse_qs(raw_request)

	result = {}
	for key in form.keys():
		result[key] = form[key]

	return result

# create basic auth header
def create_basic_auth(user, WS_PASSWORD):
	combined_string = "{}:{}".format(user, WS_PASSWORD)
	return base64.b64encode(combined_string.encode("utf8")).decode("utf8")

##############################
##		FORMAT HELPERS		##
##############################

# indent fields in data object
def indent_field(data, parent, target):
	if parent not in data.keys():
		data[parent] = {}

	data[parent][target] = data[target]
	del data[target]

# reformat amount data into indented object
def reformat_amount(data):
	indent_field(data, "amount", "value")
	indent_field(data, "amount", "currency")

# reformat card data into indented object for PAL API
def reformat_card(data):
	indent_field(data, "card", "number")
	indent_field(data, "card", "expiryMonth")
	indent_field(data, "card", "expiryYear")
	indent_field(data, "card", "holderName")
	indent_field(data, "card", "cvc")

# reformat card data into indented object for Checkout API
def reformat_card_checkout(data, encrypted=True):
	if encrypted:
		indent_field(data, "paymentMethod", "encryptedCardNumber")
		indent_field(data, "paymentMethod", "encryptedExpiryMonth")
		indent_field(data, "paymentMethod", "encryptedExpiryYear")
		indent_field(data, "paymentMethod", "holderName")
		indent_field(data, "paymentMethod", "encryptedSecurityCode")
		data["paymentMethod"]["type"] = "scheme"

		# change spaces back to plus signs
		data["paymentMethod"]["encryptedCardNumber"] = data["paymentMethod"]["encryptedCardNumber"].replace(" ", "+")  # noqa: E501
		data["paymentMethod"]["encryptedExpiryMonth"] = data["paymentMethod"]["encryptedExpiryMonth"].replace(" ", "+")  # noqa: E501
		data["paymentMethod"]["encryptedExpiryYear"] = data["paymentMethod"]["encryptedExpiryYear"].replace(" ", "+")  # noqa: E501
		data["paymentMethod"]["holderName"] = data["paymentMethod"]["holderName"].replace(" ", "+")  # noqa: E501
		data["paymentMethod"]["encryptedSecurityCode"] = data["paymentMethod"]["encryptedSecurityCode"].replace(" ", "+")  # noqa: E501
	else:
		indent_field(data, "paymentMethod", "number")
		indent_field(data, "paymentMethod", "expiryMonth")
		indent_field(data, "paymentMethod", "expiryYear")
		indent_field(data, "paymentMethod", "holderName")
		indent_field(data, "paymentMethod", "cvc")
		data["paymentMethod"]["type"] = "scheme"

##############################
##		CHECKOUT SDK		##
##############################

# javascript checkout SDK
def checkout_setup(data):

	# URL and headers
	url = "https://checkout-test.adyen.com/v32/paymentSession"
	headers = JSON_HEADER_OBJ

	# static fields
	data["sdkVersion"] = "1.3.0"

	data["html"] = "true"
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = RETURN_URL
	data["reference"] = "Localhost checkout"

	# data["shopperName"] = {}
	# data["shopperName"]["firstName"] = "Colin"
	# data["shopperName"]["lastName"] = "Rood"
	# data["shopperName"]["gender"] = "MALE"

	# data["configuration"] = {}
	# data["configuration"]["cardHolderNameRequired"] = "true"
	# data["configuration"]["avs"] = {}
	# data["configuration"]["avs"]["enabled"] = "automatic"
	# data["configuration"]["avs"]["addressEditable"] = "true"

	# data["billingAddress"] = {}
	# data["billingAddress"]["city"] = "Springfield"
	# data["billingAddress"]["country"] = "US"
	# data["billingAddress"]["houseNumberOrName"] = "1234"
	# data["billingAddress"]["postalCode"] = "74629"
	# data["billingAddress"]["stateOrProvince"] = "OR"
	# data["billingAddress"]["street"] = "Main"

	# data["additionalData"] = {}
	# data["additionalData"]["enhancedSchemeData.totalTaxAmount"] = "100"

	# data["allowedPaymentMethods"] = ["scheme"]
	# data["blockedPaymentMethods"] = ["visa"]

	# data["metadata"] = {
	# 	"key1": "value1",
	# 	"key2": "value2"
	# }

	data["enableRecurring"] = "true"
	data["enableOneClick"] = "false"

	reformat_amount(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

# javascript checkout SDK
def checkout_verify(data):

	# URL and headers
	url = "https://checkout-test.adyen.com/v32/payments/result"
	headers = JSON_HEADER_OBJ

	# fix overzealous URL encoding
	data["payload"] = data["payload"].replace(" ", "+")

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

##############################
##		CHECKOUT API		##
##############################

# paymentMethods endpoint
def checkout_payment_methods(data):

	# URL and headers
	url = "https://checkout-test.adyen.com/v41/paymentMethods"
	headers = JSON_HEADER_OBJ

	result = send_request(url, data, headers)
	send_response(result, "application/json")

# /payments endpoint (equivalent to /authorise for PAL)
def checkout_payments_api(data):

	# URL and headers
	url = "https://checkout-test.adyen.com/v41/payments"
	headers = JSON_HEADER_OBJ

	reformat_amount(data)
	reformat_card_checkout(data)

	result = send_request(url, data, headers)
	send_response(result, "application/json")

##############################
##		HMAC SIGNATURE		##
##############################

# escape un-allowed characters
def escape(val):
	if isinstance(val, int):
		return val
	if val is None:
		return ""
	return val.replace('\\', '\\\\').replace(':', '\\:')

# calculate signature
def generate_HMAC(pairs, key):

	# sort and escape data
	sorted_pairs = OrderedDict(sorted(pairs.items(), key=lambda t: t[0]))
	escaped_pairs = OrderedDict(map(
		lambda t: (t[0], escape(t[1])), sorted_pairs.items()))
	signing_string = ":".join(
		escaped_pairs.keys()) + ":" + ":".join(
		escaped_pairs.values())

	# generate key
	binary_hmac_key = binascii.a2b_hex(key)
	binary_hmac = hmac.new(
		binary_hmac_key,
		signing_string.encode("utf8"),
		hashlib.sha256)
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
		send_response("raw:\t\t{}\nencoded:\t{}".
			format(signature, urlencode({"merchantSig": signature})), "text/plain")
		send_response(urlencode(data), "text/plain", True)
	else:
		return signature

######################################
##		CLIENT SIDE ENCRYPTION		##
######################################

# get encrypted card data blob and send to Adyen
def CSE(data):

	# set request outline
	url = "https://pal-test.adyen.com/pal/servlet/Payment/authorise"
	headers = JSON_HEADER_OBJ
	data["reference"] = "Localhost CSE"

	# move value and currency into indented object
	reformat_amount(data)

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

	# server side fields
	data["sessionValidity"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"
	data["shipBeforeData"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"
	data["resURL"] = "http://localhost:8000/cgi-bin/submit.py?endpoint=result_page"

	# account specific fields
	data["skinCode"] = SKIN_CODE
	data["hmacKey"] = HMAC_KEY

	data["additionalData.enhancedSchemeData.totalTaxAmount"] = "190"
	data["additionalData.enhancedSchemeData.customerReference"] = "12345"

	# seveneleven fields
	data["shopper.firstName"] = "Test"
	data["shopper.lastName"] = "Shopper"
	data["shopper.telephoneNumber"] = "123456789"

	# generate HMAC signature
	data["merchantSig"] = HMAC_signature(data, False).decode("utf8")

	# redirect to HPP page in new window
	send_response("Redirected in another window\n\nRequest:\n{}".
		format("{}?{}".
		format(url, urlencode(data))), "text/plain")
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
	headers = JSON_HEADER_OBJ

	# account specific fields
	data["skinCode"] = SKIN_CODE
	data["hmacKey"] = HMAC_KEY

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

	# session validity
	data["sessionValidity"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"

	# account specific fields
	data["skinCode"] = SKIN_CODE
	data["hmacKey"] = HMAC_KEY

	data["orderData"] = "<h1>Order Data!</h1>"

	# populate empty but apparently mandatory fields
	data["allowedMethods"] = ""
	data["blockedMethods"] = ""
	if "issuerId" not in data.keys():
		data["issuerId"] = ""

	data["resURL"] = "http://localhost:8000/cgi-bin/submit.py?endpoint=result_page"

	# open invoice fields for Klarna, etc
	if ("klarna" in data["brandCode"]
			or "afterpay" in data["brandCode"]
			or "ratepay" in data["brandCode"]):

		data["openinvoicedata.line1.currencyCode"] = data["currencyCode"]
		data["openinvoicedata.line1.description"] = "openinvoice description"
		data["openinvoicedata.line1.itemAmount"] = data["paymentAmount"]
		data["openinvoicedata.line1.itemVatAmount"] = data["paymentAmount"]
		data["openinvoicedata.line1.itemVatPercentage"] = "7"
		data["openinvoicedata.line1.numberOfItems"] = "1"
		data["openinvoicedata.line1.vatCategory"] = "Low"
		data["openinvoicedata.numberOfLines"] = "1"

		data["shopperEmail"] = "test@email.com"
		data["shopper.firstName"] = "Colin"
		data["shopper.lastName"] = "Rood"
		data["shopper.gender"] = "MALE"
		data["shopper.telephoneNumber"] = "5555555555"
		data["shopper.socialSecurityNumber"] = "1111"

		data["shopper.dateOfBirthDayOfMonth"] = "11"
		data["shopper.dateOfBirthMonth"] = "2"
		data["shopper.dateOfBirthYear"] = "1983"

		data["billingAddress.country"] = data["countryCode"]
		data["billingAddress.city"] = "Anytown"
		data["billingAddress.houseNumberOrName"] = "123"
		data["billingAddress.street"] = "Main St"
		data["billingAddress.postalCode"] = "12345"

		data["shopperType"] = "1"
		data["billingAddressType"] = "1"

	# generate HMAC signature
	data["merchantSig"] = HMAC_signature(data, False).decode("utf8")

	# send to Adyen and display result
	# result = send_request("{}?{}".format(url, urlencode(data)), {}, headers)
	# send_response(result, "text/html")

	# redirect to HPP
	send_response("Redirected in another window\n\nRequest:\n{}".
		format("{}?{}".
		format(url, urlencode(data))), "text/plain")
	webbrowser.open("{}?{}".format(url, urlencode(data)))

##############################
##		SECURED FIELDS		##
##############################

# adyen-hosted iframes for card data entry
def secured_fields_setup(data):

	# request info
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/v30/setup"
	headers = JSON_HEADER_OBJ

	# static fields
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = RETURN_URL

	data["additionalData"] = {}
	data["additionalData"]["executeThreeD"] = "True"

	# move amount data into parent object
	reformat_amount(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

# send encrypted card data to Adyen
def secured_fields_submit(data):

	# request info
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/v32/payments"
	headers = JSON_HEADER_OBJ

	# static fields
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = RETURN_URL

	# move amount data into parent object
	reformat_amount(data)

	# move card data into paymentMethod object
	reformat_card_checkout(data, encrypted=True)

	send_debug(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json", True)

##########################
##		3D Secure 1		##
##########################

# API call with 3d Secure redirect
def threeds1(data):

	# request info
	url = "https://checkout-test.adyen.com/v40/payments"
	headers = JSON_HEADER_OBJ

	# static fields
	data["returnUrl"] = "{}/cgi-bin/submit.py?endpoint=threeds1_notification_url".format(LOCAL_ADDRESS)  # noqa: E501
	data["additionalData"] = {
		"executeThreeD": "true"
	}

	# standalone mode
	data["threeDS2RequestData"] = {
		"authenticationOnly": "true"
	}

	# move amount data into parent object
	reformat_amount(data)

	# move card data into parent object
	reformat_card_checkout(data, encrypted=False)

	# move userAgent into browserInfo object
	indent_field(data, "browserInfo", "userAgent")
	data["browserInfo"]["acceptheader"] = "text/html"

	# get response from Adyen
	payments_result = send_request(url, data, headers)

	send_response(payments_result, "application/json")

# handler for callback from issuing bank
def threeds1_notification_url(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/authorise3d"
	headers = JSON_HEADER_OBJ

	logger.debug(data)

	# reformat request to match required fields
	request_data = {}
	request_data["merchantAccount"] = MERCHANT_ACCOUNT
	request_data["md"] = data["MD"][0]
	request_data["paResponse"] = data["PaRes"][0]

	# standalone mode
	request_data["threeDS2RequestData"] = {
		"authenticationOnly": "true"
	}

	# get response from Adyen
	payments_result = send_request(url, request_data, headers)

	send_response(payments_result, "application/json")

######################################
##		3D SECURE 2.0 BASIC FLOW	##
######################################

# API call with 3d Secure 2.0
# part 1
def threeds2_part1(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise"
	headers = JSON_HEADER_OBJ

	# move amount data into parent object
	reformat_amount(data)

	# move card data into parent object
	reformat_card(data)

	# move userAgent into browserInfo object
	indent_field(data, "browserInfo", "userAgent")
	data["browserInfo"]["acceptHeader"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"  # noqa: E501
	data["browserInfo"]["language"] = "EN-GB"
	data["browserInfo"]["colorDepth"] = 32
	data["browserInfo"]["screenHeight"] = 1200
	data["browserInfo"]["screenWidth"] = 600
	data["browserInfo"]["timeZoneOffset"] = 1
	data["browserInfo"]["javaEnabled"] = "true"

	# add threeDS2RequestData
	data["threeDS2RequestData"] = {}
	data["threeDS2RequestData"]["deviceChannel"] = "browser"
	data["threeDS2RequestData"]["notificationURL"] = LOCAL_ADDRESS + "/cgi-bin/submit.py?endpoint=threeds2_result_page"  # noqa: E501
	indent_field(data, "threeDS2RequestData", "authenticationOnly")

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = data
	response["response"] = result
	response["endpoint"] = url
	send_response(response, "application/json")

# API call with 3d Secure 2.0
# part 2
def threeds2_part2(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise3ds2"
	headers = JSON_HEADER_OBJ

	data["merchantAccount"] = MERCHANT_ACCOUNT
	indent_field(data, "threeDS2RequestData", "threeDSCompInd")

	# send request to adyen
	result = send_request(url, data, headers)

	# send request and response to client
	response = {}
	response["request"] = data
	response["response"] = result
	response["endpoint"] = url
	send_response(response, "application/json")

def threeds2_auth_via_token(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise3ds2"
	headers = JSON_HEADER_OBJ

	data["merchantAccount"] = MERCHANT_ACCOUNT
	indent_field(data, "threeDS2Result", "transStatus")

	# send request to adyen
	result = send_request(url, data, headers)

	# send request and response to client
	response = {}
	response["request"] = data
	response["response"] = result
	response["endpoint"] = url
	send_response(response, "application/json")

##########################################
##		3D SECURE 2.0 ADVANCED FLOW 	##
##########################################
def threeds2_adv_initial_auth(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise"
	headers = JSON_HEADER_OBJ

	# move amount data into parent object
	reformat_amount(data)

	# move card data into parent object
	reformat_card(data)

	# move userAgent into browserInfo object
	indent_field(data, "browserInfo", "userAgent")
	data["browserInfo"]["acceptHeader"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"  # noqa: E501
	data["browserInfo"]["language"] = "EN-GB"
	data["browserInfo"]["colorDepth"] = 32
	data["browserInfo"]["screenHeight"] = 1200
	data["browserInfo"]["screenWidth"] = 600
	data["browserInfo"]["timeZoneOffset"] = 1
	data["browserInfo"]["javaEnabled"] = "true"

	# add threeDS2RequestData
	indent_field(data, "threeDS2RequestData", "threeDSServerTransID")
	indent_field(data, "threeDS2RequestData", "threeDSCompInd")
	indent_field(data, "threeDS2RequestData", "authenticationOnly")
	data["threeDS2RequestData"]["deviceChannel"] = "browser"
	data["threeDS2RequestData"]["notificationURL"] = LOCAL_ADDRESS + "/cgi-bin/submit.py?endpoint=threeds2_result_page"  # noqa: E501

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = data
	response["response"] = result
	response["endpoint"] = url

	# logging.debug(response)
	send_response(response, "application/json")

def threeds2_result_page(data):

	# echo cres value
	logger.info(data)

	if "cres" in data.keys():
		# decode data and append as GET params to redirect
		logger.info("Redirecting")
		cres = json.loads(base64.b64decode(data["cres"][0]).decode())
		get_params = ""
		for key in cres.keys():
			get_params = "{get_params}&{key}={value}".format(get_params=get_params, key=key, value=cres[key])
		redirect_url = THREEDS_RETURN_URL + get_params
		redirect(redirect_url)
	else:
		send_debug(json.dumps(data))

def threeds2_adv_authorise3ds2(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise3ds2"
	headers = JSON_HEADER_OBJ

	# hardcoding successful challenge for now
	data["threeDS2Result"] = {}
	data["threeDS2Result"]["transStatus"] = "Y"

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	response["endpoint"] = url
	send_response(str(response), "text/plain")

def threeds2_adv_retrieve3ds2Result(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/retrieve3ds2Result"
	headers = JSON_HEADER_OBJ

	data["merchantAccount"] = MERCHANT_ACCOUNT

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = data
	response["response"] = result
	response["endpoint"] = url
	send_response(response, "application/json")

def threeds2_adv_acquirerAgnosticAuth(data):
	send_debug(data)

##########################
##		RESULT PAGE		##
##########################

# landing page for complete transactions
def result_page(data):

	# send POST params to logger
	logger.info(data)

	# remove merchant account from params since it was added by server
	del data["merchantAccount"]

	# echo URL params to client
	send_debug("Response from Adyen:")
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
	"checkout_verify": checkout_verify,
	"checkout_payment_methods": checkout_payment_methods,
	"checkout_payments_api": checkout_payments_api,
	"hmac_signature": HMAC_signature,
	"CSE": CSE,
	"directory_lookup": directory_lookup,
	"secured_fields_setup": secured_fields_setup,
	"skip_details": skip_details,
	"threeds1": threeds1,
	"threeds1_notification_url": threeds1_notification_url,
	"threeds2_part1": threeds2_part1,
	"threeds2_part2": threeds2_part2,
	"threeds2_auth_via_token": threeds2_auth_via_token,
	"threeds2_adv_initial_auth": threeds2_adv_initial_auth,
	"threeds2_adv_authorise3ds2": threeds2_adv_authorise3ds2,
	"threeds2_adv_retrieve3ds2Result": threeds2_adv_retrieve3ds2Result,
	"threeds2_adv_acquirerAgnosticAuth": threeds2_adv_acquirerAgnosticAuth,
	"threeds2_result_page": threeds2_result_page,
	"result_page": result_page,
	"secured_fields_submit": secured_fields_submit,
}

try:
	# parse endpoint from request
	endpoint = data["endpoint"]
	del data["endpoint"]

except:
	logger.critical("endpoint value missing in request data")
	send_debug("endpoint value missing in request data:")
	send_debug(data, duplicate=True)
	exit(1)

# note incoming request
logger.info("")
logger.info("------- NEW REQUEST -------")

# get data from POST fields
if os.environ["REQUEST_METHOD"] == "POST":
	post_data = get_dict_from_fieldstorage()

	# log request data
	logger.info("receiving incoming request to {}".format(endpoint))
	logger.info("incoming URL params: {}".format(data))
	logger.info("incoming POST data: {}".format(post_data))

	# combine URL and POST params
	data.update(post_data)

# add merchantAccount to data
data["merchantAccount"] = MERCHANT_ACCOUNT

# make sure endpoint is valid
if endpoint not in router.keys():
	logger.critical("method not found: {}".format(endpoint))
	send_debug("SERVER ERROR")
	send_debug("Method not found: \n{}".format(endpoint), duplicate=True)
	send_debug("\n{}".format(data), duplicate=True)

# send to proper method
else:
	router[endpoint](data)
