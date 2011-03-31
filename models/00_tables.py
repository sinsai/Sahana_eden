# -*- coding: utf-8 -*-

"""
Global tables and re-usable fields

"""

# =============================================================================
# Representations for Auth Users & Groups
def shn_user_represent(id):
    table = db.auth_user
    user = db(table.id == id).select(table.email, limitby=(0, 1),
                                     cache=(cache.ram, 10)).first()
    if user:
        return user.email
    return None

def shn_role_represent(id):
    table = db.auth_group
    role = db(table.id == id).select(table.role, limitby=(0, 1),
                                     cache=(cache.ram, 10)).first()
    if role:
        return role.role
    return None

# =============================================================================
# "Reusable" fields for table meta-data

# -----------------------------------------------------------------------------
# Record identity meta-fields

# Use URNs according to http://tools.ietf.org/html/rfc4122
s3uuid = SQLCustomType(
                type = "string",
                native = "VARCHAR(128)",
                encoder = (lambda x: "'%s'" % (uuid.uuid4().urn if x == "" else str(x.encode("utf-8")).replace("'", "''"))),
                decoder = (lambda x: x)
            )

# Universally unique identifier for a record
meta_uuid = S3ReusableField("uuid",
                            type=s3uuid,
                            length=128,
                            notnull=True,
                            unique=True,
                            readable=False,
                            writable=False,
                            default="")

# Master-Copy-Index (for Sync)
meta_mci = S3ReusableField("mci", "integer",
                           default=0,
                           readable=False,
                           writable=False)

def s3_uid():
    return (meta_uuid(), meta_mci())

# -----------------------------------------------------------------------------
# Record soft-deletion meta-fields

# "Deleted"-flag
meta_deletion_status = S3ReusableField("deleted", "boolean",
                                       readable=False,
                                       writable=False,
                                       default=False)

# Parked foreign keys of a deleted record
# => to be restored upon "un"-delete
meta_deletion_fk = S3ReusableField("deleted_fk", #"text",
                                   readable=False,
                                   writable=False)

# Record verification status
v_record_status_opts = {
    1: T("unverified"),
    2: T("invalid"),
    3: T("duplicate"),
    4: T("verified")
}

meta_record_status = S3ReusableField("v_record_status", "integer",
                                     requires = IS_NULL_OR(IS_IN_SET(v_record_status_opts)),
                                     default = 1,
                                     label = T("Verification Status"),
                                     represent = lambda opt: v_record_status_opts.get(opt,
                                                                                      T("not specified")),
                                     readable=False,
                                     writable=False)

# Duplicate UID
meta_duplicate_uid = S3ReusableField("v_duplicate_uid",
                                     length=128,
                                     readable=False,
                                     writable=False)

def s3_deletion_status():
    return (meta_deletion_status(),
            meta_deletion_fk(),
            #meta_record_status(),
            #meta_duplicate_uid(),
           )

# -----------------------------------------------------------------------------
# Record timestamp meta-fields

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

# -----------------------------------------------------------------------------
# Record authorship meta-fields

# Author of a record
meta_created_by = S3ReusableField("created_by", db.auth_user,
                                  readable=False, # Enable when needed, not by default
                                  writable=False,
                                  requires=None,
                                  default=session.auth.user.id if auth.is_logged_in() else None,
                                  represent=shn_user_represent,
                                  ondelete="RESTRICT")

# Last author of a record
meta_modified_by = S3ReusableField("modified_by", db.auth_user,
                                   readable=False, # Enable when needed, not by default
                                   writable=False,
                                   requires=None,
                                   default=session.auth.user.id if auth.is_logged_in() else None,
                                   update=session.auth.user.id if auth.is_logged_in() else None,
                                   represent=shn_user_represent,
                                   ondelete="RESTRICT")

# Last verified by
meta_verified_by = S3ReusableField("verified_by", db.auth_user,
                                   readable=False, # Enable when needed, not by default
                                   writable=False,
                                   requires=None,
                                   represent=shn_user_represent,
                                   ondelete="RESTRICT")

def s3_authorstamp():
    return (meta_created_by(),
            meta_modified_by(),
            #meta_verified_by(),
           )

# -----------------------------------------------------------------------------
# Record ownership meta-fields

# Individual user who owns the record
meta_owned_by_user = S3ReusableField("owned_by_user", db.auth_user,
                                     readable=False, # Enable when needed, not by default
                                     writable=False,
                                     requires=None,
                                     default=session.auth.user.id if auth.is_logged_in() else None,
                                     represent=lambda id: id and shn_user_represent(id) or UNKNOWN_OPT,
                                     ondelete="RESTRICT")

