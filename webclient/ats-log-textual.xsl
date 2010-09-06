<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="html" standalone="yes" version="1.0" encoding="UTF-8" indent="yes"/>

<xsl:template match="ats">

<!-- header -->
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title><xsl:value-of select="/ats//@id" /></title>
	<link rel="stylesheet" type="text/css" href="/static/testerman.css" />
	<script type="text/javascript">
function expandCollapse(id) {
var element = document.getElementById(id);
element.style.display = (element.style.display != "block" ? "block" : "none"); 
}
	</script>
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
Test Execution Results for ATS:
<a>
	<xsl:attribute name="href">
		/browser?/repository/<xsl:value-of select="/ats//@id" />
	</xsl:attribute>
	<xsl:value-of select="/ats//@id" />
</a>

</p>
<h1>Test Cases Summary</h1>

<table class="summary">
	<tr><th>Test Case ID</th><th>Verdict</th></tr>
	<xsl:for-each select="testcase">
	<tr>
		<td><a><xsl:attribute name="href">#<xsl:value-of select="@id" /></xsl:attribute><xsl:value-of select="@id" /></a></td>
		<td><xsl:value-of select="@verdict" /></td>
	</tr>
	</xsl:for-each>
</table>

<p></p>
<h1>Test Cases Details</h1>

<xsl:for-each select="testcase">
<!--	<xsl:call-template name="testcase" /> -->
	<a><xsl:attribute name="name"><xsl:value-of select="@id" /></xsl:attribute></a>
	<h2><xsl:value-of select="@id" /></h2>
	<table class="testcase">
	<tr>
		<td>Result: <xsl:value-of select="@verdict" /></td>
		<td>Description:
			<xsl:call-template name="break">
				<xsl:with-param name="text" select="testcase-stopped" />
			</xsl:call-template>
		</td>
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
	
		<xsl:variable name="logElementId" select="generate-id(.)" />
		<tr>
		<td class="time">
		<xsl:value-of select="@timestamp" /> 
		</td>
		<td>
		<xsl:value-of select="@class" /> 
		</td>
		<td>
		<xsl:choose>
			<xsl:when test="name()='testcase-started'">
				<span class="testcase-started">TestCase <xsl:value-of select="@id" />(<xsl:value-of select="." />) started</span>
			</xsl:when>
			<xsl:when test="name()='testcase-stopped'">
				<span class="testcase-stopped">TestCase <xsl:value-of select="@id" /> stopped, final verdict is <xsl:value-of select="@verdict" /></span>
			</xsl:when>
			<xsl:when test="name()='verdict-updated'">
				<span class="verdict-updated">Verdict updated to <xsl:value-of select="@verdict" /> on TC <xsl:value-of select="@tc" /></span>
			</xsl:when>
			<xsl:when test="name()='user'">
				<span class="user"><xsl:value-of select="." /></span>
			</xsl:when>

			<xsl:when test="name()='tc-created'">
				<span class="tc-created">Test Component <xsl:value-of select="@id" /> created</span>
			</xsl:when>

			<xsl:when test="name()='timer-started'">
				<span class="timer-started">Timer <xsl:value-of select="@id" /> started (<xsl:value-of select="@duration" />) on TC <xsl:value-of select="@tc" /></span>
			</xsl:when>
			<xsl:when test="name()='timer-stopped'">
				<span class="timer-stopped">Timer <xsl:value-of select="@id" /> stopped on TC <xsl:value-of select="@tc" /></span>
			</xsl:when>
			<xsl:when test="name()='timer-expiry'">
				<span class="timer-expiry">Timer <xsl:value-of select="@id" /> timeout on TC <xsl:value-of select="@tc" /></span>
			</xsl:when>

			<xsl:when test="name()='timeout-branch'">
				<span class="timeout-branch">Timeout match for Timer <xsl:value-of select="@id" /></span>
			</xsl:when>
			<xsl:when test="name()='done-branch'">
				<span class="done-branch">Done match for TC <xsl:value-of select="@id" /></span>
			</xsl:when>

			<xsl:when test="name()='message-sent'">
				<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;message-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					<span class="message-sent"><xsl:value-of select="@from-tc" />.<xsl:value-of select="@from-port" /> --&gt; <xsl:value-of select="@to-tc" />.<xsl:value-of select="@to-port" /></span>
				</a>
				<!-- insert here a way to expand to the payload -->
				<div class='message'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('message-', $logElementId)" /> </xsl:attribute>
					<xsl:call-template name="message">
						<xsl:with-param name="msg" select="message" />
					</xsl:call-template>
				</div>

			</xsl:when>

			<xsl:when test="name()='template-match'">
				<span class="template-match">Template match on port <xsl:value-of select="@tc" />.<xsl:value-of select="@port" /></span>
				<!-- insert here a way to expand the message and the template -->
				( <a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;message-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					message
				</a>
				 | 
				<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;template-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					template
				</a>
				 )

				<div class='message'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('message-', $logElementId)" /> </xsl:attribute>
					message: <xsl:call-template name="message">
						<xsl:with-param name="msg" select="message" />
					</xsl:call-template>
				</div>
				<div class='message'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('template-', $logElementId)" /> </xsl:attribute>
					template: <xsl:call-template name="message">
						<xsl:with-param name="msg" select="template" />
					</xsl:call-template>
				</div>

			</xsl:when>
			<xsl:when test="name()='template-mismatch'">
				<span class="template-mismatch">Template mismatch on port <xsl:value-of select="@tc" />.<xsl:value-of select="@port" /></span>
				<!-- insert here a way to expand the message and the template -->
				( <a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;message-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					message
				</a>
				 | 
				<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;template-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					template
				</a>
				 )

				<div class='message'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('message-', $logElementId)" /> </xsl:attribute>
					message: <xsl:call-template name="message">
						<xsl:with-param name="msg" select="message" />
					</xsl:call-template>
				</div>
				<div class='message'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('template-', $logElementId)" /> </xsl:attribute>
					template: <xsl:call-template name="message">
						<xsl:with-param name="msg" select="template" />
					</xsl:call-template>
				</div>

			</xsl:when>

			<xsl:when test="name()='tc-started'">
				<span class="tc-started">PTC <xsl:value-of select="@id" /> started with Behaviour <xsl:value-of select="@behaviour" /></span>
			</xsl:when>
			<xsl:when test="name()='tc-stopped'">
				<span class="tc-stopped">PTC <xsl:value-of select="@id" /> stopped, local verdict is <xsl:value-of select="@verdict" /></span>
			</xsl:when>

			<xsl:when test="name()='system-sent'">
				<span class="system-sent">
				<xsl:value-of select="@tsi-port" /> &gt;&gt; :
					<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;system-sent-message-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					<xsl:value-of select="label" />
					</a>
				</span>
				<!-- insert here a way to expand to the payload -->
				<div class='system-payload'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('system-sent-message-', $logElementId)" /> </xsl:attribute>
					<xsl:call-template name="break">
						<xsl:with-param name="text" select="payload" />
					</xsl:call-template>
				</div>
			</xsl:when>

			<xsl:when test="name()='system-received'">
				<span class="system-received">
				<xsl:value-of select="@tsi-port" /> &lt;&lt; : 
					<a>
					<xsl:attribute name="href">
					<xsl:value-of select="concat('javascript:expandCollapse(&quot;system-received-message-', $logElementId, '&quot;)')" />
					</xsl:attribute>
					<xsl:value-of select="label" />
					</a>
				</span>
				<!-- insert here a way to expand to the payload -->
				<div class='system-payload'>
					<xsl:attribute name="id"> <xsl:value-of select="concat('system-received-message-', $logElementId)" /> </xsl:attribute>
					<xsl:call-template name="break">
						<xsl:with-param name="text" select="payload" />
					</xsl:call-template>
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


