# -*- coding: utf-8 -*-

"""
    Global tables and re-usable fields
"""

# -----------------------------------------------------------------------------
# Reusable Author fields to include in other table definitions
def shn_user_represent(id):
    table = db.auth_user
    user = db(table.id == id).select(table.email, limitby=(0, 1), cache=(cache.ram, 10)).first()
    if user:
        return user.email
    return None

def shn_role_represent(id):
    table = db.auth_group
    role = db(table.id == id).select(table.role, limitby=(0, 1), cache=(cache.ram, 10)).first()
    if role:
        return role.role
    return None

# -----------------------------------------------------------------------------
# "Reusable" fields for table meta-data
#
# Reusable UUID field to include in other table definitions
# Uses URNs according to http://tools.ietf.org/html/rfc4122
s3uuid = SQLCustomType(
                type = "string",
                native = "VARCHAR(128)",
                encoder = (lambda x: "'%s'" % (uuid.uuid4().urn if x == "" else str(x).replace("'", "''"))),
                decoder = (lambda x: x)
            )

meta_uuidstamp = S3ReusableField("uuid",
                                 type=s3uuid,
                                 length=128,
                                 notnull=True,
                                 unique=True,
                                 readable=False,
                                 writable=False,
                                 default="")

meta_mci = S3ReusableField("mci", "integer", # Master-Copy-Index
                           default=0,
                           readable=False,
                           writable=False)

def s3_uid():
    return (meta_uuidstamp(), meta_mci())

meta_deletion_status = S3ReusableField("deleted", "boolean",
                                       readable=False,
                                       writable=False,
                                       default=False)

def s3_deletion_status():
    return (meta_deletion_status(),)

meta_created_on = S3ReusableField("created_on", "datetime",
                                  readable=False,
                                  writable=False,
                                  default=request.utcnow)

meta_modified_on = S3ReusableField("modified_on", "datetime",
                                   readable=False,
                                   writable=False,
                                   default=request.utcnow,
                                   update=request.utcnow)

def s3_timestamp():
    return (meta_created_on(), meta_modified_on())

meta_created_by = S3ReusableField("created_by", db.auth_user,
                                  readable=False, # Enable when needed, not by default
                                  writable=False,
                                  requires=None,
                                  default=session.auth.user.id if auth.is_logged_in() else None,
                                  represent=lambda id: id and shn_user_represent(id) or UNKNOWN_OPT,
                                  ondelete="RESTRICT")

meta_owned_by = S3ReusableField("owned_by", db.auth_group,
                                readable=False, # Enable when needed, not by default
                                writable=False,
                                requires=None,
                                default=None,
                                represent=lambda id: id and shn_role_represent(id) or UNKNOWN_OPT,
                                ondelete="RESTRICT")

meta_modified_by = S3ReusableField("modified_by", db.auth_user,
                                   readable=False, # Enable when needed, not by default
                                   writable=False,
                                   requires=None,
                                   default=session.auth.user.id if auth.is_logged_in() else None,
                                   update=session.auth.user.id if auth.is_logged_in() else None,
                                   represent=lambda id: id and shn_user_represent(id) or UNKNOWN_OPT,
                                   ondelete="RESTRICT")

def s3_authorstamp():
    return (meta_created_by(), meta_owned_by(), meta_modified_by())

def s3_meta_fields():

    fields = (meta_uuidstamp(),
              meta_mci(),
              meta_deletion_status(),
              meta_created_on(),
              meta_modified_on(),
              meta_created_by(),
              meta_owned_by(),
              meta_modified_by())

    return fields

# -----------------------------------------------------------------------------
# Reusable comments field to include in other table definitions
comments = S3ReusableField("comments", "text",
                           label = T("Comments"),
                           comment = DIV(_class="tooltip",
                                         _title=T("Comments") + "|" + T("Please use this field to record any additional information, including a history of the record if it is updated.")))

