# -*- coding: utf-8 -*-

# For every possible user property we know which remote service is giving us data
# BBB twitter is not giving us fullname right now

#PROPERTIY_PROVIDERS_INFO = {
#        'fullname': ('linkedin.com', 'facebook.com', ),
#        'email': ('facebook.com', ),
#}

PROPERTIY_PROVIDERS_INFO = {
    'facebook.com': ('email', 'fullname', ),
    'linkedin.com': ('fullname', ),
    'twitter.com': ('fullname', 'location', 'home_page', ),
    'google.com': ('email', 'fullname', ),
    }
