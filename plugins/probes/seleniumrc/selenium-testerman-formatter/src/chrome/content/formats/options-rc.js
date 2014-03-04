/*
 * Options, header/footer generation for the Testerman ATS Formatter
 *
 * The content of this file was originally in testerman.js. As the file as grown, things were seperated.
 *
 * The selenese commands are looped several times during the ats file generation.
 * This is not the most efficient way, but keeps the code cleaner.  
 */

this.hooks.beforeClassDefinition = undefined;
this.hooks.afterClassDefinition = undefined;
this.hooks.beforeFistSeleniumCommand = undefined;
this.hooks.beforeMetaData = undefined;

///////////////////////////////////////////////////
// functions/values called/used by remoteControl.js
///////////////////////////////////////////////////

/**
 * These options are used for the configuration form in the Selenium IDE GUI (see this.configForm).
 * See header/footer generation as well.
 * 
 * You may add parameters to this.options['staticPxParameters'] like this:
 *
 * var p = { name : "PX_MY_PARAM", default : "mydefaultvalue", type : "string" };
 * addStaticPxParameter(p);
 *
 * printStaticPxParameters() will dump all parameters saved this way to the metadata block.
 *
 * ATTENTION: If you add a addStaticPxParameter(), you have to reset the options (in case you changed s.th.)
 * in Selenium IDE -> Options -> Options -> Formats -> "Reset Options"
 */
this.options = {
	receiver: "sel",
	rcHost: "localhost",
	rcPort: "4444",
	environment: "firefox",
	superClass: "TestCase",
	initialIndents: '2',
	indent: 'tab',
	tsiPort: 'selenium_rc', // TestSystemInterfacePortName
	probeType: 'selenium', // probe type (for future "webdriver" or "remotecrontrol" selenium probe
	probeUri: 'probe:selenium',
	//staticPxParameters: (this.options['staticPxParameters'] ? this.options['staticPxParameters'] : ""),
	staticPxParameters : "",
	showSelenese: 'true',
};

this.configForm = 
	'<description>Host (Selenium RC)</description>' +
	'<textbox id="options_rcHost" />' +
	'<description>Port (Selenium RC)</description>' +
	'<textbox id="options_rcPort" />' +
	'<description>Browser</description>' +
	'<textbox id="options_environment" />' +
        '<checkbox id="options_showSelenese" label="Show Selenese"/>' +
	'<description>(Note: If you do not show (print) the selenese, the resulting ats file can not be parsed (opened) with Selenium IDE)</description>' +
	'<description>Superclass</description>' +
	'<textbox id="options_superClass" />' +
	'<description>Probe Type</description>' +
	'<textbox id="options_probeType" />' +
	'<description>Probe URI</description>' +
	'<textbox id="options_probeUri" />' +
	'<description>Static parameters (<a href="#" style="color: #0000FF;cursor:pointer" onclick="alert(\'Use this text area to define static parameters.\nExample:\n&quot;PX_MY_PARAM:integer:42&quot; or &quot;PX_YOUR_PARAM:string:defaultvalue&quot;.\n\nEvery parameter defined this way will be dumped to the meta data block of the generated code.\nExample:\n&quot;# &lt;parameter name=PX_MY_PARAM default=42 type=integer&gt;&lt;![CDATA[]]&gt;&lt;/parameter&gt;&quot; or &quot;# &lt;parameter name=PX_YOUR_PARAM default=defaultvalue type=string&gt;&lt;![CDATA[]]&gt;&lt;/parameter&gt;&quot;\')" >WTF ?</a>)</description>' +
	'<textbox id="options_staticPxParameters" multiline="true" rows="6"/>' +
	'';

/**
 * Dump the ats file header.
 * Dumps meta data block and the beginning of the test case class.
 * A lot of helper functions are called to get dynamic/static px parameters,
 * dump the selenese list or do other actions.
 * Most of the helper functions will iterate over the command list. This is
 * not very performant (one big loop would probably do the trick) but way
 * more readible.
 */
