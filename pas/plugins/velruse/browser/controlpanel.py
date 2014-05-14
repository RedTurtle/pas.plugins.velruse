# -*- coding: utf-8 -*-

from Products.statusmessages.interfaces import IStatusMessage
from plone.app.registry.browser import controlpanel
from z3c.form.browser.checkbox import SingleCheckBoxFieldWidget
from z3c.form import button
from pas.plugins.velruse import _
from pas.plugins.velruse.interfaces import IVelruseGeneralSettings
from pas.plugins.velruse.interfaces import IVelrusePlugin
from Products.CMFCore.utils import getToolByName

class VelruseSettingsForm(controlpanel.RegistryEditForm):

    #fields = field.Fields(IVelruseGeneralSettings)

    schema = IVelruseGeneralSettings
    id = "VelruseSettingsEditForm"
    label = _(u"Velruse integration settings")
    description = _(u"help_velruse_settings_form",
                    default=u"Configure how Plone talk with Velruse backend")

    def updateWidgets(self):
        super(VelruseSettingsForm, self).updateWidgets()
        self.widgets['connection_timeout'].size = 4
        for widget in self.widgets['activated_plugins'].widgets:
            widget.style = u'width: 100%';
            widget.klass = u' velruseData';

    def updateFields(self):
        super(VelruseSettingsForm, self).updateFields()
        self.fields['site_login_enabled'].widgetFactory = SingleCheckBoxFieldWidget

    @button.buttonAndHandler(_('Save'), name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"),
                                                      "info")
        self.context.REQUEST.RESPONSE.redirect("@@velruse-settings")

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"),
                                                      "info")
        self.request.response.redirect("%s/%s" % (self.context.absolute_url(),
                                                  self.control_panel_view))

class VelruseSettingsFormView(controlpanel.ControlPanelFormWrapper):
    form = VelruseSettingsForm
    #index = ViewPageTemplateFile('controlpanel.pt')
    
    def velruse_plugins(self):
        acl_users = getToolByName(self.context, 'acl_users')
        return [plugin for plugin in acl_users.objectValues() if IVelrusePlugin.providedBy(plugin)]

