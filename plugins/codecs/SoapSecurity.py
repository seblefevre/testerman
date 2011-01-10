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
# SOAP Ws-Security functions to be interfaced through codecs.
##


import libxml2
import hashlib
import base64
import binascii
import time

import M2Crypto as M2

# Basic Ws-Security related namespaces
NS_WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
NS_WSU = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
NS_XMLDSIG = "http://www.w3.org/2000/09/xmldsig#"

NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"


# Supported transform algorithms
# Exclusive XML C14N support is limited: no inclusiveNamespaces support for now.
TRANSFORM_C14N_EXC = "http://www.w3.org/2001/10/xml-exc-c14n#"
TRANSFORM_C14N_EXC_WITH_COMMENTS = "http://www.w3.org/2001/10/xml-exc-c14n#WithComments"
TRANSFORM_C14N = "http://www.w3.org/2001/REC-xml-c14n-20010315"
TRANSFORM_C14N_WITH_COMMENTS = "http://www.w3.org/2001/REC-xml-c14n-20010315#WithComments"

Transforms = {}
Transforms[TRANSFORM_C14N_EXC] = lambda n: c14n(n, exclusive = 1, with_comments = 0)
Transforms[TRANSFORM_C14N_EXC_WITH_COMMENTS] = lambda n: c14n(n, exclusive = 1, with_comments = 1)
Transforms[TRANSFORM_C14N] = lambda n: c14n(n, exclusive = 0, with_comments = 0)
Transforms[TRANSFORM_C14N_WITH_COMMENTS] = lambda n: c14n(n, exclusive = 0, with_comments = 1)


# Supported digest algorithms
DIGEST_SHA1 = "http://www.w3.org/2000/09/xmldsig#sha1"
DIGEST_SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
DIGEST_SHA512 = "http://www.w3.org/2001/04/xmlenc#sha512"

Digests = {}
Digests[DIGEST_SHA1] = lambda s: hashlib.sha1(s).digest()
Digests[DIGEST_SHA256] = lambda s: hashlib.sha256(s).digest()
Digests[DIGEST_SHA512] = lambda s: hashlib.sha512(s).digest()

# Supported signature algorithms
SIGNATURE_RSA_SHA1 = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
SIGNATURE_RSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
SIGNATURE_RSA_SHA512 = "http://www.w3.org/2000/09/xmldsig-more#rsa-sha512"
# Maps of verifiers / computers
Signatures = {} 
Signatures[SIGNATURE_RSA_SHA1] = (lambda cert, sign, text: rsa_verifySignature('sha1', cert, sign, text), lambda privkey, text: rsa_computeSignature('sha1', privkey, text))
Signatures[SIGNATURE_RSA_SHA256] = (lambda cert, sign, text: rsa_verifySignature('sha256', cert, sign, text), lambda privkey, text: rsa_computeSignature('sha256', privkey, text))
Signatures[SIGNATURE_RSA_SHA512] = (lambda cert, sign, text: rsa_verifySignature('sha512', cert, sign, text), lambda privkey, text: rsa_computeSignature('sha512', privkey, text))



# Supported Token types
# Ws-Security X.509 Certificate Profile
TOKEN_REFERENCE_VALUE_TYPE_SKI = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509SubjectKeyIdentifier"

# Supported Token Encoding
ENCODING_BASE64 = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary"

# Convenience functions

def c14n(node, exclusive = 1, with_comments = 0):
	"""
	Canonicalizes the document, starting at node.
	node is a libxml2 element.
	"""
	# Only select the node (elements, attributes, ns) that are below the basenode.
	nodes = node.xpathEval('(. | .//node() | .//@* | .//namespace::*)')
	ret = node.c14nMemory(nodes = nodes, exclusive = exclusive, with_comments = with_comments)
	return ret


def applyTransform(node, algorithm):
	"""
	Applies a simple transformation to a node.
	"""
	func = Transforms.get(algorithm)
	if not func:
		raise Exception("Unsupported Transform algorithm (%s)" % algorithm)
	return func(node)

def computeDigest(text, algorithm):
	"""
	Compute text's digest based on the algorithm.
	Returns the digest as a buffer string.
	"""
	func = Digests.get(algorithm)
	if not func:
		raise Exception("Unsupported Digest algorithm (%s)" % algorithm)
	digest = func(text)
	return digest

###############################################################################
# libxml2 convenience function
###############################################################################

def getOrCreateNs(node, content, prefix):
	"""
	Create a new NS or reuse an existing one if the content/url already exists.
	"""
	ns = node.nsDefs()
	while ns:
		if ns.content == content:
			return ns
		else:
			ns = ns.next
	return node.newNs(content, prefix)
	

