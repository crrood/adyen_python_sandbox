function sendJSONData() {
	var data = JSON.parse(document.getElementById("JSONTextArea").value);
	data.endpoint = "hmac_signature";

	var paramString = "?";
	for(var key in data) {
		if(data.hasOwnProperty(key)) {
			paramString = paramString + key + "=" + data[key] + "&";
		 }
	}

	window.location = "cgi-bin/submit.py" + paramString;
};