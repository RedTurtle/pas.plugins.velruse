# -*- coding: utf-8 -*-

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from pas.plugins.velruse import _
from DateTime import DateTime


class VelrusePluginConfigView(BrowserView):
    """Config view"""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self._results = []
        request.set('disable_border', True)

    def __call__(self):
        form = self.request.form
        if form.get('form.button.Save', ''):
            errors = self.saveSettings()
            if errors:
                return self.index(errors=errors)
            else:
                return self.doReturn(_("Settings saved"), 'info')
        elif form.get('apply'):
            self.apply_changes(form.get('user', []))
        elif form.get('remove'):
            self.clean_blacklist(form.get('remove_from_blacklist', []))
        elif form.get('form.submitted'):
            self._search()
        return self.index()

    def apply_changes(self, users):
        delete_count = 0
        storage = self.context._storage
        blstorage = self.context._blacklist
        for user in users:
            if user.get('delete'):
                try:
                    del storage[user.get('id')]
                    delete_count += 1
                except KeyError:
                    pass
            if user.get('blacklist'):
                blstorage[user.get('id')] = DateTime()
            else:
                try:
                    del blstorage[user.get('id')]
                except KeyError:
                    pass
        if delete_count>0:
            ptool = getToolByName(self.context, 'plone_utils')
            ptool.addPortalMessage(_('users_delete_message',
                                     default="$count users deleted",
                                     mapping={'count': delete_count}))

    def _blacklistUsers(self, user_ids):
        """Add a set of user ids to blacklist"""
        storage = self.context._blacklist
        for userid in user_ids:
            storage[userid] = DateTime()

    def is_blacklisted(self, userid):
        storage = self.context._blacklist
        return userid in storage     

    def _search(self):
        query = self.request.form.get('query')
        context = self.context
        acl_users = getToolByName(context, 'acl_users')
        if self.request.form.get('userid') and self.request.form.get('exact_match'):
            self._results = [u for u in acl_users.searchUsers(id=self.request.form.get('userid'), exact_match=True) if u.get('plugin_id')==self.context.getId()]
        else:
            self._results = [u for u in acl_users.searchUsers(fullname=query) if u.get('plugin_id')==self.context.getId()]
        
    def search_results(self):
        return self._results

    def load_blacklist(self):
        return self.context._blacklist.keys()

    def clean_blacklist(self, ids):
        storage = self.context._blacklist
        for id in ids:
            try:
                del storage[id]
            except KeyError:
                pass

    def saveSettings(self):
        errors = {}
        velruse_server_host = self.request.form.get('velruse_server_host', "")
        velruse_auth_info_path = self.request.form.get('velruse_auth_info_path', "")
        if not velruse_server_host:
            errors['velruse_server_host'] = True
        if not velruse_auth_info_path:
            errors['velruse_auth_info_path'] = True
        if errors:
            return errors
        self.context.velruse_server_host = velruse_server_host
        self.context.velruse_auth_info_path = velruse_auth_info_path
        self.context.given_roles = self.request.form.get('given_roles', [])
        return errors

    def doReturn(self, message, type):
        pu = getToolByName(self.context, "plone_utils")
        pu.addPortalMessage(message, type=type)
        return_url = "%s/@@velruse-plugin-config" % self.context.absolute_url()
        self.request.RESPONSE.redirect(return_url)
