import os, traceback, datetime

# This scaffolding model makes your app work on Google App Engine too   #
#try:
#    from gluon.contrib.gql import *         # if running on Google App Engine
#except:
db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
#else:
#    db=GQLDB()                              # connect to Google BigTable
#    session.connect(request,response,db=db) # and store sessions there

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
#from applications.t3.modules.t2 import T2
#t2=T2(request,response,session,cache,T,db)

# Custom classes which extend default Gluon & T2
from applications.sahana.modules.sahana import *
t2=S3(request,response,session,cache,T,db)

# Define 'now'
# 'modified_on' fields used by T2 to do edit conflict-detection & by DBSync to check which is more recent
now=datetime.datetime.today()

# Reusable timestamp fields
timestamp=SQLTable(None,'timestamp',
            SQLField('created_on','datetime',
                          writable=False,
                          default=request.now),
            SQLField('modified_on','datetime',
                          writable=False,
                          default=request.now,update=request.now)) 

# We need UUIDs as part of database synchronization
import uuid
uuidstamp=SQLTable(None,'uuidstamp',
            SQLField('uuid',length=64,
                          writable=False,
                          default=uuid.uuid4()))

# Custom validators
from applications.sahana.modules.validators import *

from gluon.storage import Storage

# Keep all S3 framework-level elements stored off here, so as to avoid polluting global namespace & to make it clear which part of the framework is being interacted with
# Avoid using this where a method parameter could be used: http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
s3=Storage()
s3.crud_fields=Storage()
s3.crud_strings=Storage()

