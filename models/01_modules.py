# -*- coding: utf-8 -*-

"""
    Module configuration
"""

module = 's3'

# Model enablement
# Attention: this enables/disables model code, not modules!
# If you disable a model, you need to disable the respective
# controllers separately (you can use this variable to check)!
#
shn_module_enable = {
    "gis" : True,               # GIS
    "media": True,              # Media Manager
    "pr" : True,                # Person Registry
    "pr_ext" : True,            # Person Registry Extensions
    "or" : True,                # Organisation Registry
    "lms" : False,              # Logistics
    "budget" : True,            # Budgetting
    "cr" : True,                # Camp Registry
    "delphi" : True,            # Delphi Decision Maker
    "dvi" : True,               # Disaster Victim Identification
    "dvr" : True,               # Disaster Victim Registry
    "hms" : True,               # Hospital Management
    "hrm" : True,               # Human Resources Management
    "mpr" : True,               # Missing Person Registry
    "msg" : True,               # Messaging
    "nim" : False,              # Nursing Information Manager
    "rms" : True,               # Request Management
    "ticket" : True,            # Ticketing
    "vol" : True                # Volunteer Management
}

# Modules
s3_module_type_opts = {
    1:T('Home'),
    2:T('Situation Awareness'),
    3:T('Person Management'),
    4:T('Aid Management'),
    5:T('Communications')
    }
opt_s3_module_type = db.Table(None, 'opt_s3_module_type',
                    Field('module_type', 'integer', notnull=True,
                    requires = IS_IN_SET(s3_module_type_opts),
                    # default = 1,
                    represent = lambda opt: s3_module_type_opts.get(opt, T('Unknown'))))

resource = 'module'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('name', length=32, notnull=True, unique=True),
                Field('name_nice', length=128, notnull=True, unique=True),
                opt_s3_module_type,
                Field('access'),  # Hide modules if users don't have the required access level (NB Not yet implemented either in the Modules menu or the Controllers)
                Field('priority', 'integer', notnull=True, unique=True),
                Field('description'),
                Field('enabled', 'boolean', default=True),
                migrate=migrate)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 's3_module.name')]
table.name_nice.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 's3_module.name_nice')]
table.access.requires = IS_NULL_OR(IS_IN_DB(db, 'auth_group.id', '%(role)s', multiple=True))
table.priority.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 's3_module.priority')]

# Set to False in Production
if db(db["s3_setting"].id>0).count():
    empty = False
else:
    empty = True

