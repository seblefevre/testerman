##
# BER codec feasability test tool.
##

import asn1
# To compile TcapAsn: py_output.py tcap.asn > TcapAsn.py

import TcapAsn
import BerAdapter
import binascii


tcapBegin = \
 "62644804000227846b3e283c060700118605010101a031602fa109060704000001001302be222820060704000001010101a015a01380099622123008016901f98106a807000000016c1ca11a02010102013b301204010f0405a3986c36028006a80700000001"
#"62644804000227846b3e283c060700118605010101a031602fa109060704000001001302be222820060704000001010101a015a01380099622123008016901f98106a807000000016c1ca11a02010102013b301204010f0405a3986c36028006a80700000001"


# From gsm_map_with_ussd_string.pcap sample
tcapBegin2 = \
 "626a48042f3b46026b3a2838060700118605010101a02d602b80020780a109060704000001001302be1a2818060704000001010101a00da00b80099656051124006913f66c26a12402010102013b301c04010f040eaa180da682dd6c31192d36bbdd468007917267415827f2"
#"626a4804 2f3b4602 6b3a2838 06070011 8605010101a02d602b80020780a109060704000001001302be1a2818060704000001010101a00da00b80099656051124006913f66c26a12402010102013b301c04010f040eaa180da682dd6c31192d36bbdd468007917267415827f2"


def test():
	for buf in [ binascii.unhexlify(x) for x in [ tcapBegin2 ] ]:

		# Decoding
		# Buf -> ASN
		print 80*'-'
		dec = asn1.decode(TcapAsn.TCMessage, buf)
		print "Buffer -> ASN:"
		print repr(dec)
		print "dec[1] type: " + dec[1].__class__.__name__
		# ASN -> Testerman
		print 80*'-'
		print "ASN -> Testerman:"
		testermanDec = BerAdapter.toTesterman(dec)
		print repr(testermanDec)
	#	print 80*'-'
	#	print "ASN -> Testerman (pretty printed):"
	#	BerAdapter.prettyprint(testermanDec)
		print 80*'-'
		print

		# Testerman -> ASN
		print 80*'-'
		print "Testerman -> ASN:"
		dec = BerAdapter.fromTesterman(testermanDec)
		print repr(dec)

		# First re-encoding
		print 80*'-'
		print "Re-encoded buffer:"
		# .encode() outputs an array.array
		bufbuf = asn1.encode(TcapAsn.TCMessage, dec).tostring()
		print binascii.hexlify(bufbuf)
		print "Re-encoded buffer type: %s" % bufbuf.__class__.__name__
		print "Initial buffer:"
		print binascii.hexlify(buf)
		print "Initial buffer type: %s" % buf.__class__.__name__
		print "Re-decoded:"
		decdec = asn1.decode(TcapAsn.TCMessage, bufbuf)
		print decdec
		bufbufbuf = asn1.encode(TcapAsn.TCMessage, decdec).tostring()
		print "Re-re-encoded:"
		print binascii.hexlify(bufbufbuf)
		print "Previously re-encoded buffer:"
		print binascii.hexlify(bufbuf)
		print "Initial buffer:"
		print binascii.hexlify(buf)

def test2():
	"""
	Basic encoding testing.
	"""
	print "Sequence encoding (TCMessage):"
	s =  asn1.StructBase(otid = '\xff\x00')
	m = ('begin', s)
	buf = asn1.encode(TcapAsn.TCMessage, m).tostring()
	print binascii.hexlify(buf)

	print "Tuple encoding (OPERATION):"
	m = ('localValue', 10)
	buf = asn1.encode(TcapAsn.OPERATION, m).tostring()
	print binascii.hexlify(buf)
	
	print "Octstring encoding (Dialog1):"
	m = '\xff\x00'
	buf = asn1.encode(TcapAsn.Dialog1, m).tostring()
	print binascii.hexlify(buf)

	print "OID encoding (in OPERATION.globalValue):"
	oid = '1.2.3.4.5.65.7'
	if BerAdapter.isOid(oid):
		oid = asn1.OidVal([int(x) for x in oid.split('.')])
	m = ('globalValue', oid)
	buf = asn1.encode(TcapAsn.OPERATION, m).tostring()
	print binascii.hexlify(buf)
	
#	print "EXTERNAL encoding (DialoguePortion):"
#	m = asn1.EXTERNAL
#	a = asn1.ANY
#	m.direct_reference = asn1.OidVal([int(x) for x in '1.2.3.4.5'.split('.')])
#	m.encoding = ('single-ASN1-type', a)
#	buf = asn1.encode(TcapAsn.Parameter, m).tostring()
#	print binascii.hexlify(buf)

if __name__ == '__main__':
	test()




