# This scaffolding model makes your app work on Google App Engine too   #
#try:
#    from gluon.contrib.gql import *         # if running on Google App Engine
#except:
db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
#else:
#    db=GQLDB()                              # connect to Google BigTable
#    session.connect(request,response,db=db) # and store sessions there

# Define 'now'
# 'modified_on' fields used by T2 to do edit conflict-detection & by DBSync to check which is more recent
import datetime; now=datetime.datetime.today()

# We need UUIDs for database synchronization
import uuid

# We want to allow JS clients to access data in JSON format
#import gluon.contrib.simplejson as sj 

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
#from applications.sahana.modules.t2 import T2
#t2=T2(request,response,session,cache,T,db)

# Custom classes which extend default Gluon & T2
from applications.sahana.modules.sahana import *
t2=T2SAHANA(request,response,session,cache,T,db)

# Custom validators
from applications.sahana.modules.validators import *

#
# Representations
# designed to be called via table.represent to make t2.itemize() output useful
#

def shn_list_item(table,resource,action,display='table.name',extra=None):
    "Display nice names with clickable links & optional extra info"
    if extra:
        items=DIV(TR(TD(A(eval(display),_href=t2.action(resource,[action,table.id]))),TD(eval(extra))))
    else:
        items=DIV(A(eval(display),_href=t2.action(resource,[action,table.id])))
    return DIV(*items)

#
# Widgets
#

def shn_m2m_widget(self,value,options=[]):
    """Many-to-Many widget
    Currently this is just a renamed copy of t2.tag_widget"""
    
    script=SCRIPT("""
    function web2py_m2m(self,other,option) {
       var o=document.getElementById(other)
       if(self.className=='option_selected') {
          self.setAttribute('class','option_deselected');
          o.value=o.value.replace('['+option+']','');
       }
       else if(self.className=='option_deselected') {
          self.setAttribute('class','option_selected');
          o.value=o.value+'['+option+']';
       }
    }
    """)
    id=self._tablename+'_'+self.name
    def onclick(x):
        return "web2py_m2m(this,'%s','%s');"%(id,x.lower())
    buttons=[SPAN(A(x,_class='option_selected' if value and '[%s]'%x.lower() in value else 'option_deselected',_onclick=onclick(x)),' ') for x in options]
    return DIV(script,INPUT(_type='hidden',_id=id,_name=self.name,_value=value),*buttons) 

# M2M test
db.define_table('owner',SQLField('name'),SQLField('uuid',length=64,default=uuid.uuid4()))
db.define_table('dog',SQLField('name'),SQLField('owner','text'))
#db.dog.owner.requires=IS_IN_DB(db,'owner.uuid','owner.name',multiple=True)
db.dog.owner.requires=IS_IN_DB(db,'owner.id','owner.name',multiple=True)
#db.dog.owner.display=lambda x: ', '.join([db(db.owner.id==id).select()[0].name for id in x[1:-1].split('|')])
#db.dog.owner.display=lambda x: map(db(db.owner.id==id).select()[0].name,x[1:-1].split('|'))
db.dog.represent=lambda dog: A(dog.name,_href=t2.action('display_dog',dog.id))


def shn_crud_strings_lookup(resource):
    "Look up CRUD strings for a given resource."
    return eval('crud_strings_%s' % resource)

def shn_rest_controller(module,resource):
    """
    RESTful controller function.
    
    Anonymous users can Read.
    Authentication required for Create/Update/Delete.
    
    ToDo:
        Alternate Representations
        Search method
        Customisable Security Policy
    """
    
    table=db['%s_%s' % (module,resource)]
    
    crud_strings=shn_crud_strings_lookup(resource)

    if len(request.args)==0:
        # No arguments => default to list (or list_create if logged_in)
        list=t2.itemize(table)
        if list=="No data":
            list=crud_strings.msg_list_empty
        title=crud_strings.title_list
        subtitle=crud_strings.subtitle_list
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=crud_strings.subtitle_create
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(crud_strings.label_create_button,_href=t2.action(resource,'create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)
            
    else:
        method=request.args[0]
        if request.args[0].isdigit():
            # 1st argument is ID not method => display.
            # Default format (representation) is full HTML page
            item=t2.display(table)
            response.view='display.html'
            title=crud_strings.title_display
            edit=A(T("Edit"),_href=t2.action(resource,['update',t2.id]))
            list_btn=A(crud_strings.label_list_button,_href=t2.action(resource))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        else:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=crud_strings.msg_record_created
                    form=t2.create(table)
                    response.view='create.html'
                    title=crud_strings.title_create
                    list_btn=A(crud_strings.label_list_button,_href=t2.action(resource))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'%s/create' % resource})
            elif method=="display":
                t2.redirect(resource,args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=crud_strings.msg_record_modified
                    form=t2.update(table)
                    response.view='update.html'
                    title=crud_strings.title_update
                    list_btn=A(crud_strings.label_list_button,_href=t2.action(resource))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'%s/update/%i' % (resource,t2.id)})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=crud_strings.msg_record_deleted
                    t2.delete(table,next=resource)
                    return
                else:
                    t2.redirect('login',vars={'_destination':'%s/delete/%i' % (resource,t2.id)})
            else:
                # Unsupported method!
                t2.redirect(resource)

# Modules
db.define_table('module',
                SQLField('name'),
                SQLField('name_nice'),
                SQLField('menu_priority','integer'),
                SQLField('description',length=256),
                SQLField('enabled','boolean',default='True'))
db.module.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name')]
db.module.name_nice.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name_nice')]
db.module.menu_priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.menu_priority')]

# Home Menu Options
db.define_table('default_menu_option',
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.default_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'default_menu_option.name')]
db.default_menu_option.function.requires=IS_NOT_EMPTY()
db.default_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'default_menu_option.priority')]

# Field options meta table
# Give a custom list of options for each field in this schema 
# prefixed with opt_. This is customizable then at deployment
# See the field_options.py for default customizations
# Modules: cr
# Actually for S3 we have a per-module table for 'config'
#db.define_table('field_option',
#                SQLField('field_name'),
#                SQLField('option_code',length=20),
#                SQLField('option_description',length=50))
#db.field_option.field_name.requires=IS_NOT_EMPTY()
#db.field_option.option_code.requires=IS_NOT_EMPTY()
#db.field_option.option_description.requires=IS_NOT_EMPTY()

# System Config
db.define_table('system_config',
				SQLField('setting'),
				SQLField('description',length=256),
				SQLField('value'))
# We want a THIS_NOT_IN_DB here: admin_name, admin_email, admin_tel
db.system_config.setting.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'system_config.setting')]
