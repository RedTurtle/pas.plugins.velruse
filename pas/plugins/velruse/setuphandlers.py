# -*- coding: utf-8 -*-

from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from pas.plugins.velruse.plugin import VelruseUsers, PLONE4
from pas.plugins.velruse.interfaces import IVelruseGeneralSettings
from pas.plugins.velruse.persistent import VelruseBackendConfig
from pas.plugins.velruse import logger
from pas.plugins.velruse import config


def initRegistry(portal):
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IVelruseGeneralSettings, check=False)

    if settings and not settings.activated_plugins:
        for name, url, icon in (
                                (u"Twitter","","/++resource++pas.plugins.velruse.images/twitter-login-icon.png"),
                                (u"Google","","/++resource++pas.plugins.velruse.images/google-login-icon.png"),
                                (u"Facebook","","/++resource++pas.plugins.velruse.images/facebook-login-icon.png"),
                                (u"Linkedin","","/++resource++pas.plugins.velruse.images/linkedin-login-icon.png"),
                                ):
            settings.activated_plugins += (VelruseBackendConfig(name, url, icon),)
            logger.info('Added default config for %s' % name)


def installPASPlugin(portal, name, klass, title):

    userFolder = portal['acl_users']

    if name not in userFolder:
        
        plugin = klass(name, title)
        userFolder[name] = plugin
        
        # Activate all interfaces
        if PLONE4:
            activatePluginInterfaces(portal, name)
        else:
            from StringIO import StringIO
            activatePluginInterfaces(portal, name, StringIO())
        
        # Move plugin to the top of the list for each active interface
        plugins = userFolder['plugins']
        for info in plugins.listPluginTypeInfo():
            interface = info['interface']
            if plugin.testImplements(interface):
                active = list(plugins.listPluginIds(interface))
                if name in active:
                    active.remove(name)
                    active.insert(0, name)
                    plugins._plugins[interface] = tuple(active)
        logger.info('%s plugin created' % title)


def importVarious(context):
    """Miscellanous steps import handle
    """
    
    if context.readDataFile('pas.plugins.velruse-various.txt') is None:
        return
    
    portal = context.getSite()
    
    installPASPlugin(portal, config.PLUGIN_ID, VelruseUsers, 'Velruse Authentication Plugin')
    initRegistry(portal)
