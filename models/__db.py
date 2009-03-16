import os, traceback, datetime

# This scaffolding model makes your app work on Google App Engine too   #
#try:
#    from gluon.contrib.gql import *         # if running on Google App Engine
#except:
db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
#else:
#    db=GQLDB()                              # connect to Google BigTable
#    session.connect(request,response,db=db) # and store sessions there

# Default strings are in English
T.current_languages=['en','en-en']

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
#from applications.t3.modules.t2 import T2
#t2=T2(request,response,session,cache,T,db)

# Custom classes which extend default Gluon & T2
from applications.sahana.modules.sahana import *

t2=S3(request,response,session,cache,T,db)

mail=MailS3()
# These settings should be made configurable as part of the Messaging Module
mail.settings.server='mail:25'
mail.sender='sahana@sahanapy.org'

auth=AuthS3(globals(),T,db)
#auth=Auth(globals(),db)
auth.define_tables()
# Email settings for registration verification
auth.settings.mailer=mail
# Require captcha verification for registration
#auth.settings.captcha=RECAPTCHA(request,public_key='RECAPTCHA_PUBLIC_KEY',private_key='RECAPTCHA_PRIVATE_KEY')

crud=CrudS3(globals(),T,db)
# Use Role-based Access Control for Crud
crud.auth=auth

from gluon.tools import Service
service=Service(globals())

# Define 'now'
# 'modified_on' fields used by T2 to do edit conflict-detection & by DBSync to check which is more recent
#now=datetime.datetime.today()

# Reusable timestamp fields
timestamp=SQLTable(None,'timestamp',
            SQLField('created_on','datetime',
                          readable=False,
                          writable=False,
                          default=request.now),
            SQLField('modified_on','datetime',
                          readable=False,
                          writable=False,
                          default=request.now,update=request.now)) 

# Reusable author fields
authorstamp=SQLTable(None,'authorstamp',
            SQLField('created_by',db.auth_user,
                          default=session.auth.user.id if auth.is_logged_in() else 0,
                          writable=False),
            SQLField('modified_by',db.auth_user,
                          default=session.auth.user.id if auth.is_logged_in() else 0,update=session.auth.user.id if auth.is_logged_in() else 0,
                          writable=False)) 

# Reusable UUID field (needed as part of database synchronization)
import uuid
uuidstamp=SQLTable(None,'uuidstamp',
            SQLField('uuid',length=64,
                          readable=False,
                          writable=False,
                          default=uuid.uuid4()))

# Reusable Admin field
admin_id=SQLTable(None,'admin_id',
            SQLField('admin',
                db.auth_group,requires=IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role')),
                represent=lambda id: (id and [db(db.auth_group.id==id).select()[0].role] or ["None"])[0],
                comment=DIV(A(T('Add Role'),_class='popup',_href=URL(r=request,c='default',f='role',args='create',vars=dict(format='plain')),_target='top'),A(SPAN("[Help]"),_class="tooltip",_title=T("Contact|The Person to contact for this.")))
                ))
    
# Custom validators
from applications.sahana.modules.validators import *

from gluon.storage import Storage
# Keep all S3 framework-level elements stored off here, so as to avoid polluting global namespace & to make it clear which part of the framework is being interacted with
# Avoid using this where a method parameter could be used: http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
s3=Storage()
s3.crud_strings=Storage()
s3.display=Storage()

table='auth_group'
title_create=T('Add Role')
title_display=T('Role Details')
title_list=T('List Roles')
title_update=T('Edit Role')
title_search=T('Search Roles')
subtitle_create=T('Add New Role')
subtitle_list=T('Roles')
label_list_button=T('List Roles')
label_create_button=T('Add Role')
msg_record_created=T('Role added')
msg_record_modified=T('Role updated')
msg_record_deleted=T('Role deleted')
msg_list_empty=T('No Roles currently registered')
s3.crud_strings[table]=Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

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
s3.crud_strings[resource]=Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)