if empty:
    # Pre-populate database
    if not db(table.id>0).count():
        table.insert(
            name="default",
            name_nice="Sahana Home",
            priority=0,
            module_type=1,
            access='',
            description="",
            enabled='True' # can't disable
        )
        table.insert(
            name="admin",
            name_nice="Administration",
            priority=1,
            module_type=1,
            access='|1|',        # Administrator
            description="Site Administration",
            enabled='True' # can't disable
        )
        table.insert(
            name="gis",
            name_nice="Mapping",
            priority=2,
            module_type=2,
            access='',
            description="Situation Awareness & Geospatial Analysis",
            enabled=shn_module_enable.get('gis', False)
        )
        table.insert(
            name="media",
            name_nice="Media Manager",
            priority=16,
            module_type=4,
            access='',
            description="A library of digital resources, such as Photos.",
            enabled=shn_module_enable.get('media', False)
        )
        table.insert(
            name="pr",
            name_nice="Person Registry",
            priority=3,
            module_type=3,
            access='',
            description="Central point to record details on People",
            enabled=shn_module_enable.get('pr', False)
        )
        table.insert(
            name="or",
            name_nice="Organization Registry",
            priority=8,
            module_type=4,
            access='',
            description="Lists 'who is doing what & where'. Allows relief agencies to coordinate their activities",
            enabled=shn_module_enable.get('or', False)
        )
        table.insert(
            name="lms",
            name_nice="Logistics Management System",
            priority=11,
            module_type=4,
            access='',
            description="Several sub-modules that work together to provide for the management of relief and project items by an organization. This includes an intake system, a warehouse management system, commodity tracking, supply chain management, fleet management, procurement, financial tracking and other asset and resource management capabilities.",
            enabled=shn_module_enable.get('lms', False)
        )
        table.insert(
            name="mpr",
            name_nice="Missing Persons Registry",
            priority=4,
            module_type=3,
            access='',
            description="Helps to report and search for Missing Persons",
            enabled=shn_module_enable.get('mpr', False)
        )
        table.insert(
            name="dvr",
            name_nice="Disaster Victim Registry",
            priority=5,
            module_type=3,
            access='',
            description="Traces internally displaced people (IDPs) and their needs",
            enabled=shn_module_enable.get('dvr', False)
        )
        table.insert(
            name="hrm",
            name_nice="Human Resources",
            priority=6,
            module_type=4,
            access='',
            description="Helps to manage human resources",
            enabled=shn_module_enable.get('hrm', False)
        )
        table.insert(
            name="dvi",
            name_nice="Disaster Victim Identification",
            priority=7,
            module_type=3,
            access='',
            description="Disaster Victim Identification",
            enabled=shn_module_enable.get('dvi', False)
        )
        table.insert(
            name="cr",
            name_nice="Shelter Registry",
            priority=9,
            module_type=4,
            access='',
            description="Tracks the location, distibution, capacity and breakdown of victims in Shelters",
            enabled=shn_module_enable.get('cr', False)
        )
        table.insert(
            name="vol",
            name_nice="Volunteer Registry",
            priority=10,
            module_type=4,
            access='',
            description="Manage volunteers by capturing their skills, availability and allocation",
            enabled=shn_module_enable.get('vol', False)
        )
        table.insert(
            name="rms",
            name_nice="Request Management",
            priority=12,
            module_type=4,
            access='',
            description="Tracks requests for aid and matches them against donors who have pledged aid",
            enabled=shn_module_enable.get('rms', False)
        )
        table.insert(
            name="budget",
            name_nice="Budgeting Module",
            priority=13,
            module_type=4,
            access='',
            description="Allows a Budget to be drawn up",
            enabled=shn_module_enable.get('budget', False)
        )
        table.insert(
            name="msg",
            name_nice="Messaging Module",
            priority=14,
            module_type=5,
            access='',
            description="Sends & Receives Alerts via Email & SMS",
            enabled=shn_module_enable.get('msg', False)
        )
        table.insert(
            name="delphi",
            name_nice="Delphi Decision Maker",
            priority=15,
            module_type=4,
            access='',
            description="Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            enabled=shn_module_enable.get('delphi', False)
        )
        table.insert(
            name="nim",
            name_nice="Nursing Information Manager",
            priority=17,
            module_type=3,
            access='',
            description="Module to assist disaster nurses.",
            enabled=shn_module_enable.get('nim', False)
        )
        table.insert(
            name="hms",
            name_nice="Hospital Management",
            priority=18,
            module_type=4,
            access='',
            description="Helps to monitor status of hospitals",
            enabled=shn_module_enable.get('hms', False)
        )
        table.insert(
            name="ticket",
            name_nice="Ticketing Module",
            priority=19,
            module_type=4,
            access='',
            description="Master Message Log to process incoming reports & requests",
            enabled=shn_module_enable.get('ticket', False)
        )

# Modules Menu (available in all Controllers)
s3.menu_modules = []
for module_type in [1, 2]:
    query = (db.s3_module.enabled=='Yes') & (db.s3_module.module_type==module_type)
    modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
    for module in modules:
        if not module.access:
            s3.menu_modules.append([module.name_nice, False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
        else:
            authorised = False
            groups = re.split('\|', module.access)[1:-1]
            for group in groups:
                if auth.has_membership(group):
                    authorised = True
            if authorised == True:
                s3.menu_modules.append([module.name_nice, False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
for module_type in [3, 4]:
    module_type_name = str(s3_module_type_opts[module_type])
    module_type_menu = ([module_type_name, False, '#'])
    modules_submenu = []
    query = (db.s3_module.enabled=='Yes') & (db.s3_module.module_type==module_type)
    modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
    for module in modules:
        if not module.access:
            modules_submenu.append([module.name_nice, False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
        else:
            authorised = False
            groups = re.split('\|', module.access)[1:-1]
            for group in groups:
                if auth.has_membership(group):
                    authorised = True
            if authorised == True:
                modules_submenu.append([module.name_nice, False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
    module_type_menu.append(modules_submenu)
    s3.menu_modules.append(module_type_menu)
for module_type in [5]:
    query = (db.s3_module.enabled=='Yes') & (db.s3_module.module_type==module_type)
    modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
    for module in modules:
        if not module.access:
            s3.menu_modules.append([module.name_nice, False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
        else:
            authorised = False
            groups = re.split('\|', module.access)[1:-1]
            for group in groups:
                if auth.has_membership(group):
                    authorised = True
            if authorised == True:
                s3.menu_modules.append([module.name_nice, False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])

#s3.menu_home = [T('Home'), False, URL(request.application, 'default', 'index'), s3.menu_modules]
#response.menu = [
#            s3.menu_home,
#            s3.menu_auth,
#            s3.menu_help,
#        ]
response.menu = s3.menu_modules
response.menu.append(s3.menu_auth)
response.menu.append(s3.menu_help)
