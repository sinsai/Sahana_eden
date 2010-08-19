# -*- coding: utf-8 -*-

"""
    GIS Controllers

    @author: Fran Boon
"""

from operator import __and__

module = request.controller

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Service Catalogue"), False, URL(r=request, f="map_service_catalogue")],
    [T("Locations"), False, URL(r=request, f="location"), [
        [T("List"), False, URL(r=request, f="location")],
        [T("Add"), False, URL(r=request, f="location", args="create")],
    ]],
    [T("Fullscreen Map"), False, URL(r=request, f="map_viewing_client")],
    # Currently broken
    #[T("Bulk Uploader"), False, URL(r=request, c="doc", f="bulk_upload")]
]

# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db)

# S3 framework functions
def index():
    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    
    # Include an embedded Overview Map on the index page
    window = False
    toolbar = False
    
    map = define_map(window=window, toolbar=toolbar)

    return dict(module_name=module_name, map=map)

def define_map(window=False, toolbar=False):
    """
        Define the main Situation Map
        This can then be called from both the Index page (embedded) & the Map_Viewing_Client (fullscreen)
    """
    
    # @ToDo: Make these configurable
    #config = gis.get_config()
    if 1 in session.s3.roles or shn_has_role("MapAdmin"):
        catalogue_toolbar = True
    else:
        catalogue_toolbar = False
    search = True
    catalogue_overlays = True

    # Read which overlays to enable
    feature_groups = []
    _feature_groups = db((db.gis_feature_group.enabled == True) & (db.gis_feature_group.deleted == False)).select()
    for feature_group in _feature_groups:
        feature_groups.append(
            {
                "feature_group" : feature_group.name,
                "active" : feature_group.visible
            }
        )

    # Custom Feature Layers
    locations = db(db.gis_location.id == db.irs_ireport.location_id).select()
    # Default Red
    #marker = db(db.gis_marker.name == "marker_red").select(db.gis_marker.id, limitby=(0, 1)).first().id
    popup_url = URL(r=request, c="irs", f="ireport", args="read.popup?ireport.location_id=")
    incidents = {"name":Tstr("Incident Reports"), "query":locations, "active":True, "popup_url": popup_url}
    
    locations = db(db.gis_location.id == db.cr_shelter.location_id).select()
    marker = db(db.gis_marker.name == "shelter").select(db.gis_marker.id, limitby=(0, 1)).first().id
    popup_url = URL(r=request, c="cr", f="shelter", args="read.popup?shelter.location_id=")
    shelters = {"name":Tstr("Shelters"), "query":locations, "active":True, "marker":marker, "popup_url": popup_url}
    
    locations = db(db.gis_location.id == db.sitrep_assessment.location_id).select()
    marker = db(db.gis_marker.name == "marker_green").select(db.gis_marker.id, limitby=(0, 1)).first().id
    popup_url = URL(r=request, c="sitrep", f="assessment", args="read.popup?assessment.location_id=")
    assessments = {"name":Tstr("Assessments"), "query":locations, "active":True, "marker":marker, "popup_url": popup_url}
    
    locations = db(db.gis_location.id == db.rms_req.location_id).select()
    marker = db(db.gis_marker.name == "marker_yellow").select(db.gis_marker.id, limitby=(0, 1)).first().id
    popup_url = URL(r=request, c="rms", f="req", args="read.popup?assessment.location_id=")
    requests = {"name":Tstr("Requests"), "query":locations, "active":True, "marker":marker, "popup_url": popup_url}
    
    feature_queries = [incidents, shelters, assessments, requests]
    
    map = gis.show_map(window=window, catalogue_toolbar=catalogue_toolbar, toolbar=toolbar, search=search, catalogue_overlays=catalogue_overlays, feature_groups=feature_groups, feature_queries=feature_queries)

    return map
    
