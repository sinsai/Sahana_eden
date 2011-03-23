# -*- coding: utf-8 -*-

""" Volunteer Management System """

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions)
def shn_menu():
    menu = [
        #[T("Home"), False, aURL(r=request, f="index")],
        [T("Projects"), False, aURL(r=request, f="project"),[
            [T("List"), False, aURL(r=request, f="project")],
            [T("Search"), False, aURL(r=request, f="project", args="search_location")],
            [T("Add Project"), False, aURL(p="create", r=request, f="project", args="create")],
        ]],
    ]
    if session.rcvars and "project_project" in session.rcvars:
        project_id = session.rcvars["project_project"]
        selection = db.project_project[project_id]
        if selection:
            menu_project = [
                    ["%s: %s" % (T("Project"), selection.code), False, aURL(r=request, f="project", args=[project_id]),[
                        [T("Tasks"), False, aURL(r=request, f="project", args=[project_id, "task"])],
                        # Staff cannot be a component of Project since staff may be assigned to many projects
                        #[T("Staff"), False, URL(r=request, f="project", args=[project_id, "staff"])],
                    ]]
            ]
            menu.extend(menu_project)

    menu_teams = [
        [T("Teams"), False, aURL(r=request, f="group"),[
            [T("List"), False, aURL(r=request, f="group")],
            [T("Add"), False, aURL(p="create", r=request, f="group", args="create")],
        ]]
    ]
    menu.extend(menu_teams)
    if session.rcvars and "pr_group" in session.rcvars:
        group_id = session.rcvars["pr_group"]
        selection = db.pr_group[group_id]
        if selection:
            team_name = shn_pr_group_represent(group_id)
            menu_teams = [
                ["%s: %s" % (T("Team"), team_name), False, aURL(r=request, f="group", args=[group_id, "read"]),[
                    [T("View On Map"), False, aURL(r=request, f="view_team_map", args=[group_id])],
                    [T("Send Notification"), False, aURL(r=request, f="compose_group", vars={"group_id":group_id})],
                    #[T("Find Volunteers"), False, aURL(r=request, f="skillSearch")],
                ]],
            ]
            menu.extend(menu_teams)

    menu_persons = [
        [T("Volunteers"), False, aURL(r=request, f="index"),[
            [T("List"), False, aURL(r=request, f="person")],
            [T("Search"), False, aURL(r=request, f="person", args=["search"])],
            [T("Add"), False, aURL(p="create", r=request, f="person", args="create")],
            #[T("Find Volunteers"), False, aURL(r=request, f="skillSearch")],
        ]]
    ]
    menu.extend(menu_persons)
    if session.rcvars and "pr_person" in session.rcvars:
        person_id = session.rcvars["pr_person"]
        selection = db.pr_person[person_id]
        if selection:
            person_name = shn_pr_person_represent(person_id)
            menu_person = [
                ["%s: %s" % (T("Person"), person_name), False, aURL(r=request, f="person", args=[person_id, "read"]),[
                    # The default tab is pr_person, which is fine here.
                    [T("Show Details"), False, aURL(r=request, f="person", args=[person_id])],
                    [T("View On Map"), False, aURL(r=request, f="view_map", args=[person_id])],
                    [T("Send Notification"), False, URL(r=request, f="compose_person", vars={"person_id":person_id})],
                ]],
            ]
            menu.extend(menu_person)
    menu_skills = [
        [T("Skills"), False, aURL(r=request, f="skill")],
    ]
    menu.extend(menu_skills)
    if auth.user is not None:
        menu_user = [
            [T("My Tasks"), False, aURL(r=request, f="task", args="")],
        ]
        menu.extend(menu_user)
    response.menu_options = menu

shn_menu()


def index():

    """ Module's Home Page """

    # Module's nice name
    try:
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Volunteer Management")

    # Override prefix and resourcename
    _prefix = "pr"
    resourcename = "person"

    # Choose table
    tablename = "%s_%s" % (_prefix, resourcename)
    table = db[tablename]

    # Configure redirection and list fields
    register_url = str(URL(r=request, f=resourcename,
                           args=["[id]", "volunteer"]))
    s3xrc.model.configure(table,
                          create_next=register_url,
                          list_fields=["id",
                                       "first_name",
                                       "middle_name",
                                       "last_name",
                                       "gender",
                                       "occupation"])

    # Pre-process
    def prep(r):

        """ Redirect to search/person view """

        if r.representation == "html":
            if not r.id and not r.method:
                r.method = "search"
            else:
               redirect(URL(r=request, f=resourcename, args=request.args))
        return True


    # Post-process
    def postp(r, output):

        """ Custom action buttons """

        response.s3.actions = []

        # Button labels
        REGISTER = str(T("Register"))
        DETAILS = str(T("Details"))

        if not r.component:
            open_button_label = DETAILS

            if auth.s3_logged_in():
                # Set action buttons
                response.s3.actions = [
                    dict(label=REGISTER, _class="action-btn", url=register_url)
                ]

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

    # REST controllerperson
    output = s3_rest_controller(_prefix, resourcename,
                                module_name=module_name)

    # Set view, update menu and return output
    response.view = "vol/index.html"
    response.title = module_name
    shn_menu()
    return output