def getFirstElementChild(node):
	"""
	Returns the first element child.
	
	node.firstElementChild() is not available for all libxml2 versions.
	"""
	child = node.children
	if not child:
		return None
	while child:
		if child.type == 'element':
			return child
		child = child.next
	return None


###############################################################################
# Certificates/Key loading & referencing by Subject Key Identifier
###############################################################################

CertificatesBySki = {}

def loadCertificates(filenames):
	global CertificatesBySki
	for filename in filenames:
		try:
			f = open(filename)
			pem = f.read()
			f.close()
			cert = M2.X509.load_cert_string(pem)
			try:
				ski = cert.get_ext('subjectKeyIdentifier').get_value()
			except:
				print "DEBUG: no SKI found in certificate %s - not referencing" % filename
				continue
			# The SKI is something like AB:01:7C ...
			# let's turn it into a buffer string
			ski = binascii.unhexlify(ski.replace(':', ''))

			CertificatesBySki[ski] = cert
			print "DEBUG: certificate for '%s' loaded" % cert.get_subject().as_text()
		except Exception, e:
			print "DEBUG: unable to load certificate %s (%s)" % (filename, str(e))

def loadCertificate(filename):
	global CertificatesBySki
	try:
		f = open(filename)
		pem = f.read()
		f.close()
		cert = M2.X509.load_cert_string(pem)
		print "DEBUG: certificate for '%s' loaded" % cert.get_subject().as_text()
		try:
			ski = cert.get_ext('subjectKeyIdentifier').get_value()
		except:
			print "DEBUG: no SKI found in certificate %s - not referencing" % filename
			return cert
		# The SKI is something like AB:01:7C ...
		# let's turn it into a buffer string
		ski = binascii.unhexlify(ski.replace(':', ''))

		CertificatesBySki[ski] = cert
		return cert

	except Exception, e:
		print "DEBUG: unable to load certificate %s (%s)" % (filename, str(e))
		return None	

def loadKey(filename):
	try:
		f = open(filename)
		pem = f.read()
		f.close()
		key = M2.EVP.load_key_string(pem)
		print "DEBUG: key loaded"
		return key
	except Exception, e:
		print "DEBUG: unable to load key %s (%s)" % (filename, str(e))
		return None	

def loadKeyFromPem(pem):
	try:
		key = M2.EVP.load_key_string(pem)
		return key
	except Exception, e:
		raise Exception("unable to parse PEM key (%s)" % (str(e)))

def loadCertFromPem(pem):
	"""
	Loads a X.509 certificate from a PEM string.
	Returns the certificate and its subjectKeyIdentifier, if any
	"""
	try:
		cert = M2.X509.load_cert_string(pem)
		ski = None
		try:
			ski = cert.get_ext('subjectKeyIdentifier').get_value()
			# let's turn it into a buffer string
			ski = binascii.unhexlify(ski.replace(':', ''))
		except:
			pass
		return (cert, ski)
	except Exception, e:
		raise Exception("unable to parse PEM certificate (%s)" % (str(e)))
	

###############################################################################
# Certificate extractor (from a SOAP message)
###############################################################################

def getCertificate(signatureXPathContext, certificatesDb):
	"""
	Gets a certificate from a Signature node/context.
	
	For now, only support X.509 Certificate Profile / Subject Key Identifier variant.
	"""
	xpc = signatureXPathContext
	skiNodes = xpc.xpathEval('./ds:KeyInfo/wsse:SecurityTokenReference/wsse:KeyIdentifier[@ValueType = "%s"]' % TOKEN_REFERENCE_VALUE_TYPE_SKI)
	if not skiNodes:
		raise Exception("No X.509 Certificate Subject Key Identifier found - other tokens are not supported for now")
	if len(skiNodes) > 1:
		print "FIXME: multiple SKI nodes found. Only using the first one."
	skiNode = skiNodes[0]
	
	encoding = skiNode.prop('EncodingType')
	if encoding and encoding != ENCODING_BASE64:
		raise Exception("Unsupported Subject Key Identifier encoding type (%s)" % encoding)
	
	ski = base64.decodestring(skiNode.content)
		
	# Now, look up in our certificate DB for the certificate
	cert = certificatesDb.get(ski)
	if not cert:
		raise Exception("Cannot find a referenced certificate with this Subject Key Identifier.")
	return cert


def verifySignature(certificate, algorithm, signature, text):
	func = Signatures.get(algorithm)
	if not func:
		raise Exception("Unsupported signature algorithm (%s)" % algorithm)

	verif, comput = func
	return verif(certificate, signature, text)