def test():
    "Test Mapping API"

    # Will use default popup_url
    hospitals = {"feature_group" : "Hospitals"}

    if auth.is_logged_in():
        offices = {"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location", args="update.popup")}
    else:
        offices = {"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location", args="read.popup")}

    query = db((db.gis_feature_class.name == "Town") & (db.gis_location.feature_class_id == db.gis_feature_class.id)).select()

    html = gis.show_map(
                feature_groups = [offices, hospitals],
                feature_queries = [{"name" : "Towns", "query" : query, "active" : True}],
                wms_browser = {"name" : "OpenGeo Demo WMS", "url" : "http://demo.opengeo.org/geoserver/ows?service=WMS&request=GetCapabilities"},
                #wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
                #wms_browser = {"name" : "Risk Maps", "url" : "http://www.pdc.org/wms/wmservlet/PDC_Active_Hazards?request=getcapabilities&service=WMS&version=1.1.1"},
                catalogue_overlays = True,
                catalogue_toolbar = True,
                legend = True, # Stops Feature Layers from Printing
                toolbar = True,
                search = True,
                print_tool = {
                        #"url" : "http://localhost:8080/geoserver/pdf/",                    # Local GeoServer
                        "url" : "http://localhost:8080/print-servlet-1.2-SNAPSHOT/pdf/",    # Local Windows Tomcat
                        #"url" : "http://host.domain:8180/print-servlet-1.2-SNAPSHOT/pdf/", # Linux Tomcat
                        "mapTitle" : "Title",
                        "subTitle" : "SubTitle"
                    },
                #mgrs = {"name" : "MGRS Atlas PDFs", "url" : "http://www.sharedgeo.org/datasets/shared/maps/usng/pdf.map?VERSION=1.0.0&SERVICE=WFS&request=GetFeature&typename=wfs_all_maps"},
                window = True,
                )

    return dict(map=html)

def test2():
    "Test new OpenLayers functionality in a RAD environment"
    return dict()

