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

from applications.sahana.modules.t2 import T2

# Modified version of URL from gluon/html.py
# we just need a simplified version for our jquery delete_row function
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

class T2SAHANA(T2):

    def input_required_widget(field,value):
        """
        This sets a 'class="req"' on a SPAN after the INPUT, so that CSS &/or JS can be used to mark the field.
        """
        # Default SQLFORM INPUT is:
        #INPUT(_type='text', _id=field_id,_class=field.type,_name=fieldname,value=str(default),requires=field.requires)
        #field_id=self._tablename+'_'+self.name
        items=[DIV(INPUT(_type='text', _id=field_id,_class=field.type,_name=fieldname,value=str(default),requires=field.requires),SPAN(_class='req'))]
        #items=[DIV(INPUT(_type='text',_class=field.type,_name=field.name,value=value,requires=field.requires),SPAN(_class='req'))]
        #items=[DIV(name,INPUT(_type='radio',_value=key,_name=field.name,value=value)) for key,name in field.requires.options()]
        return DIV(items)

    def _stamp_many(self,tables,form,create=False):
        """
        Called by create and update methods. it timestamps the record.
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

    def create_sahana(self,table,next=None,vars={},onaccept=None,req=None,help=None):
        """
        Extend t2.create() to add Required fields & Help buttons
        - uses SQLFORMSAHANA()
        
        t2.create(db.table,next='index',flash='done',vars={},onaccept=None)
        makes a SQLFORM and processing logic for table. Upon success it 
        redirects to "next" and flashes "flash". 
        vars are additional variables that should be placed in the form.
        onaccept=lambda form: pass is a callback executed after form accepted
        """
        request,response,session,cache,T,db=self._globals()
        if not next: next=request.function
        fields=self._filter_fields(table.get('exposes',table.fields))
        labels=self._get_labels(table)
        col3=self._get_col3(table)
        form=SQLFORMSAHANA(table,fields=fields,labels=labels,\
                     showid=False,req=req,help=help,col3=col3,_class='t2-create')
        self._stamp(table,form,create=True)
        if type(vars)==type(lambda:0): vars(form)
        else: form.vars.update(vars)
        if form.accepts(request.vars,session):
            session.flash=self.messages.record_created
            if onaccept: onaccept(form)
            self.redirect(f=next.replace('[id]',str(form.vars.id)))
        return form

    def update_sahana(self,table,query=None,next=None,deletable=True,vars={},onaccept=None,ondelete=None,req=None,help=None):
        """
        Extend t2.update() to add Required fields & Help buttons
        - uses SQLFORMSAHANA()
        
        t2.update(db.table,query,next='index',flash='done',vars={},onaccept=None,ondelete=None)
        makes a SQLFORM and processing logic for table and the record 
        identified by the query. If no query: query=table.id==t2.id
        Upon success it redirects to "next" and flashes "flash". 
        vars are additional variables that should be placed in the form.
        onaccept=lambda form: pass is a callback executed after form accepted
        """
        request,response,session,cache,T,db=self._globals()
        if not next: next='%s/[id]'%request.function
        if query:
           rows=table._db(query).select(table.ALL,limitby=(0,1))
        else:
           id=self.id or self._error()
           rows=table._db(table.id==id).select(table.ALL,limitby=(0,1))
        if not rows: self._error()
        fields=self._filter_fields(table.get('exposes',table.fields))
        labels=self._get_labels(table)
        col3=self._get_col3(table)
        self.record=record=rows[0]
        hidden={'modified_on__original':str(record.get('modified_on',None))}
        form=SQLFORMSAHANA(table,record,upload=URL(r=request,f='download'),\
                     deletable=deletable,req=req,help=help,fields=fields,labels=labels,\
                     showid=False,col3=col3,_class='t2-update',hidden=hidden)
        self._stamp(table,form)
        if type(vars)==type(lambda:0): vars(form)
        else: form.vars.update(vars)
        if request.vars.modified_on__original and \
           request.vars.modified_on__original!=hidden['modified_on__original']:
            session.flash=self.messages.record_was_altered
            redirect(self.action(args=request.args))
        if form.accepts(request.vars,session):
            form.old=record
            session.flash=self.messages.record_modified
            if request.vars.delete_this_record:
                session.flash=self.messages.record_modified
                for f in table.fields:
                    if table[f].type=='upload' and \
                       table[f].uploadfield is True:
                        name=os.path.join(request.folder,'uploads',record[f])
                        if os.path.exists(name): os.unlink(name)
                if ondelete:                    
                    ondelete(form)
            elif onaccept:                
                onaccept(form)            
            
            self.redirect(f=next.replace('[id]',str(form.vars.id)))
        return form

