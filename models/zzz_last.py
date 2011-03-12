# -*- coding: utf-8 -*-

# File needs to be last in order to be able to have all Tables defined

# Populate dropdown
_tables = db.tables
db.auth_permission.table_name.requires = IS_IN_SET(_tables)
db.pr_pe_subscription.resource.requires = IS_IN_SET(_tables)
db.gis_feature_class.resource.requires = IS_IN_SET(_tables)
if deployment_settings.has_module("msg"):
    db.msg_tag.resource.requires = IS_IN_SET(_tables)
