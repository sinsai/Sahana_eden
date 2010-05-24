# -*- coding: utf-8 -*-

"""
    NIM Nursing Information Manager

    @author: nursix
"""

module = 'nim'
if shn_module_enable.get(module, False):

    # Settings
    resource = 'setting'
    table = module + '_' + resource
    db.define_table(table,
                    Field('audit_read', 'boolean'),
                    Field('audit_write', 'boolean'),
                    migrate=migrate)

    # *****************************************************************************
    #
    def shn_nim_represent_user(id):

        table = auth.settings.table_user

        if id:
            user = db(table.id==id).select(table.first_name, table.last_name)
            if user:
                user = user[0]
                name = user.first_name
                if user.last_name:
                    name = "%s %s" % (name, user.last_name)
                return name

        return None

    user_id = SQLTable(None, 'user_id',
                    Field('user_id', auth.settings.table_user,
                            requires = IS_NULL_OR(IS_ONE_OF(db, auth.settings.table_user.id, shn_nim_represent_user)),
                            represent = lambda id: (id and [shn_nim_represent_user(id)] or ["None"])[0],
                            ondelete = 'RESTRICT',
                            label = T('Nurse')
                            )
                    )

    if auth.user is not None:
        user_id.user_id.default = auth.user.id

    # *****************************************************************************
    # Anamnesis: General
    #
    nim_care_strategy_opts = {
        1: T("Counselling"),
        2: T("Assisted Self-care"),
        3: T("Family Care"),
        4: T("Assisted Family Care"),
        5: T("Professional Care"),
        6: T("Medical Attention"),
        7: T("On-site Hospitalization"),
        8: T("Evacuation"),
        99: T("Self-care")
    }

    resource = 'anamnesis'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        user_id,
                        shelter_id,
                        Field('opt_nim_care_strategy',
                            'integer',
                            requires = IS_IN_SET(nim_care_strategy_opts),
                            default = 99,
                            label = T('Care Strategy'),
                            represent = lambda opt: nim_care_strategy_opts.get(opt, UNKNOWN_OPT)),
                        Field('lang_spoken'),
                        Field('lang_understood'),
                        Field('lang_comment'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=False,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'opt_nim_care_strategy'])

    # *****************************************************************************
    # Anamnesis: Disabilities
    #
    resource = 'disabilities'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('disabilities'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=False,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'disabilities'])

    # *****************************************************************************
    # Anamnesis: Diseases
    #
    resource = 'diseases'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('diseases'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=False,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'diseases'])

    # *****************************************************************************
    # Anamnesis: Injuries
    #
    resource = 'injuries'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('injuries'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=False,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'injuries'])

    # *****************************************************************************
    # Anamnesis: Treatments
    #
    resource = 'treatments'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('treatments'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=False,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'treatments'])

    # *****************************************************************************
    # Status, physical
    #
    resource = 'care_status_physical'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        user_id,                            # Nurse
                        Field('time', 'datetime'),          # Timestamp
                        Field('status', 'text'),
                        migrate=migrate)

    db[table].person_id.label = T("Person")

    db[table].time.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
    db[table].time.represent = lambda value: shn_as_local_time(value)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'user_id', 'time'])

    # *****************************************************************************
    # Care Status: Mental
    #
    resource = 'care_status_mental'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('status', 'text'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id'])

    # *****************************************************************************
    # Care Status: Social
    #
    resource = 'care_status_social'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('status', 'text'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id'])

    # *****************************************************************************
    # Care Report: Planning
    #
    resource = 'care_report_problems'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('problems', 'text'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id'])

    # *****************************************************************************
    # Care Report: Measures
    #
    resource = 'care_report_measures'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('time', 'datetime'),
                        Field('measures', length=256),
                        Field('report', 'text'),
                        migrate=migrate)

    db[table].time.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
    db[table].time.represent = lambda value: shn_as_local_time(value)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id', 'time', 'measures'])

    # *****************************************************************************
    # Care Report: Planning
    #
    resource = 'care_report_planning'
    table = module + '_' + resource
    db.define_table(table, timestamp, uuidstamp, deletion_status,
                        person_id,                          # Person ID
                        Field('planning', 'text'),
                        migrate=migrate)

    # Component
    s3xrc.model.add_component(module, resource,
        multiple=False,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        list_fields = ['id'])

    # *****************************************************************************
    # Functions


    # *****************************************************************************
