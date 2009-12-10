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

response.menu = [
            #s3.menu_home,
            s3.menu_modules[0],
            s3.menu_modules[1],
            s3.menu_modules[2],
            s3.menu_modules[3],
            s3.menu_modules[4],
            s3.menu_auth,
            s3.menu_help,
        ]