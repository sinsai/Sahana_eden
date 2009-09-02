# -*- coding: utf-8 -*-

S3_PUBLIC_URL = 'http://127.0.0.1:8000'

# Default strings are in English
T.current_languages = ['en', 'en-en']

mail = Mail()
# These settings could be made configurable as part of the Messaging Module
# - however also need to be used by Auth (order issues), DB calls are overheads
# - as easy for admin to edit source here as to edit DB (although an admin panel can be nice)
mail.settings.server = 'mail:25'
#mail.settings.server = 'smtp.gmail.com:587'
#mail.settings.login = 'username:password'
mail.settings.sender = 'sahana@sahanapy.org'

auth = AuthS3(globals(),db)
auth.define_tables()
db.auth_user.password.requires = CRYPT(key='akeytochange')
auth.settings.expiration = 3600  # seconds
# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key='PUBLIC_KEY', private_key='PRIVATE_KEY')
# Require Email Verification
auth.settings.registration_requires_verification = False
# Email settings for registration verification
auth.settings.mailer = mail
auth.messages.verify_email = 'Click on the link ' + S3_PUBLIC_URL + '/verify_email/%(key)s to verify your email'
auth.settings.on_failed_authorization = URL(r=request, c='default', f='user', args='not_authorized')
# Require Admin approval for self-registered users
auth.settings.registration_requires_approval = False
# Notify UserAdmin of new pending user registration to action
# auth.settings.verify_email_onaccept = lambda form: auth.settings.mailer.send(to='adminwithapprovalpower@admindomain', subject='Sahana Login Approval Pending', message='Your action is required. Please approve user %s asap.' % form.email)
# Allow use of LDAP accounts for login
# NB Currently this means that change password should be disabled:
#auth.settings.actions_disabled.append('change_password')
# (NB These are not automatically added to PR or to Authenticated role since they enter via the login() method not register())
#from gluon.contrib.login_methods.ldap_auth import ldap_auth
# Require even alternate login methods to register users 1st
#auth.settings.alternate_requires_registration = True
# Active Directory
#auth.settings.login_methods.append(ldap_auth(mode='ad', server='dc.domain.org', base_dn='ou=Users,dc=domain,dc=org'))
# or if not wanting local users at all (no passwords saved within DB):
#auth.settings.login_methods = [ldap_auth(mode='ad', server='dc.domain.org', base_dn='ou=Users,dc=domain,dc=org')]
# Domino
#auth.settings.login_methods.append(ldap_auth(mode='domino', server='domino.domain.org'))
# OpenLDAP
#auth.settings.login_methods.append(ldap_auth(server='demo.sahanapy.org', base_dn='ou=users,dc=sahanapy,dc=org'))
# Allow use of Email accounts for login
#auth.settings.login_methods.append(email_auth("smtp.gmail.com:587", "@gmail.com"))
# We don't wish to clutter the groups list with 1 per user.
auth.settings.create_user_groups = False
# We need to allow basic logins for Webservices
auth.settings.allow_basic_login = True
# Logout session clearing
auth.settings.logout_onlogout = shn_auth_on_logout
auth.settings.login_onaccept = shn_auth_on_login

crud = CrudS3(globals(),db)
# Breaks refresh of List after Create: http://groups.google.com/group/web2py/browse_thread/thread/d5083ed08c685e34
#crud.settings.keepvalues = True

from gluon.tools import Service
service = Service(globals())

# Reusable timestamp fields
timestamp = SQLTable(None, 'timestamp',
            Field('created_on', 'datetime',
                          readable=False,
                          writable=False,
                          default=request.utcnow),
            Field('modified_on', 'datetime',
                          readable=False,
                          writable=False,
                          default=request.utcnow,
                          update=request.utcnow)
            ) 

# Reusable author fields
authorstamp = SQLTable(None, 'authorstamp',
            Field('created_by', db.auth_user,
                          writable=False,
                          default=session.auth.user.id if auth.is_logged_in() else 0,
                          represent = lambda id: (id and [db(db.auth_user.id==id).select()[0].first_name] or ["None"])[0],
                          ondelete='RESTRICT'),
            Field('modified_by', db.auth_user,
                          writable=False,
                          default=session.auth.user.id if auth.is_logged_in() else 0,
                          update=session.auth.user.id if auth.is_logged_in() else 0,
                          represent = lambda id: (id and [db(db.auth_user.id==id).select()[0].first_name] or ["None"])[0],
                          ondelete='RESTRICT')
            ) 

