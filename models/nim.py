# -*- coding: utf-8 -*-

#
# NIM Nursing Information Manager
#
# created 2009-12-07 by nursix
#

module = 'nim'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
