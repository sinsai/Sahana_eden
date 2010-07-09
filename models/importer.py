module='importer'
resource='slist'

table=module+'_'+resource

s3.crud_strings[table]= Storage(
		title_create = T("Upload a spreadsheet"),
		title_list = T("List of spreadsheets uploaded"),
		label_list_button = T("List of spreadsheets"),
		#msg_record_created = T("Spreadsheet uploaded")
		)

db.define_table(table,timestamp, uuidstamp,
		Field('Name',required=True,notnull=True),
		Field('Path',type='upload',uploadfield=True,required=True,notnull=True),
		Field('comment'),
		Field('json',writable=False,readable=False),migrate=True)
