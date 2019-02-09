// constants
export const FORM_ENCODED_HEADER = { "Content-Type": "application/x-www-form-urlencoded" };
export const SERVER_URL = "http://localhost:8000/cgi-bin/submit.py";

// wrapper to send requests to server
export function AJAXPost(path, callback, headers = FORM_ENCODED_HEADER, params = {}, method = "POST") {
	let request = new XMLHttpRequest();
	request.open(method, path, true);
	request.onreadystatechange = function() {
		if (this.readyState == 4) {
			callback(this.responseText);
		}
	};

	for (let key in headers) {
		request.setRequestHeader(key, headers[key]);
	}

	request.send(params);
}

export function AJAXGet(path, callback) {
	let request = new XMLHttpRequest();
	request.open("GET", path, true);
	request.onreadystatechange = function() {
		if (this.readyState == 4) {
			callback(this.responseText);
		}
	};

	request.send();
}

// pulls parameters from HTML form and sends to server
// accepts an optional JSON object of parameters to add
export function buildFormURL(customParams = null) {
	let inputParams = document.querySelectorAll("input[type='text'], input[type='hidden']");

	// Get request details from html form
	let formString = "";
	for (let param of inputParams) {
		formString = formString + param.name + "=" + param.value + "&";
	}

	// Add custom parameters from function call
	for (let key in customParams) {
		formString = formString + key + "=" + customParams[key] + "&";
	}

	return encodeURI(SERVER_URL + "?" + formString);
}

// generate UUID
export function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    let r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}