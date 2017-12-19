// Styling for checkout
var hostedFieldStyle = {
	base: {
		fontSize: '16px',
		background: "#68FFC1",
		outline: "2px black",
		color: "blue",
	}
};

document.getElementById("checkoutBtn").addEventListener("click", openCheckout);

// Handle response from setup call
callback = function() {

	if (this.readyState == 4) {
		console.log(this);

		try {
			var data = JSON.parse(this.responseText);

			// Initialize checkout
			var checkout = chckt.checkout(data, '.checkout', hostedFieldStyle);

			// Handle response from initiate call
			chckt.hooks.beforeComplete = function(pNode, pHookData, pData){
				document.getElementById("paymentResult").innerHTML = pData["resultCode"];	
				console.log(JSON.stringify(pData));
			}
		}
		catch (e) {
			console.log(e);
			document.getElementById("checkout").innerHTML = this.responseText;
		}
	}
};

// Send request to server
function AJAXPost(path, headers, params, method) {
	var request = new XMLHttpRequest();
	request.open(method || "POST", path, true);
	request.onreadystatechange = callback;

	for (var key in headers) {
		request.setRequestHeader(key, headers[key]);
	}

	console.log(params);

	request.send(params);
};

function openCheckout() {
	var inputParams = document.querySelectorAll("input[type=text]");

	// Get request details from html form
	var formString = "";
	for (var param of inputParams) {
		formString = formString + param.name + "=" + param.value + "&";
	}
	formString = formString + "endpoint=checkout_setup";

	// Set parameters for request to server
	// url = "http://localhost:8000/cgi-bin/checkout_requester.py";
	url = "http://localhost:8000/cgi-bin/submit.py";
	headers = { "Content-Type": "application/x-www-form-urlencoded" };
	method = "POST";

	// calls async javascript function to send to server
	AJAXPost(encodeURI(url + "?" + formString), headers, {}, method);
}