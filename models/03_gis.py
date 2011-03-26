# -*- coding: utf-8 -*-

"""
    GIS
"""

module = "gis"

MARKER = T("Marker")

gis_location_hierarchy = deployment_settings.get_gis_locations_hierarchy()
# Expose settings to views/modules
_gis = response.s3.gis

# This is needed for Location represents & Location Selector
_gis.countries = Storage()
#_gis.provinces = Storage()
# Definition needs to be below the gis_location table definition

# This is needed for onvalidation
# @ToDo: & Location Selector (old currently, new in future?)
if s3_has_role("MapAdmin"):
    _gis.edit_L0 = _gis.edit_L1 = _gis.edit_L2 = _gis.edit_L3 = _gis.edit_L4 = _gis.edit_L5 = _gis.edit_GR = True
else:
    _gis.edit_L0 = deployment_settings.get_gis_edit_l0()
    _gis.edit_L1 = deployment_settings.get_gis_edit_l1()
    _gis.edit_L2 = deployment_settings.get_gis_edit_l2()
    _gis.edit_L3 = deployment_settings.get_gis_edit_l3()
    _gis.edit_L4 = deployment_settings.get_gis_edit_l4()
    _gis.edit_L5 = deployment_settings.get_gis_edit_l5()
    _gis.edit_GR = deployment_settings.get_gis_edit_group()

# -----------------------------------------------------------------------------
# GIS Markers (Icons)
resourcename = "marker"
tablename = "gis_marker"
table = db.define_table(tablename,
                        #uuidstamp, # Markers don't sync
                        Field("name", length=128, notnull=True, unique=True),
                        Field("image", "upload", autodelete=True),
                        Field("height", "integer", writable=False), # In Pixels, for display purposes
                        Field("width", "integer", writable=False),  # We could get size client-side using Javascript's Image() class, although this is unreliable!
                        migrate=migrate, *s3_timestamp())

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "static/img/markers")
table.image.represent = lambda filename: (filename and [DIV(IMG(_src=URL(r=request, c="default", f="download", args=filename), _height=40))] or [""])[0]
table.name.label = T("Name")
table.image.label = T("Image")

# Reusable field to include in other table definitions
ADD_MARKER = T("Add Marker")
marker_id = S3ReusableField("marker_id", db.gis_marker, sortby="name",
                             requires = IS_NULL_OR(IS_ONE_OF(db, "gis_marker.id", "%(name)s", zero=T("Use default"))),
                             represent = lambda id: (id and [DIV(IMG(_src=URL(r=request, c="default", f="download",
                                                                              args=db(db.gis_marker.id == id).select(db.gis_marker.image,
                                                                                                                     limitby=(0, 1)).first().image),
                                                                     _height=40))] or [""])[0],
                             label = T("Marker"),
                             comment = DIV(A(ADD_MARKER,
                                             _class="colorbox",
                                             _href=URL(r=request, c="gis", f="marker", args="create",
                                                       vars=dict(format="popup")),
                                             _target="top",
                                             _title=ADD_MARKER),
                                       DIV( _class="tooltip",
                                            _title="%s|%s" % (MARKER,
                                                              T("Defines the icon used for display of features on interactive map & KML exports. A Marker assigned to an individual Location is set if there is a need to override the Marker assigned to the Feature Class. If neither are defined, then the Default Marker is used.")))),
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
tablename = "gis_projection"
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("epsg", "integer", notnull=True),
                        Field("maxExtent", length=64, notnull=True),
                        Field("maxResolution", "double", notnull=True),
                        Field("units", notnull=True),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid()))
table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
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
                                 represent = lambda id: (id and [db(db.gis_projection.id == id).select(db.gis_projection.name,
                                                                                                       limitby=(0, 1)).first().name] or [NONE])[0],
                                 label = T("Projection"),
                                 comment = "",
                                 ondelete = "RESTRICT"
                                )

s3xrc.model.configure(table, deletable=False)

# -----------------------------------------------------------------------------
# GIS Symbology
resourcename = "symbology"
tablename = "gis_symbology"
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid()))
# Reusable field to include in other table definitions
symbology_id = S3ReusableField("symbology_id", db.gis_symbology, sortby="name",
                                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_symbology.id", "%(name)s")),
                                represent = lambda id: (id and [db(db.gis_symbology.id == id).select(db.gis_symbology.name,
                                                                                                     limitby=(0, 1)).first().name] or [NONE])[0],
                                label = T("Symbology"),
                                comment = "",
                                ondelete = "RESTRICT"
                               )

# -----------------------------------------------------------------------------
# GIS Feature Classes
# These are used in groups (for display/export), for icons & for URLs to edit data
# This is the list of GPS Markers for Garmin devices
gis_gps_marker_opts = gis.gps_symbols

resourcename = "feature_class"
tablename = "gis_feature_class"
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

table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.gps_marker.requires = IS_NULL_OR(IS_IN_SET(gis_gps_marker_opts,
                                                 zero=T("Use default")))
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
                                    represent = lambda id: (id and [db(db.gis_feature_class.id == id).select(db.gis_feature_class.name,
                                                                                                             limitby=(0, 1)).first().name] or [NONE])[0],
                                    label = T("Feature Class"),
                                    comment = DIV(A(ADD_FEATURE_CLASS,
                                                    _class="colorbox",
                                                    _href=URL(r=request, c="gis", f="feature_class", args="create", vars=dict(format="popup")),
                                                    _target="top",
                                                    _title=ADD_FEATURE_CLASS),
                                              DIV( _class="tooltip",
                                                   _title="%s|%s" % (T("Feature Class"),
                                                                     T("Defines the marker used for display & the attributes visible in the popup.")))),
                                    ondelete = "RESTRICT"
                                    )

# -----------------------------------------------------------------------------
# GIS Locations