# Reusable currency field to include in other table definitions
currency_type_opts = {
    1:T("Dollars"),
    2:T("Euros"),
    3:T("Pounds")
}
currency_type = S3ReusableField("currency_type", "integer",
                                notnull=True,
                                requires = IS_IN_SET(currency_type_opts, zero=None),
                                #default = 1,
                                label = T("Currency"),
                                represent = lambda opt: \
                                    currency_type_opts.get(opt, UNKNOWN_OPT))

# Default CRUD strings
ADD_RECORD = T("Add Record")
LIST_RECORDS = T("List Records")
s3.crud_strings = Storage(
    title_create = ADD_RECORD,
    title_display = T("Record Details"),
    title_list = LIST_RECORDS,
    title_update = T("Edit Record"),
    title_search = T("Search Records"),
    subtitle_create = T("Add New Record"),
    subtitle_list = T("Available Records"),
    label_list_button = LIST_RECORDS,
    label_create_button = ADD_RECORD,
    label_delete_button = T("Delete Record"),
    msg_record_created = T("Record added"),
    msg_record_modified = T("Record updated"),
    msg_record_deleted = T("Record deleted"),
    msg_list_empty = T("No Records currently available"),
    msg_no_match = T("No Records matching the query"))

module = "admin"
resource = "theme"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("name"),
                        Field("logo"),
                        Field("header_background"),
                        Field("col_background"),
                        Field("col_txt"),
                        Field("col_txt_background"),
                        Field("col_txt_border"),
                        Field("col_txt_underline"),
                        Field("col_menu"),
                        Field("col_highlight"),
                        Field("col_input"),
                        Field("col_border_btn_out"),
                        Field("col_border_btn_in"),
                        Field("col_btn_hover"),
                        migrate=migrate)

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.col_background.requires = IS_HTML_COLOUR()
table.col_txt.requires = IS_HTML_COLOUR()
table.col_txt_background.requires = IS_HTML_COLOUR()
table.col_txt_border.requires = IS_HTML_COLOUR()
table.col_txt_underline.requires = IS_HTML_COLOUR()
table.col_menu.requires = IS_HTML_COLOUR()
table.col_highlight.requires = IS_HTML_COLOUR()
table.col_input.requires = IS_HTML_COLOUR()
table.col_border_btn_out.requires = IS_HTML_COLOUR()
table.col_border_btn_in.requires = IS_HTML_COLOUR()
table.col_btn_hover.requires = IS_HTML_COLOUR()

module = "s3"
# Settings - systemwide
s3_setting_security_policy_opts = {
    1:T("simple"),
    2:T("editor"),
    3:T("full")
    }
# @ToDo Move these to deployment_settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        meta_uuidstamp(),
                        Field("admin_name"),
                        Field("admin_email"),
                        Field("admin_tel"),
                        Field("theme", db.admin_theme),
                        migrate=migrate, *s3_timestamp())

table.theme.requires = IS_IN_DB(db, "admin_theme.id", "admin_theme.name", zero=None)
table.theme.represent = lambda name: db(db.admin_theme.id == name).select(db.admin_theme.name, limitby=(0, 1)).first().name
# Define CRUD strings (NB These apply to all Modules' "settings" too)
ADD_SETTING = T("Add Setting")
LIST_SETTINGS = T("List Settings")
s3.crud_strings[resource] = Storage(
    title_create = ADD_SETTING,
    title_display = T("Setting Details"),
    title_list = LIST_SETTINGS,
    title_update = T("Edit Setting"),
    title_search = T("Search Settings"),
    subtitle_create = T("Add New Setting"),
    subtitle_list = T("Settings"),
    label_list_button = LIST_SETTINGS,
    label_create_button = ADD_SETTING,
    msg_record_created = T("Setting added"),
    msg_record_modified = T("Setting updated"),
    msg_record_deleted = T("Setting deleted"),
    msg_list_empty = T("No Settings currently defined"))
