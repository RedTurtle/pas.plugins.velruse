# -*- coding: utf-8 -*-
"""
Get rid of this as soon as we drop Plone 3/PYthon 2.4 support

More or less, we are providing the most basic python-requests feature we need
"""

import simplejson as json
import urllib
import urllib2
import socket


class Response(object):
    """Try to do my best to simulate python-request object"""
    def __init__(self):
        self.status_code = 200
        self.body = None

    @property
    def content(self):
        """See http://www.python-requests.org/en/latest/api/#requests.Response.content"""
        return self.body

    def json(self):
        """See http://www.python-requests.org/en/latest/api/#requests.Response.json"""
        return json.loads(self.body)


def get(url, params={}, timeout=0):
    """See http://www.python-requests.org/en/latest/api/#requests.get"""
    if params:
        params = '?' + urllib.urlencode(params)
    old_timeout = socket.getdefaulttimeout()
    if timeout:
        socket.setdefaulttimeout(timeout)

    r = Response()
    try:
        resp = urllib2.urlopen(url + (params and params or ''))
    except urllib2.URLError, e:
        r.status_code = e.code
    else:
        # 200
        r.body = resp.read()

    if timeout:
        socket.setdefaulttimeout(old_timeout)

    return r
