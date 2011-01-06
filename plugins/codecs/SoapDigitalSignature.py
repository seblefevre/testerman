# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2011 Sebastien Lefevre and other contributors
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
##

##
# A special codec that deals with SOAP Ws-Security 1.0/1.1 header
# for digital signature.
##

import CodecManager

import SoapSecurity
import libxml2

# A default 1024-bit key
DEFAULT_SIGNING_PRIVATE_KEY = \
"""-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDa7M8bdhCyls5fAcB4hnXsMSE84qjrcNExT9VgLQvwnCgw8xgj
bVbPWysyJumGjWVN1YP9RuwGWuq0BroxlFo54ZMneZcQKm0e2+0nATtzRF9j6o3X
kcMwQfLjC9AUG5bV6odwLbeFrtKW/eZMGoDTVp/BBggJYbzyPeN0SytQwwIDAQAB
AoGBALFhJf1uD+FjZxp7ZONCrtEMjY2zaII7CoQV1yDx3ra5D6d5j5lEwg2IJNuh
w5yNfAMweJ0ClcIgcAIlYT9CoEa82BBUDn797ZUrUN1mgTXbzioyDBdHG8usFjPn
5nvcknLTbLvrlAa9t5arCcKQ511OQD+ktnhcHB4TkBtYiugBAkEA/xCKJg2q0SCL
z7Za1Jlm6T/7/IJ1Gx3RGCUccmovTRzZvo6TsWLRFiMACygr8DoAOC5tLEqj6NBu
OidgiC3bwwJBANu6VzogJXoZXAZrP2HYY85AEGWnhhXmmOupGNFPqPjBiG/urqoc
uyULq69++xtmK6BanuaSshOj3GV6A6MGZwECQDlt2+0dfqx/i3tFL8ZWk9lI0s/T
/9IPMJkjIfiQ9/2A1XYWXCLAgRte3g+lB9+a75m2ulYSqD0vUOI/I3kF+kkCQQCt
E/f3kjDTH7ysVbhkc1YStcX0vOPSxoS4RMeGwI/h+lhliwZMezsy8CF5qLVVnMJK
mndGOlFJRS6rRFQvCzEBAkBvPd3VB4lN9RGfGbQbGZW/y1BBwpCflj8w5+Jy/jvT
UYfxMLhpPbbtusTSDVbBnPEm9uOB/W4uPI56i535RoYf
-----END RSA PRIVATE KEY-----"""

# With an associated self-signed certificate
# FIXME: does not contain a SKI extension
DEFAULT_SIGNING_CERTIFICATE = \
"""-----BEGIN CERTIFICATE-----
MIIC7zCCAligAwIBAgIJAIq7T1myCRCTMA0GCSqGSIb3DQEBBQUAMFkxCzAJBgNV
BAYTAkZSMQ8wDQYDVQQIEwZGcmFuY2UxEjAQBgNVBAoTCVRlc3Rlcm1hbjElMCMG
A1UEAxMcVGVzdGVybWFuIFdzLVNlY3VyaXR5IFNhbXBsZTAeFw0xMTAxMDYxMDM5
MjRaFw0xMzAxMDUxMDM5MjRaMFkxCzAJBgNVBAYTAkZSMQ8wDQYDVQQIEwZGcmFu
Y2UxEjAQBgNVBAoTCVRlc3Rlcm1hbjElMCMGA1UEAxMcVGVzdGVybWFuIFdzLVNl
Y3VyaXR5IFNhbXBsZTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA2uzPG3YQ
spbOXwHAeIZ17DEhPOKo63DRMU/VYC0L8JwoMPMYI21Wz1srMibpho1lTdWD/Ubs
BlrqtAa6MZRaOeGTJ3mXECptHtvtJwE7c0RfY+qN15HDMEHy4wvQFBuW1eqHcC23
ha7Slv3mTBqA01afwQYICWG88j3jdEsrUMMCAwEAAaOBvjCBuzAdBgNVHQ4EFgQU
3MarnhFZj6o3UUfblFzxjuVVOH8wgYsGA1UdIwSBgzCBgIAU3MarnhFZj6o3UUfb
lFzxjuVVOH+hXaRbMFkxCzAJBgNVBAYTAkZSMQ8wDQYDVQQIEwZGcmFuY2UxEjAQ
BgNVBAoTCVRlc3Rlcm1hbjElMCMGA1UEAxMcVGVzdGVybWFuIFdzLVNlY3VyaXR5
IFNhbXBsZYIJAIq7T1myCRCTMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQAD
gYEAaEOWlTmBwS1xkwEaa+LoDblj4KNtOIz0z/WKhcsS3ngnuqbpkt95xyIyNJ9P
9rY7FIuQl1XRuzgT/IlXoe9F2zM8UTHke/dbMGHCBGDHiyfOz91nprqwCY83OReH
pbiSGFhh0br+8OpaldQmqBMj1AWYSGmBnml0GV/Cv49UC/o=
-----END CERTIFICATE-----"""