#@auth.shn_requires_membership("MapAdmin")
def apikey():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.writable = False
    table.apikey.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_KEY = T("Add Key")
    LIST_KEYS = T("List Keys")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_KEY,
        title_display = T("Key Details"),
        title_list = T("Keys"),
        title_update = T("Edit Key"),
        title_search = T("Search Keys"),
        subtitle_create = T("Add New Key"),
        subtitle_list = LIST_KEYS,
        label_list_button = LIST_KEYS,
        label_create_button = ADD_KEY,
        label_delete_button = T("Delete Key"),
        msg_record_created = T("Key added"),
        msg_record_modified = T("Key updated"),
        msg_record_deleted = T("Key deleted"),
        msg_list_empty = T("No Keys currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def config():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    # In Model so that they're visible to person() as component
    # CRUD Strings (over-ride)
    s3.crud_strings[tablename].title_display = T("Defaults")
    s3.crud_strings[tablename].title_update = T("Edit Defaults")
    s3.crud_strings[tablename].msg_record_modified = T("Defaults updated")


    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    output["list_btn"] = ""

    if auth.is_logged_in():
        personalised = db((db.pr_person.uuid == auth.user.person_uuid) & (table.pe_id == db.pr_person.pe_id)).select(table.id, limitby=(0, 1)).first()
        if personalised:
            output["rheader"] = P(T("You have personalised settings, so changes made here won't be visible to you. To change your personalised settings, click "), A(T("here"), _href=URL(r=request, c="pr", f="person", args=["config"], vars={"person.uid":auth.user.person_uuid})))
        else:
            output["rheader"] = P(T("These are the default settings for all users. To change settings just for you, click "), A(T("here"), _href=URL(r=request, c="pr", f="person", args=["config"], vars={"person.uid":auth.user.person_uuid})))

    return output

#@auth.shn_requires_membership("MapAdmin")
def feature_class():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    table.gps_marker.comment = DIV( _class="tooltip", _title=Tstr("GPS Marker") + "|" + Tstr("Defines the icon used for display of features on handheld GPS."))

    # CRUD Strings
    LIST_FEATURE_CLASS = T("List Feature Classes")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FEATURE_CLASS,
        title_display = T("Feature Class Details"),
        title_list = T("Feature Classes"),
        title_update = T("Edit Feature Class"),
        title_search = T("Search Feature Class"),
        subtitle_create = T("Add New Feature Class"),
        subtitle_list = LIST_FEATURE_CLASS,
        label_list_button = LIST_FEATURE_CLASS,
        label_create_button = ADD_FEATURE_CLASS,
        label_delete_button = T("Delete Feature Class"),
        msg_record_created = T("Feature Class added"),
        msg_record_modified = T("Feature Class updated"),
        msg_record_deleted = T("Feature Class deleted"),
        msg_list_empty = T("No Feature Classes currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def feature_group():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    #table.features.comment = DIV( _class="tooltip", _title=Tstr("Multi-Select") + "|" + Tstr("Click Features to select, Click again to Remove. Dark Green is selected."))
    #table.feature_classes.comment = DIV( _class="tooltip", _title=Tstr("Multi-Select") + "|" + Tstr("Click Features to select, Click again to Remove. Dark Green is selected."))

    # CRUD Strings
    LIST_FEATURE_GROUPS = T("List Feature Groups")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FEATURE_GROUP,
        title_display = T("Feature Group Details"),
        title_list = T("Feature Groups"),
        title_update = T("Edit Feature Group"),
        title_search = T("Search Feature Groups"),
        subtitle_create = T("Add New Feature Group"),
        subtitle_list = LIST_FEATURE_GROUPS,
        label_list_button = LIST_FEATURE_GROUPS,
        label_create_button = ADD_FEATURE_GROUP,
        label_delete_button = T("Delete Feature Group"),
        msg_record_created = T("Feature Group added"),
        msg_record_modified = T("Feature Group updated"),
        msg_record_deleted = T("Feature Group deleted"),
        msg_list_empty = T("No Feature Groups currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def feature_class_to_feature_group():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def feature_layer():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    table.query.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_FEATURE_LAYER = T("Add Feature Layer")
    LIST_FEATURE_LAYERS = T("List Feature Layers")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_FEATURE_LAYER,
        title_display = T("Feature Layer Details"),
        title_list = T("Feature Layers"),
        title_update = T("Edit Feature Layer"),
        title_search = T("Search Feature Layers"),
        subtitle_create = T("Add New Feature Layer"),
        subtitle_list = LIST_FEATURE_LAYERS,
        label_list_button = LIST_FEATURE_LAYERS,
        label_create_button = ADD_FEATURE_LAYER,
        label_delete_button = T("Delete Feature Layer"),
        msg_record_created = T("Feature Layer added"),
        msg_record_modified = T("Feature Layer updated"),
        msg_record_deleted = T("Feature Layer deleted"),
        msg_list_empty = T("No Feature Layers currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    crud.settings.create_onvalidation = lambda form: feature_layer_query(form)
    crud.settings.update_onvalidation = lambda form: feature_layer_query(form)

    output = shn_rest_controller(module, resource)

    return output

def feature_layer_query(form):
    """ OnValidation callback to build the simple Query from helpers """

    if "advanced" in form.vars:
        # We should use the query field as-is
        pass
    elif "resource" in form.vars:
        # We build query from helpers
        if "filter_field" in form.vars and "filter_value" in form.vars:
            if "deleted" in db[resource]:
                form.vars.query = "(db[%s].deleted == False) & (db[%s][%s] == '%s')" % (resource, resource, filter_field, filter_value)
            else:
                form.vars.query = "(db[%s][%s] == '%s')" % (resource, filter_field, filter_value)
        else:
            if "deleted" in db[resource]:
                # All undeleted members of the resource
                form.vars.query = "(db[%s].deleted == False)" % (resource)
            else:
                # All members of the resource
                form.vars.query = "(db[%s].id > 0)" % (resource)
    else:
        # Resource is mandatory if not in advanced mode
        session.error = T("Need to specify a Resource!")

    return

def location():
    """ RESTful CRUD controller for Locations """
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    if not shn_has_role("MapAdmin"):
        table.code.writable = False
        table.level.writable = False
        table.gis_feature_type.writable = table.gis_feature_type.readable = False
        table.wkt.writable = table.wkt.readable = False
    else:
        table.code.comment = DIV( _class="tooltip", _title=Tstr("Code") + "|" + Tstr("For a country this would be the ISO2 code, for a Town, it would be the Airport Locode."))
        table.level.comment = DIV( _class="tooltip", _title=Tstr("Level") + "|" + Tstr("If the location is a geographic area, then state at what level here."))
        table.parent.comment = DIV(A(ADD_LOCATION,
                                       _class="colorbox",
                                       _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", child="parent")),
                                       _target="top",
                                       _title=ADD_LOCATION),
                                     DIV(
                                       _class="tooltip",
                                       _title=Tstr("Parent") + "|" + Tstr("The Area which this Site is located within."))),
        table.wkt.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title="WKT" + "|" + Tstr("The <a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>Well-Known Text</a> representation of the Polygon/Line.")))

    # Model options which are only required in interactive HTML views
    table.name.comment = SPAN("*", _class="req")
    CONVERSION_TOOL = T("Conversion Tool")
    table.lat.comment = DIV(A(CONVERSION_TOOL, _style="cursor:pointer;", _title=CONVERSION_TOOL, _id="btnConvert"), DIV( _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds.")))
    table.lon.comment = DIV( _class="tooltip", _title=Tstr("Longitude") + "|" + Tstr("Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.  This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds."))
    table.osm_id.comment = DIV( _class="tooltip", _title="OSM ID" + "|" + Tstr("The <a href='http://openstreetmap.org' target=_blank>OpenStreetMap</a> ID. If you don't know the ID, you can just say 'Yes' if it has been added to OSM."))

    # CRUD Strings
    LIST_LOCATIONS = T("List Locations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOCATION,
        title_display = T("Location Details"),
        title_list = T("Locations"),
        title_update = T("Edit Location"),
        title_search = T("Search Locations"),
        subtitle_create = T("Add New Location"),
        subtitle_list = LIST_LOCATIONS,
        label_list_button = LIST_LOCATIONS,
        label_create_button = ADD_LOCATION,
        label_delete_button = T("Delete Location"),
        msg_record_created = T("Location added"),
        msg_record_modified = T("Location updated"),
        msg_record_deleted = T("Location deleted"),
        msg_list_empty = T("No Locations currently available"))

    # Options
    _vars = request.vars
    filters = []
    fclass = _vars.get("feature_class", None)
    if fclass:
        filters.append((db.gis_location.feature_class_id == db.gis_feature_class.id) &
                              (db.gis_feature_class.name.like(fclass)))

    fgroup = _vars.get("fgroup", None)
    if fgroup:
        # Filter to those Features which are in Feature Groups through their Feature Class
        filters.append((db.gis_location.feature_class_id == db.gis_feature_class_to_feature_group.feature_class_id) &
           (db.gis_feature_class_to_feature_group.feature_group_id == db.gis_feature_group.id) &
           (db.gis_feature_group.name.like(fgroup)))
        # We no longer support direct Features in Feature Groups (we can't easily OR this filter with previous one)
        #filters.append((db.gis_location.id == db.gis_location_to_feature_group.location_id) &
        #    (db.gis_location_to_feature_group.feature_group_id == db.gis_feature_group.id) & (db.gis_feature_group.name.like(fgroup)))

    parent = _vars.get("parent_", None)
    # Don't use 'parent' as the var as otherwise this will be triggered during form submission
    if parent:
        # Can't do this using a JOIN in DAL syntax
        # .belongs() not GAE-compatible!
        filters.append((db.gis_location.parent.belongs(db(db.gis_location.name.like(parent)).select(db.gis_location.id))))
        # ToDo: Make this recursive - want ancestor not just direct parent!

    caller = _vars.get("caller", None)
    if caller:
        if "gis_location_parent" in caller:
            # If a Parent location then populate defaults for the fields & Hide unnecessary rows
            table.description.readable = table.description.writable = False
            #table.level.readable = table.level.writable = False
            table.code.readable = table.code.writable = False
            table.feature_class_id.readable = table.feature_class_id.writable = False
            # Use default Marker for Class
            table.marker_id.readable = table.marker_id.writable = False
            #table.gis_feature_type.readable = table.gis_feature_type.writable = False
            #table.gis_feature_type.default =
            table.wkt.readable = table.wkt.writable = False
            table.addr_street.readable = table.addr_street.writable = False
            table.osm_id.readable = table.osm_id.writable = False
            table.source.readable = table.source.writable = False

        else:
            fc = None
            # When called from a Popup, populate defaults & hide unnecessary rows
            if "cr_shelter" in caller:
                fc = db(db.gis_feature_class.name == "Shelter").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "hms_hospital" in caller:
                fc = db(db.gis_feature_class.name == "Hospital").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "irs_ireport" in caller:
                fc = db(db.gis_feature_class.name == "Incident").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "org_office" in caller:
                fc = db(db.gis_feature_class.name == "Office").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "org_project" in caller:
                fc = db(db.gis_feature_class.name == "Project").select(db.gis_feature_class.id, limitby=(0, 1)).first()
            elif "pr_presence" in caller:
                fc = db(db.gis_feature_class.name == "Person").select(db.gis_feature_class.id, limitby=(0, 1)).first()
                table.level.readable = table.level.writable = False
                table.url.readable = table.url.writable = False
            elif "assessment_location" in caller:
                table.level.default = "L4"
                table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            elif "school_district" in caller:
                table.level.default = "L2"
                table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            elif "school_report_location" in caller:
                table.level.default = "L2"
                table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            elif "school_report_union" in caller:
                table.level.default = "L3"
                table.feature_class_id.readable = table.feature_class_id.writable = False
                table.marker_id.readable = table.marker_id.writable = False
                table.addr_street.readable = table.addr_street.writable = False
            
            try:
                table.feature_class_id.default = fc.id
                table.feature_class_id.readable = table.feature_class_id.writable = False
                # Use default Marker for Class
                table.marker_id.readable = table.marker_id.writable = False
            except:
                pass

            #table.level.readable = table.level.writable = False
            table.code.readable = table.code.writable = False
            table.gis_feature_type.readable = table.gis_feature_type.writable = False
            table.wkt.readable = table.wkt.writable = False
            table.osm_id.readable = table.osm_id.writable = False
            table.source.readable = table.source.writable = False

    # ToDo
    # if "bbox" in request.vars:

    if filters:
        response.s3.filter = reduce(__and__, filters)

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if isinstance(output, dict):
        output.update(gis_location_hierarchy=gis_location_hierarchy)

    return output

#@auth.shn_requires_membership("MapAdmin")
def marker():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")

    # CRUD Strings
    LIST_MARKERS = T("List Markers")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MARKER,
        title_display = T("Marker Details"),
        title_list = T("Markers"),
        title_update = T("Edit Marker"),
        title_search = T("Search Markers"),
        subtitle_create = T("Add New Marker"),
        subtitle_list = LIST_MARKERS,
        label_list_button = LIST_MARKERS,
        label_create_button = ADD_MARKER,
        label_delete_button = T("Delete Marker"),
        msg_record_created = T("Marker added"),
        msg_record_modified = T("Marker updated"),
        msg_record_deleted = T("Marker deleted"),
        msg_list_empty = T("No Markers currently available"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def projection():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.comment = SPAN("*", _class="req")
    table.epsg.comment = SPAN("*", _class="req")
    table.maxExtent.comment = SPAN("*", _class="req")
    table.maxResolution.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_PROJECTION = T("Add Projections")
    LIST_PROJECTIONS = T("List Projections")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_PROJECTION,
        title_display = T("Projection Details"),
        title_list = T("Projections"),
        title_update = T("Edit Projection"),
        title_search = T("Search Projections"),
        subtitle_create = T("Add New Projection"),
        subtitle_list = LIST_PROJECTIONS,
        label_list_button = LIST_PROJECTIONS,
        label_create_button = ADD_PROJECTION,
        label_delete_button = T("Delete Projection"),
        msg_record_created = T("Projection added"),
        msg_record_modified = T("Projection updated"),
        msg_record_deleted = T("Projection deleted"),
        msg_list_empty = T("No Projections currently defined"))

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def track():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options
    # used in multiple controllers, so defined in model

    # CRUD Strings
    # used in multiple controllers, so defined in model

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False)
    return output

# Common CRUD strings for all layers
ADD_LAYER = T("Add Layer")
LAYER_DETAILS = T("Layer Details")
LAYERS = T("Layers")
EDIT_LAYER = T("Edit Layer")
SEARCH_LAYERS = T("Search Layers")
ADD_NEW_LAYER = T("Add New Layer")
LIST_LAYERS = T("List Layers")
DELETE_LAYER = T("Delete Layer")
LAYER_ADDED = T("Layer added")
LAYER_UPDATED = T("Layer updated")
LAYER_DELETED = T("Layer deleted")
# These may be differentiated per type of layer.
TYPE_LAYERS_FMT = "%s Layers"
ADD_NEW_TYPE_LAYER_FMT = "Add New %s Layer"
EDIT_TYPE_LAYER_FMT = "Edit %s Layer"
LIST_TYPE_LAYERS_FMT = "List %s Layers"
NO_TYPE_LAYERS_FMT = "No %s Layers currently defined"

#@auth.shn_requires_membership("MapAdmin")
def layer_openstreetmap():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "OpenStreetMap"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_google():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "Google"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_yahoo():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "Yahoo"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_mgrs():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "MGRS"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_bing():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "Bing"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource, deletable=False, listadd=False)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_georss():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "GeoRSS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_gpx():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options
    # Needed in multiple controllers, so defined in Model

    # CRUD Strings
    type = "GPX"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_kml():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "KML"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_tms():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")
    table.layers.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "TMS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_wms():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")
    table.layers.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "WMS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("AdvancedJS")
def layer_js():
    "RESTful CRUD controller"
    resource = request.function
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "JS"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

#@auth.shn_requires_membership("MapAdmin")
def layer_xyz():
    "RESTful CRUD controller"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "XYZ"
    LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    EDIT_LAYER = T(EDIT_LAYER_FMT % type)
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_LAYERS)

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

