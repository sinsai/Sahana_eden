# -*- coding: utf-8 -*-

""" Human Resource Management

    @author: Dominic König

"""

prefix = "hrm"
if deployment_settings.has_module(prefix):

    # -----------------------------------------------------------------------------
    resourcename = "human_resource"
    tablename = "%s_%s" % (prefix, resourcename)

    table = db.define_table(tablename,
                            super_link(db.sit_resource), # res_id
                            super_link(db.sit_trackable), # track_id
                            person_id(),
                            migrate=migrate, *s3_meta_fields())

    s3xrc.model.configure(table,
                          super_entity=(db.sit_trackable, db.sit_resource)
                         )

    # -----------------------------------------------------------------------------
    resourcename = "skill"
    tablename = "%s_%s" % (prefix, resourcename)

    table = db.define_table(tablename,
                            migrate=migrate, *s3_meta_fields())

    # -----------------------------------------------------------------------------
    resourcename = "credential"
    tablename = "%s_%s" % (prefix, resourcename)

    table = db.define_table(tablename,
                            migrate=migrate, *s3_meta_fields())

    # -----------------------------------------------------------------------------
