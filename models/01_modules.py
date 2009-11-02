# -*- coding: utf-8 -*-

module = 's3'
resource = 'module'
table = module + '_' + resource
db.define_table(table,
                Field('name', notnull=True, unique=True),
                Field('name_nice', notnull=True, unique=True),
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
    db[table].insert(
        name="delphi",
        name_nice="Delphi Decision Maker",
        priority=15,
        module_type=4,
        access='',
        description="Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
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

# Test
#response.menu_modules = []
#module_type_menu = ([T('Modules'), False, '#'])
#modules_submenu = []
#query = db.s3_module.enabled=='Yes'
#modules = db(query).select(db.s3_module.ALL, orderby=db.s3_module.priority)
#for module in modules:
#    if not module.access:
#        modules_submenu.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
#    else:
#        authorised = False
#        groups = re.split('\|', module.access)[1:-1]
#        for group in groups:
#            if auth.has_membership(group):
#                authorised = True
#        if authorised == True:
#            modules_submenu.append([T(module.name_nice), False, URL(r=request, c='default', f='open_module', vars=dict(id='%d' % module.id))])
#module_type_menu.append(modules_submenu)
#response.menu_modules.append(module_type_menu)
