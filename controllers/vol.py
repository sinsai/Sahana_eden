# -*- coding: utf-8 -*-

""" Volunteer Management System """

from gluon.sql import Rows

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
                    [T("Send Mail"), False, URL(r=request, f="compose_group", vars={"group_id":group_id})],
                ]],
            ]
            menu.extend(menu_teams)

    menu_persons = [
        [T("Persons"), False, URL(r=request, f="person", args=["search_simple"]),[
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
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
                    [T("Send Mail"), False, URL(r=request, f="compose_person", vars={"person_id":person_id})],
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

    return dict(module_name=module_name)


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

    output = s3_rest_controller("pr", resourcename,
                                rheader=lambda r: shn_pr_rheader(r, tabs))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def project():

    """ RESTful CRUD controller """

    tabs = [
            (T("Basic Details"), None),
            (T("Staff"), "staff"),
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
    #table.person_id.writable = False

    response.s3.filter = (db.project_task.person_id == my_person_id)

    s3.crud_strings[tablename].title_list = T("My Tasks")
    s3.crud_strings[tablename].subtitle_list = T("Task List")

    return s3_rest_controller("project", resourcename)


# -----------------------------------------------------------------------------
def skill_types():

    """ Allow user to define new skill types. """

    return s3_rest_controller(prefix, "skill_types")


# -----------------------------------------------------------------------------
def view_map():

    """
        Show Location of a Volunteer on the Map
        
        Use most recent presence if available, else any address that's available.
    """

    person_id = request.args(0)

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

    # Need sql.Rows object for show_map, so don't extract individual row.
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
        # Use bounds if more than 1 feature
        #bounds = gis.get_bounds(features=location)
        zoom = 15

        config = gis.get_config()

        if not deployment_settings.get_security_map() or shn_has_role("MapAdmin"):
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
        
        # Insert the name into the query
        for i in range(0, len(features)):
            features[i].gis_location.name = vita.fullname(db(db.pr_person.id == features[i].pr_person.id).select(limitby=(0, 1)).first())
        
        feature_queries.append({"name" : "Volunteer",
                                "query" : features,
                                "active" : True,
                                "popup_label" : "Volunteer",
                                "popup_url" : URL(r=request, c="vol", f="person", args=person_id),
                                "marker" : marker_id})

        html = gis.show_map(
            feature_queries = feature_queries,
            #wms_browser = {"name" : "Risk Maps",
            #               "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
            catalogue_toolbar = catalogue_toolbar,
            catalogue_overlays = True,
            toolbar = True,
            search = True,
            lat = lat,
            lon = lon,
            zoom = zoom,
            #bbox = bounds,
            window = False  # We should provide a button within the map to make it go full-screen (ideally without reloading the page!)
        )
        return dict(map=html)

    # Redirect to person details if no location is available
    session.error = T("No location found")
    redirect(URL(r=request, c="vol", f="person", args=[person_id, "presence"]))


# -----------------------------------------------------------------------------
def group():

    """ Team controller -- teams use the group table from PR """

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
def skill():

    """ Select skills a volunteer has. """

    return s3_rest_controller(prefix, "skill")


# -----------------------------------------------------------------------------
def view_team_map():

    """
        Show Location of a Team of Volunteers on the Map

        Use most recent presence if available, else any address that's available
        
        @ToDo: Update for correct Presence settings, Popup details, etc (see view_map)
    """

    group_id = request.args(0)

    members_query = (db.pr_group_membership.group_id == group_id)
    members = db(members_query).select(db.pr_group_membership.person_id) #members of a team aka group
    member_person_ids = [ x.person_id for x in members ] #list of members

    #Presence Data of the members with Presence Logs
    presence_rows = db(db.pr_person.id.belongs(member_person_ids) & \
                      (db.pr_presence.pe_id == db.pr_person.pe_id) & \
                      (db.gis_location.id ==  db.pr_presence.location_id)).select(db.gis_location.ALL, db.pr_person.id, orderby=~db.pr_presence.datetime)
    #Get Latest Presence Data
    person_location_sort = presence_rows.sort(lambda row:row.pr_person.id)
    previous_person_id = None
    locations_list = []
    for row in person_location_sort:
        if row.pr_person.id != previous_person_id:
            locations_list.append(row["gis_location"])
            member_person_ids.remove(row.pr_person.id)
            previous_person_id = row.pr_person.id

    #Address of those members without Presence data
    address = db(db.pr_person.id.belongs(member_person_ids) & \
                (db.pr_address.pe_id == db.pr_person.pe_id) & \
                (db.gis_location.id ==  db.pr_address.location_id)).select(db.gis_location.ALL)

    locations_list.extend(address)

    if locations_list:

        bounds = gis.get_bounds(features=locations_list)

        volunteer = {"feature_group" : "People"}
        html = gis.show_map(
            feature_queries = [{"name" : "Volunteer", "query" : locations_list, "active" : True, "marker" : db(db.gis_marker.name == "volunteer").select().first().id}],
            feature_groups = [volunteer],
            wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
            catalogue_overlays = True,
            catalogue_toolbar = True,
            toolbar = True,
            search = True,
            bbox = bounds,
            window = True,
        )
        return dict(map=html)

    # Redirect to team details if no location is available
    response.error=T("Add Location")
    redirect(URL(r=request, c="vol", f="group", args=[group_id,"address"]))


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
# TODO: Is resource a bad name, due to possible confusion with other usage?
def resource():

    """ Select resources a volunteer has """

    return s3_rest_controller(prefix, "resource")

# -----------------------------------------------------------------------------
