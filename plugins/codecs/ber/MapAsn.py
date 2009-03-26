# Auto-generated at Thu, 26 Mar 2009 16:40:07 +0000
# with the following command line:
# ./py_output.py --implicit asn/MAP-All.asn
import Yapasn1 as asn1
#module MAP-CommonDataTypes None
MulticallBearerInfo=asn1.INTEGER_class ([],1,7)
SS_Status=asn1.OCTSTRING
OR_Phase=asn1.INTEGER_class ([],1,127)
IntraCUG_Options=asn1.ENUM({'noCUG-Restrictions':0,'cugIC-CallBarred':1,'cugOG-CallBarred':2})
Ext_TeleserviceCode=asn1.OCTSTRING
TeleserviceList=asn1.SEQUENCE_OF (Ext_TeleserviceCode)
T_BcsmTriggerDetectionPoint=asn1.ENUM({'termAttemptAuthorized':12,'tBusy':13,'tNoAnswer':14})
SupportedLCS_CapabilitySets=asn1.BITSTRING_class ([('lcsCapabilitySet1',0),('lcsCapabilitySet2',1),('lcsCapabilitySet3',2),('lcsCapabilitySet4',3),('lcsCapabilitySet5',4)],None,None)
Release_response_reason=asn1.INTEGER_class ([('normal',0),('not-finished',1),('user-defined',30)],None,None)
CallTerminationIndicator=asn1.ENUM({'terminateCallActivityReferred':0,'terminateAllCallActivities':1})
ChosenChannelInfo=asn1.OCTSTRING
ChargingCharacteristics=asn1.OCTSTRING
TraceDepth=asn1.ENUM({'minimum':0,'medium':1,'maximum':2})
Associate_source_diagnostic=asn1.CHOICE ([('dialogue-service-user',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.INTEGER_class ([('null',0),('no-reason-given',1),('application-context-name-not-supported',2)],None,None))),
    ('dialogue-service-provider',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.INTEGER_class ([('null',0),('no-reason-given',1),('no-common-dialogue-portion',2)],None,None)))])
ISDN_SubaddressString=asn1.OCTSTRING
SRES=asn1.OCTSTRING
LSAOnlyAccessIndicator=asn1.ENUM({'accessOutsideLSAsAllowed':0,'accessOutsideLSAsRestricted':1})
HopCounter=asn1.INTEGER_class ([],0,3)
MW_Status=asn1.BITSTRING_class ([('sc-AddressNotIncluded',0),('mnrf-Set',1),('mcef-Set',2),('mnrg-Set',3)],None,None)
AlertReason=asn1.ENUM({'ms-Present':0,'memoryAvailable':1})
SMS_TriggerDetectionPoint=asn1.ENUM({'sms-CollectedInfo':1,'sms-DeliveryRequest':2})
CallTypeCriteria=asn1.ENUM({'forwarded':0,'notForwarded':1})
CUG_RejectCause=asn1.ENUM({'incomingCallsBarredWithinCUG':0,'subscriberNotMemberOfCUG':1,'requestedBasicServiceViolatesCUG-Constraints':5,'calledPartySS-InteractionViolation':7})
OverrideCategory=asn1.ENUM({'overrideEnabled':0,'overrideDisabled':1})
MSNetworkCapability=asn1.OCTSTRING
Category=asn1.OCTSTRING
RNC_InterfaceList=asn1.BITSTRING_class ([('iu',0),('iur',1),('iub',2),('uu',3)],None,None)
ProtocolId=asn1.ENUM({'gsm-0408':1,'gsm-0806':2,'gsm-BSSMAP':3,'ets-300102-1':4})
NAEA_CIC=asn1.OCTSTRING
MM_Code=asn1.OCTSTRING
MS_Classmark2=asn1.OCTSTRING
MGW_InterfaceList=asn1.BITSTRING_class ([('mc',0),('nb-up',1),('iu-up',2)],None,None)
ForwardingReason=asn1.ENUM({'notReachable':0,'busy':1,'noReply':2})
RNCId=asn1.OCTSTRING
CellGlobalIdOrServiceAreaIdFixedLength=asn1.OCTSTRING
BearerServiceCode=asn1.OCTSTRING
GGSN_InterfaceList=asn1.BITSTRING_class ([('gn',0),('gi',1),('gmb',2)],None,None)
LAIFixedLength=asn1.OCTSTRING
BMSC_InterfaceList=asn1.BITSTRING_class ([('gmb',0)],None,None)
OfferedCamel4CSIs=asn1.BITSTRING_class ([('o-csi',0),('d-csi',1),('vt-csi',2),('t-csi',3),('mt-sms-csi',4),('mg-csi',5),('psi-enhancements',6)],None,None)
GeodeticInformation=asn1.OCTSTRING
InterrogationType=asn1.ENUM({'basicCall':0,'forwarding':1})
PDP_Address=asn1.OCTSTRING
AARQ_apdu=asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('protocol-version',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.BITSTRING_class ([('version1',0)],None,None)),0),
    ('application-context-name',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.OBJECT_IDENTIFIER),0),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1)], seq_name = 'AARQ-apdu'))
SM_RP_SMEA=asn1.OCTSTRING
EncryptionInformation=asn1.OCTSTRING
DefaultSMS_Handling=asn1.ENUM({'continueTransaction':0,'releaseTransaction':1})
Release_request_reason=asn1.INTEGER_class ([('normal',0),('urgent',1),('user-defined',30)],None,None)
SM_DeliveryOutcome=asn1.ENUM({'memoryCapacityExceeded':0,'absentSubscriber':1,'successfulTransfer':2})
Codec=asn1.OCTSTRING
TEID=asn1.OCTSTRING
LongTermDenialParam=asn1.SEQUENCE ([], seq_name = 'LongTermDenialParam')
CallOutcome=asn1.ENUM({'success':0,'failure':1,'busy':2})
PositionMethodFailure_Diagnostic=asn1.ENUM({'congestion':0,'insufficientResources':1,'insufficientMeasurementData':2,'inconsistentMeasurementData':3,'locationProcedureNotCompleted':4,'locationProcedureNotSupportedByTargetMS':5,'qoSNotAttainable':6,'positionMethodNotAvailableInNetwork':7,'positionMethodNotAvailableInLocationArea':8})
ServiceIndicator=asn1.BITSTRING_class ([('clir-invoked',0),('camel-invoked',1)],None,None)
NotReachableReason=asn1.ENUM({'msPurged':0,'imsiDetached':1,'restrictedArea':2,'notRegistered':3})
AgeIndicator=asn1.OCTSTRING
AddressString=asn1.OCTSTRING
Ext_ProtocolId=asn1.ENUM({'ets-300356':1})
PLMN_Id=asn1.OCTSTRING
MonitoringMode=asn1.ENUM({'a-side':0,'b-side':1})
SM_EnumeratedDeliveryFailureCause=asn1.ENUM({'memoryCapacityExceeded':0,'equipmentProtocolError':1,'equipmentNotSM-Equipped':2,'unknownServiceCentre':3,'sc-Congestion':4,'invalidSME-Address':5,'subscriberNotSC-Subscriber':6})
RAB_Id=asn1.INTEGER_class ([],1,255)
TransactionId=asn1.OCTSTRING
SM_DeliveryNotIntended=asn1.ENUM({'onlyIMSI-requested':0,'onlyMCC-MNC-requested':1})
RoamingNotAllowedCause=asn1.ENUM({'plmnRoamingNotAllowed':0,'operatorDeterminedBarring':3})
MaxMC_Bearers=asn1.INTEGER_class ([],2,7)
SupportedCCBS_Phase=asn1.INTEGER_class ([],1,127)
NetworkResource=asn1.ENUM({'plmn':0,'hlr':1,'vlr':2,'pvlr':3,'controllingMSC':4,'vmsc':5,'eir':6,'rss':7})
USSD_DataCodingScheme=asn1.OCTSTRING
QoS_Subscribed=asn1.OCTSTRING
APN=asn1.OCTSTRING
AdditionalNetworkResource=asn1.ENUM({'sgsn':0,'ggsn':1,'gmlc':2,'gsmSCF':3,'nplr':4,'auc':5,'ue':6})
UUIndicator=asn1.OCTSTRING
IntegrityProtectionInformation=asn1.OCTSTRING
ModificationInstruction=asn1.ENUM({'deactivate':0,'activate':1})
SS_Code=asn1.OCTSTRING
NumberOfRequestedVectors=asn1.INTEGER_class ([],1,5)
TraceReference2=asn1.OCTSTRING
KSI=asn1.OCTSTRING
CCBS_Index=asn1.INTEGER_class ([],1,5)
GERAN_Classmark=asn1.OCTSTRING
OfferedCamel4Functionalities=asn1.BITSTRING_class ([('initiateCallAttempt',0),('splitLeg',1),('moveLeg',2),('disconnectLeg',3),('entityReleased',4),('dfc-WithArgument',5),('playTone',6),('dtmf-MidCall',7),('chargingIndicator',8),('alertingDP',9),('locationAtAlerting',10),('changeOfPositionDP',11),('or-Interactions',12),('warningToneEnhancements',13),('cf-Enhancements',14),('subscribedEnhancedDialledServices',15),('servingNetworkEnhancedDialledServices',16),('criteriaForChangeOfPositionDP',17),('serviceChangeDP',18),('collectInformation',19)],None,None)
DefaultGPRS_Handling=asn1.ENUM({'continueTransaction':0,'releaseTransaction':1})
AUTS=asn1.OCTSTRING
DefaultCallHandling=asn1.ENUM({'continueCall':0,'releaseCall':1})
SS_EventSpecification=asn1.SEQUENCE_OF (AddressString)
PermittedIntegrityProtectionAlgorithms=asn1.OCTSTRING
CCBS_SubscriberStatus=asn1.ENUM({'ccbsNotIdle':0,'ccbsIdle':1,'ccbsNotReachable':2})
SupportedRAT_Types=asn1.BITSTRING_class ([('utran',0),('geran',1)],None,None)
AdditionalRequestedCAMEL_SubscriptionInfo=asn1.ENUM({'mt-sms-CSI':0,'mg-csi':1,'o-IM-CSI':2,'d-IM-CSI':3,'vt-IM-CSI':4})
Kc=asn1.OCTSTRING
SelectedGSM_Algorithm=asn1.OCTSTRING
FailureCause=asn1.ENUM({'wrongUserResponse':0,'wrongNetworkSignature':1})
CamelCapabilityHandling=asn1.INTEGER_class ([],1,16)
TraceRecordingSessionReference=asn1.OCTSTRING
TBCD_STRING=asn1.OCTSTRING
CauseValue=asn1.OCTSTRING
UUI=asn1.OCTSTRING
MC_Bearers=asn1.INTEGER_class ([],1,7)
ODB_GeneralData=asn1.BITSTRING_class ([('allOG-CallsBarred',0),('internationalOGCallsBarred',1),('internationalOGCallsNotToHPLMN-CountryBarred',2),('interzonalOGCallsBarred',6),('interzonalOGCallsNotToHPLMN-CountryBarred',7),('interzonalOGCallsAndInternationalOGCallsNotToHPLMN-CountryBarred',8),('premiumRateInformationOGCallsBarred',3),('premiumRateEntertainementOGCallsBarred',4),('ss-AccessBarred',5),('allECT-Barred',9),('chargeableECT-Barred',10),('internationalECT-Barred',11),('interzonalECT-Barred',12),('doublyChargeableECT-Barred',13),('multipleECT-Barred',14),('allPacketOrientedServicesBarred',15),('roamerAccessToHPLMN-AP-Barred',16),('roamerAccessToVPLMN-AP-Barred',17),('roamingOutsidePLMNOG-CallsBarred',18),('allIC-CallsBarred',19),('roamingOutsidePLMNIC-CallsBarred',20),('roamingOutsidePLMNICountryIC-CallsBarred',21),('roamingOutsidePLMN-Barred',22),('roamingOutsidePLMN-CountryBarred',23),('registrationAllCF-Barred',24),('registrationCFNotToHPLMN-Barred',25),('registrationInterzonalCF-Barred',26),('registrationInterzonalCFNotToHPLMN-Barred',27),('registrationInternationalCF-Barred',28)],None,None)
UESBI_IuB=asn1.BITSTRING_class ([],None,None)
UESBI_IuA=asn1.BITSTRING_class ([],None,None)
MSC_S_InterfaceList=asn1.BITSTRING_class ([('a',0),('iu',1),('mc',2),('map-g',3),('map-b',4),('map-e',5),('map-f',6),('cap',7),('map-d',8),('map-c',9)],None,None)
TraceDepthList=asn1.SEQUENCE ([('msc-s-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('mgw-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('sgsn-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('ggsn-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('rnc-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('bmsc-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),TraceDepth),1)], seq_name = 'TraceDepthList')
RadioResourceInformation=asn1.OCTSTRING
MSC_S_EventList=asn1.BITSTRING_class ([('mo-mtCall',0),('mo-mt-sms',1),('lu-imsiAttach-imsiDetach',2),('handovers',3),('ss',4)],None,None)
SuppressionOfAnnouncement=asn1.NULL
AbsentSubscriberDiagnosticSM=asn1.INTEGER_class ([],0,255)
UnavailabilityCause=asn1.ENUM({'bearerServiceNotProvisioned':1,'teleserviceNotProvisioned':2,'absentSubscriber':3,'busySubscriber':4,'callBarred':5,'cug-Reject':6})
CallBarringCause=asn1.ENUM({'barringServiceActive':0,'operatorBarring':1})
EquipmentStatus=asn1.ENUM({'whiteListed':0,'blackListed':1,'greyListed':2})
ReportingState=asn1.ENUM({'stopMonitoring':0,'startMonitoring':1})
ContextId=asn1.INTEGER_class ([],1,50)
NoReplyConditionTime=asn1.INTEGER_class ([],5,30)
EMLPP_Priority=asn1.INTEGER_class ([],0,15)
AdditionalRoamingNotAllowedCause=asn1.ENUM({'supportedRAT-TypesNotAllowed':0})
PW_RegistrationFailureCause=asn1.ENUM({'undetermined':0,'invalidFormat':1,'newPasswordsMismatch':2})
GPRS_TriggerDetectionPoint=asn1.ENUM({'attach':1,'attachChangeOfPosition':2,'pdp-ContextEstablishment':11,'pdp-ContextEstablishmentAcknowledgement':12,'pdp-ContextChangeOfPosition':14})
DomainType=asn1.ENUM({'cs-Domain':0,'ps-Domain':1})
RadioResource=asn1.SEQUENCE ([('radioResourceInformation',None,RadioResourceInformation,0),
    ('rab-Id',None,RAB_Id,0)], seq_name = 'RadioResource')
