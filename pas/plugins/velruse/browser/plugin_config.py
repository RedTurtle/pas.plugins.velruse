# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName


class VelrusePluginConfigView(BrowserView):
    """Config view"""

    def __call__(self):
        """
        """
        if self.request.form.get('form.button.Save', ''):
            errors = self.saveSettings()
            if errors:
                return self.index(errors=errors)
            else:
                return self.doReturn("Settings save", 'info')
        return self.index()

    def saveSettings(self):
        """
        """
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
        return_url = "%s/velruse-plugin-config" % self.context.absolute_url()
        self.request.RESPONSE.redirect(return_url)
