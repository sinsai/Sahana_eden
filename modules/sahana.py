"""
This file was developed by Fran Boon as a web2py extension.
This file is released under the BSD license (you can include it in bytecode compiled web2py apps as long as you acknowledge the author). web2py (required to run this file) is released under the GPLv2 license.
"""

from gluon.storage import Storage
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.contrib.markdown import WIKI
try: from gluon.contrib.gql import SQLTable
except ImportError: from gluon.sql import SQLTable
import traceback

#from applications.t3.modules.t2 import T2
from applications.sahana.modules.t2 import T2

def shn_db_clean(db):
    """
    Drop tables to remove all data.
    To be done before a release.
    All neccessary lookup tables will be recreated upon initialisation.
    """
    tables=['gis_layer_openstreetmap','gis_layer_google','gis_layer_yahoo','gis_layer_virtualearth','default_setting']
    for table in tables:
        # Remove table completely
        db["%s" % table].drop()
        # Clear all records (& reset IDs), but keep table
        #db["%s" % table].truncate()
    db.commit()


# Modified versions of URL from gluon/html.py
# we need simplified versions for our jquery functions
def URL2(a=None,c=None,r=None):
    """
    example:

    >>> URL(a='a',c='c')
    '/a/c'

    generates a url "/a/c" corresponding to application a & controller c 
    If r=request is passed, a & c are set, respectively,
    to r.application, r.controller

    The more typical usage is:
    
    URL(r=request) that generates a base url with the present application and controller.
    
    The function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application=controller=None
    if r:
        application=r.application
        controller=r.controller
    if a: application=a    
    if c: controller=c
    if not (application and controller):
        raise SyntaxError, 'not enough information to build the url'
    other=''
    url='/%s/%s' % (application, controller)
    return url
        
def URL3(a=None,r=None):
    """
    example:

    >>> URL(a='a')
    '/a'

    generates a url "/a" corresponding to application a
    If r=request is passed, a is set
    to r.application

    The more typical usage is:
    
    URL(r=request) that generates a base url with the present application.
    
    The controller & function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application=controller=None
    if r:
        application=r.application
        controller=r.controller
    if a: application=a    
    if not (application and controller):
        raise SyntaxError, 'not enough information to build the url'
    other=''
    url='/%s' % application
    return url
        
# Extended version of T2 from modules/t2.py 
class S3(T2):

    def __init__(self,request,response,session,cache,T,db,all_in_db=False):
        T2.__init__(self,request,response,session,cache,T,db,all_in_db=False)
        # Clear unused info from cluttering every Response
        response.files=[]
    
    # Modified version of _stamp
    # we need to support multiple tables
    # NB Needs testing!
    def _stamp_many(self,tables,form,create=False):
        """
        Called by create and update methods. it timestamps the records.
        The following fields are timestamped (if they exist):
        - created_on
        - created_by
        - created_signature
        - modified_on
        - modified_by
        - modified_signature
        """
        
        for table in tables:
            if create:
                if 'created_by_ip' in table.fields: 
                    form.vars.created_by_ip=self.request.client
                if 'created_on' in table.fields: 
                    form.vars.created_on=self.now
                if 'created_by' in table.fields: 
                    form.vars.created_by=self.person_id
                if 'created_signature' in table.fields: 
                    form.vars.created_signature=self.person_name
            if 'modified_by_ip' in table.fields:
                form.vars.modified_by_ip=self.request.client
            if 'modified_on' in table.fields: 
                form.vars.modified_on=self.now
            if 'modified_by' in table.fields:
                form.vars.modified_by=self.person_id
            if 'modified_signature' in table.fields:
                form.vars.modified_signature=self.person_name
