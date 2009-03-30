# Auto-generated at Mon, 30 Mar 2009 14:43:03 +0000
# with the following command line:
# ./py_output.py --implicit asn/tcap.asn
import Yapasn1 as asn1
#module TCAPMessages None
P_AbortCause=asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.APPLICATION_FLAG),asn1.INTEGER_class ([('unrecognizedMessageType',0),('unrecognizedTransactionID',1),('badlyFormattedTransactionPortion',2),('incorrectTransactionPortion',3),('resourceLimitation',4)],0,127))
InvokeIdType=asn1.INTEGER_class ([],-128,127)
ERROR=asn1.CHOICE ([('localValue',None,asn1.INTEGER_class ([],None,None)),
    ('globalValue',None,asn1.OBJECT_IDENTIFIER)])
ReturnResultProblem=asn1.INTEGER_class ([('unrecognizedInvokeID',0),('returnResultUnexpected',1),('mistypedParameter',2)],None,None)
Parameter=asn1.ANY
ErrorCode=asn1.CHOICE ([('nationaler',None,asn1.TYPE(asn1.IMPLICIT(19,cls=asn1.PRIVATE_FLAG),asn1.INTEGER_class ([],-32768,32767))),
    ('privateer',None,asn1.TYPE(asn1.IMPLICIT(20,cls=asn1.PRIVATE_FLAG),asn1.INTEGER_class ([],None,None)))])
ReturnError=asn1.SEQUENCE ([('invokeID',None,InvokeIdType,0,None),
    ('errorCode',None,ErrorCode,0,None),
    ('parameter',None,Parameter,1,None)], seq_name = 'ReturnError')
ReturnErrorProblem=asn1.INTEGER_class ([('unrecognizedInvokeID',0),('returnErrorUnexpected',1),('unrecognizedError',2),('unexpectedError',3),('mistypedParameter',4)],None,None)
InvokeProblem=asn1.INTEGER_class ([('duplicateInvokeID',0),('unrecognizedOperation',1),('mistypedParameter',2),('resourceLimitation',3),('initiatingRelease',4),('unrecognizedLinkedID',5),('linkedResponseUnexpected',6),('unexpectedLinkedOperation',7)],None,None)
GeneralProblem=asn1.INTEGER_class ([('unrecognizedComponent',0),('mistypedComponent',1),('badlyStructuredComponent',2)],None,None)
OPERATION=asn1.CHOICE ([('localValue',None,asn1.INTEGER_class ([],None,None)),
    ('globalValue',None,asn1.OBJECT_IDENTIFIER)])
Dialog1=asn1.OCTSTRING
ExternalPDU=asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.UNIVERSAL_FLAG),asn1.SEQUENCE ([('oid',None,asn1.OBJECT_IDENTIFIER,0,None),
    ('dialog',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Dialog1),0,None)], seq_name = 'ExternalPDU'))
OrigTransactionID=asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.APPLICATION_FLAG),asn1.OCTSTRING)
DestTransactionID=asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.APPLICATION_FLAG),asn1.OCTSTRING)
DialoguePortion=asn1.TYPE(asn1.EXPLICIT(11,cls=asn1.APPLICATION_FLAG),asn1.EXTERNAL)
Reject=asn1.SEQUENCE ([('invokeIDRej',None,    asn1.CHOICE ([('derivable',None,InvokeIdType),
        ('not_derivable',None,asn1.NULL)]),0,None),
    ('problem',None,    asn1.CHOICE ([('generalProblem',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GeneralProblem)),
        ('invokeProblem',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),InvokeProblem)),
        ('returnResultProblem',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ReturnResultProblem)),
        ('returnErrorProblem',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ReturnErrorProblem))]),0,None)], seq_name = 'Reject')
Invoke=asn1.SEQUENCE ([('invokeID',None,InvokeIdType,0,None),
    ('linkedID',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),InvokeIdType),1,None),
    ('opCode',None,OPERATION,0,None),
    ('parameter',None,Parameter,1,None)], seq_name = 'Invoke')
ReturnResult=asn1.SEQUENCE ([('invokeID',None,InvokeIdType,0,None),
    ('resultretres',None,    asn1.SEQUENCE ([('opCode',None,OPERATION,0,None),
        ('parameter',None,Parameter,1,None)], seq_name = None),1,None)], seq_name = 'ReturnResult')
Component=asn1.CHOICE ([('invoke',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Invoke)),
    ('returnResultLast',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ReturnResult)),
    ('returnError',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ReturnError)),
    ('reject',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Reject)),
    ('returnResultNotLast',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ReturnResult))])
Reason=asn1.CHOICE ([('p-abortCause',None,P_AbortCause),
    ('u-abortCause',None,DialoguePortion)])
Abort=asn1.SEQUENCE ([('dtid',None,DestTransactionID,0,None),
    ('reason',None,Reason,1,None)], seq_name = 'Abort')
ComponentPortion=asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE_OF (Component))
End=asn1.SEQUENCE ([('dtid',None,DestTransactionID,0,None),
    ('dialoguePortion',None,DialoguePortion,1,None),
    ('components',None,ComponentPortion,1,None)], seq_name = 'End')
Begin=asn1.SEQUENCE ([('otid',None,OrigTransactionID,0,None),
    ('dialoguePortion',None,DialoguePortion,1,None),
    ('components',None,ComponentPortion,1,None)], seq_name = 'Begin')
Continue=asn1.SEQUENCE ([('otid',None,OrigTransactionID,0,None),
    ('dtid',None,DestTransactionID,0,None),
    ('dialoguePortion',None,DialoguePortion,1,None),
    ('components',None,ComponentPortion,1,None)], seq_name = 'Continue')
Unidirectional=asn1.SEQUENCE ([('dialoguePortion',None,DialoguePortion,1,None),
    ('components',None,ComponentPortion,0,None)], seq_name = 'Unidirectional')
TCMessage=asn1.CHOICE ([('unidirectional',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.APPLICATION_FLAG),Unidirectional)),
    ('begin',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG),Begin)),
    ('end',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.APPLICATION_FLAG),End)),
    ('continue',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.APPLICATION_FLAG),Continue)),
    ('abort',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.APPLICATION_FLAG),Abort))])


