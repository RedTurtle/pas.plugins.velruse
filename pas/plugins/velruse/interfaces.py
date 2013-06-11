# -*- coding: utf-8 -*-

from zope.interface import Interface
from Products.PluggableAuthService.interfaces.events import IPASEvent

class IVelrusePlugin(Interface):
    """Marker interface for the Velruse PAS Plugin"""

class IVelruseFirstLoginEvent(IPASEvent):
    """Event raise on first login of a velruse user"""
