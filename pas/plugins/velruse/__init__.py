# -*- coding: utf-8 -*-

import logging

from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from .plugin import VelruseUsers, AddForm

logger = logging.getLogger('pas.plugins.velruse')

#registerMultiPlugin(VelruseUsers.meta_type)

def initialize(context):
    context.registerClass(VelruseUsers,
                          permission=add_user_folders,
                          constructors=(AddForm,),
                          visibility=None,
                          icon='openid.png'
                          )
