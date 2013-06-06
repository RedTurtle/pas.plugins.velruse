# -*- coding: utf-8 -*-

from zope.interface import implements

import requests

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin

from pas.plugins.velruse.interfaces import IVelrusePlugin


class AddForm(BrowserView):
    """Add form the PAS plugin
    """
    
    def __call__(self):
        
        if 'form.button.Add' in self.request.form:
            name = self.request.form.get('id')
            title = self.request.form.get('title')
            
            plugin = VelruseUsers(name, title)
            self.context.context[name] = plugin
            
            self.request.response.redirect(self.context.absolute_url() +
                    '/manage_workspace?manage_tabs_message=Plugin+added.')


class VelruseUsers(BasePlugin):
    """
    TODO
    """
    
    # List PAS interfaces we implement here
    implements(
            IVelrusePlugin,
            IExtractionPlugin,
#            ICredentialsResetPlugin,
            IAuthenticationPlugin,
#            IPropertiesPlugin,
            IUserEnumerationPlugin,
#            IUserFactoryPlugin,
            IRolesPlugin,
        )
    
    def __init__(self, id, title=None):
        self.__name__ = self.id = id
        self.title = title
        self.manage_addProperty('velruse_server_host', '127.0.0.1:5020', 'string')
        self.manage_addProperty('velruse_auth_info_path', '/velruse/auth_info', 'string')
        self.manage_addProperty('given_roles', ['Member',], 'lines')
        #self._storage = OOBTree()

    def getRolesForPrincipal(self, principal, request=None ):

        """ principal -> ( role_1, ... role_N )

        o Return a sequence of role names which the principal has.

        o May assign roles based on values in the REQUEST object, if present.
        """
        acl_users = getToolByName(self, 'acl_users')
        vproperty = acl_users.velruse_users_properties
        if vproperty._storage.get(principal.getId()):
            return tuple(self.getProperty('given_roles'))
        return ()

    def extractCredentials(self, request):
        """ request -> {...}

        o Return a mapping of any derived credentials.

        o Return an empty mapping to indicate that the plugin found no
          appropriate credentials.
        """
        if request.form.get('token'):
            return {'velruse-token': request.form.get('token')}
        return {}

    def authenticateCredentials(self, credentials):
        """ credentials -> (userid, login)

        o 'credentials' will be a mapping, as returned by IExtractionPlugin.

        o Return a  tuple consisting of user ID (which may be different
          from the login name) and login

        o If the credentials cannot be authenticated, return None.
        """
        if not credentials.get('velruse-token'):
            return
        velruse_host = self.getProperty('velruse_server_host')
        velruse_auth_info = self.getProperty('velruse_auth_info_path')
        r = requests.get('http://%s%s' % (velruse_host, velruse_auth_info),
                         params={'format': 'json',
                                 'token': credentials.get('velruse-token')})
        raw_user_data = r.json()
        user_data = self._format_user_data(raw_user_data)
        if user_data.get('username'):
            acl_users = getToolByName(self, 'acl_users')
            username = user_data.get('username').encode('utf-8')
            acl_users.session._setupSession(username, self.REQUEST.RESPONSE)
            self._set_user_properties(user_data)
            return (username, username)

    def enumerateUsers(self, id=None, login=None, exact_match=False, sort_by=None, max_results=None, **kw):
        """ -> ( user_info_1, ... user_info_N )

        o Return mappings for users matching the given criteria.

        o 'id' or 'login', in combination with 'exact_match' true, will
          return at most one mapping per supplied ID ('id' and 'login'
          may be sequences).

        o If 'exact_match' is False, then 'id' and / or login may be
          treated by the plugin as "contains" searches (more complicated
          searches may be supported by some plugins using other keyword
          arguments).

        o If 'sort_by' is passed, the results will be sorted accordingly.
          known valid values are 'id' and 'login' (some plugins may support
          others).

        o If 'max_results' is specified, it must be a positive integer,
          limiting the number of returned mappings.  If unspecified, the
          plugin should return mappings for all users satisfying the criteria.

        o Minimal keys in the returned mappings:

          'id' -- (required) the user ID, which may be different than
                  the login name

          'login' -- (required) the login name

          'pluginid' -- (required) the plugin ID (as returned by getId())

          'editurl' -- (optional) the URL to a page for updating the
                       mapping's user

        o Plugin *must* ignore unknown criteria.

        o Plugin may raise ValueError for invalid criteria.

        o Insufficiently-specified criteria may have catastrophic
          scaling issues for some implementations.
        """
        
        acl_users = getToolByName(self, 'acl_users')
        vproperty = acl_users.velruse_users_properties
        if vproperty._storage.get(id):
            return [{'id': id,
                    'login': id,
                    'plugin_id': self.getId()}]
        return ()

#    def createUser(self, user_id, name):
#        # Create a FacebookUser just if this is a Facebook User id 
#        user_data = self._storage.get(user_id, None)
#        if user_data is not None:
#            return FacebookUser(user_id, name)
#        
#        return None

    def _set_user_properties(self, user_data):
        """
        Write user properties in the Velruse ZODB Mutable Property, if not exists
        """
        acl_users = getToolByName(self, 'acl_users')
        vproperty = acl_users.velruse_users_properties
        vproperty._storage.insert(user_data.get('username'), user_data)

    def _format_user_data(self, raw_data):
        """
        Velruse return data in a Portable Contact format but different plugins can return or not
        informations
        """
        user_data = {}
        userid_data = raw_data.get('profile', {}).get('accounts', [None])[0]
        username = "%s.%s" % (userid_data.get('domain', None),
                              userid_data.get('userid', None))
        user_data['username'] = username.encode('utf-8')
        user_data['email'] = raw_data.get('profile', {}).get('verifiedEmail', '').encode('utf-8')
        # BBB: seems that commonly email (up) is stored as string but fullname (down) is stored as unicode
        user_data['fullname'] = raw_data.get('profile', {}).get('name', {}).get('formatted', '')
        return user_data

