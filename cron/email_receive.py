# -*- coding: utf-8 -*-

server = db(db.msg_setting.id==1).select()[0].inbound_mail_server
server_type = db(db.msg_setting.id==1).select()[0].inbound_mail_type
port = db(db.msg_setting.id==1).select()[0].inbound_mail_port
login = db(db.msg_setting.id==1).select()[0].inbound_mail_login
password = db(db.msg_setting.id==1).select()[0].inbound_mail_password

if server_type == pop3:
    import poplib
    # http://docs.python.org/library/poplib.html
    
elif server_type == imap:
    import imaplib
    # http://docs.python.org/library/imaplib.html
    