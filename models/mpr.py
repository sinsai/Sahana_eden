# -*- coding: utf-8 -*-

""" MPR Missing Persons Registry

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "mpr"

if deployment_settings.has_module(module):

    #
    # Settings --------------------------------------------------------------------
    #
    resource = 'setting'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field('audit_read', 'boolean'),
                            Field('audit_write', 'boolean'),
                            migrate=migrate)

    # Missing Report ----------------------------------------------------------
    reporter = db.Table(None, "reporter",
                        FieldS3("reporter",
                                db.pr_person,
                                sortby=["first_name", "middle_name", "last_name"],
                                requires = IS_NULL_OR(IS_ONE_OF(db,
                                                "pr_person.id",
                                                shn_pr_person_represent)),
                                represent = lambda id: \
                                            (id and
                                            [shn_pr_person_represent(id)] or
                                            ["None"])[0],
                                comment = shn_person_comment,
                                ondelete = "RESTRICT"))

    resource = 'missing_report'
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            timestamp, uuidstamp, authorstamp, deletion_status,
                            person_id,
                            reporter,
                            migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True)

    s3xrc.model.configure(table,
        list_fields = [
            "id",
            "reporter"
        ])
