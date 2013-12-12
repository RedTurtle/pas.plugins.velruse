# -*- coding: utf-8 -*-

from plone.registry.field import PersistentField
from pas.plugins.velruse import _
from zope import schema
from z3c.form.object import registerFactoryAdapter
from zope.interface import Interface, implements
from AccessControl import allow_class

class IVelruseBackendConfig(Interface):

    service_name = schema.TextLine(title=_(u"Name"),
                                   description=_("velruse_backend_name_help",
                                                 default=u"The name of the social network/authentication service"),
                                   missing_value=u"",
                                   required=False)
    service_url = schema.ASCIILine(title=_(u"URL or path"),
                                   description=_("velruse_backend_url_help",
                                                 default=u"An URL (can also be a relative path) to Velruse.\n"
                                                         u"This URL must be properly configured in Velruse to call the remote "
                                                         u"service"),
                                   missing_value="",
                                   required=False)
    service_icon = schema.ASCIILine(title=_(u"Icon"),
                                    description=_("velruse_backend_icon_help",
                                                  default=u"An URL (can also be a relative path) to an icon to be displayed in "
                                                          u"the login form. Best format is 64x64px."),
                                    missing_value="",
                                    required=False)


class VelruseBackendConfig(object):
    implements(IVelruseBackendConfig)

    def __init__(self, service_name=u'', service_url='', service_icon=""):
        self.service_name = service_name
        self.service_url = service_url
        self.service_icon = service_icon

registerFactoryAdapter(IVelruseBackendConfig, VelruseBackendConfig)
allow_class(VelruseBackendConfig)


class PersistentObject(PersistentField, schema.Object):
    pass