gis_feature_type_opts = {
    1:T("Point"),
    2:T("LineString"),
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

# This is used as the represent for IS_ONE_OF, and the "format" for the
# gis_location table, which web2py uses to construct (e.g.) selection lists
# for default validators' widgets.
def shn_gis_location_represent_row(location, showlink=True):

    """ Represent a location given its row """

    if location.level:
        # @ToDo: Worth caching these?
        level_name = deployment_settings.get_gis_locations_hierarchy(location.level)
    if location.level == "L0":
        # Countries don't have Parents & shouldn't be represented with Lat/Lon
        text = "%s (%s)" % (location.name, level_name)
    elif location.level == "L1" and _gis.countries and len(_gis.countries) == 1:
        # Regions shouldn't show their Parent if the deployment is only for 1 country
        text = "%s (%s)" % (location.name, level_name)
    elif location.level in ["L1", "L2", "L3"]:
        try:
            # Show the Parent location for larger regions. (For smaller, we show
            # lon, lat -- parent won't fit.)
            parent = db(db.gis_location.id == location.parent).select(db.gis_location.name,
                                                                      cache=(cache.ram, 60),
                                                                      limitby=(0, 1)).first()
            text = "%s (%s, %s)" % (location.name, level_name, parent.name)
        except:
            text = "%s (%s)" % (location.name, level_name)
    elif location.level in ["GR", "XX"]:
        text = "%s (%s)" % (location.name, level_name)
    else:
        # Lat/Lon (Need level name for hierarchy locations, else defeats
        # the purpose of helping users select hierarchy locations as
        # group members.  Even when we have a fancy side-by-side multiple
        # select widget, we'll still need the level for two reasons:
        # First, the widget is going to use it to distinguish hierarchy
        # locations. Second, there are different hierarchy locations with
        # the same name, e.g. Los Angeles (County) and Los Angeles (City).)
        lat = location.lat
        lon = location.lon
        if lat is not None and lon is not None:
            if lat > 0:
                lat_prefix = "N"
            else:
                lat_prefix = "S"
            if lon > 0:
                lon_prefix = "E"
            else:
                lon_prefix = "W"
            if location.level:
                start = "(%s, " % level_name
            else:
                start = "("
            text = "%s %s%s %s %s %s)" % (location.name, start,
                                          lat_prefix, lat,
                                          lon_prefix, lon)
        else:
            if location.level:
                text = "%s (%s)" % (location.name, level_name)
            else:
                text = location.name
            if not location.parent:
                # No way to show on a map
                showlink = False
    if request.raw_args == "read.plain":
       # Map popups don't support iframes (& meaningless anyway)
       showlink = False
    if showlink:
        # ToDo: Convert to popup? (HTML again!)
        represent = A(text, _style="cursor:pointer; cursor:hand",
                            _onclick="s3_viewMap(%i);return false" % location.id)
    else:
        represent = text
    return represent

def shn_gis_location_represent(id, showlink=True):
    """ Represent a location given its id """
    table = db.gis_location
    try:
        location = db(table.id == id).select(table.id,
                                             table.name,
                                             table.level,
                                             table.parent,
                                             table.lat,
                                             table.lon,
                                             cache=(cache.ram, 60),
                                             limitby=(0, 1)).first()
        return shn_gis_location_represent_row(location, showlink)
    except:
        try:
            # "Invalid" => data consistency wrong
            represent = location.id
        except:
            represent = NONE
    return represent

resourcename = "location"
tablename = "gis_location"
table = db.define_table(tablename,
                        Field("name", label = T("Primary Name")),       # Primary name
                        #Field("name_short"),                           # Secondary name
                        Field("name_dummy", label = T("Local Names")),  # Dummy field to provide Widget (real data is stored in the separate table which links back to this one)
                        Field("code", label = T("Code")),               # Christchurch: 'prupi', label=T("Property reference in the council system")
                        #Field("code2"),                                # Christchurch: 'gisratingid', label=T("Polygon reference of the rating unit")
                        Field("level", length=2, label = T("Level")),
                        Field("parent", "reference gis_location",
                              label = T("Parent"),
                              ondelete = "RESTRICT"),                   # This form of hierarchy may not work on all Databases
                        Field("path", length=500,
                              label = T("Path"),
                              readable=False, writable=False),          # Materialised Path
                        Field("members", "list:reference gis_location"),
                        # Street Address (other address fields come from hierarchy)
                        Field("addr_street", "text", label = T("Street Address")),
                        Field("addr_postcode", label = T("Postcode")),
                        Field("gis_feature_type", "integer",
                              default=1, notnull=True,
                              label = T("Feature Type")),
                        Field("lat", "double", label = T("Latitude")),                      # Points or Centroid for Polygons
                        Field("lon", "double", label = T("Longitude")),                     # Points or Centroid for Polygons
                        Field("wkt", "text", label = "WKT (%s)" % T("Well-Known Text")),    # WKT is auto-calculated from lat/lon for Points
                        Field("url", label = "URL"),
                        Field("geonames_id", "integer", unique=True,
                              label = "Geonames ID"),               # Geonames ID (for cross-correlation. OSM cannot take data from Geonames as 'polluted' with unclear sources, so can't use them as UUIDs)
                        Field("osm_id", "integer", unique=True,
                              label = "OpenStreetMap ID"),          # OpenStreetMap ID (for cross-correlation. OSM IDs can change over time, so they also have UUID fields they can store our IDs in)
                        Field("lon_min", "double", writable=False,
                              readable=False), # bounding-box
                        Field("lat_min", "double", writable=False,
                              readable=False), # bounding-box
                        Field("lon_max", "double", writable=False,
                              readable=False), # bounding-box
                        Field("lat_max", "double", writable=False,
                              readable=False), # bounding-box
                        Field("elevation", "double", writable=False,
                              readable=False),   # m in height above WGS84 ellipsoid (approximately sea-level). not displayed currently
                        Field("ce", "integer", writable=False, readable=False), # Circular 'Error' around Lat/Lon (in m). Needed for CoT.
                        Field("le", "integer", writable=False, readable=False), # Linear 'Error' for the Elevation (in m). Needed for CoT.
                        Field("source",
                              requires=IS_NULL_OR(IS_IN_SET(gis_source_opts))),
                        comments(),
                        migrate=migrate,
                        format=shn_gis_location_represent_row,
                        *s3_meta_fields())

table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % table)
#table.name.requires = IS_NOT_EMPTY()    # Placenames don't have to be unique. Waypoints don't need to have a name at all.

