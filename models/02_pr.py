# -*- coding: utf-8 -*-

"""
    S3 Person Registry

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
"""

module = "pr"

# *****************************************************************************
# Settings
#
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

# *****************************************************************************
# PersonEntity (pentity)
#
opt_pr_entity_type = SQLTable(None, "opt_pr_entity_type",
                              Field("opt_pr_entity_type", "integer",
                                    requires = IS_IN_SET(vita.trackable_types),
                                    default = vita.DEFAULT_TRACKABLE,
                                    label = T("Entity Type"),
                                    represent = lambda opt:
                                        vita.trackable_types.get(opt, UNKNOWN_OPT)))


# -----------------------------------------------------------------------------
#
def shn_pentity_represent(id,default_label="[no label]"):

    """
        Represent a Person Entity in option fields or list views
    """

    pentity_str = default = T("None (no such record)")

    table = db.pr_pentity
    pentity = db(table.id == id).select(
        table.opt_pr_entity_type,
        table.label,
        limitby=(0, 1)).first()
    if not pentity:
        return default
    entity_type = pentity.opt_pr_entity_type
    label = pentity.label or default_label

    etype = lambda entity_type: vita.trackable_types[entity_type]

    if entity_type == 1:
        table = db.pr_person
        person = db(table.pr_pe_id == id).select(
                    table.first_name,
                    table.middle_name,
                    table.last_name,
                    limitby=(0, 1))
        if person:
            person = person[0]
            pentity_str = "%s %s (%s)" % (
                vita.fullname(person),
                label,
                etype(entity_type)
            )

    elif entity_type == 2:
        table = db.pr_group
        group = db(table.pr_pe_id == id).select(
                    table.group_name,
                    limitby=(0, 1))
        if group:
            group = group[0]
            pentity_str = "%s (%s)" % (
                group.group_name,
                vita.trackable_types[entity_type]
            )

    else:
        pentity_str = "[%s] (%s)" % (
            label,
            vita.trackable_types[entity_type]
        )

    return pentity_str

# -----------------------------------------------------------------------------
#
resource = "pentity"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
#                    Field("parent"),                # Parent Entity
                    opt_pr_entity_type,              # Entity class
                    Field("label", length=128),      # Recognition Label
                    migrate=migrate)

# Field validation
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#table.label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_pentity.label"))
#table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent))

# Field representation
#table.deleted.readable = True

# Field labels
#table.parent.label = T("belongs to")

# CRUD Strings

#
# Reusable field for other tables to reference --------------------------------
#
pr_pe_id = SQLTable(None, "pr_pe_id",
                Field("pr_pe_id", db.pr_pentity,
                    requires =  IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent)),
                    represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                    ondelete = "RESTRICT",
                    label = T("ID")
                ))

#
# Person Entity Field Set -----------------------------------------------------
#
pr_pe_fieldset = SQLTable(None, "pr_pe_fieldset",
                    Field("pr_pe_id", db.pr_pentity,
                        requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent)),
                        represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                        ondelete = "RESTRICT",
                        readable = False,   # should be invisible in (most) forms
                        writable = False    # should be invisible in (most) forms
                    ),
                    #Field("pr_pe_parent", db.pr_pentity,
                        #requires =  IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.id", shn_pentity_represent)),
                        #represent = lambda id: (id and [shn_pentity_represent(id)] or ["None"])[0],
                        #ondelete = "RESTRICT",
                        #label = T("belongs to"),
                        #readable = False,   # should be invisible in (most) forms
                        #writable = False    # should be invisible in (most) forms
                    #),
                    Field("pr_pe_label", length=128,
                        label = T("ID Label"),
                        requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_pentity.label"))
                    )) # Can't be unique if we allow Null!

# -----------------------------------------------------------------------------
#
def shn_pentity_ondelete(record):

    """
        Deletes pr_pentity entries, when a subentity is deleted, used as
        delete_onaccept callback.

        crud.settings.delete_onaccept = shn_pentity_ondelete
    """

    if "pr_pe_id" in record:
        pr_pe_id = record.pr_pe_id

        delete_onvalidation = crud.settings.delete_onvalidation
        delete_onaccept = crud.settings.delete_onaccept

        crud.settings.delete_onvalidation = None
        crud.settings.delete_onaccept = None

        if db(db.s3_setting.id == 1).select().first().archive_not_delete:
            db(db.pr_pentity.id == pr_pe_id).update(deleted = True)
        else:
            crud.delete(db.pr_pentity, pr_pe_id)

        # TODO: delete joined resources!?

        crud.settings.delete_onvalidation = delete_onvalidation
        crud.settings.delete_onaccept = delete_onaccept

    return True


