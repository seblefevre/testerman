<?xml version="1.0" encoding="utf-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">

<!-- header -->
<html xmlns="http://www.w3.org/1999/xhtml">
  
<head>
	<title><xsl:value-of select="ats/ats-started//@id" /></title>
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
Test Execution Results for ATS: <xsl:value-of select="ats/ats-started//@id" />.
</p>
<h1>Test Cases Summary</h1>


<table>
	<xsl:for-each select="ats/testcase-stopped">
	<tr>
		<td><xsl:value-of select="@id" /></td>
		<td><xsl:value-of select="@verdict" /></td>
	</tr>
	</xsl:for-each>
</table>

<h1>Test Cases Details</h1>

<xsl:for-each select="ats/testcase-created">
	<h2><xsl:value-of select="@id" /></h2>

</xsl:for-each>

<!-- footer -->
				</div>
			</div>
		</div>
	</div>
</body>
	 
</html>

</xsl:template>

</xsl:stylesheet>
