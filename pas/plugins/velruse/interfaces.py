# -*- coding: utf-8 -*-

from zope import schema
from zope.interface import Interface
from Products.PluggableAuthService.interfaces.events import IPASEvent
from pas.plugins.velruse import _
from pas.plugins.velruse.persistent import PersistentObject, IVelruseBackendConfig


class IVelruseLayer(Interface):
    """Marker interface for pas.plugins.velruse product layer"""


class IVelrusePlugin(Interface):
    """Marker interface for the Velruse PAS Plugin"""


class IVelruseFirstLoginEvent(IPASEvent):
    """Event raise on first login of a velruse user"""


class IVelruseGeneralSettings(Interface):

    site_login_enabled = schema.Bool(
        title=_(u'Site login enabled'),
        description=_('help_site_login_enabled',
                      default="If checked, the default Plone login form will be preserved"),
        required=False,
        default=True,
    )

    activated_plugins = schema.Tuple(
        title=_(u'Authentication services enabled'),
        description=_('help_activated_plugins',
                      default="Provide a list of authentication services properly configured on the Velruse backend"),
        required=False,
        value_type=PersistentObject(IVelruseBackendConfig,
                                    title=_(u"Velruse backend")),
        default=(),
        missing_value=(),
    )

    connection_timeout = schema.Int(
        title=_(u'Connection timeout'),
        description=_('help_connection_timeout',
                      default="Max number of seconds to wait for Velruse backend response"),
        required=True,
        default=10,
    )