class SoapDigitalSignatureCodec(CodecManager.Codec):
	"""
	
	= Identification and Properties =
	
	Codec ID: `soap11.ds`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| prettyprint  || boolean || `False` || encoding/signing: pretty xml print the signed output ||
	|| encoding     || string  || `'utf-8'` || encoding/signing: encoding format. decoding: decoding format if no prolog is present ||
	|| write_prolog || boolean || `True` || encoding/signing: write the `<?xml version="1.0" encoding="..." ?>` prolog or not ||
	|| signing_key  || string || `None` || encoding/signing: the private key to use to sign the outgoing message, provided as a PEM string. If none is provided, a default key is used. ||
	|| signing_cert || string || `None` || encoding/signing: the X.509 certificate associated to the key above, provided as a PEM string. If none is provided, a default certificate associated to the private key above is used. ||
	|| expected_certificates || list of strings || `[]` || decoding/verification: a list of X.509 certificates, provided as PEM strings, that will be used as signing candidates. One of them should be referenced in the signature to validate, based on its subject key identifier. By default, the default signing certificate above is included. ||

	= Overview =

	A special codec that deals with SOAP Ws-Security 1.0/1.1 header
	for digital signature:
	- upon decoding, verifies the SOAP message's signature,
	- upon encoding, signs the message (soap:Body only), adding a SOAP Security/Signature Header in the outgoing message.
	
	This codec takes and returns a string,
	i.e. it is not responsible for actually turning an XML payload
	into a higher level structure.
	You may use with CodecXml for that purpose, for instance:
	
	{{{
#!python
signing_privkey = '''-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDMJBNZoKMEoEs+m/V8jjMAX57uQEJsyYe+2SbWjrZ3knQb+3+6
iMywhduDuVJJhE7leOoDZIlghOCr1CEkIZK+/HoH/kg++Olz8taOG8L/P3GnMfx4
...
gj1qvwBfBVaLGVep1QnQt1DFBbKP36I=
-----END RSA PRIVATE KEY-----'''

# The certificate associated with the key above.
# Must be X509v3 with subjectKeyIdentifier extension.
signing_certificate = '''-----BEGIN CERTIFICATE-----
MIIDEzCCAnygAwIBAgIJAIfjr0Rpa5W7MA0GCSqGSIb3DQEBBQUAMGUxCzAJBgNV
BAYTAkZSMQ8wDQYDVQQIEwZGcmFuY2UxETAPBgNVBAcTCEdyZW5vYmxlMQwwCgYD
...
gj1qvwBfBVaLGVep1QnQt1DFBbKP36I=
-----END CERTIFICATE-----
'''
	
# We create a codec alias to associate the outgoing signature
# attributes
define_codec_alias('ds', 'soap11.ds', 
	signing_key = signing_privkey, 
	signing_cert = signing_certificate)


class TC_SOAP_DS_SAMPLE(TestCase):
	def body(self):

		port01 = self.mtc['port01']
		port02 = self.mtc['port02']
		connect(port01, port02)

		# Create a structured xml document
		document = ('Envelope', { 'ns': 'http://...', 'children': [ ... ])

		# Stacked codecs - first we serialize the document with the 'xml' codec,
		# then we sign it with the 'ds' aliased codec .
		message = with_('ds', with_('xml', document))
		# This sends a signed message
		port01.send(message)
		
		# On matching event, you'll be able to see the signed message
		port02.receive()

		# Of course, we could use the 'ds' aliased codec directly with
		# an xml string

		xml = '<soapenv:Envelope xmlns:ns="http://acme.com/api/1" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
 <soapenv:Body>
    <ns:operationRequest>
       <ns:someParameter />
    </ns:operationRequest>
 </soapenv:Body>
</soapenv:Envelope>'

		port01.send(with_('ds', xml))

		# On matching event, you'll be able to see the signed message
		port02.receive()


TC_SOAP_DS_SAMPLE().execute()


	}}}
	
	This codec, which is actually a signer on encoding, and
	a signature verifier on decoding, does not support the whole
	Ws-Security 1.1 standard yet.
	
	== Signing SOAP Messages ==
	
	The message to sign must be a valid SOAP 1.1 envelope, and must
	not contain any saop:Header/wsse:Security/ds:Signature element
	yet. It is added by this codec.
	
	The signature model is currently limited to the Ws-Security
	X.509 Certificate Token Profile 1.1, and more particularly to the case
	where the signing certificate is referenced via its Subject Key
	Identifier (SKI).[[BR]]
	As a consequence, it requires that the certificate is a X.509v3
	certificate with the SKI extension. Without such a certificate,
	the signing/encoding operation fails.
	
	The "encoded" output is simply the same XML document as in input
	(string buffer), with the added signature elements.
	
	== Verifying Incoming SOAP Messages ==
	
	The decode operation is actually a signature validation.
	
	If the signature contained into the XML document is correct,
	the decoding output is a structure containing:
	- the original message (field `message`)
	- the signing token (field `signedBy`), as a choice. For now, only the `certificate` choice is provided, and is filled with the signing certificate in PEM format.
	
	== Limitations ==
	
	This codec does not support the full range of algorithms required
	to be Ws-Security 1.1 compliant.
	
	In addition, only the X.509 Certificate Token Profile is supported for now.
	Username profile, in particular, is not available.
	
	=== Signing Limitations ===
	
	The elements to be signed cannot be selected yet. By default,
	this codec signs the soap:Body element.
	
	Exclusive XML canonicalization is used for all transforms. This is
	not configurable yet.
	
	=== Signature Verification Limitations ===
	
	A (single) Transform is mandatory. Chained transforms or empty
	transform chains are not supported.
	
	Multiple token references are not supported.
	
	=== Supported Algorithms ===
	
	Supported signature algorithms (both when signing or verifying):
	- RSA-SHA1, RSA-SHA256, RSA-SHA512.
	
	Supported transform and canonicalization algorithms
	(both when signing or verifying):
	- XML "inclusive" c14n
	- XML "inclusive" c14n with comments
	- XML exclusive c14n (no support for inclusive prefixes parameter)
	- XML exclusive c14n with comments (no support for inclusive prefixes parameter)
	
	Supported digest algorithms	(both when signing or verifying):
	- SHA1
	
	= Dependencies =
	
	This codec depends on the M2Crypto Python library.
	
	
	"""
	def encode(self, template):
		"""
		Signs the message.
		"""
		if not isinstance(template, basestring):
			raise Exception('This codec requires a string')
		
		cert, ski = SoapSecurity.loadCertFromPem(self.getProperty('signing_cert', DEFAULT_SIGNING_CERTIFICATE))
		privkey = SoapSecurity.loadKeyFromPem(self.getProperty('signing_key', DEFAULT_SIGNING_PRIVATE_KEY))
		
		doc = libxml2.parseDoc(template)
		# Sign the body only
		xpc = doc.xpathNewContext()
		xpc.xpathRegisterNs("soap", SoapSecurity.NS_SOAP)
		tbs = xpc.xpathEval("/soap:Envelope/soap:Body")
		signedMessage = SoapSecurity.signMessage(doc, cert, privkey, tbsElements = tbs)

		root = signedMessage.getRootElement()

		encoding = self.getProperty('encoding', 'utf-8')
		ret = ''
		if self.getProperty('write_prolog', True):
			ret = '<?xml version="1.0" encoding="%s"?>\n' % encoding
		ret += root.serialize(encoding = encoding, format = (self.getProperty('prettyprint', False) and 1 or 0))
		
		return (ret, "Signed XML data")
			
	def decode(self, data):
		"""
		Verifies a signature.
		"""
		doc = libxml2.parseDoc(data)
		
		certificates = self.getProperty("expected_certificates", [ DEFAULT_SIGNING_CERTIFICATE ])
		certificatesDb = {}
		for c in certificates:
			cert, ski = SoapSecurity.loadCertFromPem(c)
			certificatesDb[ski] = cert
		
		cert = SoapSecurity.verifyMessage(doc, certificatesDb = certificatesDb)
		
		if not cert:
			raise Exception("This message has not been signed by the claimed party.")

		ret = {}
		ret['message'] = data
		ret['signedBy'] = ('certificate', cert.as_pem().strip())			
		return (ret, "XML data verified as signed by '%s'" % cert.get_subject().as_text())

	

