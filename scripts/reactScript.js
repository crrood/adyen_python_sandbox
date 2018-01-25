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
		<form className="clientForm" action={props.action}>
			{props.fields.map((fieldObj) => 
				<TextInput key={fieldObj[0]} fieldName={fieldObj[0]} fieldValue={fieldObj[1]}/>
			)}
			{props.hiddenFields.map((fieldObj) => 
				<HiddenInput key={fieldObj[0]} fieldName={fieldObj[0]} fieldValue={fieldObj[1]}/>
			)}
		</form>
	)
};

// add text form to DOM
//
// data:
//	 fields: [[fieldName1, fieldValue1],...,[fieldNameN, fieldValueN]]
//	 hiddenFields: [[fieldName1, fieldValue1],...,[fieldNameN, fieldValueN]]
// id: id of DOM element to attach form to
function renderReactForm(data, id) {
	ReactDOM.render(
		<ReactForm action="cgi-bin/submit.py" fields={data.fields} hiddenFields={data.hiddenFields}/>,
		document.getElementById(id)
	);
};