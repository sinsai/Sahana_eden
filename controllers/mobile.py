# -*- coding: utf-8 -*-

module = 'admin'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
# - can Insert/Delete items from default menus within a function, if required.
response.menu_options = admin_menu_options

# Web2Py Tools functions
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # Sync webservices don't use sessions, so avoid cluttering up the storage
    session.forget()
    return service()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@auth.requires_membership('Administrator')
def settings():
    "Modem and Mobile related settings"
    db.mobile_settings.port.comment = A(SPAN("[Help]"), _class="tooltip",
            _title=T("Port|The serial port where your modem is connected."))
    db.mobile_settings.baud.comment = A(SPAN("[Help]"), _class="tooltip",
            _title=T("Baud|The Baud rate of your modem - Usually listed in your modem manual."))
    title_update = T('Edit mobile settings')
    label_list_button = None
    msg_record_modified = T('Mobile settings updated')
    s3.crud_strings.mobile_settings = Storage(title_update=title_update,label_list_button=label_list_button,msg_record_modified=msg_record_modified)    
    crud.settings.update_next = URL(r=request, args=['update', 1])
    return shn_rest_controller('mobile', 'settings', deletable=False, listadd=False)

