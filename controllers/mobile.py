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
def setting():
    "Modem and Mobile related settings"
    try:
        import serial
    except:
        session.error = T('pyserial module not available within the running Python - this needs installing for SMS!')
        redirect(URL(r=request, c='mobile', f='index' ))
    module = 'mobile'
    resource = 'setting'
    table = module + '_' + resource

    # Model options
    db[table].port.comment = A(SPAN("[Help]"), _class="tooltip",
            _title=T("Port|The serial port where your modem is connected."))
    db[table].baud.comment = A(SPAN("[Help]"), _class="tooltip",
            _title=T("Baud|The Baud rate of your modem - Usually listed in your modem manual."))
    
    # CRUD Strings
    title_create = T('Add Setting')
    title_display = T('Setting Details')
    title_list = T('View Settings')
    title_update = T('Edit Mobile Settings')
    title_search = T('Search Settings')
    subtitle_list = T('Settings')
    label_list_button = T('View Settings')
    label_create_button = T('Add Setting')
    msg_record_created = T('Setting added')
    msg_record_modified = T('Mobile settings updated')
    msg_record_deleted = T('Setting deleted')
    msg_list_empty = T('No Settings currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

    crud.settings.update_next = URL(r=request, args=['update', 1])
    
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

