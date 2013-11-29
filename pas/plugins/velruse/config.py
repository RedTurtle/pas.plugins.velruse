# -*- coding: utf-8 -*-

PLUGIN_ID = "velruse_users"

# For every possible user property we know which remote service is giving us data
# BBB: in future a black list will be probably better

PROPERTY_PROVIDERS_INFO = {
    'facebook.com': ('fullname', 'email', ),
    'linkedin.com': ('fullname', 'email', ),
    'twitter.com': ('fullname', 'location', 'home_page', ),
    'accounts.google.com': ('fullname', 'email', ),
    }
