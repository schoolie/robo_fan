#!/usr/bin/python

import urllib.request 

class ipCam(object):
        
    def __init__(self,
            base_url='http://24.28.2.107:81/media',
            url_args='?action=snapshot',
            user='admin',
            pwd='Amanda09',
            ):
        
        self.base_url = base_url
        self.url = base_url + '/' + url_args

        # create a password manager
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

        # Add the username and password.
        # If we knew the realm, we could use it instead of None.
        password_mgr.add_password(None, base_url, user, pwd)

        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

        # create "opener" (OpenerDirector instance)
        opener = urllib.request.build_opener(handler)

        # Install the opener.
        # Now all calls to urllib.request.urlopen use our opener.
        urllib.request.install_opener(opener)
