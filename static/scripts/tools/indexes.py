#
# Script to create database Indexes
#
# - should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
#
# - designed to be run within the web2py environment
#   cd /path/to/web2py
#   python web2py.py -S eden -M -R applications/eden/static/scripts/tools/indexes.py
#
# - normally run from fabfile.py as part of the upgrade cycle for instances
#

tablename = "pr_person"
field = "first_name"
db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
field = "middle_name"
db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
field = "last_name"
db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

tablename = "gis_location"
field = "name"
db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
