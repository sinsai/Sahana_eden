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
#auth.settings.username_field = True
auth.settings.hmac_key = 'akeytochange'
auth.define_tables()
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
                requires = IS_NULL_OR(IS_ONE_OF(db, 'auth_group.id', '%(role)s')),
                represent = lambda id: (id and [db(db.auth_group.id==id).select()[0].role] or ["None"])[0],
                comment = DIV(A(T('Add Role'), _class='popup', _href=URL(r=request, c='admin', f='group', args='create', vars=dict(format='plain')), _target='top', _title=T('Add Role')), A(SPAN("[Help]"), _class="tooltip", _title=T("Admin|The Group whose members can edit data in this record."))),
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

module = 'admin'
resource = 'theme'
table = module + '_' + resource
db.define_table(table,
                Field('name'),
                Field('logo'),
                Field('footer'),
                Field('col_background'),    # ToDo: Colour selector
                Field('col_menu'),
                Field('col_highlight'),
                migrate=migrate)
db[table].name.label = T('Name')
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.comment = SPAN("*", _class="req")
db[table].logo.label = T('Logo')
db[table].logo.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Logo|Name of the file (& optional sub-path) located in static which should be used for the top-left image."))
db[table].footer.label = T('Footer')
db[table].footer.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Footer|Name of the file (& optional sub-path) located in views which should be used for footer."))
db[table].col_background.label = T('Background Colour')
db[table].col_background.requires = IS_HTML_COLOUR()
db[table].col_menu.label = T('Colour of dropdown menus')
db[table].col_menu.requires = IS_HTML_COLOUR()
db[table].col_highlight.label = T('Colour of selected menu items')
db[table].col_highlight.requires = IS_HTML_COLOUR()
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
    db[table].insert(
        name = T('Sahana Blue'),
        logo = 'img/sahanapy_logo.png',
        footer = 'footer.html',
        col_background = '336699',
        col_menu = '0066cc',
        col_highlight = '0077aa'
    )
    db[table].insert(
        name = T('Sahana Green'),
        logo = 'img/sahanapy_logo_green.png',
        footer = 'footer.html',
        col_background = '337733',
        col_menu = 'cc7722',
        col_highlight = '338833'
    )
# Define CRUD strings
title_create = T('Add Theme')
title_display = T('Theme Details')
title_list = T('List Themes')
title_update = T('Edit Theme')
title_search = T('Search Themes')
subtitle_create = T('Add New Theme')
subtitle_list = T('Themes')
label_list_button = T('List Themes')
label_create_button = T('Add Theme')
msg_record_created = T('Theme added')
msg_record_modified = T('Theme updated')
msg_record_deleted = T('Theme deleted')
msg_list_empty = T('No Themes currently defined')
s3.crud_strings[resource] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)

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
                Field('theme', db.admin_theme),
                Field('debug', 'boolean', default=False),
                Field('self_registration', 'boolean', default=True),
                Field('security_policy', 'integer', default=1),
                Field('archive_not_delete', 'boolean', default=True),
                Field('audit_read', 'boolean', default=False),
                Field('audit_write', 'boolean', default=False),
                migrate=migrate)
db[table].security_policy.requires = IS_IN_SET(s3_setting_security_policy_opts)
db[table].security_policy.represent = lambda opt: opt and s3_setting_security_policy_opts[opt]
db[table].security_policy.label = T('Security Policy')
db[table].security_policy.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Security Policy|The simple policy allows anonymous users to Read & registered users to Edit. The full security policy allows the administrator to set permissions on individual tables or records - see models/zzz.py."))
db[table].theme.label = T('Theme')
db[table].theme.requires = IS_IN_DB(db, 'admin_theme.id', 'admin_theme.name')
db[table].theme.represent = lambda name: db(db.admin_theme.id==name).select()[0].name
db[table].theme.comment = DIV(A(T('Add Theme'), _class='popup', _href=URL(r=request, c='admin', f='theme', args='create', vars=dict(format='plain')), _target='top', _title=T('Add Theme'))),
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
        admin_tel = T("Not Set"),
        theme = 1
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
    [T('Settings'), False, URL(r=request, c='admin', f='setting', args=['update', 1]), [
        [T('Themes'), False, URL(r=request, c='admin', f='theme')]
    ]],
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
    [T('Mobile'), False, URL(r=request, c='mobile', f='index'),[
            [T('Modem Settings'), False, URL(r=request, c='mobile', f='settings', args=['update', 1])]
    ]],
    [T('Edit Application'), False, URL(r=request, a='admin', c='default', f='design', args=['sahana'])],
    [T('Functional Tests'), False, URL(r=request, c='static', f='selenium', args=['core', 'TestRunner.html'], vars=dict(test='../tests/TestSuite.html', auto='true', resultsUrl=URL(r=request, c='admin', f='handleResults')))]
]
