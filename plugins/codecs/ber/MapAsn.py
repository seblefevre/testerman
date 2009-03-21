# Auto-generated at Sat, 21 Mar 2009 18:44:46 +0000
# with the following command line:
# ./py_output.py --implicit asn/MAP-CommonDataTypes_expanded.asn
import Yapasn1 as asn1
#module MAP_CommonDataTypes None
SGSN_EventList=asn1.BITSTRING_class ([('pdpContext',0),('mo_mt_sms',1),('rau_gprsAttach_gprsDetach',2),('mbmsContext',3)],None,None)
MulticallBearerInfo=asn1.INTEGER_class ([],1,7)
PLMN_Id=asn1.OCTSTRING
ODB_HPLMN_Data=asn1.BITSTRING_class ([('plmn_SpecificBarringType1',0),('plmn_SpecificBarringType2',1),('plmn_SpecificBarringType3',2),('plmn_SpecificBarringType4',3)],None,None)
MM_Code=asn1.OCTSTRING
ChosenChannelInfo=asn1.OCTSTRING
OfferedCamel4CSIs=asn1.BITSTRING_class ([('o_csi',0),('d_csi',1),('vt_csi',2),('t_csi',3),('mt_sms_csi',4),('mg_csi',5),('psi_enhancements',6)],None,None)
ChargingCharacteristics=asn1.OCTSTRING
RequestedCAMEL_SubscriptionInfo=asn1.ENUM(o_CSI=0,t_CSI=1,vt_CSI=2,tif_CSI=3,gprs_CSI=4,mo_sms_CSI=5,ss_CSI=6,m_CSI=7,d_csi=8)
TraceDepth=asn1.ENUM(minimum=0,medium=1,maximum=2)
QoS_Subscribed=asn1.OCTSTRING
SRES=asn1.OCTSTRING
NotificationToMSUser=asn1.ENUM(notifyLocationAllowed=0,notifyAndVerify_LocationAllowedIfNoResponse=1,notifyAndVerify_LocationNotAllowedIfNoResponse=2,locationNotAllowed=3)
LSAOnlyAccessIndicator=asn1.ENUM(accessOutsideLSAsAllowed=0,accessOutsideLSAsRestricted=1)
HopCounter=asn1.INTEGER_class ([],0,3)
PositionMethodFailure_Diagnostic=asn1.ENUM(congestion=0,insufficientResources=1,insufficientMeasurementData=2,inconsistentMeasurementData=3,locationProcedureNotCompleted=4,locationProcedureNotSupportedByTargetMS=5,qoSNotAttainable=6,positionMethodNotAvailableInNetwork=7,positionMethodNotAvailableInLocationArea=8)
PDP_Address=asn1.OCTSTRING
GeodeticInformation=asn1.OCTSTRING
AlertReason=asn1.ENUM(ms_Present=0,memoryAvailable=1)
Ext_SS_Status=asn1.OCTSTRING
CallTypeCriteria=asn1.ENUM(forwarded=0,notForwarded=1)
OverrideCategory=asn1.ENUM(overrideEnabled=0,overrideDisabled=1)
Category=asn1.OCTSTRING
SuppressMTSS=asn1.BITSTRING_class ([('suppressCUG',0),('suppressCCBS',1)],None,None)
ProtocolId=asn1.ENUM(gsm_0408=1,gsm_0806=2,gsm_BSSMAP=3,ets_300102_1=4)
ForwardingReason=asn1.ENUM(notReachable=0,busy=1,noReply=2)
RNCId=asn1.OCTSTRING
CellGlobalIdOrServiceAreaIdFixedLength=asn1.OCTSTRING
BearerServiceCode=asn1.OCTSTRING
NAEA_CIC=asn1.OCTSTRING
LAIFixedLength=asn1.OCTSTRING
RANAP_ServiceHandover=asn1.OCTSTRING
InterrogationType=asn1.ENUM(basicCall=0,forwarding=1)
InterCUG_Restrictions=asn1.OCTSTRING
EncryptionInformation=asn1.OCTSTRING
Ext_NoRepCondTime=asn1.INTEGER_class ([],1,100)
Codec=asn1.OCTSTRING
IST_AlertTimerValue=asn1.INTEGER_class ([],15,255)
TEID=asn1.OCTSTRING
LongTermDenialParam=asn1.SEQUENCE ([], seq_name = 'LongTermDenialParam')
CallOutcome=asn1.ENUM(success=0,failure=1,busy=2)
UESBI_IuA=asn1.BITSTRING_class ([],None,None)
UESBI_IuB=asn1.BITSTRING_class ([],None,None)
RAB_Id=asn1.INTEGER_class ([],1,255)
ServiceIndicator=asn1.BITSTRING_class ([('clir_invoked',0),('camel_invoked',1)],None,None)
MaxMC_Bearers=asn1.INTEGER_class ([],2,7)
NotReachableReason=asn1.ENUM(msPurged=0,imsiDetached=1,restrictedArea=2,notRegistered=3)
CS_AllocationRetentionPriority=asn1.OCTSTRING
AgeIndicator=asn1.OCTSTRING
AddressString=asn1.OCTSTRING
MonitoringMode=asn1.ENUM(a_side=0,b_side=1)
MC_Bearers=asn1.INTEGER_class ([],1,7)
CCBS_Index=asn1.INTEGER_class ([],1,5)
TransactionId=asn1.OCTSTRING
GPRS_TriggerDetectionPoint=asn1.ENUM(attach=1,attachChangeOfPosition=2,pdp_ContextEstablishment=11,pdp_ContextEstablishmentAcknowledgement=12,pdp_ContextChangeOfPosition=14)
SM_DeliveryNotIntended=asn1.ENUM(onlyIMSI_requested=0,onlyMCC_MNC_requested=1)
TBCD_STRING=asn1.OCTSTRING
RoamingNotAllowedCause=asn1.ENUM(plmnRoamingNotAllowed=0,operatorDeterminedBarring=3)
MSC_S_InterfaceList=asn1.BITSTRING_class ([('a',0),('iu',1),('mc',2),('map_g',3),('map_b',4),('map_e',5),('map_f',6),('cap',7),('map_d',8),('map_c',9)],None,None)
NetworkResource=asn1.ENUM(plmn=0,hlr=1,vlr=2,pvlr=3,controllingMSC=4,vmsc=5,eir=6,rss=7)
Long_GroupId=TBCD_STRING
RAIdentity=asn1.OCTSTRING
BSSMAP_ServiceHandover=asn1.OCTSTRING
APN=asn1.OCTSTRING
AdditionalNetworkResource=asn1.ENUM(sgsn=0,ggsn=1,gmlc=2,gsmSCF=3,nplr=4,auc=5,ue=6)
UUIndicator=asn1.OCTSTRING
IntegrityProtectionInformation=asn1.OCTSTRING
BMSC_InterfaceList=asn1.BITSTRING_class ([('gmb',0)],None,None)
DefaultSMS_Handling=asn1.ENUM(continueTransaction=0,releaseTransaction=1)
NumberOfRequestedVectors=asn1.INTEGER_class ([],1,5)
TraceReference2=asn1.OCTSTRING
KSI=asn1.OCTSTRING
GMLC_Restriction=asn1.ENUM(gmlc_List=0,home_Country=1)
USSD_DataCodingScheme=asn1.OCTSTRING
PW_RegistrationFailureCause=asn1.ENUM(undetermined=0,invalidFormat=1,newPasswordsMismatch=2)
Ext_ForwOptions=asn1.OCTSTRING
ODB_GeneralData=asn1.BITSTRING_class ([('allOG_CallsBarred',0),('internationalOGCallsBarred',1),('internationalOGCallsNotToHPLMN_CountryBarred',2),('interzonalOGCallsBarred',6),('interzonalOGCallsNotToHPLMN_CountryBarred',7),('interzonalOGCallsAndInternationalOGCallsNotToHPLMN_CountryBarred',8),('premiumRateInformationOGCallsBarred',3),('premiumRateEntertainementOGCallsBarred',4),('ss_AccessBarred',5),('allECT_Barred',9),('chargeableECT_Barred',10),('internationalECT_Barred',11),('interzonalECT_Barred',12),('doublyChargeableECT_Barred',13),('multipleECT_Barred',14),('allPacketOrientedServicesBarred',15),('roamerAccessToHPLMN_AP_Barred',16),('roamerAccessToVPLMN_AP_Barred',17),('roamingOutsidePLMNOG_CallsBarred',18),('allIC_CallsBarred',19),('roamingOutsidePLMNIC_CallsBarred',20),('roamingOutsidePLMNICountryIC_CallsBarred',21),('roamingOutsidePLMN_Barred',22),('roamingOutsidePLMN_CountryBarred',23),('registrationAllCF_Barred',24),('registrationCFNotToHPLMN_Barred',25),('registrationInterzonalCF_Barred',26),('registrationInterzonalCFNotToHPLMN_Barred',27),('registrationInternationalCF_Barred',28)],None,None)
CallTerminationIndicator=asn1.ENUM(terminateCallActivityReferred=0,terminateAllCallActivities=1)
SMS_TriggerDetectionPoint=asn1.ENUM(sms_CollectedInfo=1,sms_DeliveryRequest=2)
TraceNE_TypeList=asn1.BITSTRING_class ([('msc_s',0),('mgw',1),('sgsn',2),('ggsn',3),('rnc',4),('bm_sc',5)],None,None)
OfferedCamel4Functionalities=asn1.BITSTRING_class ([('initiateCallAttempt',0),('splitLeg',1),('moveLeg',2),('disconnectLeg',3),('entityReleased',4),('dfc_WithArgument',5),('playTone',6),('dtmf_MidCall',7),('chargingIndicator',8),('alertingDP',9),('locationAtAlerting',10),('changeOfPositionDP',11),('or_Interactions',12),('warningToneEnhancements',13),('cf_Enhancements',14),('subscribedEnhancedDialledServices',15),('servingNetworkEnhancedDialledServices',16),('criteriaForChangeOfPositionDP',17),('serviceChangeDP',18),('collectInformation',19)],None,None)
UnavailabilityCause=asn1.ENUM(bearerServiceNotProvisioned=1,teleserviceNotProvisioned=2,absentSubscriber=3,busySubscriber=4,callBarred=5,cug_Reject=6)
AUTS=asn1.OCTSTRING
GGSN_EventList=asn1.BITSTRING_class ([('pdpContext',0),('mbmsContext',1)],None,None)
SupportedCCBS_Phase=asn1.INTEGER_class ([],1,127)
DefaultCallHandling=asn1.ENUM(continueCall=0,releaseCall=1)
PermittedIntegrityProtectionAlgorithms=asn1.OCTSTRING
CUG_Interlock=asn1.OCTSTRING
SelectedGSM_Algorithm=asn1.OCTSTRING
CCBS_RequestState=asn1.ENUM(request=0,recall=1,active=2,completed=3,suspended=4,frozen=5,deleted=6)
Kc=asn1.OCTSTRING
FailureCause=asn1.ENUM(wrongUserResponse=0,wrongNetworkSignature=1)
CamelCapabilityHandling=asn1.INTEGER_class ([],1,16)
TraceRecordingSessionReference=asn1.OCTSTRING
SGSN_InterfaceList=asn1.BITSTRING_class ([('gb',0),('iu',1),('gn',2),('map_gr',3),('map_gd',4),('map_gf',5),('gs',6),('ge',7)],None,None)
IntraCUG_Options=asn1.ENUM(noCUG_Restrictions=0,cugIC_CallBarred=1,cugOG_CallBarred=2)
CauseValue=asn1.OCTSTRING
SM_EnumeratedDeliveryFailureCause=asn1.ENUM(memoryCapacityExceeded=0,equipmentProtocolError=1,equipmentNotSM_Equipped=2,unknownServiceCentre=3,sc_Congestion=4,invalidSME_Address=5,subscriberNotSC_Subscriber=6)
UUI=asn1.OCTSTRING
OR_Phase=asn1.INTEGER_class ([],1,127)
CallDiversionTreatmentIndicator=asn1.OCTSTRING
AlertingPattern=asn1.OCTSTRING
GPRSChargingID=asn1.OCTSTRING
TraceDepthList=asn1.SEQUENCE ([('msc_s_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('mgw_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('sgsn_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('ggsn_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('rnc_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('bmsc_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),TraceDepth),1)], seq_name = 'TraceDepthList')
RadioResourceInformation=asn1.OCTSTRING
T_BcsmTriggerDetectionPoint=asn1.ENUM(termAttemptAuthorized=12,tBusy=13,tNoAnswer=14)
SupportedLCS_CapabilitySets=asn1.BITSTRING_class ([('lcsCapabilitySet1',0),('lcsCapabilitySet2',1),('lcsCapabilitySet3',2),('lcsCapabilitySet4',3),('lcsCapabilitySet5',4)],None,None)
AbsentSubscriberDiagnosticSM=asn1.INTEGER_class ([],0,255)
SM_RP_MTI=asn1.INTEGER_class ([],0,10)
DefaultGPRS_Handling=asn1.ENUM(continueTransaction=0,releaseTransaction=1)
CallBarringCause=asn1.ENUM(barringServiceActive=0,operatorBarring=1)
EquipmentStatus=asn1.ENUM(whiteListed=0,blackListed=1,greyListed=2)
ReportingState=asn1.ENUM(stopMonitoring=0,startMonitoring=1)
ContextId=asn1.INTEGER_class ([],1,50)
NoReplyConditionTime=asn1.INTEGER_class ([],5,30)
AdditionalRoamingNotAllowedCause=asn1.ENUM(supportedRAT_TypesNotAllowed=0)
DomainType=asn1.ENUM(cs_Domain=0,ps_Domain=1)
RadioResource=asn1.SEQUENCE ([('radioResourceInformation',None,RadioResourceInformation,0),
    ('rab_Id',None,RAB_Id,0)], seq_name = 'RadioResource')
