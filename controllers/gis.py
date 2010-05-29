# -*- coding: utf-8 -*-

"""
    GIS Controllers

    @author: Fran Boon
"""

from operator import __and__

module = "gis"

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Map Viewing Client"), False, URL(r=request, f="map_viewing_client")],
    [T("Map Service Catalogue"), False, URL(r=request, f="map_service_catalogue")],
    [T("Bulk Uploader"), False, URL(r=request, c="media", f="bulk_upload")],
]

# Model options used in multiple Actions
table = db.gis_location
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)
table.name.requires = IS_NOT_EMPTY()    # Placenames don't have to be unique
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
table.level.label = T("Level")
table.level.comment = DIV( _class="tooltip", _title=T("Level|The Level in the Hierarchy of this location: L0=Country, L1=State, L2=District, L3=Town."))
table.code.label = T("Code")
table.code.comment = DIV( _class="tooltip", _title=T("Code|For a country this would be the ISO2 code, for a Town, it would be the Airport Locode."))
table.description.label = T("Description")
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.gis_location.id==id).select().first().name] or ["None"])[0]
table.parent.label = T("Parent")
table.addr_street.label = T("Street Address")
table.gis_feature_type.requires = IS_IN_SET(gis_feature_type_opts)
table.gis_feature_type.represent = lambda opt: gis_feature_type_opts.get(opt, UNKNOWN_OPT)
table.gis_feature_type.label = T("Feature Type")
table.wkt.represent = lambda wkt: gis.abbreviate_wkt(wkt)
table.lat.requires = IS_NULL_OR(IS_LAT())
table.lat.label = T("Latitude")
#table.lat.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere."))
CONVERSION_TOOL = T("Conversion Tool")
#table.lat.comment = DIV(SPAN("*", _class="req"), A(CONVERSION_TOOL, _class="colorbox", _href=URL(r=request, c="gis", f="convert_gps", vars=dict(KeepThis="true"))+"&TB_iframe=true", _target="top", _title=CONVERSION_TOOL), DIV( _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds."))
table.lat.comment = DIV(SPAN("*", _class="req"), A(CONVERSION_TOOL, _style="cursor:pointer;", _title=CONVERSION_TOOL, _id="btnConvert"), DIV( _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds.")))
table.lon.requires = IS_NULL_OR(IS_LON())
table.lon.label = T("Longitude")
table.lon.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("Longitude|Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.  This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds.")))
# WKT validation is done in the onvalidation callback
#table.wkt.requires=IS_NULL_OR(IS_WKT())
table.wkt.label = T("Well-Known Text")
table.wkt.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("WKT|The <a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>Well-Known Text</a> representation of the Polygon/Line.")))
table.osm_id.label = "OpenStreetMap"
table.osm_id.comment = DIV( _class="tooltip", _title=T("OSM ID|The <a href='http://openstreetmap.org' target=_blank>OpenStreetMap</a> ID. If you don't know the ID, you can just say 'Yes' if it has been added to OSM."))

# Joined Resource
#s3xrc.model.add_component("media", "metadata",
#    multiple=True,
#    joinby=dict(gis_location="location_id"),
#    deletable=True,
#    editable=True,
#    list_fields = ["id", "description", "source", "event_time", "url"])

# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db)

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def test():
    "Test server-parsed GIS functions"
    html = gis.show_map(
                feature_overlays = [{"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location")}]
                )
    return dict(map=html)

def apikey():
    "RESTlike CRUD controller"
    resource = "apikey"
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    # FIXME
    # We want a THIS_NOT_IN_DB here: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540/fc129fd476558944?lnk=gst&q=THIS_NOT_IN_DB#fc129fd476558944
    table.name.requires = IS_IN_SET(["google", "multimap", "yahoo"])
    table.name.label = T("Service")
    #table.apikey.requires = THIS_NOT_IN_DB(db(table.name==request.vars.name), "gis_apikey.name", request.vars.name, "Service already in use")
    table.apikey.requires = IS_NOT_EMPTY()
    table.apikey.label = T("Key")
    table.apikey.comment = SPAN("*", _class="req")

    # CRUD Strings
    ADD_KEY = T("Add Key")
    LIST_KEYS = T("List Keys")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_KEY,
        title_display = T("Key Details"),
        title_list = LIST_KEYS,
        title_update = T("Edit Key"),
        title_search = T("Search Keys"),
        subtitle_create = T("Add New Key"),
        subtitle_list = T("Keys"),
        label_list_button = LIST_KEYS,
        label_create_button = ADD_KEY,
        label_delete_button = T("Delete Key"),
        msg_record_created = T("Key added"),
        msg_record_modified = T("Key updated"),
        msg_record_deleted = T("Key deleted"),
        msg_list_empty = T("No Keys currently defined"))

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def config():
    "RESTlike CRUD controller"
    resource = "config"
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.uuid.requires = IS_NOT_IN_DB(db, "gis_config.uuid")
    table.lat.requires = IS_LAT()
    table.lat.label = T("Latitude")
    table.lat.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
    table.lon.requires = IS_LON()
    table.lon.label = T("Longitude")
    table.lon.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("Longitude|Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
    table.zoom.requires = IS_INT_IN_RANGE(0, 19)
    table.zoom.label = T("Zoom")
    table.zoom.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("Zoom|How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))
    table.marker_id.label = T("Default Marker")
    table.map_height.requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(50, 1024)]
    table.map_height.label = T("Map Height")
    table.map_height.comment = SPAN("*", _class="req")
    table.map_width.requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(50, 1280)]
    table.map_width.label = T("Map Width")
    table.map_width.comment = SPAN("*", _class="req")
    table.zoom_levels.requires = IS_INT_IN_RANGE(1, 30)
    table.zoom_levels.label = T("Zoom Levels")
    table.cluster_distance.requires = IS_INT_IN_RANGE(1, 30)
    table.cluster_distance.label = T("Cluster Distance")
    table.cluster_threshold.requires = IS_INT_IN_RANGE(1, 10)
    table.cluster_threshold.label = T("Cluster Threshold")

    # CRUD Strings
    ADD_CONFIG = T("Add Config")
    LIST_CONFIGS = T("List Configs")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_CONFIG,
        title_display = T("Config Details"),
        title_list = LIST_CONFIGS,
        title_update = T("Edit Config"),
        title_search = T("Search Configs"),
        subtitle_create = T("Add New Config"),
        subtitle_list = T("Configs"),
        label_list_button = LIST_CONFIGS,
        label_create_button = ADD_CONFIG,
        label_delete_button = T("Delete Config"),
        msg_record_created = T("Config added"),
        msg_record_modified = T("Config updated"),
        msg_record_deleted = T("Config deleted"),
        msg_list_empty = T("No Configs currently defined"))

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def feature_class():
    "RESTlike CRUD controller"
    resource = "feature_class"
    table = module + "_" + resource

    # Model options
    resource_opts = {
        "shelter":T("Shelter"),
        "office":T("Office"),
        "track":T("Track"),
        "image":T("Photo"),
        }
    db[table].uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % table)]
    db[table].name.label = T("Name")
    db[table].name.comment = SPAN("*", _class="req")
    db[table].description.label = T("Description")
    db[table].module.requires = IS_NULL_OR(IS_ONE_OF(db((db.s3_module.enabled=="True") & (~db.s3_module.name.like("default"))), "s3_module.name", "%(name_nice)s"))
    db[table].module.label = T("Module")
    db[table].resource.requires = IS_NULL_OR(IS_IN_SET(resource_opts))
    db[table].resource.label = T("Resource")

    # CRUD Strings
    LIST_FEATURE_CLASS = T("List Feature Classes")
    s3.crud_strings[table] = Storage(
        title_create = ADD_FEATURE_CLASS,
        title_display = T("Feature Class Details"),
        title_list = LIST_FEATURE_CLASS,
        title_update = T("Edit Feature Class"),
        title_search = T("Search Feature Class"),
        subtitle_create = T("Add New Feature Class"),
        subtitle_list = T("Feature Classes"),
        label_list_button = LIST_FEATURE_CLASS,
        label_create_button = ADD_FEATURE_CLASS,
        label_delete_button = T("Delete Feature Class"),
        msg_record_created = T("Feature Class added"),
        msg_record_modified = T("Feature Class updated"),
        msg_record_deleted = T("Feature Class deleted"),
        msg_list_empty = T("No Feature Classes currently defined"))

    return shn_rest_controller(module, resource)

