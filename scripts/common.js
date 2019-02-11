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

// utility to output to web page
export function output(text, title = null, subtitle = null, indentation = 4) {
	const containerEl = document.querySelector("#output");

	// add a title if param is present
	if (title) {
		const titleEl = document.createElement("div");
		titleEl.innerHTML = "--------------- " + title + " ---------------";
		containerEl.append(titleEl);
	}

	// add a subtitle, usually endpoint or SDK method
	if (subtitle) {
		const subtitleContainer = document.createElement("pre");
		const subtitleEl = document.createElement("code");
		subtitleContainer.appendChild(subtitleEl);
		subtitleEl.innerHTML = subtitle;
		containerEl.append(subtitleEl);
	}

	// format output
	if (typeof(text) === "object") {
		try {
			// indent JSON object
			text = JSON.stringify(text, null, indentation);
		}
		catch(e) {
			// convert object to string
			text = text.toString();
		}
	}
	else if (typeof(text) === "string") {
		try {
			// try to convert text to JSON
			text = JSON.stringify(JSON.parse(text), null, indentation);
		}
		catch(e) {
			// do nothing; sometimes text is just text - Lao Tzu
		}
	}

	// remove extra backslashes from overzealous URL encoding
	text = text.replace(/\\/g, "");

	// create element to be added
	const outputContainer = document.createElement("pre");
	const outputEl = document.createElement("code");
	outputContainer.appendChild(outputEl);
	outputEl.innerHTML = text;
	containerEl.append(outputContainer);
}

// this shouldn't be necessary.. I must be building the response wrong somehow
export function sanitizeJSON(data) {
	return JSON.parse(data.replace(/'/g, '"').replace(/"\{/g, "{").replace(/\}"/g, "}"));
}

// generate UUID for 3DS2 advanced flow
export function uuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    let r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}