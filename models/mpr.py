# -*- coding: utf-8 -*-

"""
    MPR Missing Person Registry (Sahana Legacy)
"""

module = "mpr"
if module in deployment_settings.modules:

    #
    # Settings --------------------------------------------------------------------
    #
    resource = 'setting'
    table = module + '_' + resource
    db.define_table(table,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    migrate=migrate)

    #
    # Missing Person --------------------------------------------------------------
    #

    resource = 'missing_person'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                    pr_pe_fieldset,
                    migrate=migrate)

    # Hide label
    db[table].pr_pe_label.readable=False
    db[table].pr_pe_label.writable=False

    ADD_PERSON = T('Add Person')
    LIST_PEOPLE = T('List People')
    s3.crud_strings[table] = Storage(
        title_create = ADD_PERSON,
        title_display = T('Person Details'),
        title_list = LIST_PEOPLE,
        title_update = T('Edit Person'),
        title_search = T('Search People'),
        subtitle_create = T('Add New Person'),
        subtitle_list = T('People'),
        label_list_button = LIST_PEOPLE,
        label_create_button = ADD_PERSON,
        msg_record_created = T('Person added'),
        msg_record_modified = T('Person updated'),
        msg_record_deleted = T('Person deleted'),
        msg_list_empty = T('No People currently registered'))

    resource = 'missing_report'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                    migrate=migrate)