def shn_pentity_onaccept(form, table=None, entity_type=1):

    """
        Adds or updates a pr_pentity entries as necessary, used as
        onaccept-callback for create/update of subentities.
    """

    if "pr_pe_id" in table.fields:
        record = db(table.id == form.vars.id).select(table.pr_pe_id, table.pr_pe_label).first()
        if record:
            pr_pe_id = record.pr_pe_id
            label = record.pr_pe_label
            if pr_pe_id:
                # update action
                db(db.pr_pentity.id == pr_pe_id).update(label=label)
            else:
                # create action
                pr_pe_id = db.pr_pentity.insert(opt_pr_entity_type=entity_type,
                                                label=label)
                if pr_pe_id:
                    db(table.id == form.vars.id).update(pr_pe_id=pr_pe_id)

    return True

# *****************************************************************************
# Person (person)
#

# -----------------------------------------------------------------------------
# Gender
#
pr_person_gender_opts = {
    1:T("unknown"),
    2:T("female"),
    3:T("male")
    }

opt_pr_gender = SQLTable(None, "opt_pr_gender",
                    Field("opt_pr_gender", "integer",
                        requires = IS_IN_SET(pr_person_gender_opts),
                        default = 1,
                        label = T("Gender"),
                        represent = lambda opt: pr_person_gender_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Age Group
#
pr_person_age_group_opts = {
    1:T("unknown"),
    2:T("Infant (0-1)"),
    3:T("Child (2-11)"),
    4:T("Adolescent (12-20)"),
    5:T("Adult (21-50)"),
    6:T("Senior (50+)")
    }

opt_pr_age_group = SQLTable(None, "opt_pr_age_group",
                    Field("opt_pr_age_group", "integer",
                        requires = IS_IN_SET(pr_person_age_group_opts),
                        default = 1,
                        label = T("Age Group"),
                        represent = lambda opt:
                            pr_person_age_group_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Marital Status
#
pr_marital_status_opts = {
    1:T("unknown"),
    2:T("single"),
    3:T("married"),
    4:T("separated"),
    5:T("divorced"),
    6:T("widowed"),
    99:T("other")
}

opt_pr_marital_status = SQLTable(None, "opt_pr_marital_status",
                        Field("opt_pr_marital_status", "integer",
                            requires = IS_NULL_OR(IS_IN_SET(pr_marital_status_opts)),
                            default = 1,
                            label = T("Marital Status"),
                            represent = lambda opt:
                                opt and pr_marital_status_opts.get(opt, UNKNOWN_OPT)))

# -----------------------------------------------------------------------------
# Religion
#
pr_religion_opts = {
    1:T("none"),
    2:T("Christian"),
    3:T("Muslim"),
    4:T("Jew"),
    5:T("Bhuddist"),
    6:T("Hindu"),
    99:T("other")
    }

opt_pr_religion = SQLTable(None, "opt_pr_religion",
                    Field("opt_pr_religion", "integer",
                        requires = IS_NULL_OR(IS_IN_SET(pr_religion_opts)),
                        # default = 1,
                        label = T("Religion"),
                        represent = lambda opt: pr_religion_opts.get(opt, UNKNOWN_OPT)))

#
# Nationality and Country of Residence ----------------------------------------
#
pr_nationality_opts = shn_list_of_nations

opt_pr_nationality = SQLTable(None, "opt_pr_nationality",
                        Field("opt_pr_nationality", "integer",
                            requires = IS_NULL_OR(IS_IN_SET(pr_nationality_opts)),
                            # default = 999, # unknown
                            label = T("Nationality"),
                            represent = lambda opt: pr_nationality_opts.get(opt, UNKNOWN_OPT)))

opt_pr_country = SQLTable(None, "opt_pr_country",
                        Field("opt_pr_country", "integer",
                            requires = IS_NULL_OR(IS_IN_SET(pr_nationality_opts)),
                            # default = 999, # unknown
                            label = T("Country of Residence"),
                            represent = lambda opt: pr_nationality_opts.get(opt, UNKNOWN_OPT)))

#
# shn_pr_person_represent -----------------------------------------------------
#
def shn_pr_person_represent(id):
    table = db.pr_person
    person = db(table.id == id).select(
                table.first_name,
                table.middle_name,
                table.last_name,
                limitby=(0, 1))
    if person:
        return vita.fullname(person[0])
    else:
        return None

#
# person table ----------------------------------------------------------------
#
resource = "person"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                pr_pe_fieldset,                         # Person Entity Field Set
                Field("missing", "boolean", default=False), # Missing?
                Field("first_name", notnull=True),      # first or only name
                Field("middle_name"),                   # middle name
                Field("last_name"),                     # last name
                Field("preferred_name"),                # how the person uses to be called
                Field("local_name"),                    # name in local language and script, Sahana legacy
                opt_pr_gender,
                opt_pr_age_group,
                Field("email", length=128),             # Deprecated - see pe_contact
                Field("mobile_phone"),                  # Deprecated - see pe_contact
                # Person Details
                Field("date_of_birth", "date"),         # Sahana legacy
                opt_pr_nationality,                     # Nationality
                opt_pr_country,                         # Country of residence
                opt_pr_religion,                        # Sahana legacy
                opt_pr_marital_status,                  # Sahana legacy
                Field("occupation"),                    # Sahana legacy
                Field("comment"),                       # comment
                migrate=migrate)

# Field validation
table.date_of_birth.requires = IS_NULL_OR(IS_DATE_IN_RANGE(maximum=request.utcnow.date(),
                                        error_message="%s " % T("Enter a date before") + "%(max)s!"))
table.first_name.requires = IS_NOT_EMPTY()   # People don"t have to have unique names, some just have a single name
table.email.requires = IS_NOT_IN_DB(db, "%s.email" % tablename)     # Needs to be unique as used for AAA
table.email.requires = IS_NULL_OR(IS_EMAIL())
table.mobile_phone.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "%s.mobile_phone" % tablename))   # Needs to be unique as used for AAA
table.pr_pe_label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_person.pr_pe_label"))

# Field representation
table.pr_pe_label.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("ID Label|Number or Label on the identification tag this person is wearing (if any)."))
table.first_name.comment = SPAN(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("First name|The first or only name of the person (mandatory).")))
table.preferred_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Preferred Name|The name to be used when calling for or directly addressing the person (optional)."))
table.local_name.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Local Name|Name of the person in local language and script (optional)."))
table.email.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Email|This gets used both for signing-in to the system & for receiving alerts/updates."))
table.mobile_phone.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Mobile Phone No|This gets used both for signing-in to the system & for receiving alerts/updates."))
table.opt_pr_nationality.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Nationality|Nationality of the person."))
table.opt_pr_country.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Country of Residence|The country the person usually lives in."))