table.name_dummy.comment = DIV(_class="tooltip",
                               _title="%s|%s" % (T("Local Names"),
                                                 T("Names can be added in multiple languages")))
table.level.requires = IS_NULL_OR(IS_IN_SET(gis_location_hierarchy))
table.level.represent = lambda level: \
    level and deployment_settings.get_gis_all_levels(level) or NONE
table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id",
                                             shn_gis_location_represent_row,
                                             filterby="level",
                                             filter_opts=["L0", "L1", "L2", "L3", "L4", "L5"],
                                             orderby="gis_location.name"))

table.parent.represent = shn_gis_location_represent
table.gis_feature_type.requires = IS_IN_SET(gis_feature_type_opts, zero=None)
table.gis_feature_type.represent = lambda opt: gis_feature_type_opts.get(opt, UNKNOWN_OPT)
# Full WKT validation is done in the onvalidation callback
# All we do here is allow longer fields than the default (2 ** 16)
table.wkt.requires = IS_LENGTH(2 ** 24)
table.wkt.represent = gis.abbreviate_wkt
table.lat.requires = IS_NULL_OR(IS_LAT())
table.lon.requires = IS_NULL_OR(IS_LON())
table.url.requires = IS_NULL_OR(IS_URL())
table.osm_id.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999999999))
table.geonames_id.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999999999))

# We want these visible from forms which reference the Location
CONVERSION_TOOL = T("Conversion Tool")
table.lat.comment = DIV(_class="tooltip",
                        _id="gis_location_lat_tooltip",
                        _title="%s|%s" % (T("Latitude & Longitude"),
                                          T("Longitude is West - East (sideways). Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.  These need to be added in Decimal Degrees.")))
table.lon.comment = A(CONVERSION_TOOL,
                      _style="cursor:pointer;",
                      _title=T("You can use the Conversion Tool to convert from either GPS coordinates or Degrees/Minutes/Seconds."),
                      _id="gis_location_converter-btn")

table.members.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id",
                                              shn_gis_location_represent_row,
                                              multiple=True))
# Location represent strings can be long, so show group members one per line
# on read-only views.
table.members.represent = lambda id: \
    id and s3_represent_multiref(db.gis_location, id,
                                 represent=lambda mbr_row: \
                                     shn_gis_location_represent_row(mbr_row),
                                 separator=BR()) or NONE
# FYI, this is how one would show plain text rather than links:
#table.members.represent = lambda id: \
#    id and s3_represent_multiref(db.gis_location, id,
#                                 represent=lambda mbr_row: \
#                                     shn_gis_location_represent_row(
#                                         mbr_row, showlink=False),
#                                 separator=", ") or NONE
table.members.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (T("Members"),
                                              T("A location group is a set of locations (often, a set of administrative regions representing a combined area). Member locations are added to a location group here. Location groups may be used to filter what is shown on the map and in search results to only entities covered by locations in the group. A location group can be used to define the extent of an affected area, if it does not fall within one administrative region. Location groups can be used in the Regions menu.")))

s3xrc.model.configure(table, listadd=False)
    #list_fields=["id", "name", "level", "parent", "lat", "lon"])

# CRUD Strings
ADD_LOCATION = T("Add Location")
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

# Reusable field to include in other table definitions
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name
location_id = S3ReusableField("location_id", db.gis_location,
                    sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id",
                                                    repr_select,
                                                    orderby="gis_location.name",
                                                    sort=True)),
                    represent = shn_gis_location_represent,
                    label = T("Location"),
                    widget = S3LocationSelectorWidget(db, gis,
                                                      deployment_settings,
                                                      request,
                                                      response, T),
                    # Alternate simple Autocomplete (e.g. used by pr_person_presence)
                    #widget = S3LocationAutocompleteWidget(request, deployment_settings),
                    ondelete = "RESTRICT")

# This is needed for Location represents & Location Selector
# Definition needs to be below the gis_location table definition
if response.s3.countries:
    countries = db(table.code.belongs(response.s3.countries)).select(table.id,
                                                                     table.code,
                                                                     table.name,
                                                                     limitby=(0, len(response.s3.countries)))
    for country in countries:
        _gis.countries[country.code] = Storage(name=country.name, id=country.id)

# -----------------------------------------------------------------------------
# Locations as component of Locations ('Parent')
#s3xrc.model.add_component(module, resourcename,
#                          multiple=False,
#                          joinby=dict(gis_location="parent"))

# -----------------------------------------------------------------------------
# GIS Config
gis_config_layout_opts = {
    1:T("window"),
    2:T("embedded")
    }
opt_gis_layout = db.Table(db, "opt_gis_layout",
                          Field("opt_gis_layout", "integer",
                                requires = IS_IN_SET(gis_config_layout_opts,
                                                     zero=None),
                                default = 1,
                                label = T("Layout"),
                                represent = lambda opt: gis_config_layout_opts.get(opt,
                                                                                   UNKNOWN_OPT)))
