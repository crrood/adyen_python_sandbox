#!/usr/local/adyen/python3/bin/python3
import json, os, datetime, configparser
import time, logging

# HMAC
import base64, binascii, hmac, hashlib
from collections import OrderedDict

# HTTP parsing
import cgi
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
		monthname = [None,
		             'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
		             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
		now = time.time()
		year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
		s = "%02d/%3s/%04d %02d:%02d:%02d" % (
				day, monthname[month], year, hh, mm, ss)
		return s

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s:%(levelname)s %(message)s', datefmt='[%d/%m/%Y %X %Z]')
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

	# logging
	logging.info("")
	logging.info("sending outgoing request to {}".format(url))
	logging.info("request data: {}".format(data))

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
		formatted_result = "{}\r\n".format(result.decode("utf8"))
	elif type(result) is str:
		formatted_result = "{}\r\n".format(result)
	else:
		print("Invalid data type in send_response")

	logging.info("")
	logging.info("responding to client with data: {}".format(formatted_result))
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

# indent fields in data object
def indent_field(data, parent, target):
	if not parent in data.keys():
		data[parent] = {}
	
	data[parent][target] = data[target]
	del data[target]

# reformat amount data into indented object for Adyen
def reformat_amount(data):
	indent_field(data, "amount", "value")
	indent_field(data, "amount", "currency")

# reformat card data into indented object for Adyen
def reformat_card(data):
	indent_field(data, "card", "number")
	indent_field(data, "card", "expiryMonth")
	indent_field(data, "card", "expiryYear")
	indent_field(data, "card", "holderName")
	indent_field(data, "card", "cvc")

def reformat_card_checkout(data, encrypted=True):
	if encrypted:
		indent_field(data, "paymentMethod", "encryptedCardNumber")
		indent_field(data, "paymentMethod", "encryptedExpiryMonth")
		indent_field(data, "paymentMethod", "encryptedExpiryYear")
		indent_field(data, "paymentMethod", "holderName")
		indent_field(data, "paymentMethod", "encryptedSecurityCode")
		data["paymentMethod"]["type"] = "scheme"

		# change spaces back to plus signs
		data["paymentMethod"]["encryptedCardNumber"] = data["paymentMethod"]["encryptedCardNumber"].replace(" ", "+")
		data["paymentMethod"]["encryptedExpiryMonth"] = data["paymentMethod"]["encryptedExpiryMonth"].replace(" ", "+")
		data["paymentMethod"]["encryptedExpiryYear"] = data["paymentMethod"]["encryptedExpiryYear"].replace(" ", "+")
		data["paymentMethod"]["holderName"] = data["paymentMethod"]["holderName"].replace(" ", "+")
		data["paymentMethod"]["encryptedSecurityCode"] = data["paymentMethod"]["encryptedSecurityCode"].replace(" ", "+")
	else:
		indent_field(data, "paymentMethod", "number")
		indent_field(data, "paymentMethod", "expiryMonth")
		indent_field(data, "paymentMethod", "expiryYear")
		indent_field(data, "paymentMethod", "holderName")
		indent_field(data, "paymentMethod", "cvc")
		data["paymentMethod"]["type"] = "scheme"

# create basic auth header
def create_basic_auth(user, WS_PASSWORD):
	combined_string = "{}:{}".format(user, WS_PASSWORD)
	return base64.b64encode(combined_string.encode("utf8")).decode("utf8")

# convert FieldStorage to dict
# NOTE this can only be called once per request
def get_dict_from_fieldstorage():
	form = cgi.FieldStorage()
	result = {}

	for key in form.keys():
		result[key] = form.getvalue(key)

	return result

##############################
##		CHECKOUT API		##
##############################

# javascript checkout SDK
def checkout_setup(data):

	# URL and headers
	url = "https://checkout-test.adyen.com/v32/paymentSession"
	headers = {
		"Content-Type": "application/json",
		"x-api-key": API_KEY
	}

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
	headers = {
		"Content-Type": "application/json",
		"x-api-key": API_KEY
	}

	# fix overzealous URL encoding
	data["payload"] = data["payload"].replace(" ", "+")

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
	headers = {
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD)),
		"Content-Type": "application/json"
	}
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
	headers = {
		"Content-Type": "application/x-www-form-urlencoded"
	}

	# server side fields
	data["sessionValidity"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"
	data["shipBeforeData"] = datetime.datetime.now().isoformat().split(".")[0] + "-11:00"
	# data["resURL"] = "http://localhost:8000/cgi-bin/submit.py?endpoint=result_page"
	data["resURL"] = "http://localhost:8000/cgi-bin/submit.py?endpoint=result_page"

	# account specific fields
	data["skinCode"] = SKIN_CODE
	data["hmacKey"] = HMAC_KEY

	data["additionalData.enhancedSchemeData.totalTaxAmount"] = "190"
	data["additionalData.enhancedSchemeData.customerReference"] = "12345"

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
	
	# set request outline
	headers = {
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD)),
		"Content-Type": "application/json"
	}

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
	if "klarna" in data["brandCode"] or "afterpay" in data["brandCode"] or "ratepay" in data["brandCode"]:
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
	send_response("Redirected in another window\n\nRequest:\n{}".format("{}?{}".format(url, urlencode(data))), "text/plain")
	webbrowser.open("{}?{}".format(url, urlencode(data)))