# Feature Groups
#@auth.shn_requires_membership("MapAdmin")
def feature_group_contents():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f="feature_group"))
    feature_group = request.args(0)
    table = db.gis_feature_class_to_feature_group
    authorised = shn_has_permission("update", table)

    title = str(T("Feature Group")) + ": " + str(db.gis_feature_group[feature_group].name)
    subtitle = T("Contents")
    feature_group_description = str(B(T("Description"))) + ": " + str(db.gis_feature_group[feature_group].description)
    # Start building the Return with the common items
    output = dict(title=title, description=feature_group_description)
    # Audit
    #shn_audit_read(operation="list", resource="feature_group_contents", record=feature_group, representation="html")
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, "feature_group_contents", "html")
        # Display a List_Create page with checkboxes to remove items

        # Feature Classes
        query = (table.feature_group_id == feature_group) & (table.deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class_id
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f="feature_class", args=[id, "read"]))
            checkbox = INPUT(_type="checkbox", _value="on", _name="feature_class_" + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align="left"), TD(description, _align="left"), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH("Name"), TH(T("Description")), TH(T("Remove"))))
        table_footer = TFOOT(TR(TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")))), _colspan=3, _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(r=request, f="feature_group_update_items", args=[feature_group])))

        crud.messages.submit_button=T("Add")
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: feature_group_dupes(form)
        crud.messages.record_created = T("Feature Group Updated")
        form = crud.create(table, next=URL(r=request, args=[feature_group]))
        #form[0][0].append(TR(TD(T("Type:")), TD(LABEL(T("Feature Class"), INPUT(_type="radio", _name="fg1", _value="FeatureClass", value="FeatureClass")), LABEL(T("Feature"), INPUT(_type="radio", _name="fg1", _value="Feature", value="FeatureClass")))))
        addtitle = T("Add Feature Class to Feature Group")
        response.view = "%s/feature_group_contents_list_create.html" % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form, feature_group=feature_group))
    else:
        # Display a simple List page
        # Feature Classes
        query = (table.feature_group_id == feature_group) & (table.deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class_id
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f="feature_class", args=[id, "read"]))
            item_list.append(TR(TD(id_link), TD(name, _align="left"), TD(description, _align="left"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH("Name"), TH(T("Description"))))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

        add_btn = A(T("Edit Contents"), _href=URL(r=request, c="default", f="user", args="login"), _class="action-btn")
        response.view = "%s/feature_group_contents_list.html" % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def feature_group_dupes(form):
    "Checks for duplicate FeatureClass before adding to DB"
    feature_group = form.vars.feature_group
    if "feature_class_id" in form.vars:
        feature_class_id = form.vars.feature_class_id
        table = db.gis_feature_class_to_feature_group
        query = (table.feature_group == feature_group) & (table.feature_class_id == feature_class_id)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Already in this Feature Group!")
        redirect(URL(r=request, args=feature_group))
    else:
        return

def feature_group_update_items():
    "Update a Feature Group's items (Feature Classes & Features)"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f="feature_group"))
    feature_group = request.args(0)
    table = db.gis_feature_class_to_feature_group
    authorised = shn_has_permission("update", table)
    if authorised:
        for var in request.vars:
            if "feature_class_id" in var:
                # Delete
                feature_class_id = var[14:]
                query = (table.feature_group == feature_group) & (table.feature_class_id == feature_class_id)
                db(query).delete()
        # Audit
        shn_audit_update_m2m(resource="feature_group_contents", record=feature_group, representation="html")
        session.flash = T("Feature Group updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f="feature_group_contents", args=[feature_group]))

def convert_gps():
    " Provide a form which converts from GPS Coordinates to Decimal Coordinates "
    return dict()

def display_feature():
    """
    Cut-down version of the Map Viewing Client.
    Used by shn_gis_location_represent() to show just this feature on the map.
    Called by the viewMap() JavaScript
    """

    # The Feature
    feature_id = request.args(0)

    # Check user is authorised to access record
    if not shn_has_permission("read", db.gis_location, feature_id):
        session.error = str(T("No access to this record!"))
        raise HTTP(401, body=s3xrc.xml.json_message(False, 401, session.error))

    query = db(db.gis_location.id == feature_id).select(limitby=(0, 1))
    feature = query.first()

    # Centre on Feature
    lat = feature.lat
    lon = feature.lon

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=query)

    map = gis.show_map(
        feature_queries = [{"name" : "Feature", "query" : query, "active" : True}],
        lat = lat,
        lon = lon,
        bbox = bounds,
        window = True,
        collapsed = True
    )

    return dict(map=map)

