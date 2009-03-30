# Auto-generated at Mon, 30 Mar 2009 14:52:02 +0000
# with the following command line:
# ./py_output.py --explicit asn/DialoguePDUs.asn
import Yapasn1 as asn1
#module DialoguePDUs None
Associate_source_diagnostic=asn1.CHOICE ([('dialogue-service-user',None,asn1.TYPE(asn1.EXPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.INTEGER_class ([('null',0),('no-reason-given',1),('application-context-name-not-supported',2)],None,None))),
    ('dialogue-service-provider',None,asn1.TYPE(asn1.EXPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.INTEGER_class ([('null',0),('no-reason-given',1),('no-common-dialogue-portion',2)],None,None)))])
Associate_result=asn1.INTEGER_class ([('accepted',0),('reject-permanent',1)],None,None)
Release_request_reason=asn1.INTEGER_class ([('normal',0),('urgent',1),('user-defined',30)],None,None)
Release_response_reason=asn1.INTEGER_class ([('normal',0),('not-finished',1),('user-defined',30)],None,None)
AARQ_apdu=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('protocol-version',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.BITSTRING_class ([('version1',0)],None,None)),1,'version1'),
    ('application-context-name',None,asn1.TYPE(asn1.EXPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.OBJECT_IDENTIFIER),0,None),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1,None)], seq_name = 'AARQ-apdu'))
ABRT_source=asn1.INTEGER_class ([('dialogue-service-user',0),('dialogue-service-provider',1)],None,None)
RLRQ_apdu=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('reason',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Release_request_reason),1,None),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1,None)], seq_name = 'RLRQ-apdu'))
AARE_apdu=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('protocol-version',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.BITSTRING_class ([('version1',0)],None,None)),1,'version1'),
    ('application-context-name',None,asn1.TYPE(asn1.EXPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.OBJECT_IDENTIFIER),0,None),
    ('result',None,asn1.TYPE(asn1.EXPLICIT(2,cls=asn1.CONTEXT_FLAG),Associate_result),0,None),
    ('result-source-diagnostic',None,asn1.TYPE(asn1.EXPLICIT(3,cls=asn1.CONTEXT_FLAG),Associate_source_diagnostic),0,None),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1,None)], seq_name = 'AARE-apdu'))
RLRE_apdu=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('reason',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Release_response_reason),1,None),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1,None)], seq_name = 'RLRE-apdu'))
ABRT_apdu=asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('abort-source',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ABRT_source),0,None),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1,None)], seq_name = 'ABRT-apdu'))
DialoguePDU=asn1.CHOICE ([('dialogueRequest',None,AARQ_apdu),
    ('dialogueResponse',None,AARE_apdu),
    ('dialogueAbort',None,ABRT_apdu)])


