# -*- coding: utf-8 -*-

# File needs to be last in order to be able to have all Tables defined

# Populate dropdown
_tables = db.tables
db.auth_permission.table_name.requires = IS_IN_SET(_tables)
db.pr_pe_subscription.resource.requires = IS_IN_SET(_tables)
db.gis_feature_class.resource.requires = IS_IN_SET(_tables)
if deployment_settings.has_module("msg"):
    db.msg_tag.resource.requires = IS_IN_SET(_tables)

# If table settings such as field options depend on data in the database,
# the data they depend on may not be accessible at the time define_table
# is called, even if the data is already in the database -- the tables it's
# in may not yet have been defined. There may be other dependencies that
# prevent ordering tables such that the needed table is defined before the
# table whose definition uses its data (e.g. foreign key references).
# Fixups can be done here if they're generally applicable, or in controller
# prep functions.

# Set the field options that depend on the currently selected gis_config,
# and hence on a particular set of labels for the location hierarchy.
gis.set_config(session.s3.gis_config_id)