def display_features():
    """
    Cut-down version of the Map Viewing Client.
    Used as a link from the RHeader.
        URL generated server-side
    Shows all locations matching a query.
    ToDo: Most recent location is marked using a bigger Marker.
    """

    # Parse the URL, check for implicit resources, extract the primary record
    # http://127.0.0.1:8000/eden/gis/display_features&module=pr&resource=person&instance=1&jresource=presence
    ok = 0
    if "module" in request.vars:
        res_module = request.vars.module
        ok +=1
    if "resource" in request.vars:
        resource = request.vars.resource
        ok +=1
    if "instance" in request.vars:
        instance = int(request.vars.instance)
        ok +=1
    if "jresource" in request.vars:
        jresource = request.vars.jresource
        ok +=1
    if ok != 4:
        session.error = str(T("Insufficient vars: Need module, resource, jresource, instance"))
        raise HTTP(400, body=s3xrc.xml.json_message(False, 400, session.error))

    component, pkey, fkey = s3xrc.model.get_component(res_module, resource, jresource)
    table = db["%s_%s" % (res_module, resource)]
    jtable = db[str(component.table)]
    query = (jtable[fkey] == table[pkey]) & (table.id == instance)
    # Filter out deleted
    deleted = (table.deleted == False)
    query = query & deleted
    # Filter out inaccessible
    query2 = db.gis_location.id == jtable.location_id
    accessible = shn_accessible_query("read", db.gis_location)
    query2 = query2 & accessible

    features = db(query).select(db.gis_location.ALL, left = [db.gis_location.on(query2)])

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=features)

    map = gis.show_map(
        feature_queries = [{"name" : "Features", "query" : features, "active" : True}],
        bbox = bounds,
        window = True,
        collapsed = True
    )

    return dict(map=map)