this.options.getHeader = function(testCase) {
	var result = "" +
	(hooks.beforeMetaData ? hooks.beforeMetaData(testCase) : "") +
	'# __METADATA__BEGIN__\n' +
	'# <?xml version="1.0" encoding="utf-8" ?>\n' +
	'# <metadata version="1.0">\n' +
	'# <description>' + getTestCaseDescription(testCase) + '</description>\n' +
	'# <prerequisites>prerequisites</prerequisites>\n' +
	'# <parameters>\n' +
	'# <parameter name="PX_SELENIUM_RC_HOST" default="${rcHost}" type="string"><![CDATA[]]></parameter>\n' +
	'# <parameter name="PX_SELENIUM_BROWSER" default="${environment}" type="string"><![CDATA[]]></parameter>\n' +
	'# <parameter name="PX_SELENIUM_RC_PORT" default="${rcPort}" type="integer"><![CDATA[]]></parameter>\n' +
	'# <parameter name="PX_SELENIUM_SERVER_URL" default="${baseURL}" type="string"><![CDATA[]]></parameter>\n' +
	'# <parameter name="PX_SELENIUM_CLOSE_BROWSER" default="1" type="integer"><![CDATA[]]></parameter>\n' +
	printStaticPxParameters() + // from this.options[staticPxParameters]
	printDynamicPxParameters(testCase) +
	'# </parameters>\n' +
	'# </metadata>\n' +
	'# __METADATA__END__\n' +
	(hooks.afterMetaData ? hooks.afterMetaData(testCase) : "") +
	'\n' +
	(options['showSelenese'] == "true" ? printFormalCommandList(testCase.commands) : "") +
	'\n\n' +
	(hooks.beforeClassDefinition ? hooks.beforeClassDefinition(testCase) : "") +
	'class ' + getTestermanClassName(testCase) + '(${superClass}):\n' +
	indents(1) + '# here might be python docstrings\n' + 
	indents(1) + 'def body(self):\n' +
	indents(2) + '#set up (port mapping)\n' +
	indents(2) + '${receiver} = self.mtc[\'sel\']\n' +
	indents(2) + 'port_map(${receiver}, self.system[\'${tsiPort}\'])\n' +
	'\n' + indents(2) + '#selenium commands\n' +
	(hooks.beforeFistSeleniumCommand ? hooks.beforeFistSeleniumCommand(testCase) : "")
	'';
	return result;
}

/**
 * Dump footer.
 * Dumps the test adapter configuration and the control part.
 */
this.options.getFooter = function(testCase) {
	return '' + 
	'\n' +
	indents(2) + '# (port unmapping)\n' +
	indents(2) + 'port_unmap(${receiver}, self.system[\'${tsiPort}\'])\n' +
	(hooks.afterClassDefinition ? hooks.afterClassDefinition(testCase) : "") +
	'\n\n' +
	'##\n' +
	'# Test Adapter Configurations\n' +
	'##\n' +
	'bind(\'' + this.tsiPort + '\', \'' + this.probeUri + '\', \'' + this.probeType + '\', server_url = PX_SELENIUM_SERVER_URL, rc_host = PX_SELENIUM_RC_HOST, rc_port = PX_SELENIUM_RC_PORT, browser = PX_SELENIUM_BROWSER, auto_shutdown = PX_SELENIUM_CLOSE_BROWSER)\n' + 
	'\n\n' + 
	'##\n' +
	'# Control definition\n' +
	'##\n' +
	'verdict = ' + getTestermanClassName(testCase) + '().execute()\n' +
	'#if (verdict == PASS):\n' +
	indents(1) + '# execute other test cases ...\n'+
	'\n';
}

///////////////////////////////////////////////////
// auxiliary functions for header/footer generation
///////////////////////////////////////////////////

/**
 * Get test case description
 * Basically returns a string saying "hi, this is the description for test case xy"
 */
function getTestCaseDescription(testCase) {
	var description = (testCase.description ? testCase.description : "This is the description");
	return testCase.getTitle() + ": " + description;
}

/**
 * Add a static parameter.
 * Adds a static parameter to options['staticPxParameters']. Expects an associative array
 * and adds it to the existing string.
 */
function addStaticPxParameter(parameter) {
	var s = parameter['name'] + ":" + parameter['type'] + ":" + parameter['default'] + "\n";
	options['staticPxParameters'] += s;
}

/**
 * Return all static parameters.
 * Static parameters stored in options['staticPxParameters'] as a string are split
 * and an array is returned containing the ordered list of parameters.
 */
function getStaticPxParameters() {
	var arr = options['staticPxParameters'].split("\n");
	var result = new Array();
	var re = new RegExp("^(" + pxParameterRegExp + "):(.+?):(.+)$");
	for (var i = 0; i < arr.length; i++) {
		var s = arr[i];
		var m = re.exec(s);
		if (m) {
			var p = {};
			p['name'] = m[1];
			p['type'] = m[2];
			p['default'] = m[3];
			result.push(p);
		}
	}
	return result;
}

/**
 * Dump PX_XXX parameters to the meta data block
 * Every predefined parameter (in options) will be dumped to every generated source code.
 * This functions retreives an array of parameters from getStaticPxParameters() and builds s.th. like
 * '# <parameter name="PX_XXX" default="default" type="string"><![CDATA[]]></parameter>'
 * for each of them.
 */
