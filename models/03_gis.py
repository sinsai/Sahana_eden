# -*- coding: utf-8 -*-

"""
    GIS
"""

module = "gis"

MARKER = T("Marker")

# Expose settings to views
_gis = response.s3.gis
_gis.location_id = False    # Don't display the Location Selector in Views unless the location_id field is present
_gis.map_selector = deployment_settings.get_gis_map_selector()
gis_location_hierarchy = deployment_settings.get_gis_locations_hierarchy()
_gis.location_hierarchy = gis_location_hierarchy
if shn_has_role("MapAdmin"):
    _gis.edit_L0 = True
    _gis.edit_L1 = True
    _gis.edit_L2 = True
    _gis.edit_L3 = True
    _gis.edit_L4 = True
    _gis.edit_L5 = True
else:
    _gis.edit_L0 = deployment_settings.get_gis_edit_l0()
    _gis.edit_L1 = deployment_settings.get_gis_edit_l1()
    _gis.edit_L2 = deployment_settings.get_gis_edit_l2()
    _gis.edit_L3 = deployment_settings.get_gis_edit_l3()
    _gis.edit_L4 = deployment_settings.get_gis_edit_l4()
    _gis.edit_L5 = deployment_settings.get_gis_edit_l5()

# -----------------------------------------------------------------------------
# GIS Markers (Icons)
resourcename = "marker"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        #uuidstamp, # Markers don't sync
                        Field("name", length=128, notnull=True, unique=True),
                        Field("image", "upload", autodelete=True),
                        Field("height", "integer", writable=False), # In Pixels, for display purposes
                        Field("width", "integer", writable=False),  # We could get size client-side using Javascript's Image() class, although this is unreliable!
                        migrate=migrate, *s3_timestamp())

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "static/img/markers")
table.image.represent = lambda filename: (filename and [DIV(IMG(_src=URL(r=request, c="default", f="download", args=filename), _height=40))] or [""])[0]
table.name.label = T("Name")
table.image.label = T("Image")

# Reusable field to include in other table definitions
ADD_MARKER = T("Add") + " " + MARKER
marker_id = S3ReusableField("marker_id", db.gis_marker, sortby="name",
                             requires = IS_NULL_OR(IS_ONE_OF(db, "gis_marker.id", "%(name)s", zero=T("Use default"))),
                             represent = lambda id: (id and [DIV(IMG(_src=URL(r=request, c="default", f="download", args=db(db.gis_marker.id == id).select(db.gis_marker.image, limitby=(0, 1)).first().image), _height=40))] or [""])[0],
                             label = T("Marker"),
                             comment = DIV(A(ADD_MARKER, _class="colorbox", _href=URL(r=request, c="gis", f="marker", args="create", vars=dict(format="popup")), _target="top", _title=ADD_MARKER),
                                       DIV( _class="tooltip", _title=MARKER + "|" + T("Defines the icon used for display of features on interactive map & KML exports. A Marker assigned to an individual Location is set if there is a need to override the Marker assigned to the Feature Class. If neither are defined, then the Default Marker is used."))),
                             ondelete = "RESTRICT"
                            )

def gis_marker_onvalidation(form):

    """
        Record the size of an Image upon Upload
        Don't wish to resize here as we'd like to use full resolution for printed output
    """

    import Image

    im = Image.open(form.vars.image.file)
    (width, height) = im.size

    form.vars.width = width
    form.vars.height = height

    return

s3xrc.model.configure(table,
                      onvalidation=gis_marker_onvalidation)

# -----------------------------------------------------------------------------
# GIS Projections
resourcename = "projection"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("epsg", "integer", notnull=True),
                        Field("maxExtent", length=64, notnull=True),
                        Field("maxResolution", "double", notnull=True),
                        Field("units", notnull=True),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid()))
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.epsg.requires = IS_NOT_EMPTY()
table.maxExtent.requires = IS_NOT_EMPTY()
table.maxResolution.requires = IS_NOT_EMPTY()
table.units.requires = IS_IN_SET(["m", "degrees"], zero=None)
table.name.label = T("Name")
table.epsg.label = "EPSG"
table.maxExtent.label = T("maxExtent")
table.maxResolution.label = T("maxResolution")
table.units.label = T("Units")
# Reusable field to include in other table definitions
projection_id = S3ReusableField("projection_id", db.gis_projection, sortby="name",
                                 requires = IS_NULL_OR(IS_ONE_OF(db, "gis_projection.id", "%(name)s")),
                                 represent = lambda id: (id and [db(db.gis_projection.id == id).select(db.gis_projection.name, limitby=(0, 1)).first().name] or [NONE])[0],
                                 label = T("Projection"),
                                 comment = "",
                                 ondelete = "RESTRICT"
                                )

s3xrc.model.configure(table, deletable=False)

# -----------------------------------------------------------------------------
# GIS Symbology
resourcename = "symbology"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid()))
# Reusable field to include in other table definitions
symbology_id = S3ReusableField("symbology_id", db.gis_symbology, sortby="name",
                                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_symbology.id", "%(name)s")),
                                represent = lambda id: (id and [db(db.gis_symbology.id == id).select(db.gis_symbology.name, limitby=(0, 1)).first().name] or [NONE])[0],
                                label = T("Symbology"),
                                comment = "",
                                ondelete = "RESTRICT"
                               )