# -----------------------------------------------------------------------------
# People
# -----------------------------------------------------------------------------
def register():
    """
        Custom page to allow people to register as a Volunteer whilst hiding the complexity of the data model.
    """

    # Fields that we want in our custom Form
    # Dicts of tablename/fieldname
    fields = [
              {
                "tablename" : "pr_person",
                "fieldname" : "first_name",
                "required" : True
              },
              {
                "tablename" : "pr_person",
                "fieldname" : "last_name"
              },
              {
                "tablename" : "pr_pe_contact",
                "fieldname" : "value",
                "formfieldname" : "telephone",
                "label" : T("Telephone"),
                "comment" : DIV(_class="tooltip",
                                _title="%s|%s" % (T("Telephone"),
                                                  T("Please sign-up with your Cell Phone as this allows us to send you Text messages. Please include full Area code.")))

              },
              {
                "tablename" : "pr_pe_contact",
                "fieldname" : "value",
                "formfieldname" : "email",
                "label" : T("Email Address"),
                "required" : True
              },
              {
                "tablename" : "vol_credential",
                "fieldname" : "skill_id",
                #"label":T("My Current function")
              },
              {
                "tablename" : "vol_volunteer",
                "fieldname" : "location_id",
                #"label" : T("I am available in the following area(s)"),
              },
             ]

    # Forms
    forms = Storage()
    forms["pr_person"] = SQLFORM(db.pr_person)
    forms["pr_pe_contact1"] = SQLFORM(db.pr_pe_contact)
    forms["pr_pe_contact2"] = SQLFORM(db.pr_pe_contact)
    forms["vol_credential"] = SQLFORM(db.vol_credential)
    forms["vol_volunteer"] = SQLFORM(db.vol_volunteer)

    form_rows = []
    required = SPAN(" *", _class="req")

    for field in fields:
        tablename = field["tablename"]
        fieldname = field["fieldname"]

        # Label
        try:
            label = "%s:" % field["label"]
        except:
            label = "%s:" % db[tablename][fieldname].label
        try:
            if field["required"]:
                label = DIV(label, required)
        except:
            pass
        label = TD(label, _class="w2p_fl")

        # Widget
        try:
            if field["formfieldname"] == "telephone":
                widget = forms["%s1" % tablename].custom.widget[fieldname]
            elif field["formfieldname"] == "email":
                widget = forms["%s2" % tablename].custom.widget[fieldname]
            widget.attributes["_id"] = field["formfieldname"]
            widget.attributes["_name"] = field["formfieldname"]
        except:
            widget = forms[tablename].custom.widget[fieldname]

        # Comment
        try:
            comment = field["comment"]
        except:
            comment = db[tablename][fieldname].comment or ""

        form_rows.append(TR(label))
        form_rows.append(TR(widget, comment))

    form = FORM(TABLE(*form_rows),
                INPUT(_value = T("Save"),
                      _type = "submit"))

    if form.accepts(request.vars, session):
        # Insert Person Record
        person_id = db.pr_person.insert(first_name=request.vars.first_name,
                                        last_name=request.vars.last_name)
        # Update Super-Entity
        record = Storage(id=person_id)
        s3xrc.model.update_super(db.pr_person, record)
        # Register as Volunteer
        # @ToDo: Handle Available Times (which needs reworking anyway)
        db.vol_volunteer.insert(person_id=person_id,
                                location_id=request.vars.location_id,
                                status=1)   # Active
        # Insert Credential
        db.vol_credential.insert(person_id=person_id,
                                 skill_id=request.vars.skill_id,
                                 status=1)  # Pending

        pe_id = db(db.pr_person.id == person_id).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        # Insert Email
        db.pr_pe_contact.insert(pe_id=pe_id, contact_method=1, value=request.vars.email)
        # Insert Telephone
        db.pr_pe_contact.insert(pe_id=pe_id, contact_method=2, value=request.vars.telephone)


        response.confirmation = T("Sign-up succesful - you should hear from us soon!")

    return dict(form=form)