# Modules
resource='module'
table=module+'_'+resource
db.define_table(table,
                SQLField('name'),
                SQLField('name_nice'),
                SQLField('access',db.auth_group),  # Hide modules if users don't have the required access level (NB Not yet implemented either in layout.html or the controllers)
                SQLField('priority','integer'),
                SQLField('description',length=256),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].name_nice.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name_nice' % table)]
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role'))
db[table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]
# Populate table with Default modules
if not len(db().select(db[table].ALL)):
	db[table].insert(
        name="default",
        name_nice="Sahana Home",
        priority=0,
        description="",
        enabled='True'
	)
	db[table].insert(
        name="gis",
        name_nice="Mapping",
        priority=1,
        description="Situation Awareness & Geospatial Analysis",
        enabled='True'
	)
	db[table].insert(
        name="pr",
        name_nice="Person Registry",
        priority=2,
        description="Central point to record details on People",
        enabled='True'
	)
	db[table].insert(
        name="mpr",
        name_nice="Missing Person Registry",
        priority=3,
        description="Helps to report and search missing person",
        enabled='True'
	)
	db[table].insert(
        name="dvr",
        name_nice="Disaster Victim Registry",
        priority=4,
        description="Traces internally displaced people (IDPs) and their needs",
        enabled='False'
	)
	db[table].insert(
        name="or",
        name_nice="Organization Registry",
        priority=5,
        description="Lists 'who is doing what & where'. Allows relief agencies to self organize the activities rendering fine coordination among them",
        enabled='True'
	)
	db[table].insert(
        name="cr",
        name_nice="Shelter Registry",
        priority=6,
        description="Tracks the location, distibution, capacity and breakdown of victims in shelter",
        enabled='True'
	)
	db[table].insert(
        name="vol",
        name_nice="Volunteer Registry",
        priority=7,
        description="Allows managing volunteers by capturing their skills, availability and allocation",
        enabled='False'
	)
	db[table].insert(
        name="ims",
        name_nice="Inventory Management",
        priority=8,
        description="Effectively and efficiently manage relief aid, enables transfer of inventory items to different inventories and notify when items are required to refill",
        enabled='False'
	)
	db[table].insert(
        name="rms",
        name_nice="Request Management",
        priority=9,
        description="Tracks requests for aid and matches them against donors who have pledged aid",
        enabled='False'
	)
	db[table].insert(
        name="dvi",
        name_nice="Disaster Victim Identification",
        priority=10,
        description="Assists the management of fatalities and identification of the deceased",
        enabled='True'
	)
	db[table].insert(
        name="msg",
        name_nice="Messaging Module",
        priority=11,
        description="Sends & Receives Alerts via Email & SMS",
        enabled='True'
	)
	
# Authorization
# User Roles
# uses native Web2Py Auth Groups
table = auth.settings.table_group_name
# 1st-run initialisation
if not len(db().select(db[table].ALL)):
    auth.add_group('Administrator',description='System Administrator - can access & make changes to any data')
    # 1st person created will be System Administrator (can be changed later)
    auth.add_membership(1,1)
    
# Auditing
# ToDo: consider using native Web2Py log to auth_events
resource='audit'
table=module+'_'+resource
db.define_table(table,timestamp,
                SQLField('person',db.auth_user),
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
                SQLField('access'),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role'))
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
        access='Administrator',   # Administrator role only
        priority=1,
        enabled='True'
	)
	db[table].insert(
        name="Database",
        function="database",
        access='Administrator',   # Administrator role only
        priority=2,
        enabled='True'
	)
	db[table].insert(
        name="Test",
        function="test",
        access='Administrator',   # Administrator role only
        priority=3,
        enabled='True'
	)
	db[table].insert(
        name="Import",
        function="import_data",
        access='Administrator',   # Administrator role only
        priority=4,
        enabled='True'
	)
	db[table].insert(
        name="Export",
        function="export_data",
        access='Administrator',   # Administrator role only
        priority=5,
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
    if auth.is_logged_in():
        roles=db(db.auth_membership.user_id==auth.user.id).select(db.auth_membership.group_id)
        for role in roles:
            role_name=db(db.auth_group.id==role.group_id).select(db.auth_group.role)[0].role
            session.s3.roles.append(role_name)
    return f()
response._caller=lambda f: shn_sessions(f)

#
# Representations
#

def shn_represent(table,module,resource,deletable=True,main='name',extra=None):
    "Designed to be called via table.represent to make t2.itemize() output useful"
    db[table].represent=lambda table:shn_list_item(table,resource,action='display',main=main,extra=shn_represent_extra(table,module,resource,deletable,extra))
    return

def shn_represent_extra(table,module,resource,deletable=True,extra=None):
    "Display more than one extra field (separated by spaces)"
    item_list=[]
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % (module,resource,table.id,any_item))
    if auth.is_logged_in() and deletable:
        item_list.append("TD(INPUT(_type='checkbox',_class='delete_row',_name='%s',_id='%i'))" % (resource,table.id))
    return ','.join( item_list )

