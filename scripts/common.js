// constants
export const FORM_ENCODED_HEADER = { "Content-Type": "application/x-www-form-urlencoded" };
export const JSON_ENCODED_HEADER = { "Content-Type": "application/json" };
export const SERVER_URL = "http://localhost:8000/cgi-bin/submit.py";

// wrapper to send requests to server
export function AJAXPost(path, callback, headers = FORM_ENCODED_HEADER, params = {}) {
	let request = new XMLHttpRequest();
	request.open("POST", path, true);
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

	// holder for title, subtitle, and content
	const contentEl = document.createElement("div");

	// holder for container + summary
	const containerEl = document.createElement("div");
	containerEl.classList.add("output-item");
	containerEl.appendChild(contentEl);

	// text to show when element is collapsed
	let summary;

	// format output
	if (typeof(text) === "object") {
		try {
			// indent JSON object
			text = JSON.stringify(text, null, indentation);
			summary = "{ JSON }";
		}
		catch(e) {
			// convert non-JSON object to string
			text = text.toString();
			summary = "{ Object }";
		}
	}
	else if (typeof(text) === "string") {
		try {
			// try to convert text to JSON
			text = JSON.stringify(JSON.parse(text), null, indentation);
			summary = "{ JSON }";
		}
		catch(e) {
			// do nothing; sometimes text is just text - Lao Tzu
			// use first 50 characters as summary
			summary = text.match(/.{50,50}/) + (text.length > 55) ? "..." : "";
		}
	}

	// remove extra backslashes from overzealous URL encoding
	text = text.replace(/\\/g, "");

	// add a subtitle, usually endpoint or SDK method
	if (subtitle) {
		const subtitleContainer = document.createElement("pre");
		const subtitleEl = document.createElement("code");
		subtitleContainer.appendChild(subtitleEl);
		subtitleContainer.classList.add("output-subtitle");
		subtitleEl.innerHTML = subtitle;
		contentEl.append(subtitleContainer);

		if (!title) {
			summary = subtitle;
		}
	}

	// set summary to title if it's supplied
	if (title) {
		summary = title;
		
		// append arrow at end of summary
		summary += " &#9656;";
	}


	// create main body of item
	const outputTextContainer = document.createElement("pre");
	const outputText = document.createElement("code");
	outputTextContainer.appendChild(outputText);
	outputTextContainer.classList.add("output-main-body");
	outputText.innerHTML = text;
	contentEl.appendChild(outputTextContainer);

	// create summary element
	const summaryEl = document.createElement("div");
	summaryEl.classList.add("output-summary");
	summaryEl.innerHTML = summary;
	containerEl.insertBefore(summaryEl, containerEl.firstChild);

	// add event listener to expand / collapse
	summaryEl.addEventListener("click", () => {
		contentEl.classList.toggle("display-none");
	});

	// add to page
	document.querySelector("#output").append(containerEl);
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