def feature_group():
    "RESTlike CRUD controller"
    resource = "feature_group"
    table = module + "_" + resource

    # Model options
    db[table].uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)
    #db[table].author.requires = IS_ONE_OF(db, "auth_user.id","%(id)s: %(first_name)s %(last_name)s")
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % table)]
    db[table].name.label = T("Name")
    db[table].name.comment = SPAN("*", _class="req")
    db[table].description.label = T("Description")
    #db[table].features.comment = DIV( _class="tooltip", _title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))
    #db[table].feature_classes.comment = DIV( _class="tooltip", _title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))

    # CRUD Strings
    LIST_FEATURE_GROUPS = T("List Feature Groups")
    s3.crud_strings[table] = Storage(
        title_create = ADD_FEATURE_GROUP,
        title_display = T("Feature Group Details"),
        title_list = LIST_FEATURE_GROUPS,
        title_update = T("Edit Feature Group"),
        title_search = T("Search Feature Groups"),
        subtitle_create = T("Add New Feature Group"),
        subtitle_list = T("Feature Groups"),
        label_list_button = LIST_FEATURE_GROUPS,
        label_create_button = ADD_FEATURE_GROUP,
        label_delete_button = T("Delete Feature Group"),
        msg_record_created = T("Feature Group added"),
        msg_record_modified = T("Feature Group updated"),
        msg_record_deleted = T("Feature Group deleted"),
        msg_list_empty = T("No Feature Groups currently defined"))

    return shn_rest_controller(module, resource)


def location_to_feature_group():
    "RESTlike CRUD controller"
    resource = "location_to_feature_group"
    table = module + "_" + resource

    # Model options

    # CRUD Strings

    return shn_rest_controller(module, resource)

def feature_class_to_feature_group():
    "RESTlike CRUD controller"
    resource = "feature_class_to_feature_group"
    table = module + "_" + resource

    # Model options

    # CRUD Strings

    return shn_rest_controller(module, resource)

def location():
    "RESTlike CRUD controller"
    resource = "location"
    tablename = module + "_" + resource

    # Model options
    # used in multiple controllers, so at the top of the file

    # CRUD Strings
    LIST_LOCATIONS = T("List Locations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_LOCATION,
        title_display = T("Location Details"),
        title_list = LIST_LOCATIONS,
        title_update = T("Edit Location"),
        title_search = T("Search Locations"),
        subtitle_create = T("Add New Location"),
        subtitle_list = T("Locations"),
        label_list_button = LIST_LOCATIONS,
        label_create_button = ADD_LOCATION,
        label_delete_button = T("Delete Location"),
        msg_record_created = T("Location added"),
        msg_record_modified = T("Location updated"),
        msg_record_deleted = T("Location deleted"),
        msg_list_empty = T("No Locations currently available"))

    filters = []
    if "feature_class" in request.vars:
        fclass = request.vars["feature_class"]
        filters.append((db.gis_location.feature_class_id == db.gis_feature_class.id) &
                              (db.gis_feature_class.name.like(fclass)))

    if "feature_group" in request.vars:
        fgroup = request.vars["feature_group"]
        # Filter to those Features which are in Feature Groups through their Feature Class
        filters.append((db.gis_location.feature_class_id == db.gis_feature_class_to_feature_group.feature_class_id) &
           (db.gis_feature_class_to_feature_group.feature_group_id == db.gis_feature_group.id) &
           (db.gis_feature_group.name.like(fgroup)))
        # We no longer support direct Features in Feature Groups (we can't easily OR this filter with previous one)
        #filters.append((db.gis_location.id == db.gis_location_to_feature_group.location_id) &
        #    (db.gis_location_to_feature_group.feature_group_id == db.gis_feature_group.id) & (db.gis_feature_group.name.like(fgroup)))

    if "parent" in request.vars:
        parent = request.vars["parent"]
        # Can't do this using a JOIN in DAL syntax
        # .belongs() not GAE-compatible!
        filters.append((db.gis_location.parent.belongs(db(db.gis_location.name.like(parent)).select(db.gis_location.id))))
        # ToDo: Make this recursive - want ancestor not just direct parent!

    # ToDo
    # if "bbox" in request.vars:
        
    if filters:
        response.s3.filter = reduce(__and__, filters)

    response.s3.pagination = True

    return shn_rest_controller(module, resource)

def marker():
    "RESTlike CRUD controller"
    resource = "marker"
    table = module + "_" + resource

    # Model options
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % table)]
    db[table].name.label = T("Name")
    db[table].name.comment = SPAN("*", _class="req")
    db[table].image.label = T("Image")

    # CRUD Strings
    LIST_MARKERS = T("List Markers")
    s3.crud_strings[table] = Storage(
        title_create = ADD_MARKER,
        title_display = T("Marker Details"),
        title_list = LIST_MARKERS,
        title_update = T("Edit Marker"),
        title_search = T("Search Markers"),
        subtitle_create = T("Add New Marker"),
        subtitle_list = T("Markers"),
        label_list_button = LIST_MARKERS,
        label_create_button = ADD_MARKER,
        label_delete_button = T("Delete Marker"),
        msg_record_created = T("Marker added"),
        msg_record_modified = T("Marker updated"),
        msg_record_deleted = T("Marker deleted"),
        msg_list_empty = T("No Markers currently available"))

    return shn_rest_controller(module, resource)

