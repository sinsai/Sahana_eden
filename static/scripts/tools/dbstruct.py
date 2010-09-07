#
# Recommended usage:
# 1. Create a new, empty MySQL database 'sahana' as-normal
#     mysqladmin -u root -p create sahana
#     mysql -u root -p
#      GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,INDEX,ALTER,DROP ON sahana.* TO 'sahana'@'localhost' IDENTIFIED BY 'password';
#
# 2. set deployment_settings.base.prepopulate = False in models/000_config.py
#
# 3. Allow web2py to run the Eden model to configure the Database structure
#     web2py -S eden -M
#
# 4. Export the Live database from the Live server (including structure)
#     mysqldump -u root -p sahana > backup.sql
#
# 5. Use this to populate a new table 'old'
#     mysqladmin -u root -p create old
#     mysql -u root -p old < backup.sql
#
# 6. Change database names/passwords in the script &/or access rights in the table, as-appropriate
#     mysql -u root -p
#      GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,INDEX,ALTER,DROP ON old.* TO 'sahana'@'localhost' IDENTIFIED BY 'password';
#
# 7. Run the script
#     python dbstruct.py
#
# 8. Fixup manually anything which couldn't be done automatically, e.g.:
#     "ALTER TABLE `gis_location` DROP `marker_id` ;
#      The table -> gis_location has a field -> marker_id that could not be automatically removed"
#     =>
#     mysql -u root -p
#      \r old
#      show innodb status;
#      ALTER TABLE gis_location DROP FOREIGN KEY gis_location_ibfk_2;
#      ALTER TABLE gis_location DROP marker_id ;
#      ALTER TABLE gis_location DROP osm_id ;
#
# 9. Take a dump of the fixed data (no structure, full inserts)
#     mysqldump -tc -u root -p old > old.sql
#
# 10. Import it into the empty database
#      mysql -u root -p sahana < old.sql
#
# 11. Dump the final database with good structure/data ready to import on the server (including structure)
#      mysqldump -u root -p sahana > new.sql
#
# 12. Import it on the Server
#      mysqladmin -u root -p drop sahana
#      mysqladmin -u root -p create sahana
#      mysql -u root -p sahana < new.sql
#
# 13. Restore indexes
#      w2p
#       tablename = "pr_person"
#       field = "first_name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#       field = "middle_name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#       field = "last_name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#       tablename = "gis_location"
#       field = "name"
#       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
#

import MySQLdb

# DB1 is the db to sync to (Test)
# a plain structure export of the new db schema
db1 = MySQLdb.connection(host="localhost", user="sahana", passwd="password", db="sahana")

# DB2 is the db to sync from (Live)
# the complete db (structure & data)
db2 = MySQLdb.connection(host="localhost", user="sahana", passwd="password", db="old")

def tablelist(db):
    db.query("SHOW TABLES;")
    r = db.store_result()
    tables = []
    for row in r.fetch_row(300):
        tables.append(row[0])
    return tables

# Dict to load up the database Structure
def tablestruct(db):
    tablestruct = {}
    tables = tablelist(db)
    for table in tables:
        db.query("describe " + table + ";")
        r = db.store_result()
        structure = []
        for row in r.fetch_row(100):
            structure.append(row[0])
        tablestruct[table] = structure
    return tablestruct

struct1 = tablestruct(db1)
struct2 = tablestruct(db2)
tables_to_delete = []
fields_to_delete = {}
for key in struct2:
    fields_to_delete[key] = []
    try:
        fields1 = struct1[key]
        fields2 = struct2[key]
        for field in fields2:
            try:
                fields1.index(field)
            except:
                fields_to_delete[key].append(field)

    except:
        tables_to_delete.append(key)

for table in fields_to_delete.keys():
    if fields_to_delete[table] == []:
        del fields_to_delete[table]

print tables_to_delete
print fields_to_delete

for table in tables_to_delete:
    db2.query("SET FOREIGN_KEY_CHECKS = 0;")
    db2.query("drop table " + table + ";")
    db2.query("SET FOREIGN_KEY_CHECKS = 1;")

for table in fields_to_delete:
    for field in fields_to_delete[table]:
        try:
            db2.query("SET FOREIGN_KEY_CHECKS = 0;")
            print "ALTER TABLE `" + table + "` DROP `" + field + "` ;"
            db2.query("ALTER TABLE `" + table + "` DROP  `" + field + "` ;")
            db2.query("SET FOREIGN_KEY_CHECKS = 1;")
        except:
            print "The table -> " + table + " has a field -> " + field + " that could not be automatically removed"
