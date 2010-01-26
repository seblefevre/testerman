from twisted.internet import reactor, defer
from pysnmp.entity.rfc3413 import ntforg

class NotificationOriginator(ntforg.NotificationOriginator):
    def sendNotification(
        self,
        snmpEngine,
        notificationTarget,
        notificationName,
        additionalVarBinds=None,
        contextName=''
        ):
        df = defer.Deferred()
        ntforg.NotificationOriginator.sendNotification(
            self,
            snmpEngine,
            notificationTarget,
            notificationName,
            additionalVarBinds,
            None,
            df,
            contextName=''
            )
        return df

    def _handleResponse(
        self,
        sendRequestHandle,
        errorIndication,
        cbFun,
        cbCtx):
        cbCtx.callback((sendRequestHandle, errorIndication))
