#!/usr/local/adyen/python3/bin/python3

'''
Server to forward requests to Adyen

The endpoint should be included in a header called "endpoint"
and request data as a JSON object or URL params.
'''

# system utilities
import os, sys, json

# HTTP parsing
from urllib.parse import parse_qs

# custom server utilities
from ServerUtils import ServerUtils
utils = ServerUtils("CGI")


##############################
##		REQUEST HANDLING	##
##############################

utils.logger.info("")
utils.logger.info("")
utils.logger.info("------- incoming request to server.py -------")

# parse URL params
request_data = parse_qs(os.environ["QUERY_STRING"])
utils.logger.info("incoming URL params: {}".format(request_data))

# get data from POST fields
if os.environ["REQUEST_METHOD"] == "POST":
	post_data = json.loads(sys.stdin.read(int(os.environ["CONTENT_LENGTH"])))
	utils.logger.info("incoming POST data: {}".format(post_data))

	# combine URL and POST params
	request_data.update(post_data)

# get endpoint from request
try:
	endpoint = request_data["endpoint"]
	del request_data["endpoint"]
except KeyError:
	utils.logger.error("no endpoint in request data")
	utils.send_debug("no endpoint in request data")
	exit(1)

# send request
response = utils.send_request(endpoint, request_data)

# respond to client with respose
utils.send_response(response)

utils.logger.info("")