def projection():
    "RESTlike CRUD controller"
    resource = "projection"
    table = module + "_" + resource

    # Model options
    db[table].uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % table)]
    db[table].name.label = T("Name")
    db[table].name.comment = SPAN("*", _class="req")
    db[table].epsg.requires = IS_NOT_EMPTY()
    db[table].epsg.label = "EPSG"
    db[table].epsg.comment = SPAN("*", _class="req")
    db[table].maxExtent.requires = IS_NOT_EMPTY()
    db[table].maxExtent.label = T("maxExtent")
    db[table].maxExtent.comment = SPAN("*", _class="req")
    db[table].maxResolution.requires = IS_NOT_EMPTY()
    db[table].maxResolution.label = T("maxResolution")
    db[table].maxResolution.comment = SPAN("*", _class="req")
    db[table].units.requires = IS_IN_SET(["m", "degrees"])
    db[table].units.label = T("Units")

    # CRUD Strings
    ADD_PROJECTION = T("Add Projections")
    LIST_PROJECTIONS = T("List Projections")
    s3.crud_strings[table] = Storage(
        title_create = ADD_PROJECTION,
        title_display = T("Projection Details"),
        title_list = LIST_PROJECTIONS,
        title_update = T("Edit Projection"),
        title_search = T("Search Projections"),
        subtitle_create = T("Add New Projection"),
        subtitle_list = T("Projections"),
        label_list_button = LIST_PROJECTIONS,
        label_create_button = ADD_PROJECTION,
        label_delete_button = T("Delete Projection"),
        msg_record_created = T("Projection added"),
        msg_record_modified = T("Projection updated"),
        msg_record_deleted = T("Projection deleted"),
        msg_list_empty = T("No Projections currently defined"))

    return shn_rest_controller(module, resource, deletable=False)

def track():
    "RESTlike CRUD controller"
    resource = "track"
    table = module + "_" + resource

    # Model options
    # used in multiple controllers, so defined in model

    # CRUD Strings
    # used in multiple controllers, so defined in model

    return shn_rest_controller(module, resource)

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
LIST_TYPE_LAYERS_FMT = "List %s Layers"
NO_TYPE_LAYERS_FMT = "No %s Layers currently defined"

def layer_openstreetmap():
    "RESTlike CRUD controller"
    resource = "layer_openstreetmap"
    table = module + "_" + resource

    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_openstreetmap_subtypes)

    # CRUD Strings
    type = "OpenStreetMap"
    LIST_OSM_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_OSM_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_OSM_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_OSM_LAYERS)

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def layer_google():
    "RESTlike CRUD controller"
    resource = "layer_google"
    table = module + "_" + resource

    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_google_subtypes)

    # CRUD Strings
    type = "Google"
    LIST_GOOGLE_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_GOOGLE_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_GOOGLE_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_GOOGLE_LAYERS)

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def layer_yahoo():
    "RESTlike CRUD controller"
    resource = "layer_yahoo"
    table = module + "_" + resource

    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_yahoo_subtypes)

    # CRUD Strings
    type = "Yahoo"
    LIST_YAHOO_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_YAHOO_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_YAHOO_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_YAHOO_LAYERS)

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def layer_mgrs():
    "RESTlike CRUD controller"
    resource = "layer_mgrs"
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "MGRS"
    LIST_MGRS_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_MGRS_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_MGRS_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_MGRS_LAYERS)

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def layer_bing():
    "RESTlike CRUD controller"
    resource = "layer_bing"
    table = module + "_" + resource

    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_bing_subtypes)

    # CRUD Strings
    type = "Bing"
    LIST_BING_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_BING_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_LAYER,
        subtitle_list=LIST_LAYERS,
        label_list_button=LIST_BING_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_BING_LAYERS)

    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def layer_georss():
    "RESTlike CRUD controller"
    resource = "layer_georss"
    table = module + "_" + resource

    # Model options
    #db[table].url.requires = [IS_URL, IS_NOT_EMPTY()]
    db[table].url.requires = IS_NOT_EMPTY()
    db[table].url.comment = SPAN("*", _class="req")
    db[table].projection_id.requires = IS_ONE_OF(db, "gis_projection.id", "%(name)s")
    db[table].projection_id.default = 2

    # CRUD Strings
    type = "GeoRSS"
    GEORSS_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_GEORSS_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_GEORSS_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_GEORSS_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=GEORSS_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_GEORSS_LAYER,
        subtitle_list=LIST_GEORSS_LAYERS,
        label_list_button=LIST_GEORSS_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_GEORSS_LAYERS)

    return shn_rest_controller(module, resource)

def layer_gpx():
    "RESTlike CRUD controller"
    resource = "layer_gpx"
    table = module + "_" + resource

    # Model options
    # Needed in multiple controllers, so defined in Model

    # CRUD Strings
    type = "GPX"
    GPX_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_GPX_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_GPX_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_GPX_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=GPX_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_GPX_LAYER,
        subtitle_list=LIST_GPX_LAYERS,
        label_list_button=LIST_GPX_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_GPX_LAYERS)

    return shn_rest_controller(module, resource)

def layer_kml():
    "RESTlike CRUD controller"
    resource = "layer_kml"
    table = module + "_" + resource

    # Model options
    #db[table].url.requires = [IS_URL, IS_NOT_EMPTY()]
    db[table].url.requires = IS_NOT_EMPTY()
    db[table].url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "KML"
    KML_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_KML_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_KML_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_KML_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=KML_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_KML_LAYER,
        subtitle_list=LIST_KML_LAYERS,
        label_list_button=LIST_KML_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_KML_LAYERS)

    return shn_rest_controller(module, resource)

def layer_tms():
    "RESTlike CRUD controller"
    resource = "layer_tms"
    table = module + "_" + resource

    # Model options
    #db[table].url.requires = [IS_URL, IS_NOT_EMPTY()]
    db[table].url.requires = IS_NOT_EMPTY()
    db[table].url.comment = SPAN("*", _class="req")
    db[table].layers.requires = IS_NOT_EMPTY()
    db[table].layers.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "TMS"
    TMS_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_TMS_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_TMS_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_TMS_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=TMS_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_TMS_LAYER,
        subtitle_list=LIST_TMS_LAYERS,
        label_list_button=LIST_TMS_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_TMS_LAYERS)

    return shn_rest_controller(module, resource)