LongSignalInfo=asn1.OCTSTRING
RequestingNodeType=asn1.ENUM(vlr=0,sgsn=1,s_cscf=2,bsf=3,gan_aaa_server=4,wlan_aaa_server=5)
SS_Code=asn1.OCTSTRING
PDP_Type=asn1.OCTSTRING
UnauthorizedLCSClient_Diagnostic=asn1.ENUM(noAdditionalInformation=0,clientNotInMSPrivacyExceptionList=1,callToClientNotSetup=2,privacyOverrideNotApplicable=3,disallowedByLocalRegulatoryRequirements=4,unauthorizedPrivacyClass=5,unauthorizedCallSessionUnrelatedExternalClient=6,unauthorizedCallSessionRelatedExternalClient=7)
CallReferenceNumber=asn1.OCTSTRING
MW_Status=asn1.BITSTRING_class ([('sc_AddressNotIncluded',0),('mnrf_Set',1),('mcef_Set',2),('mnrg_Set',3)],None,None)
DestinationNumberLengthList=asn1.SEQUENCE_OF (asn1.INTEGER_class ([],1,15))
CCBS_SubscriberStatus=asn1.ENUM(ccbsNotIdle=0,ccbsIdle=1,ccbsNotReachable=2)
ASCI_CallReference=TBCD_STRING
GSN_Address=asn1.OCTSTRING
SM_RP_SMEA=asn1.OCTSTRING
AllowedGSM_Algorithms=asn1.OCTSTRING
SuppressionOfAnnouncement=asn1.NULL
ForwardingOptions=asn1.OCTSTRING
SM_DeliveryOutcome=asn1.ENUM(memoryCapacityExceeded=0,absentSubscriber=1,successfulTransfer=2)
Ext_TeleserviceCode=asn1.OCTSTRING
ServiceKey=asn1.INTEGER_class ([],0,2147483647)
RouteingNumber=TBCD_STRING
ExtensionContainer=asn1.SEQUENCE ([], seq_name = 'ExtensionContainer')
SupportedRAT_Types=asn1.BITSTRING_class ([('utran',0),('geran',1)],None,None)
ChosenSpeechVersion=asn1.OCTSTRING
ResourceLimitationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ResourceLimitationParam')
MS_Classmark2=asn1.OCTSTRING
ChosenEncryptionAlgorithm=asn1.OCTSTRING
CancellationType=asn1.ENUM(updateProcedure=0,subscriptionWithdraw=1)
LSAAttributes=asn1.OCTSTRING
ActivateTraceModeRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ActivateTraceModeRes')
MSRadioAccessCapability=asn1.OCTSTRING
MT_SMS_TPDU_Type=asn1.ENUM(sms_DELIVER=0,sms_SUBMIT_REPORT=1,sms_STATUS_REPORT=2)
BSSMAP_ServiceHandoverInfo=asn1.SEQUENCE ([('bssmap_ServiceHandover',None,BSSMAP_ServiceHandover,0),
    ('rab_Id',None,RAB_Id,0)], seq_name = 'BSSMAP_ServiceHandoverInfo')
