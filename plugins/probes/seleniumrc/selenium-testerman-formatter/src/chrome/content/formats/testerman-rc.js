/*
 * Format for Selenium Remote Control via Testerman ATS scripts
 *
 * Functions like notOperator() or logicalAnd() haven't been implemented. They make no sense in TTCN-3/Testerman imho.
 */

var subScriptLoader = Components.classes["@mozilla.org/moz/jssubscript-loader;1"].getService(Components.interfaces.mozIJSSubScriptLoader);
// We load remoteControl.js which will itself load formatCommandOnlyAdapter.js (see chrome://selenium-ide/content/formats/)
// In fact, remoteControl.js provides an API to easily implement formatters. 
// Due to the import to the 'this' scope, we need to declare some functions as this.functionName = function() { } in order to redefine them
subScriptLoader.loadSubScript('chrome://selenium-ide/content/formats/remoteControl.js', this);

// Hooks are used to add arbitrary contents to the generated code.
// Youd should defined them like this:
// hooks.beforeClassDefinition = function(testCase) { return "OMG !! Chtulu is coming!\n"; }
// Check getHeader(), getFooter(), ... for their locations.
// We define them here because they are use within options.js
this.hooks = {};

// Load our own options.js for optins, header, footer, config form
subScriptLoader.loadSubScript('chrome://testerman-formatters/content/formats/options-rc.js', this);

this.name = "testerman";
this.timerCount = 0; // number of timers in this test (used to generate a unique variable name)
this.templateAny = "any_or_none()"; // the default template to be used for failing (after checking the "good" template); if templateAny == "", the resulting branch will be "...RECEIVE()"
this.failVerdict = "FAIL"; // or "'fail'"
this.passVerdict = "PASS"; // or "'pass'"
this.waitForSeconds = 60; // wait x seconds before timeout for acessors (like waitForEditable)
this.remoteControl = true; // see generic chrome://selenium-ide/content/formats/formatCommandOnlyAdapter.js
this.assertOrVerifyStatementCounter = 0; // how many veriy and alt statemants are in this test (see countVerifyOrAssertStatements() for more information)
this.pxParameterRegExp = "PX_[_A-Z0-9]+"; // this is what a Testerman parameter looks like

// PX_XXX parameters:
// Testerman can uses "global" parameters in his meta data block. They are handy to make tests more flexible.
//
// 'static' vs. 'dynamic' px parameters:
// We use these terms to diffentiate two types of px parameters.
// Static px parameters are stored as a string in options.staticPxParameters.
// Static px parameters can be changed via the options tab in Selenium IDE.
// Static px parameters are added via addStaticPxParameter(), see options.js.
// Static px parameters are always added to the generated meta data block.
// Dynamic px parameters are generated from the selenes commands.
//

// when parsing, this function get's called for each line, this enables you to extract (you own) information from ats files
// call hooks.extractFromThisLineDuringTestCaseParse(testCase, line)
this.hooks.extractFromThisLineDuringTestCaseParse = undefined;

///////////////////////////////////////
// functions called by remoteControl.js
///////////////////////////////////////

////// (assert|verify)(True|False) //////
/**
 * Assert that the given condition is true. For stuff like assertTextPresent(), assertEditable(), ...
 * (for isXXX)
 * The test will abort on failure.
 */
function assertTrue(call) {
	var isAssert = true;
	var trueOrFalse = true;
	var branchConfigs = assertOrVerifyTrueOrFalse(call, isAssert, trueOrFalse);
	return sendAndReceive(call, branchConfigs);
}

/**
 * Assert that the given condition is false. For stuff like assertTextNotPresent(), assertNotEditable(), ...
 * (for isXXX)
 * The test will abort on failure.
 */
function assertFalse(call) {
	var isAssert = true;
	var trueOrFalse = false;
	var branchConfigs = assertOrVerifyTrueOrFalse(call, isAssert, trueOrFalse);
	return sendAndReceive(call, branchConfigs);

}

/**
 * Verify that the given condition is true. For stuff like verifyTextPresent(), verifyChecked() ...
 * (for isXXX)
 */
function verifyTrue(call) {
	var isAssert = false;
	var trueOrFalse = true;
	var branchConfigs = assertOrVerifyTrueOrFalse(call, isAssert, trueOrFalse);
	return sendAndReceive(call, branchConfigs);

}

/**
 * Verify that the given condition is false. For stuff like verifyTextNotPresent(), verifyNotChecked() ...
 * (for isXXX)
 */
function verifyFalse(call) {
	var isAssert = false;
	var trueOrFalse = false;
	var branchConfigs = assertOrVerifyTrueOrFalse(call, isAssert, trueOrFalse);
	return sendAndReceive(call, branchConfigs);
}

////// (assert|verify)(equals|notEqals) //////
/**
 * This function is normally called to compare a selenium call result with a given value (e.g. "return e1 == e2;")
 * We don't need that here. This should never be called.
 */
