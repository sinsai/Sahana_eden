module='dvr'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.auth_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db[table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db[table].function.requires=IS_NOT_EMPTY()
db[table].access.requires=IS_NULL_OR(IS_IN_DB(db,'auth_group.id','auth_group.role'))
db[table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]

# Settings
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

