# -*- coding: utf-8 -*-

from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements
from zope.event import notify

from StringIO import StringIO

import requests
import posixpath
import urlparse 

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin

from Products.PlonePAS.plugins.property import ZODBMutablePropertyProvider

from pas.plugins.velruse import config
from pas.plugins.velruse.interfaces import IVelrusePlugin
from pas.plugins.velruse.events import VelruseFirstLoginEvent


class TempPortrait(StringIO):
    
    def __init__(self, filename, content):
        self.filename = filename
        StringIO.__init__(self, content) 


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


class VelruseUsers(ZODBMutablePropertyProvider):
    """
    PAS Plugin for Velruse authentication. It's more or less a basic
    ZODBMutablePropertyProvider with additional features
    """
    
    # List PAS interfaces we implement here
    implements(
            IVelrusePlugin,
            IExtractionPlugin,
#            ICredentialsResetPlugin,
            IAuthenticationPlugin,
            IPropertiesPlugin,
            IUserEnumerationPlugin,
#            IUserFactoryPlugin,
            IRolesPlugin,
        )
    
    security = ClassSecurityInfo()
    
    def __init__(self, id, title=None):
        super(VelruseUsers, self).__init__(id, title)
        self.__name__ = self.id = id
        self.title = title
        self.manage_addProperty('velruse_server_host', '127.0.0.1:5020', 'string')
        self.manage_addProperty('velruse_auth_info_path', '/velruse/auth_info', 'string')
        self.manage_addProperty('given_roles', ['Member',], 'lines')
        #self._storage = OOBTree()

    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None ):

        """ principal -> ( role_1, ... role_N )

        o Return a sequence of role names which the principal has.

        o May assign roles based on values in the REQUEST object, if present.
        """
        if self._storage.get(principal.getId()):
            return tuple(self.getProperty('given_roles'))
        return ()

    security.declarePrivate('extractCredentials')
    def extractCredentials(self, request):
        """ request -> {...}

        o Return a mapping of any derived credentials.

        o Return an empty mapping to indicate that the plugin found no
          appropriate credentials.
        """
        if request.form.get('token'):
            return {'velruse-token': request.form.get('token')}
        return {}

    security.declarePrivate('authenticateCredentials')
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
            if not self._storage.get(user_data.get('username')):
                self._storage.insert(user_data.get('username'), user_data)
                new_user = self.acl_users.getUserById(user_data.get('username'))
                notify(VelruseFirstLoginEvent(new_user))
            else:
                # we store the user info EVERY TIME because data from social network can be changed meanwhile
                self._storage.insert(user_data.get('username'), user_data)
            return (username, username)

    security.declarePrivate('enumerateUsers')
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
        if self._storage.get(id):
            return [{'id': id,
                    'login': id,
                    'plugin_id': self.getId()}]
        return ()

#    security.declarePrivate('setPropertiesForUser')
#    def setPropertiesForUser(self, user, propertysheet):
#        """Set properties in the current plugin only if they are not originally read from Velruse"""
#        properties = dict(propertysheet.propertyItems())
#        for property_id in [p for p in properties.keys() if p in config.PROPERTIY_PROVIDERS_INFO.keys()]:
#            for provider in config.PROPERTIY_PROVIDERS_INFO[property_id]:
#                if user.getId().startswith("%s." % provider) and property_id in propertysheet._properties.keys():
#                    # Do not change this value!
#                    del propertysheet._properties[property_id]
#                    # now the _schema, that is a readonly attribute :(
#                    new_schema = []
#                    for pid, pt in propertysheet._schema:
#                        if pid==property_id:
#                            continue
#                        new_schema.append( (pid, pt) )
#                    propertysheet._schema = tuple(new_schema)
#        super(VelruseUsers, self).setPropertiesForUser(user, propertysheet)

    security.declarePrivate('setPropertiesForUser')
    def setPropertiesForUser(self, user, propertysheet):
        """Set properties in the current plugin only if they are not originally read from Velruse"""
        properties = dict(propertysheet.propertyItems())
        for provider, given_properties in config.PROPERTIY_PROVIDERS_INFO.items():
            if user.getId().startswith("%s." % provider):
                for property_id in [p for p in given_properties if p in properties.keys()]:
                    del propertysheet._properties[property_id]
                    # the _schema, that is a readonly attribute :(
                    new_schema = []
                    for pid, pt in propertysheet._schema:
                        if pid==property_id:
                            continue
                        new_schema.append( (pid, pt) )
                    propertysheet._schema = tuple(new_schema)
                super(VelruseUsers, self).setPropertiesForUser(user, propertysheet)

    def _format_user_data(self, raw_data):
        """
        Velruse return data in a Portable Contact format but different plugins can return or not
        informations
        """
        user_data = {}
        userid_data = raw_data.get('profile', {}).get('accounts', [None])[0]
        username = ("%s.%s" % (userid_data.get('domain', None),
                              userid_data.get('userid', None))).encode('utf-8')
        user_data['username'] = username
        if raw_data.get('profile', {}).get('emails', []):
            # BBB: seems that commonly email (up) is stored as string
            user_data['email'] = raw_data.get('profile', {}).get('emails', [])[0]['value'].encode('utf-8')
        user_data['fullname'] = raw_data.get('profile', {}).get('name', {}).get('formatted', '') or \
                    raw_data.get('profile', {}).get('displayName', {})
        if raw_data.get('profile', {}).get('addresses', []):
            user_data['location'] = raw_data.get('profile', {}).get('addresses', [])[0].get('formatted', '')
        if raw_data.get('profile', {}).get('urls', []):
            user_data['home_page'] = raw_data.get('profile', {}).get('urls', [])[0].get('value', '')
        # profile's photo
        if raw_data.get('profile', {}).get('photos', []):
            photo_url = raw_data.get('profile', {}).get('photos', [])[0].get('value', '')
            r = requests.get(photo_url)
            path = urlparse.urlsplit(photo_url).path
            filename = posixpath.basename(path)
            portrait = TempPortrait(filename, r.content)
            getToolByName(self, 'portal_membership').changeMemberPortrait(portrait, username)            
        return user_data