CodecManager.registerCodecClass('soap11.ds', SoapDigitalSignatureCodec)


if __name__ == '__main__':
	CodecManager.alias('ds', 'soap11.ds')
	
	sampleEnv = """<?xml version="1.0" encoding="utf-8" ?>
<soapenv:Envelope xmlns:ns="http://www.eservglobal.com/homesend/tews/2.0" xmlns:ns1="http://www.eservglobal.com/homesend/types/2.0" xmlns:ns2="http://www.eservglobal.com/homesend/tews/2.1" xmlns:ns3="http://www.eservglobal.com/homesend/types/2.1" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
<library owner="John Smith" administrator="Héléna Utf8 and Mickaël Orangina" xmlns="http://default" xmlns:b="http://base">
	<book isbn="88888-7777788">
		<b:author>Mickaël Orangina</b:author>
		<title locale="fr">Tonnerre sous les tropiques</title>
		<title locale="us">Tropic thunder</title>
		<title locale="es">No <i>habla</i> espagnol</title>
		<b:summary><![CDATA[This is a CDATA section <-> <-- this is a tie fighter]]></b:summary>
	</book>
</library>
   </soapenv:Body>
</soapenv:Envelope>
"""
	
	for codec in [ 'ds' ]:
		for sample in [ sampleEnv ]:
			print "%s %s %s" % (40*'=', codec, 40*'=')
			print "signed with %s:" % codec
			(signed, summary) = CodecManager.encode(codec, sample)
			print
			print "Summary: %s" % summary
			print
			print signed
			print
			print "verifying signature with %s:" % codec
			(output, summary) = CodecManager.decode(codec,signed)
			verified = output['message']
			signedBy = output['signedBy']
			print verified
			print
			assert(signedBy[0] == 'certificate')
			assert(signedBy[1].strip() == DEFAULT_SIGNING_CERTIFICATE.strip())
			print
			print "Summary: %s" % summary
			assert(signed == verified)
			print
	
	
