# -*- coding: utf-8 -*-

from zope.interface import implements

from pas.plugins.velruse.interfaces import IVelruseFirstLoginEvent
from Products.PluggableAuthService.events import PASEvent

class VelruseFirstLoginEvent(PASEvent):
    implements(IVelruseFirstLoginEvent)
