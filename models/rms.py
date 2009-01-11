module='rms'

# Menu Options
table='%s_menu_option' % module
db.define_table(table,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('access',db.t2_group),  # Hide menu options if users don't have the required access level
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s' % table].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.name' % table)]
db['%s' % table].function.requires=IS_NOT_EMPTY()
db['%s' % table].access.requires=IS_NULL_OR(IS_IN_DB(db,'t2_group.id','t2_group.name'))
db['%s' % table].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s.priority' % table)]

# Settings
resource='setting'
table=module+'_'+resource
db.define_table(table,
                SQLField('audit_read','boolean'),
                SQLField('audit_write','boolean'))
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db['%s' % table].ALL)): 
   db['%s' % table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read=False,
        audit_write=False
    )