LongSignalInfo=asn1.OCTSTRING
RequestingNodeType=asn1.ENUM({'vlr':0,'sgsn':1,'s-cscf':2,'bsf':3,'gan-aaa-server':4,'wlan-aaa-server':5})
EraseCC_EntryArg=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ccbs-Index',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CCBS_Index),1)], seq_name = 'EraseCC-EntryArg')
BMSC_EventList=asn1.BITSTRING_class ([('mbmsMulticastServiceActivation',0)],None,None)
Ext_QoS_Subscribed=asn1.OCTSTRING
TraceNE_TypeList=asn1.BITSTRING_class ([('msc-s',0),('mgw',1),('sgsn',2),('ggsn',3),('rnc',4),('bm-sc',5)],None,None)
Associate_result=asn1.INTEGER_class ([('accepted',0),('reject-permanent',1)],None,None)
CallReferenceNumber=asn1.OCTSTRING
InterCUG_Restrictions=asn1.OCTSTRING
DestinationNumberLengthList=asn1.SEQUENCE_OF (asn1.INTEGER_class ([],1,15))
SS_EventList=asn1.SEQUENCE_OF (SS_Code)
RLRQ_apdu=asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('reason',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Release_request_reason),1),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1)], seq_name = 'RLRQ-apdu'))
ABRT_source=asn1.INTEGER_class ([('dialogue-service-user',0),('dialogue-service-provider',1)],None,None)
MT_SMS_TPDU_Type=asn1.ENUM({'sms-DELIVER':0,'sms-SUBMIT-REPORT':1,'sms-STATUS-REPORT':2})
GGSN_EventList=asn1.BITSTRING_class ([('pdpContext',0),('mbmsContext',1)],None,None)
ForwardingOptions=asn1.OCTSTRING
ServiceKey=asn1.INTEGER_class ([],0,2147483647)
SuppressMTSS=asn1.BITSTRING_class ([('suppressCUG',0),('suppressCCBS',1)],None,None)
RouteingNumber=TBCD_STRING
ExtensionContainer=asn1.SEQUENCE ([], seq_name = 'ExtensionContainer')
CUG_Interlock=asn1.OCTSTRING
ChosenSpeechVersion=asn1.OCTSTRING
SpecificCSI_Withdraw=asn1.BITSTRING_class ([('o-csi',0),('ss-csi',1),('tif-csi',2),('d-csi',3),('vt-csi',4),('mo-sms-csi',5),('m-csi',6),('gprs-csi',7),('t-csi',8),('mt-sms-csi',9),('mg-csi',10),('o-IM-CSI',11),('d-IM-CSI',12),('vt-IM-CSI',13)],None,None)
ISDN_AddressString=AddressString
SubBusyForMT_SMS_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SubBusyForMT-SMS-Param')
CCBS_RequestState=asn1.ENUM({'request':0,'recall':1,'active':2,'completed':3,'suspended':4,'frozen':5,'deleted':6})
CS_AllocationRetentionPriority=asn1.OCTSTRING
ResourceLimitationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ResourceLimitationParam')
GMLC_List=asn1.SEQUENCE_OF (ISDN_AddressString)
ChosenEncryptionAlgorithm=asn1.OCTSTRING
CancellationType=asn1.ENUM({'updateProcedure':0,'subscriptionWithdraw':1})
LSAAttributes=asn1.OCTSTRING
IST_SupportIndicator=asn1.ENUM({'basicISTSupported':0,'istCommandSupported':1})
ActivateTraceModeRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ActivateTraceModeRes')
RequestedCAMEL_SubscriptionInfo=asn1.ENUM({'o-CSI':0,'t-CSI':1,'vt-CSI':2,'tif-CSI':3,'gprs-CSI':4,'mo-sms-CSI':5,'ss-CSI':6,'m-CSI':7,'d-csi':8})
MSRadioAccessCapability=asn1.OCTSTRING
AccessType=asn1.ENUM({'call':0,'emergencyCall':1,'locationUpdating':2,'supplementaryService':3,'shortMessage':4,'gprsAttach':5,'routingAreaUpdating':6,'serviceRequest':7,'pdpContextActivation':8,'pdpContextDeactivation':9,'gprsDetach':10})
SubscriberState=asn1.CHOICE ([('assumedIdle',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('camelBusy',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('netDetNotReachable',None,NotReachableReason),
    ('notProvidedFromVLR',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL))])
RequestedEquipmentInfo=asn1.BITSTRING_class ([('equipmentStatus',0),('bmuef',1)],None,None)
UnknownSubscriberDiagnostic=asn1.ENUM({'imsiUnknown':0,'gprsSubscriptionUnknown':1,'npdbMismatch':2})
CK=asn1.OCTSTRING
NSAPI=asn1.INTEGER_class ([],0,15)
Long_GroupId=TBCD_STRING
SM_RP_MTI=asn1.INTEGER_class ([],0,10)
MatchType=asn1.ENUM({'inhibiting':0,'enabling':1})
AllowedServices=asn1.BITSTRING_class ([('firstServiceAllowed',0),('secondServiceAllowed',1)],None,None)
TargetCellOutsideGCA_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'TargetCellOutsideGCA-Param')
AbsentSubscriberSM_Param=asn1.SEQUENCE ([('absentSubscriberDiagnosticSM',None,AbsentSubscriberDiagnosticSM,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AbsentSubscriberSM-Param')
SGSN_InterfaceList=asn1.BITSTRING_class ([('gb',0),('iu',1),('gn',2),('map-gr',3),('map-gd',4),('map-gf',5),('gs',6),('ge',7)],None,None)
MGW_EventList=asn1.BITSTRING_class ([('context',0)],None,None)
ZoneCode=asn1.OCTSTRING
AlertingPattern=asn1.OCTSTRING
MM_EventNotSupported_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MM-EventNotSupported-Param')
ChosenRadioResourceInformation=asn1.SEQUENCE ([('chosenChannelInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ChosenChannelInfo),1),
    ('chosenSpeechVersion',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ChosenSpeechVersion),1)], seq_name = 'ChosenRadioResourceInformation')
NotificationToMSUser=asn1.ENUM({'notifyLocationAllowed':0,'notifyAndVerify-LocationAllowedIfNoResponse':1,'notifyAndVerify-LocationNotAllowedIfNoResponse':2,'locationNotAllowed':3})
CallDiversionTreatmentIndicator=asn1.OCTSTRING
FTN_AddressString=AddressString
ProvideRoamingNumberRes=asn1.SEQUENCE ([('roamingNumber',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ProvideRoamingNumberRes')
TraceType=asn1.INTEGER_class ([],0,255)
BSSMAP_ServiceHandover=asn1.OCTSTRING
ModificationRequestFor_CSI=asn1.SEQUENCE ([('requestedCamel-SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RequestedCAMEL_SubscriptionInfo),0),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('modifyCSI-State',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor-CSI')
SubscriberStatus=asn1.ENUM({'serviceGranted':0,'operatorDeterminedBarring':1})
InformServiceCentreArg=asn1.SEQUENCE ([('storedMSISDN',None,ISDN_AddressString,1),
    ('mw-Status',None,MW_Status,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'InformServiceCentreArg')
GeographicalInformation=asn1.OCTSTRING
AdditionalInfo=asn1.BITSTRING_class ([],None,None)
AUTN=asn1.OCTSTRING
PDP_Type=asn1.OCTSTRING
SupportedCamelPhases=asn1.BITSTRING_class ([('phase1',0),('phase2',1),('phase3',2),('phase4',3)],None,None)
O_BcsmTriggerDetectionPoint=asn1.ENUM({'collectedInfo':2,'routeSelectFailure':4})
IK=asn1.OCTSTRING
BSSMAP_ServiceHandoverInfo=asn1.SEQUENCE ([('bssmap-ServiceHandover',None,BSSMAP_ServiceHandover,0),
    ('rab-Id',None,RAB_Id,0)], seq_name = 'BSSMAP-ServiceHandoverInfo')
Cksn=asn1.OCTSTRING
AARE_apdu=asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('protocol-version',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.BITSTRING_class ([('version1',0)],None,None)),0),
    ('application-context-name',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.OBJECT_IDENTIFIER),0),
    ('result',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Associate_result),0),
    ('result-source-diagnostic',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Associate_source_diagnostic),0),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1)], seq_name = 'AARE-apdu'))
TeleservNotProvParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'TeleservNotProvParam')
AdditionalSubscriptions=asn1.BITSTRING_class ([('privilegedUplinkRequest',0),('emergencyUplinkRequest',1),('emergencyReset',2)],None,None)
UnidentifiedSubParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnidentifiedSubParam')
CliRestrictionOption=asn1.ENUM({'permanent':0,'temporaryDefaultRestricted':1,'temporaryDefaultAllowed':2})
IST_AlertTimerValue=asn1.INTEGER_class ([],15,255)
GroupId=TBCD_STRING
TeleserviceCode=asn1.OCTSTRING
ChosenIntegrityProtectionAlgorithm=asn1.OCTSTRING
LCSClientInternalID=asn1.ENUM({'broadcastService':0,'o-andM-HPLMN':1,'o-andM-VPLMN':2,'anonymousLocation':3,'targetMSsubscribedService':4})
Ext_NoRepCondTime=asn1.INTEGER_class ([],1,100)
NumberPortabilityStatus=asn1.ENUM({'notKnownToBePorted':0,'ownNumberPortedOut':1,'foreignNumberPortedToForeignNetwork':2,'ownNumberNotPortedOut':4,'foreignNumberPortedIn':5})
KeyStatus=asn1.ENUM({'old':0,'new':1})
FailureCauseParam=asn1.ENUM({'limitReachedOnNumberOfConcurrentLocationRequests':0})
T_BcsmCamelTDPData=asn1.SEQUENCE ([('t-BcsmTriggerDetectionPoint',None,T_BcsmTriggerDetectionPoint,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultCallHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DefaultCallHandling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'T-BcsmCamelTDPData')
IllegalSS_OperationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IllegalSS-OperationParam')
GlobalCellId=asn1.OCTSTRING
Ext_ForwOptions=asn1.OCTSTRING
NoSubscriberReplyParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoSubscriberReplyParam')
SM_RP_OA=asn1.CHOICE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString)),
    ('serviceCentreAddressOA',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AddressString)),
    ('noSM-RP-OA',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),asn1.NULL))])
RAIdentity=asn1.OCTSTRING
SGSN_EventList=asn1.BITSTRING_class ([('pdpContext',0),('mo-mt-sms',1),('rau-gprsAttach-gprsDetach',2),('mbmsContext',3)],None,None)
ReleaseResourcesArg=asn1.SEQUENCE ([('msrn',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReleaseResourcesArg')
GPRSMSClass=asn1.SEQUENCE ([('mSNetworkCapability',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MSNetworkCapability),0),
    ('mSRadioAccessCapability',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),MSRadioAccessCapability),1)], seq_name = 'GPRSMSClass')
BSSMAP_ServiceHandoverList=asn1.SEQUENCE_OF (BSSMAP_ServiceHandoverInfo)
GuidanceInfo=asn1.ENUM({'enterPW':0,'enterNewPW':1,'enterNewPW-Again':2})
RANAP_ServiceHandover=asn1.OCTSTRING
LMSI=asn1.OCTSTRING
UnauthorizedLCSClient_Diagnostic=asn1.ENUM({'noAdditionalInformation':0,'clientNotInMSPrivacyExceptionList':1,'callToClientNotSetup':2,'privacyOverrideNotApplicable':3,'disallowedByLocalRegulatoryRequirements':4,'unauthorizedPrivacyClass':5,'unauthorizedCallSessionUnrelatedExternalClient':6,'unauthorizedCallSessionRelatedExternalClient':7})
NoRoamingNbParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoRoamingNbParam')
AgeOfLocationInformation=asn1.INTEGER_class ([],0,32767)
RequestedInfo=asn1.SEQUENCE ([('locationInformation',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('subscriberState',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RequestedInfo')
RelocationNumber=asn1.SEQUENCE ([('handoverNumber',None,ISDN_AddressString,0),
    ('rab-Id',None,RAB_Id,0)], seq_name = 'RelocationNumber')
Ext_SS_Status=asn1.OCTSTRING
SS_CamelData=asn1.SEQUENCE ([('ss-EventList',None,SS_EventList,0),
    ('gsmSCF-Address',None,ISDN_AddressString,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SS-CamelData')
RLRE_apdu=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('reason',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Release_response_reason),1),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1)], seq_name = 'RLRE-apdu'))
AbsentSubscriberReason=asn1.ENUM({'imsiDetach':0,'restrictedArea':1,'noPageResponse':2,'purgedMS':3})
NumberOfForwarding=asn1.INTEGER_class ([],1,5)
DispatcherList=asn1.SEQUENCE_OF (ISDN_AddressString)
EventReportData=asn1.SEQUENCE ([('ccbs-SubscriberStatus',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_SubscriberStatus),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'EventReportData')
SS_List=asn1.SEQUENCE_OF (SS_Code)
AllowedGSM_Algorithms=asn1.OCTSTRING
SetReportingStateRes=asn1.SEQUENCE ([('ccbs-SubscriberStatus',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_SubscriberStatus),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SetReportingStateRes')
RegionalSubscriptionResponse=asn1.ENUM({'networkNode-AreaRestricted':0,'tooManyZoneCodes':1,'zoneCodesConflict':2,'regionalSubscNotSupported':3})
Ext_BearerServiceCode=asn1.OCTSTRING
Ext3_QoS_Subscribed=asn1.OCTSTRING
ForwardingData=asn1.SEQUENCE ([('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('forwardingOptions',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ForwardingOptions),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ForwardingData')
ODB_HPLMN_Data=asn1.BITSTRING_class ([('plmn-SpecificBarringType1',0),('plmn-SpecificBarringType2',1),('plmn-SpecificBarringType3',2),('plmn-SpecificBarringType4',3)],None,None)
GPRSChargingID=asn1.OCTSTRING
RAND=asn1.OCTSTRING
LocationNumber=asn1.OCTSTRING
NetworkAccessMode=asn1.ENUM({'bothMSCAndSGSN':0,'onlyMSC':1,'onlySGSN':2})
ReportSM_DeliveryStatusArg=asn1.SEQUENCE ([('msisdn',None,ISDN_AddressString,0),
    ('serviceCentreAddress',None,AddressString,0),
    ('sm-DeliveryOutcome',None,SM_DeliveryOutcome,0),
    ('absentSubscriberDiagnosticSM',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),AbsentSubscriberDiagnosticSM),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ReportSM-DeliveryStatusArg')
TraceInterfaceList=asn1.SEQUENCE ([('msc-s-List',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MSC_S_InterfaceList),1),
    ('mgw-List',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),MGW_InterfaceList),1),
    ('sgsn-List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SGSN_InterfaceList),1),
    ('ggsn-List',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),GGSN_InterfaceList),1),
    ('rnc-List',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),RNC_InterfaceList),1),
    ('bmsc-List',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),BMSC_InterfaceList),1)], seq_name = 'TraceInterfaceList')
