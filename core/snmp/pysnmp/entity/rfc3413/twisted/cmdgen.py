from twisted.internet import reactor, defer
from pysnmp.entity.rfc3413 import cmdgen

class GetCommandGenerator(cmdgen.GetCommandGenerator):
    def sendReq(
        self,
        snmpEngine,
        addrName,
        varBinds,
        contextEngineId=None,
        contextName=''
        ):
        df = defer.Deferred()
        cmdgen.GetCommandGenerator.sendReq(
            self,
            snmpEngine,
            addrName,
            varBinds,
            None,
            df,
            contextEngineId,
            contextName
            )
        return df

    def _handleResponse(
        self,
        snmpEngine,
        transportDomain,
        transportAddress,
        messageProcessingModel,
        securityModel,
        securityName,
        securityLevel,
        contextEngineId,
        contextName,
        pduVersion,
        PDU,
        timeout,
        retryCount,
        pMod,
        rspPDU,
        sendRequestHandle,
        (cbFun, cbCtx)
        ):        
        cbCtx.callback(
            (None,
             pMod.apiPDU.getErrorStatus(rspPDU),
             pMod.apiPDU.getErrorIndex(rspPDU),
             pMod.apiPDU.getVarBinds(rspPDU))
            )

class SetCommandGenerator(cmdgen.SetCommandGenerator):
    def sendReq(
        self,
        snmpEngine,
        addrName,
        varBinds,
        contextEngineId=None,
        contextName=''
        ):
        df = defer.Deferred()
        cmdgen.SetCommandGenerator.sendReq(
            self,
            snmpEngine,
            addrName,
            varBinds,
            None,
            df,
            contextEngineId,
            contextName
            )
        return df

    def _handleResponse(
        self,
        snmpEngine,
        transportDomain,
        transportAddress,
        messageProcessingModel,
        securityModel,
        securityName,
        securityLevel,
        contextEngineId,
        contextName,
        pduVersion,
        PDU,
        timeout,
        retryCount,
        pMod,
        rspPDU,
        sendRequestHandle,
        (cbFun, cbCtx)
        ):        
        cbCtx.callback(
            (None,
             pMod.apiPDU.getErrorStatus(rspPDU),
             pMod.apiPDU.getErrorIndex(rspPDU),
             pMod.apiPDU.getVarBinds(rspPDU))
            )

class NextCommandGenerator(cmdgen.NextCommandGenerator):
    def sendReq(
        self,
        snmpEngine,
        addrName,
        varBinds,
        contextEngineId=None,
        contextName=''
        ):
        df = defer.Deferred()
        cmdgen.NextCommandGenerator.sendReq(
            self,
            snmpEngine,
            addrName,
            varBinds,
            None,
            df,
            contextEngineId,
            contextName
            )
        return df

    def _handleResponse(
        self,
        snmpEngine,
        transportDomain,
        transportAddress,
        messageProcessingModel,
        securityModel,
        securityName,
        securityLevel,
        contextEngineId,
        contextName,
        pduVersion,
        PDU,
        timeout,
        retryCount,
        pMod,
        rspPDU,
        sendRequestHandle,
        (cbFun, cbCtx)
        ):        
        cbCtx.callback(
            (None,
             pMod.apiPDU.getErrorStatus(rspPDU),
             pMod.apiPDU.getErrorIndex(rspPDU),
             pMod.apiPDU.getVarBindTable(PDU, rspPDU))
            )

class BulkCommandGenerator(cmdgen.BulkCommandGenerator):
    def sendReq(
        self,
        snmpEngine,
        addrName,
        nonRepeaters,
        maxRepetitions,
        varBinds,
        contextEngineId=None,
        contextName=''
        ):
        df = defer.Deferred()
        cmdgen.BulkCommandGenerator.sendReq(
            self,
            snmpEngine,
            addrName,
            nonRepeaters,
            maxRepetitions,
            varBinds,
            None,
            df,
            contextEngineId=None,
            contextName=''
            )
        return df

    def _handleResponse(
        self,
        snmpEngine,
        transportDomain,
        transportAddress,
        messageProcessingModel,
        securityModel,
        securityName,
        securityLevel,
        contextEngineId,
        contextName,
        pduVersion,
        PDU,
        timeout,
        retryCount,
        pMod,
        rspPDU,
        sendRequestHandle,
        (cbFun, cbCtx)
        ):        
        cbCtx.callback(
            (None,
             pMod.apiBulkPDU.getErrorStatus(rspPDU),
             pMod.apiBulkPDU.getErrorIndex(rspPDU),
             pMod.apiBulkPDU.getVarBindTable(PDU, rspPDU))
            )
