console.log("reactScript loaded");

// single line text input item
//
// props:
// fieldName, fieldValue
function TextInput(props) {
	return (
		<div className="inputHolder">
			{props.fieldName}: <input type="text" name={props.fieldName} defaultValue={props.fieldValue}/><br/>
		</div>
	)
};

// hidden input for passing variables without a text field
//
// props:
// fieldName, fieldValue
function HiddenInput(props) {
	return (
		<input type="hidden" name={props.fieldName} defaultValue={props.fieldValue}/>
	)
};

// form consisting of text and hidden inputs
//
// props:
// fields: [[fieldName1, fieldValue1],...,[fieldNameN, fieldValueN]]
// hiddenFields: [[fieldName1, fieldValue1],...,[fieldNameN, fieldValueN]]
function ReactForm(props) {
	return (
		<form id="reactForm" className="clientForm" action={props.action}>
			{props.fields.map((fieldObj) => 
				<TextInput key={fieldObj[0]} fieldName={fieldObj[0]} fieldValue={fieldObj[1]}/>
			)}
			{props.hiddenFields.map((fieldObj) => 
				<HiddenInput key={fieldObj[0]} fieldName={fieldObj[0]} fieldValue={fieldObj[1]}/>
			)}
			<input type="submit" className="submitBtn" value={props.submitText}/>
		</form>
	)
};

// add text form to DOM
//
// data:
//	fields: [[fieldName1, fieldValue1],...,[fieldNameN, fieldValueN]]
//	hiddenFields: [[fieldName1, fieldValue1],...,[fieldNameN, fieldValueN]]
//	submitText: text for submit button
// id: id of DOM element to attach form to
function renderReactForm(data, id, onComplete = null) {
	console.log("renderReactForm");
	ReactDOM.render(
		<ReactForm {async ? : action="cgi-bin/submit.py"} fields={data.fields} hiddenFields={data.hiddenFields} submitText={data.submitText}/>,
		document.getElementById(id)
	);

	if (onComplete != null) {
		onComplete();
	}
};

// function to be called by client HTML page
//
// should call renderReactForm with data and id values defined
// and any other behavior to be defined after this script has loaded
renderPage();