module='s3'
# Settings - systemwide
resource='setting'
table=module+'_'+resource
db.define_table(table,timestamp,
                SQLField('admin_name'),
                SQLField('admin_email'),
                SQLField('admin_tel'),
                SQLField('debug','boolean'),
                SQLField('self_registration','boolean'),
                SQLField('audit_read','boolean'),
                SQLField('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        admin_name=T("Sahana Administrator"),
        admin_email=T("support@Not Set"),
        admin_tel=T("Not Set"),
        # Debug => Load all JS/CSS independently & uncompressed. Change to True for Production deployments (& hence stable branches)
        debug=True,
        # Change to False to disable Self-Registration
        self_registration=True,
        # Change to True to enable Auditing at the Global level (if False here, individual Modules can still enable it for them)
        audit_read=False,
        audit_write=False
    )
# Define CRUD strings (NB These apply to all Modules' 'settings' too)
s3.crud_strings=Storage()
title_create=T('Add Setting')
title_display=T('Setting Details')
title_list=T('List Settings')
title_update=T('Edit Setting')
title_search=T('Search Settings')
subtitle_create=T('Add New Setting')
subtitle_list=T('Settings')
label_list_button=T('List Settings')
label_create_button=T('Add Setting')
msg_record_created=T('Setting added')
msg_record_modified=T('Setting updated')
msg_record_deleted=T('Setting deleted')
msg_list_empty=T('No Settings currently defined')
exec('s3.crud_strings.%s=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)' % resource)

# Modules
resource='module'
table=module+'_'+resource
db.define_table(table,
                SQLField('name'),
                SQLField('name_nice'),
                SQLField('menu_priority','integer'),
                SQLField('description',length=256),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].name_nice.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name_nice' % table)]
db[table].menu_priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.menu_priority' % table)]
# Populate table with Default modules
if not len(db().select(db[table].ALL)):
	db[table].insert(
        name="default",
        name_nice="Sahana Home",
        menu_priority=0,
        description="",
        enabled='True'
	)
	db[table].insert(
        name="gis",
        name_nice="Mapping",
        menu_priority=1,
        description="Situation Awareness & Geospatial Analysis",
        enabled='True'
	)
	db[table].insert(
        name="pr",
        name_nice="Person Registry",
        menu_priority=2,
        description="Central point to record details on People",
        enabled='True'
	)
	db[table].insert(
        name="mpr",
        name_nice="Missing Person Registry",
        menu_priority=3,
        description="Helps to report and search missing person",
        enabled='False'
	)
	db[table].insert(
        name="dvr",
        name_nice="Disaster Victim Registry",
        menu_priority=4,
        description="Traces internally displaced people (IDPs) and their needs",
        enabled='False'
	)
	db[table].insert(
        name="or",
        name_nice="Organization Registry",
        menu_priority=5,
        description="Lists 'who is doing what & where'. Allows relief agencies to self organize the activities rendering fine coordination among them",
        enabled='True'
	)
	db[table].insert(
        name="cr",
        name_nice="Shelter Registry",
        menu_priority=6,
        description="Tracks the location, distibution, capacity and breakdown of victims in shelter",
        enabled='True'
	)
	db[table].insert(
        name="vol",
        name_nice="Volunteer Registry",
        menu_priority=7,
        description="Allows managing volunteers by capturing their skills, availability and allocation",
        enabled='False'
	)
	db[table].insert(
        name="ims",
        name_nice="Inventory Management",
        menu_priority=8,
        description="Effectively and efficiently manage relief aid, enables transfer of inventory items to different inventories and notify when items are required to refill",
        enabled='False'
	)
	db[table].insert(
        name="rms",
        name_nice="Request Management",
        menu_priority=9,
        description="Tracks requests for aid and matches them against donors who have pledged aid",
        enabled='False'
	)
	
# Authorization
# User Roles
# uses native T2 Groups
table='t2_group'
# Populate table with Default options
if not len(db().select(db[table].ALL)):
	# Default
    #db[table].insert(
    #    name="Anonymous User",
	#)
	db[table].insert(
        name="Administrator",
        description="System Administrator - can access & make changes to any data",
	)
    # t2.logged_in is the way to check for this role
	#db[table].insert(
    #    name="Registered User",
    #    description="A registered user in the system (e.g Volunteers, Family)"
	#)
    # No different to System Administrator currently...is there really a need for this role?
	#db[table].insert(
    #    name="Super User",
    #    description="Global Head of Operations - can access & make changes to any data"
	#)
    # Stored within gis_location_admin table
	#db[table].insert(
    #    name="Country Admin",
    #    description="Can make changes to any data within a given Country"
	#)
    # Stored within or_organisation_admin table
	#db[table].insert(
    #    name="Organisation Admin",
    #    description="Can make changes to an Organisation & it's assets"
	#)
	# Stored within cr_camp_admin table
	#db[table].insert(
    #    name="Camp Admin",
    #    description="Can make changes to a Camp"
	#)
# 1st person created will be System Administrator (can be changed later)
table='t2_membership'
if not len(db().select(db[table].ALL)):
	db[table].insert(
        person_id=1,
        group_id=1
	)
    
# Auditing
resource='audit'
table=module+'_'+resource
db.define_table(table,timestamp,
                SQLField('person',db.t2_person),
                SQLField('operation'),
                SQLField('representation'),
                SQLField('module'),
                SQLField('resource'),
                SQLField('record','integer'),
                SQLField('old_value'),
                SQLField('new_value'))
db[table].operation.requires=IS_IN_SET(['create','read','update','delete','list'])

module='default'
# Home Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.t2_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'t2_group.id','t2_group.name'))
db[table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
# Populate table with Default options
if not len(db().select(db[table].ALL)):
	db[table].insert(
        name="About Sahana",
        function="about_sahana",
        priority=0,
        enabled='True'
	)
	db[table].insert(
        name="Admin",
        function="admin",
        access=1,   # Administrator role only
        priority=1,
        enabled='True'
	)
	db[table].insert(
        name="Database",
        function="database",
        access=1,   # Administrator role only
        priority=2,
        enabled='True'
	)
	db[table].insert(
        name="Import",
        function="import_data",
        access=1,   # Administrator role only
        priority=3,
        enabled='True'
	)
	db[table].insert(
        name="Export",
        function="export_data",
        access=1,   # Administrator role only
        priority=4,
        enabled='True'
	)

# Settings - home
resource='setting'
table=module+'_'+resource
db.define_table(table,
                SQLField('audit_read','boolean'),
                SQLField('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

# Settings - appadmin
module='appadmin'
resource='setting'
table=module+'_'+resource
db.define_table(table,
                SQLField('audit_read','boolean'),
                SQLField('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

def shn_sessions(f):
    """
    Extend session to support:
         Multiple flash classes
         Settings
            Debug mode
            Audit modes
            Self-Registration
    """
    response.error=session.error
    response.confirmation=session.confirmation
    response.warning=session.warning
    session.error=[]
    session.confirmation=[]
    session.warning=[]
    # Keep all our configuration options in a single global variable
    if not session.s3:
        session.s3=Storage()
    session.s3.self_registration=db().select(db.s3_setting.self_registration)[0].self_registration
    session.s3.debug=db().select(db.s3_setting.debug)[0].debug
    # We Audit if either the Global or Module asks us to (ignore gracefully if module author hasn't implemented this)
    try:
        session.s3.audit_read=db().select(db.s3_setting.audit_read)[0].audit_read or db().select(db['%s_setting' % request.controller].audit_read)[0].audit_read
    except:
        session.s3.audit_read=db().select(db.s3_setting.audit_read)[0].audit_read
    try:
        session.s3.audit_write=db().select(db.s3_setting.audit_write)[0].audit_write or db().select(db['%s_setting' % request.controller].audit_write)[0].audit_write
    except:
        session.s3.audit_write=db().select(db.s3_setting.audit_write)[0].audit_write
    # Which roles does a user have?
    session.s3.roles=[]
    try:
        roles=db(db.t2_membership.person_id==t2.person_id).select(db.t2_membership.group_id)
        for role in roles:
            session.s3.roles.append(role.group_id)
    except:
        pass
    return f()
response._caller=lambda f: shn_sessions(f)

#
# Representations
# designed to be called via table.represent to make t2.itemize() output useful
#

def shn_represent(table,resource,deletable=True,extra=None):
    if t2.logged_in and deletable:
        if extra:
            db[table].represent=lambda table:shn_list_item(table,resource='%s' % resource,action='display',extra="TD(db(db.gis_projection.id==%i).select()[0].%s),TD(INPUT(_type='checkbox',_class='delete_row',_name='%s',_id='%i'))" % (table.id,extra,resource,table.id))
        else:
            db[table].represent=lambda table:shn_list_item(table,resource='%s' % resource,action='display',extra="INPUT(_type='checkbox',_class='delete_row',_name='%s' % resource,_id='%i' % table.id)")
    else:
        if extra:
            db[table].represent=lambda table:shn_list_item(table,resource='%s' % resource,action='display',extra="db(db.gis_projection.id==%i).select()[0].%s" % (table.id,extra))
        else:
            db[table].represent=lambda table:shn_list_item(table,resource='%s' % resource,action='display')
    return

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

# See test.py

#
# RESTlike CRUD Controller
#

def shn_crud_strings_lookup(resource):
    "Look up CRUD strings for a given resource based on the definitions in models/module.py."
    return getattr(s3.crud_strings,'%s' % resource)

def import_csv(table,file):
    "Import CSV file into Database. Comes from appadmin.py"
    import csv
    reader = csv.reader(file)
    colnames=None
    for line in reader:
        if not colnames: 
            colnames=[x[x.find('.')+1:] for x in line]
            c=[i for i in range(len(line)) if colnames[i]!='id']            
        else:
            items=[(colnames[i],line[i]) for i in c]
            table.insert(**dict(items))

def import_json(table,file):
    "Import JSON into Database."
    import gluon.contrib.simplejson as sj
    reader=sj.loads(file)
    # ToDo
    # Get column names
    # Insert records
    #table.insert(**dict(items))
    return
            
def shn_rest_controller(module,resource,deletable=True,listadd=True,extra=None):
    """
    RESTlike controller function.
    
    Provides CRUD operations for the given module/resource.
    Optional parameters:
    deletable=False: don't provide visible options for deletion
    listadd=False: don't provide an add form in the list view
    extra='field': extra field to display in the list view
    
    Anonymous users can Read.
    Authentication required for Create/Update/Delete.
    
    Auditing options for Read &/or Write.
    
    Supported Representations:
        HTML is the default (including full Layout)
        PLAIN is HTML with no layout
         - can be inserted into DIVs via AJAX calls
         - can be useful for clients on low-bandwidth or small screen sizes
        JSON
         - read-only for now
        CSV (useful for synchronization)
         - List/Display/Create for now
        AJAX (designed to be run asynchronously to refresh page elements)

    ToDo:
        Alternate Representations
            JSON create/update
            CSV update
            SMS,XML,PDF,LDIF
        Customisable Security Policy
    """
    
    _table='%s_%s' % (module,resource)
    table=db[_table]
    if resource=='setting':
        s3.crud_strings=shn_crud_strings_lookup(resource)
    else:
        s3.crud_strings=shn_crud_strings_lookup(table)
    
    # Which representation should output be in?
    if request.vars.format:
        representation=str.lower(request.vars.format)
    else:
        # Default to HTML
        representation="html"
    
    if len(request.args)==0:
        # No arguments => default to List (or list_create if logged_in)
        if session.s3.audit_read:
            db.s3_audit.insert(
                person=t2.person_id,
                operation='list',
                module=request.controller,
                resource=resource,
                old_value='',
                new_value=''
            )
        if representation=="html":
            shn_represent(table,resource,deletable,extra)
            list=t2.itemize(table)
            if not list:
                list=s3.crud_strings.msg_list_empty
            title=s3.crud_strings.title_list
            subtitle=s3.crud_strings.subtitle_list
            if t2.logged_in and listadd:
                # Display the Add form below List
                if deletable:
                    # Add extra column header to explain the checkboxes
                    if isinstance(list,TABLE):
                        list.insert(0,TR('',B('Delete?')))
                form=t2.create(table)
                # Check for presence of Custom View
                custom_view='%s_list_create.html' % resource
                _custom_view=os.path.join(request.folder,'views',module,custom_view)
                if os.path.exists(_custom_view):
                    response.view=module+'/'+custom_view
                else:
                    response.view='list_create.html'
                addtitle=s3.crud_strings.subtitle_create
                return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
            else:
                # List only
                if listadd:
                    add_btn=A(s3.crud_strings.label_create_button,_href=t2.action(resource,'create'),_id='add-btn')
                else:
                    add_btn=''
                # Check for presence of Custom View
                custom_view='%s_list.html' % resource
                _custom_view=os.path.join(request.folder,'views',module,custom_view)
                if os.path.exists(_custom_view):
                    response.view=module+'/'+custom_view
                else:
                    response.view='list.html'
                return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)
        elif representation=="ajax":
            shn_represent(table,resource,deletable,extra)
            list=t2.itemize(table)
            if not list:
                list=s3.crud_strings.msg_list_empty
            if deletable:
                # Add extra column header to explain the checkboxes
                if isinstance(list,TABLE):
                    list.insert(0,TR('',B('Delete?')))
            response.view='plain.html'
            return dict(item=list)
        elif representation=="plain":
            list=t2.itemize(table)
            response.view='plain.html'
            return dict(item=list)
        elif representation=="json":
            list=db().select(table.ALL).json()
            response.view='plain.html'
            return dict(item=list)
        elif representation=="csv":
            import gluon.contenttype
            response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
            query=db[table].id>0
            response.headers['Content-disposition']="attachment; filename=%s_%s_list.csv" % (request.env.server_name,resource)
            return str(db(query).select())
        else:
            session.error=T("Unsupported format!")
            redirect(URL(r=request,f=resource))
    else:
        method=str.lower(request.args[0])
        if request.args[0].isdigit():
            # 1st argument is ID not method => Display.
            if session.s3.audit_read:
                db.s3_audit.insert(
                    person=t2.person_id,
                    operation='read',
                    representation=representation,
                    module=request.controller,
                    resource=resource,
                    record=t2.id,
                    old_value='',
                    new_value=''
                )
            if representation=="html":
                try:
                    db[table].displays=s3.crud_fields[table]
                except:
                    pass
                item=t2.display(table)
                # Check for presence of Custom View
                custom_view='%s_display.html' % resource
                _custom_view=os.path.join(request.folder,'views',module,custom_view)
                if os.path.exists(_custom_view):
                    response.view=module+'/'+custom_view
                else:
                    response.view='display.html'
                title=s3.crud_strings.title_display
                edit=A(T("Edit"),_href=t2.action(resource,['update',t2.id]),_id='edit-btn')
                if deletable:
                    delete=A(T("Delete"),_href=t2.action(resource,['delete',t2.id]),_id='delete-btn')
                else:
                    delete=''
                list_btn=A(s3.crud_strings.label_list_button,_href=t2.action(resource),_id='list-btn')
                return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,delete=delete,list_btn=list_btn)
            elif representation=="plain":
                item=t2.display(table)
                response.view='plain.html'
                return dict(item=item)
            elif representation=="json":
                item=db(table.id==t2.id).select(table.ALL).json()
                response.view='plain.html'
                return dict(item=item)
            elif representation=="csv":
                import gluon.contenttype
                response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
                query=db[table].id==t2.id
                response.headers['Content-disposition']="attachment; filename=%s_%s_%d.csv" % (request.env.server_name,resource,t2.id)
                return str(db(query).select())
            elif representation=="rss":
                #if request.args and request.args[0] in settings.rss_procedures:
                #   feed=eval('%s(*request.args[1:],**dict(request.vars))'%request.args[0])
                #else:
                #   t2._error()
                #import gluon.contrib.rss2 as rss2
                #rss = rss2.RSS2(
                #   title=feed['title'],
                #   link = feed['link'],
                #   description = feed['description'],
                #   lastBuildDate = feed['created_on'],
                #   items = [
                #      rss2.RSSItem(
                #        title = entry['title'],
                #        link = entry['link'],
                #        description = entry['description'],
                #        pubDate = entry['created_on']) for entry in feed['entries']]
                #   )
                #response.headers['Content-Type']='application/rss+xml'
                #return rss2.dumps(rss)
                response.view='plain.html'
                return
            else:
                session.error=T("Unsupported format!")
                redirect(URL(r=request,f=resource))
        else:
            if method=="create":
                if t2.logged_in:
                    if session.s3.audit_write:
                        audit_id=db.s3_audit.insert(
                            person=t2.person_id,
                            operation='create',
                            representation=representation,
                            module=request.controller,
                            resource=resource,
                            record=t2.id,
                            old_value='',
                            new_value=''
                        )
                    if representation=="html":
                        t2.messages.record_created=s3.crud_strings.msg_record_created
                        form=t2.create(table)
                        # Check for presence of Custom View
                        custom_view='%s_create.html' % resource
                        _custom_view=os.path.join(request.folder,'views',module,custom_view)
                        if os.path.exists(_custom_view):
                            response.view=module+'/'+custom_view
                        else:
                            response.view='create.html'
                        title=s3.crud_strings.title_create
                        list_btn=A(s3.crud_strings.label_list_button,_href=t2.action(resource),_id='list-btn')
                        return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                    elif representation=="plain":
                        form=t2.create(table)
                        response.view='plain.html'
                        return dict(item=form)
                    elif representation=="json":
                        # ToDo
                        # Read in POST
                        #file=request.body.read()
                        #import_json(table,file)
                        item='{"Status":"failed","Error":{"StatusCode":501,"Message":"JSON creates not yet supported!"}}'
                        response.view='plain.html'
                        return dict(item=item)
                    elif representation=="csv":
                        # Read in POST
                        file=request.vars.filename.file
                        try:
                            import_csv(table,file)
                            reply=T('Data uploaded')
                        except: 
                            reply=T('Unable to parse CSV file!')
                        return reply
                    else:
                        session.error=T("Unsupported format!")
                        redirect(URL(r=request,f=resource))
                else:
                    t2.redirect('login',vars={'_destination':'%s/create' % resource})
            elif method=="display":
                t2.redirect(resource,args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    if session.s3.audit_write:
                        old_value = []
                        _old_value=db(db[table].id==t2.id).select()[0]
                        for field in _old_value:
                            old_value.append(field+':'+str(_old_value[field]))
                        audit_id=db.s3_audit.insert(
                            person=t2.person_id,
                            operation='update',
                            representation=representation,
                            module=request.controller,
                            resource=resource,
                            record=t2.id,
                            old_value=old_value,
                            new_value=''
                        )
                    if representation=="html":
                        t2.messages.record_modified=s3.crud_strings.msg_record_modified
                        form=t2.update(table,deletable=False)
                        # Check for presence of Custom View
                        custom_view='%s_update.html' % resource
                        _custom_view=os.path.join(request.folder,'views',module,custom_view)
                        if os.path.exists(_custom_view):
                            response.view=module+'/'+custom_view
                        else:
                            response.view='update.html'
                        title=s3.crud_strings.title_update
                        list_btn=A(s3.crud_strings.label_list_button,_href=t2.action(resource),_id='list-btn')
                        return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                    elif representation=="plain":
                        form=t2.update(table,deletable=False)
                        response.view='plain.html'
                        return dict(item=form)
                    elif representation=="json":
                        # ToDo
                        item='{"Status":"failed","Error":{"StatusCode":501,"Message":"JSON updates not yet supported!"}}'
                        response.view='plain.html'
                        return dict(item=item)
                    else:
                        session.error=T("Unsupported format!")
                        redirect(URL(r=request,f=resource))
                else:
                    t2.redirect('login',vars={'_destination':'%s/update/%i' % (resource,t2.id)})
            elif method=="delete":
                if t2.logged_in:
                    if session.s3.audit_write:
                        old_value = []
                        _old_value=db(db[table].id==t2.id).select()[0]
                        for field in _old_value:
                            old_value.append(field+':'+str(_old_value[field]))
                        db.s3_audit.insert(
                            person=t2.person_id,
                            operation='delete',
                            representation=representation,
                            module=request.controller,
                            resource=resource,
                            record=t2.id,
                            old_value=old_value,
                            new_value=''
                        )
                    t2.messages.record_deleted=s3.crud_strings.msg_record_deleted
                    if representation=="ajax":
                        t2.delete(table,next='%s?format=ajax' % resource)
                    else:
                        t2.delete(table,next=resource)
                else:
                    t2.redirect('login',vars={'_destination':'%s/delete/%i' % (resource,t2.id)})
            elif method=="search":
                if session.s3.audit_read:
                    db.s3_audit.insert(
                        person=t2.person_id,
                        operation='search',
                        module=request.controller,
                        resource=resource,
                        old_value='',
                        new_value=''
                    )
                if representation=="html":
                    if t2.logged_in and deletable:
                        db[table].represent=lambda table:shn_list_item(table,resource='%s' % resource,action='display',extra="INPUT(_type='checkbox',_class='delete_row',_name='%s' % resource,_id='%i' % table.id)")
                    else:
                        db[table].represent=lambda table:shn_list_item(table,resource='%s' % resource,action='display')
                    search=t2.search(table)
                    # Check for presence of Custom View
                    custom_view='%s_search.html' % resource
                    _custom_view=os.path.join(request.folder,'views',module,custom_view)
                    if os.path.exists(_custom_view):
                        response.view=module+'/'+custom_view
                    else:
                        response.view='search.html'
                    title=s3.crud_strings.title_search
                    return dict(module_name=module_name,modules=modules,options=options,search=search,title=title)
                else:
                    session.error=T("Unsupported format!")
                    redirect(URL(r=request,f=resource))
            else:
                session.error=T("Unsupported method!")
                redirect(URL(r=request,f=resource))