# Role of users who collectively own the record
meta_owned_by_role = S3ReusableField("owned_by_role", db.auth_group,
                                     readable=False, # Enable when needed, not by default
                                     writable=False,
                                     requires=None,
                                     default=None,
                                     represent=shn_role_represent,
                                     ondelete="RESTRICT")

def s3_ownerstamp():
    return (meta_owned_by_user(),
            meta_owned_by_role())

# -----------------------------------------------------------------------------
# Common meta-fields

def s3_meta_fields():

    fields = (meta_uuid(),
              meta_mci(),
              meta_deletion_status(),
              meta_deletion_fk(),
              #meta_record_status(),
              #meta_duplicate_uid(),
              meta_created_on(),
              meta_modified_on(),
              meta_created_by(),
              meta_modified_by(),
              #meta_verified_by(),
              meta_owned_by_user(),
              meta_owned_by_role())

    return fields

# -----------------------------------------------------------------------------
# This list of meta fields is used to filter out items that are not normally
# user-relevant. Used when a record is cached (e.g. in session or response).
# In particular, it is used by GIS set_config and get_config, so those should
# not be called prior to this definition.
response.s3.all_meta_field_names = [field.name for field in
    [meta_uuid(),
     meta_mci(),
     meta_deletion_status(),
     meta_deletion_fk(),
     meta_record_status(),
     meta_duplicate_uid(),
     meta_created_on(),
     meta_modified_on(),
     meta_created_by(),
     meta_modified_by(),
     meta_verified_by(),
     meta_owned_by_user(),
     meta_owned_by_role()]]

# =============================================================================
# Reusable roles fields for map layer permissions management (GIS)

role_required = S3ReusableField("role_required", db.auth_group, sortby="role",
                                requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                "auth_group.id",
                                                                "%(role)s",
                                                                zero=T("Public"))),
                                widget = S3AutocompleteWidget(request,
                                                              "auth",
                                                              "group",
                                                              fieldname="role"),
                                represent = shn_role_represent,
                                label = T("Role Required"),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Role Required"),
                                                                T("If this record should be restricted then select which role is required to access the record here."))),
                                ondelete = "RESTRICT")

roles_permitted = S3ReusableField("roles_permitted", db.auth_group, sortby="role",
                                  requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                  "auth_group.id",
                                                                  "%(role)s",
                                                                  multiple=True)),
                                  # @ToDo
                                  #widget = S3CheckboxesWidget(db,
                                  #                            lookup_table_name = "auth_group",
                                  #                            lookup_field_name = "role",
                                  #                            multiple = True),
                                  represent = shn_role_represent,
                                  label = T("Roles Permitted"),
                                  comment = DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Roles Permitted"),
                                                                  T("If this record should be restricted then select which role(s) are permitted to access the record here."))),
                                  ondelete = "RESTRICT")

# =============================================================================
# Other reusable fields

# -----------------------------------------------------------------------------
# comments field to include in other table definitions
comments = S3ReusableField("comments", "text",
                           label = T("Comments"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Comments"), 
                                                           T("Please use this field to record any additional information, including a history of the record if it is updated."))))

# -----------------------------------------------------------------------------
# Reusable currency field to include in other table definitions
currency_type_opts = {
    1:T("Dollars"),
    2:T("Euros"),
    3:T("Pounds")
}
currency_type = S3ReusableField("currency_type", "integer",
                                notnull=True,
                                requires = IS_IN_SET(currency_type_opts,
                                                     zero=None),
                                #default = 1,
                                label = T("Currency"),
                                represent = lambda opt: \
                                    currency_type_opts.get(opt, UNKNOWN_OPT))

# =============================================================================
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
    msg_match = T("Matching Records"),
    msg_no_match = T("No Matching Records"))

# =============================================================================
# Common tables

# -----------------------------------------------------------------------------
# Theme
# @ToDo: Fix or remove completely
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

# -----------------------------------------------------------------------------
# Settings - systemwide
# @ToDo: Move these to deployment_settings
module = "s3"
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        meta_uuid(),
                        #Field("admin_name"),
                        #Field("admin_email"),
                        #Field("admin_tel"),
                        Field("theme", db.admin_theme),
                        migrate=migrate, *s3_timestamp())

table.theme.requires = IS_IN_DB(db, "admin_theme.id", "admin_theme.name", zero=None)
table.theme.represent = lambda name: db(db.admin_theme.id == name).select(db.admin_theme.name,
                                                                          limitby=(0, 1)).first().name
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

# =============================================================================
