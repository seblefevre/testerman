# Auto-generated at Mon, 08 Oct 2012 15:05:58 +0000
# with the following command line:
# ./py_output.py --explicit asn/RFC2578-SMIv2.asn
import Yapasn1 as asn1
#module COMMUNITY-BASED-SNMPv2 None
Opaque=asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.APPLICATION_FLAG),asn1.OCTSTRING)
TimeTicks=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
NotificationName=asn1.OBJECT_IDENTIFIER
IpAddress=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.APPLICATION_FLAG),asn1.OCTSTRING)
Counter64=asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,18446744073709551615))
Unsigned32=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
Gauge32=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
Integer32=asn1.INTEGER_class ([],-2147483648,2147483647)
ObjectName=asn1.OBJECT_IDENTIFIER
SimpleSyntax=asn1.CHOICE ([('integer-value',None,asn1.INTEGER_class ([],-2147483648,2147483647)),
    ('string-value',None,asn1.OCTSTRING),
    ('objectID-value',None,asn1.OBJECT_IDENTIFIER)])
Counter32=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
ApplicationSyntax=asn1.CHOICE ([('ipAddress-value',None,IpAddress),
    ('counter-value',None,Counter32),
    ('timeticks-value',None,TimeTicks),
    ('arbitrary-value',None,Opaque),
    ('big-counter-value',None,Counter64),
    ('unsigned-integer-value',None,Unsigned32)])
ObjectSyntax=asn1.CHOICE ([('simple',None,SimpleSyntax),
    ('application-wide',None,ApplicationSyntax)])
VarBind=asn1.SEQUENCE ([('name',None,ObjectName,0,None),
    ('choice',None,    asn1.CHOICE ([('value',None,ObjectSyntax),
        ('unSpecified',None,asn1.NULL),
        ('noSuchObject',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
        ('noSuchInstance',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
        ('endOfMibView',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL))]),0,None)], seq_name = 'VarBind')
VarBindList=asn1.SEQUENCE_OF (VarBind)
PDU=asn1.SEQUENCE ([('request-id',None,Integer32,0,None),
    ('error-status',None,asn1.INTEGER_class ([('noError',0),('tooBig',1),('noSuchName',2),('badValue',3),('readOnly',4),('genErr',5),('noAccess',6),('wrongType',7),('wrongLength',8),('wrongEncoding',9),('wrongValue',10),('noCreation',11),('inconsistentValue',12),('resourceUnavailable',13),('commitFailed',14),('undoFailed',15),('authorizationError',16),('notWritable',17),('inconsistentName',18)],None,None),0,None),
    ('error-index',None,asn1.INTEGER_class ([],0,2147483647),0,None),
    ('variable-bindings',None,VarBindList,0,None)], seq_name = 'PDU')
Response_PDU=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),PDU)
Report_PDU=asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),PDU)
SetRequest_PDU=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),PDU)
GetNextRequest_PDU=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),PDU)
InformRequest_PDU=asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),PDU)
GetRequest_PDU=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),PDU)
SNMPv2_Trap_PDU=asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),PDU)
BulkPDU=asn1.SEQUENCE ([('request-id',None,Integer32,0,None),
    ('non-repeaters',None,asn1.INTEGER_class ([],0,2147483647),0,None),
    ('max-repetitions',None,asn1.INTEGER_class ([],0,2147483647),0,None),
    ('variable-bindings',None,VarBindList,0,None)], seq_name = 'BulkPDU')
GetBulkRequest_PDU=asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),BulkPDU)
PDUs=asn1.CHOICE ([('get-request',None,GetRequest_PDU),
    ('get-next-request',None,GetNextRequest_PDU),
    ('get-bulk-request',None,GetBulkRequest_PDU),
    ('response',None,Response_PDU),
    ('set-request',None,SetRequest_PDU),
    ('inform-request',None,InformRequest_PDU),
    ('snmpV2-trap',None,SNMPv2_Trap_PDU),
    ('report',None,Report_PDU)])
Message=asn1.SEQUENCE ([('version',None,asn1.INTEGER_class ([('version',1)],None,None),0,None),
    ('community',None,asn1.OCTSTRING,0,None),
    ('data',None,PDUs,0,None)], seq_name = 'Message')


