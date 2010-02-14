# -*- coding: utf-8 -*-

module = 'mobile'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('port'),                              # Port for the modem
                Field('baud', 'integer', default = 115200), # Modem Baud rate
                migrate=migrate)
