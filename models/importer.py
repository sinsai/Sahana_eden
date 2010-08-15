module='importer'
resource='slist'

tablename=module+'_'+resource

s3.crud_strings[tablename]= Storage(
		title_create = T("Upload a spreadsheet"),
		title_list = T("List of spreadsheets uploaded"),
		label_list_button = T("List of spreadsheets"),
		#msg_record_created = T("Spreadsheet uploaded")
		)

table = db.define_table(tablename,timestamp, uuidstamp,
		Field('Name',required=True,notnull=True),
		Field('Path',type='upload',uploadfield=True,required=True,notnull=True),
		Field('comment'),
		Field('json',writable=False,readable=False),migrate=True)

table.Name.comment = DIV(SPAN("*", _class = "req", _style = "padding-right: 5px"), DIV(_class = "tooltip", _title = Tstr("Name") + "|" + Tstr("Enter a name for the spreadsheet you are uploading(mandatory).")))
