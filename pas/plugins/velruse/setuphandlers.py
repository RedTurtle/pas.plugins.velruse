# -*- coding: utf-8 -*-

from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

from pas.plugins.velruse.plugin import VelruseUsers
from pas.plugins.velruse import logger

_PROPERTIES = [
    dict(name='site_login_enabled', type_='boolean', value=True),
    dict(name='activated_plugins', type_='lines', value=[]),
    dict(name='connection_timeout', type_='int', value=10),
]


def registerProperties(portal):
    ptool = portal.portal_properties
    props = ptool.velruse_settings

    for prop in _PROPERTIES:
        if not props.hasProperty(prop['name']):
            props.manage_addProperty(prop['name'], prop['value'], prop['type_'])
            logger.info("Added missing %s property" % prop['name'])


def installPASPlugin(portal, name, klass, title):

    userFolder = portal['acl_users']

    if name not in userFolder:
        
        plugin = klass(name, title)
        userFolder[name] = plugin
        
        # Activate all interfaces
        activatePluginInterfaces(portal, name)
        
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
    
    installPASPlugin(portal, 'velruse_users', VelruseUsers, 'Velruse Authentication Plugin')
    registerProperties(portal)
