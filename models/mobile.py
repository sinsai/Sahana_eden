# -*- coding: utf-8 -*-

"""
    Mobile Messaging
"""

module = 'mobile'

# Settings
resource = 'settings'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('account_name'), # Nametag to remember account
                Field('modem_port'),
                Field('modem_baud', 'integer', default = 115200),
                Field('url', default =\
                'https://api.clickatell.com/http/sendmsg'),
                Field('parameters', default =\
                'user=yourusername&password=yourpassword&api_id=yourapiid'),
                Field('message_variable', 'string', default = 'text'),
                Field('to_variable', 'string', default = 'to'),
                Field('enabled', 'boolean', default = True),
#                Field('preference', 'integer', default = 5),
                migrate=migrate)
table.to_variable.label = T('To variable')
table.message_variable.label = T('Message variable')
table.modem_port.label = T('Port')
table.modem_baud.label = T('Baud')