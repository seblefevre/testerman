<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="ats">

<!-- header -->
<html xmlns="http://www.w3.org/1999/xhtml">
 
<script type="text/javascript">
function expandCollapse(id) {
var element = document.getElementById(id);
element.style.display = (element.style.display != "block" ? "block" : "none"); 
}
</script>
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

<table class="summary">
	<tr><th>Test Case ID</th><th>Verdict</th></tr>
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
	<table class="testcase-userlog-table">
	<xsl:for-each select="user">
		<tr><td class="time"><xsl:value-of select="@timestamp" /></td><td><xsl:value-of select="." /></td></tr>
	</xsl:for-each>
	</table>

	</td></tr>
	<tr><td colspan="2">Analysis (Details): <br />
	
	<!-- analysis textual view -->
	<!-- choice according to the event/element -->
	<table class="testcase-analysis-table">
	<xsl:for-each select="*[not(name()='internal')]">
	
		<xsl:variable name='logEntryId' select='concat(@class, @timestamp)' />
		<tr>
		<td class="time">
		<xsl:value-of select="@timestamp" /> 
		</td>
		<td>
		<xsl:value-of select="@class" /> 
		</td>
		<td>
		<xsl:attribute name="class"><xsl:value-of select="name()" /></xsl:attribute>
		<xsl:choose>
			<xsl:when test="name()='testcase-started'">
				TestCase <xsl:value-of select="@id" />(<xsl:value-of select="." />) started
			</xsl:when>
			<xsl:when test="name()='testcase-stopped'">
				TestCase <xsl:value-of select="@id" /> stopped, final verdict is <xsl:value-of select="@verdict" />
			</xsl:when>
			<xsl:when test="name()='verdict-updated'">
				Verdict updated to <xsl:value-of select="@verdict" /> on TC <xsl:value-of select="@tc" />
			</xsl:when>
			<xsl:when test="name()='user'">
				<xsl:value-of select="." />
			</xsl:when>

			<xsl:when test="name()='tc-created'">
				Test Component <xsl:value-of select="@id" /> created
			</xsl:when>

			<xsl:when test="name()='timer-started'">
				Timer <xsl:value-of select="@id" /> started (<xsl:value-of select="@duration" />) on TC <xsl:value-of select="@tc" />
			</xsl:when>
			<xsl:when test="name()='timer-stopped'">
				Timer <xsl:value-of select="@id" /> stopped on TC <xsl:value-of select="@tc" />
			</xsl:when>
			<xsl:when test="name()='timer-expiry'">
				Timer <xsl:value-of select="@id" /> timeout on TC <xsl:value-of select="@tc" />
			</xsl:when>

			<xsl:when test="name()='timeout-branch'">
				Timeout match for Timer <xsl:value-of select="@id" />
			</xsl:when>
			<xsl:when test="name()='done-branch'">
				Done match for TC <xsl:value-of select="@id" />
			</xsl:when>

			<xsl:when test="name()='message-sent'">
				<xsl:value-of select="@from-tc" />.<xsl:value-of select="@from-port" /> --&gt; <xsl:value-of select="@to-tc" />.<xsl:value-of select="@to-port" />
				<!-- insert here a way to expand to the message -->
			</xsl:when>

			<xsl:when test="name()='template-match'">
				Template match on port <xsl:value-of select="@tc" />.<xsl:value-of select="@port" />
				<!-- insert here a way to expand the message and the template -->
			</xsl:when>
			<xsl:when test="name()='template-mismatch'">
				Template mismatch on port <xsl:value-of select="@tc" />.<xsl:value-of select="@port" />
				<!-- insert here a way to expand the message and the template -->
			</xsl:when>

			<xsl:when test="name()='tc-started'">
				PTC <xsl:value-of select="@id" /> started with Behaviour <xsl:value-of select="@behaviour" />
			</xsl:when>
			<xsl:when test="name()='tc-stopped'">
				PTC <xsl:value-of select="@id" /> stopped, local verdict is <xsl:value-of select="@verdict" />
			</xsl:when>

			<xsl:when test="name()='system-sent'">
				<xsl:value-of select="@tsi-port" /> &gt;&gt; :
					<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;system-sent-message-', $logEntryId, '&quot;)')" />
					</xsl:attribute>
					<xsl:value-of select="label" />
					</a>
				<!-- insert here a way to expand to the payload -->
				<div class='system-payload'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('system-sent-message-', $logEntryId)" /> </xsl:attribute>
					<xsl:value-of select="payload" />
<!--					<xsl:value-of select="replace(payload, '#0A;', '&lt;br /&gt;')" /> -->
				</div>
			</xsl:when>

			<xsl:when test="name()='system-received'">
				<xsl:value-of select="@tsi-port" /> &lt;&lt; : 
					<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;system-received-message-', $logEntryId, '&quot;)')" />
					</xsl:attribute>
					<xsl:value-of select="label" />
					</a>
				<!-- insert here a way to expand to the payload -->
				<div class='system-payload'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('system-received-message-', $logEntryId)" /> </xsl:attribute>
					<xsl:value-of select="payload" />
<!--					<xsl:value-of select="replace(payload, '#0A;', '&lt;br /&gt;')" /> -->
				</div>
			</xsl:when>


		</xsl:choose>
		</td>
		</tr>
		
	</xsl:for-each>
	</table>
	<!-- analysis textual view - end -->

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