def shn_list_item(table,resource,action,main='name',extra=None):
    "Display nice names with clickable links & optional extra info"
    item_list = [TD(A(table[main],_href=URL(r=request,f=resource,args=[action,table.id])))]
    if extra:
        item_list.extend(eval(extra))
    items=DIV(TABLE(TR(item_list)))
    return DIV(*items)

#
# Widgets
#

# See test.py

#
# Onvalidation callbacks
#
def wkt_centroid(form):
    """GIS
    If a Point has LonLat defined: calculate the WKT.
    If a Line/Polygon has WKT defined: validate the format & calculate the LonLat of the Centroid
    Centroid calculation is done using Shapely, which wraps Geos.
    A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm
    """
    if form.vars.type=='point':
        if form.vars.lon==None:
            form.errors['lon'] = T("Invalid: Longitude can't be empty!")
            return
        if form.vars.lat==None:
            form.errors['lat'] = T("Invalid: Latitude can't be empty!")
            return
        form.vars.wkt = 'POINT(%(lon)f %(lat)f)' % form.vars
    elif form.vars.type=='line':
        try:
            from shapely.wkt import loads
            try:
                line=loads(form.vars.wkt)
            except:
                form.errors['wkt'] = T("Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!")
                return
            centroid_point = line.centroid
            form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
            form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
        except:
            #form.errors['type'] = str(A('Shapely',_href='http://pypi.python.org/pypi/Shapely/',_target='_blank'))+str(T(" library not found, so can't find centroid!"))
            form.errors['type'] = T("Shapely library not found, so can't find centroid!")
    elif form.vars.type=='polygon':
        try:
            from shapely.wkt import loads
            try:
                polygon=loads(form.vars.wkt)
            except:
                form.errors['wkt'] = T("Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!")
                return
            centroid_point = polygon.centroid
            form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
            form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
        except:
            form.errors['type'] = T("Shapely library not found, so can't find centroid!")
    else:
        form.errors['type'] = T('Unknown type!')
    return

#
# RESTlike CRUD Controller
#

def shn_crud_strings_lookup(resource):
    "Look up CRUD strings for a given resource based on the definitions in models/module.py."
    return getattr(s3.crud_strings,'%s' % resource)

def import_csv(table,file):
    "Import CSV file into Database. Comes from appadmin.py. Modified to do Validation on UUIDs"
    table.import_from_csv_file(file)

def import_json(table,file):
    "Import JSON into Database."
    import gluon.contrib.simplejson as sj
    reader=sj.loads(file)
    # ToDo
    # Get column names (like for SQLTable.import_from_csv_file() )
    # Insert records (or Update if unique field duplicated)
    #table.insert(**dict(items))
    return
            
