// Styling for checkout
var sdkConfigObj = {
	base: {
		fontSize: '16px',
		background: "#68FFC1",
		outline: "2px black",
		color: "blue",
	},
	context: "test"
};

document.getElementById("checkoutBtn").addEventListener("click", openCheckout);

// Handle response from setup call
const setupCallback = function() {

	if (this.readyState == 4) {
		console.log(this);

		try {
			var data = JSON.parse(this.responseText);

			// Initialize checkout
			var checkout = chckt.checkout(data, '.checkout', sdkConfigObj);

			// Handle response from initiate call
			chckt.hooks.beforeComplete = function(pNode, pHookData){
				console.log(JSON.stringify(pHookData));
				document.getElementById("paymentResult").innerHTML = pHookData["resultCode"];

				if (pHookData.resultCode.toLowerCase() === "authorised") {
					// Set up verify call
					document.getElementById("verifyBtn").addEventListener("click", function() {
						document.getElementById("verifyBtn").remove()
						var url = "http://localhost:8000/cgi-bin/submit.py";
						var postData = "endpoint=checkout_verify&payload=" + pHookData.payload;
						
						AJAXPost(url + "?" + postData, "", "", "POST", function() {
							document.getElementById("verifyResult").innerHTML = this.responseText;
						});
					});
					document.getElementById("verifyBtn").classList.remove("inactive");
				}
			}
		}
		catch (e) {
			console.log(e);
			document.getElementById("checkout").innerHTML = this.responseText;
		}
	}
};

// Send request to server
function AJAXPost(path, headers, params, method, callback) {
	var request = new XMLHttpRequest();
	request.open(method || "POST", path, true);
	request.onreadystatechange = callback;

	for (var key in headers) {
		request.setRequestHeader(key, headers[key]);
	}

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
	url = "cgi-bin/submit.py";
	headers = { "Content-Type": "application/x-www-form-urlencoded" };
	method = "POST";

	// calls async javascript function to send to server
	AJAXPost(encodeURI(url + "?" + formString), headers, {}, method, setupCallback);
}