LCSServiceTypeID=asn1.INTEGER_class ([],0,127)
SignalInfo=asn1.OCTSTRING
CUG_Index=asn1.INTEGER_class ([],0,32767)
GPRS_CamelTDPData=asn1.SEQUENCE ([('gprs-TriggerDetectionPoint',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GPRS_TriggerDetectionPoint),0),
    ('serviceKey',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ServiceKey),0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultSessionHandling',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),DefaultGPRS_Handling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'GPRS-CamelTDPData')
ContextIdList=asn1.SEQUENCE_OF (ContextId)
DeleteSubscriberDataRes=asn1.SEQUENCE ([('regionalSubscriptionResponse',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RegionalSubscriptionResponse),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'DeleteSubscriberDataRes')
MobilityTriggers=asn1.SEQUENCE_OF (MM_Code)
GMLC_Restriction=asn1.ENUM({'gmlc-List':0,'home-Country':1})
SelectedUMTS_Algorithms=asn1.SEQUENCE ([('integrityProtectionAlgorithm',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ChosenIntegrityProtectionAlgorithm),1),
    ('encryptionAlgorithm',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ChosenEncryptionAlgorithm),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SelectedUMTS-Algorithms')
M_CSI=asn1.SEQUENCE ([('mobilityTriggers',None,MobilityTriggers,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi-Active',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'M-CSI')
LSAIdentity=asn1.OCTSTRING
TMSI=asn1.OCTSTRING
PermittedEncryptionAlgorithms=asn1.OCTSTRING
GSN_Address=asn1.OCTSTRING
TraceReference=asn1.OCTSTRING
XRES=asn1.OCTSTRING
CodecList=asn1.SEQUENCE ([('codec1',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Codec),0),
    ('codec2',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('codec3',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('codec4',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('codec5',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('codec6',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('codec7',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('codec8',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),Codec),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CodecList')
ReleaseResourcesRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReleaseResourcesRes')
OngoingGroupCallParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'OngoingGroupCallParam')
AccessRestrictionData=asn1.BITSTRING_class ([('utranNotAllowed',0),('geranNotAllowed',1)],None,None)
RUF_Outcome=asn1.ENUM({'accepted':0,'rejected':1,'noResponseFromFreeMS':2,'noResponseFromBusyMS':3,'udubFromFreeMS':4,'udubFromBusyMS':5})
Password=asn1.NumericString
WrongPasswordAttemptsCounter=asn1.INTEGER_class ([],0,4)
USSD_String=asn1.OCTSTRING
CellGlobalIdOrServiceAreaIdOrLAI=asn1.CHOICE ([('cellGlobalIdOrServiceAreaIdFixedLength',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CellGlobalIdOrServiceAreaIdFixedLength)),
    ('laiFixedLength',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LAIFixedLength))])
SendEndSignal_Res=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendEndSignal-Res')
UnauthorizedRequestingNetwork_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnauthorizedRequestingNetwork-Param')
AccessNetworkProtocolId=asn1.ENUM({'ts3G-48006':1,'ts3G-25413':2})
ShortTermDenialParam=asn1.SEQUENCE ([], seq_name = 'ShortTermDenialParam')
AlertServiceCentreArg=asn1.SEQUENCE ([('msisdn',None,ISDN_AddressString,0),
    ('serviceCentreAddress',None,AddressString,0)], seq_name = 'AlertServiceCentreArg')
BearerServNotProvParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'BearerServNotProvParam')
Ext2_QoS_Subscribed=asn1.OCTSTRING
FacilityNotSupParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'FacilityNotSupParam')
ForwardingFailedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ForwardingFailedParam')
LocationInformationGPRS=asn1.SEQUENCE ([('cellGlobalIdOrServiceAreaIdOrLAI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CellGlobalIdOrServiceAreaIdOrLAI),1),
    ('routeingAreaIdentity',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RAIdentity),1),
    ('geographicalInformation',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),GeographicalInformation),1),
    ('sgsn-Number',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('selectedLSAIdentity',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),LSAIdentity),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LocationInformationGPRS')
ExternalSignalInfo=asn1.SEQUENCE ([('protocolId',None,ProtocolId,0),
    ('signalInfo',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ExternalSignalInfo')
SS_NotAvailableParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS-NotAvailableParam')
SendRoutingInfoForGprsRes=asn1.SEQUENCE ([('sgsn-Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GSN_Address),0),
    ('ggsn-Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('mobileNotReachableReason',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AbsentSubscriberDiagnosticSM),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoForGprsRes')
ExtensibleSystemFailureParam=asn1.SEQUENCE ([('networkResource',None,NetworkResource,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ExtensibleSystemFailureParam')
RoutingInfoForSM_Arg=asn1.SEQUENCE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('sm-RP-PRI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.BOOLEAN),0),
    ('serviceCentreAddress',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RoutingInfoForSM-Arg')
RoutingInfo=asn1.CHOICE ([('roamingNumber',None,ISDN_AddressString),
    ('forwardingData',None,ForwardingData)])
NoteMM_EventRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoteMM-EventRes')
OR_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'OR-NotAllowedParam')
AuthenticationFailureReportRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AuthenticationFailureReportRes')
BasicServiceCode=asn1.CHOICE ([('bearerService',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),BearerServiceCode)),
    ('teleservice',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),TeleserviceCode))])
CallReportData=asn1.SEQUENCE ([('monitoringMode',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MonitoringMode),1),
    ('callOutcome',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CallOutcome),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CallReportData')
NoteMsPresentForGprsRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NoteMsPresentForGprsRes')
IMSI=TBCD_STRING
ResumeCallHandlingRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ResumeCallHandlingRes')
Ext_ExternalSignalInfo=asn1.SEQUENCE ([('ext-ProtocolId',None,Ext_ProtocolId,0),
    ('signalInfo',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'Ext-ExternalSignalInfo')
IncompatibleTerminalParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IncompatibleTerminalParam')
IllegalSubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IllegalSubscriberParam')
ASCI_CallReference=TBCD_STRING
ReportSM_DeliveryStatusRes=asn1.SEQUENCE ([('storedMSISDN',None,ISDN_AddressString,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReportSM-DeliveryStatusRes')
DestinationNumberList=asn1.SEQUENCE_OF (ISDN_AddressString)
ModificationRequestFor_IP_SM_GW_Data=asn1.SEQUENCE ([('modifyRegistrationStatus',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor-IP-SM-GW-Data')
ReadyForSM_Arg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('alertReason',None,AlertReason,0),
    ('alertReasonIndicator',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReadyForSM-Arg')
MessageWaitListFullParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MessageWaitListFullParam')
DataMissingParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'DataMissingParam')
MT_ForwardSM_VGCS_Arg=asn1.SEQUENCE ([('asciCallReference',None,ASCI_CallReference,0),
    ('sm-RP-OA',None,SM_RP_OA,0),
    ('sm-RP-UI',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MT-ForwardSM-VGCS-Arg')
ATSI_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ATSI-NotAllowedParam')
NumberChangedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NumberChangedParam')
SM_RP_DA=asn1.CHOICE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI)),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LMSI)),
    ('serviceCentreAddressDA',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AddressString)),
    ('noSM-RP-DA',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),asn1.NULL))])
UESBI_Iu=asn1.SEQUENCE ([('uesbi-IuA',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),UESBI_IuA),1),
    ('uesbi-IuB',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),UESBI_IuB),1)], seq_name = 'UESBI-Iu')
NoGroupCallNbParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoGroupCallNbParam')
RestoreDataRes=asn1.SEQUENCE ([('hlr-Number',None,ISDN_AddressString,0),
    ('msNotReachable',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'RestoreDataRes')
BusySubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'BusySubscriberParam')
PDP_Context=asn1.SEQUENCE ([('pdp-ContextId',None,ContextId,0),
    ('pdp-Type',None,asn1.TYPE(asn1.IMPLICIT(16,cls=asn1.CONTEXT_FLAG),PDP_Type),0),
    ('pdp-Address',None,asn1.TYPE(asn1.IMPLICIT(17,cls=asn1.CONTEXT_FLAG),PDP_Address),1),
    ('qos-Subscribed',None,asn1.TYPE(asn1.IMPLICIT(18,cls=asn1.CONTEXT_FLAG),QoS_Subscribed),0),
    ('vplmnAddressAllowed',None,asn1.TYPE(asn1.IMPLICIT(19,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('apn',None,asn1.TYPE(asn1.IMPLICIT(20,cls=asn1.CONTEXT_FLAG),APN),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(21,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PDP-Context')
UpdateGprsLocationRes=asn1.SEQUENCE ([('hlr-Number',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateGprsLocationRes')
SetReportingStateArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('ccbs-Monitoring',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ReportingState),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SetReportingStateArg')
ServiceType=asn1.SEQUENCE ([('serviceTypeIdentity',None,LCSServiceTypeID,0),
    ('gmlc-Restriction',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GMLC_Restriction),1),
    ('notificationToMSUser',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),NotificationToMSUser),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ServiceType')
RoamingNotAllowedParam=asn1.SEQUENCE ([('roamingNotAllowedCause',None,RoamingNotAllowedCause,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'RoamingNotAllowedParam')
DeactivateTraceModeArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('traceReference',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceReference),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'DeactivateTraceModeArg')
SendIdentificationArg=asn1.SEQUENCE ([('tmsi',None,TMSI,0),
    ('numberOfRequestedVectors',None,NumberOfRequestedVectors,1),
    ('segmentationProhibited',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SendIdentificationArg')
SubscriberIdentity=asn1.CHOICE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI)),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString))])
TraceEventList=asn1.SEQUENCE ([('msc-s-List',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MSC_S_EventList),1),
    ('mgw-List',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),MGW_EventList),1),
    ('sgsn-List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SGSN_EventList),1),
    ('ggsn-List',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),GGSN_EventList),1),
    ('bmsc-List',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),BMSC_EventList),1)], seq_name = 'TraceEventList')
ReadyForSM_Res=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReadyForSM-Res')
MG_CSI=asn1.SEQUENCE ([('mobilityTriggers',None,MobilityTriggers,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi-Active',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'MG-CSI')
ABRT_apdu=asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.APPLICATION_FLAG),asn1.SEQUENCE ([('abort-source',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ABRT_source),0),
    ('user-information',None,asn1.TYPE(asn1.IMPLICIT(30,cls=asn1.CONTEXT_FLAG),    asn1.SEQUENCE_OF (asn1.EXTERNAL)),1)], seq_name = 'ABRT-apdu'))
ServiceTypeList=asn1.SEQUENCE_OF (ServiceType)
O_CauseValueCriteria=asn1.SEQUENCE_OF (CauseValue)
CancelLocationRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CancelLocationRes')
SuperChargerInfo=asn1.CHOICE ([('sendSubscriberData',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('subscriberDataStored',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),AgeIndicator))])
IMEI=TBCD_STRING
DestinationNumberCriteria=asn1.SEQUENCE ([('matchType',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MatchType),0),
    ('destinationNumberList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DestinationNumberList),1),
    ('destinationNumberLengthList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),DestinationNumberLengthList),1)], seq_name = 'DestinationNumberCriteria')
TracingBufferFullParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'TracingBufferFullParam')
ZoneCodeList=asn1.SEQUENCE_OF (ZoneCode)
PositionMethodFailure_Param=asn1.SEQUENCE ([('positionMethodFailure-Diagnostic',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),PositionMethodFailure_Diagnostic),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PositionMethodFailure-Param')
RemoteUserFreeRes=asn1.SEQUENCE ([('ruf-Outcome',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RUF_Outcome),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RemoteUserFreeRes')
IMSI_WithLMSI=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('lmsi',None,LMSI,0)], seq_name = 'IMSI-WithLMSI')
PLMNClientList=asn1.SEQUENCE_OF (LCSClientInternalID)
PurgeMS_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('vlr-Number',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('sgsn-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'PurgeMS-Arg'))
DP_AnalysedInfoCriterium=asn1.SEQUENCE ([('dialledNumber',None,ISDN_AddressString,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF-Address',None,ISDN_AddressString,0),
    ('defaultCallHandling',None,DefaultCallHandling,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'DP-AnalysedInfoCriterium')
MT_ForwardSM_Arg=asn1.SEQUENCE ([('sm-RP-DA',None,SM_RP_DA,0),
    ('sm-RP-OA',None,SM_RP_OA,0),
    ('sm-RP-UI',None,SignalInfo,0),
    ('moreMessagesToSend',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MT-ForwardSM-Arg')
FailureReportRes=asn1.SEQUENCE ([('ggsn-Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'FailureReportRes')
TPDU_TypeCriterion=asn1.SEQUENCE_OF (MT_SMS_TPDU_Type)
EraseCC_EntryRes=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_Status),1)], seq_name = 'EraseCC-EntryRes')
AccessNetworkSignalInfo=asn1.SEQUENCE ([('accessNetworkProtocolId',None,AccessNetworkProtocolId,0),
    ('signalInfo',None,LongSignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AccessNetworkSignalInfo')
LSAIdentityList=asn1.SEQUENCE_OF (LSAIdentity)
RadioResourceList=asn1.SEQUENCE_OF (RadioResource)
ExtensibleCallBarredParam=asn1.SEQUENCE ([('callBarringCause',None,CallBarringCause,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ExtensibleCallBarredParam')
CCBS_Indicators=asn1.SEQUENCE ([('ccbs-Possible',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('keepCCBS-CallIndicator',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CCBS-Indicators')
LCSClientExternalID=asn1.SEQUENCE ([('externalAddress',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LCSClientExternalID')
IST_AlertRes=asn1.SEQUENCE ([('istAlertTimer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IST_AlertTimerValue),1),
    ('istInformationWithdraw',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('callTerminationIndicator',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallTerminationIndicator),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'IST-AlertRes')
InformationNotAvailableParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'InformationNotAvailableParam')
DeactivateTraceModeRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'DeactivateTraceModeRes')
PDP_ContextInfo=asn1.SEQUENCE ([('pdp-ContextIdentifier',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ContextId),0),
    ('pdp-ContextActive',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('pdp-Type',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),PDP_Type),0),
    ('pdp-Address',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),PDP_Address),1),
    ('apn-Subscribed',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),APN),1),
    ('apn-InUse',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),APN),1),
    ('nsapi',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),NSAPI),1),
    ('transactionId',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),TransactionId),1),
    ('teid-ForGnAndGp',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),TEID),1),
    ('teid-ForIu',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),TEID),1),
    ('ggsn-Address',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('qos-Subscribed',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),Ext_QoS_Subscribed),1),
    ('qos-Requested',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),Ext_QoS_Subscribed),1),
    ('qos-Negotiated',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),Ext_QoS_Subscribed),1),
    ('chargingId',None,asn1.TYPE(asn1.IMPLICIT(14,cls=asn1.CONTEXT_FLAG),GPRSChargingID),1),
    ('chargingCharacteristics',None,asn1.TYPE(asn1.IMPLICIT(15,cls=asn1.CONTEXT_FLAG),ChargingCharacteristics),1),
    ('rnc-Address',None,asn1.TYPE(asn1.IMPLICIT(16,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(17,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PDP-ContextInfo')
Additional_Number=asn1.CHOICE ([('msc-Number',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString)),
    ('sgsn-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString))])
LocationInfoWithLMSI=asn1.SEQUENCE ([('networkNode-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('lmsi',None,LMSI,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'LocationInfoWithLMSI')
UU_Data=asn1.SEQUENCE ([('uuIndicator',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),UUIndicator),1),
    ('uui',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),UUI),1),
    ('uusCFInteraction',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'UU-Data')
SMS_CAMEL_TDP_Data=asn1.SEQUENCE ([('sms-TriggerDetectionPoint',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SMS_TriggerDetectionPoint),0),
    ('serviceKey',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ServiceKey),0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultSMS-Handling',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),DefaultSMS_Handling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SMS-CAMEL-TDP-Data')
UnexpectedDataParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnexpectedDataParam')
NAEA_PreferredCI=asn1.SEQUENCE ([('naea-PreferredCIC',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),NAEA_CIC),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NAEA-PreferredCI')
CUG_RejectParam=asn1.SEQUENCE ([('cug-RejectCause',None,CUG_RejectCause,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CUG-RejectParam')
T_CauseValueCriteria=asn1.SEQUENCE_OF (CauseValue)
T_BcsmCamelTDPDataList=asn1.SEQUENCE_OF (T_BcsmCamelTDPData)
CUG_CheckInfo=asn1.SEQUENCE ([('cug-Interlock',None,CUG_Interlock,0),
    ('cug-OutgoingAccess',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CUG-CheckInfo')
SS_SubscriptionOption=asn1.CHOICE ([('cliRestrictionOption',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CliRestrictionOption)),
    ('overrideCategory',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),OverrideCategory))])
MT_smsCAMELTDP_Criteria=asn1.SEQUENCE ([('sms-TriggerDetectionPoint',None,SMS_TriggerDetectionPoint,0),
    ('tpdu-TypeCriterion',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TPDU_TypeCriterion),1)], seq_name = 'MT-smsCAMELTDP-Criteria')
DialoguePDU=asn1.CHOICE ([('dialogueRequest',None,AARQ_apdu),
    ('dialogueResponse',None,AARE_apdu),
    ('dialogueAbort',None,ABRT_apdu)])
HLR_Id=IMSI
SS_SubscriptionViolationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS-SubscriptionViolationParam')
MC_SS_Info=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('nbrSB',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),MaxMC_Bearers),0),
    ('nbrUser',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),MC_Bearers),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MC-SS-Info')
CheckIMEI_Arg=asn1.SEQUENCE ([('imei',None,IMEI,0),
    ('requestedEquipmentInfo',None,RequestedEquipmentInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CheckIMEI-Arg')
GPRS_CamelTDPDataList=asn1.SEQUENCE_OF (GPRS_CamelTDPData)
AbsentSubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AbsentSubscriberParam')
PurgeMS_Res=asn1.SEQUENCE ([('freezeTMSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('freezeP-TMSI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'PurgeMS-Res')
MT_ForwardSM_Res=asn1.SEQUENCE ([('sm-RP-UI',None,SignalInfo,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MT-ForwardSM-Res')
MT_ForwardSM_VGCS_Res=asn1.SEQUENCE ([('sm-RP-UI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SignalInfo),1),
    ('dispatcherList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DispatcherList),1),
    ('ongoingCall',None,asn1.NULL,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MT-ForwardSM-VGCS-Res')
UpdateLocationRes=asn1.SEQUENCE ([('hlr-Number',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateLocationRes')
MO_ForwardSM_Arg=asn1.SEQUENCE ([('sm-RP-DA',None,SM_RP_DA,0),
    ('sm-RP-OA',None,SM_RP_OA,0),
    ('sm-RP-UI',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MO-ForwardSM-Arg')
MO_ForwardSM_Res=asn1.SEQUENCE ([('sm-RP-UI',None,SignalInfo,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MO-ForwardSM-Res')
ATI_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ATI-NotAllowedParam')
MNPInfoRes=asn1.SEQUENCE ([('routeingNumber',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RouteingNumber),1),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('numberPortabilityStatus',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),NumberPortabilityStatus),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MNPInfoRes')
Re_synchronisationInfo=asn1.SEQUENCE ([('rand',None,RAND,0),
    ('auts',None,AUTS,0)], seq_name = 'Re-synchronisationInfo')
IllegalEquipmentParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IllegalEquipmentParam')
USSD_Arg=asn1.SEQUENCE ([('ussd-DataCodingScheme',None,USSD_DataCodingScheme,0),
    ('ussd-String',None,USSD_String,0)], seq_name = 'USSD-Arg')
FailureReportArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('ggsn-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('ggsn-Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'FailureReportArg')
EMLPP_Info=asn1.SEQUENCE ([('maximumentitledPriority',None,EMLPP_Priority,0),
    ('defaultPriority',None,EMLPP_Priority,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'EMLPP-Info')
UnauthorizedLCSClient_Param=asn1.SEQUENCE ([('unauthorizedLCSClient-Diagnostic',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),UnauthorizedLCSClient_Diagnostic),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'UnauthorizedLCSClient-Param')
IST_CommandRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IST-CommandRes')
NoteSubscriberDataModifiedRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoteSubscriberDataModifiedRes')
SendAuthenticationInfoArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('numberOfRequestedVectors',None,NumberOfRequestedVectors,0),
    ('segmentationProhibited',None,asn1.NULL,1),
    ('immediateResponsePreferred',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('re-synchronisationInfo',None,Re_synchronisationInfo,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendAuthenticationInfoArg')
ProcessAccessSignalling_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an-APDU',None,AccessNetworkSignalInfo,0),
    ('selectedUMTS-Algorithms',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SelectedUMTS_Algorithms),1),
    ('selectedGSM-Algorithm',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SelectedGSM_Algorithm),1),
    ('chosenRadioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ChosenRadioResourceInformation),1),
    ('selectedRab-Id',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),RAB_Id),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ProcessAccessSignalling-Arg'))
StatusReportRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'StatusReportRes')
SS_InvocationNotificationRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS-InvocationNotificationRes')
StatusReportArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('eventReportData',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),EventReportData),1),
    ('callReportdata',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallReportData),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'StatusReportArg')
UMTS_SecurityContextData=asn1.SEQUENCE ([('ck',None,CK,0),
    ('ik',None,IK,0),
    ('ksi',None,KSI,0)], seq_name = 'UMTS-SecurityContextData')
ODB_Data=asn1.SEQUENCE ([('odb-GeneralData',None,ODB_GeneralData,0),
    ('odb-HPLMN-Data',None,ODB_HPLMN_Data,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ODB-Data')
AuthenticationFailureReportArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('failureCause',None,FailureCause,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AuthenticationFailureReportArg')
ForwardingViolationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ForwardingViolationParam')
ATM_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ATM-NotAllowedParam')
AuthenticationQuintuplet=asn1.SEQUENCE ([('rand',None,RAND,0),
    ('xres',None,XRES,0),
    ('ck',None,CK,0),
    ('ik',None,IK,0),
    ('autn',None,AUTN,0)], seq_name = 'AuthenticationQuintuplet')
ADD_Info=asn1.SEQUENCE ([('imeisv',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMEI),0),
    ('skipSubscriberDataUpdate',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'ADD-Info')
RelocationNumberList=asn1.SEQUENCE_OF (RelocationNumber)
BearerServiceList=asn1.SEQUENCE_OF (Ext_BearerServiceCode)
MT_smsCAMELTDP_CriteriaList=asn1.SEQUENCE_OF (MT_smsCAMELTDP_Criteria)
UnknownOrUnreachableLCSClient_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnknownOrUnreachableLCSClient-Param')
SubscriberId=asn1.CHOICE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI)),
    ('tmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TMSI))])
InsertSubscriberDataRes=asn1.SEQUENCE ([('teleserviceList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TeleserviceList),1),
    ('bearerServiceList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),BearerServiceList),1),
    ('ss-List',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SS_List),1),
    ('odb-GeneralData',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ODB_GeneralData),1),
    ('regionalSubscriptionResponse',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),RegionalSubscriptionResponse),1),
    ('supportedCamelPhases',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'InsertSubscriberDataRes')
UnknownSubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnknownSubscriberParam')
USSD_Res=asn1.SEQUENCE ([('ussd-DataCodingScheme',None,USSD_DataCodingScheme,0),
    ('ussd-String',None,USSD_String,0)], seq_name = 'USSD-Res')
GSM_SecurityContextData=asn1.SEQUENCE ([('kc',None,Kc,0),
    ('cksn',None,Cksn,0)], seq_name = 'GSM-SecurityContextData')
CamelInfo=asn1.SEQUENCE ([('supportedCamelPhases',None,SupportedCamelPhases,0),
    ('suppress-T-CSI',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CamelInfo')
ModificationRequestFor_ODB_data=asn1.SEQUENCE ([('odb-data',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ODB_Data),1),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor-ODB-data')
O_BcsmCamelTDPData=asn1.SEQUENCE ([('o-BcsmTriggerDetectionPoint',None,O_BcsmTriggerDetectionPoint,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultCallHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DefaultCallHandling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'O-BcsmCamelTDPData')
Identity=asn1.CHOICE ([('imsi',None,IMSI),
    ('imsi-WithLMSI',None,IMSI_WithLMSI)])
ForwardingFeature=asn1.SEQUENCE ([('basicService',None,BasicServiceCode,1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('forwardingOptions',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ForwardingOptions),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),NoReplyConditionTime),1)], seq_name = 'ForwardingFeature')
GPRSSubscriptionDataWithdraw=asn1.CHOICE ([('allGPRSData',None,asn1.NULL),
    ('contextIdList',None,ContextIdList)])
IST_CommandArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'IST-CommandArg')
ProvideRoamingNumberArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('msc-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('gsm-BearerCapability',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),1),
    ('networkSignalInfo',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),1),
    ('suppressionOfAnnouncement',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),SuppressionOfAnnouncement),1),
    ('gmsc-Address',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('callReferenceNumber',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),CallReferenceNumber),1),
    ('or-Interrogation',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ProvideRoamingNumberArg')
SM_DeliveryFailureCause=asn1.SEQUENCE ([('sm-EnumeratedDeliveryFailureCause',None,SM_EnumeratedDeliveryFailureCause,0),
    ('diagnosticInfo',None,SignalInfo,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SM-DeliveryFailureCause')
SS_InvocationNotificationArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('ss-Event',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ss-EventSpecification',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SS_EventSpecification),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SS-InvocationNotificationArg')
RegisterSS_Arg=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('basicService',None,BasicServiceCode,1),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),NoReplyConditionTime),1)], seq_name = 'RegisterSS-Arg')
VoiceBroadcastData=asn1.SEQUENCE ([('groupid',None,GroupId,0),
    ('broadcastInitEntitlement',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'VoiceBroadcastData')
AllowedUMTS_Algorithms=asn1.SEQUENCE ([('integrityProtectionAlgorithms',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),PermittedIntegrityProtectionAlgorithms),1),
    ('encryptionAlgorithms',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),PermittedEncryptionAlgorithms),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AllowedUMTS-Algorithms')
ActivateTraceModeArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('traceReference',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceReference),0),
    ('traceType',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),TraceType),0),
    ('omc-Id',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),AddressString),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ActivateTraceModeArg')
MOLR_Class=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('ss-Status',None,Ext_SS_Status,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MOLR-Class')
VoiceGroupCallData=asn1.SEQUENCE ([('groupId',None,GroupId,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'VoiceGroupCallData')
SS_CSI=asn1.SEQUENCE ([('ss-CamelData',None,SS_CamelData,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS-CSI')
TracePropagationList=asn1.SEQUENCE ([('traceReference',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TraceReference),1),
    ('traceType',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceType),1),
    ('traceReference2',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),TraceReference2),1),
    ('traceRecordingSessionReference',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),TraceRecordingSessionReference),1),
    ('rnc-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('rnc-InterfaceList',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),RNC_InterfaceList),1),
    ('msc-s-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('msc-s-InterfaceList',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),MSC_S_InterfaceList),1),
    ('msc-s-EventList',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),MSC_S_EventList),1),
    ('mgw-TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('mgw-InterfaceList',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),MGW_InterfaceList),1),
    ('mgw-EventList',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),MGW_EventList),1)], seq_name = 'TracePropagationList')
SS_IncompatibilityCause=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_Code),1),
    ('basicService',None,BasicServiceCode,1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1)], seq_name = 'SS-IncompatibilityCause')
ProvideSubscriberInfoArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('requestedInfo',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),RequestedInfo),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ProvideSubscriberInfoArg')
LSAData=asn1.SEQUENCE ([('lsaIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),LSAIdentity),0),
    ('lsaAttributes',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LSAAttributes),0),
    ('lsaActiveModeIndicator',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LSAData')
AuthenticationTriplet=asn1.SEQUENCE ([('rand',None,RAND,0),
    ('sres',None,SRES,0),
    ('kc',None,Kc,0)], seq_name = 'AuthenticationTriplet')
CheckIMEI_Res=asn1.SEQUENCE ([('equipmentStatus',None,EquipmentStatus,1),
    ('bmuef',None,UESBI_Iu,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CheckIMEI-Res')
Ext_BasicServiceCode=asn1.CHOICE ([('ext-BearerService',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Ext_BearerServiceCode)),
    ('ext-Teleservice',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Ext_TeleserviceCode))])
NoteMsPresentForGprsArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('sgsn-Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GSN_Address),0),
    ('ggsn-Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NoteMsPresentForGprsArg')
BasicServiceGroupList=asn1.SEQUENCE_OF (BasicServiceCode)
RoutingInfoForSM_Res=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('locationInfoWithLMSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),LocationInfoWithLMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RoutingInfoForSM-Res')
LocationInformation=asn1.SEQUENCE ([('ageOfLocationInformation',None,AgeOfLocationInformation,1),
    ('geographicalInformation',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GeographicalInformation),1),
    ('vlr-number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('locationNumber',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),LocationNumber),1),
    ('cellGlobalIdOrServiceAreaIdOrLAI',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),CellGlobalIdOrServiceAreaIdOrLAI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LocationInformation')
CUG_Feature=asn1.SEQUENCE ([('basicService',None,Ext_BasicServiceCode,1),
    ('preferentialCUG-Indicator',None,CUG_Index,1),
    ('interCUG-Restrictions',None,InterCUG_Restrictions,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CUG-Feature')
GPRS_CSI=asn1.SEQUENCE ([('gprs-CamelTDPDataList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GPRS_CamelTDPDataList),1),
    ('camelCapabilityHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CamelCapabilityHandling),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi-Active',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'GPRS-CSI')
T_CSI=asn1.SEQUENCE ([('t-BcsmCamelTDPDataList',None,T_BcsmCamelTDPDataList,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'T-CSI')
ModificationRequestFor_CF_Info=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('basicService',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),1),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),Ext_NoRepCondTime),1),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor-CF-Info')
CUG_FeatureList=asn1.SEQUENCE_OF (CUG_Feature)
ODB_Info=asn1.SEQUENCE ([('odb-Data',None,ODB_Data,0),
    ('notificationToCSE',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ODB-Info')
SystemFailureParam=asn1.CHOICE ([('networkResource',None,NetworkResource),
    ('extensibleSystemFailureParam',None,ExtensibleSystemFailureParam)])
SGSN_Capability=asn1.SEQUENCE ([('solsaSupportIndicator',None,asn1.NULL,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SGSN-Capability')
PrepareHO_Res=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('handoverNumber',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('relocationNumberList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RelocationNumberList),1),
    ('an-APDU',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AccessNetworkSignalInfo),1),
    ('multicallBearerInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),MulticallBearerInfo),1),
    ('multipleBearerNotSupported',None,asn1.NULL,1),
    ('selectedUMTS-Algorithms',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),SelectedUMTS_Algorithms),1),
    ('chosenRadioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ChosenRadioResourceInformation),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareHO-Res'))
PDP_ContextInfoList=asn1.SEQUENCE_OF (PDP_ContextInfo)
IST_AlertArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'IST-AlertArg')
CallBarringFeature=asn1.SEQUENCE ([('basicService',None,BasicServiceCode,1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1)], seq_name = 'CallBarringFeature')
VLR_Capability=asn1.SEQUENCE ([('supportedCamelPhases',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'VLR-Capability')
SupportedCodecsList=asn1.SEQUENCE ([('utranCodecList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CodecList),1),
    ('geranCodecList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CodecList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SupportedCodecsList')
UpdateGprsLocationArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('sgsn-Number',None,ISDN_AddressString,0),
    ('sgsn-Address',None,GSN_Address,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateGprsLocationArg')
GPRSDataList=asn1.SEQUENCE_OF (PDP_Context)
SendRoutingInfoForGprsArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('ggsn-Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('ggsn-Number',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoForGprsArg')
SS_ForBS_Code=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('basicService',None,BasicServiceCode,1)], seq_name = 'SS-ForBS-Code')
DP_AnalysedInfoCriteriaList=asn1.SEQUENCE_OF (DP_AnalysedInfoCriterium)
CCBS_Feature=asn1.SEQUENCE ([('ccbs-Index',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_Index),1),
    ('b-subscriberNumber',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('b-subscriberSubaddress',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('basicServiceGroup',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),BasicServiceCode),1)], seq_name = 'CCBS-Feature')
UpdateLocationArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('msc-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('vlr-Number',None,ISDN_AddressString,0),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateLocationArg')
CallBarringFeatureList=asn1.SEQUENCE_OF (CallBarringFeature)
QuintupletList=asn1.SEQUENCE_OF (AuthenticationQuintuplet)
SendEndSignal_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an-APDU',None,AccessNetworkSignalInfo,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendEndSignal-Arg'))
PrepareSubsequentHO_Res=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an-APDU',None,AccessNetworkSignalInfo,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareSubsequentHO-Res'))
CCBS_Data=asn1.SEQUENCE ([('ccbs-Feature',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_Feature),0),
    ('translatedB-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('serviceIndicator',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ServiceIndicator),1),
    ('callInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),0),
    ('networkSignalInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),0)], seq_name = 'CCBS-Data')
PrepareSubsequentHO_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('targetCellId',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GlobalCellId),1),
    ('targetMSC-Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('targetRNCId',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),RNCId),1),
    ('an-APDU',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),AccessNetworkSignalInfo),1),
    ('selectedRab-Id',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),RAB_Id),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareSubsequentHO-Arg'))
AnyTimeInterrogationArg=asn1.SEQUENCE ([('subscriberIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SubscriberIdentity),0),
    ('requestedInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RequestedInfo),0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AnyTimeInterrogationArg')
Ext_ForwFeature=asn1.SEQUENCE ([('basicService',None,Ext_BasicServiceCode,1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('forwardingOptions',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),Ext_ForwOptions),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),Ext_NoRepCondTime),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext-ForwFeature')
CallBarredParam=asn1.CHOICE ([('callBarringCause',None,CallBarringCause),
    ('extensibleCallBarredParam',None,ExtensibleCallBarredParam)])
RemoteUserFreeArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('callInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),0),
    ('ccbs-Feature',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CCBS_Feature),0),
    ('translatedB-Number',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('replaceB-Number',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('alertingPattern',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),AlertingPattern),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RemoteUserFreeArg')
CancelLocationArg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('identity',None,Identity,0),
    ('cancellationType',None,CancellationType,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CancelLocationArg'))
ExternalClient=asn1.SEQUENCE ([('clientIdentity',None,LCSClientExternalID,0),
    ('gmlc-Restriction',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GMLC_Restriction),1),
    ('notificationToMSUser',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),NotificationToMSUser),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ExternalClient')
RequestedSubscriptionInfo=asn1.SEQUENCE ([('requestedSS-Info',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_ForBS_Code),1),
    ('odb',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('requestedCAMEL-SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),RequestedCAMEL_SubscriptionInfo),1),
    ('supportedVLR-CAMEL-Phases',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('supportedSGSN-CAMEL-Phases',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RequestedSubscriptionInfo')
LSAInformationWithdraw=asn1.CHOICE ([('allLSAData',None,asn1.NULL),
    ('lsaIdentityList',None,LSAIdentityList)])
MOLR_List=asn1.SEQUENCE_OF (MOLR_Class)
ForwardAccessSignalling_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an-APDU',None,AccessNetworkSignalInfo,0),
    ('integrityProtectionInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IntegrityProtectionInformation),1),
    ('encryptionInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),EncryptionInformation),1),
    ('keyStatus',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),KeyStatus),1),
    ('allowedGSM-Algorithms',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AllowedGSM_Algorithms),1),
    ('allowedUMTS-Algorithms',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),AllowedUMTS_Algorithms),1),
    ('radioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),RadioResourceInformation),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ForwardAccessSignalling-Arg'))
Ext_ForwFeatureList=asn1.SEQUENCE_OF (Ext_ForwFeature)
AnyTimeSubscriptionInterrogationArg=asn1.SEQUENCE ([('subscriberIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SubscriberIdentity),0),
    ('requestedSubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RequestedSubscriptionInfo),0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('longFTN-Supported',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'AnyTimeSubscriptionInterrogationArg')
SMS_CAMEL_TDP_DataList=asn1.SEQUENCE_OF (SMS_CAMEL_TDP_Data)
SS_Data=asn1.SEQUENCE ([('ss-Code',None,SS_Code,1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1),
    ('ss-SubscriptionOption',None,SS_SubscriptionOption,1),
    ('basicServiceGroupList',None,BasicServiceGroupList,1)], seq_name = 'SS-Data')
LSADataList=asn1.SEQUENCE_OF (LSAData)
HLR_List=asn1.SEQUENCE_OF (HLR_Id)
ForwardingFeatureList=asn1.SEQUENCE_OF (ForwardingFeature)
CallBarringInfo=asn1.SEQUENCE ([('ss-Code',None,SS_Code,1),
    ('callBarringFeatureList',None,CallBarringFeatureList,0)], seq_name = 'CallBarringInfo')
RegisterCC_EntryRes=asn1.SEQUENCE ([('ccbs-Feature',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_Feature),1)], seq_name = 'RegisterCC-EntryRes')
GPRSSubscriptionData=asn1.SEQUENCE ([('completeDataListIncluded',None,asn1.NULL,1),
    ('gprsDataList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GPRSDataList),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'GPRSSubscriptionData')
NoteMM_EventArg=asn1.SEQUENCE ([('serviceKey',None,ServiceKey,0),
    ('eventMet',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MM_Code),0),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('locationInformation',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),LocationInformation),1),
    ('supportedCAMELPhases',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NoteMM-EventArg')
PrepareHO_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('targetCellId',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GlobalCellId),1),
    ('ho-NumberNotRequired',None,asn1.NULL,1),
    ('targetRNCId',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RNCId),1),
    ('an-APDU',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AccessNetworkSignalInfo),1),
    ('multipleBearerRequested',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('integrityProtectionInfo',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),IntegrityProtectionInformation),1),
    ('encryptionInfo',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),EncryptionInformation),1),
    ('radioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),RadioResourceInformation),1),
    ('allowedGSM-Algorithms',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),AllowedGSM_Algorithms),1),
    ('allowedUMTS-Algorithms',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),AllowedUMTS_Algorithms),1),
    ('radioResourceList',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),RadioResourceList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareHO-Arg'))
VBSDataList=asn1.SEQUENCE_OF (VoiceBroadcastData)
CallForwardingData=asn1.SEQUENCE ([('forwardingFeatureList',None,Ext_ForwFeatureList,0),
    ('notificationToCSE',None,asn1.NULL,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CallForwardingData')
SMS_CSI=asn1.SEQUENCE ([('sms-CAMEL-TDP-DataList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SMS_CAMEL_TDP_DataList),1),
    ('camelCapabilityHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CamelCapabilityHandling),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi-Active',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'SMS-CSI')
ResetArg=asn1.SEQUENCE ([('hlr-Number',None,ISDN_AddressString,0),
    ('hlr-List',None,HLR_List,1)], seq_name = 'ResetArg')
CurrentSecurityContext=asn1.CHOICE ([('gsm-SecurityContextData',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GSM_SecurityContextData)),
    ('umts-SecurityContextData',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),UMTS_SecurityContextData))])
D_CSI=asn1.SEQUENCE ([('dp-AnalysedInfoCriteriaList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),DP_AnalysedInfoCriteriaList),1),
    ('camelCapabilityHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CamelCapabilityHandling),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi-Active',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'D-CSI')
PS_SubscriberState=asn1.CHOICE ([('notProvidedFromSGSN',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps-Detached',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps-AttachedNotReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps-AttachedReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps-PDP-ActiveNotReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),PDP_ContextInfoList)),
    ('ps-PDP-ActiveReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),PDP_ContextInfoList)),
    ('netDetNotReachable',None,NotReachableReason)])
SGSN_CAMEL_SubscriptionInfo=asn1.SEQUENCE ([('gprs-CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GPRS_CSI),1),
    ('mo-sms-CSI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SMS_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SGSN-CAMEL-SubscriptionInfo')
CCBS_FeatureList=asn1.SEQUENCE_OF (CCBS_Feature)
SendRoutingInfoArg=asn1.SEQUENCE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('cug-CheckInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CUG_CheckInfo),1),
    ('numberOfForwarding',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),NumberOfForwarding),1),
    ('interrogationType',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),InterrogationType),0),
    ('or-Interrogation',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('or-Capability',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),OR_Phase),1),
    ('gmsc-OrGsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('callReferenceNumber',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),CallReferenceNumber),1),
    ('forwardingReason',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ForwardingReason),1),
    ('basicServiceGroup',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('networkSignalInfo',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),1),
    ('camelInfo',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),CamelInfo),1),
    ('suppressionOfAnnouncement',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),SuppressionOfAnnouncement),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoArg')
O_BcsmCamelTDPDataList=asn1.SEQUENCE_OF (O_BcsmCamelTDPData)
RegisterCC_EntryArg=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ccbs-Data',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CCBS_Data),1)], seq_name = 'RegisterCC-EntryArg')
BasicServiceList=asn1.SEQUENCE_OF (Ext_BasicServiceCode)
VGCSDataList=asn1.SEQUENCE_OF (VoiceGroupCallData)
TripletList=asn1.SEQUENCE_OF (AuthenticationTriplet)
ExternalClientList=asn1.SEQUENCE_OF (ExternalClient)
Ext_ForwardingInfoFor_CSE=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('forwardingFeatureList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_ForwFeatureList),0),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext-ForwardingInfoFor-CSE')
RestoreDataArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('lmsi',None,LMSI,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'RestoreDataArg')
ModificationRequestFor_CB_Info=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('basicService',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),1),
    ('password',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Password),1),
    ('wrongPasswordAttemptsCounter',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),WrongPasswordAttemptsCounter),1),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor-CB-Info')
LSAInformation=asn1.SEQUENCE ([('completeDataListIncluded',None,asn1.NULL,1),
    ('lsaOnlyAccessIndicator',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LSAOnlyAccessIndicator),1),
    ('lsaDataList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),LSADataList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LSAInformation')
BasicServiceCriteria=asn1.SEQUENCE_OF (Ext_BasicServiceCode)
Ext_BasicServiceGroupList=asn1.SEQUENCE_OF (Ext_BasicServiceCode)
Ext_CallBarringFeature=asn1.SEQUENCE ([('basicService',None,Ext_BasicServiceCode,1),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'Ext-CallBarringFeature')
Ext_ForwInfo=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('forwardingFeatureList',None,Ext_ForwFeatureList,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext-ForwInfo')
Ext_SS_Data=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('ss-SubscriptionOption',None,SS_SubscriptionOption,1),
    ('basicServiceGroupList',None,Ext_BasicServiceGroupList,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext-SS-Data')
MSISDN_BS=asn1.SEQUENCE ([('msisdn',None,ISDN_AddressString,0),
    ('basicServiceList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),BasicServiceList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MSISDN-BS')
AuthenticationSetList=asn1.CHOICE ([('tripletList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TripletList)),
    ('quintupletList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),QuintupletList))])
AnyTimeModificationArg=asn1.SEQUENCE ([('subscriberIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SubscriberIdentity),0),
    ('gsmSCF-Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('modificationRequestFor-CF-Info',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ModificationRequestFor_CF_Info),1),
    ('modificationRequestFor-CB-Info',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ModificationRequestFor_CB_Info),1),
    ('modificationRequestFor-CSI',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ModificationRequestFor_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('longFTN-Supported',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'AnyTimeModificationArg')
CUG_Subscription=asn1.SEQUENCE ([('cug-Index',None,CUG_Index,0),
    ('cug-Interlock',None,CUG_Interlock,0),
    ('intraCUG-Options',None,IntraCUG_Options,0),
    ('basicServiceGroupList',None,Ext_BasicServiceGroupList,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CUG-Subscription')
Ext_ExternalClientList=asn1.SEQUENCE_OF (ExternalClient)
DeleteSubscriberDataArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('basicServiceList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),BasicServiceList),1),
    ('ss-List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SS_List),1),
    ('roamingRestrictionDueToUnsupportedFeature',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('regionalSubscriptionIdentifier',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ZoneCode),1),
    ('vbsGroupIndication',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('vgcsGroupIndication',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('camelSubscriptionInfoWithdraw',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'DeleteSubscriberDataArg')
GenericServiceInfo=asn1.SEQUENCE ([('ss-Status',None,SS_Status,0),
    ('cliRestrictionOption',None,CliRestrictionOption,1)], seq_name = 'GenericServiceInfo')
ForwardingInfo=asn1.SEQUENCE ([('ss-Code',None,SS_Code,1),
    ('forwardingFeatureList',None,ForwardingFeatureList,0)], seq_name = 'ForwardingInfo')
MSISDN_BS_List=asn1.SEQUENCE_OF (MSISDN_BS)
InterrogateSS_Res=asn1.CHOICE ([('ss-Status',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Status)),
    ('basicServiceGroupList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),BasicServiceGroupList)),
    ('forwardingFeatureList',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ForwardingFeatureList)),
    ('genericServiceInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),GenericServiceInfo))])
T_BCSM_CAMEL_TDP_Criteria=asn1.SEQUENCE ([('t-BCSM-TriggerDetectionPoint',None,T_BcsmTriggerDetectionPoint,0),
    ('basicServiceCriteria',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),BasicServiceCriteria),1),
    ('t-CauseValueCriteria',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),T_CauseValueCriteria),1)], seq_name = 'T-BCSM-CAMEL-TDP-Criteria')
O_BcsmCamelTDP_Criteria=asn1.SEQUENCE ([('o-BcsmTriggerDetectionPoint',None,O_BcsmTriggerDetectionPoint,0),
    ('destinationNumberCriteria',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),DestinationNumberCriteria),1),
    ('basicServiceCriteria',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),BasicServiceCriteria),1),
    ('callTypeCriteria',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallTypeCriteria),1)], seq_name = 'O-BcsmCamelTDP-Criteria')
SS_Info=asn1.CHOICE ([('forwardingInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ForwardingInfo)),
    ('callBarringInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CallBarringInfo)),
    ('ss-Data',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SS_Data))])
Ext_CallBarFeatureList=asn1.SEQUENCE_OF (Ext_CallBarringFeature)
T_BCSM_CAMEL_TDP_CriteriaList=asn1.SEQUENCE_OF (T_BCSM_CAMEL_TDP_Criteria)
SubscriberInfo=asn1.SEQUENCE ([('locationInformation',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),LocationInformation),1),
    ('subscriberState',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SubscriberState),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SubscriberInfo')
O_CSI=asn1.SEQUENCE ([('o-BcsmCamelTDPDataList',None,O_BcsmCamelTDPDataList,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'O-CSI')
O_BcsmCamelTDPCriteriaList=asn1.SEQUENCE_OF (O_BcsmCamelTDP_Criteria)
SendAuthenticationInfoRes=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('authenticationSetList',None,AuthenticationSetList,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SendAuthenticationInfoRes'))
AnyTimeInterrogationRes=asn1.SEQUENCE ([('subscriberInfo',None,SubscriberInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AnyTimeInterrogationRes')
ResumeCallHandlingArg=asn1.SEQUENCE ([('callReferenceNumber',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CallReferenceNumber),1),
    ('basicServiceGroup',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('forwardingData',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ForwardingData),1),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('cug-CheckInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),CUG_CheckInfo),1),
    ('o-CSI',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('ccbs-Possible',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('uu-Data',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),UU_Data),1),
    ('allInformationSent',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'ResumeCallHandlingArg')
LCS_PrivacyClass=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('ss-Status',None,Ext_SS_Status,0),
    ('notificationToMSUser',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),NotificationToMSUser),1),
    ('externalClientList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExternalClientList),1),
    ('plmnClientList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),PLMNClientList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LCS-PrivacyClass')
ProvideSubscriberInfoRes=asn1.SEQUENCE ([('subscriberInfo',None,SubscriberInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ProvideSubscriberInfoRes')
SS_InfoList=asn1.SEQUENCE_OF (SS_Info)
CAMEL_SubscriptionInfo=asn1.SEQUENCE ([('o-CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('o-BcsmCamelTDP-CriteriaList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),O_BcsmCamelTDPCriteriaList),1),
    ('d-CSI',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),D_CSI),1),
    ('t-CSI',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),T_CSI),1),
    ('t-BCSM-CAMEL-TDP-CriteriaList',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),T_BCSM_CAMEL_TDP_CriteriaList),1),
    ('vt-CSI',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),T_CSI),1),
    ('vt-BCSM-CAMEL-TDP-CriteriaList',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),T_BCSM_CAMEL_TDP_CriteriaList),1),
    ('tif-CSI',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('tif-CSI-NotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('gprs-CSI',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),GPRS_CSI),1),
    ('mo-sms-CSI',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),SMS_CSI),1),
    ('ss-CSI',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),SS_CSI),1),
    ('m-CSI',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),M_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CAMEL-SubscriptionInfo')
VlrCamelSubscriptionInfo=asn1.SEQUENCE ([('o-CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'VlrCamelSubscriptionInfo')
SendIdentificationRes=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('imsi',None,IMSI,1),
    ('authenticationSetList',None,AuthenticationSetList,1),
    ('currentSecurityContext',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CurrentSecurityContext),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendIdentificationRes'))
Ext_CallBarInfo=asn1.SEQUENCE ([('ss-Code',None,SS_Code,0),
    ('callBarringFeatureList',None,Ext_CallBarFeatureList,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'Ext-CallBarInfo')
CUG_SubscriptionList=asn1.SEQUENCE_OF (CUG_Subscription)
Ext_CallBarringInfoFor_CSE=asn1.SEQUENCE ([('ss-Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('callBarringFeatureList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarFeatureList),0),
    ('password',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Password),1),
    ('wrongPasswordAttemptsCounter',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),WrongPasswordAttemptsCounter),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext-CallBarringInfoFor-CSE')
LCS_PrivacyExceptionList=asn1.SEQUENCE_OF (LCS_PrivacyClass)
Ext_SS_InfoFor_CSE=asn1.CHOICE ([('forwardingInfoFor-CSE',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_ForwardingInfoFor_CSE)),
    ('callBarringInfoFor-CSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarringInfoFor_CSE))])
AnyTimeModificationRes=asn1.SEQUENCE ([('ss-InfoFor-CSE',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_SS_InfoFor_CSE),1),
    ('camel-SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CAMEL_SubscriptionInfo),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AnyTimeModificationRes')
CallBarringData=asn1.SEQUENCE ([('callBarringFeatureList',None,Ext_CallBarFeatureList,0),
    ('password',None,Password,1),
    ('wrongPasswordAttemptsCounter',None,WrongPasswordAttemptsCounter,1),
    ('notificationToCSE',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CallBarringData')
LCSInformation=asn1.SEQUENCE ([('gmlc-List',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GMLC_List),1),
    ('lcs-PrivacyExceptionList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LCS_PrivacyExceptionList),1),
    ('molr-List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),MOLR_List),1)], seq_name = 'LCSInformation')
GmscCamelSubscriptionInfo=asn1.SEQUENCE ([('t-CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),T_CSI),1),
    ('o-CSI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'GmscCamelSubscriptionInfo')
CUG_Info=asn1.SEQUENCE ([('cug-SubscriptionList',None,CUG_SubscriptionList,0),
    ('cug-FeatureList',None,CUG_FeatureList,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CUG-Info')
InsertSubscriberDataArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(14,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'InsertSubscriberDataArg')
AnyTimeSubscriptionInterrogationRes=asn1.SEQUENCE ([('callForwardingData',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CallForwardingData),1),
    ('callBarringData',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallBarringData),1),
    ('odb-Info',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ODB_Info),1),
    ('camel-SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),CAMEL_SubscriptionInfo),1),
    ('supportedVLR-CAMEL-Phases',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('supportedSGSN-CAMEL-Phases',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AnyTimeSubscriptionInterrogationRes')
CamelRoutingInfo=asn1.SEQUENCE ([('forwardingData',None,ForwardingData,1),
    ('gmscCamelSubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GmscCamelSubscriptionInfo),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CamelRoutingInfo')
NoteSubscriberDataModifiedArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('msisdn',None,ISDN_AddressString,0),
    ('forwardingInfoFor-CSE',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_ForwardingInfoFor_CSE),1),
    ('callBarringInfoFor-CSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarringInfoFor_CSE),1),
    ('odb-Info',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ODB_Info),1),
    ('camel-SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),CAMEL_SubscriptionInfo),1),
    ('allInformationSent',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoteSubscriberDataModifiedArg')
Ext_SS_Info=asn1.CHOICE ([('forwardingInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_ForwInfo)),
    ('callBarringInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarInfo)),
    ('cug-Info',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CUG_Info)),
    ('ss-Data',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Ext_SS_Data)),
    ('emlpp-Info',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),EMLPP_Info))])
ExtendedRoutingInfo=asn1.CHOICE ([('routingInfo',None,RoutingInfo),
    ('camelRoutingInfo',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),CamelRoutingInfo))])
Ext_SS_InfoList=asn1.SEQUENCE_OF (Ext_SS_Info)
SubscriberData=asn1.SEQUENCE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('category',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Category),1),
    ('subscriberStatus',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SubscriberStatus),1),
    ('bearerServiceList',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),BearerServiceList),1),
    ('teleserviceList',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),TeleserviceList),1),
    ('provisionedSS',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),Ext_SS_InfoList),1),
    ('odb-Data',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ODB_Data),1),
    ('roamingRestrictionDueToUnsupportedFeature',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('regionalSubscriptionData',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),ZoneCodeList),1),
    ('vbsSubscriptionData',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),VBSDataList),1),
    ('vgcsSubscriptionData',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),VGCSDataList),1),
    ('vlrCamelSubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),VlrCamelSubscriptionInfo),1)], seq_name = 'SubscriberData')
SendRoutingInfoRes=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('extendedRoutingInfo',None,ExtendedRoutingInfo,1),
    ('cug-CheckInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),CUG_CheckInfo),1),
    ('cugSubscriptionFlag',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('subscriberInfo',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),SubscriberInfo),1),
    ('ss-List',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_List),1),
    ('basicService',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('forwardingInterrogationRequired',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('vmsc-Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoRes'))