# Reusable UUID field (needed as part of database synchronization)
import uuid
uuidstamp = SQLTable(None, 'uuidstamp',
            Field('uuid', length=64,
                          notnull=True,
                          unique=True,
                          readable=False,
                          writable=False,
                          default=uuid.uuid4()))

# Reusable Deletion status field (needed as part of database synchronization)
# Q: Will this be moved to a separate table? (Simpler for module writers but a performance penalty)
deletion_status = SQLTable(None, 'deletion_status',
            Field('deleted', 'boolean',
                          readable=False,
                          writable=False,
                          default=False))

# Reusable Admin field
admin_id = SQLTable(None, 'admin_id',
            Field('admin', db.auth_group,
                requires = IS_NULL_OR(IS_IN_DB(db, 'auth_group.id', 'auth_group.role')),
                represent = lambda id: (id and [db(db.auth_group.id==id).select()[0].role] or ["None"])[0],
                comment = DIV(A(T('Add Role'), _class='popup', _href=URL(r=request, c='admin', f='group', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Admin|The Group whose members can edit data in this record."))),
                ondelete='RESTRICT'
                ))
    
from gluon.storage import Storage
# Keep all S3 framework-level elements stored off here, so as to avoid polluting global namespace & to make it clear which part of the framework is being interacted with
# Avoid using this where a method parameter could be used: http://en.wikipedia.org/wiki/Anti_pattern#Programming_anti-patterns
s3 = Storage()

s3.crud_strings = Storage()
s3.crud_strings.title_create = T('Add Record')
s3.crud_strings.title_display = T('Record Details')
s3.crud_strings.title_list = T('List Records')
s3.crud_strings.title_update = T('Edit Record')
s3.crud_strings.title_search = T('Search Records')
s3.crud_strings.subtitle_create = T('Add New Record')
s3.crud_strings.subtitle_list = T('Available Records')
s3.crud_strings.label_list_button = T('List Records')
s3.crud_strings.label_create_button = T('Add Record')
s3.crud_strings.msg_record_created = T('Record added')
s3.crud_strings.msg_record_modified = T('Record updated')
s3.crud_strings.msg_record_deleted = T('Record deleted')
s3.crud_strings.msg_list_empty = T('No Records currently available')

s3.display = Storage()

table = 'auth_user'
title_create = T('Add User')
title_display = T('User Details')
title_list = T('List Users')
title_update = T('Edit User')
title_search = T('Search Users')
subtitle_create = T('Add New User')
subtitle_list = T('Users')
label_list_button = T('List Users')
label_create_button = T('Add User')
msg_record_created = T('User added')
msg_record_modified = T('User updated')
msg_record_deleted = T('User deleted')
msg_list_empty = T('No Users currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

table = 'auth_group'
title_create = T('Add Role')
title_display = T('Role Details')
title_list = T('List Roles')
title_update = T('Edit Role')
title_search = T('Search Roles')
subtitle_create = T('Add New Role')
subtitle_list = T('Roles')
label_list_button = T('List Roles')
label_create_button = T('Add Role')
msg_record_created = T('Role added')
msg_record_modified = T('Role updated')
msg_record_deleted = T('Role deleted')
msg_list_empty = T('No Roles currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

table = 'auth_membership'
title_create = T('Add Membership')
title_display = T('Membership Details')
title_list = T('List Memberships')
title_update = T('Edit Membership')
title_search = T('Search Memberships')
subtitle_create = T('Add New Membership')
subtitle_list = T('Memberships')
label_list_button = T('List Memberships')
label_create_button = T('Add Membership')
msg_record_created = T('Membership added')
msg_record_modified = T('Membership updated')
msg_record_deleted = T('Membership deleted')
msg_list_empty = T('No Memberships currently defined')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Authorization
# User Roles (uses native Web2Py Auth Groups)
table = auth.settings.table_group_name
# 1st-run initialisation
if not len(db().select(db[table].ALL)):
    auth.add_group('Administrator', description = 'System Administrator - can access & make changes to any data')
    # Doesn't work on Postgres!
    auth.add_membership(1, 1) # 1st person created will be System Administrator (can be changed later)
    auth.add_group('Anonymous', description = 'Anonymous - dummy group to grant permissions')
    auth.add_group('Authenticated', description = 'Authenticated - all logged-in users')
    auth.add_group('Editor', description = 'Editor - can access & make changes to any unprotected data')
    
module = 's3'
# Auditing
# ToDo: consider using native Web2Py log to auth_events
resource = 'audit'
table = module + '_' + resource
db.define_table(table,timestamp,
                Field('person', db.auth_user, ondelete='RESTRICT'),
                Field('operation'),
                Field('representation'),
                Field('module'),
                Field('resource'),
                Field('record', 'integer'),
                Field('old_value'),
                Field('new_value'),
                migrate=migrate)
db[table].operation.requires = IS_IN_SET(['create', 'read', 'update', 'delete', 'list', 'search'])

# Settings - systemwide
s3_setting_security_policy_opts = {
    1:T('simple'),
    2:T('full')
    }
resource = 'setting'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                Field('admin_name'),
                Field('admin_email'),
                Field('admin_tel'),
                Field('debug', 'boolean', default=False),
                Field('security_policy', 'integer', default=1),
                Field('self_registration', 'boolean', default=True),
                Field('archive_not_delete', 'boolean', default=True),
                Field('audit_read', 'boolean', default=False),
                Field('audit_write', 'boolean', default=False),
                migrate=migrate)
db[table].security_policy.requires = IS_IN_SET(s3_setting_security_policy_opts)
db[table].security_policy.represent = lambda opt: opt and s3_setting_security_policy_opts[opt]
db[table].security_policy.label = T('Security Policy')
db[table].security_policy.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Security Policy|The simple policy allows anonymous users to Read & registered users to Edit. The full security policy allows the administrator to set permissions on individual tables or records - see models/zzz.py."))
db[table].debug.label = T('Debug')
db[table].debug.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Debug|Switch this on to use individual CSS/Javascript files for diagnostics during development."))
db[table].self_registration.label = T('Self Registration')
db[table].self_registration.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Self-registration|Can users register themselves for authenticated login access?"))
db[table].archive_not_delete.label = T('Archive not Delete')
db[table].archive_not_delete.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Archive not Delete|If this setting is enabled then all deleted records are just flagged as deleted instead of being really deleted. They will appear in the raw database access but won't be visible to normal users."))
db[table].audit_read.label = T('Audit Read')
db[table].audit_read.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Audit Read|If enabled then a log is maintained of all records a user accesses. If disabled then it can still be enabled on a per-module basis."))
db[table].audit_write.label = T('Audit Write')
db[table].audit_write.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Audit Write|If enabled then a log is maintained of all records a user edits. If disabled then it can still be enabled on a per-module basis."))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
    db[table].insert(
        admin_name = T("Sahana Administrator"),
        admin_email = T("support@Not Set"),
        admin_tel = T("Not Set")
    )
# Define CRUD strings (NB These apply to all Modules' 'settings' too)
title_create = T('Add Setting')
title_display = T('Setting Details')
title_list = T('List Settings')
title_update = T('Edit Setting')
title_search = T('Search Settings')
subtitle_create = T('Add New Setting')
subtitle_list = T('Settings')
label_list_button = T('List Settings')
label_create_button = T('Add Setting')
msg_record_created = T('Setting added')
msg_record_modified = T('Setting updated')
msg_record_deleted = T('Setting deleted')
msg_list_empty = T('No Settings currently defined')
s3.crud_strings[resource] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)

# Auth Menu (available in all Modules)
if not auth.is_logged_in():
    self_registration = db().select(db.s3_setting.self_registration)[0].self_registration
    if self_registration:
        response.menu_auth = [
            [T('Login'), False, URL(request.application, 'default', 'user/login'),
             [
                    [T('Register'), False,
                     URL(request.application, 'default', 'user/register')],
                    [T('Lost Password'), False,
                     URL(request.application, 'default', 'user/retrieve_password')]]
             ],
            ]
    else:
        response.menu_auth = [
            [T('Login'), False, URL(request.application, 'default', 'user/login'),
             [
                    [T('Lost Password'), False,
                     URL(request.application, 'default', 'user/retrieve_password')]]
             ],
            ]
else:
    response.menu_auth = [
        ['Logged-in as: ' + auth.user.first_name + ' ' + auth.user.last_name, False, None,
         [
                [T('Logout'), False, 
                 URL(request.application, 'default', 'user/logout')],
                [T('Edit Profile'), False, 
                 URL(request.application, 'default', 'user/profile')],
                [T('Change Password'), False,
                 URL(request.application, 'default', 'user/change_password')]]
         ],
        ]

        
# Modules
s3_module_type_opts = {
    1:T('Home'),
    2:T('Situation Awareness'),
    3:T('Person Management'),
    4:T('Aid Management'),
    5:T('Communications')
    }
opt_s3_module_type = SQLTable(None, 'opt_s3_module_type',
                    db.Field('module_type', 'integer', notnull=True,
                    requires = IS_IN_SET(s3_module_type_opts),
                    default = 1,
                    represent = lambda opt: opt and s3_module_type_opts[opt]))

resource = 'module'
table = module + '_' + resource
db.define_table(table,
                Field('name', notnull=True, unique=True),
                Field('name_nice', notnull=True, unique=True),
                opt_s3_module_type,
                Field('access'),  # Hide modules if users don't have the required access level (NB Not yet implemented either in the Modules menu or the Controllers)
                Field('priority', 'integer', notnull=True, unique=True),
                Field('description', length=256),
                Field('enabled', 'boolean', default=True),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name_nice.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name_nice' % table)]
db[table].access.requires = IS_NULL_OR(IS_IN_DB(db, 'auth_group.id', 'auth_group.role', multiple=True))
db[table].priority.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.priority' % table)]
# Populate table with Default modules
if not len(db().select(db[table].ALL)):
    db[table].insert(
        name="default",
        name_nice="Sahana Home",
        priority=0,
        module_type=1,
        access='',
        description="",
        enabled='True'
    )
    db[table].insert(
        name="admin",
        name_nice="Administration",
        priority=1,
        module_type=1,
        access='|1|',        # Administrator
        description="Site Administration",
        enabled='True'
    )
    db[table].insert(
        name="gis",
        name_nice="Mapping",
        priority=2,
        module_type=2,
        access='',
        description="Situation Awareness & Geospatial Analysis",
        enabled='True'
    )
    db[table].insert(
        name="pr",
        name_nice="Person Registry",
        priority=3,
        module_type=3,
        access='',
        description="Central point to record details on People",
        enabled='True'
    )
    db[table].insert(
        name="mpr",
        name_nice="Missing Persons Registry",
        priority=4,
        module_type=3,
        access='',
        description="Helps to report and search for Missing Persons",
        enabled='True'
    )
    db[table].insert(
        name="dvr",
        name_nice="Disaster Victim Registry",
        priority=5,
        module_type=3,
        access='',
        description="Traces internally displaced people (IDPs) and their needs",
        enabled='True'
    )
    db[table].insert(
        name="hrm",
        name_nice="Human Remains Management",
        priority=6,
        module_type=3,
        access='',
        description="Helps to manage human remains",
        enabled='True'
    )
    db[table].insert(
        name="dvi",
        name_nice="Disaster Victim Identification",
        priority=7,
        module_type=3,
        access='',
        description="Disaster Victim Identification",
        enabled='True'
    )
    db[table].insert(
        name="or",
        name_nice="Organization Registry",
        priority=8,
        module_type=4,
        access='',
        description="Lists 'who is doing what & where'. Allows relief agencies to coordinate their activities",
        enabled='True'
    )
    db[table].insert(
        name="cr",
        name_nice="Shelter Registry",
        priority=9,
        module_type=4,
        access='',
        description="Tracks the location, distibution, capacity and breakdown of victims in Shelters",
        enabled='True'
    )
    db[table].insert(
        name="vol",
        name_nice="Volunteer Registry",
        priority=10,
        module_type=4,
        access='',
        description="Manage volunteers by capturing their skills, availability and allocation",
        enabled='False'
    )
    db[table].insert(
        name="lms",
        name_nice="Logistics Management System",
        priority=11,
        module_type=4,
        access='',
        description="Several sub-modules that work together to provide for the management of relief and project items by an organization. This includes an intake system, a warehouse management system, commodity tracking, supply chain management, fleet management, procurement, financial tracking and other asset and resource management capabilities.",
        enabled='True'
    )
    db[table].insert(
        name="rms",
        name_nice="Request Management",
        priority=12,
        module_type=4,
        access='',
        description="Tracks requests for aid and matches them against donors who have pledged aid",
        enabled='False'
    )
    db[table].insert(
        name="budget",
        name_nice="Budgeting Module",
        priority=13,
        module_type=4,
        access='',
        description="Allows a Budget to be drawn up",
        enabled='True'
    )
    db[table].insert(
        name="msg",
        name_nice="Messaging Module",
        priority=14,
        module_type=5,
        access='',
        description="Sends & Receives Alerts via Email & SMS",
        enabled='True'
    )

# Modules Menu (available in all Controllers)
response.menu_modules = []
for module_type in [1, 2]:
    query = (db.s3_module.enabled=='Yes')&(db.s3_module.module_type==module_type)
    modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
    for module in modules:
        if not module.access:
            response.menu_modules.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
        else:
            authorised = False
            groups = re.split('\|', module.access)[1:-1]
            for group in groups:
                if auth.has_membership(group):
                    authorised = True
            if authorised == True:
                response.menu_modules.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
for module_type in [3, 4]:
    module_type_name = str(s3_module_type_opts[module_type])
    module_type_menu = ([T(module_type_name), False, '#'])
    modules_submenu = []
    query = (db.s3_module.enabled=='Yes')&(db.s3_module.module_type==module_type)
    modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
    for module in modules:
        if not module.access:
            modules_submenu.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
        else:
            authorised = False
            groups = re.split('\|', module.access)[1:-1]
            for group in groups:
                if auth.has_membership(group):
                    authorised = True
            if authorised == True:
                modules_submenu.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
    module_type_menu.append(modules_submenu)
    response.menu_modules.append(module_type_menu)
for module_type in [5]:
    query = (db.s3_module.enabled=='Yes')&(db.s3_module.module_type==module_type)
    modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
    for module in modules:
        if not module.access:
            response.menu_modules.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
        else:
            authorised = False
            groups = re.split('\|', module.access)[1:-1]
            for group in groups:
                if auth.has_membership(group):
                    authorised = True
            if authorised == True:
                response.menu_modules.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
                
# Settings - appadmin
module = 'appadmin'
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

admin_menu_options = [
    [T('Home'), False, URL(r=request, c='admin', f='index')],
    [T('Settings'), False, URL(r=request, c='admin', f='setting', args=['update', 1])],
    [T('User Management'), False, '#', [
        [T('Users'), False, URL(r=request, c='admin', f='user')],
        [T('Roles'), False, URL(r=request, c='admin', f='group')],
        #[T('Membership'), False, URL(r=request, c='admin', f='membership')]
    ]],
    [T('Database'), False, '#', [
        [T('Import'), False, URL(r=request, c='admin', f='import_data')],
        [T('Export'), False, URL(r=request, c='admin', f='export_data')],
        [T('Raw Database access'), False, URL(r=request, c='appadmin', f='index')]
    ]],
    [T('Synchronisation'), False, URL(r=request, c='sync', f='index'), [
            [T('Sync History'), False, URL(r=request, c='sync', f='history')],
            [T('Sync Partners'), False, URL(r=request, c='sync', f='partner')],
            [T('Sync Settings'), False, URL(r=request, c='sync', f='setting', args=['update', 1])]
    ]],
    [T('Edit Application'), False, URL(r=request, a='admin', c='default', f='design', args=['sahana'])],
    [T('Functional Tests'), False, URL(r=request, c='static', f='selenium', args=['core', 'TestRunner.html'], vars=dict(test='../tests/TestSuite.html', auto='true', resultsUrl=URL(r=request, c='admin', f='handleResults')))]
]