# -----------------------------------------------------------------------------
def person():

    """
        RESTful CRUD Controller
        Configures options for Persons relevant to a Volunteer context
    """

    # Override prefix
    _prefix = "pr"

    # Choose table
    tablename = "%s_%s" % (_prefix, resourcename)
    table = db[tablename]

    # If we Register a volunteer, then we can assume they're not Missing
    table.missing.default = False

    # Direct to the Volunteer Availability tab after registration
    register_url = str(URL(r=request, f=resourcename,
                           args=["[id]", "volunteer"]))
    s3xrc.model.configure(table,
                          create_next=register_url)

    tabs = [
            (T("Basic Details"), None),
            (T("Address"), "address"),
            (T("Identity"), "identity"),
            (T("Contact Data"), "pe_contact"),
            #(T("Teams"), "group_membership"),
            (T("Skills"), "credential"),
            (T("Availability"), "volunteer"),
            (T("Images"), "image"),
           ]

    # Pre-process
    def prep(r):
        if r.interactive:

            table = r.table
            # Assume volunteers only between 12-81
            #table.date_of_birth.widget = S3DateWidget(past=972, future=-144)

            # Hide fields
            #table.preferred_name.readable = table.preferred_name.writable = False
            table.local_name.readable = table.local_name.writable = False
            table.pe_label.readable = table.pe_label.writable = False
            table.missing.readable = table.missing.writable = False
            table.tags.readable = table.tags.writable = False
            table.age_group.readable = table.age_group.writable = False
            table.religion.readable = table.religion.writable = False
            table.marital_status.readable = table.marital_status.writable = False

            # CRUD strings
            ADD_VOL = T("Add Volunteer")
            LIST_VOLS = T("List Volunteers")
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add a Volunteer"),
                title_display = T("Volunteer Details"),
                title_list = LIST_VOLS,
                title_update = T("Edit Volunteer Details"),
                title_search = T("Search Volunteers"),
                subtitle_create = ADD_VOL,
                subtitle_list = T("Volunteers"),
                label_list_button = LIST_VOLS,
                label_create_button = ADD_VOL,
                label_delete_button = T("Delete Volunteer"),
                msg_record_created = T("Volunteer added"),
                msg_record_modified = T("Volunteer details updated"),
                msg_record_deleted = T("Volunteer deleted"),
                msg_list_empty = T("No Volunteers currently registered"))

        if r.component:
            if r.component.name == "presence":
                table = db.pr_presence
                table.presence_condition.default = vita.CONFIRMED
                table.presence_condition.readable = False
                table.presence_condition.writable = False
                table.orig_id.readable = False
                table.orig_id.writable = False
                table.dest_id.readable = False
                table.dest_id.writable = False
                table.proc_desc.readable = False
                table.proc_desc.writable = False

            elif r.component.name == "group_membership":
                table = db.pr_group_membership
                table.group_id.label = T("Team Id")
                table.group_head.label = T("Team Leader")
                s3xrc.model.configure(table,
                                      list_fields=["id",
                                                   "group_id",
                                                   "group_head",
                                                   "description"])


            elif r.component.name == "address":
                if r.method != "read":
                    table = db.pr_address
                    table.type.default = 1 # Home Address
                    # Don't want to see in Create forms
                    # inc list_create (list_fields over-rides)
                    table.address.readable = False
                    table.L4.readable = False
                    table.L3.readable = False
                    table.L2.readable = False
                    table.L1.readable = False
                    table.L0.readable = False
                    table.postcode.readable = False
                    # Process Base Location
                    s3xrc.model.configure(table,
                                          onaccept=address_onaccept)
        else:
            # Only display active volunteers
            response.s3.filter = (table.id == db.vol_volunteer.person_id) & \
                                 (db.vol_volunteer.status == 1)

        return True


    # Post-process
    def postp(r, output):

        if r.interactive and r.component and r.method != "read":
            if r.component.name == "address":
                try:
                    # Inject a flag to say whether this address should be set as the user's Base Location
                    HELP = T("If this is ticked, then this will become the user's Base Location & hence where the user is shown on the Map")
                    output["form"][0].insert(2,
                                             TR(TD(LABEL("%s:" % T("Base Location?")),
                                                   INPUT(_name="base_location",
                                                         _id="base_location",
                                                         _class="boolean",
                                                         _type="checkbox",
                                                         _value="on"),
                                                    _class="w2p_fl"),
                                                TD(DIV(_class="tooltip",
                                                       _title="%s|%s" % (T("Base Location"),
                                                                         HELP)))))
                except:
                    # No form to inject into
                    pass

        return output

    # Set hooks
    response.s3.prep = prep
    response.s3.postp = postp


    output = s3_rest_controller(_prefix, resourcename,
                                rheader=lambda r: vol_rheader(r, tabs))

    shn_menu()
    return output

# -----------------------------------------------------------------------------
#
def vol_rheader(r, tabs=[]):

    """ Volunteer page headers """

    if r.representation == "html":

        rheader_tabs = shn_rheader_tabs(r, tabs)

        if r.name == "person":

            person = r.record

            if person:
                rheader = DIV(TABLE(

                    TR(TH("%s: " % T("Name")),
                       vita.fullname(person),
                       TH("%s: " % T("Gender")),
                       "%s" % pr_gender_opts.get(person.gender, T("unknown"))),

                    TR(TH("%s: " % T("Nationality")),
                       "%s" % pr_nations.get(person.nationality, T("unknown")),
                       TH("%s: " % T("Date of Birth")),
                       "%s" % (person.date_of_birth or T("unknown"))),

                    ), rheader_tabs)

                return rheader

    return None

# -----------------------------------------------------------------------------
# Skills
# -----------------------------------------------------------------------------
def skill():

    """
        RESTful CRUD Controller
        Lookup list of skill types
    """

    return s3_rest_controller(prefix, "skill")

# -----------------------------------------------------------------------------
def credential():

    """
        RESTful CRUD Controller
        Select skills a volunteer has & validate them
    """

    return s3_rest_controller(prefix, "skill_types")