# -----------------------------------------------------------------------------
# GIS Config
gis_config_layout_opts = {
    1:T("window"),
    2:T("embedded")
    }
opt_gis_layout = db.Table(None, "opt_gis_layout",
                          Field("opt_gis_layout", "integer",
                                requires = IS_IN_SET(gis_config_layout_opts, zero=None),
                                default = 1,
                                label = T("Layout"),
                                represent = lambda opt: gis_config_layout_opts.get(opt, UNKNOWN_OPT)))
# id=1 = Default settings
resourcename = "config"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("lat", "double"),
                        Field("lon", "double"),
                        Field("zoom", "integer"),
                        projection_id(),
                        symbology_id(),
                        marker_id(),
                        Field("map_height", "integer", notnull=True),
                        Field("map_width", "integer", notnull=True),
                        Field("min_lon", "double", default=-180),
                        Field("min_lat", "double", default=-90),
                        Field("max_lon", "double", default=180),
                        Field("max_lat", "double", default=90),
                        Field("zoom_levels", "integer", default=16, notnull=True),
                        Field("cluster_distance", "integer", default=5, notnull=True),
                        Field("cluster_threshold", "integer", default=2, notnull=True),
                        opt_gis_layout,
                        Field("wmsbrowser_name", default="Web Map Service"),
                        Field("wmsbrowser_url"),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid()))
table.uuid.requires = IS_NOT_IN_DB(db, "gis_config.uuid")
table.pe_id.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.pe_id", shn_pentity_represent))
table.pe_id.readable = table.pe_id.writable = False
table.lat.requires = IS_LAT()
table.lon.requires = IS_LON()
table.zoom.requires = IS_INT_IN_RANGE(0, 19)
table.map_height.requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(160, 1024)]
table.map_width.requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(320, 1280)]
table.min_lat.requires = IS_LAT()
table.max_lat.requires = IS_LAT()
table.min_lon.requires = IS_LON()
table.max_lon.requires = IS_LON()
table.zoom_levels.requires = IS_INT_IN_RANGE(1, 30)
table.cluster_distance.requires = IS_INT_IN_RANGE(1, 30)
table.cluster_threshold.requires = IS_INT_IN_RANGE(1, 10)
table.lat.label = T("Latitude")
table.lon.label = T("Longitude")
table.zoom.label = T("Zoom")
table.marker_id.label = T("Default Marker")
table.map_height.label = T("Map Height")
table.map_width.label = T("Map Width")
table.zoom_levels.label = T("Zoom Levels")
table.cluster_distance.label = T("Cluster Distance")
table.cluster_threshold.label = T("Cluster Threshold")
table.wmsbrowser_name.label = T("WMS Browser Name")
table.wmsbrowser_url.label =  T("WMS Browser URL")
# Defined here since Component
table.lat.comment = DIV( _class="tooltip", _title=T("Latitude") + "|" + T("Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere."))
table.lon.comment = DIV( _class="tooltip", _title=T("Longitude") + "|" + T("Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas."))
table.zoom.comment = DIV( _class="tooltip", _title=T("Zoom") + "|" + T("How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail."))
table.map_height.comment = DIV( _class="tooltip", _title=T("Height") + "|" + T("Default Height of the map window. In Window layout the map maximises to fill the window, so no need to set a large value here."))
table.map_width.comment = DIV( _class="tooltip", _title=T("Width") + "|" + T("Default Width of the map window. In Window layout the map maximises to fill the window, so no need to set a large value here."))
table.wmsbrowser_name.comment = DIV( _class="tooltip", _title=T("WMS Browser Name") + "|" + T("The title of the WMS Browser panel in the Tools panel."))
table.wmsbrowser_url.comment = DIV( _class="tooltip", _title=T("WMS Browser URL") + "|" + T("The URL for the GetCapabilities of a WMS Service whose layers you want accessible via the Map."))
ADD_CONFIG = T("Add Config")
LIST_CONFIGS = T("List Configs")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_CONFIG,
    title_display = T("Config"),
    title_list = T("Configs"),
    title_update = T("Edit Config"),
    title_search = T("Search Configs"),
    subtitle_create = T("Add New Config"),
    subtitle_list = LIST_CONFIGS,
    label_list_button = LIST_CONFIGS,
    label_create_button = ADD_CONFIG,
    label_delete_button = T("Delete Config"),
    msg_record_created = T("Config added"),
    msg_record_modified = T("Config updated"),
    msg_record_deleted = T("Config deleted"),
    msg_list_empty = T("No Configs currently defined")
)

# Configs as component of Persons (Personalised configurations)
s3xrc.model.add_component(module, resourcename,
                          multiple=False,
                          joinby=super_key(db.pr_pentity))

s3xrc.model.configure(table,
                      deletable=False,
                      listadd=False,
                      list_fields = ["lat",
                                     "lon",
                                     "zoom",
                                     "projection_id",
                                     "map_height",
                                     "map_width"])