Equals.prototype.toString = function() {
	alert("Equals.prototype.toString() was called for { e1 = " + this.e1 + ", e2 = " + this.e2 + "}.\nThis function is not implemented.");
	return "";
};

/**
 * Assert that the returned result equals a given value.
 * (for getXXX)
 * The test will abort on failure.
 */
Equals.prototype.assert = function() {
	var equalsOrNot = true;
	var isAssert = true;
	var pattern = this.e1;
	var call = this.e2;
	var branchConfigs = assertOrVerifyEqualsOrNot(call, pattern, isAssert, equalsOrNot);
	return sendAndReceive(call, branchConfigs);
}

/**
 * Verify that the returned result equals a given value.
 * (for getXXX)
 */
Equals.prototype.verify = function() {
	var equalsOrNot = true;
	var isAssert = false;
	var pattern = this.e1;
	var call = this.e2;
	var branchConfigs = assertOrVerifyEqualsOrNot(call, pattern, isAssert, equalsOrNot);
	return sendAndReceive(call, branchConfigs);
};


/**
 * This function is normally called to compare a selenium call result with a given value (e.g. "return e1 != e2;")
 * We don't need that here. This should never be called.
 */
NotEquals.prototype.toString = function() {
	alert("NotEquals.prototype.toString() was called.\nThis function is not implemented.");
	return "";
};

/**
 * Assert that the returned result does not equal a given value.
 * (for getXXX)
 * The test will abort on failure.
 */
NotEquals.prototype.assert = function() {
	var equalsOrNot = false;
	var isAssert = true;
	var pattern = this.e1;
	var call = this.e2;
	var branchConfigs = assertOrVerifyEqualsOrNot(call, pattern, isAssert, equalsOrNot);
	return sendAndReceive(call, branchConfigs);
};

/**
 * Verify that the returned result does not equal a given value.
 * (for getXXX)
 */
NotEquals.prototype.verify = function() {
	var equalsOrNot = false;
	var isAssert = false;
	var pattern = this.e1;
	var call = this.e2;
	var branchConfigs = assertOrVerifyEqualsOrNot(call, pattern, isAssert, equalsOrNot);
	return sendAndReceive(call, branchConfigs);

};

////// (assert|verify)(matches|notMatches) //////
/**
 * This function is normally called to compare a selenium call result with a given value (e.g. "return match(e1,e2);")
 * We don't need that here. This should never be called.
 */
RegexpMatch.prototype.toString = function() {
	alert("RegexpMatch.prototype.toString() was called.\nThis function is not implemented.");
	return "";
};

/**
 * Assert that the returned result matches a regular expression.
 * (for getXXX)
 * The test will abort on failure.
 */
RegexpMatch.prototype.assert = function() {
	var matchesOrNot = true;
	var isAssert = true;
	var pattern = this.pattern;
	var call = this.expression;
	var branchConfigs = assertOrVerifyMatchesOrNot(call, pattern, isAssert, matchesOrNot);
	return sendAndReceive(call, branchConfigs);
};

/**
 * Verify that the returned result matches a regular expression.
 * (for getXXX)
 */
RegexpMatch.prototype.verify = function() {
	var matchesOrNot = true;
	var isAssert = false;
	var pattern = this.pattern;
	var call = this.expression;
	var branchConfigs = assertOrVerifyMatchesOrNot(call, pattern, isAssert, matchesOrNot);
	return sendAndReceive(call, branchConfigs);
};

/**
 * This function is normally called to compare a selenium call result with a given value (e.g. "return not match(e1,e2);")
 * We don't need that here. This should never be called.
 */
RegexpNotMatch.prototype.toString = function() {
	alert("RegexpNotMatch.prototype.toString() was called.\nThis function is not implemented.");
	return "";
};

/**
 * Assert that the returned result doesn't match a regular expression.
 * (for getXXX)
 * The test will abort on failure.
 */
RegexpNotMatch.prototype.assert = function() {
	var matchesOrNot = false;
	var isAssert = true;
	var pattern = this.pattern;
	var call = this.expression;
	var branchConfigs = assertOrVerifyMatchesOrNot(call, pattern, isAssert, matchesOrNot);
	return sendAndReceive(call, branchConfigs);
};

/**
 * Verify that the returned result does'nt match a regular expression.
 * (for getXXX)
 */
RegexpNotMatch.prototype.verify = function() {
	var matchesOrNot = false;
	var isAssert = false;
	var pattern = this.pattern;
	var call = this.expression;
	var branchConfigs = assertOrVerifyMatchesOrNot(call, pattern, isAssert, matchesOrNot);
	return sendAndReceive(call, branchConfigs);
};

////// variable assignment //////
/**
 * Assign the result to a given variable. For functions like storeText(), ...
 */
function assignToVariable(type, variableName, expression) {
	variableName = replaceFlaggedPxLiteralWithActualValue(variableName);
	var result = "" +
	"# store (selenium): " + variableName + " = " + expression.toLine() + "\n" +
	expression.send() + "\n" +
	options['receiver'] + ".receive(value = '" + variableName + "')\n";

	result += variableName + " = value('" + variableName + "')\n";

	result += "log('" + variableName + " = %s' % " + this.variableName(variableName) + ")";
	return result;
}

