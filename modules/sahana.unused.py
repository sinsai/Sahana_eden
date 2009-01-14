"""
This file was developed by Fran Boon as a web2py extension.

UNUSED

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

def shn_db_clean(db):
    """
    Drop tables to remove all data.
    To be done before a release. (Actually we can just delete the contents of databases/
    All necessary lookup tables will be recreated upon initialisation.
    """
    tables=['gis_layer_openstreetmap','gis_layer_google','gis_layer_yahoo','gis_layer_virtualearth','default_setting']
    for table in tables:
        # Remove table completely
        db["%s" % table].drop()
        # Clear all records (& reset IDs), but keep table
        #db["%s" % table].truncate()
    db.commit()

from applications.sahana.modules.t2 import T2

class SQLFORMSAHANA(SQLFORM):
    """
    SQLFORMSAHANA is used to map a table (and a current record) into an HTML form
    - extends SQLFORM() to add Required fields & Help buttons
    - this needs ot be on a per-field basis & not per-table or per record!
    - this info needs to be in the database as this 
    - req could be a single field which is an array of those fields which are Required
    - help needs to be a separate field for each field, e.g. ['%s_help' % field]
   
    given a SQLTable stored in db.table

    SQLFORMSAHANA(db.table) generates an insert form
    record=db(db.table.id==some_id).select()[0]
    SQLFORMSAHANA(db.table,record) generates an update form
    SQLFORMSAHANA(db.table,record,deletable=True) generates an update with a delete button
    
    optional arguments:
    
    fields: a list of fields that should be placed in the form, default is all.
    labels: a dictionary with labels for each field. keys are field names.
    col3  : a dictionary with content for an optional third column (right of each field). keys are field names.
    linkto: the URL of a controller/function to access referencedby records
            see controller appadmin.py for examples
    upload: the URL of a controller/function to download an uploaded file
            see controller appadmin.py for examples
    any named optional attribute is passed to the <form> tag
            for example _class, _id, _style, _action,_method, etc.

    """
    # usability improvements proposal by fpp - 4 May 2008 :
    # - correct labels (for points to filed id, not field name)
    # - add label for delete checkbox
    # - add translatable label for record ID
    # - add third column to right of fields, populated from the col3 dict
    
    def __init__(self,table,record=None,deletable=False,
                 linkto=None,upload=None,fields=None,labels=None,col3={},
                 submit_button='Submit', delete_label='Check to delete:', 
                 id_label='Record id: ', showid=True,**attributes):
        """
        SQLFORMSAHANA(db.table,
               record=None,
               fields=['name'],
               labels={'name':'Your name'},
               linkto=ULR(r=request,f='table/db/')
        """
        self.table=table
        self.trows={}
        FORM.__init__(self,*[],**attributes)            
        xfields=[]
        self.fields=fields
        if not self.fields: self.fields=self.table.fields        
        if not 'id' in self.fields: self.fields.insert(0,'id')
        self.record=record
        self.record_id=None
        for fieldname in self.fields:
            if fieldname.find('.')>=0: continue
            field_id='%s_%s' % (table._tablename,fieldname)
            if fieldname=='id':                
                if record: 
                    if showid:
                        xfields.append(TR(LABEL(id_label,_for='id',_id='id__label'),\
                                          B(record['id']),col3.get('id',''),\
                                          _id='id__row'))
                    self.record_id=str(record['id'])
                continue
            field=self.table[fieldname]
            if record: default=record[fieldname]
            else: default=field.default
            if default: default=field.formatter(default)
            if labels!=None and labels.has_key(fieldname):
                label=labels[fieldname]
            else:
                label=str(field.label)+': '
            label=LABEL(label,_for=field_id,_id='%s__label'%field_id)
            comment=col3.get(fieldname,'')
            row_id=field_id+'__row'
            if hasattr(field,'widget') and field.widget:
                inp=field.widget(field,default)
            elif field.type=='text':
                inp=TEXTAREA(_type='text',_id=field_id,_class=field.type,
                    _name=fieldname,value=default, requires=field.requires)
            elif field.type=='blob':
                continue
            elif field.type=='upload':
                inp=INPUT(_type='file',_id=field_id,_class=field.type,
                          _name=fieldname, requires=field.requires)
                if upload and default:
                    inp=DIV(inp,'[',A('file',_href=upload+'/'+default),'|',
                        INPUT(_type='checkbox',_name=fieldname+'__delete'),'delete]')
            elif field.type=='boolean':
                inp=INPUT(_type='checkbox',_id=field_id,_class=field.type,
                    _name=fieldname,value=default, requires=field.requires)
            elif hasattr(field.requires,'options'):
                opts=[]
                for k,v in field.requires.options():
                    opts.append(OPTION(v,_value=k))
                inp=SELECT(*opts,**dict(_id=field_id,_class=field.type,
                     _name=fieldname,value=default,requires=field.requires))
            elif isinstance(field.requires,IS_NULL_OR) and \
                 hasattr(field.requires.other,'options'):
                opts=[OPTION(_value="")]
                for k,v in field.requires.other.options():
                    opts.append(OPTION(v,_value=k))
                inp=SELECT(*opts,**dict(_id=field_id,_class=field.type,
                     _name=fieldname,value=default,requires=field.requires))
            elif field.type=='password':
                if self.record: v='********'
                else: v=''
                inp=INPUT(_type='password', _id=field_id,
                      _name=fieldname,_value=v,_class=field.type,
                      requires=field.requires)
            else:
                if default==None: default=''
                inp=INPUT(_type='text', _id=field_id,_class=field.type,
                      _name=fieldname,value=str(default),
                      requires=field.requires)
            tr=self.trows[fieldname]=TR(label,inp,comment,_id=row_id)
            xfields.append(tr)
        if record and linkto:
            if linkto:
                for rtable,rfield in table._referenced_by:
                    query=urllib.quote(str(table._db[rtable][rfield]==record.id))
                    lname=olname='%s.%s' % (rtable,rfield)
                    if fields and not olname in fields: continue
                    if labels and labels.has_key(lname): lname=labels[lname]
                    xfields.append(TR('',A(lname,
                           _class='reference',
                           _href='%s/%s?query=%s'%(linkto,rtable,query)),
                           col3.get(olname,''),
                           _id='%s__row'%olname.replace('.','__')))
        if record and deletable:
            xfields.append(TR(LABEL(delete_label, _for='delete_record',_id='delete_record__label'),INPUT(_type='checkbox', _class='delete', _id='delete_record', _name='delete_this_record'),col3.get('delete_record',''),_id='delete_record__row'))            
        xfields.append(TR('',INPUT(_type='submit',_value=submit_button),col3.get('submit_button',''),_id='submit_record__row'))
        if record:
            self.components=[TABLE(*xfields),INPUT(_type='hidden',_name='id',_value=record['id'])]
        else: self.components=[TABLE(*xfields)]

class T2SAHANA(T2):

    def input_required_widget(field,value):
        """
        This sets a 'class="req"' on a SPAN after the INPUT, so that CSS &/or JS can be used to mark the field.
        """
        # Default SQLFORM INPUT is:
        #INPUT(_type='text', _id=field_id,_class=field.type,_name=fieldname,value=str(default),requires=field.requires)
        items=[INPUT(_type='text', _id=field_id),SPAN(_class='req')]
        #items=[TR(LABEL(id_label,_for='id',_id='id__label'),B(record['id']),col3.get('id',''),_id='id__row')]
        #items=[DIV(name,INPUT(_type='radio',_value=key,_name=field.name,value=value)) for key,name in field.requires.options()]
        return DIV(*items)

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