function printStaticPxParameters() {
	var parameters = getStaticPxParameters();
	if (parameters.length == 0) return "";

	var result = "";
	for (var i = 0; i < parameters.length; i++) {
		var p = parameters[i];
		result += '# <parameter name="' + p['name'] + '" default="' + p['default'] + '" type="' + p['type'] + '"><![CDATA[]]></parameter>\n';
	}
	return result;
}


/**
 * Return all PX_XXX parameters for dumping to the Testerman metadata block.
 * Retuns parameters generated from the actual selenese commands.
 * "Regular expression" for parameter values:
 * [(regex|regexp):]${PX_XXX[:default_value]}
 * Some selenese (matching the regexp) will use get_variable(PX_XXX) later instead of their original values.
 * Every PX_XXX in one of the commands will declared as a known variable.
 * See example/explanations in testerman.js
 *
 */
function printDynamicPxParameters(testCase) {
	// "${PX_XXX:42} || ${PX_XXX} || regexp:${PX_XXX:42} || ${PX_XXX:42:http://www.urlg/} 
	var re = new RegExp("^.*\\$\{(" + pxParameterRegExp + "):?(.+)?\}.*$");

	function extractPxParameterName(value) {
		var m = re.exec(value);
		return m[1];
	}

	function extractActualValue(value) {
		var m = re.exec(value);
		if (m[2]) { // "[regepx:]PX_XXX:42"
			return m[2];
		}
		return undefined; // "PX_XXX"
	}

	function getTypeOf(value) {
		if (typeof(value) == "number" || ! isNaN(value)) { // for 444 || "444"
			return "integer";
		}
		return typeof(value);
	}
	var result = ""; 
	commands = testCase.commands;
	// loop over all commands and extract patterns to store them as PX_XXX
	for (var i = 0; i < commands.length; i++) {
		var command = commands[i];
		if (command.type == "command") {
			var lastArg = command.getRealValue(); // "if (this.value) return value else return target" --> see selenium-ide/chrome/content/testCase.js
			// this is a command with a PX_XXX parameter
			if (re.test(lastArg)) {
				// the name of the px parameter is already given by the user ("PX_MY_VALUE:1234")
				var name = extractPxParameterName(lastArg);
				var actualValue = extractActualValue(lastArg);
				var type = getTypeOf(actualValue);

				if (actualValue) { // if the user didn't gave a value, this means that the PX_XXX has already been defined during the previous loopings (e.g. current command was only "PX_XXX" and not "PX_XXX:value") or the user supposes, that this parameter is given as a static parameter
					result += '# <parameter name="' + name + '" default="' + actualValue + '" type="' + type + '"><![CDATA[]]></parameter>\n';
					// declare PX_XXX:42 so that the current command is recognized as having a declared var as well
					addDeclaredVar(name + ":" + actualValue);
				}
				// we declare all PX_XXX 
				addDeclaredVar(name);
			}
			
		}

	}
	
	return result;
}

/**
 * Return class name.
 */
function getTestermanClassName(testCase) {
	return 'TC_' + testCase.getTitle().toUpperCase().replace(/[^A-Z0-9]/g, "_");
}

/**
 * Print selenese list.
 * This functions is called during header generation. It will list every command.
 * The generated can later be used to generate a Selenium IDE test case from the ats file (e.g. pars()).
 */
function printFormalCommandList(commands) {
	if (commands.length == 0) return ""; // don't bother people
	var result = "# Please do not alter the following command list. It is used to extract a Selenium IDE test case from this ats file.\n# command list (command | target | value):\n";
	for (var i = 0; i < commands.length; i++) {
		var command = commands[i];
		var c = ""; var t = ""; var v = "";
		if (command.type == "command") {
			c = command.command; t = command.target; v = command.value;
		} else if (command.type == "comment") {
			c = command.type; t = command.comment;
		} else if (command.type == "line") {
			c = command.type; t = command.line;
		}
		result += "#selenese: " + c + " | " + t + " | " + v + "\n";
	}
	return result;
}

/**
 * Replace option values in the given text.
 * Every option, represented in the text whit ${optionName} is replaced by the value in this.options[optionName].
 * Used during header/footer generation.
 */
function parseTextWithOptions(text, testCase) {
	var parsedText = text.
		replace(/\$\{baseURL\}/g, testCase.getBaseURL()).
		replace(/(\$\{([a-zA-Z0-9_]+)\})/g, function(str, dollarAndName, name) { return (options[name] ? options[name] : dollarAndName) }).
		replace(/\"\"/g, "\""); //make sure we don't have 
	return parsedText;
}

