/*
 * Format for Selenium Webdriver via Testerman ATS scripts
 */

var subScriptLoader = Components.classes["@mozilla.org/moz/jssubscript-loader;1"].getService(Components.interfaces.mozIJSSubScriptLoader);
subScriptLoader.loadSubScript('chrome://testerman-formatters/content/formats/testerman-rc.js', this);


/*
 * Overwrite some options from options-rc.js
 */
this.options['tsiPort'] = 'selenium_wd';
this.options['probeType'] = 'selenium.webdriver';
this.options['probeUri'] = 'probe:selenium.webdriver';



/*
 * Rename some methods to correctly represent Webdriver API.
 * See CallSelenium.prototype.send() in testerman-rc.js.
 */
CallSelenium.prototype.modifyCall = function() {
	if (this.message == "open") {
		this.message = "get";
		var url = this.args[0];
		if (url.substring(1,8) != "http://" && url.substring(1,9) != "https://") {
			url = "PX_SELENIUM_SERVER_URL + " + url;
		}
		this.args[0] = url;
	} else if (this.message == "type") {
		this.message = "send_keys";
	} else if (this.message == "waitForPageToLoad") {
		return "# implicitely wait";
	}
	return '';
}