# -----------------------------------------------------------------------------
def skillSearch():

    """
        Search for Volunteers by Skill
        - A Notification is sent to each matching volunteer

        @ToDo: Make into a normal S3Search? (may need minor modification)
        @ToDo: Make the Notification into a separate button (may want to search without notifications)
    """

    from gluon.sqlhtml import CheckboxesWidget
    vol_skill_widget = CheckboxesWidget().widget(db.vol_credential.skill_id, None)
    search_btn = INPUT(_value = "search", _type = "submit")
    search_form = FORM(vol_skill_widget, search_btn)
    output = dict(search_form = search_form)

    output["table"] = ""
    if search_form.accepts(request.vars, session, keepvalues=True):
        search_skill_ids =  request.vars.skill_id

        table1 = db.vol_credential
        table2 = db.vol_skill
        table3 = db.pr_person
        #person_details = []
        # Print a list of volunteers with their skills status.
        # @ToDo: selects for only one skills right now. add displaying of skill name
        vol_id = db((table2.id == table1.skill_id) & \
                    (table2.id == search_skill_ids)).select(table1.person_id)

        vol_idset = []
        html = DIV(DIV(B(T("List of Volunteers for this skill set"))))
        for id in vol_id:
            vol_idset.append(id.person_id)

        for pe_id in vol_idset:
            person_details = db((table3.id == pe_id)).select(table3.first_name, table3.middle_name, table3.last_name).first()
            skillset = db(table1.person_id == pe_id).select(table1.status).first()
            html.append(DIV(LABEL(vita.fullname(person_details)),DIV(T("Skill Status") + ": "), UL(skillset.status)))
            # @ToDo: Make the notification message configurable
            #msg.send_by_pe_id(pe_id, "CERT: Please Report for Duty", "We ask you to report for duty if you are available", 1, 1)

        html.append(DIV(B(T("Volunteers were notified!"))))
    #for one_pr in person_details:
        #skillset = "approved"
        #html += DIV(LABEL(vita.fullname(one_pr)),DIV(T("Skill Status") + ": "), UL(skillset), _id="table-container")
        #person_data="<div>%s</div>" % str(person_details)
        html2 = DIV(html, _id="table-container")
        output["table"] = html2

    return output

# -----------------------------------------------------------------------------
# Teams
# -----------------------------------------------------------------------------
def group():

    """
        Team controller
        - uses the group table from PR
    """

    tablename = "pr_group"
    table = db[tablename]

    table.group_type.label = T("Team Type")
    table.description.label = T("Team Description")
    table.name.label = T("Team Name")
    db.pr_group_membership.group_id.label = T("Team Id")
    db.pr_group_membership.group_head.label = T("Team Leader")

    # Set Defaults
    db.pr_group.group_type.default = 3  # 'Relief Team'
    db.pr_group.group_type.readable = db.pr_group.group_type.writable = False

    # CRUD Strings
    ADD_TEAM = T("Add Team")
    LIST_TEAMS = T("List Teams")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TEAM,
        title_display = T("Team Details"),
        title_list = LIST_TEAMS,
        title_update = T("Edit Team"),
        title_search = T("Search Teams"),
        subtitle_create = T("Add New Team"),
        subtitle_list = T("Teams"),
        label_list_button = LIST_TEAMS,
        label_create_button = ADD_TEAM,
        label_search_button = T("Search Teams"),
        msg_record_created = T("Team added"),
        msg_record_modified = T("Team updated"),
        msg_record_deleted = T("Team deleted"),
        msg_list_empty = T("No Items currently registered"))

    s3.crud_strings["pr_group_membership"] = Storage(
        title_create = T("Add Member"),
        title_display = T("Membership Details"),
        title_list = T("Team Members"),
        title_update = T("Edit Membership"),
        title_search = T("Search Member"),
        subtitle_create = T("Add New Member"),
        subtitle_list = T("Current Team Members"),
        label_list_button = T("List Members"),
        label_create_button = T("Add Group Member"),
        label_delete_button = T("Delete Membership"),
        msg_record_created = T("Team Member added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Members currently registered"))

    response.s3.filter = (db.pr_group.system == False) # do not show system groups

    # Redirect to member list when a new group has been created
    s3xrc.model.configure(db.pr_group,
        create_next = URL(r=request, c="vol", f="group", args=["[id]", "group_membership"]))
    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "person_id",
                                       "group_head",
                                       "description"])

    s3xrc.model.configure(table, main="name", extra="description")
    output = s3_rest_controller("pr", "group",
                                 rheader=lambda jr: shn_pr_rheader(jr,
                                        tabs = [(T("Team Details"), None),
                                                (T("Address"), "address"),
                                                (T("Contact Data"), "pe_contact"),
                                                (T("Members"), "group_membership")]))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
# Projects & Tasks
# -----------------------------------------------------------------------------
def project():

    """ RESTful CRUD controller """

    tabs = [
            (T("Basic Details"), None),
            #(T("Staff"), "staff"),
            (T("Tasks"), "task"),
            #(T("Donors"), "organisation"),
            #(T("Sites"), "site"),  # Ticket 195
           ]

    rheader = lambda r: shn_project_rheader(r, tabs)
    return s3_rest_controller("project", resourcename, rheader=rheader)