# -----------------------------------------------------------------------------
# GIS Feature Classes
# These are used in groups (for display/export), for icons & for URLs to edit data
# This is the list of GPS Markers for Garmin devices
gis_gps_marker_opts = [
    "Airport",
    "Amusement Park"
    "Ball Park",
    "Bank",
    "Bar",
    "Beach",
    "Bell",
    "Boat Ramp",
    "Bowling",
    "Bridge",
    "Building",
    "Campground",
    "Car",
    "Car Rental",
    "Car Repair",
    "Cemetery",
    "Church",
    "Circle with X",
    "City (Capitol)",
    "City (Large)",
    "City (Medium)",
    "City (Small)",
    "Civil",
    "Controlled Area",
    "Convenience Store",
    "Crossing",
    "Dam",
    "Danger Area",
    "Department Store",
    "Diver Down Flag 1",
    "Diver Down Flag 2",
    "Drinking Water",
    "Exit",
    "Fast Food",
    "Fishing Area",
    "Fitness Center",
    "Flag",
    "Forest",
    "Gas Station",
    "Geocache",
    "Geocache Found",
    "Ghost Town",
    "Glider Area",
    "Golf Course",
    "Green Diamond",
    "Green Square",
    "Heliport",
    "Horn",
    "Hunting Area",
    "Information",
    "Levee",
    "Light",
    "Live Theater",
    "Lodging",
    "Man Overboard",
    "Marina",
    "Medical Facility",
    "Mile Marker",
    "Military",
    "Mine",
    "Movie Theater",
    "Museum",
    "Navaid, Amber",
    "Navaid, Black",
    "Navaid, Blue",
    "Navaid, Green",
    "Navaid, Green/Red",
    "Navaid, Green/White",
    "Navaid, Orange",
    "Navaid, Red",
    "Navaid, Red/Green",
    "Navaid, Red/White",
    "Navaid, Violet",
    "Navaid, White",
    "Navaid, White/Green",
    "Navaid, White/Red",
    "Oil Field",
    "Parachute Area",
    "Park",
    "Parking Area",
    "Pharmacy",
    "Picnic Area",
    "Pizza",
    "Post Office",
    "Private Field",
    "Radio Beacon",
    "Red Diamond",
    "Red Square",
    "Residence",
    "Restaurant",
    "Restricted Area",
    "Restroom",
    "RV Park",
    "Scales",
    "Scenic Area",
    "School",
    "Seaplane Base",
    "Shipwreck",
    "Shopping Center",
    "Short Tower",
    "Shower",
    "Skiing Area",
    "Skull and Crossbones",
    "Soft Field",
    "Stadium",
    "Summit",
    "Swimming Area",
    "Tall Tower",
    "Telephone",
    "Toll Booth",
    "TracBack Point",
    "Trail Head",
    "Truck Stop",
    "Tunnel",
    "Ultralight Area",
    "Water Hydrant",
    "Waypoint",
    "White Buoy",
    "White Dot",
    "Zoo"
]
resourcename = "feature_class"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("description"),
                        symbology_id(),
                        marker_id(),
                        Field("gps_marker"),
                        Field("resource"),  # Used for Web Service Feeds
                        Field("category"),  # Used for Web Service Feeds & also interactive maps' get_marker()
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid() + s3_deletion_status()))

table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.gps_marker.requires = IS_NULL_OR(IS_IN_SET(gis_gps_marker_opts, zero=T("Use default")))
# Configured in zzz_last.py when all tables are available
#table.resource.requires = IS_NULL_OR(IS_IN_SET(db.tables))
table.name.label = T("Name")
table.gps_marker.label = T("GPS Marker")
table.description.label = T("Description")
table.resource.label = T("Resource")
table.category.label = T("Category")

# Reusable field to include in other table definitions
ADD_FEATURE_CLASS = T("Add Feature Class")
feature_class_id = S3ReusableField("feature_class_id", db.gis_feature_class, sortby="name",
                                    requires = IS_NULL_OR(IS_ONE_OF(db, "gis_feature_class.id", "%(name)s")),
                                    represent = lambda id: (id and [db(db.gis_feature_class.id == id).select(db.gis_feature_class.name, limitby=(0, 1)).first().name] or [NONE])[0],
                                    label = T("Feature Class"),
                                    comment = DIV(A(ADD_FEATURE_CLASS, _class="colorbox", _href=URL(r=request, c="gis", f="feature_class", args="create", vars=dict(format="popup")), _target="top", _title=ADD_FEATURE_CLASS),
                                              DIV( _class="tooltip", _title=T("Feature Class") + "|" + T("Defines the marker used for display & the attributes visible in the popup."))),
                                    ondelete = "RESTRICT"
                                    )

# -----------------------------------------------------------------------------
# GIS Locations
gis_feature_type_opts = {
    1:T("Point"),
    2:T("Line"),
    3:T("Polygon"),
    #4:T("MultiPolygon") This just counts as Polygon as far as we're concerned
    }
gis_source_opts = {
    "gps":T("GPS"),
    "imagery":T("Imagery"),
    "geonames":"Geonames",
    "osm":"OpenStreetMap",
    "wikipedia":"Wikipedia",
    "yahoo":"Yahoo! GeoPlanet",
    }
