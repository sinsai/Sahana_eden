# -*- coding: utf-8 -*-

""" Volunteer Management System """

#from gluon.sql import Rows

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions)
def shn_menu():
    menu = [
        [T("Projects"), False, URL(r=request, f="project"),[
            [T("Search"), False, URL(r=request, f="project", args="search_location")],
            [T("Add Project"), False, URL(r=request, f="project", args="create")],
        ]],
    ]
    if session.rcvars and "project_project" in session.rcvars:
        project_id = session.rcvars["project_project"]
        selection = db.project_project[project_id]
        if selection:
            menu_project = [
                    ["%s %s" % (T("Project") + ":", selection.code), False, URL(r=request, f="project", args=[project_id]),[
                        [T("Tasks"), False, URL(r=request, f="project", args=[project_id, "task"])],
                        # Staff cannot be a component of Project since staff may be assigned to many projects
                        #[T("Staff"), False, URL(r=request, f="project", args=[project_id, "staff"])],
                    ]]
            ]
            menu.extend(menu_project)

    menu_teams = [
        [T("Teams"), False, URL(r=request, f="group"),[
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create")],
        ]]
    ]
    menu.extend(menu_teams)
    if session.rcvars and "pr_group" in session.rcvars:
        group_id = session.rcvars["pr_group"]
        selection = db.pr_group[group_id]
        if selection:
            team_name = shn_pr_group_represent(group_id)
            menu_teams = [
                ["%s %s" % (T("Team") + ":", team_name), False, URL(r=request, f="group", args=[group_id, "read"]),[
                    [T("View On Map"), False, URL(r=request, f="view_team_map", args=[group_id])],
                    [T("Send Notification"), False, URL(r=request, f="compose_group", vars={"group_id":group_id})],
                    [T("Find Volunteers"), False, URL(r=request, f="showSkillOptions")],
                ]],
            ]
            menu.extend(menu_teams)

    menu_persons = [
        [T("Volunteers"), False, URL(r=request, f="person", args=["search_simple"]),[
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
            # Not ready yet
            #[T("Search by Skill Types"), False, URL(r=request, f="showSkillOptions")],
        ]]
    ]
    menu.extend(menu_persons)
    if session.rcvars and "pr_person" in session.rcvars:
        person_id = session.rcvars["pr_person"]
        selection = db.pr_person[person_id]
        if selection:
            person_name = shn_pr_person_represent(person_id)
            # ?vol_tabs=person and ?vol_tabs=volunteer are used by the person
            # controller to select which set of tabs to display.
            menu_person = [
                ["%s %s" % (T("Person") + ":", person_name), False, URL(r=request, f="person", args=[person_id, "read"]),[
                    # The arg "volunteer" causes this to display the
                    # vol_volunteer tab initially.
                    [T("Volunteer Data"), False, URL(r=request, f="person", args=[person_id, "volunteer"], vars={"vol_tabs":"volunteer"})],
                    # The default tab is pr_person, which is fine here.
                    [T("Person Data"), False, URL(r=request, f="person", args=[person_id], vars={"vol_tabs":"person"})],
                    [T("View On Map"), False, URL(r=request, f="view_map", args=[person_id])],
                    [T("Send Notification"), False, URL(r=request, f="compose_person", vars={"person_id":person_id})],
                ]],
            ]
            menu.extend(menu_person)
    menu_skills = [
        [T("Skill Types"), False, URL(r=request, f="skill_types")],
    ]
    menu.extend(menu_skills)
    if auth.user is not None:
        menu_user = [
            [T("My Tasks"), False, URL(r=request, f="task", args="")],
        ]
        menu.extend(menu_user)
    response.menu_options = menu

shn_menu()