##############################
##		SECURED FIELDS		##
##############################

# adyen-hosted iframes for card data entry
def secured_fields_setup(data):

	# request info
	url = "https://checkout-test.adyen.com/services/PaymentSetupAndVerification/v30/setup"
	headers = {
		"Content-Type": "application/json",
		"X-API-Key": API_KEY
	}

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
	headers = {
		"Content-Type": "application/json",
		"X-API-Key": API_KEY
	}

	# static fields
	data["origin"] = LOCAL_ADDRESS
	data["returnUrl"] = RETURN_URL

	# move amount data into parent object
	reformat_amount(data)

	# move card data into paymentMethod object
	reformat_card_checkout(data)

	send_debug(data)

	# get and return response
	result = send_request(url, data, headers)
	send_response(result, "application/json")

##########################
##		3D Secure 1		##
##########################

# API call with 3d Secure redirect
def threeds1(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/authorise"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	# static fields
	data["returnUrl"] = "www.example.com"
	data["additionalData"] = {
		"executeThreeD": "true"
	}

	# move amount data into parent object
	reformat_amount(data)

	# move card data into parent object
	reformat_card(data)

	# move userAgent into browserInfo object
	indent_field(data, "browserInfo", "userAgent")
	data["browserInfo"]["acceptheader"] = "text/html"

	# get response from Adyen
	# and create a self-submitting form to redirect user to auth page
	result = json.loads(send_request(url, data, headers).decode("utf8"))
	result = '''
		<body onload="document.getElementById('3dform').submit();">
			<form method="POST" action="{issuer_url}" id="3dform">
				<input type="hidden" name="PaReq" value="{pa_request}" />
				<input type="hidden" name="MD" value="{md}" />
				<input type="hidden" name="TermUrl" value="{term_url}" />
				<noscript>
					<br>
					<br>
					<div style="text-align: center">
						<h1>Processing your 3D Secure Transaction</h1>
						<p>Please click continue to continue the processing of your 3D Secure transaction.</p>
						<input type="submit" class="button" value="continue"/>
					</div>
				</noscript>
			</form>
		</body>
		'''.format(
			pa_request=result["paRequest"], 
			issuer_url=result["issuerUrl"],
			md=result["md"],
			term_url="www.example.com"
		)

	send_response(result, "text/html")

######################################
##		3D SECURE 2.0 BASIC FLOW	##
######################################

# API call with 3d Secure 2.0
# part 1
def threeds2_part1(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	# move amount data into parent object
	reformat_amount(data)

	# move card data into parent object
	reformat_card(data)

	# move userAgent into browserInfo object
	indent_field(data, "browserInfo", "userAgent")
	data["browserInfo"]["acceptHeader"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
	data["browserInfo"]["language"] = "EN-GB"
	data["browserInfo"]["colorDepth"] = 32
	data["browserInfo"]["screenHeight"] = 1200
	data["browserInfo"]["screenWidth"] = 600
	data["browserInfo"]["timeZoneOffset"] = 1
	data["browserInfo"]["javaEnabled"] = "true"

	# add threeDS2RequestData
	data["threeDS2RequestData"] = {}
	data["threeDS2RequestData"]["deviceChannel"] = "browser"
	data["threeDS2RequestData"]["notificationURL"] = LOCAL_ADDRESS + "/cgi-bin/submit.py?endpoint=threeds2_result_page"

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	send_response(str(response), "text/plain")

# API call with 3d Secure 2.0
# part 2
def threeds2_part2(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise3ds2"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	data["merchantAccount"] = MERCHANT_ACCOUNT
	indent_field(data, "threeDS2RequestData", "threeDSCompInd")

	# send request to adyen
	result = send_request(url, data, headers)
	
	# send request and response to client
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	send_response(str(response), "text/plain")

def threeds2_auth_via_token(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise3ds2"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	data["merchantAccount"] = MERCHANT_ACCOUNT
	indent_field(data, "threeDS2Result", "transStatus")

	# send request to adyen
	result = send_request(url, data, headers)
	
	# send request and response to client
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	send_response(str(response), "text/plain")

##########################################
##		3D SECURE 2.0 ADVANCED FLOW 	##
##########################################
def threeds2_adv_initial_auth(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	# move amount data into parent object
	reformat_amount(data)

	# move card data into parent object
	reformat_card(data)

	# move userAgent into browserInfo object
	indent_field(data, "browserInfo", "userAgent")
	data["browserInfo"]["acceptHeader"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
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
	data["threeDS2RequestData"]["notificationURL"] = LOCAL_ADDRESS + "/cgi-bin/submit.py?endpoint=threeds2_result_page"
	
	# if data["threeDS2RequestData"]["authenticationOnly"] == "true":
		# data["threeDS2RequestData"]["acquirerBIN"] = "526567"
		# data["threeDS2RequestData"]["acquirerMerchantID"] = "526567000000005"

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	send_response(str(response), "text/plain")

def threeds2_result_page(data):

	# echo cres value
	logger.info(post_data)

	# return cres if available
	# TODO there should be a separate endpoint to return cres
	if "cres" in post_data.keys():
		send_debug(post_data["cres"])
	else:
		send_debug(post_data)

def threeds2_adv_authorise3ds2(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/authorise3ds2"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	# hardcoding successful challenge for now
	data["threeDS2Result"] = {}
	data["threeDS2Result"]["transStatus"] = "Y"

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	send_response(str(response), "text/plain")

def threeds2_adv_retrieve3ds2Result(data):

	# request info
	url = "https://pal-test.adyen.com/pal/servlet/Payment/v40/retrieve3ds2Result"
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Basic {}".format(create_basic_auth(WS_USERNAME, WS_PASSWORD))
	}

	data["merchantAccount"] = MERCHANT_ACCOUNT

	# send request to Adyen
	result = send_request(url, data, headers)

	# create response object with request and response both
	response = {}
	response["request"] = str(data)
	response["response"] = result.decode("utf8")
	send_response(str(response), "text/plain")

def threeds2_adv_acquirerAgnosticAuth(data):
	send_debug(data)

##########################
##		RESULT PAGE		##
##########################

# landing page for complete transactions
def result_page(data):
	# send POST params to logger
	logger.info(post_data)

	# echo URL params to client
	send_debug("Response from Adyen:")
	send_debug("URL params:", duplicate=True)
	send_debug(data, duplicate=True)
	send_debug("POST data:", duplicate=True)
	send_debug(post_data, duplicate=True)

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
	"hmac_signature": HMAC_signature,
	"CSE": CSE,
	"directory_lookup": directory_lookup,
	"secured_fields_setup": secured_fields_setup,
	"skip_details": skip_details,
	"threeds1": threeds1,
	"threeds2_part1": threeds2_part1,
	"threeds2_part2": threeds2_part2,
	"threeds2_auth_via_token": threeds2_auth_via_token,
	"threeds2_adv_initial_auth": threeds2_adv_initial_auth,
	"threeds2_adv_authorise3ds2": threeds2_adv_authorise3ds2,
	"threeds2_adv_retrieve3ds2Result": threeds2_adv_retrieve3ds2Result,
	"threeds2_adv_acquirerAgnosticAuth": threeds2_adv_acquirerAgnosticAuth,
	"threeds2_result_page": threeds2_result_page,
	"result_page": result_page,
	"secured_fields_submit": secured_fields_submit
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

# get data from POST fields
post_data = get_dict_from_fieldstorage()
del post_data["endpoint"]

# log request
logger.info("")
logger.info("------- NEW REQUEST -------")
logger.info("receiving incoming request to {}".format(endpoint))
logger.info("incoming URL params: {}".format(data))
logger.info("incoming POST data: {}".format(post_data))

# add merchantAccount to data
data["merchantAccount"] = MERCHANT_ACCOUNT

# make sure endpoint is valid
if not endpoint in router.keys():
	logger.critical("method not found: {}".format(endpoint))
	send_debug("SERVER ERROR")
	send_debug("Method not found: \n{}".format(e), duplicate=True)
	send_debug("\n{}".format(data), duplicate=True)

# send to proper method
else:
	router[endpoint](data)

	