<xsl:template match="text()">
	<xsl:call-template name="break">
		<xsl:with-param name="text" select="." />
	</xsl:call-template>
</xsl:template>

<!-- replace line breaks with <br > -->
<xsl:template name="break">
   <xsl:param name="text" />
   <xsl:choose>
   <xsl:when test="contains($text, '&#xa;')">
      <xsl:value-of select="substring-before($text, '&#xa;')"/>
      <br xmlns="" />
      <xsl:call-template name="break">
          <xsl:with-param name="text" select="substring-after($text,'&#xa;')"/>
      </xsl:call-template>
   </xsl:when>
   <xsl:otherwise>
		<xsl:value-of select="$text"/>
   </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- recursive template to format structured messages/templates -->
<xsl:template name="message">
	<xsl:param name="msg" />

	<!-- terminal values, i.e. a node without children -->
	<xsl:for-each select="$msg[not(*)]">
		<span class="value">
			<xsl:call-template name="break">
				<xsl:with-param name="text" select="$msg" />
			</xsl:call-template>
		</span>
	</xsl:for-each>

	<!-- records -->
	<xsl:for-each select="$msg/r">
		record:<ul class="record">
			<xsl:for-each select="f">
				<li><xsl:value-of select="@n" />: 
					<xsl:call-template name="message">
						<xsl:with-param name="msg" select="."/>
					</xsl:call-template>
				</li>
			</xsl:for-each>
		</ul>
	</xsl:for-each>

	<!-- lists -->
	<xsl:for-each select="$msg/l">
		list:<ol class="list">
			<xsl:for-each select="i">
				<li> 
					<xsl:call-template name="message">
						<xsl:with-param name="msg" select="."/>
					</xsl:call-template>
				</li>
			</xsl:for-each>
		</ol>
	</xsl:for-each>

	<!-- choice -->
	<xsl:for-each select="$msg/c">
		choice <xsl:value-of select="@n" />: 
					<xsl:call-template name="message">
						<xsl:with-param name="msg" select="."/>
					</xsl:call-template>
	</xsl:for-each>


</xsl:template>

</xsl:stylesheet>
