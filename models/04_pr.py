# -*- coding: utf-8 -*-

""" VITA Person Registry, Additional Models

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

prefix = "pr"

# *****************************************************************************
# Address (address)
#
pr_address_type_opts = {
    1:T("Home Address"),
    2:T("Office Address"),
    3:T("Holiday Address"),
    99:T("other")
}


# -----------------------------------------------------------------------------
resourcename = "address"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("type",
                              "integer",
                              requires = IS_IN_SET(pr_address_type_opts, zero=None),
                              default = 99,
                              label = T("Address Type"),
                              represent = lambda opt: \
                                          pr_address_type_opts.get(opt, UNKNOWN_OPT)),
                        Field("co_name", label=T("c/o Name")),
                        location_id(),
                        Field("address", "text", label=T("Address"), writable=False), # Populated from location_id
                        Field("L4", label=deployment_settings.get_gis_locations_hierarchy("L4"), writable=False), # Populated from location_id
                        Field("L3", label=deployment_settings.get_gis_locations_hierarchy("L3"), writable=False), # Populated from location_id
                        Field("L2", label=deployment_settings.get_gis_locations_hierarchy("L2"), writable=False), # Populated from location_id
                        Field("L1", label=deployment_settings.get_gis_locations_hierarchy("L1"), writable=False), # Populated from location_id
                        Field("L0", label=deployment_settings.get_gis_locations_hierarchy("L0"), writable=False), # Populated from location_id
                        Field("postcode", label=T("Postcode"), writable=False), # Populated from location_id
                        comments(),
                        migrate=migrate, *s3_meta_fields())



table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)

table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id", shn_pentity_represent,
                                 orderby="instance_type",
                                 filterby="instance_type",
                                 filter_opts=("pr_person", "pr_group"))

ADD_ADDRESS = T("Add Address")
LIST_ADDRESS = T("List of addresses")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_ADDRESS,
    title_display = T("Address Details"),
    title_list = LIST_ADDRESS,
    title_update = T("Edit Address"),
    title_search = T("Search Addresses"),
    subtitle_create = T("Add New Address"),
    subtitle_list = T("Addresses"),
    label_list_button = LIST_ADDRESS,
    label_create_button = ADD_ADDRESS,
    msg_record_created = T("Address added"),
    msg_record_modified = T("Address updated"),
    msg_record_deleted = T("Address deleted"),
    msg_list_empty = T("No Addresses currently registered"))

def address_onvalidation(form):
    """
        Write the Postcode & Street Address fields from the Location
        - also used by org_office

        @ToDo: Allow the reverse operation.
        If these fields are populated then create an appropriate location
    """

    if "location_id" in form.vars:
        locations = db.gis_location
        # Read Postcode & Street Address
        location = db(locations.id == form.vars.location_id).select(locations.addr_street,
                                                                    locations.addr_postcode,
                                                                    locations.name,
                                                                    locations.level,
                                                                    locations.parent,
                                                                    locations.path,
                                                                    limitby=(0, 1)).first()
        if location:
            form.vars.address = location.addr_street
            form.vars.postcode = location.addr_postcode
            if location.level == "L0":
                form.vars.L0 = location.name
            elif location.level == "L1":
                form.vars.L1 = location.name
                if location.parent:
                    country = db(locations.id == location.parent).select(locations.name, limitby=(0, 1)).first()
                    if country:
                        form.vars.L0 = country.name
            else:
                # Get ids of ancestors at each level.
                gis.get_parent_per_level(form.vars,
                                         form.vars.location_id,
                                         feature=location,
                                         names=True)

# Addresses as component of person entities
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=super_key(db.pr_pentity))

s3xrc.model.configure(table,
                      onvalidation=lambda form: address_onvalidation(form),
                      list_fields = [
                        "id",
                        "type",
                        "address",
                        "postcode",
                        #"co_name",
                        #"L4",
                        "L3",
                        "L2",
                        "L1",
                        "L0"
                    ])

# *****************************************************************************
# Contact (pe_contact)
#
pr_contact_method_opts = {
    1:T("Email"),
    2:T("Mobile Phone"),
    3:"XMPP",
    4:T("Twitter"),
    5:T("Telephone"),
    6:T("Fax"),
    7:T("Facebook"),
    99:T("other")
}


# -----------------------------------------------------------------------------
resourcename = "pe_contact"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("contact_method",
                              "integer",
                              requires = IS_IN_SET(pr_contact_method_opts, zero=None),
                              default = 99,
                              label = T("Contact Method"),
                              represent = lambda opt: \
                                          pr_contact_method_opts.get(opt, UNKNOWN_OPT)),
                        Field("value", notnull=True),
                        Field("priority"),
                        Field("contact_person"),
                        comments(),
                        #Field("name"),
                        migrate=migrate, *s3_meta_fields())


table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                 shn_pentity_represent,
                                 orderby="instance_type",
                                 filterby="instance_type",
                                 filter_opts=("pr_person", "pr_group"))

table.value.requires = IS_NOT_EMPTY()
table.priority.requires = IS_IN_SET(range(1, 10), zero=None)


pe_contact_id = S3ReusableField("pe_contact_id", db.pr_pe_contact,
                                requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pe_contact.id")),
                                ondelete = "RESTRICT")


# Contact information as component of person entities
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=super_key(db.pr_pentity))

def shn_pe_contact_onvalidation(form):

    """ Contact form validation """

    table = db.pr_pe_contact

    if form.vars.contact_method == '1':
        email, error = IS_EMAIL()(form.vars.value)
        if error:
            form.errors.value = T("Enter a valid email")

    return False

s3xrc.model.configure(table,
                      onvalidation=shn_pe_contact_onvalidation,
                      list_fields=[
                        #"id",
                        #"pe_id",
                        "contact_method",
                        "value",
                        "priority",
                        #"contact_person",
                        #"name",
                      ])

s3.crud_strings[tablename] = Storage(
    title_create = T("Add Contact Information"),
    title_display = T("Contact Details"),
    title_list = T("Contact Information"),
    title_update = T("Edit Contact Information"),
    title_search = T("Search Contact Information"),
    subtitle_create = T("Add Contact Information"),
    subtitle_list = T("Contact Information"),
    label_list_button = T("List Records"),
    label_create_button = T("Add Record"),
    label_delete_button = T("Delete Record"),
    msg_record_created = T("Contact information added"),
    msg_record_modified = T("Contact information updated"),
    msg_record_deleted = T("Contact information deleted"),
    msg_list_empty = T("No contact information available"))


# *****************************************************************************
# Image (image)
#
pr_image_type_opts = {
    1:T("Photograph"),
    2:T("Sketch"),
    3:T("Fingerprint"),
    4:T("X-Ray"),
    5:T("Document Scan"),
    99:T("other")
}


# -----------------------------------------------------------------------------
resourcename = "image"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("type", "integer",
                              requires = IS_IN_SET(pr_image_type_opts, zero=None),
                              default = 1,
                              label = T("Image Type"),
                              represent = lambda opt: pr_image_type_opts.get(opt, UNKNOWN_OPT)),
                        Field("title"),
                        Field("image", "upload", autodelete=True),
                        Field("url"),
                        Field("description"),
                        comments(),
                        migrate=migrate, *s3_meta_fields())


table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)

table.title.requires = IS_NOT_EMPTY()
table.title.comment = DIV(_class="tooltip",
    _title=T("Title") + "|" + T("Specify a descriptive title for the image."))

table.url.label = T("URL")
table.url.represent = lambda url: url and DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None")
table.url.comment =  DIV(_class="tooltip",
    _title=T("URL") + "|" + T("The URL of the image file. If you don't upload an image file, then you must specify its location here."))
table.image.comment =  DIV(_class="tooltip",
    _title=T("Image") + "|" + T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field."))
table.image.represent = lambda image: image and \
        DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=image),_height=60, _alt=T("View Image")),
              _href=URL(r=request, c="default", f="download", args=image))) or \
        T("No Image")
table.description.comment =  DIV(_class="tooltip",
    _title=T("Description") + "|" + T("Give a brief description of the image, e.g. what can be seen where on the picture (optional)."))


# -----------------------------------------------------------------------------
def shn_pr_image_onvalidation(form):

    """ Image form validation """

    table = db.pr_image
    image = form.vars.image

    if not hasattr(image, "file"):
        id = request.post_vars.id
        if id:
            record = db(table.id == id).select(table.image, limitby=(0, 1)).first()
            if record:
                image = record.image

    url = form.vars.url
    if not hasattr(image, "file") and not image and not url:
        form.errors.image = \
        form.errors.url = T("Either file upload or image URL required.")

    return False


# -----------------------------------------------------------------------------
# Images as component of person entities
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=super_key(db.pr_pentity))

s3xrc.model.configure(table,
    onvalidation=shn_pr_image_onvalidation,
    mark_required = ["url", "image"],
    list_fields=[
        "id",
        "title",
        "type",
        "image",
        "url",
        "description"
    ])


LIST_IMAGES = T("List Images")
s3.crud_strings[tablename] = Storage(
    title_create = T("Image"),
    title_display = T("Image Details"),
    title_list = LIST_IMAGES,
    title_update = T("Edit Image Details"),
    title_search = T("Search Images"),
    subtitle_create = T("Add New Image"),
    subtitle_list = T("Images"),
    label_list_button = LIST_IMAGES,
    label_create_button = T("Add Image"),
    label_delete_button = T("Delete Image"),
    msg_record_created = T("Image added"),
    msg_record_modified = T("Image updated"),
    msg_record_deleted = T("Image deleted"),
    msg_list_empty = T("No Images currently registered"))


# *****************************************************************************
# Presence Log (presence)
#
pr_presence_condition_opts = vita.presence_conditions

# -----------------------------------------------------------------------------
resourcename = "presence"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        super_link(db.sit_situation), # sit_id
                        person_id("observer",
                                  label=T("Observer"),
                                  default = s3_logged_in_person(),
                                  comment=shn_person_comment(T("Observer"),
                                                             T("Person who has actually seen the person/group."))),
                        Field("shelter_id", "integer"),
                        location_id(widget = S3LocationAutocompleteWidget(request, deployment_settings),
                                    comment = DIV(A(ADD_LOCATION, _class="colorbox", _target="top", _title=ADD_LOCATION,
                                                  _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup"))),
                                              DIV(_class="tooltip",
                                                  _title=T("Current Location") + "|" + T("The Current Location of the Person/Group, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations.")))),
                        Field("location_details",
                              comment = DIV(_class="tooltip",
                                            _title=T("Location Details") + "|" + T("Specific Area (e.g. Building/Room) within the Location that this Person/Group is seen."))
                             ),
                        Field("datetime", "datetime"),
                        Field("presence_condition", "integer",
                              requires = IS_IN_SET(pr_presence_condition_opts,
                                                   zero=None),
                              default = vita.DEFAULT_PRESENCE,
                              label = T("Presence Condition"),
                              represent = lambda opt: \
                                          pr_presence_condition_opts.get(opt, UNKNOWN_OPT)),
                        Field("proc_desc"),
                        location_id("orig_id", label=T("Origin"), widget = S3LocationAutocompleteWidget(request, deployment_settings),
                                    comment = DIV(A(ADD_LOCATION, _class="colorbox", _target="top", _title=ADD_LOCATION,
                                                  _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup"))),
                                              DIV(_class="tooltip",
                                                  _title=T("Origin") + "|" + T("The Location the Person has come from, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations.")))),
                        location_id("dest_id", label=T("Destination"), widget = S3LocationAutocompleteWidget(request, deployment_settings),
                                    comment = DIV(A(ADD_LOCATION, _class="colorbox", _target="top", _title=ADD_LOCATION,
                                                  _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup"))),
                                              DIV(_class="tooltip",
                                                  _title=T("Destination") + "|" + T("The Location the Person is going to, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations.")))),
                        Field("comment"),
                        Field("closed", "boolean", default=False),
                        migrate=migrate, *s3_meta_fields())



table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)

table.datetime.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
table.datetime.represent = lambda value: shn_as_local_time(value)
table.datetime.label = T("Date/Time")
table.datetime.default = request.utcnow

table.closed.readable = False
table.closed.writable = False
#table.closed.represent = lambda opt: opt and "closed" or ""

table.proc_desc.label = T("Procedure")
table.proc_desc.comment = DIV(DIV(_class="tooltip",
        _title=T("Procedure") + "|" + T('Describe the procedure which this record relates to (e.g. "medical examination")')))

table.shelter_id.readable = False
table.shelter_id.writable = False


# -----------------------------------------------------------------------------
def s3_pr_presence_onvalidation(form):

    """ Presence record validation """

    table = db.pr_presence

    location = form.vars.location_id
    shelter = form.vars.shelter_id

    if shelter and "cr_shelter" in db:
        set = db(db.cr_shelter.id == shelter)
        row = set.select(db.cr_shelter.location_id, limitby=(0, 1)).first()
        if row:
            location = form.vars.location_id = row.location_id
        else:
            shelter = None

    if location or shelter:
        return

    condition = form.vars.presence_condition
    if condition:
        try:
            condition = int(condition)
        except ValueError:
            condition = None
    else:
        condition = table.presence_condition.default
        form.vars.condition = condition

    if condition:
        if condition in vita.PERSISTANT_PRESENCE or \
           condition in vita.ABSENCE:
            if not form.vars.id:
                if table.location_id.default or \
                   table.shelter_id.default:
                    return
            else:
                record = db(table.id == form.vars.id).select(table.location_id,
                                                             table.shelter_id,
                                                             limitby=(0, 1)).first()
                if record and \
                   record.location_id or record.shelter_id:
                    return
        else:
            return
    else:
        return

    form.errors.location_id = \
    form.errors.shelter_id = T("Either a shelter or a location must be specified")
    return


# -----------------------------------------------------------------------------
# Presence as component of person entities
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=super_key(db.pr_pentity))

def s3_pr_presence_onaccept(form):
    vita.presence_accept(form)

def s3_pr_presence_ondelete(row):
    vita.presence_accept(row)

s3xrc.model.configure(table,
    super_entity = db.sit_situation,
    onvalidation = lambda form: s3_pr_presence_onvalidation(form),
    onaccept = lambda form: s3_pr_presence_onaccept(form),
    delete_onaccept = lambda row: s3_pr_presence_ondelete(row),
    list_fields = [
        "id",
        "datetime",
        "location_id",
        "shelter_id",
        "presence_condition",
        "orig_id",
        "dest_id"
    ],
    main="time", extra="location_details")


ADD_LOG_ENTRY = T("Add Log Entry")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_LOG_ENTRY,
    title_display = T("Log Entry Details"),
    title_list = T("Presence Log"),
    title_update = T("Edit Log Entry"),
    title_search = T("Search Log Entry"),
    subtitle_create = T("Add New Log Entry"),
    subtitle_list = T("Current Log Entries"),
    label_list_button = T("List Log Entries"),
    label_create_button = ADD_LOG_ENTRY,
    msg_record_created = T("Log entry added"),
    msg_record_modified = T("Log entry updated"),
    msg_record_deleted = T("Log entry deleted"),
    msg_list_empty = T("No Presence Log Entries currently registered"))


# *****************************************************************************
# Note (future replacement for pr_presence and pf_missing_report)
#
#pr_note_types = {
    #1:T("Location"),
    #2:T("Status"),
    #3:T("Note")
#}

#pr_note_status = {
    #1:T("reported"),
    #2:T("confirmed"),
    #3:T("invalid")
#}

#pr_procedure_types = {
    #1:T("Check-in"),
    #2:T("Check-out")
#}

#resourcename = "note"
#tablename = "%s_%s" % (prefix, resourcename)
#table = db.define_table(tablename,
                        #super_link(db.pr_pentity), # pe_id
                        #person_id("reporter"),

                        ## Note type and status
                        #Field("note_type", "integer",
                              #requires = IS_IN_SET(pr_note_types, zero=None),
                              #default = 3,
                              #label = T("Note Type"),
                              #represent = lambda opt: \
                                          #pr_note_types.get(opt, UNKNOWN_OPT)),
                        #Field("note_status", "integer",
                              #requires = IS_IN_SET(pr_note_status, zero=None),
                              #default = 1,
                              #label = T("Note Status"),
                              #represent = lambda opt: \
                                          #pr_note_status.get(opt, UNKNOWN_OPT)),

                        ## Time stamp
                        #Field("timestmp", "datetime"),

                        ## Last known location
                        #location_id(),
                        #shelter_id(),
                        #hospital_id(),

                        ## Note text (optional)
                        #Field("note_text", "text"),

                        ## Person status
                        #Field("missing", "boolean", default=False),
                        #Field("injured", "boolean", default=False),
                        #Field("deceased", "boolean", default=False),

                        ## Procedure: None, Check-in or Check-out
                        #Field("procedure", "integer",
                              #requires = IS_EMPTY_OR(IS_IN_SET(pr_procedure_types)),
                              #default = None,
                              #label = T("Procedure"),
                              #represent = lambda opt: \
                                          #pr_procedure_types.get(opt, UNKNOWN_OPT)),

                        #Field("closed", "boolean", default=False),
                        #migrate=migrate, *s3_meta_fields())


## CRUD strings
#ADD_NOTE = T("Add Note")
#s3.crud_strings[tablename] = Storage(
    #title_create = ADD_NOTE,
    #title_display = T("Note Details"),
    #title_list = T("Notes"),
    #title_update = T("Edit Note"),
    #title_search = T("Search Notes"),
    #subtitle_create = T("Add New Note"),
    #subtitle_list = T("Current Notes"),
    #label_list_button = T("List Notes"),
    #label_create_button = ADD_NOTE,
    #msg_record_created = T("Note added"),
    #msg_record_modified = T("Note updated"),
    #msg_record_deleted = T("Note deleted"),
    #msg_list_empty = T("No notes available"))


## Notes as component of person entities
#s3xrc.model.add_component(prefix, resourcename,
                          #multiple=True,
                          #joinby=super_key(db.pr_pentity))


# *****************************************************************************
# Subscription (pe_subscription)
#
resourcename = "pe_subscription"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("resource"),
                        Field("record"), # type="s3uuid"
                        comments(),
                        migrate=migrate, *s3_meta_fields())



table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                    shn_pentity_represent,
                                    filterby="instance_type",
                                    orderby="instance_type",
                                    filter_opts=("pr_person", "pr_group"))

# Moved to zzz_last.py to ensure all tables caught!
#table.resource.requires = IS_IN_SET(db.tables)

# Subscriptions as component of person entities
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=super_key(db.pr_pentity))

s3xrc.model.configure(table,
    list_fields=[
        "id",
        "resource",
        "record"
    ])

s3.crud_strings[tablename] = Storage(
    title_create = T("Add Subscription"),
    title_display = T("Subscription Details"),
    title_list = T("Subscriptions"),
    title_update = T("Edit Subscription"),
    title_search = T("Search Subscriptions"),
    subtitle_create = T("Add Subscription"),
    subtitle_list = T("Subscriptions"),
    label_list_button = T("List Subscriptions"),
    label_create_button = T("Add Subscription"),
    label_delete_button = T("Delete Subscription"),
    msg_record_created = T("Subscription added"),
    msg_record_modified = T("Subscription updated"),
    msg_record_deleted = T("Subscription deleted"),
    msg_list_empty = T("No Subscription available"))


# *****************************************************************************
# Identity
#
pr_id_type_opts = {
    1:T("Passport"),
    2:T("National ID Card"),
    3:T("Driving License"),
    99:T("other")
}


# -----------------------------------------------------------------------------
resourcename = "identity"
tablename = "%s_%s" % (prefix, resourcename)
table = db.define_table(tablename,
                        person_id(),
                        Field("type", "integer",
                              requires = IS_IN_SET(pr_id_type_opts, zero=None),
                              default = 1,
                              label = T("ID type"),
                              represent = lambda opt: \
                                          pr_id_type_opts.get(opt, UNKNOWN_OPT)),
                        Field("value"),
                        Field("description"),
                        Field("country_code", length=4),
                        Field("ia_name"), # Name of issuing authority
                        #Field("ia_subdivision"), # Name of issuing authority subdivision
                        #Field("ia_code"), # Code of issuing authority (if any)
                        comments(),
                        migrate=migrate, *s3_meta_fields())


table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.person_id.label = T("Person")
table.value.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.value" % tablename)]
table.ia_name.label = T("Issuing Authority")

# Identity as component of persons
s3xrc.model.add_component(prefix, resourcename,
                          multiple=True,
                          joinby=dict(pr_person="person_id"))

s3xrc.model.configure(table,
    list_fields=[
        "id",
        "type",
        "type",
        "value",
        "country_code",
        "ia_name"
    ])

ADD_IDENTITY = T("Add Identity")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_IDENTITY,
    title_display = T("Identity Details"),
    title_list = T("Known Identities"),
    title_update = T("Edit Identity"),
    title_search = T("Search Identity"),
    subtitle_create = T("Add New Identity"),
    subtitle_list = T("Current Identities"),
    label_list_button = T("List Identities"),
    label_create_button = ADD_IDENTITY,
    msg_record_created = T("Identity added"),
    msg_record_modified = T("Identity updated"),
    msg_record_deleted = T("Identity deleted"),
    msg_list_empty = T("No Identities currently registered"))


# *****************************************************************************
# PR Extension: physical description
#
if deployment_settings.has_module("dvi") or \
   deployment_settings.has_module("mpr"):

    pr_race_opts = {
        1: T("caucasoid"),
        2: T("mongoloid"),
        3: T("negroid"),
        99: T("other")
    }

    pr_complexion_opts = {
        1: T("light"),
        2: T("medium"),
        3: T("dark"),
        99: T("other")
    }

    pr_height_opts = {
        1: T("short"),
        2: T("average"),
        3: T("tall")
    }

    pr_weight_opts = {
        1: T("slim"),
        2: T("average"),
        3: T("fat")
    }

    pr_blood_type_opts = {
        1: "A",
        2: "B",
        3: "0",
        4: "AB"
    }

    pr_eye_color_opts = {
        1: T("blue"),
        2: T("grey"),
        3: T("green"),
        4: T("brown"),
        5: T("black"),
        99: T("other")
    }

    pr_hair_color_opts = {
        1: T("blond"),
        2: T("brown"),
        3: T("black"),
        4: T("red"),
        5: T("grey"),
        6: T("white"),
        99: T("see comment")
    }

    pr_hair_style_opts = {
        1: T("straight"),
        2: T("wavy"),
        3: T("curly"),
        99: T("see comment")
    }

    pr_hair_length_opts = {
        1: T("short<6cm"),
        2: T("medium<12cm"),
        3: T("long>12cm"),
        4: T("shaved"),
        99: T("see comment")
    }

    pr_hair_baldness_opts = {
        1: T("forehead"),
        2: T("sides"),
        3: T("tonsure"),
        4: T("total"),
        99: T("see comment")
    }

    pr_facial_hair_type_opts = {
        1: T("none"),
        2: T("Moustache"),
        3: T("Goatee"),
        4: T("Whiskers"),
        5: T("Full beard"),
        99: T("see comment")
    }

    pr_facial_hair_length_opts = {
        1: T("short"),
        2: T("medium"),
        3: T("long"),
        4: T("shaved")
    }


# -----------------------------------------------------------------------------
    resourcename = "physical_description"
    tablename = "%s_%s" % (prefix, resourcename)
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id

                            # Race and complexion
                            Field("race", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_race_opts)),
                                  label = T("Race"),
                                  represent = lambda opt: \
                                              pr_race_opts.get(opt, UNKNOWN_OPT)),
                            Field("complexion", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_complexion_opts)),
                                  label = T("Complexion"),
                                  represent = lambda opt: \
                                              pr_complexion_opts.get(opt, UNKNOWN_OPT)),
                            Field("ethnicity"),

                            # Height and weight
                            Field("height", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_height_opts)),
                                  label = T("Height"),
                                  represent = lambda opt: \
                                              pr_height_opts.get(opt, UNKNOWN_OPT)),
                            Field("height_cm", "integer",
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 300)),
                                  label = T("Height (cm)")),
                            Field("weight", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_weight_opts)),
                                  label = T("Weight"),
                                  represent = lambda opt: \
                                              pr_weight_opts.get(opt, UNKNOWN_OPT)),
                            Field("weight_kg", "integer",
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 500)),
                                  label = T("Weight (kg)")),

                            # Blood type, eye color
                            Field("blood_type", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_blood_type_opts)),
                                  label = T("Blood Type (AB0)"),
                                  represent = lambda opt: \
                                              pr_blood_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("eye_color", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_eye_color_opts)),
                                  label = T("Eye Color"),
                                  represent = lambda opt: \
                                              pr_eye_color_opts.get(opt, UNKNOWN_OPT)),

                            # Hair of the head
                            Field("hair_color", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                  label = T("Hair Color"),
                                  represent = lambda opt: \
                                              pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_style", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_style_opts)),
                                  label = T("Hair Style"),
                                  represent = lambda opt: \
                                              pr_hair_style_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_length", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_length_opts)),
                                  label = T("Hair Length"),
                                  represent = lambda opt: \
                                              pr_hair_length_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_baldness", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_baldness_opts)),
                                  label = T("Baldness"),
                                  represent = lambda opt: \
                                              pr_hair_baldness_opts.get(opt, UNKNOWN_OPT)),
                            Field("hair_comment"),

                            # Facial hair
                            Field("facial_hair_type", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_type_opts)),
                                  label = T("Facial hair, type"),
                                  represent = lambda opt: \
                                              pr_facial_hair_type_opts.get(opt, UNKNOWN_OPT)),
                            Field("facial_hair_color", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                  label = T("Facial hair, color"),
                                  represent = lambda opt: \
                                              pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                            Field("facial_hair_length", "integer",
                                  requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_length_opts)),
                                  label = T("Facial hear, length"),
                                  represent = lambda opt: \
                                              pr_facial_hair_length_opts.get(opt, UNKNOWN_OPT)),
                            Field("facial_hair_comment"),

                            # Body hair and skin marks
                            Field("body_hair"),
                            Field("skin_marks", "text"),

                            # Medical Details: scars, amputations, implants
                            Field("medical_conditions", "text"),

                            # Other details
                            Field("other_details", "text"),

                            comments(),
                            migrate=migrate, *s3_meta_fields())


    table.height_cm.comment = DIV(DIV(_class="tooltip",
        _title=T("Height") + "|" + T("The body height (crown to heel) in cm.")))
    table.weight_kg.comment = DIV(DIV(_class="tooltip",
        _title=T("Weight") + "|" + T("The weight in kg.")))

    table.pe_id.readable = False
    table.pe_id.writable = False

    # Physical description as component of person entity
    s3xrc.model.add_component(prefix, resourcename,
                              multiple=False,
                              joinby=super_key(db.pr_pentity))

# End
# *****************************************************************************
