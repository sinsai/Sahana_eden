# -*- coding: utf-8 -*-

"""
    Importer 
    
    @author: Shikhar Kohli
"""

module = "importer"
if deployment_settings.has_module(module):

    resource = "spreadsheet"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                            Field("name", required=True, notnull=True),
                            Field("path", type="upload", uploadfield=True, required=True, notnull=True),
                            comments,
                            Field("json", writable=False, readable=False),
                            migrate=migrate)

    table.name.comment = DIV(SPAN("*",
                                  _class="req",
                                  _style="padding-right: 5px"),
                             DIV(_class = "tooltip",
                                 _title = Tstr("Name") + "|" + Tstr("Enter a name for the spreadsheet you are uploading (mandatory).")))

    s3.crud_strings[tablename]= Storage(
            title_create = T("Upload a Spreadsheet"),
            title_list = T("List of Spreadsheets uploaded"),
            label_list_button = T("List of Spreadsheets"),
            #msg_record_created = T("Spreadsheet uploaded")
            )
