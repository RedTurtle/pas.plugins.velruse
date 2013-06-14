# -*- coding: utf-8 -*-

# For every possible user property we know which remote service is giving us data
# BBB twitter is not giving us fullname right now

#PROPERTIY_PROVIDERS_INFO = {
#        'fullname': ('linkedin.com', 'facebook.com', ),
#        'email': ('facebook.com', ),
#}

PROPERTY_PROVIDERS_INFO = {
    'facebook.com': ('email', 'fullname', ),
    'linkedin.com': ('fullname', 'email', ),
    'twitter.com': ('fullname', 'location', 'home_page', ),
    'accounts.google.com': ('email', 'fullname', ),
    }
