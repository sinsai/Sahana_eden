module = 'admin'

# Menu Options
table = '%s_menu_option' % module
db.define_table(table,
                db.Field('name'),
                db.Field('function'),
                db.Field('description',length=256),
                db.Field('access'),  # Hide menu options if users don't have the required access level
                db.Field('priority','integer'),
                db.Field('enabled','boolean',default='True'))
db[table].name.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].name.requires = IS_NOT_EMPTY()
db[table].access.requires = IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role'))
db[table].priority.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]

if not len(db().select(db[table].ALL)):
	db[table].insert(
        name="Home",
        function="index",
        priority=0,
        description="Home",
        enabled='True'
	)
	db[table].insert(
        name="Database",
        function="database",
        access='Administrator',   # Administrator role only
        priority=1,
        description="View/Edit the Database directly (caution doesn't respect the framework rules!)",
        enabled='True'
	)
	db[table].insert(
        name="Import",
        function="import_data",
        access='Administrator',   # Administrator role only
        priority=2,
        description="Import data from CSV or JSON",
        enabled='True'
	)
	db[table].insert(
        name="Export",
        function="export_data",
        access='Administrator',   # Administrator role only
        priority=3,
        description="Export data to CSV or JSON",
        enabled='True'
	)
	db[table].insert(
        name="Site Admin",
        function="admin",
        access='Administrator',   # Administrator role only
        priority=9,
        description="Site Administration (Web2Py IDE)",
        enabled='True'
	)
	db[table].insert(
        name="Test",
        function="test",
        access='Administrator',   # Administrator role only
        priority=10,
        description="Functional Testing",
        enabled='True'
	)

# Settings
resource = 'setting'
table = module+'_'+resource
db.define_table(table,
                db.Field('audit_read','boolean'),
                db.Field('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )

