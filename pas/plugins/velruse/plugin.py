# -*- coding: utf-8 -*-

# Remove as soon as possible
try:
    import requests
    from requests.exceptions import Timeout
except ImportError:
    from pas.plugins.velruse import fallback_requests as requests
    from pas.plugins.velruse.fallback_requests import Timeout

try:
    from Products.PlonePAS.utils import scale_image
except ImportError:
    from Products.CMFPlone.utils import scale_image

import posixpath
import urlparse
import re
import sys

from BTrees.OOBTree import OOBTree
from AccessControl import ClassSecurityInfo
from OFS.Image import Image
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.PlonePAS.interfaces.plugins import IUserIntrospection
from Products.PlonePAS.plugins.property import ZODBMutablePropertyProvider
from Products.PlonePAS.sheet import MutablePropertySheet
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import IExtractionPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PluggableAuthService.interfaces.plugins import IRolesPlugin
from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
from StringIO import StringIO
from ZODB.POSException import ConflictError
from pas.plugins.velruse import config
from pas.plugins.velruse import logger
from pas.plugins.velruse.events import VelruseFirstLoginEvent
from pas.plugins.velruse.interfaces import IVelrusePlugin
from pas.plugins.velruse.interfaces import IVelruseGeneralSettings
from zope.event import notify
from zope.interface import implements
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry


if sys.version_info < (2, 6):
    PLONE4 = False
else:
    PLONE4 = True 

SEARCH_PATTERN_STR = r"\s*%s"

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
            return
        return self.index()


class VelruseMutablePropertySheet(MutablePropertySheet):
    """An IMutablePropertySheet implementation but check writeable field taken from Velruse"""
    
    def canWriteProperty(self, object, id):
        """
        Check if a property can be modified.
        
        Properties take from Velruse can't be changed
        """
        for provider, given_properties in config.PROPERTY_PROVIDERS_INFO.items():
            if object.getId().startswith("%s." % provider) and id in given_properties:
                return False
        return True


