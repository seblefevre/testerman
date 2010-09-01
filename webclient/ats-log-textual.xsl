<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="ats">

<!-- header -->
<html xmlns="http://www.w3.org/1999/xhtml">
  
<head>
	<title><xsl:value-of select="/ats//@id" /></title>
	<link rel="stylesheet" type="text/css" href="/static/testerman.css" />
</head>
<body>
	<div id="page">
		<div id="banner">
			<div id="header">
				<a id="logo" href="/"><img src="/static/testerman-logo.png" alt="testerman" /></a>
			</div>
		</div>
		<div id="main">
			<div id="content" class="wiki">
				<div class="wikipage">

<!-- the interesting part -->
<p>
Test Execution Results for ATS: <xsl:value-of select="/ats//@id" />.
</p>
<h1>Test Cases Summary</h1>

<table>
	<xsl:for-each select="testcase">
	<tr>
		<td><xsl:value-of select="@id" /></td>
		<td><xsl:value-of select="@verdict" /></td>
	</tr>
	</xsl:for-each>
</table>

<p></p>
<h1>Test Cases Details</h1>

<xsl:for-each select="testcase">
<!--	<xsl:call-template name="testcase" /> -->
	<h2><xsl:value-of select="@id" /></h2>
	<table class="testcase">
	<tr>
		<td>Result: <xsl:value-of select="@verdict" /></td>
		<td>Description: <xsl:value-of select="testcase-stopped" /></td>
	</tr>
	<tr><td colspan="2">Execution summary (User logs): <br />
	<p>
	<xsl:for-each select="user">
		<xsl:value-of select="@timestamp" /> <xsl:value-of select="." /><br />
	</xsl:for-each>
	</p>
	</td></tr>
	<tr><td colspan="2">Analysis (Details): <br />
	<p>
	<xsl:for-each select="*[not(name()='internal')]">
		<xsl:value-of select="@timestamp" /> 
		<!-- choice according to the event/element -->
		<xsl:choose>
			<xsl:when test="name()='testcase-started'">
				Testcase Started.
			</xsl:when>
			<xsl:when test="name()='testcase-stopped'">
				Testcase Stopped.
			</xsl:when>
			<xsl:when test="name()='verdict-updated'">
				Verdict set to '<xsl:value-of select="@verdict" />'.
			</xsl:when>
			<xsl:when test="name()='user'">
				<i><xsl:value-of select="." /></i>
			</xsl:when>
		</xsl:choose>
		<br />
	</xsl:for-each>
	</p>
	</td></tr>
	</table>
</xsl:for-each>


<!-- footer -->
				</div>
			</div>
		</div>
	</div>
</body>
	 
</html>

</xsl:template>

<xsl:template name="testcase">
	<h2><xsl:value-of select="@id" /></h2>
	<p>Result: <xsl:value-of select="@verdict" /></p>
	<p>User Logs: </p>
	<xsl:for-each select="user">
		<xsl:value-of select="@timestamp" /> <xsl:value-of select="." /><br />
	</xsl:for-each>
</xsl:template>

</xsl:stylesheet>