table.missing.represent = lambda missing: (missing and ["missing"] or [""])[0]

# Field labels
table.opt_pr_gender.label = T("Gender")
table.opt_pr_age_group.label = T("Age group")
table.mobile_phone.label = T("Mobile Phone #")

# CRUD Strings
ADD_PERSON = T("Add Person")
LIST_PERSONS = T("List Persons")
s3.crud_strings[tablename] = Storage(
    title_create = T("Add a Person"),
    title_display = T("Person Details"),
    title_list = LIST_PERSONS,
    title_update = T("Edit Person Details"),
    title_search = T("Search Persons"),
    subtitle_create = ADD_PERSON,
    subtitle_list = T("Persons"),
    label_list_button = LIST_PERSONS,
    label_create_button = ADD_PERSON,
    label_delete_button = T("Delete Person"),
    msg_record_created = T("Person added"),
    msg_record_modified = T("Person details updated"),
    msg_record_deleted = T("Person deleted"),
    msg_list_empty = T("No Persons currently registered"))

#
# person_id: reusable field for other tables to reference ---------------------
#
shn_person_comment = DIV(A(s3.crud_strings.pr_person.label_create_button, _class="colorbox", _href=URL(r=request, c="pr", f="person", args="create", vars=dict(format="popup")), _target="top", _title=s3.crud_strings.pr_person.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Person Entry|Create a person entry in the registry.")))
person_id = SQLTable(None, "person_id",
                FieldS3("person_id", db.pr_person, sortby=["first_name", "middle_name", "last_name"],
                    requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent)),
                    represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0],
                    comment = shn_person_comment,
                    ondelete = "RESTRICT"
                ))