# -----------------------------------------------------------------------------
def task():

    """ Manage current user's tasks """

    tablename = "project_%s" % (resourcename)
    table = db[tablename]

    my_person_id = s3_logged_in_person()

    if not my_person_id:
        session.error = T("No person record found for current user.")
        redirect(URL(r=request, f="index"))

    table.person_id.default = my_person_id
    #@ToDo: if not a team leader then:
    #   can only assign themselves tasks

    response.s3.filter = (db.project_task.person_id == my_person_id)

    s3.crud_strings[tablename].title_list = T("My Tasks")
    s3.crud_strings[tablename].subtitle_list = T("Task List")

    return s3_rest_controller("project", resourcename)


# -----------------------------------------------------------------------------
# Maps
# -----------------------------------------------------------------------------
def view_map():

    """
        Show Location of a Volunteer on the Map

        Use most recent presence if available, else any address that's available.

        @ToDo: Convert to a custom method of the person resource
    """

    person_id = request.args(0)

    # Shortcuts
    persons = db.pr_person
    presences = db.pr_presence
    locations = db.gis_location

    # Include the person's last verified location, assuming that they're not missing
    presence_query = (persons.id == person_id) & \
                     (persons.missing == False) & \
                     (presences.pe_id == persons.pe_id) & \
                     (presences.presence_condition.belongs(vita.PERSISTANT_PRESENCE)) & \
                     (presences.closed == False) & \
                     (locations.id == presences.location_id)

    # Need sql.Rows object for show_map, so don't extract individual row yet.
    features = db(presence_query).select(locations.id,
                                         locations.lat,
                                         locations.lon,
                                         persons.id,
                                         limitby=(0, 1))

    if not features:
        # Use their Address
        address_query = (persons.id == person_id) & \
                        (db.pr_address.pe_id == persons.pe_id) & \
                        (locations.id == db.pr_address.location_id)
        # @ToDo: Lookup their schedule to see whether they should be at Work, Home or Holiday & lookup the correct address
        # For now, take whichever address is supplied first.
        features = db(address_query).select(locations.id,
                                            locations.lat,
                                            locations.lon,
                                            persons.id,
                                            limitby=(0, 1))

    if features:
        # Center and zoom the map.
        record = features.first()
        lat = record.gis_location.lat
        lon = record.gis_location.lon
        zoom = 15

        config = gis.get_config()

        if not deployment_settings.get_security_map() or s3_has_role("MapAdmin"):
            catalogue_toolbar = True
        else:
            catalogue_toolbar = False

        # Standard Feature Layers
        feature_queries = []
        feature_layers = db(db.gis_layer_feature.enabled == True).select()
        for layer in feature_layers:
            _layer = gis.get_feature_layer(layer.module,
                                           layer.resource,
                                           layer.name,
                                           layer.popup_label,
                                           config=config,
                                           marker_id=layer.marker_id,
                                           active=False,
                                           polygons=layer.polygons)
            if _layer:
                feature_queries.append(_layer)

        # Add the Volunteer layer
        try:
            marker_id = db(db.gis_marker.name == "volunteer").select(db.gis_marker.id,
                                                                     limitby=(0, 1)).first().id
        except:
            marker_id = 1

        # Can't use this since the location_id link is via pr_presence not pr_person
        #_layer = gis.get_feature_layer("pr", "person", "Volunteer", "Volunteer", config=config, marker_id=marker_id, active=True, polygons=False)
        #if _layer:
        #    feature_queries.append(_layer)

        # Insert the name into the query & replace the location_id with the person_id
        for i in range(0, len(features)):
            features[i].gis_location.name = vita.fullname(db(db.pr_person.id == features[i].pr_person.id).select(limitby=(0, 1)).first())
            features[i].gis_location.id = features[i].pr_person.id

        feature_queries.append({"name" : "Volunteer",
                                "query" : features,
                                "active" : True,
                                "popup_label" : "Volunteer",
                                "popup_url" : URL(r=request, c="vol", f="popup") + "/<id>/read.plain",
                                "marker" : marker_id})

        html = gis.show_map(
            feature_queries = feature_queries,
            catalogue_toolbar = catalogue_toolbar,
            catalogue_overlays = True,
            toolbar = True,
            search = True,
            lat = lat,
            lon = lon,
            zoom = zoom,
            window = False  # We should provide a button within the map to make it go full-screen (ideally without reloading the page!)
        )
        response.view = "vol/view_map.html"
        return dict(map=html)

    # Redirect to person details if no location is available
    session.warning = T("No location known for this person")
    redirect(URL(r=request, c="vol", f="person", args=[person_id, "presence"]))

def popup():

    """
        Controller that returns a person's data
        To be used to populate map popup
    """

    person_id = request.args(0)

    vol_query = (db.pr_person.id == person_id)
    vol = db(vol_query).select(db.pr_person.first_name, db.pr_person.middle_name, db.pr_person.last_name, limitby=(0, 1)).first()

    skill_query = (db.vol_skill.person_id == person_id) & (db.vol_skill.skill_types_id == db.vol_skill_types.id)
    skills = db(skill_query).select(db.vol_skill_types.name)

    skillset = []

    for s in skills:
        skillset.append(s.name)

    if len(skillset) == 0:
        skillset.append(T("n/a"))

    html = DIV(LABEL(vita.fullname(vol)), DIV(T("Skills") + ": "), UL(skillset), _id="table-container")

    return dict(html=html)

