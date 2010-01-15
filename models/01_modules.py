# -*- coding: utf-8 -*-

module = 's3'

# Modules
s3_module_type_opts = {
    1:T('Home'),
    2:T('Situation Awareness'),
    3:T('Person Management'),
    4:T('Aid Management'),
    5:T('Communications')
    }
opt_s3_module_type = db.Table(None, 'opt_s3_module_type',
                    db.Field('module_type', 'integer', notnull=True,
                    requires = IS_IN_SET(s3_module_type_opts),
                    default = 1,
                    represent = lambda opt: opt and s3_module_type_opts[opt]))

resource = 'module'
table = module + '_' + resource
db.define_table(table,
                Field('name', length=32, notnull=True, unique=True),
                Field('name_nice', length=128, notnull=True, unique=True),
                opt_s3_module_type,
                Field('access'),  # Hide modules if users don't have the required access level (NB Not yet implemented either in the Modules menu or the Controllers)
                Field('priority', 'integer', notnull=True, unique=True),
                Field('description'),
                Field('enabled', 'boolean', default=True),
                migrate=migrate)
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name_nice.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name_nice' % table)]
db[table].access.requires = IS_NULL_OR(IS_IN_DB(db, 'auth_group.id', '%(role)s', multiple=True)) # IS_ONE_OF ignores multiple!
db[table].priority.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.priority' % table)]

# Set to False in Production
if db(db["s3_setting"].id).count():
    empty = False
else:
    empty = True

if empty:
    # Pre-populate database
    if not db(db[table].id).count():
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
            enabled='False'
        )
        db[table].insert(
            name="dvr",
            name_nice="Disaster Victim Registry",
            priority=5,
            module_type=3,
            access='',
            description="Traces internally displaced people (IDPs) and their needs",
            enabled='False'
        )
        db[table].insert(
            name="hrm",
            name_nice="Human Remains Management",
            priority=6,
            module_type=3,
            access='',
            description="Helps to manage human remains",
            enabled='False'
        )
        db[table].insert(
            name="dvi",
            name_nice="Disaster Victim Identification",
            priority=7,
            module_type=3,
            access='',
            description="Disaster Victim Identification",
            enabled='False'
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
            enabled='False'
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
            enabled='False'
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
            enabled='False'
        )
        db[table].insert(
            name="msg",
            name_nice="Messaging Module",
            priority=14,
            module_type=5,
            access='',
            description="Sends & Receives Alerts via Email & SMS",
            enabled='False'
        )
        db[table].insert(
            name="delphi",
            name_nice="Delphi Decision Maker",
            priority=15,
            module_type=4,
            access='',
            description="Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            enabled='False'
        )
        db[table].insert(
            name="media",
            name_nice="Media Manager",
            priority=16,
            module_type=4,
            access='',
            description="A library of digital resources, such as Photos.",
            enabled='False'
        )
        db[table].insert(
            name="nim",
            name_nice="Nursing Information Manager",
            priority=17,
            module_type=3,
            access='',
            description="Module to assist disaster nurses.",
            enabled='False'
        )


# Modules Menu (available in all Controllers)
s3.menu_modules = []
for module_type in [1, 2, 3, 4]:
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

response.menu = s3.menu_modules
response.menu.append(s3.menu_auth)
response.menu.append(s3.menu_help)