def computeSignature(algorithm, privkey, text):
	func = Signatures.get(algorithm)
	if not func:
		raise Exception("Unsupported signature algorithm (%s)" % algorithm)

	verif, comput = func
	return comput(privkey, text)


def rsa_verifySignature(md, certificate, signature, text):
	"""
	md is the digest method (sha1, sha256, ...)
	"""
	pubkey = certificate.get_pubkey()

	pubkey.reset_context(md = md)
	pubkey.verify_init()
	pubkey.verify_update(text)
	ret = pubkey.verify_final(signature)
	return (ret == 1)


def rsa_computeSignature(md, privkey, text):
	"""
	md is the digest method (sha1, sha256, ...)
	"""
	privkey.reset_context(md = md)
	privkey.sign_init()
	privkey.sign_update(text)
	return privkey.sign_final()


###############################################################################
# High-level functions
###############################################################################

def verifyMessage(doc, certificatesDb):
	"""
	Checks the digests & signature of a signed SOAP message.
	Only supports Ws-Security X.509 Certificate Profile 1.0/1.1.
	Username or Binary Token profiles are not supported.
	
	The message is assumred to be signed by a certificate
	which is contains in the certificatesDb.
	
	@type  doc: libxml2 document.
	@param doc: the SOAP document whose signature must be verified.
	@type  certificatesDb: dict(string buf) of M2Crypto.X509
	@param certificatesDb: possible signing certificates, 
	indexed by their Subject Key Identifier.
	
	@rtype: M2Crypto.X509 or None
	@returns: the signing certificate, or None if not signed
	by the expected certificate.
	
	@throws: Exception in case of any error (invalid SOAP envelope
	or signature, unsupported algorithm, missing token reference,
	no matching certificate found, message altered).
	"""
	xpc = doc.xpathNewContext()
	xpc.xpathRegisterNs("wsu", NS_WSU)
	xpc.xpathRegisterNs("wsse", NS_WSSE)
	xpc.xpathRegisterNs("ds", NS_XMLDSIG)
	
	docxpc = doc.xpathNewContext()
	docxpc.xpathRegisterNs("wsu", NS_WSU)
	
	# Extract signature-related elements
	signature = xpc.xpathEval('/*/*/wsse:Security/ds:Signature')
	
	if not signature or len(signature) > 1:
		raise Exception("No or multiple digital signature found in this SOAP payload.")
	
	signature = signature[0]
	
	xpc.setContextNode(signature)
	signedInfo = xpc.xpathEval('./ds:SignedInfo')
	if not signedInfo:
		raise Exception("No SignedInfo in this Signature element")
	signedInfo = signedInfo[0]
	signatureValue = xpc.xpathEval('./ds:SignatureValue/text()')
	if not signatureValue:
		raise Exception("Missing SignatureValue") 
	signatureValue = base64.decodestring(signatureValue[0].content)

	keyInfo = xpc.xpathEval('./ds:KeyInfo')

#	print "DEBUG: signedInfo: %s" % signedInfo
#	print "DEBUG: signature value: %s" % signatureValue
	

	# Signed Elements verification
		
	# Now, let's check each signed elements from SignedInfo.Reference
	references = xpc.xpathEval('./ds:SignedInfo/ds:Reference')
	for reference in references:
		xpc.setContextNode(reference)
		uri = reference.prop("URI")
		transformAlgorithm = xpc.xpathEval('./ds:Transforms/ds:Transform/@Algorithm')[0].content
		digestAlgorithm = xpc.xpathEval('./ds:DigestMethod/@Algorithm')[0].content
		digestValue = base64.decodestring(xpc.xpathEval('./ds:DigestValue/text()')[0].content)
	
#		print "Signed reference:"
#		print "URI: %s" % uri
#		print "Transform: %s" % transformAlgorithm
#		print "Digest Algorithm: %s" % digestAlgorithm
#		print "Digest Value: %s" % base64.encodestring(digestValue)

		# Select the node corresponding to the uri
		if not uri.startswith('#'):
			raise Exception("Unsupported Signed Reference URI (%s)" % uri)
		
		# First, check if we have a wsu:Id somewhere	
		part = docxpc.xpathEval('//*[@wsu:Id = "%s"]' % uri[1:])
		if not part:
			# fallback to Id
			part = docxpc.xpathEval('//*[@Id = "%s"]' % uri[1:])
		if not part or len(part) > 1:
			raise Exception("No or multiple elements referenced by %s" % uri)
		
		# OK, now apply the transformation(s)
		part = part[0]
		transformedPart = applyTransform(part, transformAlgorithm)
		
		# Then compute the digest
		digest = computeDigest(transformedPart, digestAlgorithm)
		
		if digest != digestValue:
			raise Exception("Digest values differ for URI %s (computed: %s, expected: %s)" % (uri, base64.encodestring(digest), base64.encodestring(digestValue)))
		
