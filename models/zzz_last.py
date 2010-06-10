# -*- coding: utf-8 -*-

# File needs to be last in order to be able to have all Tables defined

# Populate dropdown
db.auth_permission.table_name.requires = IS_IN_SET(db.tables)

# MSG
s3msg = local_import("s3msg")
msg = s3msg.Msg(globals(), db, T, mail)
