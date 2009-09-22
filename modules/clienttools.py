#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   Client tools for web2py 
   Developed by Nathan Freeze <nathan@freezable.com>
   License: GPL v2
   
   This file contains tools for managing client events 
   and resources from the server in web2py
"""

from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
import urllib
import os
import string

__all__ = ['PageManager','EventManager']

__events__ = ['blur', 'focus', 'load', 'resize', 'scroll', 'unload', 
                 'beforeunload', 'click', 'dblclick',  'mousedown', 
                 'mouseup', 'mousemove', 'mouseover', 'mouseout', 
                 'mouseenter', 'mouseleave', 'change', 'select',
                 'submit', 'keydown', 'keypress', 'keyup', 'error']

def valid_filename(filename):
    import string
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)

class PageManager(object):
    """
    The page manager object is used to dynamically
    include resources on a page
    
    include - downloads a resource and/or adds a 
              reference to it on the page              
    google_load - adds a reference to a google hosted library
                  example: page.google_load("jqueryui","1.7.2")
                  more here: http://code.google.com/apis/ajaxlibs/                  
    ready - adds a script to the jQuery(document).ready function    
    render - returns the page manager output for views    
    """
    def __init__(self, environment):
        self.environment = Storage(environment)        
        self.resources = []
        self.onready = []
    def include(self, path, download=False, overwrite=False, subfolder=None):       
        request = self.environment.request
        out = path        
        if hasattr(path, 'xml'):
            out = path.xml()
        if download and path.startswith("http://"):                     
            if not request.env.web2py_runtime_gae:                
                fname = valid_filename(path.split("/")[-1])
                if len(fname):                    
                    pieces = (request.folder, 'static', subfolder)
                    fld = os.path.join(*(x for x in pieces if x))
                    if not os.path.exists(fld): os.mkdir(fld)
                    fpath = os.path.join(fld,fname)
                    exists = os.path.exists(fpath)
                    if (not exists) or (exists and overwrite):            
                        urllib.urlretrieve(path, fpath)
                    out = URL(r=request,c='/'.join(
                          x for x in ['static', subfolder] if x),f=fname)                 
        self.resources.append(out)
    def google_load(self, lib, version):
        gsapi = '<script src="http://www.google.com/jsapi"></script>'
        if not gsapi in self.resources:
            self.include(gsapi)
        self.include('<script type="text/javascript">google.load("%s", "%s");</script>' % \
                      (lib,version))
    def ready(self, script):
        if isinstance(script, SCRIPT):
            self.onready.append(script.xml())
        elif isinstance(script, str):
            self.onready.append(script) 
        else:
            raise ValueError("Invalid script for ready function. Must be string or SCRIPT.")     
    def render(self):
        out = ''
        for r in self.resources:
            if r.endswith(".js"):
                out += "<script type=\"text/javascript\" src=\"%s\"></script>" % r
            elif r.endswith(".css"):
                out += LINK(_href=r,_rel="stylesheet", _type="text/css").xml()
            else:
                out += r
        if len(self.onready):
            inner = "\n  ".join(s for s in self.onready)
            out += "<script type=\"text/javascript\">function page_onready(){\n  " + \
             inner + "\n}\njQuery(document).ready(page_onready);</script>"         
        
        return XML(out)

class EventManager(object):
    """
    The event manager allows you to bind client
    side events to client or server side functions.
    
    example: div = DIV('Click me',_id="clickme")
             event.listen('click',div,handle_it, "alert('Clicked!');")
             event.listen('blur',"#test", handle_it, div)
             
    requires an instance of PageManager             
    """
    def __init__(self, page_manager):
        self.events = []
        self.page_manager = page_manager
        self.environment = page_manager.environment        
    def listen(self, event, helper, handler, success="eval(msg);", 
               data='form:first', args=None, persist=False, event_args=False):        
        act_on = 'document'      
        use_jq = isinstance(helper,str)
        bind = 'live' if persist else 'bind'        
        if not event in __events__:            
            raise ValueError('Invalid event name.')        
        if not use_jq:
            if not hasattr(helper,'xml'):
                raise TypeError("Invalid helper for event.")
            if not helper['_id']:
                raise ValueError('Invalid helper for event. Component has no ID attribute.')
            if helper:
                act_on = '"#%s"' % helper['_id']
        if use_jq and helper != 'document':
            act_on = '"' + helper + '"'
        if hasattr(success,'xml'):
            if success['_id']:
                success = 'jQuery("#%s").html(msg);' % success['_id']
            else:
                raise ValueError('Invalid success component for event. No ID attribute found.')
        elif success != "eval(msg);":
            success = 'jQuery("%s").html(msg);' % success             
        if not isinstance(handler, str):        
            if not hasattr(handler, '__call__'):
                raise TypeError('Invalid handler for event. Object is not callable')
            url = URL(r=self.environment.request,f=handler.__name__, args=args) \
                  if args else URL(r=self.environment.request,f=handler.__name__)
            e = '"event_target_id=" + encodeURIComponent(e.target.id) + "&event_target_html=" + '\
                'encodeURIComponent(jQuery(e.target).wrap("<div></div>").parent().html()) + '\
                '"&event_pageX=" + e.pageX + "&event_pageY=" + e.pageY + '\
                '"&event_timeStamp=" + e.timeStamp + "&"' if event_args else '""'
            handler = 'jQuery.ajax({type:"POST",url:"%s",data:%s + jQuery("%s").serialize(),'\
                      'success: function(msg){%s} });'  % (url, e, data, success)                   
        self.events.append([event, helper, handler, data])        
        self.page_manager.onready.append('jQuery(%s).%s("%s", function(e){%s});' % 
                                         (act_on, bind, event, handler))
        
