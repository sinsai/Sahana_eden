# -*- coding: utf-8 -*-

# File needs to be last in order to be able to have all Tables defined

# Populate dropdown
_tables = db.tables
db.auth_permission.table_name.requires = IS_IN_SET(_tables)
db.pr_pe_subscription.resource.requires = IS_IN_SET(_tables)
db.gis_feature_class.resource.requires = IS_IN_SET(_tables)
db.msg_tag.resource.requires = IS_IN_SET(_tables)

# Which tables have GIS Locations
tables = []
for table in db.tables:
    if "location_id" in db[table]:
        tables.append(table)
db.gis_feature_layer.resource.requires = IS_NULL_OR(IS_IN_SET(tables))

# MSG
s3msg = local_import("s3msg")
msg = s3msg.Msg(globals(), db, T, mail)