def shn_rest_controller(module,resource,deletable=True,listadd=True,main='name',extra=None,onvalidation=None):
    """
    RESTlike controller function.
    
    Provides CRUD operations for the given module/resource.
    Optional parameters:
    deletable=False: don't provide visible options for deletion
    listadd=False: don't provide an add form in the list view
    main='field': main field to display in the list view (defaults to 'name')
    extra='field': extra field to display in the list view
    
    Anonymous users can Read.
    Authentication required for Create/Update/Delete.
    
    Auditing options for Read &/or Write.
    
    Supported Representations:
        HTML is the default (including full Layout)
        PLAIN is HTML with no layout
         - can be inserted into DIVs via AJAX calls
         - can be useful for clients on low-bandwidth or small screen sizes
        JSON (designed to be accessed via JavaScript)
         - responses in JSON format
         - create/update/delete done via simple GET vars (no form displayed)
        CSV (useful for synchronization)
         - List/Display/Create for now
        RSS (list only)
        AJAX (designed to be run asynchronously to refresh page elements)
        POPUP
    ToDo:
        Alternate Representations
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
    
    try:
        crud.messages.record_created=s3.crud_strings.msg_record_created
        crud.messages.record_updated=s3.crud_strings.msg_record_modified
        crud.messages.record_deleted=s3.crud_strings.msg_record_deleted
    except:
        pass

    # Which representation should output be in?
    if request.vars.format:
        representation=str.lower(request.vars.format)
    else:
        # Default to HTML
        representation="html"
    
    # Is user logged-in?
    logged_in = auth.is_logged_in()
    
    if len(request.args)==0:
        # No arguments => default to List (or list_create if logged_in)
        if session.s3.audit_read:
            db.s3_audit.insert(
                person=auth.user.id if logged_in else 0,
                operation='list',
                module=request.controller,
                resource=resource,
                old_value='',
                new_value=''
            )
        if representation=="html":
            # Not yet a replacement for t2.itemize
            #fields=['%s.id' % table,'%s.first_name' % table,'%s.last_name' % table]
            #headers={'%s.id' % table:'ID','%s.first_name' % table:'First Name','%s.last_name' % table:'Last Name'}
            #list=crud.select(table,fields=fields,headers=headers)
            shn_represent(table,module,resource,deletable,main,extra)
            list=t2.itemize(table)
            if not list:
                list=s3.crud_strings.msg_list_empty
            title=s3.crud_strings.title_list
            subtitle=s3.crud_strings.subtitle_list
            if logged_in and listadd:
                # Display the Add form below List
                if deletable:
                    # Add extra column header to explain the checkboxes
                    if isinstance(list,TABLE):
                        list.insert(0,TR('',B('Delete?')))
                form=crud.create(table,onvalidation=onvalidation)
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
                    add_btn=A(s3.crud_strings.label_create_button,_href=URL(r=request,f=resource,args='create'),_id='add-btn')
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
            #list=crud.select(table,fields=fields,headers=headers)
            shn_represent(table,module,resource,deletable,main,extra)
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
            list=crud.select(table)
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
        elif representation=="rss":
            if request.env.remote_addr=='127.0.0.1':
                server='http://127.0.0.1:' + request.env.server_port
            else:
                server='http://' + request.env.server_name + ':' + request.env.server_port
            link='/%s/%s/%s' % (request.application,module,resource)
            entries=[]
            rows=db(table.id>0).select()
            for row in rows:
                entries.append(dict(title=row.name,link=server+link+'/%d' % row.id,description=row.description or '',created_on=row.created_on))
            import gluon.contrib.rss2 as rss2
            items = [ rss2.RSSItem(title = entry['title'], link = entry['link'], description = entry['description'], pubDate = entry['created_on']) for entry in entries]
            rss = rss2.RSS2(title = str(s3.crud_strings.subtitle_list), link = server+link+'/%d' % row.id, description = '', lastBuildDate = request.now, items = items)
            response.headers['Content-Type']='application/rss+xml'
            return rss2.dumps(rss)
        else:
            session.error=T("Unsupported format!")
            redirect(URL(r=request))
    else:
        if request.args[0].isdigit():
            # 1st argument is ID not method => Read.
            s3.id=request.args[0]
            if session.s3.audit_read:
                db.s3_audit.insert(
                    person=auth.user.id if logged_in else 0,
                    operation='read',
                    representation=representation,
                    module=request.controller,
                    resource=resource,
                    record=s3.id,
                    old_value='',
                    new_value=''
                )
            if representation=="html":
                item=crud.read(table,s3.id)
                # Check for presence of Custom View
                custom_view='%s_display.html' % resource
                _custom_view=os.path.join(request.folder,'views',module,custom_view)
                if os.path.exists(_custom_view):
                    response.view=module+'/'+custom_view
                else:
                    response.view='display.html'
                title=s3.crud_strings.title_display
                edit=A(T("Edit"),_href=URL(r=request,f=resource,args=['update',s3.id]),_id='edit-btn')
                if deletable:
                    delete=A(T("Delete"),_href=URL(r=request,f=resource,args=['delete',s3.id]),_id='delete-btn')
                else:
                    delete=''
                list_btn=A(s3.crud_strings.label_list_button,_href=URL(r=request,f=resource),_id='list-btn')
                return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,delete=delete,list_btn=list_btn)
            elif representation=="plain":
                item=crud.read(table,s3.id)
                response.view='plain.html'
                return dict(item=item)
            elif representation=="json":
                item=db(table.id==s3.id).select(table.ALL).json()
                response.view='plain.html'
                return dict(item=item)
            elif representation=="csv":
                import gluon.contenttype
                response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
                query=db[table].id==s3.id
                response.headers['Content-disposition']="attachment; filename=%s_%s_%d.csv" % (request.env.server_name,resource,s3.id)
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
                entries[0]=dict(title=table.name,link=URL(r=request,c='module',f='resource',args=[table.id]),description=table.description,created_on=table.created_on)
                item=service.rss(entries=entries)
                response.view='plain.html'
                return dict(item=item)
            else:
                session.error=T("Unsupported format!")
                redirect(URL(r=request))
        else:
            method=str.lower(request.args[0])
            try:
                s3.id=request.args[1]
            except:
                pass
            if method=="create":
                if logged_in:
                    if session.s3.audit_write:
                        audit_id=db.s3_audit.insert(
                            person=auth.user.id,
                            operation='create',
                            representation=representation,
                            module=request.controller,
                            resource=resource,
                            record=s3.id,
                            old_value='',
                            new_value=''
                        )
                    if representation=="html":
                        form=crud.create(table,onvalidation=onvalidation)
                        # Check for presence of Custom View
                        custom_view='%s_create.html' % resource
                        _custom_view=os.path.join(request.folder,'views',module,custom_view)
                        if os.path.exists(_custom_view):
                            response.view=module+'/'+custom_view
                        else:
                            response.view='create.html'
                        title=s3.crud_strings.title_create
                        list_btn=A(s3.crud_strings.label_list_button,_href=URL(r=request,f=resource),_id='list-btn')
                        return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                    elif representation=="plain":
                        form=crud.create(table,onvalidation=onvalidation)
                        response.view='plain.html'
                        return dict(item=form)
                    elif representation=="popup":
                        form=crud.create(table,onvalidation=onvalidation)
                        response.view='popup.html'
                        return dict(module_name=module_name,form=form,module=module,resource=resource,main=main,caller=request.vars.caller)
                    elif representation=="json":
                        record=Storage()
                        for var in request.vars:
                            if var=='format':
                                pass
                            else:
                                record[var] = request.vars[var]
                        item=''
                        for var in record:
                            # Validate request manually
                            if table[var].requires(record[var])[1]:
                                item+='{"Status":"failed","Error":{"StatusCode":403,"Message":"'+var+' invalid: '+table[var].requires(record[var])[1]+'"}}'
                        if item:
                            pass
                        else:
                            try:
                                id=table.insert(**dict (record))
                                item='{"Status":"success","Error":{"StatusCode":201,"Message":"Created as '+URL(r=request,c=module,f=resource,args=id)+'"}}'
                            except:
                                item='{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
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
                        redirect(URL(r=request))
                else:
                    redirect(URL(r=request,c='default',f='user',args='login',vars={'_next':URL(r=request,c=module,f=resource,args='create')}))
            elif method=="display" or method=="read":
                redirect(URL(r=request,args=s3.id))
            elif method=="update":
                if logged_in:
                    if session.s3.audit_write:
                        old_value = []
                        _old_value=db(db[table].id==s3.id).select()[0]
                        for field in _old_value:
                            old_value.append(field+':'+str(_old_value[field]))
                        audit_id=db.s3_audit.insert(
                            person=auth.user.id,
                            operation='update',
                            representation=representation,
                            module=request.controller,
                            resource=resource,
                            record=s3.id,
                            old_value=old_value,
                            new_value=''
                        )
                    if representation=="html":
                        form=crud.update(table,s3.id,onvalidation=onvalidation)
                        # Check for presence of Custom View
                        custom_view='%s_update.html' % resource
                        _custom_view=os.path.join(request.folder,'views',module,custom_view)
                        if os.path.exists(_custom_view):
                            response.view=module+'/'+custom_view
                        else:
                            response.view='update.html'
                        title=s3.crud_strings.title_update
                        list_btn=A(s3.crud_strings.label_list_button,_href=URL(r=request,f=resource),_id='list-btn')
                        return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                    elif representation=="plain":
                        form=crud.update(table,s3.id,onvalidation=onvalidation)
                        response.view='plain.html'
                        return dict(item=form)
                    elif representation=="json":
                        record=Storage()
                        uuid=0
                        for var in request.vars:
                            if var=='format':
                                pass
                            elif var=='uuid':
                                uuid=1
                            else:
                                record[var] = request.vars[var]
                        if uuid:
                            item=''
                            for var in record:
                                # Validate request manually
                                if table[var].requires(record[var])[1]:
                                    item+='{"Status":"failed","Error":{"StatusCode":403,"Message":"'+var+' invalid: '+table[var].requires(record[var])[1]+'"}}'
                            if item:
                                pass
                            else:
                                try:
                                    result=db(table.uuid==request.vars.uuid).update(**dict (record))
                                    if result:
                                        item='{"Status":"success","Error":{"StatusCode":200,"Message":"Record updated."}}'
                                    else:
                                        item='{"Status":"failed","Error":{"StatusCode":404,"Message":"Record '+request.vars.uuid+' does not exist."}}'
                                except:
                                    item='{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
                        else:
                            item='{"Status":"failed","Error":{"StatusCode":400,"Message":"UUID required!"}}'
                        response.view='plain.html'
                        return dict(item=item)
                    else:
                        session.error=T("Unsupported format!")
                        redirect(URL(r=request))
                else:
                    redirect(URL(r=request,c='default',f='user',args='login',vars={'_next':URL(r=request,c=module,f=resource,args=['update',s3.id])}))
            elif method=="delete":
                if logged_in:
                    if session.s3.audit_write:
                        old_value = []
                        _old_value=db(db[table].id==s3.id).select()[0]
                        for field in _old_value:
                            old_value.append(field+':'+str(_old_value[field]))
                        db.s3_audit.insert(
                            person=auth.user.id,
                            operation='delete',
                            representation=representation,
                            module=request.controller,
                            resource=resource,
                            record=s3.id,
                            old_value=old_value,
                            new_value=''
                        )
                    if representation=="ajax":
                        #crud.delete(table,s3.id,next='%s?format=ajax' % resource)
                        t2.delete(table,next='%s?format=ajax' % resource)
                    else:
                        crud.delete(table,s3.id)
                else:
                    redirect(URL(r=request,c='default',f='user',args='login',vars={'_next':URL(r=request,c=module,f=resource,args=['delete',s3.id])}))
            elif method=="search":
                if session.s3.audit_read:
                    db.s3_audit.insert(
                        person=auth.user.id if logged_in else 0,
                        operation='search',
                        module=request.controller,
                        resource=resource,
                        old_value='',
                        new_value=''
                    )
                if representation=="html":
                    shn_represent(table,module,resource,deletable,main,extra)
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
                if representation=="json":
                    if request.vars.field and request.vars.filter and request.vars.value:
                        field=str.lower(request.vars.field)
                        filter=str.lower(request.vars.filter)
                        if filter == '=':
                            query=(table['%s' % field]==request.vars.value)
                            item = db(query).select().json()
                        else:
                            item='{"Status":"failed","Error":{"StatusCode":501,"Message":"Unsupported filter! Supported filters: ="}}'
                    else:
                        item='{"Status":"failed","Error":{"StatusCode":501,"Message":"Search requires specifying Field, Filter & Value!"}}'
                    response.view='plain.html'
                    return dict(item=item)
                else:
                    session.error=T("Unsupported format!")
                    redirect(URL(r=request))
            else:
                session.error=T("Unsupported method!")
                redirect(URL(r=request))