def layer_wms():
    "RESTlike CRUD controller"
    resource = "layer_wms"
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    #table.url.requires = [IS_URL, IS_NOT_EMPTY()]
    table.url.requires = IS_NOT_EMPTY()
    table.url.comment = SPAN("*", _class="req")
    table.layers.requires = IS_NOT_EMPTY()
    table.layers.comment = SPAN("*", _class="req")
    table.format.requires = IS_NULL_OR(IS_IN_SET(["image/jpeg", "image/png"]))
    table.projection_id.requires = IS_ONE_OF(db, "gis_projection.id", "%(name)s")
    table.projection_id.default = 2

    # CRUD Strings
    type = "WMS"
    WMS_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_WMS_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_WMS_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_WMS_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=WMS_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_WMS_LAYER,
        subtitle_list=LIST_WMS_LAYERS,
        label_list_button=LIST_WMS_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_WMS_LAYERS)

    return shn_rest_controller(module, resource)

#@auth.requires_membership("AdvancedJS")
def layer_js():
    "RESTlike CRUD controller"
    resource = "layer_js"
    table = module + "_" + resource

    # Model options

    # CRUD Strings
    type = "JS"
    JS_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_JS_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_JS_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_JS_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[table] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=JS_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_JS_LAYER,
        subtitle_list=LIST_JS_LAYERS,
        label_list_button=LIST_JS_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_JS_LAYERS)

    return shn_rest_controller(module, resource)

def layer_xyz():
    "RESTlike CRUD controller"
    resource = "layer_xyz"
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.url.requires = IS_NOT_EMPTY()
    table.url.comment = SPAN("*", _class="req")

    # CRUD Strings
    type = "XYZ"
    XYZ_LAYERS = T(TYPE_LAYERS_FMT % type)
    ADD_NEW_XYZ_LAYER = T(ADD_NEW_TYPE_LAYER_FMT % type)
    LIST_XYZ_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    NO_XYZ_LAYERS = T(NO_TYPE_LAYERS_FMT % type)
    s3.crud_strings[tablename] = Storage(
        title_create=ADD_LAYER,
        title_display=LAYER_DETAILS,
        title_list=XYZ_LAYERS,
        title_update=EDIT_LAYER,
        title_search=SEARCH_LAYERS,
        subtitle_create=ADD_NEW_XYZ_LAYER,
        subtitle_list=LIST_XYZ_LAYERS,
        label_list_button=LIST_XYZ_LAYERS,
        label_create_button=ADD_LAYER,
        label_delete_button = DELETE_LAYER,
        msg_record_created=LAYER_ADDED,
        msg_record_modified=LAYER_UPDATED,
        msg_record_deleted=LAYER_DELETED,
        msg_list_empty=NO_XYZ_LAYERS)

    return shn_rest_controller(module, resource)

# Module-specific functions
def convert_gps():
    " Provide a form which converts from GPS Coordinates to Decimal Coordinates "
    return dict()

def proxy():
    """Based on http://trac.openlayers.org/browser/trunk/openlayers/examples/proxy.cgi
This is a blind proxy that we use to get around browser
restrictions that prevent the Javascript from loading pages not on the
same server as the Javascript. This has several problems: it's less
efficient, it might break some sites, and it's a security risk because
people can use this proxy to browse the web and possibly do bad stuff
with it. It only loads pages via http and https, but it can load any
content type. It supports GET and POST requests."""

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

# Features
# - experimental!
def feature_create_map():
    "Show a map to draw the feature"
    title = T("Add GIS Feature")
    form = crud.create("gis_location", onvalidation=lambda form: gis.wkt_centroid(form))
    _projection = db(db.gis_config.id==1).select().first().projection_id
    projection = db(db.gis_projection.id==_projection).select().first().epsg

    # Layers
    baselayers = layers()

    return dict(title=title, module_name=module_name, form=form, projection=projection, openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing)

