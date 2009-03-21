import Yapasn1 as asn1

import MapAsn
import TcapAsn

import binascii
def o(x):
	return binascii.unhexlify(x.replace(' ', ''))

def oo(x):
	return binascii.hexlify(x)

def test_map():
	# MapAsn.sendRoutingInfoForSM result
	AddressString=asn1.OCTSTRING
	ISDN_AddressString=AddressString
	TBCD_STRING=asn1.OCTSTRING
	IMSI=TBCD_STRING
	LMSI=asn1.OCTSTRING
	ExtensionContainer=asn1.SEQUENCE ([], seq_name = 'ExtensionContainer')
	LocationInfoWithLMSI=asn1.SEQUENCE ([('networkNode_Number',None,asn1.TYPE(asn1.EXPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('lmsi',None,LMSI,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'LocationInfoWithLMSI')
	RoutingInfoForSM_Res=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('locationInfoWithLMSI',None,asn1.TYPE(asn1.EXPLICIT(0,cls=asn1.CONTEXT_FLAG),LocationInfoWithLMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.EXPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RoutingInfoForSM_Res')

	
	for encoded, pdu in [
#		("301a 040491103254 a012 3010 a108 0406 912222222222 0404 01020304", MapAsn.RoutingInfoForSM_Res), 
		("62644804000227846b3e283c060700118605010101a031602fa109060704000001001302be222820060704000001010101a015a01380099622123008016901f98106a807000000016c1ca11a02010102013b301204010f0405a3986c36028006a80700000001", TcapAsn.TCMessage),
#		("626a48042f3b46026b3a2838060700118605010101a02d602b80020780a109060704000001001302be1a2818060704000001010101a00da00b80099656051124006913f66c26a12402010102013b301c04010f040eaa180da682dd6c31192d36bbdd468007917267415827f2", TcapAsn.TCMessage),
	]:
		encoded = o(encoded)
		print "Decoding..."
		decoded = asn1.decode(pdu, encoded)
		print
		print "Decoded:"
		print repr(decoded)
		print
		print "Re-encoding..."
		reencoded = asn1.encode(pdu, decoded)
		print
		print "Re-encoded:"	
		print oo(reencoded)
		print "Original:"
		print oo(encoded)
		# The reencoded is probably different from the original due to construct and length forms variants, so we can't compare them
		print
		print "Re-decoding..."
		redecoded = asn1.decode(pdu, reencoded)
		print
		print "Redecoded:"
		print repr(redecoded)
		assert(redecoded == decoded)
		print "Re-re-encoding..."
		rereencoded = asn1.encode(pdu, redecoded)
		print
		print "Re-re-encoded:"
		print oo(rereencoded)
		print "Previous iteration:"
		print oo(reencoded)
		assert(rereencoded == reencoded)


"""
6264
		4804
				00022784
								6b3e283c060700118605010101a031602fa109060704000001001302be222820060704000001010101a015a01380099622123008016901f98106a807000000016c1ca11a02010102013b301204010f0405a3986c36028006a80700000001
"""		


def test_sample():
	# Samples from X.690-0207
	Name=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.APPLICATION_FLAG), asn1.SEQUENCE([('givenName', None, asn1.VisibleString, 0),
		('initial', None, asn1.VisibleString, 0),
		('familyName', None, asn1.VisibleString, 0)], seq_name = 'Name'))
	EmployeeNumber=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG), asn1.INTEGER_class([],0,2147483647))
	Date=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.APPLICATION_FLAG), asn1.VisibleString)
	ChildInformation=asn1.SEQUENCE([('name',None,Name,0),('dateOfBirth',asn1.EXPLICIT(0,cls=asn1.CONTEXT_FLAG),Date,0)], seq_name = 'ChildInformation')
	
	PersonnelRecord=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.APPLICATION_FLAG), asn1.SEQUENCE([
		('name',None,Name,0),
		('title',None,asn1.TYPE(asn1.EXPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.VisibleString),0),
		('number',None,EmployeeNumber,1),
		('dateOfHire',None,asn1.TYPE(asn1.EXPLICIT(1,cls=asn1.CONTEXT_FLAG),Date),0),
		('nameOfSpouse',None,asn1.TYPE(asn1.EXPLICIT(2,cls=asn1.CONTEXT_FLAG),Name),0),
		('children',None,asn1.TYPE(asn1.EXPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE_OF(ChildInformation)),0),
		], seq_name = 'PersonnelRecord'))
	
	decoded = {
		'name': { 'givenName': 'John', 'initial': 'P', 'familyName': 'Smith' },
		'title': 'Director',
		'number': 51,
		'dateOfHire': '19710917',
		'nameOfSpouse': { 'givenName': 'Mary', 'initial': 'T', 'familyName': 'Smith' },
		'children': [
			{ 'name': { 'givenName': 'Ralph', 'initial': 'T', 'familyName': 'Smith' },
			  'dateOfBirth': '19571111' },
			{ 'name': { 'givenName': 'Susan', 'initial': 'B', 'familyName': 'Jones' },
			  'dateOfBirth': '19590717' },
		]}
	
	pdu = PersonnelRecord
	print "Encoded:"
	encoded = asn1.encode(pdu, decoded)
	print oo(encoded)
	print "Decoded:"
	redecoded = asn1.decode(pdu, encoded)
	print repr(redecoded)
	assert(redecoded == decoded)
	print "Re-encoded:"	
	reencoded = asn1.encode(pdu, redecoded)
	print oo(reencoded)
	print "Original:"
	print oo(encoded)
	assert(encoded == reencoded)
				

if __name__ == '__main__':
	test_map()