#		print "DEBUG: reference %s has not been altered." % uri
	

	# Now, let's take care of the signature.
	
	xpc.setContextNode(signedInfo)
	signatureAlgorithm = xpc.xpathEval('./ds:SignatureMethod/@Algorithm')[0].content
	c14nAlgorithm = xpc.xpathEval('./ds:CanonicalizationMethod/@Algorithm')[0].content
	
	# We need to transform the SignedInfo part
	transformedSignedInfo = applyTransform(signedInfo, c14nAlgorithm)
	
	# We need to extract the security token
	# For now, we only support X.509 Certificate Profile
	xpc.setContextNode(signature)
	cert = getCertificate(xpc, certificatesDb)

	# Then apply our signature algorithm
	verified = verifySignature(certificate = cert, algorithm = signatureAlgorithm, 
		signature = signatureValue, text = transformedSignedInfo)
	
	if verified:
		print "This message has been verified as signed by %s." % cert.get_subject().as_text()
		return cert
	else:
		print "This message has NOT been signed by the claimed certificate."
		return None


def signMessage(doc, cert, privkey, tbsElements = [], 
		c14nAlgorithm = TRANSFORM_C14N_EXC, 
		transformAlgorithm = TRANSFORM_C14N_EXC,
		digestAlgorithm = DIGEST_SHA1,
		signatureAlgorithm = SIGNATURE_RSA_SHA1):
	"""
	Signs a message using Ws-Security X.509 Certificate Profile 1.0/1.1,
	using the certificate's Subject Key Identifier as the token reference.
	
	The initial document shall not include any Ws-Security-related info.
	
	WARNING: this method does not check that the privkey and the certificate
	are associated.
	
	@type  doc: libxml2 Document
	@param doc: the document corresponding to the whole SOAP envelope
	@type  cert: M2Crypto.X509
	@param cert: the signing certificate. Must contain a Subject Key Identifier.
	@type  privkey: M2Crypto.PKey
	@type  privkey: the private key associated to the certificate.
	@type  tbsElements: list of libxml2 Element nodes
	@param tbsElements: the list of elements to be signed (typically the body).
	
	@rtype: libxml2 document
	@returns: the updated XML document, with an added Signature header.
	"""
	try:
		ski = cert.get_ext('subjectKeyIdentifier').get_value()
	except:
		raise Exception("Cannot sign with this certificate (%s), no Subject Key Identifier found" % cert.get_subject().as_text())
	ski = binascii.unhexlify(ski.replace(':', ''))

	ns_ds = getOrCreateNs(doc.getRootElement(), NS_XMLDSIG, "ds")
	ns_wsse = getOrCreateNs(doc.getRootElement(), NS_WSSE, "wsse")
	ns_wsu = getOrCreateNs(doc.getRootElement(), NS_WSU, "wsu")
	ns_soap = getOrCreateNs(doc.getRootElement(), NS_SOAP, "soap")

	xpc = doc.xpathNewContext()
	xpc.xpathRegisterNs("wsse", NS_WSSE)
	xpc.xpathRegisterNs("soap", NS_SOAP)

	env = xpc.xpathEval("/soap:Envelope")
	if not env:
		raise Exception("Cannot sign this message: not a SOAP envelope")
	env = env[0]
	header = xpc.xpathEval("/soap:Envelope/soap:Header")
	if not header:
		header = libxml2.newNode("Header")
		header.setNs(ns_soap)
		firstElementChild = getFirstElementChild(env)
		if firstElementChild:
			firstElementChild.addPrevSibling(header)
		else:
			env.addChild(header)
	else:
		header = header[0]

	security = xpc.xpathEval("/soap:Envelope/soap:Header/wsse:Security")
	if not security:
		security = libxml2.newNode("Security")
		security.setNs(ns_wsse)
		header.addChild(security)
	else:
		security = security[0]
	
	signature = libxml2.newNode("Signature")
	signature.setNs(ns_ds)
	security.addChild(signature)
	
	# Signed Info
	signedInfo = libxml2.newNode("SignedInfo")
	signedInfo.setNs(ns_ds)
	# c14n method
	c14nMethod = libxml2.newNode("CanonicalizationMethod")
	c14nMethod.setProp("Algorithm", c14nAlgorithm)
	c14nMethod.setNs(ns_ds)
	signedInfo.addChild(c14nMethod)
	# Signature method	
	signatureMethod = libxml2.newNode("SignatureMethod")
	signatureMethod.setProp("Algorithm", signatureAlgorithm)
	signatureMethod.setNs(ns_ds)
	signedInfo.addChild(signatureMethod)
	# Compute digests for each elements
	for tbs in tbsElements:
		reference = libxml2.newNode("Reference")
		reference.setNs(ns_ds)
		# Generate a local ID
		uri = "id-%s" % time.time()
		reference.setProp("URI", '#' + uri)
		
		# Transforms - only a single Transform is used
		transforms = libxml2.newNode("Transforms")
		transforms.setNs(ns_ds)
		transform = libxml2.newNode("Transform")
		transform.setNs(ns_ds)
		transform.setProp("Algorithm", transformAlgorithm)
		transforms.addChild(transform)
		reference.addChild(transforms)

		# Digest method
		digestMethod = libxml2.newNode("DigestMethod")
		digestMethod.setNs(ns_ds)
		digestMethod.setProp("Algorithm", digestAlgorithm)
		reference.addChild(digestMethod)
		
		# Digest value
		# first, add a wsu:Id=uri
		tbs.setNsProp(ns_wsu, "Id", uri)
		digest = computeDigest(applyTransform(tbs, transformAlgorithm), digestAlgorithm)
		digestValue = libxml2.newNode("DigestValue")
		digestValue.setNs(ns_ds)
		digestValue.addChild(libxml2.newText(base64.encodestring(digest)))
		reference.addChild(digestValue)

		# OK, we're done with this reference/tbs element		
		signedInfo.addChild(reference)
	
	signature.addChild(signedInfo)

	# Signature Value
	signatureValue = libxml2.newNode("SignatureValue")
	signatureValue.setNs(ns_ds)
	# Signature computation
	# transform the signedInfo
	tbs = applyTransform(signedInfo, c14nAlgorithm)
	sign = computeSignature(privkey = privkey, algorithm = signatureAlgorithm, text = tbs)
	signatureValue.addChild(libxml2.newText(base64.encodestring(sign)))

	# A single key info (cert SKI)
	keyInfo = libxml2.newNode("KeyInfo")
	keyInfo.setNs(ns_ds)
	securityTokenReference = libxml2.newNode("SecurityTokenReference")
	securityTokenReference.setNs(ns_wsse)
	keyIdentifier = libxml2.newNode("KeyIdentifier")
	keyIdentifier.setNs(ns_wsse)
	keyIdentifier.setProp("EncodingType", ENCODING_BASE64)
	keyIdentifier.setProp("ValueType", TOKEN_REFERENCE_VALUE_TYPE_SKI)
	keyIdentifier.addChild(libxml2.newText(base64.encodestring(ski)))
	securityTokenReference.addChild(keyIdentifier)
	keyInfo.addChild(securityTokenReference)

	signature.addChild(signatureValue)
	signature.addChild(keyInfo)

	# OK, return the updated doc
	return doc


