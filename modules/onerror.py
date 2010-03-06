# -*- coding: utf-8 -*-
# Error handling model - as per http://trac.sahanapy.org/wiki/Haiti#ToDo
#   based on http://web2py.com/AlterEgo/default/show/75

# Usage - 
#   in a controller / model - import onerror function from onerror model
#   import help (http://groups.google.com/group/web2py/browse_thread/thread/f33921cada42b424/de2824a475967ac7?lnk=raot)
# @onerror
# def index:

from gluon.http import *
from gluon.html import *

def onerror(function):
  def __onerror__(*a,**b):
    try:
        return function(*a,**b)
    except HTTP, e:
        import os
        try:
            status=int(e.status.split(' ')[0])
        except AttributeError:
            status=e.status
          
        filename=os.path.join(request.folder,'views/errors/error%i.html'%status)
        if os.access(filename,os.R_OK):
            e.body=open(filename,'r').read()
        raise e
    except Exception:
        import os, gluon.restricted
        e=gluon.restricted.RestrictedError(function.__name__)
        # SQLDB.close_all_instances(SQLDB.rollback)
        # TODO: sort out if the above line is necessary
        
        ticket=e.log(request)
        filename=os.path.join(request.folder,'views/errors/error.html')
        if os.access(filename,os.R_OK):
            body=open(filename,'r').read()
        else:
            body="""<html><body><h1>Internal error</h1>Ticket issued: 
            <a href="/admin/default/ticket/%(ticket)s" target="_blank">%(ticket)s</a></body></html>"""
        body=body % dict(ticket=ticket)
        raise HTTP(200,body=body)
  return __onerror__
 
