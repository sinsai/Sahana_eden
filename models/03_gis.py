# -*- coding: utf-8 -*-

"""
    GIS
"""

module = "gis"

# Settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

# GIS Markers (Icons)
resource = "marker"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                #uuidstamp, # Markers don't sync
                Field("name", length=128, notnull=True, unique=True),
                #Field("height", "integer"), # In Pixels, for display purposes
                #Field("width", "integer"),  # Not needed since we get size client-side using Javascript's Image() class
                Field("image", "upload", autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "static/img/markers")
# Reusable field for other tables to reference
ADD_MARKER = T("Add Marker")
marker_id = SQLTable(None, "marker_id",
            FieldS3("marker_id", db.gis_marker, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_marker.id", "%(name)s")),
                represent = lambda id: (id and [DIV(IMG(_src=URL(r=request, c="default", f="download", args=db(db.gis_marker.id==id).select().first().image), _height=40))] or [""])[0],
                label = T("Marker"),
                comment = DIV(A(ADD_MARKER, _class="colorbox", _href=URL(r=request, c="gis", f="marker", args="create", vars=dict(format="popup")), _target="top", _title=ADD_MARKER), DIV( _class="tooltip", _title=T("Marker|Defines the icon used for display of features."))),
                ondelete = "RESTRICT"
                ))

# GIS Projections
resource = "projection"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                Field("name", length=128, notnull=True, unique=True),
                Field("epsg", "integer", notnull=True),
                Field("maxExtent", length=64, notnull=True),
                Field("maxResolution", "double", notnull=True),
                Field("units", notnull=True),
                migrate=migrate)
# Reusable field for other tables to reference
projection_id = SQLTable(None, "projection_id",
            FieldS3("projection_id", db.gis_projection, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_projection.id", "%(name)s")),
                represent = lambda id: db(db.gis_projection.id==id).select().first().name,
                label = T("Projection"),
                comment = "",
                ondelete = "RESTRICT"
                ))

# GIS Symbology
resource = "symbology"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                Field("name", length=128, notnull=True, unique=True),
                migrate=migrate)
# Reusable field for other tables to reference
symbology_id = SQLTable(None, "symbology_id",
            FieldS3("symbology_id", db.gis_symbology, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_symbology.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_symbology.id==id).select().first().name] or ["None"])[0],
                label = T("Symbology"),
                comment = "",
                ondelete = "RESTRICT"
                ))

# GIS Config
gis_config_layout_opts = {
    1:T("window"),
    2:T("embedded")
    }
opt_gis_layout = SQLTable(None, "opt_gis_layout",
                    Field("opt_gis_layout", "integer",
                        requires = IS_IN_SET(gis_config_layout_opts),
                        default = 1,
                        label = T("Layout"),
                        represent = lambda opt: gis_config_layout_opts.get(opt, UNKNOWN_OPT)))
# id=1 = Default settings
# separated from Framework settings above
# ToDo Extend for per-user Profiles - this is the WMC
resource = "config"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp,
                Field("lat", "double"),
                Field("lon", "double"),
                Field("zoom", "integer"),
                projection_id,
                symbology_id,
                marker_id,
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
                migrate=migrate)

# GIS Feature Classes
# These are used in groups (for display/export), for icons & for URLs to edit data
resource = "feature_class"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                Field("description"),
                marker_id,
                Field("module"),    # Used to build Edit URL
                Field("resource"),  # Used to build Edit URL & to provide Attributes to Display
                migrate=migrate)
# Reusable field for other tables to reference
ADD_FEATURE_CLASS = T("Add Feature Class")
feature_class_id = SQLTable(None, "feature_class_id",
            FieldS3("feature_class_id", db.gis_feature_class, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_feature_class.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_feature_class.id==id).select().first().name] or ["None"])[0],
                label = T("Feature Class"),
                comment = DIV(A(ADD_FEATURE_CLASS, _class="colorbox", _href=URL(r=request, c="gis", f="feature_class", args="create", vars=dict(format="popup")), _target="top", _title=ADD_FEATURE_CLASS), A(SPAN("[Help]"), _class="tooltip", _title=T("Feature Class|Defines the marker used for display & the attributes visible in the popup."))),
                ondelete = "RESTRICT"
                ))

# Symbology to Feature Class to Marker
resource = "symbology_to_feature_class"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                symbology_id,
                feature_class_id,
                marker_id,
                migrate=migrate)

# GIS Locations
gis_feature_type_opts = {
    1:T("Point"),
    2:T("Line"),
    3:T("Polygon"),
    #4:T("MultiPolygon")
    }
