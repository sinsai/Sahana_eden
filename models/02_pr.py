# -*- coding: utf-8 -*-

""" S3 Person Registry

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "pr"

# *****************************************************************************
# Person Entity
#
pr_pe_types = Storage(
    pr_person = T("Person"),
    pr_group = T("Group"),
    org_organisation = T("Organization"),
    org_office = T("Office"),
    dvi_body = T("Body")
)

resource = "pentity"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("pe_id", "id"),
                        Field("pe_type"),
                        Field("uuid", length=128),
                        #Field("pe_id", "integer"),
                        Field("pe_label", length=128),
                        migrate=migrate, *s3_deletion_status())


table.pe_type.writable = False
table.pe_type.represent = lambda opt: pr_pe_types.get(opt, opt)
table.uuid.writable = False
table.pe_label.writable = False


# -----------------------------------------------------------------------------
def shn_pentity_represent(id, default_label="[no label]"):

    """
        Represent a Person Entity in option fields or list views
    """

    pe_str = T("None (no such record)")

    pe_table = db.pr_pentity
    pe = db(pe_table.pe_id == id).select(pe_table.pe_type,
                                         pe_table.pe_label,
                                         limitby=(0, 1)).first()
    if not pe:
        return pe_str

    pe_type = pe.pe_type
    pe_type_nice = pe_table.pe_type.represent(pe_type)

    table = db.get(pe_type, None)
    if not table:
        return pe_str

    label = pe.pe_label or default_label

    if pe_type == "pr_person":
        person = db(table.pe_id == id).select(
                    table.first_name, table.middle_name, table.last_name,
                    limitby=(0, 1)).first()
        if person:
            pe_str = "%s %s (%s)" % (
                vita.fullname(person), label, pe_type_nice
            )

    elif pe_type == "pr_group":
        group = db(table.pe_id == id).select(
                   table.name,
                   limitby=(0, 1)).first()
        if group:
            pe_str = "%s (%s)" % (
                group.name, pe_type_nice
            )

    elif pe_type == "org_organisation":
        organisation = db(table.pe_id == id).select(
                          table.name,
                          limitby=(0, 1)).first()
        if organisation:
            pe_str = "%s (%s)" % (
                organisation.name, pe_type_nice
            )

    elif pe_type == "org_office":
        office = db(table.pe_id == id).select(
                    table.name,
                    limitby=(0, 1)).first()
        if office:
            pe_str = "%s (%s)" % (
                office.name, pe_type_nice
            )

    else:
        pe_str = "[%s] (%s)" % (
            label,
            pe_type_nice
        )

    return pe_str


# -----------------------------------------------------------------------------
pe_label = S3ReusableField("pe_label", length=128,
                           label = T("ID Label"),
                           requires = IS_NULL_OR(IS_NOT_IN_DB(db,
                                      "pr_pentity.pe_label")))

pe_id = S3ReusableField("pe_id", db.pr_pentity,
                        requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.pe_id", shn_pentity_represent, orderby="pr_pentity.pe_id")),
                        represent = lambda id: (id and [shn_pentity_represent(id)] or [NONE])[0],
                        readable = False,
                        writable = False,
                        ondelete = "RESTRICT")


# -----------------------------------------------------------------------------
def shn_pentity_ondelete(record):

    uid = record.get("uuid", None)

    if uid:

        pentity = db.pr_pentity
        db(pentity.uuid == uid).update(deleted=True)

    return True


# -----------------------------------------------------------------------------
def shn_pentity_onaccept(form, table=None):

    if not "uuid" in table.fields or "id" not in form.vars:
        return False

    id = form.vars.id

    if "pe_label" in table.fields:
        fields = [table.id, table.uuid, table.pe_label]
    else:
        fields = [table.id, table.uuid]
    if "missing" in table.fields:
        fields.append(table.missing)
    record = db(table.id == id).select(limitby=(0,1), *fields).first()

    if record:

        pentity = db.pr_pentity
        uid = record.uuid

        pe = db(pentity.uuid == uid).select(pentity.pe_id, limitby=(0,1)).first()
        if pe:
            values = dict(pe_id = pe.pe_id)
            if "pe_label" in record:
                values.update(pe_label = record.pe_label)
            db(pentity.uuid == uid).update(**values)
        else:
            pe_type = table._tablename
            pe_label = record.get("pe_label", None)
            pe_id = pentity.insert(uuid=uid, pe_label=pe_label, pe_type=pe_type)
            #db(pentity.id == pe_id).update(pe_id=pe_id, deleted=False)
            db(table.id == id).update(pe_id=pe_id)

        # If a person gets added in MPR, then redirect to missing report
        if request.controller == "mpr" and \
           table._tablename == "pr_person" and \
           record.missing == True:
            response.s3.mpr_next = URL(r=request, c="mpr", f="person", args=[record.id, "missing_report"])

        return True

    else:
        return False


# *****************************************************************************
# Person
#

# -----------------------------------------------------------------------------
pr_gender_opts = {
    1:T("unknown"),
    2:T("female"),
    3:T("male")
}

pr_gender = S3ReusableField("gender", "integer",
                            requires = IS_IN_SET(pr_gender_opts, zero=None),
                            default = 1,
                            label = T("Gender"),
                            represent = lambda opt: \
                                        pr_gender_opts.get(opt, UNKNOWN_OPT))


# -----------------------------------------------------------------------------
pr_age_group_opts = {
    1:T("unknown"),
    2:T("Infant (0-1)"),
    3:T("Child (2-11)"),
    4:T("Adolescent (12-20)"),
    5:T("Adult (21-50)"),
    6:T("Senior (50+)")
}

pr_age_group = S3ReusableField("age_group", "integer",
                               requires = IS_IN_SET(pr_age_group_opts, zero=None),
                               default = 1,
                               label = T("Age Group"),
                               represent = lambda opt: \
                                           pr_age_group_opts.get(opt, UNKNOWN_OPT))


# -----------------------------------------------------------------------------
pr_marital_status_opts = {
    1:T("unknown"),
    2:T("single"),
    3:T("married"),
    4:T("separated"),
    5:T("divorced"),
    6:T("widowed"),
    99:T("other")
}

pr_marital_status = S3ReusableField("marital_status", "integer",
                                    requires = IS_NULL_OR(IS_IN_SET(pr_marital_status_opts)),
                                    default = 1,
                                    label = T("Marital Status"),
                                    represent = lambda opt: opt and \
                                                pr_marital_status_opts.get(opt, UNKNOWN_OPT))


# -----------------------------------------------------------------------------
pr_religion_opts = deployment_settings.get_L10n_religions()

pr_religion = S3ReusableField("religion",
                              requires = IS_EMPTY_OR(IS_IN_SET(pr_religion_opts)),
                              label = T("Religion"),
                              represent = lambda opt: opt and \
                                          pr_religion_opts.get(opt, UNKNOWN_OPT))


# -----------------------------------------------------------------------------
# Tags for the impact of the disaster on a person (formerly "victim status")
# NOTE: "Missing" is defined elsewhere, because this doesn't impact the person
#
pr_impact_tags = {
    1: T("injured"),
    4: T("diseased"),
    2: T("displaced"),
    5: T("separated from family"),
    3: T("suffered financial losses")
}

# -----------------------------------------------------------------------------
pr_nations = s3_list_of_nations

pr_country = S3ReusableField("country", "string", length=2,
                             requires = IS_NULL_OR(IS_IN_SET(pr_nations, sort=True)),
                             label = T("Country of Residence"),
                             represent = lambda opt: \
                                         pr_nations.get(opt, UNKNOWN_OPT))


# -----------------------------------------------------------------------------
def shn_pr_person_represent(id):

    def _represent(id):
        table = db.pr_person
        person = db(table.id == id).select(
                    table.first_name,
                    table.middle_name,
                    table.last_name,
                    limitby=(0, 1))
        if person:
            return vita.fullname(person.first())
        else:
            return None

    name = cache.ram("pr_person_%s" % id, lambda: _represent(id), time_expire=10)
    return name


# -----------------------------------------------------------------------------
resource = "person"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
                        pe_label(),
                        Field("missing", "boolean", default=False),
                        Field("first_name", notnull=True),
                        Field("middle_name"),
                        Field("last_name"),
                        Field("preferred_name"),
                        Field("local_name"),
                        pr_gender(),
                        pr_age_group(),
                        Field("date_of_birth", "date"),
                        pr_country("nationality"),
                        pr_country("country"),
                        pr_religion(),
                        pr_marital_status(),
                        Field("occupation"),
                        Field("tags", "list:integer"),
                        comments(),
                        migrate=migrate, *s3_meta_fields())


table.date_of_birth.requires = IS_NULL_OR(IS_DATE_IN_RANGE(
                               maximum=request.utcnow.date(),
                               error_message="%s " % T("Enter a date before") + "%(max)s!"))

table.first_name.requires = IS_NOT_EMPTY()
table.first_name.requires.error_message = T("Please enter a First Name")

table.pe_label.comment = DIV(DIV(_class="tooltip",
    _title=T("ID Label") + "|" + T("Number or Label on the identification tag this person is wearing (if any).")))
table.first_name.comment =  DIV(SPAN("*", _class="req", _style="padding-right: 5px;"), DIV(_class="tooltip",
    _title=T("First name") + "|" + T("The first or only name of the person (mandatory).")))
table.preferred_name.comment = DIV(DIV(_class="tooltip",
    _title=T("Preferred Name") + "|" + T("The name to be used when calling for or directly addressing the person (optional).")))
table.local_name.comment = DIV(DIV(_class="tooltip",
    _title=T("Local Name") + "|" + T("Name of the person in local language and script (optional).")))
table.nationality.comment = DIV(DIV(_class="tooltip",
    _title=T("Nationality") + "|" + T("Nationality of the person.")))
table.country.comment = DIV(DIV(_class="tooltip",
    _title=T("Country of Residence") + "|" + T("The country the person usually lives in.")))

table.missing.represent = lambda missing: (missing and ["missing"] or [""])[0]

table.gender.label = T("Gender")
table.age_group.label = T("Age group")

table.tags.label = T("Personal impact of disaster")
table.tags.comment = DIV(DIV(_class="tooltip",
    _title=T("Personal impact of disaster") + "|" + T("How is this person affected by the disaster? (Select all that apply)")))
table.tags.requires = IS_EMPTY_OR(IS_IN_SET(pr_impact_tags, zero=None, multiple=True))
table.tags.represent = lambda opt: opt and \
                       ", ".join([str(pr_impact_tags.get(o, UNKNOWN_OPT)) for o in opt]) or ""

# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
shn_person_comment = lambda title, comment: \
    DIV(A(ADD_PERSON,
        _class="colorbox",
        _href=URL(r=request, c="pr", f="person", args="create", vars=dict(format="popup")),
        _target="top",
        _title=ADD_PERSON),
    DIV(DIV(_class="tooltip",
        _title="%s|%s" % (title, comment))))

shn_person_id_comment = shn_person_comment(
    T("Person"),
    T("Select the person associated with this scenario."))

person_id = S3ReusableField("person_id", db.pr_person,
                            sortby = ["first_name", "middle_name", "last_name"],
                            requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id",
                                                            shn_pr_person_represent,
                                                            orderby="pr_person.first_name",
                                                            sort=True)),
                            represent = lambda id: (id and \
                                        [shn_pr_person_represent(id)] or [NONE])[0],
                            label = T("Person"),
                            comment = shn_person_id_comment,
                            ondelete = "RESTRICT")

# -----------------------------------------------------------------------------
def pr_person_onvalidation(form):

    try:
        age = int(form.vars.get("age_group", None))
    except ValueError:
        age = None
    dob = form.vars.get("date_of_birth", None)

    if age and age != 1 and dob:
        now = request.utcnow
        dy = int((now.date() - dob).days / 365.25)
        if dy < 1:
            ag = 1
        elif dy < 2:
            ag = 2
        elif dy < 12:
            ag = 3
        elif dy < 21:
            ag = 4
        elif dy < 51:
            ag = 5
        else:
            ag = 6

        if age != ag:
            form.errors.age_group = T("Age group does not match actual age.")
            return False

    return True

# -----------------------------------------------------------------------------
s3xrc.model.configure(table,
    onvalidation=lambda form: pr_person_onvalidation(form),
    onaccept=lambda form, table=table: shn_pentity_onaccept(form, table=table),
    delete_onaccept=lambda form: shn_pentity_ondelete(form),
    list_fields = [
        "id",
        "first_name",
        "middle_name",
        "last_name",
        "gender",
        "age_group"
    ])


# *****************************************************************************
# Group (group)
#

# -----------------------------------------------------------------------------
pr_group_type_opts = {
    1:T("Family"),
    2:T("Tourist Group"),
    3:T("Relief Team"),
    4:T("other")
}

pr_group_type = S3ReusableField("group_type", "integer",
                                requires = IS_IN_SET(pr_group_type_opts, zero=None),
                                default = 4,
                                label = T("Group Type"),
                                represent = lambda opt: \
                                            pr_group_type_opts.get(opt, UNKNOWN_OPT))


# -----------------------------------------------------------------------------
resource = "group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        pe_id(),
                        pr_group_type(),
                        Field("system","boolean",default=False),
                        Field("name"),
                        Field("description"),
                        comments(),
                        migrate=migrate, *s3_meta_fields())



table.system.readable = False
table.system.writable = False
table.group_type.label = T("Group type")
table.name.label = T("Group name")
table.name.requires = IS_NOT_EMPTY()
table.name.comment = DIV(SPAN("*", _class="req", _style="padding-right: 5px;"))

table.description.label = T("Group description")
table.description.comment = DIV(DIV(_class="tooltip",
    _title=T("Group description") + "|" + T("A brief description of the group (optional)")))

# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
group_id = S3ReusableField("group_id", db.pr_group,
                           sortby="name",
                           requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id",
                                                           "%(id)s: %(name)s",
                                                           filterby="system",
                                                           filter_opts=(False,))),
                           represent = lambda id: (id and \
                                       [db(db.pr_group.id == id).select(db.pr_group.name, limitby=(0, 1)).first().name] or [NONE])[0],
                           comment = \
                                DIV(A(s3.crud_strings.pr_group.label_create_button,
                                    _class="colorbox",
                                    _href=URL(r=request, c="pr", f="group", args="create", vars=dict(format="popup")),
                                    _target="top",
                                    _title=s3.crud_strings.pr_group.label_create_button),
                                DIV(DIV(_class="tooltip",
                                    _title=T("Create Group Entry") + "|" + T("Create a group entry in the registry.")))),
                           ondelete = "RESTRICT")

# -----------------------------------------------------------------------------
s3xrc.model.configure(table,
    onaccept=lambda form, table=table: shn_pentity_onaccept(form, table=table),
    delete_onaccept=lambda form: shn_pentity_ondelete(form))


# *****************************************************************************
# Group membership
#
resource = "group_membership"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        group_id(),
                        person_id(),
                        Field("group_head", "boolean", default=False),
                        Field("description"),
                        comments(),
                        migrate=migrate, *s3_meta_fields())


table.group_head.represent = lambda group_head: (group_head and [T("yes")] or [""])[0]

table.group_id.label = T("Group")
table.person_id.label = T("Person")


# -----------------------------------------------------------------------------
s3xrc.model.add_component(module, resource,
                          multiple=True,
                          joinby=dict(pr_group="group_id",
                                      pr_person="person_id"),
                          deletable=True,
                          editable=True)

s3xrc.model.configure(table,
    list_fields=[
        "id",
        "group_id",
        "person_id",
        "group_head",
        "description"
    ])


# -----------------------------------------------------------------------------
if request.function in ("person", "group_membership"):
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Membership"),
        title_display = T("Membership Details"),
        title_list = T("Memberships"),
        title_update = T("Edit Membership"),
        title_search = T("Search Membership"),
        subtitle_create = T("Add New Membership"),
        subtitle_list = T("Current Memberships"),
        label_list_button = T("List All Memberships"),
        label_create_button = T("Add Membership"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Membership added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Memberships currently registered"))
elif request.function == "group":
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Group Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Group Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Group Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))


# *****************************************************************************
# Functions:
#
def shn_pr_person_search_simple(r, **attr):

    """ Simple search form for persons """

    resource = r.resource
    table = resource.table

    r.id = None

    # Check permission
    if not shn_has_permission("read", table):
        r.unauthorised()

    if r.representation == "html":

        # Check for redirection
        next = r.request.vars.get("_next", None)
        if not next:
            next = URL(r=request, f="person", args="[id]")

        # Select form
        form = FORM(TABLE(
                TR(T("Name and/or ID") + ": ",
                   INPUT(_type="text", _name="label", _size="40"),
                   DIV(DIV(_class="tooltip",
                           _title=T("Name and/or ID") + "|" + T("To search for a person, enter any of the first, middle or last names and/or an ID number of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons.")))),
                TR("", INPUT(_type="submit", _value=T("Search")))))

        output = dict(form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session, keepvalues=True):

            if form.vars.label == "":
                form.vars.label = "%"

            # Search
            results = s3xrc.search_simple(table,
                        fields = ["pe_label",
                                  "first_name",
                                  "middle_name",
                                  "last_name",
                                  "identity.value"],
                        label = form.vars.label)

            # Get the results
            if results:
                resource.build_query(id=results)
                report = shn_list(r, listadd=False)
            else:
                report = dict(items=T("No matching records found."))

            output.update(dict(report))

        # Title and subtitle
        title = T("Search for a Person")
        subtitle = T("Matching Records")

        # Add-button
        label_create_button = shn_get_crud_string("pr_person", "label_create_button")
        add_btn = A(label_create_button, _class="action-btn",
                    _href=URL(r=request, f="person", args="create"))

        output.update(title=title, subtitle=subtitle, add_btn=add_btn)
        response.view = "search_simple.html"
        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, "person", method="search_simple", action=shn_pr_person_search_simple )

# -----------------------------------------------------------------------------
#
def shn_pr_rheader(jr, tabs=[]):

    """ Person Registry page headers """

    if jr.representation == "html":

        rheader_tabs = shn_rheader_tabs(jr, tabs)

        if jr.name == "person":

            _next = jr.here()
            _same = jr.same()

            person = jr.record

            if person:
                rheader = DIV(TABLE(

                    TR(TH(T("Name") + ": "),
                       vita.fullname(person),
                       TH(T("ID Label") + ": "),
                       "%(pe_label)s" % person),

                    TR(TH(T("Date of Birth") + ": "),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH(T("Gender") + ": "),
                       "%s" % pr_gender_opts.get(person.gender, T("unknown"))),

                    TR(TH(T("Nationality") + ": "),
                       "%s" % pr_nations.get(person.nationality, T("unknown")),
                       TH(T("Age Group") + ": "),
                       "%s" % pr_age_group_opts.get(person.age_group, T("unknown"))),

                    #))
                    ), rheader_tabs)

                return rheader

        elif jr.name == "group":

            _next = jr.here()
            _same = jr.same()

            group = jr.record

            if group:
                rheader = DIV(TABLE(

                    TR(TH(T("Name") + ": "),
                       group.name,
                       TH(""),
                       ""),
                    TR(TH(T("Description") + ": "),
                       group.description,
                       TH(""),
                       "")

                    ), rheader_tabs)

                return rheader

    return None

#
# END
# *****************************************************************************