s3xrc.model.configure(table,
    onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_person, entity_type=1),
    delete_onaccept=lambda form: shn_pentity_ondelete(form))


# *****************************************************************************
# Group (group)
#

#
# Group types -----------------------------------------------------------------
#
pr_group_type_opts = {
    1:T("Family"),
    2:T("Tourist Group"),
    3:T("Relief Team"),
    4:T("other")
    }

opt_pr_group_type = SQLTable(None, "opt_pr_group_type",
                    Field("opt_pr_group_type", "integer",
                        requires = IS_IN_SET(pr_group_type_opts),
                        default = 4,
                        label = T("Group Type"),
                        represent = lambda opt: pr_group_type_opts.get(opt, UNKNOWN_OPT)))

#
# group table -----------------------------------------------------------------
#
resource = "group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                pr_pe_fieldset,                                 # Person Entity Field Set
                opt_pr_group_type,                              # group type
                Field("system","boolean",default=False),        # System internal? (e.g. users?)
                Field("group_name"),                            # Group name (optional? => No!)
                Field("group_description"),                     # Group short description
#                Field("group_head"),                           # Sahana legacy
#                Field("no_of_adult_males", "integer"),         # Sahana legacy
#                Field("no_of_adult_females", "integer"),       # Sahana legacy
#                Field("no_of_children", "integer"),            # Sahana legacy
#                Field("no_of_children_males", "integer"),      # by Khushbu
#                Field("no_of_children_females", "integer"),    # by Khushbu
#                Field("no_of_displaced", "integer"),           # Sahana legacy
#                Field("no_of_missing", "integer"),             # Sahana legacy
#                Field("no_of_dead", "integer"),                # Sahana legacy
#                Field("no_of_rehabilitated", "integer"),       # Sahana legacy
#                Field("checklist", "text"),                    # Sahana legacy
#                Field("description", "text"),                  # Sahana legacy
                Field("comment"),                               # optional comment
                migrate=migrate)

# Field validation

# Field representation
table.pr_pe_label.readable = False
table.pr_pe_label.writable = False
table.system.readable = False
table.system.writable = False
table.pr_pe_label.requires = IS_NULL_OR(IS_NOT_IN_DB(db, "pr_group.pr_pe_label"))

# Field labels
table.opt_pr_group_type.label = T("Group type")
table.group_name.label = T("Group name")
table.group_description.label = T("Group description")

# CRUD Strings
ADD_GROUP = T("Add Group")
LIST_GROUPS = T("List Groups")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_GROUP,
    title_display = T("Group Details"),
    title_list = LIST_GROUPS,
    title_update = T("Edit Group"),
    title_search = T("Search Groups"),
    subtitle_create = T("Add New Group"),
    subtitle_list = T("Groups"),
    label_list_button = LIST_GROUPS,
    label_create_button = ADD_GROUP,
    label_delete_button = T("Delete Group"),
    msg_record_created = T("Group added"),
    msg_record_modified = T("Group updated"),
    msg_record_deleted = T("Group deleted"),
    msg_list_empty = T("No Groups currently registered"))

#
# group_id: reusable field for other tables to reference ----------------------
#
group_id = SQLTable(None, "group_id",
                FieldS3("group_id", db.pr_group, sortby="group_name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id", "%(id)s: %(group_name)s", filterby="system", filter_opts=(False,))),
                    represent = lambda id: (id and [db(db.pr_group.id==id).select()[0].group_name] or ["None"])[0],
                    comment = DIV(A(s3.crud_strings.pr_group.label_create_button, _class="colorbox", _href=URL(r=request, c="pr", f="group", args="create", vars=dict(format="popup")), _target="top", _title=s3.crud_strings.pr_group.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Create Group Entry|Create a group entry in the registry."))),
                    ondelete = "RESTRICT"
                ))

s3xrc.model.configure(table,
    onaccept=lambda form: shn_pentity_onaccept(form, table=db.pr_group, entity_type=2),
    delete_onaccept=lambda form: shn_pentity_ondelete(form))

# *****************************************************************************
# Functions:
#
def shn_pr_person_list_fields():

    list_fields = ["id",
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "opt_pr_nationality",
            "missing"]

    return list_fields

