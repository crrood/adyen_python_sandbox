import { AJAXPost, buildFormURL } from "./common.js";

// Define a custom style.
const styleObject = {
	base: {
		color: 'black',
		fontSize: '16px',
		fontSmoothing: 'antialiased',
		fontFamily: 'Helvetica'
	},
	error: {
		color: 'red'
	},
	placeholder: {
		color: '#d8d8d8'
	},
	validated: {
		color: 'green'
	}
};

window._$bsdl = true;

// Called on page load
export function initForms() {
	// Logging
	document.querySelector("#logInputs").addEventListener("click", function() {
		console.log(document.querySelectorAll("input:not([type='button']):not([type='submit'])"));
		console.log(document.querySelector("div.cards-div.js-chckt-pm__pm-holder"));
	});

	// Mutation observer
	// Logs to console when a child is added to the card form
	var observer = new MutationObserver(function(mutationsList) {
		console.log(mutationsList);
	});
	var config = { attributes: true, childList: true };
	observer.observe(document.querySelector("div.cards-div.js-chckt-pm__pm-holder"), config);

	// Initialize object
	var securedFields = csf(
		{
			configObject : {
				originKey : "pub.v2.8115054323780109.aHR0cDovL2xvY2FsaG9zdDo4MDAw.B92basPQjzeM7_TtJ2IKZoln780QtvwAiPFDEbKs7Ng"
			},
			rootNode: '.cards-div',
			paymentMethods : {
				card : {
					sfStyles : styleObject,
				}
			}
		}
	);

	// Listen to events.
	securedFields.onLoad(function(){
		console.log('All fields have been loaded');
	});

	securedFields.onAllValid(function(allValidObject){
		// Triggers when all credit card input fields are valid - and triggers again if this state changes.
		if(allValidObject.allValid === true){
			console.log('All credit card input is valid');
		}
	});

	securedFields.onBrand(function(brandObject){
		// Triggers when receiving a brand callback from the credit card number validation.
		if(brandObject.brand) {
			document.getElementById('card-type').innerHTML = brandObject.brand;
		}
	});

	securedFields.onConfigSuccess(function(someObject){
		console.log("onClientSuccess");
		console.log(someObject);
	});

	// Send data to server
	document.querySelector("#submitPayment").addEventListener("click", function() {

		const paramString = buildFormURL();

		console.log("Data sent to local server:");
		console.log(paramString);

		AJAXPost(paramString, function(data) {
			console.log("Response from local server:");
			console.log(data);

			document.querySelector("#output").innerHTML = data.replace(/\n/g, "<br>");
		});
	});
}