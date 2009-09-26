#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   Client tools for web2py 
   Developed by Nathan Freeze <nathan@freezable.com>
   License: GPL v2
   
   This file contains tools for managing client events 
   and resources from the server in web2py
"""

import urllib
import os
import string
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
import gluon.contrib.simplejson as json

__all__ = ['PageManager','EventManager', 'ScriptManager', 'JQuery']

__events__ = ['blur', 'focus', 'load', 'resize', 'scroll', 'unload', 
                 'beforeunload', 'click', 'dblclick',  'mousedown', 
                 'mouseup', 'mousemove', 'mouseover', 'mouseout', 
                 'mouseenter', 'mouseleave', 'change', 'select',
                 'submit', 'keydown', 'keypress', 'keyup', 'error']

__scripts__ = ['alert','delay','confirm','timer','stop_timer','call_function']

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
        
class ScriptManager(object):
    """
    Helpers to generate scripts
    All methods return a string
              
    example: page = PageManager(globals())
             scripts = Scripts(page)
             page.ready(scripts.call_function(function, data, success))
    """
    def __init__(self, page_manager):
        self.page_manager = page_manager
        self.environment = page_manager.environment
        
    def alert(self,message):
        return 'alert("%s");' % message
    
    def confirm(self,message, if_ok, if_cancel=''):
        return 'var c = confirm("%s");if(c==true){%s}else{%s}' % \
               (message, if_ok, if_cancel)
    
    def delay(self, function, timeout):
        return 'setTimeout(\'%s\',%s);' % (function,timeout)
        
    def timer(self, function, interval=10000, append_to="form:first"):
        return 'var timer_id = setInterval(\'%s\',%s);jQuery("%s").'\
               'append("<input name=\'timer_id\' type=\'hidden\' value=\'" + timer_id + "\'/>");' % \
                (function, interval, append_to)
                
    def stop_timer(self, timer_id):
        return 'clearTimeout(%s);jQuery("input[name=\'timer_id\']").remove();' % timer_id 
    
    def call_function(self, function, data="form:first", success="eval(msg);", args=None):
        url = function
        if hasattr(success,'xml'):
            if success['_id']:
                success = 'jQuery("#%s").html(msg);' % success['_id']
            else:
                raise ValueError('Invalid success component for event. No ID attribute found.')
        elif success != "eval(msg);":
            success = 'jQuery("%s").html(msg);' % success             
        if not isinstance(function, str):        
            if not hasattr(function, '__call__'):
                raise TypeError('Invalid function. Object is not callable')
            url = URL(r=self.environment.request,f=function.__name__, args=args) \
                  if args else URL(r=self.environment.request,f=function.__name__)
        return 'jQuery.ajax({type:"POST",url:"%s",data: jQuery("%s").serialize(),'\
                      'success: function(msg){%s} });'  % (url, data, success)    
    
class JQuery:
    def __init__(self,name,attr=None,*args):
        self.name=name
        self.attr=attr
        self.args=args
    def __str__(self):
        import gluon.contrib.simplejson as json
        def encode(obj):
            if isinstance(obj,JQuery): return str(obj)
            return json.dumps(obj)
        if not self.attr:
            return ('jQuery("%s")' % self.name).replace('"this"',"this").replace('"document"',"document")        
        args=', '.join([encode(a) for a in self.args])
        return '%s.%s(%s)' % (self.name, self.attr, args)
    def __repr__(self):
        return str(self)
    def xml(self):
        raise AttributeError
    def __getattr__(self,attr):
        def f(*args):
            return JQuery(self,attr,*args)
        return f
    def __call__(self,*args):
        if not args:
            jq = str(JQuery(self))       
            jq = jq[8:-2]
            return jq + ";"
    def __add__(self,other):
        return str(self)+str(other)    

    