////// waitForXXX //////
/**
 * Sends waitForXXX commands and receives the result.
 * ATTENTION: This is not stuff like waitForCondition(), where Selenium will wait. This waitForXXX will repeatedly
 * send the same selenium command (like isEditable()) and check whether the response matches.
 * A Testerman timer is set up which will wait for $this.waitForSeconds seconds before stopping the loop.
 * Builds the following alt structure
 * alt([
 * 	[ sel.RECEIVE(template = str("1234")),
 * 		#pass
 * 	],
 * 	[ sel.RECEIVE(template = any_or_none()),
 * 		lambda: t_sleepTimer.start(),
 * 		lambda: REPEAT,
 * 	],
 * 	[ t_sleepTimer.TIMEOUT, # 1 sec
 * 		lambda: sel.send(["getValue", "id=hw_id_ajax"]),
 * 		lambda: REPEAT,
 * 	],
 * 	[ t_watchdogTimer.TIMEOUT, # wait this.waitForSeconds before finally fail
 * 		lambda: self.setverdict('fail'),
 * 		lambda: log('qsdfqsdf'),
 * 		#lambda: RETURN,
 * 	],
 * ])
 */
function waitFor(expression) {
	var isAssert = false; // don't stop test, repeat instead
	if (Equals.prototype.isPrototypeOf(expression) || NotEquals.prototype.isPrototypeOf(expression)) {
		var pattern = expression.e1;
		var call = expression.e2;
		var equalsOrNot = (expression.negative ? false : true);
		var branchConfigs = assertOrVerifyEqualsOrNot(call, pattern, isAssert, equalsOrNot);
	} else if (RegexpMatch.prototype.isPrototypeOf(expression) || RegexpNotMatch.prototype.isPrototypeOf(expression)) {
		var pattern = expression.pattern;
		var call = expression.expression;
		var matchesOrNot = (expression.negative ? false : true);
		var branchConfigs = assertOrVerifyMatchesOrNot(call, pattern, isAssert, matchesOrNot);
	} else { // isXXX
		var call = expression;
		var trueOrFalse = (expression.negative ? false : true);
		var branchConfigs = assertOrVerifyTrueOrFalse(call, isAssert, trueOrFalse);

	}

	// we now have to alt branches, one with the "pass" template, and the other with the "fail" template
	// the idea is to replace the "fail" template with the start of the sleepTimer and add a 3rd branch
	// for receiving the timeout event of the sleepTimer. This branch will then resend the msg.
	// replace "false" temlplate (the message we did'nt want to receive) with sleep timer
	var timerSleep = getTestermanTimerVariable();
	var indexFailedBranch = 0;
	while (indexFailedBranch < branchConfigs.length && branchConfigs[indexFailedBranch]['verdict'] != failVerdict) {
		indexFailedBranch++;
	}
	branchConfigs[indexFailedBranch]['verdict'] = null;
	branchConfigs[indexFailedBranch]['repeat'] = true;
	branchConfigs[indexFailedBranch]['logMessage'] = null;
	branchConfigs[indexFailedBranch]['timer'] = timerSleep;
	branchConfigs[indexFailedBranch]['timerShouldStart'] = true;
	// resend selenese one sleep timer times out
	branchConfigSleepTimeout = {};
	branchConfigSleepTimeout['timer'] = timerSleep;
	branchConfigSleepTimeout['timerTimeoutIsBranchCondition'] = true;
	branchConfigSleepTimeout['repeat'] = true;
	branchConfigSleepTimeout['sendExpressionAgain'] = true;
	branchConfigs.push(branchConfigSleepTimeout);

	// the last branch is for the overall timeout (in case the SUT doesn't change at all)
	// watchdog for timeout
	var timerWatchdog = getTestermanTimerVariable();
	var branchConfigWatchdog = {};
	branchConfigWatchdog['timer'] = timerWatchdog;
	branchConfigWatchdog['logMessage'] = "Waiting for " + call.toLine() + " timed out!";
	branchConfigWatchdog['verdict'] = failVerdict;
	branchConfigWatchdog['timerTimeoutIsBranchCondition'] = true;
	branchConfigWatchdog['abortOnMatch'] = true;
	branchConfigWatchdog['explicitReturn'] = true; // make sure we get really outta here
	branchConfigs.push(branchConfigWatchdog);

	var result = "" +
	"# " + timerSleep + " is used to wait a litte before the next send()\n" +
	timerSleep + " = Timer(1, '" + timerSleep + "')\n" +
	"# " + timerWatchdog + " is the local watchdog (see branch conditions in next alt)\n" +
	timerWatchdog + " = Timer(" + this.waitForSeconds + ", '" + timerWatchdog + "')\n" +
	timerWatchdog + ".start()\n" +
	"";

	result += sendAndReceive(call, branchConfigs);

	return result;
}

