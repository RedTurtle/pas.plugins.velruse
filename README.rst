A PAS plugin for Plone that **authenticate users from social networks** through the use of **Velruse**.

.. contents::

Introduction
============

This Plone plugin let you to enable authentication of social networks users in Plone sites, using `Velruse`__.

__ http://velruse.readthedocs.org/

Velruse is a Pyramid application so defined:

    Velruse is a set of authentication routines that provide a **unified way** to have a website user authenticate to a
    variety of different identity providers and/or a variety of different authentication schemes.
    
    It is similar in some ways to `Janrain Engage`__ with the exception of being **open-source**, **locally installable**,
    and **easily pluggable** for custom identity providers and authentication schemes.

    __ http://www.janrain.com/products/engage
    
    -- from Velruse documentation

Why use Velruse instead of RPX service?
---------------------------------------

Plone ecosystem already have at least one plugin for a general social authentication: `plonesocial.auth.rpx`__. But in some
environments (for example: public company or whatever use case where the user's privacy follow strict rules) this
kind of service can't be used.

__ http://comlounge.net/rpx/

Privacy apart, Velruse is **open source* and **easilly pluggable**: you can provide authentication providers for new services
not covered by Janrain.

Check also this `Velruse presentation`__ for more.

__ http://www.slideshare.net/amleczko/lost-in-o-auth-learn-velruse-and-get-your-life-back

How to Use
==========

Installing Velruse
------------------

Velruse is a `Pyramid`__ application so you must follow the proper `installation instruction`__ the refer to the
`Velruse setup guide`__.

__ http://www.pylonsproject.org/projects/pyramid/about
__ http://docs.pylonsproject.org/projects/pyramid/en/1.4-branch/narr/install.html
__ http://velruse.readthedocs.org/en/latest/usage.html

Velruse can be executed as a separate *Pyramid service* and the Plone plugin needs this configuration.
It will talk to Velruse using HTTP requests.

**TODO**: recent Zope version can be executed in the WSGI stack. Maybe future version of the plugin would support
also this alternative way? Who knows.

Installing pas.plugins.velruse
------------------------------

Just add ``pas.plugins.velruse`` to your buildout configuration and re-run it.

.. code:: ini

    [instance]
    recipe = plone.recipe.zope2instance
    
    ...
    
    eggs =
        ...
        pas.plugins.velruse

After Plone restart, add "**Velruse authentication plugin**" product to you Plone site.

Configuring pas.plugins.velruse
-------------------------------

All configuration are done through the "*Velruse integration settings*" configuration, from the Plone
control panel.

General site settings
~~~~~~~~~~~~~~~~~~~~~

The first section is for configuration that globally controls how Plone talk to Velruse, and other user interface
options.

**Site login enabled**
    If you want to keep enabled the standard Plone site login form or not.
**Authentication services enabled**
    A configuration list of available Velruse backends. See below.
**Connection timeout**
    A timeout value for connection to velruse server.

The "*Authentication services enabled*" configuration is composed by a set of triplets:

**Name**
    (optional) A descriptive name of the remote service. For example: "Facebook".
**URL or path**
    (mandatory) URL or path to the running Velruse service. Please note: this must be a public URL the user must
    able to access. This is not really mandatory, but if not provided the login method is not displayed in the login form.
**Icon**
    (optional) URL or path for an icon that can recall the service logo.
    
    Default CSS implementation is for 64x64px images.

URLs above can be absolute ("http://auth.yourservice.com/login/facebook") or relative to the portal root URL by
using a starting slash ("/velruse/login/facebook"). The latter will help you keeping Plone and Velruse behind Apache.

Those information are used to properly configure the new login form.

.. image:: http://blog.redturtle.it/pypi-images/pas.plugins.velruse/pas.plugins.velruse-0.1a1-01.png/image_large
   :alt: New login form
   :target: http://blog.redturtle.it/pypi-images/pas.plugins.velruse/pas.plugins.velruse-0.1a1-01.png

PAS plugins configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

The other configuration section is relative the Velruse PAS plugin(s).

**Velruse server host** 
    The hostname of the Pyramid Velruse service. For example: ``127.0.0.1:8080`` if Velruse run on the same
    server of Plone.
**Velruse auth info path**
    The configured Pyramid route for calling **auth_info**. Default is ``/velruse/auth_info``.
    
    Keep in mind this warning taken from official Velruse documentation:
    
        The ``/auth_info`` URL should be considered sensitive and only trusted services should be allowed access.
        If an attacker intercepts a an authentication token, they could potentially query /auth_info and learn all of
        the credentials for the user.

**User roles**
    Set of default roles automatically given to users that perform authentication with the Velruse plugin.
    Default to "*Members*" only.

Plus, you have two additional forms: "*Users management*" and "*Blacklist management*" to manage user's data
inside the plugin. You can delete data or enableadd the user to the **blacklist**.
Blacklisted users can't authenticate anymore.

Data read by Plone from Velruse
-------------------------------

Right now only Twitter, Facebook, Linkedin and Google+ are automatically configured:

* from Twitter: fullname, location, personal home page and portrait
  (no e-mail can be read)
* from Facebook: fullname, e-mail and portrait
* from Linkedin: fullname, e-mail and portrait
  (must properly configure the Linkedin API)
* from Google: fullname and e-mail

But Velruse support *a lot* of additional providers; if you want to enable more
(this is true also for custom providers) you must configure the plugin, setting what data try to read
by changing a configuration variable.

.. code:: python

    from pas.plugins.velruse.config import PROPERTY_PROVIDERS_INFO
    PROPERTY_PROVIDERS_INFO['yourmagicnewprovider'] = ('fullname', 'email', 'description')

**TODO**: this will probably change in future, maybe replaced by a blacklist of property you *don't* want to read, or
something configurable TTW.

Requirements
============

Tested with:

* Plone 3.3
* Plone 4.2
* Plone 4.3

All using Velruse 1.1.

Credits
=======

Developed with the support of `Regione Emilia Romagna`__;
Regione Emilia Romagna supports the `PloneGov initiative`__.

__ http://www.regione.emilia-romagna.it/
__ http://www.plonegov.it/

Authors
=======

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.it/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.it/

Special thanks to `Mauro Amico`__ and `Ben Bangert`__ (for accepting a couple of mine pull requests).

__ https://github.com/mamico
__ https://github.com/bbangert