# -----------------------------------------------------------------------------
#
def shn_pr_person_search_simple(xrequest, **attr):

    """
        Simple search form for persons
    """

    if attr is None:
        attr = {}

    table = db.pr_person

    if not shn_has_permission("read", table):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, args="search_simple", vars=request.vars)}))

    if xrequest.representation == "html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f="person", args="[id]"))

        # Custom view
        response.view = "%s/person_search.html" % xrequest.prefix

        # Title and subtitle
        title = T("Search for a Person")
        subtitle = T("Matching Records")

        # Select form
        form = FORM(TABLE(
                TR(T("Name and/or ID Label: "),
                   INPUT(_type="text", _name="label", _size="40"),
                   A(SPAN("[Help]"), _class="tooltip", _title=T("Name and/or ID Label|To search for a person, enter any of the first, middle or last names and/or the ID label of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            results = s3xrc.search_simple(db.pr_person,
                fields = ["pr_pe_label", "first_name", "middle_name", "last_name"],
                label = form.vars.label)

            if results and len(results):
                query = table.id.belongs(results)
            else:
                query = (table.id == 0)
                rows = None

            # Add filter
            if response.s3.filter:
                response.s3.filter = (response.s3.filter) & (query)
            else:
                response.s3.filter = (query)

            xrequest.id = None

            # Get report from HTML exporter
            report = shn_list(xrequest,
                              listadd=False,
                              list_fields=shn_pr_person_list_fields())

            output.update(dict(report))

        # Title and subtitle
        title = T("List of persons")
        subtitle = T("Matching Records")
        output.update(title=title, subtitle=subtitle)

        # Custom view
        response.view = "%s/person_search.html" % xrequest.prefix

        try:
            label_create_button = s3.crud_strings["pr_person"].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f="person", args="create"), _class="action-btn")

        output.update(add_btn=add_btn)
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, "person", method="search_simple", action=shn_pr_person_search_simple )

# -----------------------------------------------------------------------------
#
def shn_pr_pheader(resource, record_id, representation, next=None, same=None):

    """
        Person Registry page headers
    """

    if resource == "person":
        if representation == "html":

            if next:
                _next = next
            else:
                _next = URL(r=request, f=resource, args=["read"])

            if same:
                _same = same
            else:
                _same = URL(r=request, f=resource, args=["read", "[id]"])

            person = vita.person(record_id)

            if person:
                pheader = DIV(TABLE(
                    TR(
                        TH(T("Name: ")),
                        vita.fullname(person),
                        TH(T("ID Label: ")),
                        "%(pr_pe_label)s" % person,
                        TH(A(T("Clear Selection"),
                            _href=URL(r=request, f="person", args="clear", vars={"_next": _same})))
                        ),
                    TR(
                        TH(T("Date of Birth: ")),
                        "%s" % (person.date_of_birth or T("unknown")),
                        TH(T("Gender: ")),
                        "%s" % pr_person_gender_opts.get(person.opt_pr_gender, T("unknown")),
                        TH(""),
                        ),
                    TR(
                        TH(T("Nationality: ")),
                        "%s" % pr_nationality_opts.get(person.opt_pr_nationality, T("unknown")),
                        TH(T("Age Group: ")),
                        "%s" % pr_person_age_group_opts.get(person.opt_pr_age_group, T("unknown")),
                        TH(A(T("Edit Person"),
                            _href=URL(r=request, f="person", args=["update", record_id], vars={"_next": _next})))
                        )
                #), DIV(
                        #A(T("Images"), _href=URL(r=request, f="person", args=[record_id, "image"], vars={"_next": _next})),
                        #A(T("Identity"), _href=URL(r=request, f="person", args=[record_id, "identity"], vars={"_next": _next})),
                        #A(T("Addresses"), _href=URL(r=request, f="person", args=[record_id, "address"], vars={"_next": _next})),
                        #A(T("Contact Information"), _href=URL(r=request, f="person", args=[record_id, "pe_contact"], vars={"_next": _next})),
                        #A(T("Presence Log"), _href=URL(r=request, f="person", args=[record_id, "presence"], vars={"_next": _next})),
                        #_class="pheader_tabs"
                ))
                return pheader

        else:
            pass

    elif resource == "group":
        pass
    else:
        pass

    return None

#
# END
# *****************************************************************************
