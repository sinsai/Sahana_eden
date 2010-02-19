# -*- coding: utf-8 -*-

#
# DVR Disaster Victim Registry (Sahana Legacy)
#
# created 2009-08-06 by nursix
#

module = 'dvr'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)