def geolocate():
    " Call a Geocoder service "
    if "location" in request.vars:
        location = request.vars.location
    else:
        session.error = T("Need to specify a location to search for.")
        redirect(URL(r=request, f="index"))

    if "service" in request.vars:
        service = request.vars.service
    else:
        # ToDo service=all should be default
        service = "google"

    if service == "google":
        return s3gis.GoogleGeocoder(location, db).get_kml()

    if service == "yahoo":
        return s3gis.YahooGeocoder(location, db).get_xml()

def layers_enable():
    """
    Enable/Disable Layers
    """

    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission("update", table)
    if authorised:
        for type in gis_layer_types:
            resource = "gis_layer_%s" % type
            table = db[resource]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                query_inner = (table.id == row.id)
                var = "%s_%i" % (type, row.id)
                # Read current state
                if db(query_inner).select(table.enabled, limitby=(0, 1)).first().enabled:
                    # Old state: Enabled
                    if var in request.vars:
                        # Do nothing
                        pass
                    else:
                        # Disable
                        db(query_inner).update(enabled=False)
                        # Audit
                        #shn_audit_update_m2m(resource=resource, record=row.id, representation="html")
                        shn_audit_update_m2m(resource, row.id, "html")
                else:
                    # Old state: Disabled
                    if var in request.vars:
                        # Enable
                        db(query_inner).update(enabled=True)
                        # Audit
                        shn_audit_update_m2m(resource, row.id, "html")
                    else:
                        # Do nothing
                        pass
        session.flash = T("Layers updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f="map_service_catalogue"))

#@auth.shn_requires_membership("MapAdmin")
def map_service_catalogue():
    """
    Map Service Catalogue.
    Allows selection of which Layers are active.
    """

    subtitle = T("List Layers")
    # Start building the Return with the common items
    output = dict(subtitle=subtitle)

    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission("update", table)
    item_list = []
    even = True
    if authorised:
        # List View with checkboxes to Enable/Disable layers
        for type in gis_layer_types:
            table = db["gis_layer_%s" % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ""
                label = type + "_" + str(row.id)
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value=True, _name=label)
                else:
                    enabled = INPUT(_type="checkbox", _name=label)
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))

        table_header = THEAD(TR(TH("Layer"), TH("Description"), TH("Enabled?")))
        table_footer = TFOOT(TR(TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")), _colspan=3)), _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(r=request, f="layers_enable")))

    else:
        # Simple List View
        for type in gis_layer_types:
            table = db["gis_layer_%s" % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ""
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value="on", _disabled="disabled")
                else:
                    enabled = INPUT(_type="checkbox", _disabled="disabled")
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))

        table_header = THEAD(TR(TH("Layer"), TH("Description"), TH("Enabled?")))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

    output.update(dict(items=items))
    return output

