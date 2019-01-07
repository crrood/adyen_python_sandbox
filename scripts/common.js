// constants
var FORM_ENCODED_HEADER = { "Content-Type": "application/x-www-form-urlencoded" };
var SERVER_URL = "cgi-bin/submit.py";

// wrapper to send requests to server
function AJAXPost(path, callback, headers = FORM_ENCODED_HEADER, params = {}, method = "POST") {
	var request = new XMLHttpRequest();
	request.open("POST", path, true);
	request.onreadystatechange = callback;

	for (var key in headers) {
		request.setRequestHeader(key, headers[key]);
	}

	request.send(params);
};

// pulls parameters from HTML form and sends to server
// accepts an optional object of parameters to add
function buildFormURL(customParams = null) {
	var inputParams = document.querySelectorAll("input[type='text'], input[type='hidden']");

	// Get request details from html form
	var formString = "";
	for (var param of inputParams) {
		formString = formString + param.name + "=" + param.value + "&";
	}

	// Add custom parameters from function call
	for (var key in customParams) {
		formString = formString + key + "=" + customParams.key + "&";
	}

	return encodeURI(SERVER_URL + "?" + formString);
}