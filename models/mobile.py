# -*- coding: utf-8 -*-

"""
    Mobile Messaging
"""

module = 'mobile'

# Settings
resource = 'setting'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('port'),                              # Port for the modem
                Field('baud', 'integer', default = 115200), # Modem Baud rate
                Field('account_name'), # Nametag to remember account
                Field('url', default = 'https://api.clickatell.com/http/sendmsg'), # URL for Clickatell
                Field('ip', default = ''), # [Optional] IP address for the server
                Field('user'), # Clickatell account username
                Field('api_id', 'integer', default = ''), # Clickatell generated s/http id
                Field('password', 'string', default = ''), # Clickatell password
                Field('sender_num', 'integer', default = ''), # Sender phone number
                migrate=migrate)

# SMS store for persistence and scratch pad for combining incoming xform chunks
resource = 'store'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('sender','string', length = 20),
                Field('fileno','integer'),
                Field('totalno','integer'),
                Field('partno','integer'),
                Field('message','string', length = 160),
            migrate=migrate)