###############################################################################
# Command line interface
###############################################################################

def usage():
	print "Usage:"
	print "Verify a signed SOAP message:"
	print " %s verify <message.xml> [<cert.pem>]+" % sys.argv[0]
	print " (wildcards accepted for certificates) - signature verification based on SKI)"
	print
	print "Sign a SOAP message:"
	print " %s sign <message.xml> <privkey.pem> <cert.pem>" % sys.argv[0]
	print

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 4:
		usage()
		sys.exit(1)
	action = sys.argv[1]
	inputfilename = sys.argv[2]
	
	if action == "verify":
		import glob
		loadCertificates(glob.glob(sys.argv[3]))
		doc = libxml2.parseFile(inputfilename)
		verifyMessage(doc, certificatesDb = CertificatesBySki)

	elif action == "sign":
		cert = loadCertificate(sys.argv[4])
		privkey = loadKey(sys.argv[3])
		doc = libxml2.parseFile(inputfilename)
		# we sign the body only
		xpc = doc.xpathNewContext()
		xpc.xpathRegisterNs("wsse", NS_WSSE)
		xpc.xpathRegisterNs("soap", NS_SOAP)
		tbs = xpc.xpathEval("/soap:Envelope/soap:Body")
		if not tbs:
			print("WARNING: No soap:body to sign.")
		signedMessage = signMessage(doc, cert, privkey, tbsElements = tbs)
		ret = signedMessage.serialize(encoding = 'utf-8', format = 0)
		print ret

	else:
		usage()
		sys.exit(1)
	
	
