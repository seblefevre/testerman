# Auto-generated at Mon, 08 Oct 2012 15:04:21 +0000
# with the following command line:
# ./py_output.py --explicit asn/RFC1157-SMI.asn
import Yapasn1 as asn1
#module RFC1157-SNMP None
Counter=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
ObjectName=asn1.OBJECT_IDENTIFIER
Opaque=asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.APPLICATION_FLAG),asn1.OCTSTRING)
TimeTicks=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
SimpleSyntax=asn1.CHOICE ([('number',None,asn1.INTEGER_class ([],None,None)),
    ('string',None,asn1.OCTSTRING),
    ('object',None,asn1.OBJECT_IDENTIFIER),
    ('empty',None,asn1.NULL)])
Gauge=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([],0,4294967295))
IpAddress=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.APPLICATION_FLAG),asn1.OCTSTRING)
NetworkAddress=asn1.CHOICE ([('internet',None,IpAddress)])
ApplicationSyntax=asn1.CHOICE ([('address',None,NetworkAddress),
    ('counter',None,Counter),
    ('gauge',None,Gauge),
    ('ticks',None,TimeTicks),
    ('arbitrary',None,Opaque)])
ObjectSyntax=asn1.CHOICE ([('simple',None,SimpleSyntax),
    ('application-wide',None,ApplicationSyntax)])
VarBind=asn1.SEQUENCE ([('name',None,ObjectName,0,None),
    ('value',None,ObjectSyntax,0,None)], seq_name = 'VarBind')
VarBindList=asn1.SEQUENCE_OF (VarBind)
PDU=asn1.SEQUENCE ([('request-id',None,asn1.INTEGER_class ([],None,None),0,None),
    ('error-status',None,asn1.INTEGER_class ([('noError',0),('tooBig',1),('noSuchName',2),('badValue',3),('readOnly',4),('genErr',5)],None,None),0,None),
    ('error-index',None,asn1.INTEGER_class ([],None,None),0,None),
    ('variable-bindings',None,VarBindList,0,None)], seq_name = 'PDU')
GetRequest_PDU=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),PDU)
GetResponse_PDU=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),PDU)
GetNextRequest_PDU=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),PDU)
Trap_PDU=asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('enterprise',None,asn1.OBJECT_IDENTIFIER,0,None),
    ('agent-addr',None,NetworkAddress,0,None),
    ('generic-trap',None,asn1.INTEGER_class ([('coldStart',0),('warmStart',1),('linkDown',2),('linkUp',3),('authenticationFailure',4),('egpNeighborLoss',5),('enterpriseSpecific',6)],None,None),0,None),
    ('specific-trap',None,asn1.INTEGER_class ([],None,None),0,None),
    ('time-stamp',None,TimeTicks,0,None),
    ('variable-bindings',None,VarBindList,0,None)], seq_name = 'Trap-PDU'))
SetRequest_PDU=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),PDU)
PDUs=asn1.CHOICE ([('get-request',None,GetRequest_PDU),
    ('get-next-request',None,GetNextRequest_PDU),
    ('get-response',None,GetResponse_PDU),
    ('set-request',None,SetRequest_PDU),
    ('trap',None,Trap_PDU)])
Message=asn1.SEQUENCE ([('version',None,asn1.INTEGER_class ([('version_1',0)],None,None),0,None),
    ('community',None,asn1.OCTSTRING,0,None),
    ('data',None,PDUs,0,None)], seq_name = 'Message')


