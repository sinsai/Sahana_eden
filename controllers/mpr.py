# -*- coding: utf-8 -*-

""" MPR Missing Person Registry, Controllers
    (Part of VITA)

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
    @version: 1.0.0

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
def shn_menu():

    """ Options menu """

    response.menu_options = [
        [T("Search for a Person"), False, URL(r=request, f="index")],
        [T("Missing Persons"), False, URL(r=request, f="person"), [
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]]]

    menu_selected = []
    if session.rcvars and "pr_person" in session.rcvars:
        person = db.pr_person
        query = (person.id == session.rcvars["pr_person"])
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = shn_pr_person_represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                 URL(r=request, f="person", args=[record.id])])

    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)


shn_menu()


# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    # Module's nice name
    try:
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Missing Persons")

    # Override prefix and resourcename
    prefix = "pr"
    resourcename = "person"

    # Choose table
    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Configure redirection and list fields
    report_url = URL(r=request, c="mpr", f=resourcename,
                     args=["[id]", "missing_report"])
    s3xrc.model.configure(table,
                          create_next =report_url,
                          list_fields=["id",
                                       "first_name",
                                       "middle_name",
                                       "last_name",
                                       "gender",
                                       "age_group",
                                       "missing"])

    # Pre-process
    def prep(r):

        """ Redirect to search_simple/person view """

        if r.representation == "html":
            if not r.id:
                r.method = "search_simple"
                r.custom_action = shn_pr_person_search_simple
            else:
               redirect(URL(r=request, f=resourcename, args=[r.id]))
        return True


    # Post-process
    def postp(r, output):

        """ Custom action buttons """

        response.s3.actions = []

        # Button labels
        MISSING = str(T("Missing"))
        SEEN = str(T("Seen"))
        FOUND = str(T("Found"))
        DETAILS = str(T("Details"))

        if not r.component:
            open_button_label = DETAILS

            if auth.shn_logged_in():

                # Define URLs
                report_missing = str(URL(r=request, f=resourcename,
                                         args=["[id]", "missing_report"]))
                #report_seen = str(URL(r=request, f=resourcename,
                                      #args=["[id]", "presence"],
                                      #vars=dict(condition=vita.SEEN)))
                report_found = str(URL(r=request, f=resourcename,
                                       args=["[id]", "presence"],
                                       vars=dict(condition=vita.CONFIRMED)))

                # Set action buttons
                response.s3.actions = [
                    dict(label=MISSING, _class="action-btn", url=report_missing),
                    #dict(label=SEEN, _class="action-btn", url=report_seen),
                    dict(label=FOUND, _class="action-btn", url=report_found),
                ]

                # Is the current user reported missing?
                if isinstance(output, dict):
                    person = db(table.uuid == session.auth.user.person_uuid)
                    person = person.select(table.id, table.missing,
                                           limitby=(0, 1)).first()
                    if person and person.missing:
                        myself = URL(r=request, f=resourcename,
                                     args=[person.id, "presence"],
                                     vars=dict(condition=vita.CONFIRMED))
                        output.update(myself=myself)

        else:
            open_button_label = UPDATE

        # Always have an Open-button
        linkto = r.resource.crud._linkto(r, update=True)("[id]")
        response.s3.actions.append(dict(label=open_button_label,
                                        _class="action-btn", url=linkto))

        return output

    # Set hooks
    response.s3.prep = prep
    response.s3.postp = postp

    # REST controller
    output = s3_rest_controller("pr", "person", module_name=module_name)

    # Set view, update menu and return output
    response.view = "mpr/index.html"
    shn_menu()
    return output


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    prefix = "pr"

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    s3.crud_strings[tablename].update(
        title_display = T("Missing Person Details"),
        title_list = T("Missing Persons Registry"),
        subtitle_list = T("Missing Persons"),
        label_list_button = T("List Missing Persons"),
        msg_list_empty = T("No Persons currently reported missing"))

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    s3xrc.model.configure(table,
        # Redirect to missing report when a new person has been added
        create_next = URL(r=request, c="mpr", f="person", args=["[id]", "missing_report"]),
        list_fields=["id",
                     "first_name",
                     "middle_name",
                     "last_name",
                     "gender",
                     "age_group",
                     "missing"])

    def person_prep(r):

        # Pre-populate reporter fields
        if auth.shn_logged_in():
            persons = db.pr_person
            person = db(persons.uuid == session.auth.user.person_uuid).select(persons.id, limitby=(0,1)).first()
            if person:
                db.pr_presence.reporter.default = person.id
                db.pr_presence.reporter.writable = False
                db.pr_presence.reporter.comment = None
                db.mpr_missing_report.reporter.default = person.id
                db.mpr_missing_report.reporter.writable = False
                db.mpr_missing_report.reporter.comment = None

        # Copy config
        if r.component_name == "config":
            _config = db.gis_config
            defaults = db(_config.id == 1).select(limitby=(0, 1)).first()
            for key in defaults.keys():
                if key not in ["id", "uuid", "mci", "update_record", "delete_record"]:
                    _config[key].default = defaults[key]

        # Pre-populate presence condition from URL vars
        elif r.component_name == "presence":
            condition = r.request.vars.get("condition", None)
            if condition:
                try:
                    condition = int(condition)
                except:
                    pass
                else:
                    table = db.pr_presence
                    table.presence_condition.default = condition
                    table.presence_condition.readable = False
                    table.presence_condition.writable = False
                    if condition in vita.PERSISTANT_PRESENCE or \
                       condition in vita.ABSENCE:
                        s3xrc.model.configure(table,
                            mark_required=["location_id", "shelter_id"])
                    table.orig_id.readable = False
                    table.orig_id.writable = False
                    table.dest_id.readable = False
                    table.dest_id.writable = False
                    table.observer.readable = False
                    table.observer.writable = False

        return True

    response.s3.prep = person_prep

    def person_postp(r, output):

        # Action buttons
        if r.interactive:
            if not r.component:
                label = READ
                linkto = URL(r=request, f="person", args=("[id]", "missing_report"))
            else:
                label = UPDATE
                linkto = s3xrc.crud._linkto(r)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))]
            if not r.component:
                label = T("Found")
                linkto = URL(r=request, f="person",
                             args=("[id]", "presence"),
                             vars=dict(condition=vita.CONFIRMED))
                response.s3.actions.append(
                    dict(label=str(label), _class="action-btn", url=str(linkto)))
            elif r.component_name == "presence":
                if "showaddbtn" in output:
                    del output["showaddbtn"]
        return output
    response.s3.postp = person_postp

    # Disable missing flag in person
    db.pr_person.missing.readable = False
    db.pr_person.missing.writable = False
    db.pr_person.missing.default = True

    # Disable person_id in missing report
    db.mpr_missing_report.person_id.readable = False
    db.mpr_missing_report.person_id.writable = False

    # Show only missing persons in list views
    if len(request.args) == 0:
        response.s3.filter = (db.pr_person.missing == True)

    # Resource header and tab list
    mpr_tabs = [(T("Missing Report"), "missing_report"),
                (T("Person Details"), None),
                (T("Physical Description"), "physical_description"),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "pe_contact"),
                (T("Presence Log"), "presence")]

    rheader = lambda r: shn_pr_rheader(r, tabs=mpr_tabs)

    # REST controller
    output = s3_rest_controller("pr", resourcename, rheader=rheader)

    # Update menu and return output
    shn_menu()
    return output


# -----------------------------------------------------------------------------
def download():

    """ Download a file. """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()


# -----------------------------------------------------------------------------
