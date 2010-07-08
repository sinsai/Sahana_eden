module='importer'
resource='slist'
table=module+'_'+resource
db.define_table(table,timestamp, uuidstamp,Field('Name',required=True,notnull=True),Field('Path',type='upload',uploadfield=True,required=True,notnull=True),Field('json',writable=False,readable=False),migrate=True)