# Feature Groups
def feature_group_contents():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f="feature_group"))
    feature_group = request.args(0)
    tables = [db.gis_feature_class_to_feature_group, db.gis_location_to_feature_group]
    authorised = shn_has_permission("update", tables[0]) and shn_has_permission("update", tables[1])

    title = db.gis_feature_group[feature_group].name
    feature_group_description = db.gis_feature_group[feature_group].description
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=feature_group_description)
    # Audit
    shn_audit_read(operation="list", resource="feature_group_contents", record=feature_group, representation="html")
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, "feature_group_contents", "html")
        # Display a List_Create page with checkboxes to remove items

        # Feature Classes
        query = (tables[0].feature_group_id == feature_group) & (tables[0].deleted == False)
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

        # Features
        query = (tables[1].feature_group_id == feature_group) & (tables[1].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.location_id
            name = db.gis_location[id].name
            # Metadata is M->1 to Features
            metadata = db(db.media_metadata.location_id==id & db.media_metadata.deleted==False).select()
            if metadata:
                # We just read the description of the 1st one
                description = metadata[0].description
            else:
                description = ""
            id_link = A(id, _href=URL(r=request, f="location", args=[id, "read"]))
            checkbox = INPUT(_type="checkbox", _value="on", _name="feature_" + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align="left"), TD(description, _align="left"), TD(checkbox, _align="center"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH("Name"), TH(T("Description")), TH(T("Remove"))))
        table_footer = TFOOT(TR(TD(INPUT(_id="submit_button", _type="submit", _value=T("Update")))), _colspan=3, _align="right")
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(r=request, f="feature_group_update_items", args=[feature_group])))
        subtitle = T("Contents")

        crud.messages.submit_button=T("Add")
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: feature_group_dupes(form)
        crud.messages.record_created = T("Feature Group Updated")
        form1 = crud.create(tables[0], next=URL(r=request, args=[feature_group]))
        form1[0][0].append(TR(TD(T("Type:")), TD(LABEL(T("Feature Class"), INPUT(_type="radio", _name="fg1", _value="FeatureClass", value="FeatureClass")), LABEL(T("Feature"), INPUT(_type="radio", _name="fg1", _value="Feature", value="FeatureClass")))))
        form2 = crud.create(tables[1], next=URL(r=request, args=[feature_group]))
        form2[0][0].append(TR(TD(T("Type:")), TD(LABEL(T("Feature Class"), INPUT(_type="radio", _name="fg2", _value="FeatureClass", value="Feature")), LABEL(T("Feature"), INPUT(_type="radio", _name="fg2", _value="Feature", value="Feature")))))
        addtitle = T("Add to Feature Group")
        response.view = "%s/feature_group_contents_list_create.html" % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, feature_group=feature_group))
    else:
        # Display a simple List page
        # Feature Classes
        query = (tables[0].feature_group_id == feature_group) & (tables[0].deleted == False)
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

        # Features
        query = (tables[1].feature_group_id == feature_group) & (tables[1].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.location_id
            name = db.gis_location[id].name
            # Metadata is M->1 to Features
            metadata = db(db.media_metadata.location_id==id & db.media_metadata.deleted==False).select()
            if metadata:
                # We just read the description of the 1st one
                description = metadata[0].description
            else:
                description = ""
            id_link = A(id, _href=URL(r=request, f="location", args=[id, "read"]))
            item_list.append(TR(TD(id_link), TD(name, _align="left"), TD(description, _align="left"), _class=theclass, _align="right"))

        table_header = THEAD(TR(TH("ID"), TH("Name"), TH(T("Description"))))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

        add_btn = A(T("Edit Contents"), _href=URL(r=request, c="default", f="user", args="login"), _id="add-btn")
        response.view = "%s/feature_group_contents_list.html" % module
        output.update(dict(items=items, add_btn=add_btn))
    return output

def feature_group_dupes(form):
    "Checks for duplicate Feature/FeatureClass before adding to DB"
    feature_group = form.vars.feature_group
    if "feature_class_id" in form.vars:
        feature_class_id = form.vars.feature_class_id
        table = db.gis_feature_class_to_feature_group
        query = (table.feature_group==feature_group) & (table.feature_class_id==feature_class_id)
    elif "location_id" in form.vars:
        location_id = form.vars.location_id
        table = db.gis_location_to_feature_group
        query = (table.feature_group==feature_group) & (table.location_id==location_id)
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
    tables = [db.gis_feature_class_to_feature_group, db.gis_location_to_feature_group]
    authorised = shn_has_permission("update", tables[0]) and shn_has_permission("update", tables[1])
    if authorised:
        for var in request.vars:
            if "feature_class_id" in var:
                # Delete
                feature_class_id = var[14:]
                query = (tables[0].feature_group==feature_group) & (tables[0].feature_class_id==feature_class_id)
                db(query).delete()
            elif "location_id" in var:
                # Delete
                location_id = var[8:]
                query = (tables[1].feature_group==feature_group) & (tables[1].location_id==location_id)
                db(query).delete()
        # Audit
        shn_audit_update_m2m(resource="feature_group_contents", record=feature_group, representation="html")
        session.flash = T("Feature Group updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f="feature_group_contents", args=[feature_group]))

def map_service_catalogue():
    """Map Service Catalogue.
    Allows selection of which Layers are active."""

    title = T("Map Service Catalogue")
    subtitle = T("List Layers")
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, subtitle=subtitle)

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

def layers():
    "Provide the Enabled Layers"

    from gluon.tools import fetch

    response.warning = ""

    layers = Storage()

    # OpenStreetMap
    layers.openstreetmap = Storage()
    layers_openstreetmap = db(db.gis_layer_openstreetmap.enabled==True).select()
    for layer in layers_openstreetmap:
        for subtype in gis_layer_openstreetmap_subtypes:
            if layer.subtype == subtype:
                layers.openstreetmap["%s" % subtype] = layer.name

    # Google
    layers.google = Storage()
    # Check for Google Key
    try:
        layers.google.key = db(db.gis_apikey.name == "google").select(db.gis_apikey.apikey).first().apikey
        layers_google = db(db.gis_layer_google.enabled==True).select()
        for layer in layers_google:
            for subtype in gis_layer_google_subtypes:
                if layer.subtype == subtype:
                    layers.google["%s" % subtype] = layer.name
                    layers.google.enabled = 1
    except:
        # Redirect to Key entry screen
        session.warning = T("Please enter a Google Key if you wish to use Google Layers")
        redirect(URL(r=request, f=apikey))

    # Yahoo
    layers.yahoo = Storage()
    # Check for Yahoo Key
    try:
        layers.yahoo.key = db(db.gis_apikey.name == "yahoo").select(db.gis_apikey.apikey).first().apikey
        layers_yahoo = db(db.gis_layer_yahoo.enabled==True).select()
        for layer in layers_yahoo:
            for subtype in gis_layer_yahoo_subtypes:
                if layer.subtype == subtype:
                    layers.yahoo["%s" % subtype] = layer.name
                    layers.yahoo.enabled = 1
    except:
        # Redirect to Key entry screen
        session.warning = T("Please enter a Yahoo Key if you wish to use Yahoo Layers")
        redirect(URL(r=request, f=apikey))

    # Bing (Virtual Earth)
    # Broken in GeoExt: http://www.geoext.org/pipermail/users/2009-December/000393.html
    #layers.bing = Storage()
    #layers_bing = db(db.gis_layer_bing.enabled==True).select()
    #for layer in layers_bing:
    #    for subtype in gis_layer_bing_subtypes:
    #        if layer.subtype == subtype:
    #            layers.bing["%s" % subtype] = layer.name

    # GPX
    layers.gpx = Storage()
    layers_gpx = db(db.gis_layer_gpx.enabled==True).select()
    for layer in layers_gpx:
        name = layer.name
        layers.gpx[name] = Storage()
        track = db(db.gis_track.id==layer.track_id).select().first()
        layers.gpx[name].url = track.track
        if layer.marker_id:
            layers.gpx[name].marker = db(db.gis_marker.id == layer.marker_id).select().first().image
        else:
            marker_id = db(db.gis_config.id==1).select().first().marker_id
            layers.gpx[name].marker = db(db.gis_marker.id == marker_id).select().first().image

    cachepath = os.path.join(request.folder, "uploads", "gis_cache")
    if os.access(cachepath, os.W_OK):
        cache = True
    else:
        cache = False

    # GeoRSS
    layers.georss = Storage()
    layers_georss = db(db.gis_layer_georss.enabled==True).select()
    if layers_georss and not cache:
        response.warning += cachepath + " " + str(T("not writable - unable to cache GeoRSS layers!")) + "\n"
    for layer in layers_georss:
        name = layer.name
        url = layer.url
        if cache:
            filename = "gis_cache.file." + name.replace(" ", "_") + ".rss"
            filepath = os.path.join(cachepath, filename)
            try:
                # Download file to cache
                file = fetch(url)
                f = open(filepath, "w")
                f.write(file)
                f.close()
                records = db(db.gis_cache.name == name).select()
                if records:
                    records[0].update(modified_on=response.utcnow)
                else:
                    db.gis_cache.insert(name=name, file=filename)
                url = URL(r=request, c="default", f="download", args=[filename])
            except:
                # URL inaccessible
                if os.access(filepath, os.R_OK):
                    # Use cached version
                    date = db(db.gis_cache.name == name).select().first().modified_on
                    response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                    url = URL(r=request, c="default", f="download", args=[filename])
                else:
                    # No cached version available
                    response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                    # skip layer
                    continue
        else:
            # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
            pass

        # Add to return
        layers.georss[name] = Storage()
        layers.georss[name].url = url
        layers.georss[name].projection = db(db.gis_projection.id == layer.projection_id).select().first().epsg
        if layer.marker_id:
            layers.georss[name].marker = db(db.gis_marker.id == layer.marker_id).select().first().image
        else:
            marker_id = db(db.gis_config.id==1).select().first().marker_id
            layers.georss[name].marker = db(db.gis_marker.id == marker_id).select().first().image

    # KML
    layers.kml = Storage()
    layers_kml = db(db.gis_layer_kml.enabled==True).select()
    if layers_kml and not cache:
        response.warning += cachepath + " " + str(T("not writable - unable to cache KML layers!")) + "\n"

    # Append dynamic feed:
    # /gis/map_viewing_client?kml_feed=<url>&kml_name=<feed_name>
    layers_kml = [Storage(name=l.name, url=l.url) for l in layers_kml]
    if "kml_feed" in request.vars and "kml_name" in request.vars:
        layers_kml.append(Storage(name=request.vars["kml_name"], url=request.vars["kml_feed"]))

    for layer in layers_kml:
        name = layer.name
        url = layer.url
        if cache:
            filename = "gis_cache.file." + name.replace(" ", "_") + ".kml"
            filepath = os.path.join(cachepath, filename)
            # Download file
            file, warning = gis.download_kml(url, S3_PUBLIC_URL)
            # Handle errors
            if "URLError" in warning or "HTTPError" in warning:
                # URL inaccessible
                if os.access(filepath, os.R_OK):
                    # Use cached version
                    date = db(db.gis_cache.name == name).select().first().modified_on
                    response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                    url = URL(r=request, c="default", f="download", args=[filename])
                else:
                    # No cached version available
                    response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                    # skip layer
                    continue
            else:
                # Download was succesful
                if "ParseError" in warning:
                    # @ToDo Parse detail
                    response.warning += str(T("Layer")) + ": " + name + " " + str(T("couldn't be parsed so NetworkLinks not followed.")) + "\n"
                if "GroundOverlay" in warning or "ScreenOverlay" in warning:
                    response.warning += str(T("Layer")) + ": " + name + " " + str(T("includes a GroundOverlay or ScreenOverlay which aren't supported in OpenLayers yet, so it may not work properly.")) + "\n"
                # Write file to cache
                f = open(filepath, "w")
                f.write(file)
                f.close()
                records = db(db.gis_cache.name == name).select()
                if records:
                    records[0].update(modified_on=response.utcnow)
                else:
                    db.gis_cache.insert(name=name, file=filename)
                url = URL(r=request, c="default", f="download", args=[filename])
        else:
            # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
            pass

        # Add to return
        layers.kml[name] = Storage()
        layers.kml[name].url = url

    # WMS
    layers.wms = Storage()
    layers_wms = db(db.gis_layer_wms.enabled==True).select()
    for layer in layers_wms:
        name = layer.name
        layers.wms[name] = Storage()
        layers.wms[name].url = layer.url
        layers.wms[name].base = layer.base
        if layer.map:
            layers.wms[name].map = layer.map
        layers.wms[name].layers = layer.layers
        layers.wms[name].projection = db(db.gis_projection.id == layer.projection_id).select().first().epsg
        layers.wms[name].transparent = layer.transparent
        if layer.format:
            layers.wms[name].format = layer.format

    # TMS
    layers.tms = Storage()
    layers_tms = db(db.gis_layer_tms.enabled==True).select()
    for layer in layers_tms:
        name = layer.name
        layers.tms[name] = Storage()
        layers.tms[name].url = layer.url
        layers.tms[name].layers = layer.layers
        if layer.format:
            layers.tms[name].format = layer.format

    # MGRS - only a single one of these should be defined & it actually appears as a Control not a Layer
    mgrs = db(db.gis_layer_mgrs.enabled==True).select().first()
    if mgrs:
        layers.mgrs = Storage()
        layers.mgrs.name = mgrs.name
        layers.mgrs.url = mgrs.url

    # XYZ
    layers.xyz = Storage()
    layers_xyz = db(db.gis_layer_xyz.enabled==True).select()
    for layer in layers_xyz:
        name = layer.name
        layers.xyz[name] = Storage()
        layers.xyz[name].url = layer.url
        layers.xyz[name].base = layer.base
        layers.xyz[name].sphericalMercator = layer.sphericalMercator
        layers.xyz[name].transitionEffect = layer.transitionEffect
        layers.xyz[name].numZoomLevels = layer.numZoomLevels
        layers.xyz[name].transparent = layer.transparent
        layers.xyz[name].visible = layer.visible
        layers.xyz[name].opacity = layer.opacity

    # JS
    layers.js = Storage()
    layers_js = db(db.gis_layer_js.enabled==True).select()
    for layer in layers_js:
        name = layer.name
        layers.js[name] = Storage()
        layers.js[name].code = layer.code

    return layers

def layers_enable():
    "Enable/Disable Layers"

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
                query_inner = table.id==row.id
                var = "%s_%i" % (type, row.id)
                # Read current state
                if db(query_inner).select().first().enabled:
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

def map_viewing_client():
    """
    Map Viewing Client.
    Main user UI for viewing the Maps with associated Features
    """

    title = T("Map Viewing Client")
    response.title = title

    # Start building the Return with the Framework
    output = dict(title=title, module_name=module_name)

    # Config
    # ToDo return all of these to the view via a single 'config' var
    config = gis.config_read()
    width = config.map_width
    height = config.map_height
    numZoomLevels = config.zoom_levels
    _projection = config.projection_id
    projection = db(db.gis_projection.id==_projection).select().first().epsg
    # Support bookmarks (such as from the control)
    if "lat" in request.vars:
        lat = request.vars.lat
    else:
        lat = config.lat
    if "lon" in request.vars:
        lon = request.vars.lon
    else:
        lon = config.lon
    if "zoom" in request.vars:
        zoom = request.vars.zoom
    else:
        zoom = config.zoom
    epsg = db(db.gis_projection.epsg==projection).select().first()
    units = epsg.units
    maxResolution = epsg.maxResolution
    maxExtent = epsg.maxExtent
    marker_default = config.marker_id
    cluster_distance = config.cluster_distance
    cluster_threshold = config.cluster_threshold
    layout = config.opt_gis_layout

    # Add the Config to the Return
    output.update(dict(width=width, height=height, numZoomLevels=numZoomLevels, projection=projection, lat=lat, lon=lon, zoom=zoom, units=units, maxResolution=maxResolution, maxExtent=maxExtent, cluster_distance=cluster_distance, cluster_threshold=cluster_threshold, layout=layout))

    # Layers
    baselayers = layers()
    # Add the Layers to the Return
    output.update(dict(openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing, tms_layers=baselayers.tms, wms_layers=baselayers.wms, xyz_layers=baselayers.xyz))
    output.update(dict(georss_layers=baselayers.georss, gpx_layers=baselayers.gpx, js_layers=baselayers.js, kml_layers=baselayers.kml))
    # MGRS isn't a Layer, it's a Control, but added here anyway
    output.update(dict(mgrs=baselayers.mgrs))

    # Internal Features
    # ToDo: Replace with self-referring KML feed (easier to maintain 1 source of good popups for both internal & external purposes)
    features = Storage()
    # Features are displayed in a layer per FeatureGroup
    feature_groups = db(db.gis_feature_group.enabled == True).select()
    for feature_group in feature_groups:
        groups = db.gis_feature_group
        locations = db.gis_location
        classes = db.gis_feature_class
        metadata = db.media_metadata
        # Which Features are added to the Group directly?
        # ^^ No longer supported, for simplicity
        #link = db.gis_location_to_feature_group
        # JOINs are efficient for RDBMS but not compatible with GAE
        #features1 = db(link.feature_group_id == feature_group.id).select(groups.ALL, locations.ALL, classes.ALL, left=[groups.on(groups.id == link.feature_group_id), locations.on(locations.id == link.location_id), classes.on(classes.id == locations.feature_class_id)])
        # FIXME?: Extend JOIN for Metadata (sortby, want 1 only), Markers (complex logic), Resource_id (need to find from the results of prev query)
        # Which Features are added to the Group via their FeatureClass?
        link = db.gis_feature_class_to_feature_group
        features2 = db(link.feature_group_id == feature_group.id).select(groups.ALL, locations.ALL, classes.ALL, left=[groups.on(groups.id == link.feature_group_id), classes.on(classes.id == link.feature_class_id), locations.on(locations.feature_class_id == link.feature_class_id)])
        # FIXME?: Extend JOIN for Metadata (sortby, want 1 only), Markers (complex logic), Resource_id (need to find from the results of prev query)
        #features[feature_group.id] = features1 | features2
        features[feature_group.id] = features2
        for feature in features[feature_group.id]:
            try:
                # Deprecated since we'll be using KML to populate Popups with Edit URLs, etc
                feature.module = feature.gis_feature_class.module
                feature.resource = feature.gis_feature_class.resource
                if feature.module and feature.resource:
                    try:
                        feature.resource_id = db(db["%s_%s" % (feature.module, feature.resource)].location_id == feature.gis_location.id).select().first().id
                    except:
                        feature.resource_id = None
                else:
                    feature.resource_id = None

                # Look up the marker to display
                feature.marker = gis.get_marker(feature.gis_location.id)

                try:
                    # Metadata is M->1 to Features
                    # We use the most recent one
                    query = (db.media_metadata.location_id == feature.gis_location.id) & (db.media_metadata.deleted == False)
                    metadata = db(query).select(orderby=~db.media_metadata.event_time).first()

                    # Person .represent is too complex to put into JOIN
                    contact = shn_pr_person_represent(metadata.person_id)

                except:
                    metadata = None
                    contact = None
                feature.metadata = metadata
                feature.contact = contact

                try:
                    # Images are M->1 to Features
                    # We use the most recently uploaded one
                    query = (db.media_image.location_id == feature.gis_location.id) & (db.media_image.deleted == False)
                    image = db(query).select(orderby=~db.media_image.created_on).first().image
                except:
                    image = None
                feature.image = image
            except:
                pass

    # Add the Features to the Return
    #output.update(dict(features=features, features_classes=feature_classes, features_markers=feature_markers, features_metadata=feature_metadata))
    output.update(dict(feature_groups=feature_groups, features=features))

    return output

def display_feature():
    """
    Cut-down version of the Map Viewing Client.
    Used as a .represent for location_id to show just this feature on the map.
    """

    # The Feature
    feature_id = request.args(0)
    feature = db(db.gis_location.id == feature_id).select().first()

    # Check user is authorised to access record
    if not shn_has_permission("read", db.gis_location, feature.id):
        session.error = str(T("No access to this record!"))
        raise HTTP(401, body=s3xrc.xml.json_message(False, 401, session.error))

    # Config
    config = gis.config_read()
    width = config.map_width
    height = config.map_height
    numZoomLevels = config.zoom_levels
    _projection = config.projection_id
    projection = db(db.gis_projection.id==_projection).select().first().epsg
    # Support bookmarks (such as from the control)
    if "lat" in request.vars:
        lat = request.vars.lat
    else:
        lat = feature.lat
    if "lon" in request.vars:
        lon = request.vars.lon
    else:
        lon = feature.lon
    if "zoom" in request.vars:
        zoom = request.vars.zoom
    else:
        zoom = config.zoom
    epsg = db(db.gis_projection.epsg==projection).select().first()
    units = epsg.units
    maxResolution = epsg.maxResolution
    maxExtent = epsg.maxExtent
    marker_default = config.marker_id
    cluster_distance = config.cluster_distance
    cluster_threshold = config.cluster_threshold
    layout = config.opt_gis_layout

    # Add the config to the Return
    output = dict(width=width, height=height, numZoomLevels=numZoomLevels, projection=projection, lat=lat, lon=lon, zoom=zoom, units=units, maxResolution=maxResolution, maxExtent=maxExtent, cluster_distance=cluster_distance, cluster_threshold=cluster_threshold, layout=layout)

    # Feature details
    try:
        feature_class = db(db.gis_feature_class.id == feature.feature_class_id).select().first()
        feature.module = feature_class.module
        feature.resource = feature_class.resource
    except:
        feature_class = None
        feature.module = None
        feature.resource = None
    if feature.module and feature.resource:
        feature.resource_id = db(db["%s_%s" % (feature.module, feature.resource)].location_id == feature.id).select().first().id
    else:
        feature.resource_id = None
    # provide an extra access so no need to duplicate popups code
    feature.gis_location = Storage()
    feature.gis_location = feature
    feature.gis_feature_class = feature_class

    # Look up the marker to display
    feature.marker = gis.get_marker(feature_id)

    try:
        # Metadata is M->1 to Features
        # We use the most recent one
        query = (db.media_metadata.location_id == feature.id) & (db.media_metadata.deleted == False)
        metadata = db(query).select(orderby=~db.media_metadata.event_time).first()

        # Person .represent is too complex to put into JOIN
        contact = shn_pr_person_represent(metadata.person_id)

    except:
        metadata = None
        contact = None
    feature.metadata = metadata
    feature.contact = contact

    try:
        # Images are M->1 to Features
        # We use the most recently uploaded one
        query = (db.media_image.location_id == feature.id) & (db.media_image.deleted == False)
        image = db(query).select(orderby=~db.media_image.created_on).first().image
    except:
        image = None
    feature.image = image

    # Add the feature to the Return
    output.update(dict(feature=feature))

    # Layers
    baselayers = layers()
    # Add the Base Layers to the Return
    output.update(dict(openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing, tms_layers=baselayers.tms, wms_layers=baselayers.wms, xyz_layers=baselayers.xyz))
    # Don't want confusing overlays
    output.update(dict(georss_layers=[], gpx_layers=[], kml_layers=[], js_layers=[], mgrs=[]))

    return output

def display_features():
    """
    Cut-down version of the Map Viewing Client.
    Used as a link from the PHeader.
        URL generated server-side
    Shows all locations matching a query.
    Most recent location is marked using a bigger Marker.
    """

    # Parse the URL, check for implicit resources, extract the primary record
    # http://127.0.0.1:8000/sahana/gis/display_features&module=pr&resource=person&instance=1&jresource=presence
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
    query = (jtable[fkey]==table[pkey]) & (table.id==instance)
    # Filter out deleted
    deleted = (table.deleted == False)
    query = query & deleted
    # Filter out inaccessible
    query2 = db.gis_location.id==jtable.location_id
    accessible = shn_accessible_query("read", db.gis_location)
    query2 = query2 & accessible

    features = db(query).select(db.gis_location.ALL, left = [db.gis_location.on(query2)])

    # Implicit case for instance requires:
    #request = the_web2py_way_to_build_a_request_from_url(button-data)
    #jr = s3xrc.request(request)
    #xml_tree = jr.export_xml()
    #retrieve the location_id's from xml_tree using XPath

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=features)
    lon_max = bounds["max_lon"]
    lon_min = bounds["min_lon"]
    lat_max = bounds["max_lat"]
    lat_min = bounds["min_lat"]

    #bbox = str(lon_min) + "," + str(lat_min) + "," + str(lon_max) + "," + str(lat_max)
    #We now project these client-side, so pass raw info (client-side projection means less server-side dependencies)
    output = dict(lon_max=lon_max, lon_min=lon_min, lat_max=lat_max, lat_min=lat_min)

    # Config
    config = gis.config_read()
    width = config.map_width
    height = config.map_height
    numZoomLevels = config.zoom_levels
    _projection = config.projection_id
    projection = db(db.gis_projection.id==_projection).select().first().epsg
    # Support bookmarks (such as from the control)
    if "lat" in request.vars:
        lat = request.vars.lat
    else:
        lat = None
    if "lon" in request.vars:
        lon = request.vars.lon
    else:
        lon = None
    if "zoom" in request.vars:
        zoom = request.vars.zoom
    else:
        zoom = None
    epsg = db(db.gis_projection.epsg==projection).select().first()
    units = epsg.units
    maxResolution = epsg.maxResolution
    maxExtent = epsg.maxExtent
    marker_default = config.marker_id
    cluster_distance = config.cluster_distance
    cluster_threshold = config.cluster_threshold
    layout = config.opt_gis_layout

    # Add the config to the Return
    output.update(dict(width=width, height=height, numZoomLevels=numZoomLevels, projection=projection, lat=lat, lon=lon, zoom=zoom, units=units, maxResolution=maxResolution, maxExtent=maxExtent, cluster_distance=cluster_distance, cluster_threshold=cluster_threshold, layout=layout))

    # Feature details
    for feature in features:
        try:
            feature_class = db(db.gis_feature_class.id == feature.feature_class_id).select().first()
        except:
            feature_class = None
        feature.module = feature_class.module
        feature.resource = feature_class.resource
        if feature.module and feature.resource:
            try:
                feature.resource_id = db(db["%s_%s" % (feature.module, feature.resource)].location_id == feature.id).select().first().id
            except:
                feature.resource_id = None
        else:
            feature.resource_id = None
        # provide an extra access so no need to duplicate popups code
        feature.gis_location = Storage()
        feature.gis_location = feature
        feature.gis_feature_class = feature_class

        # Look up the marker to display
        feature.marker = gis.get_marker(feature.id)

        try:
            # Metadata is M->1 to Features
            # We use the most recent one
            query = (db.media_metadata.location_id == feature.id) & (db.media_metadata.deleted == False)
            metadata = db(query).select(orderby=~db.media_metadata.event_time)[0]

            # Person .represent is too complex to put into JOIN
            contact = shn_pr_person_represent(metadata.person_id)

        except:
            metadata = None
            contact = None
        feature.metadata = metadata
        feature.contact = contact

        try:
            # Images are M->1 to Features
            # We use the most recently uploaded one
            query = (db.media_image.location_id == feature.id) & (db.media_image.deleted == False)
            image = db(query).select(orderby=~db.media_image.created_on)[0].image
        except:
            image = None
        feature.image = image

    # Add the features to the Return
    output.update(dict(features=features))

    # Layers
    baselayers = layers()
    # Add the Base Layers to the Return
    output.update(dict(openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing, tms_layers=baselayers.tms, wms_layers=baselayers.wms, xyz_layers=baselayers.xyz))
    # Don't want confusing overlays
    output.update(dict(georss_layers=[], gpx_layers=[], kml_layers=[], js_layers=[], mgrs=[]))

    return output

