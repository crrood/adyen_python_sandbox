import { SERVER_URL, uuid } from "./common.js";

const NOTIFICATION_URL = SERVER_URL + "?endpoint=threeds2_result_page";
const CACHED_THREEDS_URL = "https://pal-test.adyen.com/threeds2simulator/acs/startMethod.shtml";

const globals = {};


  //////////////////
 // MAIN METHODS //
//////////////////

// creates an iframe with a self-submitting form, which redirects to the issuer's page
// that page redirects to the result on completion
export async function getFingerprint(serverTransactionID, methodURL, threedsMethodNotificationURL, container) {

    return new Promise((resolve, reject) => {

    	// Create and Base64Url encode a JSON object containing the serverTransactionID & threeDSMethodNotificationURL
    	const dataObj = { threeDSServerTransID : serverTransactionID, threeDSMethodNotificationURL : threedsMethodNotificationURL };
    	const jsonStr = JSON.stringify(dataObj);
    	const base64URLencodedData = btoa(jsonStr);

    	// Create an iframe with a form that redirects to issuer's fingerprinting page
    	globals.iframe = createIFrame(container, "threeDSMethodIframe", "0", "0", data => {
            console.log("callback");
            if (data.target.contentWindow.location.host) {
                resolve({threeDSCompInd: "Y"});
                console.log("resolved");
                console.log(data.target.contentWindow.location.host);
            }
        });
        const form = createForm('threedsMethodForm', methodURL, 'threeDSMethodIframe', 'threeDSMethodData', base64URLencodedData);
        globals.iframe.appendChild(form);
        form.submit();

        // timeout after 15 seconds
        setTimeout(() => reject({threeDSCompInd: "U"}), 15000);
    });
}

  ////////////////////
 // HELPER METHODS //
////////////////////

// creates an iFrame element and attaches it to the page
function createIFrame(container, name, width = '0', height = '0', callback = undefined) {

	// 1. Create iframe HTML
	const iframe = document.createElement('iframe');
	const iframeHTML = '<html><body></body></html>';

	iframe.height = height;
	iframe.width = width;
	iframe.name = name;
	iframe.innerHTML = iframeHTML;

	iframe.onload = callback;

	// attach to page
	if (container instanceof HTMLElement) {
		container.appendChild(iframe);
		return iframe;
	}
	else {
		console.error("container is not of type HTMLElement");
	}
}

// creates a form for sending post data
// can't be sent via normal AJAX because the issuer redirect requires the page to load
function createForm(name, action, target, inputName, inputValue) {

    if (!name || !action || !inputName || !inputValue) {
        throw new Error('Not all parameters provided');
    }

    const form = document.createElement( 'form' );
    form.style.display = 'none';
    form.name = name;
    form.action = action;
    form.method = "POST";
    form.target = target;
    const input = document.createElement( 'input' );
    input.name = inputName;
    input.value = inputValue;
    form.appendChild( input );
    return form;
}