# -----------------------------------------------------------------------------
def view_team_map():

    """
        Show Locations of a Team of Volunteers on the Map

        Use most recent presence for each if available

    """

    # @ToDo: Convert to a custom method of the group resource

    # Currently all presence records created in vol have condition set to
    # confirmed (see person controller's prep).  Then we ignore records that
    # are not confirmed.  This does not guarantee that only vol-specific
    # records are used, but if other modules use confirmed to mean the
    # presence record is valid, that is probably acceptable.  @ToDo: Could
    # we make use of some of the other presence conditions, like transit and
    # check-in/out?  @ToDo: Is it proper to exclude conditions like missing?
    # What if the team manager wants to know what happened to their volunteers?
    # Could indicate status, e.g., by marker color or in popup.

    group_id = request.args(0)

    # Get a list of team (group) member ids.
    members_query = (db.pr_group_membership.group_id == group_id)
    members = db(members_query).select(db.pr_group_membership.person_id)
    member_person_ids = [ x.person_id for x in members ]

    # Presence data of the members with Presence Logs:
    # Get only valid presence data for each person.  Here, valid means
    # not closed (a closed presence has been explicitly marked no longer
    # valid) and the presence condition is confirmed (all presences made
    # in the vol module are set to confirmed).  Also exclude missing
    # persons.  See @ToDo re. possible alternate uses of condition.
    # Note the explicit tests against False are due to a Web2py issue:
    # Use of unary negation leads to a syntax error in the generated SQL.
    presence_rows = db(
        db.pr_person.id.belongs(member_person_ids) &
        (db.pr_person.missing == False) &
        (db.pr_presence.pe_id == db.pr_person.pe_id) &
        db.pr_presence.presence_condition.belongs(vita.PERSISTANT_PRESENCE) &
        (db.pr_presence.closed == False) &
        (db.gis_location.id ==  db.pr_presence.location_id)).select(
            db.gis_location.ALL,
            db.pr_person.id,
            db.pr_person.first_name,
            db.pr_person.middle_name,
            db.pr_person.last_name,
            orderby=~db.pr_presence.datetime)

    # Get latest presence data for each person.
    # Note sort is stable, so preserves time order.
    person_location_sort = presence_rows.sort(lambda row:row.pr_person.id)
    previous_person_id = None
    features = []
    for row in person_location_sort:
        if row.pr_person.id != previous_person_id:
            features.append(row)
            member_person_ids.remove(row.pr_person.id)
            previous_person_id = row.pr_person.id

    # Get addresses of those members without presence data.
    address_rows = db(
        db.pr_person.id.belongs(member_person_ids) &
        (db.pr_address.pe_id == db.pr_person.pe_id) &
        (db.gis_location.id == db.pr_address.location_id)).select(
            db.gis_location.ALL,
            db.pr_person.id,
            db.pr_person.first_name,
            db.pr_person.middle_name,
            db.pr_person.last_name)

    features.extend(address_rows)

    if features:

        config = gis.get_config()

        catalogue_toolbar = not deployment_settings.get_security_map() or s3_has_role("MapAdmin")

        # Standard Feature Layers
        feature_queries = []
        feature_layers = db(db.gis_layer_feature.enabled == True).select()
        for layer in feature_layers:
            _layer = gis.get_feature_layer(layer.module,
                                           layer.resource,
                                           layer.name,
                                           layer.popup_label,
                                           config=config,
                                           marker_id=layer.marker_id,
                                           active=False,
                                           polygons=layer.polygons)
            if _layer:
                feature_queries.append(_layer)

        # Add the Volunteer layer
        try:
            marker_id = db(db.gis_marker.name == "volunteer").select().first().id
        except:
            # @ToDo Why not fall back to the person marker?
            marker_id = 1

        # Insert the name into the query & replace the location_id with the
        # person_id.
        for feature in features:
            names = Storage(first_name = feature.pr_person.first_name,
                            middle_name = feature.pr_person.middle_name,
                            last_name = feature.pr_person.last_name)
            feature.gis_location.name = vita.fullname(names)
            feature.gis_location.id = feature.pr_person.id

        feature_queries.append({"name" : "Volunteers",
                                "query" : features,
                                "active" : True,
                                "popup_label" : "Volunteer",
                                "popup_url" : URL(r=request, c="vol", f="popup") + "/<id>/read.plain",
                                "marker" : marker_id})

        bounds = gis.get_bounds(features=features)

        html = gis.show_map(
            feature_queries = feature_queries,
            catalogue_toolbar = catalogue_toolbar,
            catalogue_overlays = True,
            toolbar = True,
            search = True,
            bbox = bounds,
            window = True)  # @ToDo: Change to False & create a way to convert an embedded map to a full-screen one without a screen refresh

        response.view = "vol/view_map.html"
        return dict(map=html)

    # Redirect to team member list if no locations are available.
    session.warning = T("No locations found for members of this team")
    redirect(URL(r=request, c="vol", f="group",
                 args=[group_id, "group_membership"]))