def wms_capabilities():
    " Controller for custom view testing WMS Capabilities Browser "
    google = Storage()
    google.enabled = False
    yahoo = Storage()
    yahoo.enabled = False
    
    return dict(projection=900913, bing=False, google=google, yahoo=yahoo)

def wms_tree():
    " Controller for custom view testing WMSCapabilitiesLoader "
    
    # Dummies for the 'gis/ol_js_loaders.html'
    google = Storage()
    google.enabled = False
    yahoo = Storage()
    yahoo.enabled = False
    
    # Read the Config from Database
    config = gis.config_read()
    # Support bookmarks (such as from the control)
    if "lat" in request.vars:
        config.lat = request.vars.lat
    if "lon" in request.vars:
        config.lon = request.vars.lon
    if "zoom" in request.vars:
        config.zoom = request.vars.zoom
    _projection = config.projection_id
    #config.projection = db(db.gis_projection.id == _projection).select().first().epsg
    config.projection = 4326
    epsg = db(db.gis_projection.epsg == config.projection).select().first()
    config.units = epsg.units
    config.maxResolution = epsg.maxResolution
    config.maxExtent = epsg.maxExtent
    
    return dict(config=config, projection=config.projection, bing=False, google=google, yahoo=yahoo)

def geolocate():
    " Call a Geocoder service "
    if "location" in request.vars:
        location = request.vars.service
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