class VelruseUsers(ZODBMutablePropertyProvider):
    """
    PAS Plugin for Velruse authentication. It's more or less a basic
    ZODBMutablePropertyProvider with additional features
    """
    
    # List PAS interfaces we implement here
    implements(
            IVelrusePlugin,
            IExtractionPlugin,
            IAuthenticationPlugin,
            IPropertiesPlugin,
            IUserEnumerationPlugin,
            IRolesPlugin,
            IUserIntrospection,
        )
    
    security = ClassSecurityInfo()
    
    #_dont_swallow_my_exceptions = True
    
    def __init__(self, id, title=None):
        super(VelruseUsers, self).__init__(id, title)
        self.__name__ = self.id = id
        self.title = title
        self.manage_addProperty('velruse_server_host', '127.0.0.1:5020', 'string')
        self.manage_addProperty('velruse_auth_info_path', '/velruse/auth_info', 'string')
        self.manage_addProperty('given_roles', ['Member',], 'lines')
        self._blacklist = OOBTree()

    security.declarePrivate('getRolesForPrincipal')
    def getRolesForPrincipal(self, principal, request=None):

        """ principal -> ( role_1, ... role_N )

        o Return a sequence of role names which the principal has.

        o May assign roles based on values in the REQUEST object, if present.
        """
        if self._storage.get(principal.getId()) and not self._blacklist.get(principal.getId()):
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
        try:
            r = requests.get('http://%s%s' % (velruse_host, velruse_auth_info),
                         params={'format': 'json',
                                 'token': credentials.get('velruse-token')},
                         timeout=self.getConnectionTimeout())
        except Timeout:
            logger.error("Can't connect to Velruse backend. Timeout.")
            return None
        if r.status_code >= 300:
            logger.error("Can't connect to Velruse backend. Code %s" % r.status_code)
            return None
        raw_user_data = r.json()
        user_data = self._format_user_data(raw_user_data)
        if user_data.get('userid'):
            acl_users = getToolByName(self, 'acl_users')
            userid = user_data.get('userid').encode('utf-8')
            username = user_data.get('username').encode('utf-8')
            if self._blacklist.get(userid):
                logger.warning("User %s is blacklisted" % (userid))
                return None
            if not self._storage.get(userid):
                # userdata not existing: this is the first time we enter here
                if PLONE4:
                    acl_users.session._setupSession(userid, self.REQUEST.RESPONSE)
                else:
                    acl_users.session.setupSession(userid, self.REQUEST.RESPONSE)
                self._storage.insert(userid, user_data)
                new_user = self.acl_users.getUserById(userid)
                if new_user:
                    self.REQUEST.set('first_user_login', userid)
                    notify(VelruseFirstLoginEvent(new_user))
            else:
                if PLONE4:
                    acl_users.session._setupSession(userid, self.REQUEST.RESPONSE)
                else:
                    acl_users.session.setupSession(userid, self.REQUEST.RESPONSE)
                # we store the user info EVERY TIME because data from social network can be changed meanwhile
                # but we need to take care of not overriding other Plone-only user's information
                existing_user_data = self._storage[userid]
                existing_user_data.update(user_data)
                self._storage[userid] = existing_user_data
                new_user = self.acl_users.getUserById(userid)
            if not new_user:
                logger.error("Can't authenticate with userid %s (%s)" % (userid, username))
                return None
            return (userid, username)
        else:
            logger.error("Invalid token %s > %r" % (credentials.get('velruse-token'), raw_user_data))

    def getConnectionTimeout(self):
        """
        o Return a connection timeout for velruse call.
        o Timeout is set in velruse_settings.
        """
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IVelruseGeneralSettings, check=False)
        if settings and settings.connection_timeout:
            return settings.connection_timeout
        return 10

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
        id = id or login
        if self._storage.get(id):
            return ({'id': id,
                    'login': id,
                    'plugin_id': self.getId()},)
        results = []
        # Panic! Very slow
        if not kw and not id:
            for userid, user_data in self._storage.items():
                results.append({'id': userid, 
                                'login': userid,
                                'plugin_id': self.getId(),
                                'email': user_data.get('email'),
                                'title': user_data.get('fullname'),
                                })
        elif set(kw.keys()) & set(('fullname', 'email',)):
            for userid, user_data in self._storage.items():
                # BBB potentially very slow
                if not user_data.get('fullname') and not user_data.get('email'):
                    continue
                if re.search(SEARCH_PATTERN_STR % kw.get('fullname'), user_data.get('fullname'), re.I) or \
                        re.search(SEARCH_PATTERN_STR % kw.get('email'), user_data.get('email'), re.I):
                    results.append({'id': userid,
                                    'login': userid,
                                    'plugin_id': self.getId(),
                                    'email': user_data.get('email'),
                                    'title': user_data.get('fullname'),
                                    })
        return tuple(results)

    security.declarePrivate('setPropertiesForUser')
    def setPropertiesForUser(self, user, propertysheet):
        """Set properties in the current plugin only if they are not originally read from Velruse"""
        properties = dict(propertysheet.propertyItems())
        for provider, given_properties in config.PROPERTY_PROVIDERS_INFO.items():
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

    security.declarePrivate('getPropertiesForUser')
    def getPropertiesForUser(self, user, request=None):
        """Get property values for a user or group.
        Returns a dictionary of values or a PropertySheet.

        This implementation will always return a MutablePropertySheet.

        NOTE: Must always return something, or else the property sheet
        won't get created and this will screw up portal_memberdata.
        """
        for provider, given_properties in config.PROPERTY_PROVIDERS_INFO.items():
            if user.getId().startswith("%s." % provider):
                # Code taken from base getPropertiesForUser method
                isGroup = getattr(user, 'isGroup', lambda: None)()
        
                data = self._storage.get(user.getId())
                defaults = self._getDefaultValues(isGroup)
                # provide default values where missing
                if not data:
                    data = {}
                for key, val in defaults.items():
                    if not key in data:
                        data[key] = val
        
                return VelruseMutablePropertySheet(self.id,
                                                   schema=self._getSchema(isGroup), **data)

    def _format_user_data(self, raw_data):
        """
        Velruse return data in a Portable Contact format but different plugins can return or not
        informations
        """
        user_data = {}
        userid_data = raw_data.get('profile', {}).get('accounts', [None])[0]
        userid = ("%s.%s" % (userid_data.get('domain', ''),
                             userid_data.get('userid', None))).encode('utf-8')
        user_data['userid'] = userid
        username = userid_data.get('username', None)
        if not username:
            username = userid
        else:
            username = ("%s.%s" % (userid_data.get('domain', ''),
                                   username)).encode('utf-8')
        user_data['username'] = username
        for provider, given_properties in config.PROPERTY_PROVIDERS_INFO.items():
            if username.startswith("%s." % provider):
                for property_id in [p for p in given_properties]:
                    if property_id == 'email' and raw_data.get('profile', {}).get('emails', []):
                        # BBB: seems that commonly email (up) is stored as string
                        user_data['email'] = raw_data.get('profile', {}).get('emails', [])[0]['value'].encode('utf-8')
                    if property_id == 'fullname':
                        user_data['fullname'] = raw_data.get('profile', {}).get('name', {}).get('formatted', '') or \
                                raw_data.get('profile', {}).get('displayName', {})
                    if property_id == "addresses" and raw_data.get('profile', {}).get('addresses', []):
                        user_data['location'] = raw_data.get('profile', {}).get('addresses', [])[0].get('formatted', '')
                    if property_id == "home_page" and raw_data.get('profile', {}).get('urls', []):
                        user_data['home_page'] = raw_data.get('profile', {}).get('urls', [])[0].get('value', '')
        # profile's photo
        if raw_data.get('profile', {}).get('photos', []):
            photo_url = raw_data.get('profile', {}).get('photos', [])[0].get('value', '')
            r = requests.get(photo_url)
            #path = urlparse.urlsplit(photo_url).path # only with Python 2.5+
            path = urlparse.urlsplit(photo_url)[2]
            filename = posixpath.basename(path)
            portrait = TempPortrait(filename, r.content)
            # getToolByName(self, 'portal_membership').changeMemberPortrait(portrait, username)
            try:
                self._changePortraitFor(portrait, userid)
            except ConflictError:
                raise
            except Exception, inst:
                logger.error("Can't change portrait for %s: %s" % (username, str(inst)))
        return user_data

    security.declarePrivate('_changePortrait')
    def _changePortraitFor(self, portrait, username):
        """
        Like getToolByName(self, 'portal_membership').changeMemberPortrait(portrait, username),
        that is not working anymore after the PloneHotfix20130618
        """
        portal_membership = getToolByName(self, 'portal_membership')
        safe_id = portal_membership._getSafeMemberId(username)
        if portrait and portrait.filename:
            scaled, mimetype = scale_image(portrait)
            portrait = Image(id=safe_id, file=scaled, title='')
            membertool = getToolByName(self, 'portal_memberdata')
            membertool._setPortrait(portrait, safe_id)

    security.declarePrivate('getUserIds')
    def getUserIds(self):
        """
        Return a list of user ids
        """
        for u in self._storage.items():
            yield u[0]

    security.declarePrivate('getUserNames')
    def getUserNames(self):
        """
        Return a list of usernames
        """
        for u in self.getUserIds():
            yield u

    security.declarePrivate('getUsers')
    def getUsers(self):
        """
        Return a list of users
        """
        acl_users = getToolByName(self, 'acl_users')
        for u in self._storage.items():
            yield acl_users.getUserById(u[0])

