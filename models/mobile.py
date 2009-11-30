# -*- coding: utf-8 -*-

module = 'mobile'

# Settings
resource = 'settings'
table = module + '_' + resource
db.define_table(table,
                Field('port'),                              # Port for the modem
                Field('baud', 'integer', default = 115200), # Modem Baud rate
                migrate=migrate)
# Populate default values
if not len(db().select(db[table].ALL)):
   db[table].insert(baud=115200)