# id=1 = Default settings
resourcename = "config"
tablename = "gis_config"
table = db.define_table(tablename,
                        super_link(db.pr_pentity), # pe_id
                        Field("lat", "double"),
                        Field("lon", "double"),
                        Field("zoom", "integer"),
                        Field("bbox_min_size", "double", default=0.01),
                        Field("bbox_inset", "double", default=0.007),
                        projection_id(),
                        symbology_id(),
                        marker_id(),
                        Field("map_height", "integer", notnull=True),
                        Field("map_width", "integer", notnull=True),
                        Field("min_lon", "double", default=-180),
                        Field("min_lat", "double", default=-90),
                        Field("max_lon", "double", default=180),
                        Field("max_lat", "double", default=90),
                        Field("zoom_levels", "integer", default=22,
                              notnull=True),
                        Field("cluster_distance", "integer", default=5,
                              notnull=True),
                        Field("cluster_threshold", "integer", default=2,
                              notnull=True),
                        opt_gis_layout,
                        Field("wmsbrowser_name", default="Web Map Service"),
                        Field("wmsbrowser_url"),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid()))
table.uuid.requires = IS_NOT_ONE_OF(db, "gis_config.uuid")
table.pe_id.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                            shn_pentity_represent))
table.pe_id.readable = table.pe_id.writable = False
table.lat.requires = IS_LAT()
table.lon.requires = IS_LON()
table.zoom.requires = IS_INT_IN_RANGE(1, 20)
table.bbox_min_size.requires = IS_FLOAT_IN_RANGE(0, 90)
table.bbox_inset.requires = IS_FLOAT_IN_RANGE(0, 90)
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
table.bbox_min_size.label = T("Bounding Box Size")
table.bbox_inset.label = T("Bounding Box Insets")
table.marker_id.label = T("Default Marker")
table.map_height.label = T("Map Height")
table.map_width.label = T("Map Width")
table.zoom_levels.label = T("Zoom Levels")
table.cluster_distance.label = T("Cluster Distance")
table.cluster_threshold.label = T("Cluster Threshold")
table.wmsbrowser_name.label = T("WMS Browser Name")
table.wmsbrowser_url.label =  T("WMS Browser URL")
# Defined here since Component
table.lat.comment = DIV( _class="tooltip",
                         _title="%s|%s" % (T("Latitude"),
                                           T("Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
table.lon.comment = DIV( _class="tooltip",
                         _title="%s|%s" % (T("Longitude"),
                                           T("Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
table.zoom.comment = DIV( _class="tooltip",
                          _title="%s|%s" % (T("Zoom"),
                                            T("How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))
table.bbox_min_size.comment = DIV( _class="tooltip",
                                   _title="%s|%s" % (T("Minimum Bounding Box"),
                                                     T("When a map is displayed that focuses on a collection of points, the map is zoomed to show just the region bounding the points. This value gives a minimum width and height in degrees for the region shown. Without this, a map showing a single point would not show any extent around that point. After the map is displayed, it can be zoomed as desired.")))
table.bbox_inset.comment = DIV( _class="tooltip",
                                _title="%s|%s" % (T("Bounding Box Insets"),
                                                  T("When a map is displayed that focuses on a collection of points, the map is zoomed to show just the region bounding the points. This value adds a small mount of distance outside the points. Without this, the outermost points would be on the bounding box, and might not be visible.")))
table.map_height.comment = DIV( _class="tooltip",
                                _title="%s|%s" % (T("Height"),
                                                  T("Default Height of the map window. In Window layout the map maximises to fill the window, so no need to set a large value here.")))
table.map_width.comment = DIV( _class="tooltip",
                               _title="%s|%s" % (T("Width"),
                                                 T("Default Width of the map window. In Window layout the map maximises to fill the window, so no need to set a large value here.")))
table.wmsbrowser_name.comment = DIV( _class="tooltip",
                                     _title="%s|%s" % (T("WMS Browser Name"),
                                                       T("The title of the WMS Browser panel in the Tools panel.")))
table.wmsbrowser_url.comment = DIV( _class="tooltip",
                                    _title="%s|%s" % (T("WMS Browser URL"),
                                                      T("The URL for the GetCapabilities of a WMS Service whose layers you want accessible via the Map.")))
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
# Local Names
resourcename = "location_name"
tablename = "gis_location_name"
table = db.define_table(tablename,
                        location_id(),
                        Field("language"),
                        Field("name_l10n"),
                        migrate=migrate,
                        *(s3_timestamp() + s3_uid() + s3_deletion_status()))

table.uuid.requires = IS_NOT_ONE_OF(db, '%s.uuid' % tablename)
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
            db(table.id == location_id).update(name_dummy=name_dummy)
    # Update the Path
    gis.update_location_tree(form.vars.id, form.vars.parent)
    return

def gis_location_onvalidation(form):

    """
        On Validation for GIS Locations (before DB I/O)
    """

    # If you need more info from the old location record, add it here.
    # Check if this has already been called and use the existing info.
    def get_location_info():
        if "id" in request:
            query = (db.gis_location.id == request.id)
            return db(query).select(db.gis_location.level,
                                    limitby=(0, 1)).first()
        else:
            return None

    record_error = T("Sorry, only users with the MapAdmin role are allowed to edit these locations")
    field_error = T("Please select another level")

    # Shortcuts
    level = "level" in form.vars and form.vars.level
    parent = "parent" in form.vars and form.vars.parent
    lat = "lat" in form.vars and form.vars.lat
    lon = "lon" in form.vars and form.vars.lon
    members = "members" in form.vars and form.vars.members

    # Allowed changes for location groups: Once it's a group, it stays a
    # group, and existing non-group locations can't be converted to groups.
    # For a new location, set the level to "GR" if members are present.
    # If it's already a group, don't allow clearing the members or altering
    # the level. Don't allow adding members to an existing location that's
    # not a group. Note: We can't rely on checking form.vars.level to tell
    # if an existing location was a group, because it might not be available
    # in either form.vars or request.vars -- for an interactive form, that
    # field was set to not writable, so it's just plain text in the page.
    # Note also that many of the errors "available" here are not accessible
    # via the interactive form. Note further that permission to *edit* a
    # group does not give one permission to *mess up* a group, so the above
    # restrictions apply to MapAdmins too.
    if "id" in request.vars:
        # Existing location? Check attempts to manipulate group or members.
        # Note we cannot rely on merely checking form.vars.level -- it might
        # not be present, or this request might be attempting to change the
        # level to group.
        # Is this a location group?
        # Use the breadcrumb set in prep if available to avoid a db read.
        if "location_is_group" in response.s3:
            location_is_group = response.s3.location_is_group
        else:
            old_location = get_location_info()
            location_is_group = location.level == "GR"
        if location_is_group:
            if not _gis.edit_GR:
                response.error = record_error
                return
            # Make sure no-one takes away all members.
            if "members" in form.vars and not form.vars.members:
                form.errors["members"] = T("A location group must have at least one member.")
                return
        else:
            # Don't allow changing non-group to group.
            if members:
                form.errors["members"] = T("Location cannot be converted into a group.")
                return
            if level == "GR":
                form.errors["level"] = T("Location cannot be converted into a group.")
                return
    else:
        # New location -- if the location has members, and if permitted to
        # make a group, set "group" level. Don't allow also setting a parent.
        if members:
            if _gis.edit_GR:
                if "parent" in form.vars and form.vars.parent:
                    form.errors["parent"] = T("Location group cannot have a parent.")
                    return
                form.vars.level = "GR"
            else:
                response.error = T("Sorry, only users with the MapAdmin role are allowed to create location groups.")
                return

    # Check Permissions
    # 'MapAdmin' has all these perms set, no matter what 000_config has
    if level == "L0" and not _gis.edit_L0:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif level == "L1" and not _gis.edit_L1:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif level == "L2" and not _gis.edit_L2:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif level == "L3" and not _gis.edit_L3:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif level == "L4" and not _gis.edit_L4:
        response.error = record_error
        form.errors["level"] = field_error
        return
    elif level == "L5" and not _gis.edit_L5:
        response.error = record_error
        form.errors["level"] = field_error
        return

    if parent:
        query = (db.gis_location.id == parent)
        _parent = db(query).select(db.gis_location.level,
                                   db.gis_location.gis_feature_type,
                                   db.gis_location.lat_min,
                                   db.gis_location.lon_min,
                                   db.gis_location.lat_max,
                                   db.gis_location.lon_max,
                                   #db.gis_location.level,
                                   limitby=(0, 1),
                                   cache=(cache.ram, 3600)).first()

    # Don't allow a group as parent (that way lies madness!).
    # (Check not needed here -- enforced in requires validator.)
    #if _parent and _parent.level == "GR":
    #    form.errors["parent"] = T("Location group cannot be a parent.")
    #    return

    # Check Parents are in sane order
    if level and parent and _parent:
        # Check that parent is of a higher level (http://eden.sahanafoundation.org/ticket/450)
        if level[1:] < _parent.level[1:]:
            response.error = "%s: %s" % (T("Parent level should be higher than this record's level. Parent level is"),
                                         gis_location_hierarchy[_parent.level])
            form.errors["level"] = T("Level is higher than parent's")
            return
    strict = deployment_settings.get_gis_strict_hierarchy()
    if strict:
        # Check Parents are in exact order
        if level == "L1" and len(_gis.countries) == 1:
            # Hardcode the Parent
            parent = _gis.countries.popitem()[1].id
        elif level == "L0":
            # Parent is impossible
            parent = ""
        elif not parent:
            # Parent is mandatory
            response.error = "%s: %s" % (T("Parent needs to be set for locations of level"),
                                         gis_location_hierarchy[level])
            form.errors["parent"] = T("Parent needs to be set")
            return
        elif not level:
            # Parents needs to be of level max_hierarchy
            max_hierarchy = deployment_settings.get_gis_max_hierarchy()
            if _parent.level != max_hierarchy:
                response.error = "%s: %s" % (T("Specific locations need to have a parent of level"),
                                             gis_location_hierarchy[max_hierarchy])
                form.errors["parent"] = T("Parent needs to be of the correct level")
                return
        else:
            # Check that parent is of exactly next higher order
            if (int(level[1:]) - 1) != int(_parent.level[1:]):
                response.error = "%s: %s" % (T("Locations of this level need to have a parent of level"),
                                             gis_location_hierarchy["L%i" % (int(level[1:]) - 1)])
                form.errors["parent"] = T("Parent needs to be of the correct level")
                return

    # Check within permitted bounds
    # (avoid incorrect data entry)
    # Points only for now
    if not "gis_feature_type" in form.vars or (form.vars.gis_feature_type == "1"):
        # Skip if no Lat/Lon provided
        if (lat != None) and (lon != None):
            if parent and _parent.gis_feature_type == 3:
                # Check within Bounds of the Parent
                # Rough (Bounding Box)
                min_lat = _parent.lat_min
                min_lon = _parent.lon_min
                max_lat = _parent.lat_max
                max_lon = _parent.lon_max
                base_error = T("Sorry that location appears to be outside the area of the Parent.")
                lat_error =  "%s: %s & %s" % (T("Latitude should be between"),
                                              str(min_lat), str(max_lat))
                lon_error = "%s: %s & %s" % (T("Longitude should be between"),
                                             str(min_lon), str(max_lon))
                if (lat > max_lat) or (lat < min_lat):
                    response.error = base_error
                    form.errors["lat"] = lat_error
                    return
                elif (lon > max_lon) or (lon < min_lon):
                    response.error = base_error
                    form.errors["lon"] = lon_error
                    return

                # @ToDo: Precise (GIS function)
                # (if using PostGIS then don't do a separate BBOX check as this is done within the query)

            else:
                # Check bounds for the Instance
                config = gis.get_config()
                min_lat = config.min_lat
                min_lon = config.min_lon
                max_lat = config.max_lat
                max_lon = config.max_lon
                base_error = T("Sorry that location appears to be outside the area supported by this deployment.")
                lat_error =  "%s: %s & %s" % (T("Latitude should be between"),
                                              str(min_lat), str(max_lat))
                lon_error = "%s: %s & %s" % (T("Longitude should be between"),
                                             str(min_lon), str(max_lon))
                if (lat > max_lat) or (lat < min_lat):
                    response.error = base_error
                    form.errors["lat"] = lat_error
                    return
                elif (lon > max_lon) or (lon < min_lon):
                    response.error = base_error
                    form.errors["lon"] = lon_error
                    return

    # ToDo: Check for probable duplicates
    # http://eden.sahanafoundation.org/ticket/481
    # name soundex
    # parent
    # radius
    # response.warning = T("This appears to be a duplicate of ") + xxx (with appropriate representation including hyperlink to view full details - launch de-duplication UI?)
    # form.errors["name"] = T("Duplicate?")
    # Set flag to say that this has been confirmed as not a duplicate

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
s3xrc.model.set_method(module, "location", method="simple",
                       action=s3_gis_location_simple)

gis_location_search = s3base.S3LocationSearch(
    name="location_search_simple",
    label=T("Name"),
    comment=T("To search for a location, enter the name. You may use % as wildcard. Press 'Search' without input to list all locations."),
    field=["name"])

# Set as default search method
s3xrc.model.configure(db.gis_location, search_method=gis_location_search)

# -----------------------------------------------------------------------------
def s3_gis_location_parents(r, **attr):

    """ Return a list of Parents for a Location """

    resource = r.resource
    table = resource.table

    # Check permission
    if not s3_has_permission("read", table):
        r.unauthorised()

    if r.representation == "html":

        # @ToDo
        output = dict()
        #return output
        raise HTTP(501, body=s3xrc.ERROR.BAD_FORMAT)

    elif r.representation == "json":

        if r.id:
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
s3xrc.model.set_method(module, "location", method="parents",
                       action=s3_gis_location_parents)

# -----------------------------------------------------------------------------
# Feature Layers
# Used to select a set of Features for either Display or Export
# (replaces feature_group)
resourcename = "layer_feature"
tablename = "gis_layer_feature"
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("module"),
                        Field("resource"),
                        #Field("type", "integer"),  # @ToDo: Optional filtering by type (e.g. for Warehouses)
                        Field("popup_label"),       # @ToDo: Replace with s3.crud_strings[tablename]
                        marker_id(),                # Optional Marker to over-ride the values from the Feature Classes
                        Field("polygons", "boolean", default=False,
                              label=T("Display Polygons?")),
                        Field("enabled", "boolean", default=True,
                              label=T("Available in Viewer?")),
                        Field("visible", "boolean", default=True,
                              label=T("On by default?")),
                        Field("opacity", "double", default=1.0,
                              requires=IS_FLOAT_IN_RANGE(0, 1),
                              label=T("Opacity (1 for opaque, 0 for fully-transparent)")),
                        # @ToDo Expose the Graphic options
                        # e.g. L1 for Provinces, L2 for Districts, etc
                        # e.g. office type 5 for Warehouses
                        Field("filter_field"),     # Used to build a simple query
                        Field("filter_value"),     # Used to build a simple query
                        # @ToDo Allow defining more complex queries
                        #Field("query", notnull=True),
                        role_required(),       # Single Role
                        #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                        comments(),
                        migrate=migrate,
                        *s3_timestamp())

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.resource.label = T("Resource")
# In Controller (to ensure all tables visible)
#table.resource.requires = IS_IN_SET(db.tables)
table.filter_field.label = T("Filter Field")
table.filter_value.label = T("Filter Value")
table.filter_value.comment = DIV(_class="tooltip",
                                 _title="%s|%s /" % (T("Filter Value"),
                                                     T("If you want several values, then separate with")))
#table.query.label = T("Query")

# -----------------------------------------------------------------------------
# GIS Keys - needed for commercial mapping services
resourcename = "apikey" # Can't use 'key' as this has other meanings for dicts!
tablename = "gis_apikey"
table = db.define_table(tablename,
                        Field("name", notnull=True),
                        Field("apikey", length=128, notnull=True),
                        Field("description"),
                        migrate=migrate, *s3_timestamp())

# FIXME
# We want a THIS_NOT_ONE_OF here: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540/fc129fd476558944?lnk=gst&q=THIS_NOT_ONE_OF#fc129fd476558944
table.name.requires = IS_IN_SET(["google", "bing", "multimap", "yahoo"],
                                zero=None)
#table.apikey.requires = THIS_NOT_ONE_OF(db(table.name == request.vars.name), "gis_apikey.name", request.vars.name, "Service already in use")
table.apikey.requires = IS_NOT_EMPTY()
table.name.label = T("Service")
table.apikey.label = T("Key")

s3xrc.model.configure(table, listadd=False, deletable=False)

# -----------------------------------------------------------------------------
# GPS Waypoints
resourcename = "waypoint"
tablename = "gis_waypoint"
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True),
                        Field("description", length=128),
                        Field("category", length=128),
                        location_id(),
                        migrate=migrate,
                        *s3_meta_fields())

table.name.label = T("Name")
table.description.label = T("Description")
table.category.label = T("Category")

# -----------------------------------------------------------------------------
# GPS Tracks (stored as 1 record per point)
resourcename = "trackpoint"
tablename = "gis_trackpoint"
table = db.define_table(tablename,
                        location_id(),
                        #track_id(),        # link to the uploaded file?
                        migrate=migrate,
                        *s3_meta_fields())

# -----------------------------------------------------------------------------
# GPS Tracks (files in GPX format)
resourcename = "track"
tablename = "gis_track"
table = db.define_table(tablename,
                        #uuidstamp, # Tracks don't sync
                        Field("name", length=128, notnull=True, unique=True),
                        Field("description", length=128),
                        Field("track", "upload", autodelete = True),
                        migrate=migrate,
                        *s3_timestamp())


# upload folder needs to be visible to the download() function as well as the upload
table.track.uploadfolder = os.path.join(request.folder, "uploads/tracks")
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.track.requires = IS_UPLOAD_FILENAME(extension="gpx")
table.track.description = T("Description")
table.track.label = T("GPS Track File")
table.track.comment = DIV( _class="tooltip",
                           _title="%s|%s" % (T("GPS Track"),
                                             T("A file in GPX format taken from a GPS whose timestamps can be correlated with the timestamps on the photos to locate them on the map.")))
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
                represent = lambda id: (id and [db(db.gis_track.id == id).select(db.gis_track.name,
                                                                                 limitby=(0, 1)).first().name] or [NONE])[0],
                label = T("Track"),
                comment = DIV(A(ADD_TRACK,
                                _class="colorbox",
                                _href=URL(r=request, c="gis", f="track",
                                          args="create",
                                          vars=dict(format="popup")),
                                _target="top",
                                _title=ADD_TRACK),
                          DIV( _class="tooltip",
                               _title="%s|%s" % (T("GPX Track"),
                                                 T("A file downloaded from a GPS containing a series of geographic points in XML format.")))),
                ondelete = "RESTRICT"
                )

s3xrc.model.configure(table, deletable=False)

# -----------------------------------------------------------------------------
# GIS Layers
#gis_layer_types = ["shapefile", "scan"]
gis_layer_types = ["bing", "coordinate", "openstreetmap", "geojson", "georss", "google", "gpx", "js", "kml", "mgrs", "tms", "wfs", "wms", "xyz", "yahoo"]
gis_layer_google_subtypes = gis.layer_subtypes("google")
gis_layer_yahoo_subtypes = gis.layer_subtypes("yahoo")
gis_layer_bing_subtypes = gis.layer_subtypes("bing")
gis_layer_wms_img_formats = ["image/jpeg", "image/png", "image/bmp", "image/tiff", "image/gif", "image/svg+xml"]
# Base table from which the rest inherit
gis_layer = db.Table(db, "gis_layer",
                     #uuidstamp, # Layers like OpenStreetMap, Google, etc shouldn't sync
                     Field("name", notnull=True, label=T("Name"), requires=IS_NOT_EMPTY()),
                     Field("description", label=T("Description")),
                     # System default priority is set in s3gis. User priorities will be set in WMC.
                     #Field("priority", "integer", label=T("Priority")),
                     Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                     role_required(),       # Single Role
                     #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     migrate=migrate, *s3_timestamp())
for layertype in gis_layer_types:
    resourcename = "layer_%s" % layertype
    tablename = "gis_%s" % resourcename
    # Create Type-specific Layer tables
    if layertype == "coordinate":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False,
                           label=T("On by default?")),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "openstreetmap":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=True,
                           label=T("On by default? (only applicable to Overlays)")),
                     Field("url1", label=T("Location"), requires=IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("The URL to access the service.")))),
                     Field("url2", label=T("Secondary Server (Optional)")),
                     Field("url3", label=T("Tertiary Server (Optional)")),
                     Field("base", "boolean", default=True,
                           label=T("Base Layer?")),
                     Field("attribution", label=T("Attribution")),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "geojson":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False,
                           label=T("On by default?")),
                     Field("url", label=T("Location"), requires=IS_NOT_EMPTY()),
                     projection_id(default=2,
                                   requires = IS_ONE_OF(db, "gis_projection.id",
                                                        "%(name)s")),
                     marker_id()
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "georss":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False,
                           label=T("On by default?")),
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                     projection_id(default=2,
                                   requires = IS_ONE_OF(db, "gis_projection.id",
                                                        "%(name)s")),
                     marker_id()
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "google":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"),
                           requires=IS_IN_SET(gis_layer_google_subtypes,
                                              zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "gpx":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False,
                           label=T("On by default?")),
                     #Field("url", label=T("Location"),
                           #comment=DIV( _class="tooltip", _title="%s|%s" % (T("Location", T("The URL to access the service.")))),
                     track_id(), # @ToDo remove this layer of complexity: Inlcude the upload field within the Layer
                     Field("waypoints", "boolean", default=True,
                           label=T("Display Waypoints?")),
                     Field("tracks", "boolean", default=True,
                           label=T("Display Tracks?")),
                     Field("routes", "boolean", default=False,
                           label=T("Display Routes?")),
                     marker_id()
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "kml":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires=IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("The URL to access the service.")))),
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
                     Field("url", label=T("Location"),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("The URL to access the service.")))),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "tms":
        t = db.Table(db, table,
                     gis_layer,
                     Field("url", label=T("Location"), requires=IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("The URL to access the service.")))),
                     Field("layers", label=T("Layers"),
                           requires=IS_NOT_EMPTY()),
                     Field("img_format", label=T("Format"))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "wfs":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("Mandatory. The URL to access the service.")))),
                     Field("version", label=T("Version"), default="1.1.0",
                           requires=IS_IN_SET(["1.0.0", "1.1.0"], zero=None)),
                     Field("featureNS", label=T("Feature Namespace"),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % ("Feature Namespace",
                                                          T("Optional. In GeoServer, this is the Workspace Namespace URI. Within the WFS getCapabilities, this is the FeatureType Name part before the colon(:).")))),
                     Field("featureType", label=T("Feature Type"),
                           requires = IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Feature Type"),
                                                          T("Mandatory. In GeoServer, this is the Layer Name. Within the WFS getCapabilities, this is the FeatureType Name part after the colon(:).")))),
                     Field("geometryName", label=T("Geometry Name"), default = "the_geom",
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Geometry Name"),
                                                          T("Optional. The name of the geometry column. In PostGIS this defaults to 'the_geom'.")))),
                     projection_id(),
                     #Field("editable", "boolean", default=False, label=T("Editable?")),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "wms":
        t = db.Table(db, table,
                     gis_layer,
                     Field("visible", "boolean", default=False, label=T("On by default?")),
                     Field("url", label=T("Location"), requires = IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("The URL to access the service.")))),
                     Field("version", label=T("Version"), default="1.1.1",
                           requires=IS_IN_SET(["1.1.1", "1.3.0"], zero=None)),
                     Field("base", "boolean", default=False,
                           label=T("Base Layer?")),
                     Field("transparent", "boolean", default=True,
                           label=T("Transparent?")),
                     Field("opacity", "double", default=1.0,
                           requires=IS_FLOAT_IN_RANGE(0, 1),
                           label=T("Opacity (1 for opaque, 0 for fully-transparent)")),
                     Field("map", label=T("Map")),
                     Field("layers", label=T("Layers"),
                           requires=IS_NOT_EMPTY()),
                     Field("img_format", label=T("Format"),
                           requires=IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats)),
                           default="img/png"
                           ),
                     Field("buffer", "integer", label=T("Buffer"), default=0,
                           requires=IS_INT_IN_RANGE(0, 10),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Buffer"),
                                                          T("The number of tiles around the visible map to download. Zero means that the 1st page loads faster, higher numbers mean subsequent panning is faster.")))),
                     #Field("queryable", "boolean", default=False, label=T("Queryable?")),
                     #Field("legend_url", label=T("legend URL")),
                     #Field("legend_format", label=T("Legend Format"), requires = IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats))),
                    )
        table = db.define_table(tablename, t, migrate=migrate)
        #table.url.requires = [IS_URL, IS_NOT_EMPTY()]
    elif layertype == "xyz":
        t = db.Table(db, table,
                     gis_layer,
                     Field("url", label=T("Location"), requires=IS_NOT_EMPTY(),
                           comment=DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Location"),
                                                          T("The URL to access the service.")))),
                     Field("base", "boolean", default=True,
                           label=T("Base Layer?")),
                     Field("sphericalMercator", "boolean", default=False,
                           label=T("Spherical Mercator?")),
                     Field("transitionEffect",
                           requires=IS_NULL_OR(IS_IN_SET(["resize"])),
                           label=T("Transition Effect")),
                     Field("numZoomLevels", "integer", label=T("num Zoom Levels")),
                     Field("transparent", "boolean", default=False,
                           label=T("Transparent?")),
                     Field("visible", "boolean", default=True, label=T("Visible?")),
                     Field("opacity", "double", default=0.0,
                           label=T("Transparent?"))
            )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "yahoo":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"),
                           requires = IS_IN_SET(gis_layer_yahoo_subtypes,
                                                zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "bing":
        t = db.Table(db, table,
                     gis_layer,
                     Field("subtype", label=T("Sub-type"),
                           requires = IS_IN_SET(gis_layer_bing_subtypes,
                                                zero=None))
                    )
        table = db.define_table(tablename, t, migrate=migrate)

# -----------------------------------------------------------------------------
# GIS Cache
# (Store downloaded KML & GeoRSS feeds)
resourcename = "cache"
tablename = "gis_cache"
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("file", "upload", autodelete = True),
                        migrate=migrate, *s3_timestamp())