def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
# People
# -----------------------------------------------------------------------------
def person():

    """
        This controller produces either generic person component tabs or
        volunteer-specific person component tabs, depending on whether "vol_tabs"
        in the URL's vars is "person" or "volunteer".
    """

    tab_set = "person"
    if "vol_tabs" in request.vars:
        tab_set = request.vars["vol_tabs"]
    if tab_set == "person":
        #db.pr_person.pr_impact_tags.readable=False
        db.pr_person.missing.default = False
        tabs = [(T("Basic Details"), None),
                (T("Images"), "image"),
                (T("Identity"), "identity"),
                (T("Address"), "address"),
                (T("Contact Data"), "pe_contact"),
                (T("Presence Log"), "presence")]
    else:
        # TODO: These files are for the multiselect widget used for skills.
        # Check if we still need them if we switch to a different widget.
        response.files.append(URL(r=request,c='static/scripts/S3',f='jquery.multiSelect.js'))
        response.files.append(URL(r=request,c='static/styles/S3',f='jquery.multiSelect.css'))
        db.pr_group_membership.group_id.label = T("Team Id")
        db.pr_group_membership.group_head.label = T("Team Head")
        s3xrc.model.configure(db.pr_group_membership,
                              list_fields=["id",
                                           "group_id",
                                           "group_head",
                                           "description"])
        # TODO: If we don't know what a "status report" is supposed to be,
        # take it out.  Take out resources til they're modernized.
        tabs = [
                #(T("Status Report"), None),
                (T("Availablity"), "volunteer"),
                (T("Teams"), "group_membership"),
                (T("Skills"), "skill"),
                #(T("Resources"), "resource"),
               ]

    # Only display active volunteers
    response.s3.filter = (db.pr_person.id == db.vol_volunteer.person_id) & (db.vol_volunteer.status == 1)

    db.pr_presence.presence_condition.default = vita.CONFIRMED
    db.pr_presence.presence_condition.readable = False
    db.pr_presence.presence_condition.writable = False
    db.pr_presence.orig_id.readable = False
    db.pr_presence.orig_id.writable = False
    db.pr_presence.dest_id.readable = False
    db.pr_presence.dest_id.writable = False
    db.pr_presence.proc_desc.readable = False
    db.pr_presence.proc_desc.writable = False

    output = s3_rest_controller("pr", resourcename,
                                rheader=lambda r: shn_pr_rheader(r, tabs))

    shn_menu()
    return output

def skillsearch():

    """ tbc """

    item = []
    table1 = db.vol_skill
    table2 = db.vol_skill_types
    table3 = db.pr_person
    vol_id = db((table2.id == table1.skill_types_id) & \
                (table2.name == "medical")).select(table1.person_id, limitby=(0, 1)).first()
    person_details = db((table3.id == vol_id.person_id)).select(table3.first_name, table3.last_name, limitby=(0,1)).first()

    html = DIV(LABEL(vita.fullname(person_details)), DIV(T("Skills") + ": "), UL(skillset), _id="table-container")
    person_data = "<div>%s</div>" % (person_details)
    return dict(html=person_data)

def showSkillOptions():

    """
        Search for Volunteers by Skill Type
        - A Notification is sent to each matching volunteer

        @ToDo: Make into a normal search_simple? (may need minor modification)
        @ToDo: Make the Notification into a separate button (may want to search without notifications)
    """

    from gluon.sqlhtml import CheckboxesWidget
    vol_skill_type_widget = CheckboxesWidget().widget(db.vol_skill.skill_types_id, None)
    search_btn = INPUT(_value = "search", _type = "submit")
    search_form = FORM(vol_skill_type_widget, search_btn)
    output = dict(search_form = search_form)

    output["table"] = ""
    if search_form.accepts(request.vars, session, keepvalues=True):
        search_skill_ids =  request.vars.skill_types_id

        table1 = db.vol_skill
        table2 = db.vol_skill_types
        table3 = db.pr_person
        #person_details = []
        # Print a list of volunteers with their skills status.
        # @ToDo: selects for only one skills right now. add displaying of skill name
        vol_id = db((table2.id == table1.skill_types_id) & \
                    (table2.id == search_skill_ids)).select(table1.person_id)

        vol_idset = []
        html = DIV(DIV(B(T("List of Volunteers for this skills set"))))
        for id in vol_id:
            vol_idset.append(id.person_id)


        for pe_id in vol_idset:
            person_details = db((table3.id == pe_id)).select(table3.first_name, table3.middle_name, table3.last_name).first()
            skillset = db(table1.person_id == pe_id).select(table1.status).first()
            html.append(DIV(LABEL(vita.fullname(person_details)),DIV(T("Skill Status") + ": "), UL(skillset.status)))
            # @ToDo: Make the notification message configurable
            msg.send_by_pe_id(pe_id, "CERT: Please Report for Duty", "We ask you to report for duty if you are available", 1, 1)

        html.append(DIV(B(T("Volunteers were notified!"))))
    #for one_pr in person_details:
        #skillset = "approved"
        #html += DIV(LABEL(vita.fullname(one_pr)),DIV(T("Skill Status") + ": "), UL(skillset), _id="table-container")
        #person_data="<div>"+str(person_details)+"</div>"
        html2 = DIV(html, _id="table-container")
        output["table"] = html2

    return output