resource = "location"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                Field("name", notnull=True),
                Field("level", length=2),
                Field("code"),
                Field("description"),
                feature_class_id,
                #Field("resource_id", "integer"), # ID in associated resource table. FIXME: Remove as link should be reversed?
                Field("parent", "reference gis_location", ondelete = "RESTRICT"),   # This form of hierarchy may not work on all Databases
                # Street Address (other address fields come from hierarchy)
                Field("addr_street"),
                #Field("addr_postcode"),
                Field("lft", "integer", readable=False, writable=False), # Left will be for MPTT: http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
                Field("rght", "integer", readable=False, writable=False),# Right currently unused
                marker_id,
                Field("gis_feature_type", "integer", default=1, notnull=True),
                Field("lat", "double"), # Points or Centroid for Polygons
                Field("lon", "double"), # Points or Centroid for Polygons
                Field("wkt", "text"),   # WKT is auto-calculated from lat/lon for Points
                Field("osm_id"),        # OpenStreetMap ID. Should this be used in UUID field instead?
                Field("lon_min", "double", writable=False, readable=False), # bounding-box
                Field("lat_min", "double", writable=False, readable=False), # bounding-box
                Field("lon_max", "double", writable=False, readable=False), # bounding-box
                Field("lat_max", "double", writable=False, readable=False), # bounding-box
                Field("elevation", "integer", writable=False, readable=False),   # m in height above WGS84 ellipsoid (approximately sea-level). not displayed currently
                Field("ce", "integer", writable=False, readable=False), # Circular 'Error' around Lat/Lon (in m). Needed for CoT.
                Field("le", "integer", writable=False, readable=False), # Linear 'Error' for the Elevation (in m). Needed for CoT.
                admin_id,
                migrate=migrate)

# Reusable field for other tables to reference
ADD_LOCATION = T("Add Location")
location_id = SQLTable(None, "location_id",
            FieldS3("location_id", db.gis_location, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", "%(name)s")),
                represent = lambda id: shn_gis_location_represent(id),
                label = T("Location"),
                comment = DIV(A(ADD_LOCATION, _class="colorbox", _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")), _target="top", _title=ADD_LOCATION), A(SPAN("[Help]"), _class="tooltip", _title=T("Location|The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                ondelete = "RESTRICT"
                ))

s3xrc.model.configure(db.gis_location,
                      onvalidation=lambda form: gis.wkt_centroid(form),
                      onaccept=gis.update_location_tree())

# -----------------------------------------------------------------------------
#
def shn_gis_location_represent(id):
    # TODO: optimize! (very slow)
    try:
        location = db(db.gis_location.id==id).select().first()
        # Simple
        #represent = location.name
        # Fancy Map
        #represent = A(location.name, _href="#", _onclick="viewMap(" + str(id) +");return false")
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
            text = lat_prefix + " " + str(lat) + " " + lon_prefix + " " + str(lon)
        else:
            text = location.name
        represent = text
        # Hyperlink
        represent = A(text, _href = S3_PUBLIC_URL + URL(r=request, c="gis", f="location", args=[location.id]))
        # ToDo: Convert to popup? (HTML again!)
    except:
        try:
            # "Invalid" => data consistency wrong
            represent = location.id
        except:
            represent = None
    return represent


# Feature Groups
# Used to select a set of Feature Classes for either Display or Export
resource = "feature_group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                Field("description"),
                Field("enabled", "boolean", default=True, label=T("Enabled?")),
                migrate=migrate)
# Reusable field for other tables to reference
ADD_FEATURE_GROUP = T("Add Feature Group")
feature_group_id = SQLTable(None, "feature_group_id",
            FieldS3("feature_group_id", db.gis_feature_group, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_feature_group.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_feature_group.id==id).select().first().name] or ["None"])[0],
                label = T("Feature Group"),
                comment = DIV(A(ADD_FEATURE_GROUP, _class="colorbox", _href=URL(r=request, c="gis", f="feature_group", args="create", vars=dict(format="popup")), _target="top", _title=ADD_FEATURE_GROUP), DIV( _class="tooltip", _title=T("Feature Group|A collection of Feature Classes which can be displayed together on a map or exported together."))),
                ondelete = "RESTRICT"
                ))

# Many-to-Many tables
# No longer supported
#resource = "location_to_feature_group"
#tablename = "%s_%s" % (module, resource)
#table = db.define_table(tablename, timestamp, deletion_status,
#                feature_group_id,
#                location_id,
#                migrate=migrate)

resource = "feature_class_to_feature_group"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, deletion_status,
                feature_group_id,
                feature_class_id,
                migrate=migrate)

# GIS Keys - needed for commercial mapping services
resource = "apikey" # Can't use 'key' as this has other meanings for dicts!
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                Field("name", notnull=True),
                Field("apikey", length=128, notnull=True),
                Field("description"),
                migrate=migrate)