def map_viewing_client():
    """
        Map Viewing Client.
        UI for a user to view the overall Maps with associated Features
    """

    # Read configuration settings
    config = gis.get_config()
    if config.opt_gis_layout == 1:
        window = True
    else:
        window = False

    # @ToDo Make Configurable
    toolbar = True
    
    map = define_map(window=window, toolbar=toolbar)

    return dict(map=map)

def proxy():
    """
    Based on http://trac.openlayers.org/browser/trunk/openlayers/examples/proxy.cgi
    This is a blind proxy that we use to get around browser
    restrictions that prevent the Javascript from loading pages not on the
    same server as the Javascript. This has several problems: it's less
    efficient, it might break some sites, and it's a security risk because
    people can use this proxy to browse the web and possibly do bad stuff
    with it. It only loads pages via http and https, but it can load any
    content type. It supports GET and POST requests.
    """

    import urllib2
    import cgi
    import sys, os

    # ToDo - need to link to map_service_catalogue
    # prevent Open Proxy abuse
    allowedHosts = []
    #allowedHosts = ["www.openlayers.org", "openlayers.org",
    #                "labs.metacarta.com", "world.freemap.in",
    #                "prototype.openmnnd.org", "geo.openplans.org",
    #                "sigma.openplans.org", "demo.opengeo.org",
    #                "www.openstreetmap.org", "sample.avencia.com",
    #                "v-swe.uni-muenster.de:8080"]

    method = request["wsgi"].environ["REQUEST_METHOD"]

    if method == "POST":
        # This can probably use same call as GET in web2py
        qs = request["wsgi"].environ["QUERY_STRING"]

        d = cgi.parse_qs(qs)
        if d.has_key("url"):
            url = d["url"][0]
        else:
            url = "http://www.openlayers.org"
    else:
        # GET
        #fs = cgi.FieldStorage()
        #url = fs.getvalue("url", "http://www.openlayers.org")
        if "url" in request.vars:
            url = request.vars.url
        else:
            session.error = str(T("Need a 'url' argument!"))
            raise HTTP(400, body=s3xrc.xml.json_message(False, 400, session.error))

    try:
        host = url.split("/")[2]
        if allowedHosts and not host in allowedHosts:
            msg = "Status: 502 Bad Gateway\n"
            msg += "Content-Type: text/plain\n\n"
            msg += "This proxy does not allow you to access that location (%s).\n\n" % (host,)

            msg += os.environ
            return msg

        elif url.startswith("http://") or url.startswith("https://"):
            if method == "POST":
                length = int(request["wsgi"].environ["CONTENT_LENGTH"])
                headers = {"Content-Type": request["wsgi"].environ["CONTENT_TYPE"]}
                body = request.body.read(length)
                r = urllib2.Request(url, body, headers)
                y = urllib2.urlopen(r)
            else:
                y = urllib2.urlopen(url)

            # print content type header
            # TODO: this doesn't work in web2py, need to figure out how that happens?
            #i = y.info()
            #if i.has_key("Content-Type"):
            # msg = "Content-Type: %s" % (i["Content-Type"])
            #else:
            # msg = "Content-Type: text/plain"

            #msg += "\n" + y.read()

            msg = y.read()
            y.close()
            return msg
        else:
            msg = "Content-Type: text/plain\n\n"

            msg += "Illegal request."
            return msg

    except Exception, E:
        msg = "Status: 500 Unexpected Error\n"
        msg += "Content-Type: text/plain\n\n"
        msg += "Some unexpected error occurred. Error text was: %s" % str(E)
        return msg
