# -*- coding: utf-8 -*-

# Security Model

# FIle needs to be last in order to be able to have all Tables defined

# Populate dropdown
db.auth_permission.table_name.requires = IS_IN_SET(db.tables)

# Defaults for all tables
# For performance we only populate this once (at system startup)
# => need to populate manually when adding new tables to the database! (less RAD)
table = auth.settings.table_permission_name
if not len(db().select(db[table].ALL)):
    authenticated = auth.id_group('Authenticated')
    editors = auth.id_group('Editor')
    for table in db.tables:
        # allow all registered users the ability to Read all records
        auth.add_permission(authenticated, 'read', db[table])
        # allow anonymous users the ability to Read all records
        #auth.add_permission(anonymous, 'read', db[table])
        # Editors can make changes
        auth.add_permission(editors, 'create', db[table])
        auth.add_permission(editors, 'update', db[table])
        auth.add_permission(editors, 'delete', db[table])

    # Module-specific defaults can be set here
    #table = pr_person
    # Clear out defaults
    #auth.del_permission(authenticated, 'read', db[table])
    #auth.del_permission(editors, 'create', db[table])
    #auth.del_permission(editors, 'update', db[table])
    #auth.del_permission(editors, 'delete', db[table])
    # Add specific Role(s)
    #id = auth.id_group('myrole')
    #auth.add_permission(id, 'read', db[table])
    #auth.add_permission(id, 'create', db[table])
    #auth.add_permission(id, 'update', db[table])
    #auth.add_permission(id, 'delete', db[table])
