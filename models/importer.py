# -*- coding: utf-8 -*-

"""
    Importer

    @author: Shikhar Kohli
"""

module = "importer"
if deployment_settings.has_module(module):

    resourcename = "spreadsheet"
    tablename = module + "_" + resourcename
    table = db.define_table(tablename,
                            Field("name", required=True, notnull=True),
                            Field("path", type="upload", uploadfield=True, required=True, notnull=True),
                            comments(),
                            Field("json", writable=False, readable=False),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid()))

    table.name.comment = DIV(_class = "tooltip",
                             _title = T("Name") + "|" + T("Enter a name for the spreadsheet you are uploading (mandatory)."))

    s3.crud_strings[tablename]= Storage(
            title_create = T("Upload a Spreadsheet"),
            title_list = T("List of Spreadsheets uploaded"),
            label_list_button = T("List of Spreadsheets"),
            #msg_record_created = T("Spreadsheet uploaded")
            )