resourcename = "location"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", notnull=True),    # Primary name
                        Field("name_dummy"),            # Dummy field to provide Widget (real data is stored in the separate table which links back to this one)
                        Field("code"),
                        #feature_class_id(),    # Being removed
                        #marker_id(),           # Being removed
                        Field("level", length=2),
                        Field("parent", "reference gis_location", ondelete = "RESTRICT"),   # This form of hierarchy may not work on all Databases
                        Field("lft", "integer", readable=False, writable=False), # Left will be for MPTT: http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
                        Field("rght", "integer", readable=False, writable=False),# Right currently unused
                        # Street Address (other address fields come from hierarchy)
                        Field("addr_street"),
                        #Field("addr_postcode"),
                        Field("gis_feature_type", "integer", default=1, notnull=True),
                        Field("lat", "double"), # Points or Centroid for Polygons
                        Field("lon", "double"), # Points or Centroid for Polygons
                        Field("wkt", "text"),   # WKT is auto-calculated from lat/lon for Points
                        Field("url"),
                        Field("geonames_id", "integer", unique=True),# Geonames ID (for cross-correlation. OSM cannot take data from Geonames as 'polluted' with unclear sources, so can't use them as UUIDs)
                        Field("osm_id", "integer", unique=True),     # OpenStreetMap ID (for cross-correlation. OSM IDs can change over time, so they also have UUID fields they can store our IDs in)
                        Field("lon_min", "double", writable=False, readable=False), # bounding-box
                        Field("lat_min", "double", writable=False, readable=False), # bounding-box
                        Field("lon_max", "double", writable=False, readable=False), # bounding-box
                        Field("lat_max", "double", writable=False, readable=False), # bounding-box
                        Field("elevation", "integer", writable=False, readable=False),   # m in height above WGS84 ellipsoid (approximately sea-level). not displayed currently
                        Field("ce", "integer", writable=False, readable=False), # Circular 'Error' around Lat/Lon (in m). Needed for CoT.
                        Field("le", "integer", writable=False, readable=False), # Linear 'Error' for the Elevation (in m). Needed for CoT.
                        Field("source", requires=IS_NULL_OR(IS_IN_SET(gis_source_opts))),
                        comments(),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid() + s3_deletion_status()))
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)
table.name.requires = IS_NOT_EMPTY()    # Placenames don't have to be unique

table.name.label = T("Primary Name")
table.name_dummy.label = T("Local Names")
table.name_dummy.comment = DIV(_class="tooltip", _title=T("Local Names") + "|" + T("Names can be added in multiple languages"))

table.level.requires = IS_NULL_OR(IS_IN_SET(gis_location_hierarchy))
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", "%(name)s"))
table.parent.represent = lambda id: (id and [db(db.gis_location.id == id).select(db.gis_location.name, limitby=(0, 1)).first().name] or [NONE])[0]
table.gis_feature_type.requires = IS_IN_SET(gis_feature_type_opts, zero=None)
table.gis_feature_type.represent = lambda opt: gis_feature_type_opts.get(opt, UNKNOWN_OPT)
# Full WKT validation is done in the onvalidation callback
# All we do here is allow longer fields than the default (2 ** 16)
table.wkt.requires = IS_LENGTH(2 ** 24)
table.wkt.represent = lambda wkt: gis.abbreviate_wkt(wkt)
table.lat.requires = IS_NULL_OR(IS_LAT())
table.lon.requires = IS_NULL_OR(IS_LON())
table.url.requires = IS_NULL_OR(IS_URL())
table.osm_id.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999999999))
table.geonames_id.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999999))

table.level.label = T("Level")
table.code.label = T("Code")
table.parent.label = T("Parent")
table.addr_street.label = T("Street Address")
table.gis_feature_type.label = T("Feature Type")
table.lat.label = T("Latitude")
table.lon.label = T("Longitude")
table.wkt.label = "WKT (" + T("Well-Known Text") + ")"
table.url.label = "URL"
table.geonames_id.label = "Geonames ID"
table.osm_id.label = "OpenStreetMap ID"
# We want these visible from forms which reference the Location
CONVERSION_TOOL = T("Conversion Tool")
table.lat.comment = DIV(_class="tooltip",
                        _id="gis_location_lat_tooltip",
                        _title=T("Latitude & Longitude") + "|" + T("You can click on the map to select the Lat/Lon fields. Longitude is West - East (sideways). Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.  This needs to be added in Decimal Degrees."))
table.lon.comment = A(CONVERSION_TOOL,
                      _style="cursor:pointer;",
                      _title=T("You can use the Conversion Tool to convert from either GPS coordinates or Degrees/Minutes/Seconds."),
                      _id="btnConvert")

s3xrc.model.configure(table, listadd=False)
    #list_fields=["id", "name", "level", "parent", "lat", "lon"])