/**
 * Print a message, Testerman-style.
 */
function echo(message) {
	return "log(" + xlateArgument(message) + ")";
}

// Sometimes expression is only a call, sometimes it's the call + alt statement. Hence we have to take care of both cases
/*
 * Convert a selenium command into a Python expression. We have to fool the API here. $expression can be
 * a) a "normal" selenium command without any feedback (like click()); or
 * b) a string containing the converted expression into Testerman code and the following alt conditions.
 * In case a) we have to convert the expression to Testerman/python code; in case b) we don't do nothing as the expression has already been parsed.
 * See chrome://selenium-ide/content/formats/remoteControl.js for more information
 */
function statement(expression) {
	if (expression.send) {
		return expression.send();
	} else {
		return expression;
	}
}

//credit goes to the Python-formatter
function nonBreakingSpace() {
    return "u\"\\u00a0\"";
}

//credit goes to the Python-formatter
function formatComment(comment) {
	return comment.comment.replace(/.+/mg, function(str) {
			return "# " + str;
		});
}

//credit goes to the Python-formatter
string = function(value) {
	value = value.replace(/\\/g, '\\\\');
	value = value.replace(/\"/g, '\\"');
	value = value.replace(/\r/g, '\\r');
	value = value.replace(/\n/g, '\\n');
	var unicode = false;
	for (var i = 0; i < value.length; i++) {
		if (value.charCodeAt(i) >= 128) {
			unicode = true;
		}
	}
	return (unicode ? 'u' : '') + '"' + value + '"';
};

/**
 * TODO?: We use Python's str() to convert the parameter. If it's an integer and no conversion
 * is done, template matching doesn't seem to work (e.g. Selenium returns a string but the template
 * expects an integer). Another workaround would be to define parameters always as string, like
 * #<parameter name="PX_... type="string" ... (see printDynamicPxParameters() in chrome://testerman-formatters/content/formats/options.js)
 * It seemed to be more flexible to set the right type at the beginning (for manually coding after export).
 */
this.variableName = function(value) {
	return replacePxLiteralWithActualValueAndConvertToString(value);
}

// TODO:
// In Testerman, the received message is directly compared to a given template. It is not possible (afaik) to parse the message before comparison.
// Hence, we cannot "join" a received array. Pattern matching will not work. See adaptPatternForGetAllXXXSelenese() for a work around.
// In the meanwhile, do nothing but alert the user.
function joinExpression(expression) {
	//alert("Oops, I'm sorry, I cannot handle array-like messages :(\nPlease adapt the generated output from '" + expression.toLine() + "' to your requirements");
	return expression;
}

/*
 * Pause the execution. This will set up a timer and block until it timeouts.
 */
function pause(milliseconds) {
	var seconds = Math.round(milliseconds / 1000);
	var timer = getTestermanTimerVariable();
	return '' + 
	"#sleep for " + seconds + " seconds (selenium command: pause())\n" +
	timer + ' = Timer(' + seconds + ', \'' + timer + '\')\n' +
	timer + '.start()\n' +
	timer + '.timeout() #blocking' +
	'';
}

/**
 * Generate the header (before selenium commands)
 */
this.formatHeader = function(testCase) {
	// before dump: preliminary checks about the seleneses
	warnAboutGetAllXXXSelenese(testCase);
	countVerifyOrAssertStatements(testCase);//count all verifyXXX() and assertXXX() in this testcase

	var formatLocal = testCase.formatLocal(this.name);
	var header = (options.getHeader ? options.getHeader(testCase) : options.header);
	var parsedHeader = parseTextWithOptions(header, testCase); 
	this.lastIndent = indents(parseInt(options.initialIndents, 10));
	formatLocal.header = parsedHeader;
	return formatLocal.header;
}

/**
 * Generate the footer (everything after selenium commands).
 */
this.formatFooter = function(testCase) {
	var formatLocal = testCase.formatLocal(this.name);
	var footer = (options.getFooter ? options.getFooter(testCase) : options.footer);
	formatLocal.footer = parseTextWithOptions(footer, testCase);
	return formatLocal.footer;
}

this.parse = function(testCase, source) {
	var reSelenese = /^#selenese:(.*?)\|(.*)\|(.*)/;
	var reDescription = /# <description>(.*):\s(.*)<\/description>/;
	var reSeleniumBaseURL = /# <parameter name=\"PX_SELENIUM_SERVER_URL\" default=\"(.*)\" type=\"string\"><!\[CDATA\[\]\]><\/parameter>/;

	// make sure test case is empty (this is in fact copied an pasted, not sure we need this)
	testCase.header = null;
	testCase.footer = null;
	testCase.formatLocal(this.name).header = "";
	testCase.formatLocal(this.name).footer = "";
	testCase.commands = [];

	var reader = new LineReader(source);
	var line;
	var dummyTitle = "";
	while ((line = reader.read()) != null) {
		var m = reSelenese.exec(line);
		var command = new Command();
		command.type = "command";
		if (m) {
			var c = m[1].trim();
			var t = m[2].trim();
			var v = m[3].trim();
			if (c == "comment") {
				command.type = "comment";
				command.comment = t;
			} else if (c == "line") {
				command.type = "line";
				command.line = t;

			} else { // "normal" selenese
				command.command = c;
				command.target = t;
				command.value = v;
			}
			testCase.commands.push(command);
		}
		m = reDescription.exec(line);
		if (m) {
			dummyTitle = m[1];
			testCase.description = m[2];
		}
		m = reSeleniumBaseURL.exec(line);
		if (m) {
			testCase.setBaseURL(m[1]);
		}

		if (hooks.extractFromThisLineDuringTestCaseParse) {
			hooks.extractFromThisLineDuringTestCaseParse(testCase, line);
		}
	}

	// create dummy test and for comparing with original file
	var dummyTestCase = testCase;
	dummyTestCase.title = dummyTitle;
	var newSource = format(dummyTestCase);

	// alert if something went wrong
	if (testCase.commands.length == 0) {
		alert("No command found. Is this really an ats file?");
	} else {
		if (testCase.baseURL == "") {
			alert("Could not identify base URL. Make sure to set the right URL in the Base URL address bar");
		}
		if (newSource.length != source.length) {
			alert("ATTENTION: The test case exported from this source will not be identical to the original file! Either you use a another version of the Testerman Formatter, changed it's options or SOMEONE MODIFIED THE TEST BY HAND! Make sure to have a backup copy.");
		}
	}
}

/////////////////////////////////////////
// auxiliary functions for selenium calls
/////////////////////////////////////////

/**
 * Return a branch for the alt statement in Testerman.
 * Builds something like:
 *	[ sel.RECEIVE(template = any()),
 *		lambda: self.setverdict('fail'),
 *		lambda: log('logmsg'),
 *		lambda: stop(),
 *	],
 * The given branchConfig is used to setup the different conditions and lambdas.
 * See the code for possible options.
 */
function getAltBranch(expression, branchConfig) {
	function lambda() { return indents(2) + "lambda: " };
	var template = branchConfig['template'];
	var verdict = branchConfig['verdict'];
	var log = branchConfig['logMessage'];
	var abort = branchConfig['abortOnMatch'];
	var repeat = branchConfig['repeat'];
	var explicitReturn = branchConfig['explicitReturn'];
	var sendExpressionAgain = branchConfig['sendExpressionAgain'];
	var timer = branchConfig['timer'];
	var timerShouldStart = branchConfig['timerShouldStart'];
	var timerTimeoutIsBranchCondition = branchConfig['timerTimeoutIsBranchCondition'];

	var branchCondition = options.receiver + ".RECEIVE(" + (template ? "template = " + template : "") + ")";
	branchCondition = (timerTimeoutIsBranchCondition ? timer + ".TIMEOUT" : branchCondition); // change condition if we have a timer instead of a RECEIVE

	var result = indents(1) + "[ " + branchCondition + ",\n" +
	(verdict ? lambda() + "self.setverdict(" + verdict + "),\n" : "") +
	(log ? lambda() + "log('" + log + "'),\n" : "") +
	(abort ? lambda() + "stop(),\n" : "") +
	(timerShouldStart ? lambda() + timer + ".start(),\n" : "") +
	(sendExpressionAgain ? lambda() + expression.send() + ",\n" : "") +
	(repeat ? lambda() + "REPEAT,\n" : "") +
	(explicitReturn ? lambda() + "RETURN,\n" : "") +
	indents(1) + "],\n" +
	"";
	return result;
}
/**
 * Return a port.send() and the following alt statement.
 * This is the most generic function.
 * Builds something like this:
 *	sel.send(["getText", "locator"])
 *	alt([
 *		[ sel.RECEIVE(template = "pattern"),
 *			lambda: self.setverdict('pass'),
 *			lambda: log('logmsg'),
 *		],
 *		[ sel.RECEIVE(template = any()),
 *			lambda: self.setverdict('fail'),
 *			lambda: log('logmsg'),
 *		],
 *	])
 * The parameter branchConfigs is an array of branch configurations.
 */
function sendAndReceive(expression, branchConfigs) {
	var result = "" +
	expression.send() + "\n" +
	"alt([\n";
	for (var i = 0; i < branchConfigs.length; i++) {
		result += getAltBranch(expression, branchConfigs[i]);
	}
	result += "" +
	//'#' + indents(1) + '[ t_timer.TIMEOUT,\n' +
	//'#' + indents(2) + 'lambda: log("Timer timeout!"),\n' +
	//'#' + indents(2) + 'lambda: self.setverdict("fail"),\n' +
	//'#' + indents(1) + '],\n' + 
	'])\n';
	return result;
}


/**
 * Print Testerman's pattern() function.
 * This fucntion is called when matching against regexp. The template gets surrrounded by pattern(' + actual template + ')
 * See chrome://pythonformatters@seleniumhq.org/content/format/python2-rc.js for more details.
 */
function testermanPattern(pattern) {
	var tmp = pattern;
	tmp = tmp.replace(/\"\s\+\s/g, "' + ").replace(/\s\+\s\"/g, " + '").replace(/^\"/, "'").replace(/\"$/, "'");
	if (tmp.match(/\"/)) {// if we still have double quotes (after replacing those before and after str() [...qsdfsqdf" + str() + "sqdfqsdf...], do not use regexp)
		//impertinently stolen from the python formatter
		pattern = pattern.replace(/\\/g, "\\\\");
		pattern = pattern.replace(/\"/g, '\\"');
		pattern = pattern.replace(/\n/g, '\\n');
		return '"' + pattern + '"';
	}

	if (pattern[0] != '"') {
		pattern = '"" + ' + pattern;
	}
	return "pattern(r" + pattern + ")";
}


/**
 * Build branch configuration for assert/verfiy.
 * This function is called for isXXX selenese, which means that expected return value is a boolean.
 * $trueOrFalse tells us the value we exptect to pass the test.
 * If $isAssert the test will abort on failure.
 */
function assertOrVerifyTrueOrFalse(expression, isAssert, trueOrFalse) {
	var pass = (isLastVerifyOrAssertStatement() ? passVerdict : null);
	var template = (trueOrFalse ? "True" : "False");

	// the matching template
	var branchConfig1 = {};
	branchConfig1['template'] = template;
	branchConfig1['verdict'] = pass;
	branchConfig1['logMessage'] = expression.toLine() + " == " + template + " -> Good!"; //make sure there is no empty branch (at least, do a log)
	branchConfig1['abortOnMatch'] = false;
	// the template in case we don't match
	var branchConfig2 = {};
	branchConfig2['template'] = templateAny;
	branchConfig2['verdict'] = failVerdict;
	branchConfig2['abortOnMatch'] = isAssert;
	branchConfig2['logMessage'] = expression.toLine() + " != " + template + " -> Bad!";
	// put things together
	var branchConfigs = new Array();
	branchConfigs[0] = branchConfig1;
	branchConfigs[1] = branchConfig2;
	return branchConfigs;
}

/**
 * Build branch configurations for assert/verfiy.
 * This function is called for getXXX selenese, which means that expected return value is $pattern.
 * $equalsOrNot tells us whether we want the pattern to be found or not
 * If $isAssert the test will abort on failure.
 */
function assertOrVerifyEqualsOrNot(expression, pattern, isAssert, equalsOrNot) {
	var pass = (isLastVerifyOrAssertStatement() ? passVerdict : null);
	patternForLog = getLogMsgFromPxConvertedToString(pattern);
	pattern = (isGetAllXXXSelenese(expression) ? adaptPatternForGetAllXXXSelenese(pattern) : pattern); // make an array if necessary

	// the matching template
	var branchConfig1 = {};
	branchConfig1['template'] = pattern;
	branchConfig1['verdict'] = (equalsOrNot ? pass : failVerdict);
	branchConfig1['abortOnMatch'] = (equalsOrNot ? false : isAssert); // stop only if notEqal AND isAssert
	branchConfig1['logMessage'] = (equalsOrNot ? expression.toLine() + " == " + patternForLog + " -> Good!" : expression.toLine() + " == " + patternForLog + " -> Bad!");
	// the template in case we don't match
	var branchConfig2 = {};
	branchConfig2['template'] = templateAny;
	branchConfig2['verdict'] = (equalsOrNot ? failVerdict : pass);
	branchConfig2['abortOnMatch'] = (equalsOrNot ? isAssert : false); // stop only if Eqal AND isAssert
	branchConfig2['logMessage'] = (equalsOrNot ? expression.toLine() + " != " + patternForLog + " -> Bad!" : expression.toLine() + " != " + patternForLog + " -> Good!");
	// put things together
	var branchConfigs = new Array();
	branchConfigs[0] = branchConfig1;
	branchConfigs[1] = branchConfig2;
	return branchConfigs;
}

/**
 * Build branch configuration for assert/verfiy.
 * This function is called for getXXX selenese using regular expressions, which means that expected return value is $pattern.
 * $matchesOrNot tells us whether we want the pattern to be found or not
 * If $isAssert the test will abort on failure.
 */
function assertOrVerifyMatchesOrNot(expression, pattern, isAssert, matchesOrNot) {
	var pass = (isLastVerifyOrAssertStatement() ? passVerdict : null);
	pattern = replaceFlaggedPxLiteralWithActualValueAndConvertToSeleniumString(pattern); // selenium doesn't parse stuff after regexp:this_stuff_here, so we do it
	patternForLog = getLogMsgFromPxConvertedToString(pattern); // create the appropriate log message
	pattern = testermanPattern(pattern); // convert into "pattern(qsdfqsfd)"
	pattern = (isGetAllXXXSelenese(expression) ? adaptPatternForGetAllXXXSelenese(pattern) : pattern); //make an array if necessary

	// the matching template
	var branchConfig1 = {};
	branchConfig1['template'] = pattern;
	branchConfig1['verdict'] = (matchesOrNot ? pass : failVerdict);
	branchConfig1['abortOnMatch'] = (matchesOrNot ? false : isAssert);
	branchConfig1['logMessage'] = (matchesOrNot ? expression.toLine() + " == regexp:" + patternForLog + " -> Good!" : expression.toLine() + " == regexp:" + patternForLog + " -> Bad!");
	// the template in case we don't match
	var branchConfig2 = {};
	branchConfig2['template'] = templateAny; //(trueOrFalse ? "True" : "False");
	branchConfig2['verdict'] = (matchesOrNot ? failVerdict : pass);
	branchConfig2['abortOnMatch'] = (matchesOrNot ? isAssert : false);
	branchConfig2['logMessage'] = (matchesOrNot ? expression.toLine() + " != regexp:" + patternForLog + " -> Bad!" : expression.toLine() + " != regexp:" + patternForLog + " -> Good!");
	// put things together
	var branchConfigs = new Array();
	branchConfigs[0] = branchConfig1;
	branchConfigs[1] = branchConfig2;
	return branchConfigs;
}

/**
 * Get a timer variable.
 * Counts up timerCount to ensure unique variable names.
 */
function getTestermanTimerVariable() {
	return 't_timer' + ++timerCount;
}

/**
 * Check whether a given name is a PX_XXX parameter
 * "PX_MY_PARA" -> true
 * "myvar" -> false
 */
function variableNameIsPxParameter(name) {
	return (name != null && name.match("^" + pxParameterRegExp + "$"));
}

/**
 * Send the command to the port.
 * Returns something like:
 * sel.send(["isEditable", "target"])
 * This function is this formatter's equivalent for CallSelenium.prototype.toString().
 */
CallSelenium.prototype.send = function() {
	var result = '';
	if (this.modifyCall) {
		result = this.modifyCall();
	}
	if (result == '') {
		if (options.receiver) {
			result = options.receiver + '.';
		}
		result += 'send([';
		result += "\"" + this.message + "\"";
		if (this.args.length > 0) {
			for (var i = 0; i < this.args.length; i++) {
				result += ", " + this.args[i];
			}
		}
		result += '])';
	}
	return result;
}

/**
 * Return the selenes as a one-liner
 * ex: verifyText("locator_id", "mypattern")
 */
CallSelenium.prototype.toLine = function() {
	var out = this.message + "(";
	for (var i = 0; i < this.args.length; i++) {
		out += this.args[i];
		if (i < this.args.length - 1) {
			out += ', ';
		}
	}
	out += ")";
	//make sure we don't get problems when we use this statement for logging
	out = out.replace(/[\"\']/g, '');
	return out;
}

/**
 * Check the state of the assertOrVerifyStatementCounter counter.
 * Decrements the counter and returns true if counter is zero.
 * The caller knows then that "it" is the last assert/verify.
 *
 */
function isLastVerifyOrAssertStatement() {
	assertOrVerifyStatementCounter--;
	return (assertOrVerifyStatementCounter == 0);
}

/**
 * Count assert() and veriy() commands.
 * This function increments the assertOrVerifyStatementCounter counter for each assertXXX()
 * and each verifyXXX(). We use the counter later to dump a setverdict('pass') only
 * at the very last check.
 */
function countVerifyOrAssertStatements(testCase) {
	assertOrVerifyStatementCounter = 0; //when running multiple exports and still having bugs ;)
	var commands = testCase.commands;
	for (var i = 0; i < commands.length; i++) {
		var command = commands[i];
		if (command.getDefinition) {
			var def = command.getDefinition();
			// if def -> no comment, if def.isAccessor -> isXXX or getXXX, if store -> no verdicts for storeXXX
			if (def && def.isAccessor && ! command.command.match(/^store/)) {
				assertOrVerifyStatementCounter++;
			}
		}
	}
}

/**
 * Replace the named Testerman's px parameter with it's actual value
 * The given argument may contain be a PX_XXX parameter (matched by it's name). Instead
 * of using only it's name, replace it with PX_XXX to access it's actual
 * value in Testerman.
 * This function used to wrap get_variable() around, it is probably legacy code today
 * ex: PX_XXX --> PX_XXX
 * ex: PX_XXX:42 --> PX_XXX
 */
function replacePxLiteralWithActualValue(value) {
	// what arrives here is either "PX_XXX" or "PX_XXX:42" (both are declared as existing variables)
	// we only want to have PX_XXX
	var re = new RegExp("^(" + pxParameterRegExp + ")(:.*)?$");
	var m = re.exec(value);
	if (m) {
		value = m[1];
	}
	return value;
}
/**
 * ${PX_XXX:42} --> PX_XXX
 * ${PX_XXX} --> PX_XXX
 */
function replaceFlaggedPxLiteralWithActualValue(value) {
	var re = new RegExp("^\\$\{(" + pxParameterRegExp + ")(:.*)?\}$");
	var m = re.exec(value);
	if (m) {
		return replacePxLiteralWithActualValue(m[1]);
	}
	return value;
}

/**
 * Replace the named Testerman's px parameter with it's actual value.
 * The given argument may contain be a PX_XXX parameter (matched by it's name) still flagged via
 * ${NameOfPxParam}. Replace it with str(PX_XXX) to access it's actual
 * value in Testerman and convert it to a string.
 * ex: ${PX_XXX} --> str(PX_XXX)
 * ex: ${PX_XXX:42} --> str(PX_XXX)
 * ex: This is the ${PX_XXX:42} param --> "This is the " + str(PX_XXX) + "param"
 */
function replaceFlaggedPxLiteralWithActualValueAndConvertToSeleniumString(s) {
	var re = new RegExp("^(.*)?\\$\{(" + pxParameterRegExp + ")(:.*)?\}(.*)?$");
	var m = re.exec(s);
	if (m) {
		var result = "";
		result += (m[1] ? '"' + m[1] + '" + ': '');
		result += replacePxLiteralWithActualValueAndConvertToString(m[2]);
		result += (m[4] ? ' + "' + m[4] + '"': '');
		return result;
	}
	return '"' + s + '"';
}

/**
 * Replace the named Testerman's px parameter with it's actual value
 * The given argument may contain be a PX_XXX parameter (matched by it's name).
 * Convert it into a Python string.
 * ex: PX_XXX --> str(PX_XXX)
 * ex: PX_XXX:42 --> str(PX_XXX)
 */
function replacePxLiteralWithActualValueAndConvertToString(value) {
	return "str(" + replacePxLiteralWithActualValue(value) + ")";
}
/**
 * Create a log statement from a px parameter.
 * This function is used to comment the verdict after an assert/verdict.
 * Takes a value (containing maybe a px param) and converts a to a suitable string.
 * (this function supposes we are "inside" a string using \' as delimiter
 * ex: "ssss" --> "ssss"
 * ex: "ssss" + str(('PX_XXX')) + "ssss" --> "ssss' + str(('PX_XXX')) + 'ssss" [using PX_XXX]
 * ex: "ssss" + str(('PX_XXX')) --> "ssss' + str(('PX_XXX')) + ' [using PX_XXX]
 * ex: str(('PX_XXX')) + "ssss" --> ' + str(('PX_XXX')) + 'ssss" [using PX_XXX]
 */
function getLogMsgFromPxConvertedToString(value) {
	// "qdsf" + str(...) + "qdf" --> "qdsf' + str(...) + 'qsdf"
	value = value.replace(/\"\s\+\s([^\"])/g, "' + $1"); 
	value = value.replace(/([^\"])\s\+\s\"/g, "$1 + '");

	// str(...) --> ' + str(...) + ' (no text before and/or after the px_xxx)
	value = value.replace(/^([^\"])/, "\"' + $1");
	value = value.replace(/([^\"])$/, "$1 + '\"");

	// "dd"' + str(('PX_XXX')) + '"sfd" --> "dd"' + str(('PX_XXX')) + '"sfd" [using PX_XXX]
	var re = new RegExp("(.*)(" + pxParameterRegExp + ")(\\S+)(.*)");
	var m = re.exec(value);
	if (m) {
		//value = m[1] + m[2] + m[3] + " + ' [" + m[2] + "]'" + m[4];
		value += " [using " + m[2] + "]";
	}

	return value;
}

/**
 * Checkh whether this call is a getAllXXX() selenese.
 * Returns true, if this selenese begins with "getAll..."
 * This matches for stuff like getAllLinks, getAllButtons, ...
 */
function isGetAllXXXSelenese(call) {
	return (call.message.match(/^getAll(.+)$/));
}

/**
 * Support selenese which return an array
 * TODO: This is NOT the same way the other formatters work.
 * They join the returned array, before trying to match it against
 * a pattern, python example: try: self.assertEqual("disconnect", ','.join(sel.get_all_links()))
 * This means that they match against the whole string. In Testerman,
 * we can not execute any operation on the returned message (at least
 * not without a codec). Therefore, we build an array around the actual
 * pattern to match against a return array. In consequence, the pattern
 * matching takes place against a *single* value of the array.
 * The user gets warned.
 */
function adaptPatternForGetAllXXXSelenese(pattern) {
	return "[any_or_none(), " + pattern + ", any_or_none()]";
}

function warnAboutGetAllXXXSelenese(testCase) {
	var commands = testCase.commands;
	for (var i = 0; i < commands.length; i++) {
		var command = commands[i];
		if (command.command.match(/^(assert|verify|waitFor)All(.+)$/)) {
			alert('Support for "' + command.command + '(pattern)" (command #' + (i+1) + ') is experimental! Please check the generated code.');
		}
	}
}
/**
 * Javascript trim()
 */
String.prototype.ltrim=function(){return this.replace(/^\s+/,'');}
String.prototype.rtrim=function(){return this.replace(/\s+$/,'');}
String.prototype.trim=function(){return this.ltrim().rtrim();}