# upload folder needs to be visible to the download() function as well as the upload
table.file.uploadfolder = os.path.join(request.folder, "uploads/gis_cache")

# -----------------------------------------------------------------------------
# GIS Web Map Contexts
# (Saved Map definitions)
# GIS Config's Defaults should just be the version for id=1?

# @ToDo Unify WMC Layers with the rest of the Layers system
resourcename = "wmc_layer"
tablename = "gis_wmc_layer"
table = db.define_table(tablename,
                        Field("source"),
                        Field("name"),
                        Field("title"),
                        Field("visibility", "boolean"),
                        Field("group_"),
                        Field("fixed", "boolean"),
                        Field("opacity", "double"),
                        Field("type_"),
                        # Handle this as a special case for 'None' layer ('ol' source)
                        #"args":["None",{"visibility":false}]
                        Field("img_format"),
                        Field("styles"),
                        Field("transparent", "boolean"),
                        migrate=migrate, *s3_timestamp())
# We don't need dropdowns as these aren't currently edited using Web2Py forms
# @ToDo Handle Added WMS servers (& KML/GeoRSS once GeoExplorer supports them!)
#table.source.requires = IS_IN_SET(["ol", "osm", "google", "local", "sahana"])
#table.name.requires = IS_IN_SET(["mapnik", "TERRAIN", "Pakistan:level3", "Pakistan:pak_flood_17Aug"])
# @ToDo Use this to split Internal/External Feeds
#table.group_.requires = IS_NULL_OR(IS_IN_SET(["background"]))
# @ToDo: Can we add KML/GeoRSS/GPX layers using this?
#table.type_.requires = IS_NULL_OR(IS_IN_SET(["OpenLayers.Layer"]))
#table.format.requires = IS_NULL_OR(IS_IN_SET(["image/png"]))