# Reusable field to include in other table definitions
ADD_LOCATION = T("Add Location")
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name
location_id = S3ReusableField("location_id", db.gis_location,
                    sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", repr_select, orderby="gis_location.name", sort=True)),
                    represent = lambda id: shn_gis_location_represent(id),
                    label = T("Location"),
                    comment = DIV(A(ADD_LOCATION,
                                    _class="colorbox",
                                    _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_LOCATION),
                                  DIV(_class="tooltip",
                                      _title=T("Location") + "|" + T("The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                    ondelete = "RESTRICT")

_gis.countries = Storage()
_countries = []
#_gis.provinces = Storage()
if response.s3.countries:
    countries = db(table.code.belongs(response.s3.countries)).select(table.id, table.code, table.name, limitby=(0, len(response.s3.countries)))
    for country in countries:
        _id = country.id
        _gis.countries[country.code] = Storage(name=country.name, id=_id)
        _countries.append(_id)

# -----------------------------------------------------------------------------
# Locations as component of Locations ('Parent')
#s3xrc.model.add_component(module, resourcename,
#                          multiple=False,
#                          joinby=dict(gis_location="parent"))

# -----------------------------------------------------------------------------
# Local Names
resourcename = "location_name"
tablename = module + "_" + resourcename
table = db.define_table(tablename,
                        location_id(),
                        Field("language"),
                        Field("name_l10n"),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid() + s3_deletion_status()))

table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
table.language.requires = IS_IN_SET(s3.l10n_languages)
table.language.represent = lambda opt: s3.l10n_languages.get(opt, UNKNOWN_OPT)
table.language.label = T("Language")
table.name_l10n.label = T("Name")

# Names as component of Locations
s3xrc.model.add_component(module, resourcename,
                          joinby=dict(gis_location="location_id"),
                          multiple=True)

# Multiselect Widget
name_dummy_element = S3MultiSelectWidget(db = db,
                                         link_table_name = tablename,
                                         link_field_name = "location_id")
table = db.gis_location
table.name_dummy.widget = name_dummy_element.widget
table.name_dummy.represent = name_dummy_element.represent

def gis_location_onaccept(form):
    """
        On Accept for GIS Locations (after DB I/O)
    """
    if session.rcvars and hasattr(name_dummy_element, "onaccept"):
        # HTML UI, not XML import
        name_dummy_element.onaccept(db, session.rcvars.gis_location, request)
    else:
        location_id = form.vars.id
        table = db.gis_location_name
        names = db(table.location_id == location_id).select(table.id)
        if names:
            ids = [str(name.id) for name in names]
            #name_dummy = "|%s|" % "|".join(ids)
            name_dummy = "|".join(ids) # That's not how it should be
            table = db.gis_location
            db(table.id==location_id).update(name_dummy=name_dummy)
    # Update the parent Hierarchy
    gis.update_location_tree()

    return

def gis_location_onvalidation(form):

    """
        On Validation for GIS Locations (before DB I/O)
    """

    record_error = T("Sorry, only users with the MapAdmin role are allowed to edit these locations")
    field_error = T("Please select another level")

    # Check Permissions
    # 'MapAdmin' should have all these perms set, no matter what 000_config has
    if form.vars.level == "L0" and not _gis.edit_L0:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif form.vars.level == "L1" and not _gis.edit_L1:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif form.vars.level == "L2" and not _gis.edit_L2:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif form.vars.level == "L3" and not _gis.edit_L3:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif form.vars.level == "L4" and not _gis.edit_L4:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif form.vars.level == "L5" and not _gis.edit_L5:
        response.error = record_error
        form.errors["level"] = field_error
        return
    # Check within permitted bounds for the Instance
    # (avoid incorrect data entry)
    # Points only for now
    if not "gis_feature_type" in form.vars or (form.vars.gis_feature_type == "1"):
        # Skip if no Lat/Lon provided
        if (form.vars.lat != None) and (form.vars.lon != None):
            config = gis.get_config()
            base_error = T("Sorry that location appears to be outside the area supported by this deployment.")
            lat_error =  T("Latitude should be between") + ": " + str(config.min_lat) + " & " + str(config.max_lat)
            lon_error = T("Longitude should be between") + ": " + str(config.min_lon) + " & " + str(config.max_lon)
            if (form.vars.lat > config.max_lat) or (form.vars.lat < config.min_lat):
                response.error = base_error
                form.errors["lat"] = lat_error
                return
            elif (form.vars.lon > config.max_lon) or (form.vars.lon < config.min_lon):
                response.error = base_error
                form.errors["lon"] = lon_error
                return

    # ToDo: Check for probable duplicates
    #
    # ToDo: Check within Bounds of the Parent
    #

    # Add the bounds (& Centroid for Polygons)
    gis.wkt_centroid(form)

    # ToDo: Calculate the bounding box
    # gis.parse_location(form)

    return

s3xrc.model.configure(table,
                      onvalidation=gis_location_onvalidation,
                      onaccept=gis_location_onaccept,
                      list_fields = [
                        "id",
                        "name",
                        "name_dummy",
                        "level",
                        "parent",
                        "gis_feature_type",
                        "lat",
                        "lon"
                      ])

# -----------------------------------------------------------------------------
def s3_gis_location_simple(r, **attr):
    """
        Provide a simple JSON output for a Location
        - easier to parse than S3XRC
        - Don't include the potentially heavy WKT field

        Status: Currently unused
        @ToDo: Extend to a group of locations
    """

    resource = r.resource
    table = resource.table
    id = r.id

    fields = [uuid, level, parent, gis_feature_type, lat, lon, geonames_id, osm_id, comments]
    # @ToDo local_name
    output = db(table.id == id).select(table.uuid).json()

    return output

# Plug into REST controller
s3xrc.model.set_method(module, "location", method="simple", action=s3_gis_location_simple )

# -----------------------------------------------------------------------------
def s3_gis_location_search_simple(r, **attr):

    """ Simple search form for locations """

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
            next = URL(r=request, f="location", args="[id]")

        # Select form
        form = FORM(TABLE(
                TR(T("Name" + ": "),
                   INPUT(_type="text", _name="label", _size="40"),
                   DIV(DIV(_class="tooltip",
                           _title=T("Name") + "|" + T("To search for a location, enter the name. You may use % as wildcard. Press 'Search' without input to list all locations.")))),
                TR("", INPUT(_type="submit", _value=T("Search")))))

        output = dict(form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            if form.vars.label == "":
                form.vars.label = "%"

            # Search
            results = s3xrc.search_simple(table,
                        fields = ["name",
                                  # @ToDo: http://eden.sahanafoundation.org/wiki/S3XRC_Roadmap#Version2.1
                                  #"name_l10n"
                                  ],
                        label = form.vars.label)

            # Get the results
            if results:
                resource.build_query(id=results)
                report = resource.crud(r, method="list", **attr)["items"]
                r.next = None
            else:
                report = T("No matching records found.")

            output.update(items=report)

        # Title and subtitle
        title = T("Search for a Location")
        subtitle = T("Matching Records")

        # Add-button
        label_create_button = shn_get_crud_string("gis_location", "label_create_button")
        add_btn = A(label_create_button, _class="action-btn",
                    _href=URL(r=request, f="location", args="create"))

        output.update(title=title, subtitle=subtitle, add_btn=add_btn)
        response.view = "search_simple.html"
        return output

    else:
        raise HTTP(501, body=s3xrc.ERROR.BAD_FORMAT)

# Plug into REST controller
s3xrc.model.set_method(module, "location", method="search_simple", action=s3_gis_location_search_simple )

# -----------------------------------------------------------------------------
def s3_gis_location_parents(r, **attr):

    """ Return a list of Parents for a Location """

    resource = r.resource
    table = resource.table

    # Check permission
    if not shn_has_permission("read", table):
        r.unauthorised()

    if r.representation == "html":

        # @ToDo
        output = dict()
        #return output
        raise HTTP(501, body=s3xrc.ERROR.BAD_FORMAT)

    elif r.representation == "json":

        if r.id:
            import gluon.contrib.simplejson as json
            # Get the parents for a Location
            parents = gis.get_parents(r.id)
            if parents:
                _parents = {}
                for parent in parents:
                    _parents[parent.level] = parent.id
                output = json.dumps(_parents)
                return output
            else:
                raise HTTP(404, body=s3xrc.ERROR.NO_MATCH)
        else:
            raise HTTP(404, body=s3xrc.ERROR.BAD_RECORD)

    else:
        raise HTTP(501, body=s3xrc.ERROR.BAD_FORMAT)

# Plug into REST controller
s3xrc.model.set_method(module, "location", method="parents", action=s3_gis_location_parents )

# -----------------------------------------------------------------------------
def shn_gis_location_represent(id):
    """ Represent a Location """
    try:
        location = db(db.gis_location.id == id).select(db.gis_location.name, db.gis_location.level, db.gis_location.lat, db.gis_location.lon, db.gis_location.id, limitby=(0, 1)).first()
        if location.level in ["L0", "L1", "L2"]:
            # Countries, Regions shouldn't be represented as Lat/Lon
            text = location.name
        else:
            # Simple
            #represent = location.name
            # Lat/Lon
            lat = location.lat
            lon = location.lon
            if lat and lon:
                if lat > 0:
                    lat_prefix = "N"
                else:
                    lat_prefix = "S"
                if lon > 0:
                    lon_prefix = "E"
                else:
                    lon_prefix = "W"
                text = location.name + " (%s %s %s %s)" % (lat_prefix, lat, lon_prefix, lon)
            else:
                text = location.name
        # Simple
        #represent = text
        # Hyperlink
        #represent = A(text, _href = deployment_settings.get_base_public_url() + URL(r=request, c="gis", f="location", args=[location.id]))
        # Map
        represent = A(text, _href="#", _onclick="s3_viewMap(" + str(id) +");return false")
        # ToDo: Convert to popup? (HTML again!)
    except:
        try:
            # "Invalid" => data consistency wrong
            represent = location.id
        except:
            represent = NONE
    return represent

# -----------------------------------------------------------------------------
# Feature Layers
# Used to select a set of Features for either Display or Export
# (replaces feature_group)
resourcename = "layer_feature"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("module"),
                        Field("resource"),
                        Field("popup_label"),       # Replace with s3.crud_strings[tablename]
                        marker_id(),                # Optional Marker to over-ride the values from the Feature Classes
                        Field("polygons", "boolean", default=False, label=T("Display Polygons?")),
                        Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                        Field("visible", "boolean", default=True, label=T("On by default?")),
                        # ToDo Expose the Graphic options
                        # ToDo Allow defining more complex queries
                        # e.g. L1 for Provinces, L2 for Districts, etc
                        #Field("filter_field"),     # Used to build a simple query
                        #Field("filter_value"),     # Used to build a simple query
                        #Field("query", notnull=True),
                        comments(),
                        migrate=migrate, )

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.resource.label = T("Resource")
# In zzz_last.py
#table.resource.requires = IS_IN_SET(db.tables)
#table.filter_field.label = T("Filter Field")
#table.filter_value.label = T("Filter Value")
#table.query.label = T("Query")

# -----------------------------------------------------------------------------
# GIS Keys - needed for commercial mapping services
resourcename = "apikey" # Can't use 'key' as this has other meanings for dicts!
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", notnull=True),
                        Field("apikey", length=128, notnull=True),
                        Field("description"),
                        migrate=migrate, *s3_timestamp())

# FIXME
# We want a THIS_NOT_IN_DB here: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540/fc129fd476558944?lnk=gst&q=THIS_NOT_IN_DB#fc129fd476558944
table.name.requires = IS_IN_SET(["google", "multimap", "yahoo"], zero=None)
#table.apikey.requires = THIS_NOT_IN_DB(db(table.name == request.vars.name), "gis_apikey.name", request.vars.name, "Service already in use")
table.apikey.requires = IS_NOT_EMPTY()
table.name.label = T("Service")
table.apikey.label = T("Key")

s3xrc.model.configure(table, listadd=False, deletable=False)

# -----------------------------------------------------------------------------
# GPS Tracks (files in GPX format)
resourcename = "track"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename, #timestamp,
                        #uuidstamp, # Tracks don't sync
                        Field("name", length=128, notnull=True, unique=True),
                        Field("description", length=128),
                        Field("track", "upload", autodelete = True),
                        migrate=migrate, *s3_timestamp())


# upload folder needs to be visible to the download() function as well as the upload
table.track.uploadfolder = os.path.join(request.folder, "uploads/tracks")
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.track.requires = IS_UPLOAD_FILENAME(extension="gpx")
table.track.description = T("Description")
table.track.label = T("GPS Track File")
table.track.comment = DIV( _class="tooltip", _title=T("GPS Track") + "|" + T("A file in GPX format taken from a GPS whose timestamps can be correlated with the timestamps on the photos to locate them on the map."))
ADD_TRACK = T("Upload Track")
LIST_TRACKS = T("List Tracks")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_TRACK,
    title_display = T("Track Details"),
    title_list = LIST_TRACKS,
    title_update = T("Edit Track"),
    title_search = T("Search Tracks"),
    subtitle_create = T("Add New Track"),
    subtitle_list = T("Tracks"),
    label_list_button = LIST_TRACKS,
    label_create_button = ADD_TRACK,
    msg_record_created = T("Track uploaded"),
    msg_record_modified = T("Track updated"),
    msg_record_deleted = T("Track deleted"),
    msg_list_empty = T("No Tracks currently available"))
