import { AJAXPost, buildFormURL } from "./common.js";

// Global vars
var globals = {};

// Config object
globals.securedFieldsConfiguration = {
	configObject : {
		originKey: "YOUR_ORIGIN_KEY", // Comes from the setupResponseJSON object.
		publicKeyToken : "YOUR_PUBLIC_KEY_TOKEN" // Comes from the setupResponseJSON object.
	},
	rootNode: '.secured-fields-form'
};

// Event listeners async form submissions
export function initForms() {
	document.getElementById("setupBtn").addEventListener("click", setupSecuredFields);
	document.getElementById("checkoutBtn").addEventListener("click", submitPayment);

	globals.brandImage = document.getElementById("brand-container");
}

// Helper method for log output
function displayToWindow(text) {
	document.getElementById("output").innerHTML = document.getElementById("output").innerHTML + "<br>" + text;
}

// Handle response from setup call
const setupCallback = function(data) {

	console.log("response:" );
	console.log(data);

	try {

		// Parse data
		globals.data = data;
		globals.securedFieldsConfiguration.configObject.originKey = globals.data.originKey;
		globals.securedFieldsConfiguration.configObject.publicKeyToken = globals.data.publicKeyToken;

		console.log(globals.data);

		// Initialize secured fields
		globals.securedFields = csf(globals.securedFieldsConfiguration);

		console.log(globals.securedFields);

		// Set initial 'generic' card logo
		globals.brandImage.setAttribute("src", globals.data.logoBaseUrl + "card@2x.png");

		globals.securedFields.onBrand( function(brandObject){

			// Triggered when receiving a brand callback from the credit card number validation.
			if (brandObject.brand) {
				globals.brandImage.setAttribute("src", globals.data.logoBaseUrl + brandObject.brand + "@2x.png");
				globals.paymentMethodType = brandObject.brand;
			}
		});

		globals.securedFields.onAllValid(function(allValidObject){
			// Triggers when all credit card input fields are valid - and triggers again if this state changes.
			if(allValidObject.allValid === true){
				console.log('All credit card input is valid :-)');
			}
		});

		// Un-gray out the entry fields
		document.getElementById("secured-fields-container").classList.remove("inactive");
	}
	catch (e) {
		console.log(e);
		document.getElementById("output").innerHTML = e;
	}
};

// Called on submitting payment data form
function setupSecuredFields(e) {
	e.preventDefault();

	// calls async javascript function to send to server
	AJAXPost(buildFormURL(), setupCallback);
}

// Called from JS library on successful payment
function paymentSuccess(result) {
	if (result.type === "complete") {
		document.getElementById("secured-fields-container").remove();
		if (result.resultCode === "authorised") {
			displayToWindow("Success!");
		}
		else {
			displayToWindow("Failure");
		}
	}
	displayToWindow(JSON.stringify(result));

	// Show verify container
	document.getElementById("verifyContainer").classList.remove("inactive");

	// Set up verify call
	document.getElementById("verifyBtn").addEventListener("click", function() {

		// Disable verify button
		document.getElementById("verifyBtn").disabled = true;

		// Send data to server
		var url = "./cgi-bin/submit.py";
		var postData = "endpoint=checkout_verify&payload=" + result.payload;

		AJAXPost(url + "?" + postData, function(data) {
			// Display response
			document.getElementById("verifyResult").innerHTML = data;
		});
	});
}

// Called from JS library on failed payment
function paymentError(result) {
	displayToWindow("Error!");
	displayToWindow(result);
}

// Send payment using info from SecuredFields
function submitPayment(e) {
	e.preventDefault();

	console.log(globals.securedFields);

	// Configuration object
	var initPayConfig = {
		responseData : globals.data, // This is the JSON object you received from the ‘setup’ call to the Checkout API.
		pmType : globals.paymentMethodType, // e.g. ‘visa’,’mc’, ‘amex’.
		formEl : document.getElementById("adyen-encrypted-form"), // The <form> element that holds your securedFields.
		onSuccess : paymentSuccess, // Callback function for the AJAX call that checkoutInitiatePayment makes.
		onError : paymentError // Callback function function for the AJAX call that checkoutInitiatePayment makes.
	};

	displayToWindow("sending payment...")
	
	// Sends data to server
	// Using method from JS library
	var res = chcktPay(initPayConfig);
}