# @ToDo add security
resourcename = "wmc"
tablename = "gis_wmc"
table = db.define_table(tablename,
                        #uuidstamp, # WMCs don't sync
                        projection_id(),
                        Field("lat", "double"), # This is currently 'x' not 'lat'
                        Field("lon", "double"), # This is currently 'y' not 'lon'
                        Field("zoom", "integer"),
                        Field("layer_id", "list:reference gis_wmc_layer",
                              requires=IS_ONE_OF(db, "gis_wmc_layer.id",
                                                 "%(title)s",
                                                 multiple=True)),
                        # Metadata tbc
                        migrate=migrate,
                        *(s3_authorstamp() + s3_ownerstamp() + s3_timestamp()))
#table.lat.requires = IS_LAT()
#table.lon.requires = IS_LON()
table.zoom.requires = IS_INT_IN_RANGE(1, 20)
table.lat.label = T("Latitude")
table.lon.label = T("Longitude")
table.zoom.label = T("Zoom")

# -----------------------------------------------------------------------------
# Below tables are not yet implemented

# GIS Styles: SLD
#resourcename = "style"
#tablename = "gis_style"
#table = db.define_table(tablename,
#                        Field("name", notnull=True, unique=True)
#                        migrate=migrate, *s3_timestamp())
#db.gis_style.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "gis_style.name")]