# Reusable field to include in other table definitions
track_id = S3ReusableField("track_id", db.gis_track, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_track.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_track.id == id).select(db.gis_track.name, limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Track"),
                comment = DIV(A(ADD_TRACK, _class="colorbox", _href=URL(r=request, c="gis", f="track", args="create", vars=dict(format="popup")), _target="top", _title=ADD_TRACK),
                          DIV( _class="tooltip", _title=T("GPX Track") + "|" + T("A file downloaded from a GPS containing a series of geographic points in XML format."))),
                ondelete = "RESTRICT"
                )

s3xrc.model.configure(table, deletable=False)

# -----------------------------------------------------------------------------
# GIS Layers
#gis_layer_types = ["bing", "shapefile", "scan"]
gis_layer_types = ["openstreetmap", "georss", "google", "gpx", "js", "kml", "mgrs", "tms", "wfs", "wms", "xyz", "yahoo"]
gis_layer_openstreetmap_subtypes = gis.layer_subtypes("openstreetmap")
gis_layer_google_subtypes = gis.layer_subtypes("google")
gis_layer_yahoo_subtypes = gis.layer_subtypes("yahoo")
gis_layer_bing_subtypes = gis.layer_subtypes("bing")
gis_layer_wms_img_formats = ["image/jpeg", "image/png", "image/bmp", "image/tiff", "image/gif", "image/svg+xml"]
# Base table from which the rest inherit
gis_layer = db.Table(db, "gis_layer", timestamp,
                     #uuidstamp, # Layers like OpenStreetMap, Google, etc shouldn't sync
                     Field("name", notnull=True, label=T("Name"), requires=IS_NOT_EMPTY()),
                     Field("description", label=T("Description")),
                     # System default priority is set in s3gis. User priorities will be set in WMC.
                     #Field("priority", "integer", label=T("Priority")),
                     Field("enabled", "boolean", default=True, label=T("Available in Viewer?"))
                    )