# GPS Tracks (files in GPX format)
resource = "track"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                #uuidstamp, # Tracks don't sync
                Field("name", length=128, notnull=True, unique=True),
                Field("description", length=128),
                Field("track", "upload", autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
table.track.uploadfolder = os.path.join(request.folder, "uploads/tracks")
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
table.track.requires = IS_UPLOAD_FILENAME(extension="gpx")
table.track.description = T("Description")
table.track.label = T("GPS Track File")
table.track.comment = DIV(SPAN("*", _class="req"), DIV( _class="tooltip", _title=T("GPS Track|A file in GPX format taken from a GPS whose timestamps can be correlated with the timestamps on the photos to locate them on the map.")))
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
# Reusable field for other tables to reference
track_id = SQLTable(None, "track_id",
            FieldS3("track_id", db.gis_track, sortby="name",
                requires = IS_NULL_OR(IS_ONE_OF(db, "gis_track.id", "%(name)s")),
                represent = lambda id: (id and [db(db.gis_track.id==id).select().first().name] or ["None"])[0],
                label = T("Track"),
                comment = DIV(A(ADD_TRACK, _class="colorbox", _href=URL(r=request, c="gis", f="track", args="create", vars=dict(format="popup")), _target="top", _title=ADD_TRACK), DIV( _class="tooltip", _title=T("GPX Track|A file downloaded from a GPS containing a series of geographic points in XML format."))),
                ondelete = "RESTRICT"
                ))

# GIS Layers
#gis_layer_types = ["shapefile", "scan", "wfs"]
gis_layer_types = ["openstreetmap", "georss", "google", "gpx", "js", "kml", "mgrs", "tms", "wms", "xyz", "yahoo"]
#gis_layer_openstreetmap_subtypes = ["Mapnik", "Osmarender", "Aerial"]
gis_layer_openstreetmap_subtypes = ["Mapnik", "Osmarender"]
gis_layer_google_subtypes = ["Satellite", "Maps", "Hybrid", "Terrain"]
gis_layer_yahoo_subtypes = ["Satellite", "Maps", "Hybrid"]
gis_layer_bing_subtypes = ["Satellite", "Maps", "Hybrid", "Terrain"]
# Base table from which the rest inherit
gis_layer = SQLTable(db, "gis_layer", timestamp,
            #uuidstamp, # Layers like OpenStreetMap, Google, etc shouldn't sync
            Field("name", notnull=True, label=T("Name"), requires=IS_NOT_EMPTY(), comment=SPAN("*", _class="req")),
            Field("description", label=T("Description")),
            #Field("priority", "integer", label=T("Priority")),    # System default priority is set in ol_layers_all.js. User priorities are set in WMC.
            Field("enabled", "boolean", default=True, label=T("Available in Viewer?")))
for layertype in gis_layer_types:
    resource = "layer_" + layertype
    tablename = "%s_%s" % (module, resource)
    # Create Type-specific Layer tables
    if layertype == "openstreetmap":
        t = SQLTable(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type"))            )
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "georss":
        t = SQLTable(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            Field("url", label=T("Location")),
            projection_id,
            marker_id)
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "google":
        t = SQLTable(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "gpx":
        t = SQLTable(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            #Field("url", label=T("Location")),
            track_id,
            marker_id)
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "kml":
        t = SQLTable(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            Field("url", label=T("Location")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "js":
        t = SQLTable(db, table,
            gis_layer,
            Field("code", "text", label=T("Code"), default="var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);"))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "mgrs":
        t = SQLTable(db, table,
            gis_layer,
            Field("url", label=T("Location")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "tms":
        t = SQLTable(db, table,
            gis_layer,
            Field("url", label=T("Location")),
            Field("layers", label=T("Layers")),
            Field("format", label=T("Format")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "wms":
        t = SQLTable(db, table,
            gis_layer,
            Field("visible", "boolean", default=False, label=T("On by default?")),
            Field("url", label=T("Location")),
            Field("base", "boolean", default=True, label=T("Base Layer?")),
            Field("map", label=T("Map")),
            Field("layers", label=T("Layers")),
            Field("format", label=T("Format")),
            Field("transparent", "boolean", default=False, label=T("Transparent?")),
            projection_id)
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "xyz":
        t = SQLTable(db, table,
            gis_layer,
            Field("url", label=T("Location")),
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
        t = SQLTable(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type")))
        table = db.define_table(tablename, t, migrate=migrate)
    elif layertype == "bing":
        t = SQLTable(db, table,
            gis_layer,
            Field("subtype", label=T("Sub-type")))
        table = db.define_table(tablename, t, migrate=migrate)

# GIS Cache
# (Store downloaded KML & GeoRSS feeds)
resource = "cache"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp,
                Field("name", length=128, notnull=True, unique=True),
                Field("file", "upload", autodelete = True),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
table.file.uploadfolder = os.path.join(request.folder, "uploads/gis_cache")

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