# -----------------------------------------------------------------------------
def view_project_map():

    """
        Show Location of all Tasks on the Map

        @ToDo: Different Colours for Status
            Green for Complete
            Red for Urgent/Incomplete
            Amber for Non-Urgent/Incomplete

        @ToDo: A single map with both Tasks & Volunteers displayed on it

        @ToDo: Convert to a custom method of the project resource
    """

    project_id = request.args(0)

    # Shortcuts
    tasks = db.project_task
    locations = db.gis_location

    features = db((tasks.project_id == project_id) & \
                  (locations.id == tasks.location_id)).select(locations.id,
                                                              locations.lat,
                                                              locations.lon,
                                                              locations.lat_min,
                                                              locations.lat_max,
                                                              locations.lon_min,
                                                              locations.lon_max,
                                                              tasks.subject,
                                                              tasks.status,
                                                              tasks.urgent,
                                                              tasks.id)

    if features:

        if len(features) > 1:
            # Set the viewport to the appropriate area to see all the tasks
            bounds = gis.get_bounds(features=features)
        else:
            # A 1-task bounds zooms in too far for many tilesets
            lat = features.first().gis_location.lat
            lon = features.first().gis_location.lon
            zoom = 15

        config = gis.get_config()

        if not deployment_settings.get_security_map() or s3_has_role("MapAdmin"):
            catalogue_toolbar = True
        else:
            catalogue_toolbar = False

        # Standard Feature Layers
        feature_queries = []
        feature_layers = db(db.gis_layer_feature.enabled == True).select()
        for layer in feature_layers:
            _layer = gis.get_feature_layer(layer.module,
                                           layer.resource,
                                           layer.name,
                                           layer.popup_label,
                                           config=config,
                                           marker_id=layer.marker_id,
                                           active=False,
                                           polygons=layer.polygons)
            if _layer:
                feature_queries.append(_layer)

        # Add the Tasks layer
        # Can't use this since we want to use different colours, not markers
        #_layer = gis.get_feature_layer("project", "task", "Tasks", "Task", config=config, marker_id=marker_id, active=True, polygons=False)
        #if _layer:
        #    feature_queries.append(_layer)

        # Insert the name into the query & replace the location_id with the task_id
        for i in range(0, len(features)):
            features[i].gis_location.name = features[i].project_task.subject
            features[i].gis_location.id = features[i].project_task.id
            features[i].gis_location.shape = "circle"
            if features[i].project_task.status in [3, 4, 6]:
                # Green for 'Completed', 'Postponed' or 'Cancelled'
                features[i].gis_location.color = "green"
            elif features[i].project_task.status == 1 and features[i].project_task.urgent == True:
                # Red for 'Urgent' and 'New' (i.e. Unassigned)
                features[i].gis_location.color = "red"
            else:
                # Amber for 'Feedback' or 'non-urgent'
                features[i].gis_location.color = "	#FFBF00"


        feature_queries.append({
                                "name" : "Tasks",
                                "query" : features,
                                "active" : True,
                                "popup_label" : "Task",
                                "popup_url" : URL(r=request, c="project", f="task") + "/<id>/read.plain"
                                })

        try:
            # bbox
            html = gis.show_map(
                feature_queries = feature_queries,
                catalogue_toolbar = catalogue_toolbar,
                catalogue_overlays = True,
                toolbar = True,
                search = True,
                bbox = bounds,
                window = True,  # @ToDo Change to False & create a way to convert an embedded map to a full-screen one without a screen refresh
            )
        except:
            # lat/lon/zoom
            html = gis.show_map(
                feature_queries = feature_queries,
                catalogue_toolbar = catalogue_toolbar,
                catalogue_overlays = True,
                toolbar = True,
                search = True,
                lat = lat,
                lon = lon,
                zoom = zoom,
                window = True,  # @ToDo Change to False & create a way to convert an embedded map to a full-screen one without a screen refresh
            )
        response.view = "vol/view_map.html"
        return dict(map=html)

    # Redirect to tasks if no task location is available
    session.warning = T("No Tasks with Location Data")
    redirect(URL(r=request, c="vol", f="project", args=[project_id, "task"]))