# -----------------------------------------------------------------------------
def skill_types():

    """ Allow user to define new skill types. """

    return s3_rest_controller(prefix, "skill_types")


# -----------------------------------------------------------------------------
def skill():

    """ Select skills a volunteer has. """

    return s3_rest_controller(prefix, "skill")


# -----------------------------------------------------------------------------
# TODO: Is resource a bad name, due to possible confusion with other usage?
def resource():

    """ Select resources a volunteer has """

    return s3_rest_controller(prefix, "resource")

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
    db.pr_group_membership.group_head.label = T("Team Head")

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

    s3xrc.model.configure(table, main="name", extra="description", listadd=False, deletable=False)
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
            _layer = gis.get_feature_layer(layer.module, layer.resource, layer.name, layer.popup_label, config=config, marker_id=layer.marker_id, active=False, polygons=layer.polygons)
            if _layer:
                feature_queries.append(_layer)

        # Add the Volunteer layer
        try:
            marker_id = db(db.gis_marker.name == "volunteer").select().first().id
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
        Show Location of a Team of Volunteers on the Map

        Use most recent presence if available

        @ToDo: Fallback to addresses

        @ToDo: Convert to a custom method of the group resource
    """

    group_id = request.args(0)

    members_query = (db.pr_group_membership.group_id == group_id)
    members = db(members_query).select(db.pr_group_membership.person_id) # Members of a team (aka group)
    member_person_ids = [ x.person_id for x in members ] # List of members

    # Shortcuts
    persons = db.pr_person
    presences = db.pr_presence
    locations = db.gis_location

    # Presence Data for Members who aren't Missing & have a Verified Presence
    features = db(persons.id.belongs(member_person_ids) & \
                 (persons.missing == False) & \
                 (presences.pe_id == persons.pe_id) & \
                 (presences.presence_condition.belongs(vita.PERSISTANT_PRESENCE)) & \
                 (presences.closed == False) & \
                 (locations.id == presences.location_id)).select(locations.id,
                                                                 locations.lat,
                                                                 locations.lon,
                                                                 locations.lat_min,
                                                                 locations.lat_max,
                                                                 locations.lon_min,
                                                                 locations.lon_max,
                                                                 persons.id)

    # Address of those members without Presence data
    #address = db(persons.id.belongs(member_person_ids) & \
    #            (db.pr_address.pe_id == persons.pe_id) & \
    #            (locations.id ==  db.pr_address.location_id)).select(locations.id,
    #                                                                 locations.lat,
    #                                                                 locations.lon,
    #                                                                 persons.id)
    #locations_list.extend(address)

    if features:

        if len(features) > 1:
            # Set the viewport to the appropriate area to see everyone
            bounds = gis.get_bounds(features=features)
        else:
            # A 1-person bounds zooms in too far for many tilesets
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
            _layer = gis.get_feature_layer(layer.module, layer.resource, layer.name, layer.popup_label, config=config, marker_id=layer.marker_id, active=False, polygons=layer.polygons)
            if _layer:
                feature_queries.append(_layer)

        # Add the Volunteer layer
        try:
            marker_id = db(db.gis_marker.name == "volunteer").select().first().id
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

        feature_queries.append({"name" : "Volunteers",
                                "query" : features,
                                "active" : True,
                                "popup_label" : "Volunteer",
                                "popup_url" : URL(r=request, c="vol", f="popup") + "/<id>/read.plain",
                                "marker" : marker_id})

        try:
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

    # Redirect to team details if no location is available
    # Present warning if no location is available
    session.warning = T("No location known for this team")
    redirect(URL(r=request, c="vol", f="group", args=[group_id, "address"]))

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
            _layer = gis.get_feature_layer(layer.module, layer.resource, layer.name, layer.popup_label, config=config, marker_id=layer.marker_id, active=False, polygons=layer.polygons)
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
            _layer = gis.get_feature_layer(layer.module, layer.resource, layer.name, layer.popup_label, config=config, marker_id=layer.marker_id, active=False, polygons=layer.polygons)
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