for layertype in gis_layer_types:
    resourcename = "layer_" + layertype
    tablename = "%s_%s" % (module, resourcename)
    # Create Type-specific Layer tables
    if layertype == "openstreetmap":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_openstreetmap_subtypes, zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "georss":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                     projection_id(),
                     marker_id()
                    )
        table = db.define_table(tablename, t, migrate=migrate)
        table.projection_id.requires = IS_ONE_OF(db, "gis_projection.id", "%(name)s")
        table.projection_id.default = 2
    elif layertype == "google":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_google_subtypes, zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "gpx":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     #Field("url", label=T("Location")),
                     track_id(),
                     marker_id()
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "kml":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires=IS_NOT_EMPTY()),
                     Field("title", label=T("Title"), default="name",
                           comment=T("The attribute within the KML which is used for the title of popups.")),
                     Field("body", label=T("Body"), default="description",
                           comment=T("The attribute(s) within the KML which are used for the body of popups. (Use a space between attributes)")),
                     marker_id()
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "js":
        t = db.Table(db, table,
                     gis_layer,
                     Field("code", "text", label=T("Code"),
                           default="var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);")
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "mgrs":
        t = db.Table(db, table,
                     gis_layer,
                     Field("url", label=T("Location"))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "tms":
        t = db.Table(db, table,
                     gis_layer,
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                     Field("layers", label=T("Layers"), requires = IS_NOT_EMPTY()),
                     Field("format", label=T("Format"))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "wfs":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                     Field("version", label=T("Version"), default="1.1.0", requires = IS_IN_SET(["1.0.0", "1.1.0"], zero=None)),
                     Field("featureNS", requires=IS_NOT_EMPTY(), label=T("Feature Namespace"),
                           comment=DIV( _class="tooltip", _title="Feature Namespace" + "|" + T("In GeoServer, this is the Workspace Name. Within the WFS getCapabilities, this is the FeatureType Name part before the colon(:)."))),
                     Field("featureType", requires=IS_NOT_EMPTY(), label=T("Feature Type"),
                           comment=DIV( _class="tooltip", _title=T("Feature Type") + "|" + T("In GeoServer, this is the Layer Name. Within the WFS getCapabilities, this is the FeatureType Name part after the colon(:)."))),
                     projection_id(),
                     #Field("editable", "boolean", default=False, label=T("Editable?")),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
        #table.url.requires = [IS_URL, IS_NOT_EMPTY()]
    elif layertype == "wms":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                     Field("version", label=T("Version"), default="1.1.1", requires = IS_IN_SET(["1.1.1", "1.3.0"], zero=None)),
                     Field("base", "boolean", default=True, label=T("Base Layer?")),
                     Field("transparent", "boolean", default=False, label=T("Transparent?")),
                     Field("map", label=T("Map")),
                     Field("layers", label=T("Layers"), requires = IS_NOT_EMPTY()),
                     Field("format", label=T("Format"), requires = IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats))),
                     Field("buffer", "integer", label=T("Buffer"), default=0, requires=IS_INT_IN_RANGE(0, 10), comment=DIV( _class="tooltip", _title=T("Buffer") + "|" + T("The number of tiles around the visible map to download. Zero means that the 1st page loads faster, higher numbers mean subsequent panning is faster."))),
                     #Field("queryable", "boolean", default=False, label=T("Queryable?")),
                     #Field("legend_url", label=T("legend URL")),
                     #Field("legend_format", label=T("Legend Format"), requires = IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats))),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
        #table.url.requires = [IS_URL, IS_NOT_EMPTY()]
    elif layertype == "xyz":
        t = db.Table(db, table,
                     gis_layer,
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                     Field("base", "boolean", default=True, label=T("Base Layer?")),
                     Field("sphericalMercator", "boolean", default=False, label=T("Spherical Mercator?")),
                     Field("transitionEffect", requires=IS_NULL_OR(IS_IN_SET(["resize"])), label=T("Transition Effect")),
                     Field("numZoomLevels", "integer", label=T("num Zoom Levels")),
                     Field("transparent", "boolean", default=False, label=T("Transparent?")),
                     Field("visible", "boolean", default=True, label=T("Visible?")),
                     Field("opacity", "double", default=0.0, label=T("Transparent?"))
            )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "yahoo":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_yahoo_subtypes, zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "bing":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"), requires = IS_IN_SET(gis_layer_bing_subtypes, zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)

# -----------------------------------------------------------------------------
# GIS Cache
# (Store downloaded KML & GeoRSS feeds)
resourcename = "cache"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                Field("name", length=128, notnull=True, unique=True),
                Field("file", "upload", autodelete = True),
                migrate=migrate, *s3_timestamp())
# upload folder needs to be visible to the download() function as well as the upload
table.file.uploadfolder = os.path.join(request.folder, "uploads/gis_cache")

# -----------------------------------------------------------------------------
# Below tables are not yet implemented

# GIS Styles: SLD
#db.define_table("gis_style", timestamp,
#                Field("name", notnull=True, unique=True))
#db.gis_style.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "gis_style.name")]

# GIS WebMapContexts
# (User preferences)
# GIS Config's Defaults should just be the version for user=0?
#db.define_table("gis_webmapcontext", timestamp,
#                Field("user", db.auth_user))
#db.gis_webmapcontext.user.requires = IS_ONE_OF(db, "auth_user.id", "%(email)s")
