module='importer'
resource='slist'
table=module+'_'+resource
db.define_table(table,timestamp, uuidstamp,Field('Name',length=128,notnull=True),
            Field('Path',type='upload',uploadfield=True))
