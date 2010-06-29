# -*- coding: utf-8 -*-
"""
    Template for a Controller

    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-05-23

    This controller introduces some of the basic features of Sahana
    it can be used as a template to build a controller for your own modules
"""

module = "template"

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

def disaster():
    "RESTful CRUD controller"
    return shn_rest_controller(module, "disaster" )

def geochat():
    import urllib2
    output = {}
    output["test"] = "Test"
    
    theurl = "http://geochat.instedd.org/api/groups/mkict/messages"
    gc_file = urllib2.urlopen(theurl)
    mkict = [ gc_file_line for gc_file_line in gc_file ]
    
    output["mkict"] = BEAUTIFY(mkict)
    
    return output

def geochat_auth():
        
    import urllib2
    import sys
    import re
    import base64
    from urlparse import urlparse
    
    output = dict(auth = "test")
    
    theurl = "http://geochat.instedd.org/api/users/michaelhowden/messages"
    # if you want to run this example you'll need to supply
    # a protected page with your username and password
    
    username = 'michaelhowden'
    password = 'dr3mike6'           
    
    req = urllib2.Request(theurl)
    try:
        handle = urllib2.urlopen(req)
    except IOError, e:
        # here we *want* to fail
        pass
    else:
        # If we don't fail then the page isn't protected
        output["result"] = "This page isn't protected by authentication."
        return output 
    
    if not hasattr(e, 'code') or e.code != 401:
        # we got an error - but not a 401 error
        output["result1"] = "This page isn't protected by authentication."
        output["result2"] = 'But we failed for another reason.'
        return output
    
    authline = e.headers['www-authenticate']
    # this gets the www-authenticate line from the headers
    # which has the authentication scheme and realm in it
        
    authobj = re.compile(
        r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
        re.IGNORECASE)
    # this regular expression is used to extract scheme and realm
    matchobj = authobj.match(authline)
    
    if not matchobj:
        # if the authline isn't matched by the regular expression
        # then something is wrong
        output["result1"] = 'The authentication header is badly formed.'
        output["result2"] = authline
        return output
    
        scheme = matchobj.group(1)
        realm = matchobj.group(2)
        # here we've extracted the scheme
        # and the realm from the header
        if scheme.lower() != 'basic':
            print 'This example only works with BASIC authentication.'
            sys.exit(1)
        
        base64string = base64.encodestring(
                        '%s:%s' % (username, password))[:-1]
        authheader =  "Basic %s" % base64string
        req.add_header("Authorization", authheader)
        try:
            handle = urllib2.urlopen(req)
        except IOError, e:
            # here we shouldn't fail if the username/password is right
            output["result"] =  "It looks like the username or password is wrong."
            return output
        thepage = handle.read()    
        
    return 