AccessType=asn1.ENUM(call=0,emergencyCall=1,locationUpdating=2,supplementaryService=3,shortMessage=4,gprsAttach=5,routingAreaUpdating=6,serviceRequest=7,pdpContextActivation=8,pdpContextDeactivation=9,gprsDetach=10)
SubscriberState=asn1.CHOICE ([('assumedIdle',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('camelBusy',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('netDetNotReachable',None,NotReachableReason),
    ('notProvidedFromVLR',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL))])
RequestedEquipmentInfo=asn1.BITSTRING_class ([('equipmentStatus',0),('bmuef',1)],None,None)
TPDU_TypeCriterion=asn1.SEQUENCE_OF (MT_SMS_TPDU_Type)
UnknownSubscriberDiagnostic=asn1.ENUM(imsiUnknown=0,gprsSubscriptionUnknown=1,npdbMismatch=2)
CK=asn1.OCTSTRING
NSAPI=asn1.INTEGER_class ([],0,15)
Ext_QoS_Subscribed=asn1.OCTSTRING
MGW_EventList=asn1.BITSTRING_class ([('context',0)],None,None)
MatchType=asn1.ENUM(inhibiting=0,enabling=1)
T_CauseValueCriteria=asn1.SEQUENCE_OF (CauseValue)
AllowedServices=asn1.BITSTRING_class ([('firstServiceAllowed',0),('secondServiceAllowed',1)],None,None)
Ext3_QoS_Subscribed=asn1.OCTSTRING
AbsentSubscriberSM_Param=asn1.SEQUENCE ([('absentSubscriberDiagnosticSM',None,AbsentSubscriberDiagnosticSM,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AbsentSubscriberSM_Param')
ZoneCode=asn1.OCTSTRING
USSD_String=asn1.OCTSTRING
ChosenRadioResourceInformation=asn1.SEQUENCE ([('chosenChannelInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ChosenChannelInfo),1),
    ('chosenSpeechVersion',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ChosenSpeechVersion),1)], seq_name = 'ChosenRadioResourceInformation')
SpecificCSI_Withdraw=asn1.BITSTRING_class ([('o_csi',0),('ss_csi',1),('tif_csi',2),('d_csi',3),('vt_csi',4),('mo_sms_csi',5),('m_csi',6),('gprs_csi',7),('t_csi',8),('mt_sms_csi',9),('mg_csi',10),('o_IM_CSI',11),('d_IM_CSI',12),('vt_IM_CSI',13)],None,None)
Ext_ProtocolId=asn1.ENUM(ets_300356=1)
SS_SubscriptionViolationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS_SubscriptionViolationParam')
Ext_BearerServiceCode=asn1.OCTSTRING
TraceType=asn1.INTEGER_class ([],0,255)
O_BcsmTriggerDetectionPoint=asn1.ENUM(collectedInfo=2,routeSelectFailure=4)
SubscriberStatus=asn1.ENUM(serviceGranted=0,operatorDeterminedBarring=1)
GeographicalInformation=asn1.OCTSTRING
AdditionalInfo=asn1.BITSTRING_class ([],None,None)
AUTN=asn1.OCTSTRING
SupportedCamelPhases=asn1.BITSTRING_class ([('phase1',0),('phase2',1),('phase3',2),('phase4',3)],None,None)
MessageWaitListFullParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MessageWaitListFullParam')
IK=asn1.OCTSTRING
EraseCC_EntryArg=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ccbs_Index',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CCBS_Index),1)], seq_name = 'EraseCC_EntryArg')
Cksn=asn1.OCTSTRING
CUG_Index=asn1.INTEGER_class ([],0,32767)
MSNetworkCapability=asn1.OCTSTRING
TeleservNotProvParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'TeleservNotProvParam')
AdditionalSubscriptions=asn1.BITSTRING_class ([('privilegedUplinkRequest',0),('emergencyUplinkRequest',1),('emergencyReset',2)],None,None)
SS_EventSpecification=asn1.SEQUENCE_OF (AddressString)
UnidentifiedSubParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnidentifiedSubParam')
CliRestrictionOption=asn1.ENUM(permanent=0,temporaryDefaultRestricted=1,temporaryDefaultAllowed=2)
GroupId=TBCD_STRING
TeleserviceCode=asn1.OCTSTRING
ChosenIntegrityProtectionAlgorithm=asn1.OCTSTRING
LCSClientInternalID=asn1.ENUM(broadcastService=0,o_andM_HPLMN=1,o_andM_VPLMN=2,anonymousLocation=3,targetMSsubscribedService=4)
SelectedUMTS_Algorithms=asn1.SEQUENCE ([('integrityProtectionAlgorithm',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ChosenIntegrityProtectionAlgorithm),1),
    ('encryptionAlgorithm',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ChosenEncryptionAlgorithm),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SelectedUMTS_Algorithms')
NumberPortabilityStatus=asn1.ENUM(notKnownToBePorted=0,ownNumberPortedOut=1,foreignNumberPortedToForeignNetwork=2,ownNumberNotPortedOut=4,foreignNumberPortedIn=5)
KeyStatus=asn1.ENUM(old=0,new=1)
SS_Status=asn1.OCTSTRING
FTN_AddressString=AddressString
FailureCauseParam=asn1.ENUM(limitReachedOnNumberOfConcurrentLocationRequests=0)
UnauthorizedRequestingNetwork_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnauthorizedRequestingNetwork_Param')
EMLPP_Priority=asn1.INTEGER_class ([],0,15)
GlobalCellId=asn1.OCTSTRING
IST_AlertRes=asn1.SEQUENCE ([('istAlertTimer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IST_AlertTimerValue),1),
    ('istInformationWithdraw',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('callTerminationIndicator',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallTerminationIndicator),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'IST_AlertRes')
NoSubscriberReplyParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoSubscriberReplyParam')
RNC_InterfaceList=asn1.BITSTRING_class ([('iu',0),('iur',1),('iub',2),('uu',3)],None,None)
GPRSMSClass=asn1.SEQUENCE ([('mSNetworkCapability',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MSNetworkCapability),0),
    ('mSRadioAccessCapability',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),MSRadioAccessCapability),1)], seq_name = 'GPRSMSClass')
ATI_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ATI_NotAllowedParam')
GuidanceInfo=asn1.ENUM(enterPW=0,enterNewPW=1,enterNewPW_Again=2)
LMSI=asn1.OCTSTRING
NoRoamingNbParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoRoamingNbParam')
AgeOfLocationInformation=asn1.INTEGER_class ([],0,32767)
RequestedInfo=asn1.SEQUENCE ([('locationInformation',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('subscriberState',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RequestedInfo')
MSC_S_EventList=asn1.BITSTRING_class ([('mo_mtCall',0),('mo_mt_sms',1),('lu_imsiAttach_imsiDetach',2),('handovers',3),('ss',4)],None,None)
AbsentSubscriberReason=asn1.ENUM(imsiDetach=0,restrictedArea=1,noPageResponse=2,purgedMS=3)
BMSC_EventList=asn1.BITSTRING_class ([('mbmsMulticastServiceActivation',0)],None,None)
NumberOfForwarding=asn1.INTEGER_class ([],1,5)
EventReportData=asn1.SEQUENCE ([('ccbs_SubscriberStatus',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_SubscriberStatus),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'EventReportData')
MT_smsCAMELTDP_Criteria=asn1.SEQUENCE ([('sms_TriggerDetectionPoint',None,SMS_TriggerDetectionPoint,0),
    ('tpdu_TypeCriterion',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TPDU_TypeCriterion),1)], seq_name = 'MT_smsCAMELTDP_Criteria')
RegionalSubscriptionResponse=asn1.ENUM(networkNode_AreaRestricted=0,tooManyZoneCodes=1,zoneCodesConflict=2,regionalSubscNotSupported=3)
SS_EventList=asn1.SEQUENCE_OF (SS_Code)
IST_SupportIndicator=asn1.ENUM(basicISTSupported=0,istCommandSupported=1)
SS_List=asn1.SEQUENCE_OF (SS_Code)
BSSMAP_ServiceHandoverList=asn1.SEQUENCE_OF (BSSMAP_ServiceHandoverInfo)
UU_Data=asn1.SEQUENCE ([('uuIndicator',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),UUIndicator),1),
    ('uui',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),UUI),1),
    ('uusCFInteraction',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'UU_Data')
RAND=asn1.OCTSTRING
LocationNumber=asn1.OCTSTRING
NetworkAccessMode=asn1.ENUM(bothMSCAndSGSN=0,onlyMSC=1,onlySGSN=2)
LCSServiceTypeID=asn1.INTEGER_class ([],0,127)
SignalInfo=asn1.OCTSTRING
GERAN_Classmark=asn1.OCTSTRING
ContextIdList=asn1.SEQUENCE_OF (ContextId)
DeleteSubscriberDataRes=asn1.SEQUENCE ([('regionalSubscriptionResponse',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RegionalSubscriptionResponse),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'DeleteSubscriberDataRes')
MobilityTriggers=asn1.SEQUENCE_OF (MM_Code)
Ext2_QoS_Subscribed=asn1.OCTSTRING
ModificationInstruction=asn1.ENUM(deactivate=0,activate=1)
LSAIdentity=asn1.OCTSTRING
TMSI=asn1.OCTSTRING
GGSN_InterfaceList=asn1.BITSTRING_class ([('gn',0),('gi',1),('gmb',2)],None,None)
PermittedEncryptionAlgorithms=asn1.OCTSTRING
RUF_Outcome=asn1.ENUM(accepted=0,rejected=1,noResponseFromFreeMS=2,noResponseFromBusyMS=3,udubFromFreeMS=4,udubFromBusyMS=5)
PDP_ContextInfo=asn1.SEQUENCE ([('pdp_ContextIdentifier',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ContextId),0),
    ('pdp_ContextActive',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('pdp_Type',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),PDP_Type),0),
    ('pdp_Address',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),PDP_Address),1),
    ('apn_Subscribed',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),APN),1),
    ('apn_InUse',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),APN),1),
    ('nsapi',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),NSAPI),1),
    ('transactionId',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),TransactionId),1),
    ('teid_ForGnAndGp',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),TEID),1),
    ('teid_ForIu',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),TEID),1),
    ('ggsn_Address',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('qos_Subscribed',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),Ext_QoS_Subscribed),1),
    ('qos_Requested',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),Ext_QoS_Subscribed),1),
    ('qos_Negotiated',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),Ext_QoS_Subscribed),1),
    ('chargingId',None,asn1.TYPE(asn1.IMPLICIT(14,cls=asn1.CONTEXT_FLAG),GPRSChargingID),1),
    ('chargingCharacteristics',None,asn1.TYPE(asn1.IMPLICIT(15,cls=asn1.CONTEXT_FLAG),ChargingCharacteristics),1),
    ('rnc_Address',None,asn1.TYPE(asn1.IMPLICIT(16,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(17,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PDP_ContextInfo')
TraceReference=asn1.OCTSTRING
XRES=asn1.OCTSTRING
O_CauseValueCriteria=asn1.SEQUENCE_OF (CauseValue)
MO_ForwardSM_Res=asn1.SEQUENCE ([('sm_RP_UI',None,SignalInfo,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MO_ForwardSM_Res')
ATSI_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ATSI_NotAllowedParam')
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
PurgeMS_Res=asn1.SEQUENCE ([('freezeTMSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('freezeP_TMSI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'PurgeMS_Res')
OngoingGroupCallParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'OngoingGroupCallParam')
AccessRestrictionData=asn1.BITSTRING_class ([('utranNotAllowed',0),('geranNotAllowed',1)],None,None)
Password=asn1.NumericString
WrongPasswordAttemptsCounter=asn1.INTEGER_class ([],0,4)
CellGlobalIdOrServiceAreaIdOrLAI=asn1.CHOICE ([('cellGlobalIdOrServiceAreaIdFixedLength',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CellGlobalIdOrServiceAreaIdFixedLength)),
    ('laiFixedLength',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LAIFixedLength))])
AdditionalRequestedCAMEL_SubscriptionInfo=asn1.ENUM(mt_sms_CSI=0,mg_csi=1,o_IM_CSI=2,d_IM_CSI=3,vt_IM_CSI=4)
AccessNetworkProtocolId=asn1.ENUM(ts3G_48006=1,ts3G_25413=2)
ShortTermDenialParam=asn1.SEQUENCE ([], seq_name = 'ShortTermDenialParam')
MGW_InterfaceList=asn1.BITSTRING_class ([('mc',0),('nb_up',1),('iu_up',2)],None,None)
ISDN_SubaddressString=asn1.OCTSTRING
UESBI_Iu=asn1.SEQUENCE ([('uesbi_IuA',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),UESBI_IuA),1),
    ('uesbi_IuB',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),UESBI_IuB),1)], seq_name = 'UESBI_Iu')
BearerServNotProvParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'BearerServNotProvParam')
CUG_RejectCause=asn1.ENUM(incomingCallsBarredWithinCUG=0,subscriberNotMemberOfCUG=1,requestedBasicServiceViolatesCUG_Constraints=5,calledPartySS_InteractionViolation=7)
MT_ForwardSM_Res=asn1.SEQUENCE ([('sm_RP_UI',None,SignalInfo,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MT_ForwardSM_Res')
FacilityNotSupParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'FacilityNotSupParam')
ExternalSignalInfo=asn1.SEQUENCE ([('protocolId',None,ProtocolId,0),
    ('signalInfo',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ExternalSignalInfo')
SendRoutingInfoForGprsRes=asn1.SEQUENCE ([('sgsn_Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GSN_Address),0),
    ('ggsn_Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('mobileNotReachableReason',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AbsentSubscriberDiagnosticSM),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoForGprsRes')
ForwardingFailedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ForwardingFailedParam')
MC_SS_Info=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('nbrSB',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),MaxMC_Bearers),0),
    ('nbrUser',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),MC_Bearers),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MC_SS_Info')
SubBusyForMT_SMS_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SubBusyForMT_SMS_Param')
ExtensibleSystemFailureParam=asn1.SEQUENCE ([('networkResource',None,NetworkResource,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ExtensibleSystemFailureParam')
EraseCC_EntryRes=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_Status),1)], seq_name = 'EraseCC_EntryRes')
AuthenticationFailureReportRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AuthenticationFailureReportRes')
BasicServiceCode=asn1.CHOICE ([('bearerService',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),BearerServiceCode)),
    ('teleservice',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),TeleserviceCode))])
CallReportData=asn1.SEQUENCE ([('monitoringMode',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MonitoringMode),1),
    ('callOutcome',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CallOutcome),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CallReportData')
NoteMsPresentForGprsRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NoteMsPresentForGprsRes')
IMSI=TBCD_STRING
NAEA_PreferredCI=asn1.SEQUENCE ([('naea_PreferredCIC',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),NAEA_CIC),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NAEA_PreferredCI')
IST_AlertArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'IST_AlertArg')
ISDN_AddressString=AddressString
USSD_Arg=asn1.SEQUENCE ([('ussd_DataCodingScheme',None,USSD_DataCodingScheme,0),
    ('ussd_String',None,USSD_String,0)], seq_name = 'USSD_Arg')
IncompatibleTerminalParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IncompatibleTerminalParam')
Ext_BasicServiceCode=asn1.CHOICE ([('ext_BearerService',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Ext_BearerServiceCode)),
    ('ext_Teleservice',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Ext_TeleserviceCode))])
IllegalSubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IllegalSubscriberParam')
DestinationNumberList=asn1.SEQUENCE_OF (ISDN_AddressString)
ModificationRequestFor_CB_Info=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('basicService',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),1),
    ('password',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Password),1),
    ('wrongPasswordAttemptsCounter',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),WrongPasswordAttemptsCounter),1),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor_CB_Info')
RoutingInfoForSM_Arg=asn1.SEQUENCE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('sm_RP_PRI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.BOOLEAN),0),
    ('serviceCentreAddress',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RoutingInfoForSM_Arg')
SS_NotAvailableParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS_NotAvailableParam')
DataMissingParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'DataMissingParam')
NumberChangedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NumberChangedParam')
SM_RP_OA=asn1.CHOICE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString)),
    ('serviceCentreAddressOA',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AddressString)),
    ('noSM_RP_OA',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),asn1.NULL))])
ForwardingData=asn1.SEQUENCE ([('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('forwardingOptions',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ForwardingOptions),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ForwardingData')
NoGroupCallNbParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoGroupCallNbParam')
IST_CommandRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IST_CommandRes')
HLR_Id=IMSI
RestoreDataRes=asn1.SEQUENCE ([('hlr_Number',None,ISDN_AddressString,0),
    ('msNotReachable',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'RestoreDataRes')
BusySubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'BusySubscriberParam')
TeleserviceList=asn1.SEQUENCE_OF (Ext_TeleserviceCode)
BearerServiceList=asn1.SEQUENCE_OF (Ext_BearerServiceCode)
VoiceBroadcastData=asn1.SEQUENCE ([('groupid',None,GroupId,0),
    ('broadcastInitEntitlement',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'VoiceBroadcastData')
UpdateGprsLocationRes=asn1.SEQUENCE ([('hlr_Number',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateGprsLocationRes')
SetReportingStateArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('ccbs_Monitoring',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ReportingState),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SetReportingStateArg')
ServiceType=asn1.SEQUENCE ([('serviceTypeIdentity',None,LCSServiceTypeID,0),
    ('gmlc_Restriction',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GMLC_Restriction),1),
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
CheckIMEI_Res=asn1.SEQUENCE ([('equipmentStatus',None,EquipmentStatus,1),
    ('bmuef',None,UESBI_Iu,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CheckIMEI_Res')
ODB_Data=asn1.SEQUENCE ([('odb_GeneralData',None,ODB_GeneralData,0),
    ('odb_HPLMN_Data',None,ODB_HPLMN_Data,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ODB_Data')
SubscriberIdentity=asn1.CHOICE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI)),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString))])
TraceEventList=asn1.SEQUENCE ([('msc_s_List',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MSC_S_EventList),1),
    ('mgw_List',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),MGW_EventList),1),
    ('sgsn_List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SGSN_EventList),1),
    ('ggsn_List',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),GGSN_EventList),1),
    ('bmsc_List',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),BMSC_EventList),1)], seq_name = 'TraceEventList')
USSD_Res=asn1.SEQUENCE ([('ussd_DataCodingScheme',None,USSD_DataCodingScheme,0),
    ('ussd_String',None,USSD_String,0)], seq_name = 'USSD_Res')
Ext_CallBarringFeature=asn1.SEQUENCE ([('basicService',None,Ext_BasicServiceCode,1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'Ext_CallBarringFeature')
PositionMethodFailure_Param=asn1.SEQUENCE ([('positionMethodFailure_Diagnostic',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),PositionMethodFailure_Diagnostic),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PositionMethodFailure_Param')
ServiceTypeList=asn1.SEQUENCE_OF (ServiceType)
LCSClientExternalID=asn1.SEQUENCE ([('externalAddress',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LCSClientExternalID')
UnauthorizedLCSClient_Param=asn1.SEQUENCE ([('unauthorizedLCSClient_Diagnostic',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),UnauthorizedLCSClient_Diagnostic),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'UnauthorizedLCSClient_Param')
CancelLocationRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CancelLocationRes')
SendEndSignal_Res=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendEndSignal_Res')
SuperChargerInfo=asn1.CHOICE ([('sendSubscriberData',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('subscriberDataStored',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),AgeIndicator))])
IMEI=TBCD_STRING
Re_synchronisationInfo=asn1.SEQUENCE ([('rand',None,RAND,0),
    ('auts',None,AUTS,0)], seq_name = 'Re_synchronisationInfo')
DestinationNumberCriteria=asn1.SEQUENCE ([('matchType',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MatchType),0),
    ('destinationNumberList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DestinationNumberList),1),
    ('destinationNumberLengthList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),DestinationNumberLengthList),1)], seq_name = 'DestinationNumberCriteria')
TracingBufferFullParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'TracingBufferFullParam')
ZoneCodeList=asn1.SEQUENCE_OF (ZoneCode)
CCBS_Indicators=asn1.SEQUENCE ([('ccbs_Possible',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('keepCCBS_CallIndicator',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CCBS_Indicators')
RemoteUserFreeRes=asn1.SEQUENCE ([('ruf_Outcome',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RUF_Outcome),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RemoteUserFreeRes')
IST_CommandArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'IST_CommandArg')
PLMNClientList=asn1.SEQUENCE_OF (LCSClientInternalID)
EMLPP_Info=asn1.SEQUENCE ([('maximumentitledPriority',None,EMLPP_Priority,0),
    ('defaultPriority',None,EMLPP_Priority,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'EMLPP_Info')
FailureReportRes=asn1.SEQUENCE ([('ggsn_Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'FailureReportRes')
OR_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'OR_NotAllowedParam')
AccessNetworkSignalInfo=asn1.SEQUENCE ([('accessNetworkProtocolId',None,AccessNetworkProtocolId,0),
    ('signalInfo',None,LongSignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AccessNetworkSignalInfo')
LSAIdentityList=asn1.SEQUENCE_OF (LSAIdentity)
RadioResourceList=asn1.SEQUENCE_OF (RadioResource)
ExtensibleCallBarredParam=asn1.SEQUENCE ([('callBarringCause',None,CallBarringCause,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ExtensibleCallBarredParam')
UMTS_SecurityContextData=asn1.SEQUENCE ([('ck',None,CK,0),
    ('ik',None,IK,0),
    ('ksi',None,KSI,0)], seq_name = 'UMTS_SecurityContextData')
ADD_Info=asn1.SEQUENCE ([('imeisv',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMEI),0),
    ('skipSubscriberDataUpdate',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'ADD_Info')
CUG_CheckInfo=asn1.SEQUENCE ([('cug_Interlock',None,CUG_Interlock,0),
    ('cug_OutgoingAccess',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CUG_CheckInfo')
InformationNotAvailableParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'InformationNotAvailableParam')
DeactivateTraceModeRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'DeactivateTraceModeRes')
AllowedUMTS_Algorithms=asn1.SEQUENCE ([('integrityProtectionAlgorithms',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),PermittedIntegrityProtectionAlgorithms),1),
    ('encryptionAlgorithms',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),PermittedEncryptionAlgorithms),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AllowedUMTS_Algorithms')
ATM_NotAllowedParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ATM_NotAllowedParam')
MM_EventNotSupported_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MM_EventNotSupported_Param')
UnexpectedDataParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnexpectedDataParam')
M_CSI=asn1.SEQUENCE ([('mobilityTriggers',None,MobilityTriggers,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi_Active',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'M_CSI')
SS_ForBS_Code=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('basicService',None,BasicServiceCode,1)], seq_name = 'SS_ForBS_Code')
UnknownOrUnreachableLCSClient_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnknownOrUnreachableLCSClient_Param')
ResumeCallHandlingRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ResumeCallHandlingRes')
DP_AnalysedInfoCriterium=asn1.SEQUENCE ([('dialledNumber',None,ISDN_AddressString,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF_Address',None,ISDN_AddressString,0),
    ('defaultCallHandling',None,DefaultCallHandling,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'DP_AnalysedInfoCriterium')
NoteMM_EventRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoteMM_EventRes')
SS_CamelData=asn1.SEQUENCE ([('ss_EventList',None,SS_EventList,0),
    ('gsmSCF_Address',None,ISDN_AddressString,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SS_CamelData')
SS_InvocationNotificationArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('ss_Event',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ss_EventSpecification',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SS_EventSpecification),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SS_InvocationNotificationArg')
Ext_ExternalSignalInfo=asn1.SEQUENCE ([('ext_ProtocolId',None,Ext_ProtocolId,0),
    ('signalInfo',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'Ext_ExternalSignalInfo')
MOLR_Class=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('ss_Status',None,Ext_SS_Status,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MOLR_Class')
AbsentSubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AbsentSubscriberParam')
UpdateLocationRes=asn1.SEQUENCE ([('hlr_Number',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateLocationRes')
CheckIMEI_Arg=asn1.SEQUENCE ([('imei',None,IMEI,0),
    ('requestedEquipmentInfo',None,RequestedEquipmentInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CheckIMEI_Arg')
MNPInfoRes=asn1.SEQUENCE ([('routeingNumber',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RouteingNumber),1),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('numberPortabilityStatus',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),NumberPortabilityStatus),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MNPInfoRes')
IllegalEquipmentParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IllegalEquipmentParam')
SetReportingStateRes=asn1.SEQUENCE ([('ccbs_SubscriberStatus',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_SubscriberStatus),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SetReportingStateRes')
ReadyForSM_Res=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReadyForSM_Res')
IMSI_WithLMSI=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('lmsi',None,LMSI,0)], seq_name = 'IMSI_WithLMSI')
NoteSubscriberDataModifiedRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoteSubscriberDataModifiedRes')
SendAuthenticationInfoArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('numberOfRequestedVectors',None,NumberOfRequestedVectors,0),
    ('segmentationProhibited',None,asn1.NULL,1),
    ('immediateResponsePreferred',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('re_synchronisationInfo',None,Re_synchronisationInfo,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendAuthenticationInfoArg')
StatusReportRes=asn1.SEQUENCE ([('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'StatusReportRes')
TargetCellOutsideGCA_Param=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'TargetCellOutsideGCA_Param')
AnyTimeInterrogationArg=asn1.SEQUENCE ([('subscriberIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SubscriberIdentity),0),
    ('requestedInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RequestedInfo),0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AnyTimeInterrogationArg')
StatusReportArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('eventReportData',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),EventReportData),1),
    ('callReportdata',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallReportData),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'StatusReportArg')
SMS_CAMEL_TDP_Data=asn1.SEQUENCE ([('sms_TriggerDetectionPoint',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SMS_TriggerDetectionPoint),0),
    ('serviceKey',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ServiceKey),0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultSMS_Handling',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),DefaultSMS_Handling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SMS_CAMEL_TDP_Data')
SS_InvocationNotificationRes=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS_InvocationNotificationRes')
ForwardingViolationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ForwardingViolationParam')
ReportSM_DeliveryStatusArg=asn1.SEQUENCE ([('msisdn',None,ISDN_AddressString,0),
    ('serviceCentreAddress',None,AddressString,0),
    ('sm_DeliveryOutcome',None,SM_DeliveryOutcome,0),
    ('absentSubscriberDiagnosticSM',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),AbsentSubscriberDiagnosticSM),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ReportSM_DeliveryStatusArg')
AuthenticationQuintuplet=asn1.SEQUENCE ([('rand',None,RAND,0),
    ('xres',None,XRES,0),
    ('ck',None,CK,0),
    ('ik',None,IK,0),
    ('autn',None,AUTN,0)], seq_name = 'AuthenticationQuintuplet')
MT_smsCAMELTDP_CriteriaList=asn1.SEQUENCE_OF (MT_smsCAMELTDP_Criteria)
ReportSM_DeliveryStatusRes=asn1.SEQUENCE ([('storedMSISDN',None,ISDN_AddressString,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReportSM_DeliveryStatusRes')
ProcessAccessSignalling_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an_APDU',None,AccessNetworkSignalInfo,0),
    ('selectedUMTS_Algorithms',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SelectedUMTS_Algorithms),1),
    ('selectedGSM_Algorithm',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SelectedGSM_Algorithm),1),
    ('chosenRadioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ChosenRadioResourceInformation),1),
    ('selectedRab_Id',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),RAB_Id),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ProcessAccessSignalling_Arg'))
Ext_CallBarFeatureList=asn1.SEQUENCE_OF (Ext_CallBarringFeature)
SS_SubscriptionOption=asn1.CHOICE ([('cliRestrictionOption',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CliRestrictionOption)),
    ('overrideCategory',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),OverrideCategory))])
IllegalSS_OperationParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'IllegalSS_OperationParam')
AuthenticationFailureReportArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('failureCause',None,FailureCause,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AuthenticationFailureReportArg')
SubscriberId=asn1.CHOICE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI)),
    ('tmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TMSI))])
InsertSubscriberDataRes=asn1.SEQUENCE ([('teleserviceList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TeleserviceList),1),
    ('bearerServiceList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),BearerServiceList),1),
    ('ss_List',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SS_List),1),
    ('odb_GeneralData',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ODB_GeneralData),1),
    ('regionalSubscriptionResponse',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),RegionalSubscriptionResponse),1),
    ('supportedCamelPhases',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'InsertSubscriberDataRes')
PDP_ContextInfoList=asn1.SEQUENCE_OF (PDP_ContextInfo)
UnknownSubscriberParam=asn1.SEQUENCE ([('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UnknownSubscriberParam')
MG_CSI=asn1.SEQUENCE ([('mobilityTriggers',None,MobilityTriggers,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi_Active',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'MG_CSI')
CamelInfo=asn1.SEQUENCE ([('supportedCamelPhases',None,SupportedCamelPhases,0),
    ('suppress_T_CSI',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CamelInfo')
PurgeMS_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('vlr_Number',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('sgsn_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'PurgeMS_Arg'))
Identity=asn1.CHOICE ([('imsi',None,IMSI),
    ('imsi_WithLMSI',None,IMSI_WithLMSI)])
ForwardingFeature=asn1.SEQUENCE ([('basicService',None,BasicServiceCode,1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('forwardingOptions',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ForwardingOptions),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),NoReplyConditionTime),1)], seq_name = 'ForwardingFeature')
GPRSSubscriptionDataWithdraw=asn1.CHOICE ([('allGPRSData',None,asn1.NULL),
    ('contextIdList',None,ContextIdList)])
ModificationRequestFor_CSI=asn1.SEQUENCE ([('requestedCamel_SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),RequestedCAMEL_SubscriptionInfo),0),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('modifyCSI_State',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor_CSI')
BasicServiceList=asn1.SEQUENCE_OF (Ext_BasicServiceCode)
ProvideRoamingNumberArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('msc_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('gsm_BearerCapability',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),1),
    ('networkSignalInfo',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),1),
    ('suppressionOfAnnouncement',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),SuppressionOfAnnouncement),1),
    ('gmsc_Address',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('callReferenceNumber',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),CallReferenceNumber),1),
    ('or_Interrogation',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ProvideRoamingNumberArg')
ProvideRoamingNumberRes=asn1.SEQUENCE ([('roamingNumber',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ProvideRoamingNumberRes')
GSM_SecurityContextData=asn1.SEQUENCE ([('kc',None,Kc,0),
    ('cksn',None,Cksn,0)], seq_name = 'GSM_SecurityContextData')
InformServiceCentreArg=asn1.SEQUENCE ([('storedMSISDN',None,ISDN_AddressString,1),
    ('mw_Status',None,MW_Status,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'InformServiceCentreArg')
O_BcsmCamelTDPData=asn1.SEQUENCE ([('o_BcsmTriggerDetectionPoint',None,O_BcsmTriggerDetectionPoint,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultCallHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DefaultCallHandling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'O_BcsmCamelTDPData')
Additional_Number=asn1.CHOICE ([('msc_Number',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString)),
    ('sgsn_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString))])
SM_DeliveryFailureCause=asn1.SEQUENCE ([('sm_EnumeratedDeliveryFailureCause',None,SM_EnumeratedDeliveryFailureCause,0),
    ('diagnosticInfo',None,SignalInfo,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SM_DeliveryFailureCause')
CUG_Feature=asn1.SEQUENCE ([('basicService',None,Ext_BasicServiceCode,1),
    ('preferentialCUG_Indicator',None,CUG_Index,1),
    ('interCUG_Restrictions',None,InterCUG_Restrictions,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CUG_Feature')
VoiceGroupCallData=asn1.SEQUENCE ([('groupId',None,GroupId,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'VoiceGroupCallData')
SMS_CAMEL_TDP_DataList=asn1.SEQUENCE_OF (SMS_CAMEL_TDP_Data)
VBSDataList=asn1.SEQUENCE_OF (VoiceBroadcastData)
TracePropagationList=asn1.SEQUENCE ([('traceReference',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TraceReference),1),
    ('traceType',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceType),1),
    ('traceReference2',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),TraceReference2),1),
    ('traceRecordingSessionReference',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),TraceRecordingSessionReference),1),
    ('rnc_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('rnc_InterfaceList',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),RNC_InterfaceList),1),
    ('msc_s_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('msc_s_InterfaceList',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),MSC_S_InterfaceList),1),
    ('msc_s_EventList',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),MSC_S_EventList),1),
    ('mgw_TraceDepth',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),TraceDepth),1),
    ('mgw_InterfaceList',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),MGW_InterfaceList),1),
    ('mgw_EventList',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),MGW_EventList),1)], seq_name = 'TracePropagationList')
Ext_ForwFeature=asn1.SEQUENCE ([('basicService',None,Ext_BasicServiceCode,1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('forwardingOptions',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),Ext_ForwOptions),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),Ext_NoRepCondTime),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext_ForwFeature')
GPRS_CamelTDPData=asn1.SEQUENCE ([('gprs_TriggerDetectionPoint',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GPRS_TriggerDetectionPoint),0),
    ('serviceKey',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ServiceKey),0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultSessionHandling',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),DefaultGPRS_Handling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'GPRS_CamelTDPData')
BasicServiceCriteria=asn1.SEQUENCE_OF (Ext_BasicServiceCode)
ProvideSubscriberInfoArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('requestedInfo',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),RequestedInfo),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ProvideSubscriberInfoArg')
LSAData=asn1.SEQUENCE ([('lsaIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),LSAIdentity),0),
    ('lsaAttributes',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LSAAttributes),0),
    ('lsaActiveModeIndicator',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LSAData')
ReleaseResourcesArg=asn1.SEQUENCE ([('msrn',None,ISDN_AddressString,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReleaseResourcesArg')
Ext_BasicServiceGroupList=asn1.SEQUENCE_OF (Ext_BasicServiceCode)
AuthenticationTriplet=asn1.SEQUENCE ([('rand',None,RAND,0),
    ('sres',None,SRES,0),
    ('kc',None,Kc,0)], seq_name = 'AuthenticationTriplet')
T_BcsmCamelTDPData=asn1.SEQUENCE ([('t_BcsmTriggerDetectionPoint',None,T_BcsmTriggerDetectionPoint,0),
    ('serviceKey',None,ServiceKey,0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('defaultCallHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DefaultCallHandling),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'T_BcsmCamelTDPData')
ReadyForSM_Arg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('alertReason',None,AlertReason,0),
    ('alertReasonIndicator',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ReadyForSM_Arg')
SMS_CSI=asn1.SEQUENCE ([('sms_CAMEL_TDP_DataList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SMS_CAMEL_TDP_DataList),1),
    ('camelCapabilityHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CamelCapabilityHandling),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi_Active',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'SMS_CSI')
RelocationNumber=asn1.SEQUENCE ([('handoverNumber',None,ISDN_AddressString,0),
    ('rab_Id',None,RAB_Id,0)], seq_name = 'RelocationNumber')
ModificationRequestFor_IP_SM_GW_Data=asn1.SEQUENCE ([('modifyRegistrationStatus',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor_IP_SM_GW_Data')
NoteMsPresentForGprsArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('sgsn_Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GSN_Address),0),
    ('ggsn_Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NoteMsPresentForGprsArg')
BasicServiceGroupList=asn1.SEQUENCE_OF (BasicServiceCode)
Ext_ForwFeatureList=asn1.SEQUENCE_OF (Ext_ForwFeature)
O_BcsmCamelTDPDataList=asn1.SEQUENCE_OF (O_BcsmCamelTDPData)
GMLC_List=asn1.SEQUENCE_OF (ISDN_AddressString)
PDP_Context=asn1.SEQUENCE ([('pdp_ContextId',None,ContextId,0),
    ('pdp_Type',None,asn1.TYPE(asn1.IMPLICIT(16,cls=asn1.CONTEXT_FLAG),PDP_Type),0),
    ('pdp_Address',None,asn1.TYPE(asn1.IMPLICIT(17,cls=asn1.CONTEXT_FLAG),PDP_Address),1),
    ('qos_Subscribed',None,asn1.TYPE(asn1.IMPLICIT(18,cls=asn1.CONTEXT_FLAG),QoS_Subscribed),0),
    ('vplmnAddressAllowed',None,asn1.TYPE(asn1.IMPLICIT(19,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('apn',None,asn1.TYPE(asn1.IMPLICIT(20,cls=asn1.CONTEXT_FLAG),APN),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(21,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PDP_Context')
SM_RP_DA=asn1.CHOICE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI)),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LMSI)),
    ('serviceCentreAddressDA',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AddressString)),
    ('noSM_RP_DA',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),asn1.NULL))])
HLR_List=asn1.SEQUENCE_OF (HLR_Id)
TraceInterfaceList=asn1.SEQUENCE ([('msc_s_List',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MSC_S_InterfaceList),1),
    ('mgw_List',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),MGW_InterfaceList),1),
    ('sgsn_List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SGSN_InterfaceList),1),
    ('ggsn_List',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),GGSN_InterfaceList),1),
    ('rnc_List',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),RNC_InterfaceList),1),
    ('bmsc_List',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),BMSC_InterfaceList),1)], seq_name = 'TraceInterfaceList')
FailureReportArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('ggsn_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('ggsn_Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'FailureReportArg')
SystemFailureParam=asn1.CHOICE ([('networkResource',None,NetworkResource),
    ('extensibleSystemFailureParam',None,ExtensibleSystemFailureParam)])
MT_ForwardSM_VGCS_Arg=asn1.SEQUENCE ([('asciCallReference',None,ASCI_CallReference,0),
    ('sm_RP_OA',None,SM_RP_OA,0),
    ('sm_RP_UI',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MT_ForwardSM_VGCS_Arg')
ODB_Info=asn1.SEQUENCE ([('odb_Data',None,ODB_Data,0),
    ('notificationToCSE',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ODB_Info')
T_BcsmCamelTDPDataList=asn1.SEQUENCE_OF (T_BcsmCamelTDPData)
CallBarringFeature=asn1.SEQUENCE ([('basicService',None,BasicServiceCode,1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1)], seq_name = 'CallBarringFeature')
AlertServiceCentreArg=asn1.SEQUENCE ([('msisdn',None,ISDN_AddressString,0),
    ('serviceCentreAddress',None,AddressString,0)], seq_name = 'AlertServiceCentreArg')
CUG_RejectParam=asn1.SEQUENCE ([('cug_RejectCause',None,CUG_RejectCause,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CUG_RejectParam')
LocationInformationGPRS=asn1.SEQUENCE ([('cellGlobalIdOrServiceAreaIdOrLAI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CellGlobalIdOrServiceAreaIdOrLAI),1),
    ('routeingAreaIdentity',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RAIdentity),1),
    ('geographicalInformation',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),GeographicalInformation),1),
    ('sgsn_Number',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('selectedLSAIdentity',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),LSAIdentity),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LocationInformationGPRS')
SupportedCodecsList=asn1.SEQUENCE ([('utranCodecList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CodecList),1),
    ('geranCodecList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CodecList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SupportedCodecsList')
RegisterSS_Arg=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('basicService',None,BasicServiceCode,1),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),NoReplyConditionTime),1)], seq_name = 'RegisterSS_Arg')
GPRSDataList=asn1.SEQUENCE_OF (PDP_Context)
SendRoutingInfoForGprsArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('ggsn_Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GSN_Address),1),
    ('ggsn_Number',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoForGprsArg')
PrepareSubsequentHO_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('targetCellId',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GlobalCellId),1),
    ('targetMSC_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('targetRNCId',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),RNCId),1),
    ('an_APDU',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),AccessNetworkSignalInfo),1),
    ('selectedRab_Id',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),RAB_Id),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareSubsequentHO_Arg'))
ModificationRequestFor_CF_Info=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('basicService',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),1),
    ('forwardedToNumber',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),AddressString),1),
    ('forwardedToSubaddress',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('noReplyConditionTime',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),Ext_NoRepCondTime),1),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor_CF_Info')
LocationInformation=asn1.SEQUENCE ([('ageOfLocationInformation',None,AgeOfLocationInformation,1),
    ('geographicalInformation',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GeographicalInformation),1),
    ('vlr_number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('locationNumber',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),LocationNumber),1),
    ('cellGlobalIdOrServiceAreaIdOrLAI',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),CellGlobalIdOrServiceAreaIdOrLAI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LocationInformation')
SS_IncompatibilityCause=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_Code),1),
    ('basicService',None,BasicServiceCode,1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1)], seq_name = 'SS_IncompatibilityCause')
ModificationRequestFor_ODB_data=asn1.SEQUENCE ([('odb_data',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ODB_Data),1),
    ('modifyNotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ModificationInstruction),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ModificationRequestFor_ODB_data')
CCBS_Feature=asn1.SEQUENCE ([('ccbs_Index',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_Index),1),
    ('b_subscriberNumber',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('b_subscriberSubaddress',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_SubaddressString),1),
    ('basicServiceGroup',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),BasicServiceCode),1)], seq_name = 'CCBS_Feature')
CallBarringFeatureList=asn1.SEQUENCE_OF (CallBarringFeature)
ExternalClient=asn1.SEQUENCE ([('clientIdentity',None,LCSClientExternalID,0),
    ('gmlc_Restriction',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GMLC_Restriction),1),
    ('notificationToMSUser',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),NotificationToMSUser),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ExternalClient')
RoutingInfo=asn1.CHOICE ([('roamingNumber',None,ISDN_AddressString),
    ('forwardingData',None,ForwardingData)])
ForwardAccessSignalling_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an_APDU',None,AccessNetworkSignalInfo,0),
    ('integrityProtectionInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IntegrityProtectionInformation),1),
    ('encryptionInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),EncryptionInformation),1),
    ('keyStatus',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),KeyStatus),1),
    ('allowedGSM_Algorithms',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),AllowedGSM_Algorithms),1),
    ('allowedUMTS_Algorithms',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),AllowedUMTS_Algorithms),1),
    ('radioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),RadioResourceInformation),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ForwardAccessSignalling_Arg'))
DispatcherList=asn1.SEQUENCE_OF (ISDN_AddressString)
O_CSI=asn1.SEQUENCE ([('o_BcsmCamelTDPDataList',None,O_BcsmCamelTDPDataList,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'O_CSI')
QuintupletList=asn1.SEQUENCE_OF (AuthenticationQuintuplet)
MT_ForwardSM_Arg=asn1.SEQUENCE ([('sm_RP_DA',None,SM_RP_DA,0),
    ('sm_RP_OA',None,SM_RP_OA,0),
    ('sm_RP_UI',None,SignalInfo,0),
    ('moreMessagesToSend',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MT_ForwardSM_Arg')
PrepareSubsequentHO_Res=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an_APDU',None,AccessNetworkSignalInfo,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareSubsequentHO_Res'))
PS_SubscriberState=asn1.CHOICE ([('notProvidedFromSGSN',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps_Detached',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps_AttachedNotReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps_AttachedReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL)),
    ('ps_PDP_ActiveNotReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),PDP_ContextInfoList)),
    ('ps_PDP_ActiveReachableForPaging',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),PDP_ContextInfoList)),
    ('netDetNotReachable',None,NotReachableReason)])
SGSN_Capability=asn1.SEQUENCE ([('solsaSupportIndicator',None,asn1.NULL,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SGSN_Capability')
SendEndSignal_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('an_APDU',None,AccessNetworkSignalInfo,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendEndSignal_Arg'))
CallBarredParam=asn1.CHOICE ([('callBarringCause',None,CallBarringCause),
    ('extensibleCallBarredParam',None,ExtensibleCallBarredParam)])
RemoteUserFreeArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('callInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),0),
    ('ccbs_Feature',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CCBS_Feature),0),
    ('translatedB_Number',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('replaceB_Number',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('alertingPattern',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),AlertingPattern),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RemoteUserFreeArg')
CancelLocationArg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('identity',None,Identity,0),
    ('cancellationType',None,CancellationType,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CancelLocationArg'))
RequestedSubscriptionInfo=asn1.SEQUENCE ([('requestedSS_Info',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_ForBS_Code),1),
    ('odb',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('requestedCAMEL_SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),RequestedCAMEL_SubscriptionInfo),1),
    ('supportedVLR_CAMEL_Phases',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('supportedSGSN_CAMEL_Phases',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RequestedSubscriptionInfo')
VLR_Capability=asn1.SEQUENCE ([('supportedCamelPhases',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'VLR_Capability')
LSAInformationWithdraw=asn1.CHOICE ([('allLSAData',None,asn1.NULL),
    ('lsaIdentityList',None,LSAIdentityList)])
CallBarringData=asn1.SEQUENCE ([('callBarringFeatureList',None,Ext_CallBarFeatureList,0),
    ('password',None,Password,1),
    ('wrongPasswordAttemptsCounter',None,WrongPasswordAttemptsCounter,1),
    ('notificationToCSE',None,asn1.NULL,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'CallBarringData')
DP_AnalysedInfoCriteriaList=asn1.SEQUENCE_OF (DP_AnalysedInfoCriterium)
CUG_FeatureList=asn1.SEQUENCE_OF (CUG_Feature)
AnyTimeSubscriptionInterrogationArg=asn1.SEQUENCE ([('subscriberIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SubscriberIdentity),0),
    ('requestedSubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RequestedSubscriptionInfo),0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('longFTN_Supported',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'AnyTimeSubscriptionInterrogationArg')
LSADataList=asn1.SEQUENCE_OF (LSAData)
Ext_ForwInfo=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('forwardingFeatureList',None,Ext_ForwFeatureList,0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext_ForwInfo')
Ext_SS_Data=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),Ext_SS_Status),0),
    ('ss_SubscriptionOption',None,SS_SubscriptionOption,1),
    ('basicServiceGroupList',None,Ext_BasicServiceGroupList,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext_SS_Data')
O_BcsmCamelTDP_Criteria=asn1.SEQUENCE ([('o_BcsmTriggerDetectionPoint',None,O_BcsmTriggerDetectionPoint,0),
    ('destinationNumberCriteria',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),DestinationNumberCriteria),1),
    ('basicServiceCriteria',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),BasicServiceCriteria),1),
    ('callTypeCriteria',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallTypeCriteria),1)], seq_name = 'O_BcsmCamelTDP_Criteria')
ForwardingFeatureList=asn1.SEQUENCE_OF (ForwardingFeature)
SS_CSI=asn1.SEQUENCE ([('ss_CamelData',None,SS_CamelData,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SS_CSI')
LocationInfoWithLMSI=asn1.SEQUENCE ([('networkNode_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('lmsi',None,LMSI,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'LocationInfoWithLMSI')
CUG_Subscription=asn1.SEQUENCE ([('cug_Index',None,CUG_Index,0),
    ('cug_Interlock',None,CUG_Interlock,0),
    ('intraCUG_Options',None,IntraCUG_Options,0),
    ('basicServiceGroupList',None,Ext_BasicServiceGroupList,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CUG_Subscription')
CallBarringInfo=asn1.SEQUENCE ([('ss_Code',None,SS_Code,1),
    ('callBarringFeatureList',None,CallBarringFeatureList,0)], seq_name = 'CallBarringInfo')
MT_ForwardSM_VGCS_Res=asn1.SEQUENCE ([('sm_RP_UI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SignalInfo),1),
    ('dispatcherList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),DispatcherList),1),
    ('ongoingCall',None,asn1.NULL,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MT_ForwardSM_VGCS_Res')
MOLR_List=asn1.SEQUENCE_OF (MOLR_Class)
MSISDN_BS=asn1.SEQUENCE ([('msisdn',None,ISDN_AddressString,0),
    ('basicServiceList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),BasicServiceList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'MSISDN_BS')
GPRSSubscriptionData=asn1.SEQUENCE ([('completeDataListIncluded',None,asn1.NULL,1),
    ('gprsDataList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),GPRSDataList),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'GPRSSubscriptionData')
CCBS_FeatureList=asn1.SEQUENCE_OF (CCBS_Feature)
Ext_CallBarInfo=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('callBarringFeatureList',None,Ext_CallBarFeatureList,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'Ext_CallBarInfo')
Ext_CallBarringInfoFor_CSE=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('callBarringFeatureList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarFeatureList),0),
    ('password',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Password),1),
    ('wrongPasswordAttemptsCounter',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),WrongPasswordAttemptsCounter),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext_CallBarringInfoFor_CSE')
GPRS_CamelTDPDataList=asn1.SEQUENCE_OF (GPRS_CamelTDPData)
SubscriberInfo=asn1.SEQUENCE ([('locationInformation',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),LocationInformation),1),
    ('subscriberState',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SubscriberState),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SubscriberInfo')
CallForwardingData=asn1.SEQUENCE ([('forwardingFeatureList',None,Ext_ForwFeatureList,0),
    ('notificationToCSE',None,asn1.NULL,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CallForwardingData')
PrepareHO_Arg=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('targetCellId',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GlobalCellId),1),
    ('ho_NumberNotRequired',None,asn1.NULL,1),
    ('targetRNCId',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RNCId),1),
    ('an_APDU',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AccessNetworkSignalInfo),1),
    ('multipleBearerRequested',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('integrityProtectionInfo',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),IntegrityProtectionInformation),1),
    ('encryptionInfo',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),EncryptionInformation),1),
    ('radioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),RadioResourceInformation),1),
    ('allowedGSM_Algorithms',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),AllowedGSM_Algorithms),1),
    ('allowedUMTS_Algorithms',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),AllowedUMTS_Algorithms),1),
    ('radioResourceList',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),RadioResourceList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareHO_Arg'))
ResetArg=asn1.SEQUENCE ([('hlr_Number',None,ISDN_AddressString,0),
    ('hlr_List',None,HLR_List,1)], seq_name = 'ResetArg')
CurrentSecurityContext=asn1.CHOICE ([('gsm_SecurityContextData',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GSM_SecurityContextData)),
    ('umts_SecurityContextData',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),UMTS_SecurityContextData))])
CCBS_Data=asn1.SEQUENCE ([('ccbs_Feature',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_Feature),0),
    ('translatedB_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('serviceIndicator',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ServiceIndicator),1),
    ('callInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),0),
    ('networkSignalInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),0)], seq_name = 'CCBS_Data')
GPRS_CSI=asn1.SEQUENCE ([('gprs_CamelTDPDataList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GPRS_CamelTDPDataList),1),
    ('camelCapabilityHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CamelCapabilityHandling),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi_Active',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'GPRS_CSI')
RelocationNumberList=asn1.SEQUENCE_OF (RelocationNumber)
SendRoutingInfoArg=asn1.SEQUENCE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('cug_CheckInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CUG_CheckInfo),1),
    ('numberOfForwarding',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),NumberOfForwarding),1),
    ('interrogationType',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),InterrogationType),0),
    ('or_Interrogation',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('or_Capability',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),OR_Phase),1),
    ('gmsc_OrGsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('callReferenceNumber',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),CallReferenceNumber),1),
    ('forwardingReason',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ForwardingReason),1),
    ('basicServiceGroup',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('networkSignalInfo',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),ExternalSignalInfo),1),
    ('camelInfo',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),CamelInfo),1),
    ('suppressionOfAnnouncement',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),SuppressionOfAnnouncement),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoArg')
RegisterCC_EntryRes=asn1.SEQUENCE ([('ccbs_Feature',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CCBS_Feature),1)], seq_name = 'RegisterCC_EntryRes')
AnyTimeInterrogationRes=asn1.SEQUENCE ([('subscriberInfo',None,SubscriberInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'AnyTimeInterrogationRes')
Ext_ExternalClientList=asn1.SEQUENCE_OF (ExternalClient)
RegisterCC_EntryArg=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('ccbs_Data',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CCBS_Data),1)], seq_name = 'RegisterCC_EntryArg')
VGCSDataList=asn1.SEQUENCE_OF (VoiceGroupCallData)
TripletList=asn1.SEQUENCE_OF (AuthenticationTriplet)
ExternalClientList=asn1.SEQUENCE_OF (ExternalClient)
RestoreDataArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('lmsi',None,LMSI,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'RestoreDataArg')
SGSN_CAMEL_SubscriptionInfo=asn1.SEQUENCE ([('gprs_CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GPRS_CSI),1),
    ('mo_sms_CSI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SMS_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SGSN_CAMEL_SubscriptionInfo')
ActivateTraceModeArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('traceReference',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),TraceReference),0),
    ('traceType',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),TraceType),0),
    ('omc_Id',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),AddressString),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'ActivateTraceModeArg')
T_BCSM_CAMEL_TDP_Criteria=asn1.SEQUENCE ([('t_BCSM_TriggerDetectionPoint',None,T_BcsmTriggerDetectionPoint,0),
    ('basicServiceCriteria',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),BasicServiceCriteria),1),
    ('t_CauseValueCriteria',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),T_CauseValueCriteria),1)], seq_name = 'T_BCSM_CAMEL_TDP_Criteria')
Ext_ForwardingInfoFor_CSE=asn1.SEQUENCE ([('ss_Code',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Code),0),
    ('forwardingFeatureList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_ForwFeatureList),0),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'Ext_ForwardingInfoFor_CSE')
LSAInformation=asn1.SEQUENCE ([('completeDataListIncluded',None,asn1.NULL,1),
    ('lsaOnlyAccessIndicator',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LSAOnlyAccessIndicator),1),
    ('lsaDataList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),LSADataList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LSAInformation')
SS_Data=asn1.SEQUENCE ([('ss_Code',None,SS_Code,1),
    ('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),SS_Status),1),
    ('ss_SubscriptionOption',None,SS_SubscriptionOption,1),
    ('basicServiceGroupList',None,BasicServiceGroupList,1)], seq_name = 'SS_Data')
ProvideSubscriberInfoRes=asn1.SEQUENCE ([('subscriberInfo',None,SubscriberInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'ProvideSubscriberInfoRes')
T_BCSM_CAMEL_TDP_CriteriaList=asn1.SEQUENCE_OF (T_BCSM_CAMEL_TDP_Criteria)
MO_ForwardSM_Arg=asn1.SEQUENCE ([('sm_RP_DA',None,SM_RP_DA,0),
    ('sm_RP_OA',None,SM_RP_OA,0),
    ('sm_RP_UI',None,SignalInfo,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'MO_ForwardSM_Arg')
T_CSI=asn1.SEQUENCE ([('t_BcsmCamelTDPDataList',None,T_BcsmCamelTDPDataList,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'T_CSI')
NoteMM_EventArg=asn1.SEQUENCE ([('serviceKey',None,ServiceKey,0),
    ('eventMet',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),MM_Code),0),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('locationInformation',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),LocationInformation),1),
    ('supportedCAMELPhases',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'NoteMM_EventArg')
AuthenticationSetList=asn1.CHOICE ([('tripletList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),TripletList)),
    ('quintupletList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),QuintupletList))])
UpdateGprsLocationArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('sgsn_Number',None,ISDN_AddressString,0),
    ('sgsn_Address',None,GSN_Address,0),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateGprsLocationArg')
AnyTimeModificationArg=asn1.SEQUENCE ([('subscriberIdentity',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SubscriberIdentity),0),
    ('gsmSCF_Address',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('modificationRequestFor_CF_Info',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ModificationRequestFor_CF_Info),1),
    ('modificationRequestFor_CB_Info',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ModificationRequestFor_CB_Info),1),
    ('modificationRequestFor_CSI',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ModificationRequestFor_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('longFTN_Supported',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'AnyTimeModificationArg')
CUG_SubscriptionList=asn1.SEQUENCE_OF (CUG_Subscription)
UpdateLocationArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('msc_Number',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),0),
    ('vlr_Number',None,ISDN_AddressString,0),
    ('lmsi',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),LMSI),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'UpdateLocationArg')
ForwardingInfo=asn1.SEQUENCE ([('ss_Code',None,SS_Code,1),
    ('forwardingFeatureList',None,ForwardingFeatureList,0)], seq_name = 'ForwardingInfo')
DeleteSubscriberDataArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),0),
    ('basicServiceList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),BasicServiceList),1),
    ('ss_List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),SS_List),1),
    ('roamingRestrictionDueToUnsupportedFeature',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('regionalSubscriptionIdentifier',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),ZoneCode),1),
    ('vbsGroupIndication',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('vgcsGroupIndication',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('camelSubscriptionInfoWithdraw',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'DeleteSubscriberDataArg')
D_CSI=asn1.SEQUENCE ([('dp_AnalysedInfoCriteriaList',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),DP_AnalysedInfoCriteriaList),1),
    ('camelCapabilityHandling',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CamelCapabilityHandling),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('notificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('csi_Active',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'D_CSI')
O_BcsmCamelTDPCriteriaList=asn1.SEQUENCE_OF (O_BcsmCamelTDP_Criteria)
GenericServiceInfo=asn1.SEQUENCE ([('ss_Status',None,SS_Status,0),
    ('cliRestrictionOption',None,CliRestrictionOption,1)], seq_name = 'GenericServiceInfo')
RoutingInfoForSM_Res=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('locationInfoWithLMSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),LocationInfoWithLMSI),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'RoutingInfoForSM_Res')
LCS_PrivacyClass=asn1.SEQUENCE ([('ss_Code',None,SS_Code,0),
    ('ss_Status',None,Ext_SS_Status,0),
    ('notificationToMSUser',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),NotificationToMSUser),1),
    ('externalClientList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExternalClientList),1),
    ('plmnClientList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),PLMNClientList),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'LCS_PrivacyClass')
LCS_PrivacyExceptionList=asn1.SEQUENCE_OF (LCS_PrivacyClass)
PrepareHO_Res=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('handoverNumber',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('relocationNumberList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),RelocationNumberList),1),
    ('an_APDU',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),AccessNetworkSignalInfo),1),
    ('multicallBearerInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),MulticallBearerInfo),1),
    ('multipleBearerNotSupported',None,asn1.NULL,1),
    ('selectedUMTS_Algorithms',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),SelectedUMTS_Algorithms),1),
    ('chosenRadioResourceInformation',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),ChosenRadioResourceInformation),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'PrepareHO_Res'))
LCSInformation=asn1.SEQUENCE ([('gmlc_List',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GMLC_List),1),
    ('lcs_PrivacyExceptionList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),LCS_PrivacyExceptionList),1),
    ('molr_List',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),MOLR_List),1)], seq_name = 'LCSInformation')
GmscCamelSubscriptionInfo=asn1.SEQUENCE ([('t_CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),T_CSI),1),
    ('o_CSI',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'GmscCamelSubscriptionInfo')
MSISDN_BS_List=asn1.SEQUENCE_OF (MSISDN_BS)
InsertSubscriberDataArg=asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(14,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'InsertSubscriberDataArg')
Ext_SS_InfoFor_CSE=asn1.CHOICE ([('forwardingInfoFor_CSE',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_ForwardingInfoFor_CSE)),
    ('callBarringInfoFor_CSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarringInfoFor_CSE))])
SendAuthenticationInfoRes=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('authenticationSetList',None,AuthenticationSetList,1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'SendAuthenticationInfoRes'))
SS_Info=asn1.CHOICE ([('forwardingInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ForwardingInfo)),
    ('callBarringInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CallBarringInfo)),
    ('ss_Data',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SS_Data))])
InterrogateSS_Res=asn1.CHOICE ([('ss_Status',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),SS_Status)),
    ('basicServiceGroupList',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),BasicServiceGroupList)),
    ('forwardingFeatureList',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ForwardingFeatureList)),
    ('genericServiceInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),GenericServiceInfo))])
CamelRoutingInfo=asn1.SEQUENCE ([('forwardingData',None,ForwardingData,1),
    ('gmscCamelSubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),GmscCamelSubscriptionInfo),0),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CamelRoutingInfo')
CUG_Info=asn1.SEQUENCE ([('cug_SubscriptionList',None,CUG_SubscriptionList,0),
    ('cug_FeatureList',None,CUG_FeatureList,1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CUG_Info')
VlrCamelSubscriptionInfo=asn1.SEQUENCE ([('o_CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'VlrCamelSubscriptionInfo')
SendIdentificationRes=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('imsi',None,IMSI,1),
    ('authenticationSetList',None,AuthenticationSetList,1),
    ('currentSecurityContext',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CurrentSecurityContext),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendIdentificationRes'))
ResumeCallHandlingArg=asn1.SEQUENCE ([('callReferenceNumber',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),CallReferenceNumber),1),
    ('basicServiceGroup',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('forwardingData',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ForwardingData),1),
    ('imsi',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('cug_CheckInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),CUG_CheckInfo),1),
    ('o_CSI',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1),
    ('ccbs_Possible',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('msisdn',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('uu_Data',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),UU_Data),1),
    ('allInformationSent',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),asn1.NULL),1)], seq_name = 'ResumeCallHandlingArg')
CAMEL_SubscriptionInfo=asn1.SEQUENCE ([('o_CSI',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),O_CSI),1),
    ('o_BcsmCamelTDP_CriteriaList',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),O_BcsmCamelTDPCriteriaList),1),
    ('d_CSI',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),D_CSI),1),
    ('t_CSI',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),T_CSI),1),
    ('t_BCSM_CAMEL_TDP_CriteriaList',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),T_BCSM_CAMEL_TDP_CriteriaList),1),
    ('vt_CSI',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),T_CSI),1),
    ('vt_BCSM_CAMEL_TDP_CriteriaList',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),T_BCSM_CAMEL_TDP_CriteriaList),1),
    ('tif_CSI',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('tif_CSI_NotificationToCSE',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('gprs_CSI',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),GPRS_CSI),1),
    ('mo_sms_CSI',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),SMS_CSI),1),
    ('ss_CSI',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),SS_CSI),1),
    ('m_CSI',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),M_CSI),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'CAMEL_SubscriptionInfo')
AnyTimeModificationRes=asn1.SEQUENCE ([('ss_InfoFor_CSE',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_SS_InfoFor_CSE),1),
    ('camel_SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CAMEL_SubscriptionInfo),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AnyTimeModificationRes')
SS_InfoList=asn1.SEQUENCE_OF (SS_Info)
AnyTimeSubscriptionInterrogationRes=asn1.SEQUENCE ([('callForwardingData',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),CallForwardingData),1),
    ('callBarringData',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CallBarringData),1),
    ('odb_Info',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),ODB_Info),1),
    ('camel_SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),CAMEL_SubscriptionInfo),1),
    ('supportedVLR_CAMEL_Phases',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('supportedSGSN_CAMEL_Phases',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),SupportedCamelPhases),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'AnyTimeSubscriptionInterrogationRes')
Ext_SS_Info=asn1.CHOICE ([('forwardingInfo',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_ForwInfo)),
    ('callBarringInfo',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarInfo)),
    ('cug_Info',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),CUG_Info)),
    ('ss_Data',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),Ext_SS_Data)),
    ('emlpp_Info',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),EMLPP_Info))])
ExtendedRoutingInfo=asn1.CHOICE ([('routingInfo',None,RoutingInfo),
    ('camelRoutingInfo',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),CamelRoutingInfo))])
NoteSubscriberDataModifiedArg=asn1.SEQUENCE ([('imsi',None,IMSI,0),
    ('msisdn',None,ISDN_AddressString,0),
    ('forwardingInfoFor_CSE',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),Ext_ForwardingInfoFor_CSE),1),
    ('callBarringInfoFor_CSE',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),Ext_CallBarringInfoFor_CSE),1),
    ('odb_Info',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ODB_Info),1),
    ('camel_SubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),CAMEL_SubscriptionInfo),1),
    ('allInformationSent',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('extensionContainer',None,ExtensionContainer,1)], seq_name = 'NoteSubscriberDataModifiedArg')
Ext_SS_InfoList=asn1.SEQUENCE_OF (Ext_SS_Info)
SendRoutingInfoRes=asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),asn1.SEQUENCE ([('imsi',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),IMSI),1),
    ('extendedRoutingInfo',None,ExtendedRoutingInfo,1),
    ('cug_CheckInfo',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),CUG_CheckInfo),1),
    ('cugSubscriptionFlag',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('subscriberInfo',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),SubscriberInfo),1),
    ('ss_List',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),SS_List),1),
    ('basicService',None,asn1.TYPE(asn1.IMPLICIT(5,cls=asn1.CONTEXT_FLAG),Ext_BasicServiceCode),1),
    ('forwardingInterrogationRequired',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('vmsc_Address',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('extensionContainer',None,asn1.TYPE(asn1.IMPLICIT(0,cls=asn1.CONTEXT_FLAG),ExtensionContainer),1)], seq_name = 'SendRoutingInfoRes'))
SubscriberData=asn1.SEQUENCE ([('msisdn',None,asn1.TYPE(asn1.IMPLICIT(1,cls=asn1.CONTEXT_FLAG),ISDN_AddressString),1),
    ('category',None,asn1.TYPE(asn1.IMPLICIT(2,cls=asn1.CONTEXT_FLAG),Category),1),
    ('subscriberStatus',None,asn1.TYPE(asn1.IMPLICIT(3,cls=asn1.CONTEXT_FLAG),SubscriberStatus),1),
    ('bearerServiceList',None,asn1.TYPE(asn1.IMPLICIT(4,cls=asn1.CONTEXT_FLAG),BearerServiceList),1),
    ('teleserviceList',None,asn1.TYPE(asn1.IMPLICIT(6,cls=asn1.CONTEXT_FLAG),TeleserviceList),1),
    ('provisionedSS',None,asn1.TYPE(asn1.IMPLICIT(7,cls=asn1.CONTEXT_FLAG),Ext_SS_InfoList),1),
    ('odb_Data',None,asn1.TYPE(asn1.IMPLICIT(8,cls=asn1.CONTEXT_FLAG),ODB_Data),1),
    ('roamingRestrictionDueToUnsupportedFeature',None,asn1.TYPE(asn1.IMPLICIT(9,cls=asn1.CONTEXT_FLAG),asn1.NULL),1),
    ('regionalSubscriptionData',None,asn1.TYPE(asn1.IMPLICIT(10,cls=asn1.CONTEXT_FLAG),ZoneCodeList),1),
    ('vbsSubscriptionData',None,asn1.TYPE(asn1.IMPLICIT(11,cls=asn1.CONTEXT_FLAG),VBSDataList),1),
    ('vgcsSubscriptionData',None,asn1.TYPE(asn1.IMPLICIT(12,cls=asn1.CONTEXT_FLAG),VGCSDataList),1),
    ('vlrCamelSubscriptionInfo',None,asn1.TYPE(asn1.IMPLICIT(13,cls=asn1.CONTEXT_FLAG),VlrCamelSubscriptionInfo),1)], seq_name = 'SubscriberData')


