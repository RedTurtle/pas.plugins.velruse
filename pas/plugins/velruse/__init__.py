# -*- coding: utf-8 -*-

import logging
from AccessControl.Permissions import add_user_folders
from zope.i18nmessageid import MessageFactory

logger = logging.getLogger('pas.plugins.velruse')
_ = MessageFactory('pas.plugins.velruse')

#from Products.PluggableAuthService import registerMultiPlugin
#registerMultiPlugin(VelruseUsers.meta_type)
from pas.plugins.velruse.plugin import VelruseUsers, AddForm


def initialize(context):
    context.registerClass(VelruseUsers,
                          permission=add_user_folders,
                          constructors=(AddForm,),
                          visibility=None,
                          icon='browser/images/openid.png'
                          )
