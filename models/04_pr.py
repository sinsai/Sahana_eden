# -*- coding: utf-8 -*-

""" S3 Person Registry, additional components

    @author: nursix

    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "pr"

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
resource = "address"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
                        Field("type",
                              "integer",
                              requires = IS_IN_SET(pr_address_type_opts, zero=None),
                              default = 99,
                              label = T("Address Type"),
                              represent = lambda opt: \
                                          pr_address_type_opts.get(opt, UNKNOWN_OPT)),
                        Field("co_name"),
                        Field("street1"),
                        Field("street2"),
                        Field("postcode"),
                        Field("city"),
                        Field("state"),
                        pr_country(),
                        location_id(),
                        comments(),
                        migrate=migrate, *s3_meta_fields())



table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id", shn_pentity_represent,
                                 orderby="pe_type",
                                 filterby="pe_type",
                                 filter_opts=("pr_person", "pr_group"))

table.co_name.label = T("c/o Name")
table.street1.label = T("Street")
table.street2.label = T("Street (continued)")
table.postcode.label = T("ZIP/Postcode")
table.country.label = T("Country")

table.city.requires = IS_NOT_EMPTY()
table.city.comment = SPAN("*", _class="req")

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

# Addresses as component of person entities
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby="pe_id",
                          deletable=True,
                          editable=True)


s3xrc.model.configure(table,
    list_fields = [
        "id",
        "type",
        "co_name",
        "street1",
        "postcode",
        "city",
        "country"
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
resource = "pe_contact"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
                        Field("name"),
                        Field("contact_method",
                              "integer",
                              requires = IS_IN_SET(pr_contact_method_opts, zero=None),
                              default = 99,
                              label = T("Contact Method"),
                              represent = lambda opt: \
                                          pr_contact_method_opts.get(opt, UNKNOWN_OPT)),
                        Field("contact_person"),
                        Field("priority"),
                        Field("value", notnull=True),
                        comments(),
                        migrate=migrate, *s3_meta_fields())


table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                 shn_pentity_represent,
                                 orderby="pe_type",
                                 filterby="pe_type",
                                 filter_opts=("pr_person", "pr_group"))

table.value.requires = IS_NOT_EMPTY()
table.value.comment = SPAN("*", _class="req")
table.priority.requires = IS_IN_SET(range(1,10), zero=None)


pe_contact_id = S3ReusableField("pe_contact_id", db.pr_pe_contact,
                                requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pe_contact.id")),
                                ondelete = "RESTRICT")


# Contact information as component of person entities
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby="pe_id",
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
    list_fields=[
        "id",
        "pe_id",
        "name",
        "contact_person",
        "contact_method",
        "value",
        "priority"
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
resource = "image"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
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


table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

table.title.requires = IS_NOT_EMPTY()
table.title.comment = DIV(SPAN("*", _class="req", _style="padding-right: 5px;"), DIV(_class="tooltip",
    _title=T("Title") + "|" + T("Specify a descriptive title for the image.")))

table.url.label = T("URL")
table.url.represent = lambda url: url and DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None")
table.url.comment =  DIV(SPAN("*", _class="req", _style="padding-right: 5px;"), DIV(_class="tooltip",
    _title=T("URL") + "|" + T("The URL of the image file. If you don't upload an image file, then you must specify its location here.")))

table.image.comment =  DIV(SPAN("*", _class="req", _style="padding-right: 5px;"), DIV(_class="tooltip",
    _title=T("Image") + "|" + T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field.")))
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
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby="pe_id",
                          deletable=True,
                          editable=True)


s3xrc.model.configure(table,
    onvalidation=shn_pr_image_onvalidation,
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
resource = "presence"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
                        sit_id(),
                        Field("reporter", db.pr_person),
                        Field("observer", db.pr_person),
                        Field("shelter_id", "integer"),
                        location_id(),
                        Field("location_details"),
                        Field("datetime", "datetime"),
                        Field("presence_condition", "integer",
                              requires = IS_IN_SET(pr_presence_condition_opts,
                                                   zero=None),
                              default = vita.DEFAULT_PRESENCE,
                              label = T("Presence Condition"),
                              represent = lambda opt: \
                                          pr_presence_condition_opts.get(opt, UNKNOWN_OPT)),
                        Field("proc_desc"),
                        location_id("orig_id", label=T("Origin")),
                        location_id("dest_id", label=T("Destination")),
                        Field("comment"),
                        Field("closed", "boolean", default=False),
                        migrate=migrate, *s3_meta_fields())



table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)

table.observer.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name"))
table.observer.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
table.observer.comment = shn_person_comment(
        T("Observer"),
        T("Person who observed the presence (if different from reporter)."))
table.observer.ondelete = "RESTRICT"

table.reporter.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name"))
table.reporter.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
table.reporter.comment = shn_person_comment(
        T("Reporter"),
        T("Person who is reporting about the presence."))
table.reporter.ondelete = "RESTRICT"
table.reporter.default = s3_logged_in_person()

table.datetime.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
table.datetime.represent = lambda value: shn_as_local_time(value)
table.datetime.label = T("Date/Time")
table.datetime.comment = SPAN("*", _class="req")
table.datetime.default = request.utcnow

table.closed.readable = False
table.closed.writable = False
#table.closed.represent = lambda opt: opt and "closed" or ""

table.proc_desc.label = T("Procedure")

table.shelter_id.readable = False
table.shelter_id.writable = False


# -----------------------------------------------------------------------------
def s3_pr_presence_onvalidation(form):

    """ Presence record validation """

    table = db.pr_presence

    location = form.vars.location_id
    shelter = form.vars.shelter_id

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
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby="pe_id",
                          deletable=True,
                          editable=True,
                          main="time", extra="location_details")

def s3_pr_presence_onaccept(form):
    vita.presence_accept(form)
    s3_situation_onaccept(form, table=db.pr_presence)

def s3_pr_presence_ondelete(row):
    vita.presence_accept(row)
    s3_situation_ondelete(row)

s3xrc.model.configure(table,
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
    ])


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
# Subscription (pe_subscription)
#
resource = "pe_subscription"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
                        Field("resource"),
                        Field("record"), # type="s3uuid"
                        comments(),
                        migrate=migrate, *s3_meta_fields())



table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                    shn_pentity_represent,
                                    filterby="pe_type",
                                    orderby="pe_type",
                                    filter_opts=("pr_person", "pr_group"))

# Moved to zzz_last.py to ensure all tables caught!
#table.resource.requires = IS_IN_SET(db.tables)

# Subscriptions as component of person entities
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby="pe_id",
                          deletable=True,
                          editable=True)

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
resource = "identity"
tablename = "%s_%s" % (module, resource)
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


table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.person_id.label = T("Person")
table.value.requires = IS_NOT_IN_DB(db,"%s.value" % tablename)
table.value.comment = SPAN("*", _class="req")
table.ia_name.label = T("Issuing Authority")

# Identity as component of persons
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(pr_person="person_id"),
                          deletable=True,
                          editable=True)

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
    resource = "physical_description"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            pe_id(),

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
    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby="pe_id",
                              deletable=True,
                              editable=True)

# End
# *****************************************************************************