# -----------------------------------------------------------------------------
def view_offices_map():

    """
        Show Location of all Offices on the Map
        - optionally filter by those within a radius of a specific Event (Project)
    """

    project_id = None
    radius = None

    if "project_id" in request.vars:
        project_id = request.vars.project_id

    if "radius" in request.vars:
        radius = request.vars.radius

    # Shortcuts
    projects = db.project_project
    offices = db.org_office
    locations = db.gis_location

    if project_id and radius:
        # @ToDo: Optimise by doing a single SQL query with the Spatial one
        project_locations = db((projects.id == project_id) & (locations.id == projects.location_id)).select(locations.id,
                                                                                                            locations.lat,
                                                                                                            locations.lon,
                                                                                                            locations.lat_min,
                                                                                                            locations.lat_max,
                                                                                                            locations.lon_min,
                                                                                                            locations.lon_max,
                                                                                                            projects.code,
                                                                                                            projects.id,
                                                                                                            limitby=(0, 1))
        project_location = project_locations.first()
        lat = project_location.gis_location.lat
        lon = project_location.gis_location.lon

        if (lat is None) or (lon is None):
            # Zero is allowed
            session.error = T("Project has no Lat/Lon")
            redirect(URL(r=request, c="vol", f="project", args=[project_id]))

        # Perform the Spatial query
        features = gis.get_features_in_radius(lat, lon, radius, tablename="org_office")

        # @ToDo: we also want the Project to show (with different Icon): project_locations set ready

    else:
        features = db((offices.id > 0) & \
                      (locations.id == offices.location_id)).select(locations.id,
                                                                    locations.lat,
                                                                    locations.lon,
                                                                    locations.lat_min,
                                                                    locations.lat_max,
                                                                    locations.lon_min,
                                                                    locations.lon_max,
                                                                    offices.name,
                                                                    offices.id)

    if features:

        if len(features) > 1:
            # Set the viewport to the appropriate area to see all the tasks
            bounds = gis.get_bounds(features=features)
        else:
            # A 1-task bounds zooms in too far for many tilesets
            lat = features[0].gis_location.lat
            lon = features[0].gis_location.lon
            zoom = 15

        config = gis.get_config()

        if not deployment_settings.get_security_map() or s3_has_role("MapAdmin"):
            catalogue_toolbar = True
        else:
            catalogue_toolbar = False

        # Standard Feature Layers
        feature_queries = []
        feature_layers = db(db.gis_layer_feature.enabled == True).select()
        for layer in feature_layers:
            _layer = gis.get_feature_layer(layer.module,
                                           layer.resource,
                                           layer.name,
                                           layer.popup_label,
                                           config=config,
                                           marker_id=layer.marker_id,
                                           active=False,
                                           polygons=layer.polygons)
            if _layer:
                feature_queries.append(_layer)

        # Add the Offices layer
        # Can't use this since we may have a custom spatial query
        #_layer = gis.get_feature_layer("org", "office", "Offices", "Office", config=config, marker_id=marker_id, active=True, polygons=False)
        #if _layer:
        #    feature_queries.append(_layer)

        try:
            office_marker_id = db(db.gis_marker.name == "office").select().first().id
        except:
            office_marker_id = 1

        # Insert the name into the query & replace the location_id with the office_id
        for i in range(0, len(features)):
            features[i].gis_location.name = features[i].org_office.name
            features[i].gis_location.id = features[i].org_office.id
            # If a Project
            #    features[i].gis_location.shape = "circle"
            #    if features[i].project_task.status in [3, 4, 6]:
            #        # Green for 'Completed', 'Postponed' or 'Cancelled'
            #        features[i].gis_location.color = "green"
            #    elif features[i].project_task.status == 1 and features[i].project_task.urgent == True:
            #        # Red for 'Urgent' and 'New' (i.e. Unassigned)
            #        features[i].gis_location.color = "red"
            #    else:
            #        # Amber for 'Feedback' or 'non-urgent'
            #        features[i].gis_location.color = "	#FFBF00"

        feature_queries.append({
                                "name" : "Tasks",
                                "query" : features,
                                "active" : True,
                                "popup_label" : "Task",
                                "popup_url" : URL(r=request, c="org", f="office") + "/<id>/read.plain",
                                "marker" : office_marker_id
                                })

        try:
            # Are we using bbox?
            html = gis.show_map(
                feature_queries = feature_queries,
                catalogue_toolbar = catalogue_toolbar,
                catalogue_overlays = True,
                toolbar = True,
                search = True,
                bbox = bounds,
                window = True,  # @ToDo: Change to False & create a way to convert an embedded map to a full-screen one without a screen refresh
            )
        except:
            # No: Lat/Lon/Zoom
            html = gis.show_map(
                feature_queries = feature_queries,
                catalogue_toolbar = catalogue_toolbar,
                catalogue_overlays = True,
                toolbar = True,
                search = True,
                lat = lat,
                lon = lon,
                zoom = zoom,
                window = True,  # @ToDo: Change to False & create a way to convert an embedded map to a full-screen one without a screen refresh
            )

        response.view = "vol/view_map.html"
        return dict(map=html)

    else:
        # Redirect to offices if none found
        session.error = T("No Offices found!")
        redirect(URL(r=request, c="org", f="office"))

# -----------------------------------------------------------------------------
# Messaging
# -----------------------------------------------------------------------------
def compose_person():

    """ Send message to volunteer """

    person_pe_id_query = (db.pr_person.id == request.vars.person_id)
    pe_id_row = db(person_pe_id_query).select(db.pr_person.pe_id).first()
    request.vars.pe_id = pe_id_row["pe_id"]

    return shn_msg_compose(redirect_module=prefix,
                           redirect_function="compose_person",
                           redirect_vars={"person_id":request.vars.person_id},
                           title_name="Send a message to a volunteer")


# -----------------------------------------------------------------------------
def compose_group():

    """ Send message to members of a team """

    group_pe_id_query = (db.pr_group.id == request.vars.group_id)
    pe_id_row = db(group_pe_id_query).select(db.pr_group.pe_id).first()
    request.vars.pe_id = pe_id_row["pe_id"]

    return shn_msg_compose(redirect_module=prefix,
                           redirect_function="compose_group",
                           redirect_vars={"group_id":request.vars.group_id},
                           title_name="Send a message to a team of volunteers")

# -----------------------------------------------------------------------------
