# -*- coding: utf-8 -*-

"""
    GIS Controllers

    @author: Fran Boon <fran@aidiq.com>
"""

module = request.controller
resourcename = request.function

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Locations"), False, URL(r=request, f="location"), [
        #[T("List"), False, URL(r=request, f="location")],
        [T("Search"), False, URL(r=request, f="location", args="search")],
        [T("Add"), False, URL(r=request, f="location", args="create")],
        #[T("Geocode"), False, URL(r=request, f="geocode_manual")],
    ]],
    [T("Fullscreen Map"), False, URL(r=request, f="map_viewing_client")],
    # Currently not got geocoding support
    #[T("Bulk Uploader"), False, URL(r=request, c="doc", f="bulk_upload")]
]

if not deployment_settings.get_security_map() or s3_has_role("MapAdmin"):
    response.menu_options.append([T("Service Catalogue"), False, URL(r=request, f="map_service_catalogue")])
    response.menu_options.append([T("De-duplicator"), False, URL(r=request, f="location_duplicates")])


# -----------------------------------------------------------------------------
# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db)

# S3 framework functions
def index():
    """
       Module's Home Page
    """

    module_name = deployment_settings.modules[module].name_nice

    # Include an embedded Overview Map on the index page
    window = False
    toolbar = False

    map = define_map(window=window, toolbar=toolbar)

    response.title = module_name
    return dict(module_name=module_name, map=map)

# -----------------------------------------------------------------------------
def define_map(window=False, toolbar=False, config=None):
    """
        Define the main Situation Map
        This can then be called from both the Index page (embedded) & the Map_Viewing_Client (fullscreen)
    """

    if not config:
        config = gis.get_config()

    if not deployment_settings.get_security_map() or s3_has_role("MapAdmin"):
        catalogue_toolbar = True
    else:
        catalogue_toolbar = False

    # @ToDo: Make these configurable
    search = True
    catalogue_overlays = True

    if config.wmsbrowser_url:
        wms_browser = {"name" : config.wmsbrowser_name,
                       "url" : config.wmsbrowser_url}
    else:
        wms_browser = None

    # 'normal', 'mgrs' or 'off'
    mouse_position = deployment_settings.get_gis_mouse_position()

    # http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
    print_service = deployment_settings.get_gis_print_service()
    if print_service:
        print_tool = {"url": print_service}
    else:
        print_tool = {}

    # Internal Feature Layers
    feature_queries = []
    feature_layers = db(db.gis_layer_feature.enabled == True).select()
    for layer in feature_layers:
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            # Skip layer is it i srestricted & we don't have the required role
            continue
        if layer.filter_field and layer.filter_value:
            table = db["%s_%s" % (layer.module, layer.resource)]
            filter = (table[layer.filter_field] == layer.filter_value)
        else:
            filter = None
        _layer = gis.get_feature_layer(layer.module,
                                       layer.resource,
                                       layer.name,
                                       layer.popup_label,
                                       config=config,
                                       marker_id=layer.marker_id,
                                       filter=filter,
                                       active=layer.visible,
                                       polygons=layer.polygons,
                                       opacity=layer.opacity)
        if _layer:
            feature_queries.append(_layer)

    map = gis.show_map(
                       window=window,
                       catalogue_toolbar=catalogue_toolbar,
                       wms_browser = wms_browser,
                       toolbar=toolbar,
                       search=search,
                       catalogue_overlays=catalogue_overlays,
                       feature_queries=feature_queries,
                       mouse_position = mouse_position,
                       print_tool = print_tool
                      )

    return map

# -----------------------------------------------------------------------------
def location():

    """ RESTful CRUD controller for Locations """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Allow prep to pass vars back to the controller
    vars = {}

    # @ToDo: Clean up what needs to be done only for interactive views,
    # vs. what needs to be done generally. E.g. some tooltips are defined
    # for non-interactive.
    # Pre-processor
    def prep(r, vars):

        def get_location_info():
            return db(db.gis_location.id == r.id).select(db.gis_location.lat,
                                                         db.gis_location.lon,
                                                         db.gis_location.level,
                                                         limitby=(0, 1)).first()

        # Override the default Search Method
        #r.resource.set_handler("search", s3base.S3LocationSearch())

        # Restrict access to Polygons to just MapAdmins
        if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
            table.code.writable = False
            if r.method == "create":
                table.code.readable = False
            table.gis_feature_type.writable = table.gis_feature_type.readable = False
            table.wkt.writable = table.wkt.readable = False
        else:
            table.code.comment = DIV(_class="tooltip",
                                     _title="%s|%s" % (T("Code"),
                                                       T("For a country this would be the ISO2 code, for a Town, it would be the Airport Locode.")))
            table.wkt.comment = DIV(_class="stickytip",
                                    _title="WKT|%s %s%s %s%s" % (T("The"),
                                                               "<a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>",
                                                               T("Well-Known Text"),
                                                               "</a>",
                                                               T("representation of the Polygon/Line.")))

        if r.method == "update":
            # We don't allow converting a location group to non-group and
            # vice versa. We also don't allow taking away all the members of
            # a group -- setting "notnull" gets the "required" * displayed.
            # Groups don't have parents. (This is all checked in onvalidation.)
            location = get_location_info()
            if location.level == "GR":
                table.level.writable = False
                table.parent.readable = table.parent.writable = False
                table.members.notnull = True
                # Record that this is a group location. Since we're setting
                # level to not writable, it won't be in either form.vars or
                # request.vars. Saving it while we have it avoids another
                # db access.
                response.s3.location_is_group = True
            else:
                table.members.writable = table.members.readable = False
                response.s3.location_is_group = False

        # Don't show street address, postcode for hierarchy on read or update.
        if r.method != "create" and r.id:
            try:
                location
            except:
                location = get_location_info()
            if location.level:
                table.addr_street.writable = table.addr_street.readable = False
                table.addr_postcode.writable = table.addr_postcode.readable = False

        if r.http in ("GET", "POST") and r.representation in shn_interactive_view_formats:
            # Options which are only required in interactive HTML views
            table.level.comment = DIV(_class="tooltip",
                                      _title=T("Level") + "|" + T("If the location is a geographic area, then state at what level here."))
            if r.representation == "popup":
                # No 'Add Location' button
                table.parent.comment = DIV(_class="tooltip",
                                           _title=T("Parent") + "|" + T("The Area which this Site is located within."))
            else:
                table.parent.comment = DIV(A(ADD_LOCATION,
                                               _class="colorbox",
                                               _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", child="parent")),
                                               _target="top",
                                               _title=ADD_LOCATION),
                                             DIV(
                                               _class="tooltip",
                                               _title=T("Parent") + "|" + T("The Area which this Site is located within."))),
            table.osm_id.comment = DIV(_class="stickytip",
                                       _title="OpenStreetMap ID|" + T("The") + " <a href='http://openstreetmap.org' target=_blank>OpenStreetMap</a> ID. " + T("If you know what the OSM ID of this location is then you can enter it here."))
            table.geonames_id.comment = DIV(_class="stickytip",
                                            _title="Geonames ID|" + T("The") + " <a href='http://geonames.org' target=_blank>Geonames</a> ID. " + T("If you know what the Geonames ID of this location is then you can enter it here."))
            table.comments.comment = DIV(_class="tooltip",
                                         _title=T("Comments") + "|" + T("Please use this field to record any additional information, such as Ushahidi instance IDs. Include a history of the record if it is updated."))

            if r.representation == "iframe":
                # De-duplicator needs to be able to access UUID fields
                table.uuid.readable = table.uuid.writable = True
                table.uuid.label = "UUID"
                table.uuid.comment = DIV(_class="stickytip",
                                         _title="UUID|" + T("The") + " <a href='http://eden.sahanafoundation.org/wiki/UUID#Mapping' target=_blank>Universally Unique ID</a>. " + T("Suggest not changing this field unless you know what you are doing."))

            if r.method in (None, "list") and r.record is None:
                # List
                pass
            elif r.method in ("delete", "search"):
                pass
            else:
                # Add Map to allow locations to be found this way
                config = gis.get_config()
                lat = config.lat
                lon = config.lon
                zoom = config.zoom
                feature_queries = []

                if r.method == "create":
                    add_feature = True
                    add_feature_active = True
                else:
                    if r.method == "update":
                        add_feature = True
                        add_feature_active = False
                    else:
                        # Read
                        add_feature = False
                        add_feature_active = False

                    try:
                        location
                    except:
                        location = get_location_info()
                    if location and location.lat is not None and location.lon is not None:
                        lat = location.lat
                        lon = location.lon
                    # Same as a single zoom on a cluster
                    zoom = zoom + 2

                # @ToDo: Does map make sense if the user is updating a group?
                # If not, maybe leave it out. OTOH, might be nice to select
                # admin regions to include in the group by clicking on them in
                # the map. Would involve boundaries...
                _map = gis.show_map(lat = lat,
                                    lon = lon,
                                    zoom = zoom,
                                    feature_queries = feature_queries,
                                    add_feature = add_feature,
                                    add_feature_active = add_feature_active,
                                    toolbar = True,
                                    collapsed = True)

                # Pass the map back to the main controller
                vars.update(_map=_map)
        return True
    response.s3.prep = lambda r, vars=vars: prep(r, vars)

    # Options
    _vars = request.vars
    filters = []

    parent = _vars.get("parent_", None)
    # Don't use 'parent' as the var name as otherwise it conflicts with the form's var of the same name & hence this will be triggered during form submission
    if parent:
        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        _parent = parent.lower()

        # Can't do this using a JOIN in DAL syntax
        # .belongs() not GAE-compatible!
        filters.append((db.gis_location.parent.belongs(db(db.gis_location.name.lower().like(_parent)).select(db.gis_location.id))))
        # ToDo: Make this recursive - want descendants not just direct children!
        # Use new gis.get_children() function

    # ToDo
    # bbox = _vars.get("bbox", None):

    if filters:
        from operator import __and__
        response.s3.filter = reduce(__and__, filters)

    caller = _vars.get("caller", None)
    if caller:
        # We've been called as a Popup
        if "gis_location_parent" in caller:
            # Hide unnecessary rows
            table.addr_street.readable = table.addr_street.writable = False
        else:
            parent = _vars.get("parent_", None)
            # Don't use 'parent' as the var name as otherwise it conflicts with the form's var of the same name & hence this will be triggered during form submission
            if parent:
                table.parent.default = parent

            # Hide unnecessary rows
            table.level.readable = table.level.writable = False
            table.geonames_id.readable = table.geonames_id.writable = False
            table.osm_id.readable = table.osm_id.writable = False
            table.source.readable = table.source.writable = False
            table.url.readable = table.url.writable = False

    level = _vars.get("level", None)
    if level:
        # We've been called from the Location Selector widget
        table.addr_street.readable = table.addr_street.writable = False

    output = s3_rest_controller(module, resourcename)

    _map = vars.get("_map", None)
    if _map and isinstance(output, dict):
        output.update(_map=_map)

    return output

def location_duplicates():
    """
        Handle De-duplication of Locations by comparing the ones which are closest together

        @ToDo: Extend to being able to check locations for which we have no Lat<>Lon info (i.e. just names & parents)
    """

    # @ToDo: Set this via the UI & pass in as a var
    dupe_distance = 50 # km

    # Shortcut
    locations = db.gis_location

    table_header = THEAD(TR(TH(T("Location 1")),
                            TH(T("Location 2")),
                            TH(T("Distance(Kms)")),
                            TH(T("Resolve"))))

    # Calculate max possible combinations of records
    # To handle the AJAX requests by the dataTables jQuery plugin.
    totalLocations = db(locations.id > 0).count()

    item_list = []
    if request.vars.iDisplayStart:
        end = int(request.vars.iDisplayLength) + int(request.vars.iDisplayStart)
        locations = db((locations.id > 0) & \
                       (locations.deleted == False) & \
                       (locations.lat != None) & \
                       (locations.lon != None)).select(locations.id,
                                                       locations.name,
                                                       locations.level,
                                                       locations.lat,
                                                       locations.lon)
        # Calculate the Great Circle distance
        count = 0
        for oneLocation in locations[:len(locations) / 2]:
            for anotherLocation in locations[len(locations) / 2:]:
                if count > end and request.vars.max != "undefined":
                    count = int(request.vars.max)
                    break
                if oneLocation.id == anotherLocation.id:
                    continue
                else:
                    dist = gis.greatCircleDistance(oneLocation.lat,
                                                   oneLocation.lon,
                                                   anotherLocation.lat,
                                                   anotherLocation.lon)
                    if dist < dupe_distance:
                        count = count + 1
                        item_list.append([oneLocation.name,
                                          anotherLocation.name,
                                          dist,
                                          "<a href=\"../gis/location_resolve?locID1=%i&locID2=%i\", class=\"action-btn\">Resolve</a>" % (oneLocation.id, anotherLocation.id)
                                         ])
                    else:
                        continue

        item_list = item_list[int(request.vars.iDisplayStart):end]
        # Convert data to JSON
        result  = []
        result.append({
                    "sEcho" : request.vars.sEcho,
                    "iTotalRecords" : count,
                    "iTotalDisplayRecords" : count,
                    "aaData" : item_list
                    })
        output = json.dumps(result)
        # Remove unwanted brackets
        output = output[1:]
        output = output[:-1]
        return output
    else:
        # Don't load records except via dataTables (saves duplicate loading & less confusing for user)
        items = DIV((TABLE(table_header, TBODY(), _id="list", _class="display")))
        return(dict(items=items))

def delete_location():

    """ Delete references to a old record and replacing it with the new one. """

    old = request.vars.old
    new = request.vars.new

    # Find all tables which link to the Locations table
    # @ToDo Replace with db.gis_location._referenced_by
    tables = shn_table_links("gis_location")

    for table in tables:
        for count in range(len(tables[table])):
            field = tables[str(db[table])][count]
            query = db[table][field] == old
            db(query).update(**{field:new})

    # Remove the record
    db(db.gis_location.id == old).update(deleted=True)
    return "Record Gracefully Deleted"

def location_resolve():

    """ Opens a popup screen where the de-duplication process takes place. """

    # @ToDo: Error gracefully if conditions not satisfied
    locID1 = request.vars.locID1
    locID2 = request.vars.locID2

    # Shortcut
    locations = db.gis_location

    # Remove the comment and replace it with buttons for each of the fields
    count = 0
    for field in locations:
        id1 = str(count) + "Right"      # Gives a unique number to each of the arrow keys
        id2 = str(count) + "Left"
        count  = count + 1

        # Comment field filled with buttons
        field.comment = DIV(TABLE(TR(TD(INPUT(_type="button", _id=id1, _class="rightArrows", _value="-->")),
                                     TD(INPUT(_type="button", _id=id2, _class="leftArrows", _value="<--")))))
        record = locations[locID1]
    myUrl = URL(r=request, c="gis", f="location")
    form1 = SQLFORM(locations, record, _id="form1", _action=("%s/%s" % (myUrl, locID1)))

    # For the second location remove all the comments to save space.
    for field in locations:
        field.comment = None
    record = locations[locID2]
    form2 = SQLFORM(locations, record,_id="form2", _action=("%s/%s" % (myUrl, locID2)))
    return dict(form1=form1, form2=form2, locID1=locID1, locID2=locID2)

def location_links():
    """
        @arg id - the location record id
        Returns a JSON array of records which link to the specified location

        @ToDo: Deprecated with new de-duplicator?
    """

    try:
        record_id = request.args[0]
    except:
        item = s3xrc.xml.json_message(False, 400, "Need to specify a record ID!")
        raise HTTP(400, body=item)

    try:
        # Shortcut
        locations = db.gis_location

        deleted = (locations.deleted == False)
        query = (locations.id == record_id)
        query = deleted & query
        record = db(query).select(locations.id, limitby=(0, 1)).first().id
    except:
        item = s3xrc.xml.json_message(False, 404, "Record not found!")
        raise HTTP(404, body=item)

    # Find all tables which link to the Locations table
    # @ToDo: Replace with db.gis_location._referenced_by
    tables = shn_table_links("gis_location")

    results = []
    for table in tables:
        for count in range(len(tables[table])):
            field = tables[str(db[table])][count]
            query = db[table][field] == record_id
            _results = db(query).select()
            module, resourcename = table.split("_", 1)
            for result in _results:
                id = result.id
                # We currently have no easy way to get the default represent for a table!
                try:
                    # Locations & Persons
                    represent = eval("shn_%s_represent(id)" % table)
                except:
                    try:
                        # Organisations
                        represent = eval("shn_%s_represent(id)" % resourcename)
                    except:
                        try:
                            # Many tables have a Name field
                            represent = (id and [db[table][id].name] or ["None"])[0]
                        except:
                            # Fallback
                            represent = id
                results.append({
                    "module" : module,
                    "resource" : resourcename,
                    "id" : id,
                    "represent" : represent
                    })

    output = json.dumps(results)
    return output

# -----------------------------------------------------------------------------
def map_service_catalogue():
    """
        Map Service Catalogue.
        Allows selection of which Layers are active.
    """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    subtitle = T("List Layers")
    # Start building the Return with the common items
    output = dict(subtitle=subtitle)

    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = s3_has_permission("update", table)
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
                item_list.append(TR(TD(A(row.name, _href=URL(r=request, f="layer_%s" % type, args=row.id))), TD(description), TD(enabled), _class=theclass))
        # Feature Layers
        type = "feature"
        for row in db(db.gis_layer_feature.id > 0).select():
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            if row.comments:
                    description = row.comments
            else:
                description = ""
            label = type + "_" + str(row.id)
            if row.enabled:
                enabled = INPUT(_type="checkbox", value=True, _name=label)
            else:
                enabled = INPUT(_type="checkbox", _name=label)
            item_list.append(TR(TD(A(row.name, _href=URL(r=request, f="layer_feature", args=row.id))), TD(description), TD(enabled), _class=theclass))

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
                item_list.append(TR(TD(A(row.name, _href=URL(r=request, f="layer_%s" % type, args=row.id))), TD(description), TD(enabled), _class=theclass))
        # Feature Layers
        type = "feature"
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
            if row.comments:
                description = row.comments
            else:
                description = ""
            if row.enabled:
                enabled = INPUT(_type="checkbox", value="on", _disabled="disabled")
            else:
                enabled = INPUT(_type="checkbox", _disabled="disabled")
            item_list.append(TR(TD(A(row.name, _href=URL(r=request, f="layer_feature", args=row.id))), TD(description), TD(enabled), _class=theclass))

        table_header = THEAD(TR(TH("Layer"), TH("Description"), TH("Enabled?")))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

    output.update(dict(items=items))
    return output

def layers_enable():
    """
        Enable/Disable Layers
    """

    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = s3_has_permission("update", table)
    if authorised:
        for type in gis_layer_types:
            resourcename = "gis_layer_%s" % type
            table = db[resourcename]
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
                        s3_audit("update", module, resourcename, record=row.id, representation="html")
                else:
                    # Old state: Disabled
                    if var in request.vars:
                        # Enable
                        db(query_inner).update(enabled=True)
                        # Audit
                        s3_audit("update", module, resourcename, record=row.id, representation="html")
                    else:
                        # Do nothing
                        pass
        resourcename = "gis_layer_feature"
        table = db[resourcename]
        query = table.id > 0
        sqlrows = db(query).select()
        for row in sqlrows:
            query_inner = (table.id == row.id)
            var = "feature_%i" % (row.id)
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
                    s3_audit("update", module, resourcename, record=row.id, representation="html")
            else:
                # Old state: Disabled
                if var in request.vars:
                    # Enable
                    db(query_inner).update(enabled=True)
                    # Audit
                    s3_audit("update", module, resourcename, record=row.id, representation="html")
                else:
                    # Do nothing
                    pass

        session.flash = T("Layers updated")

    else:
        session.error = T("Not authorised!")

    redirect(URL(r=request, f="map_service_catalogue"))

# -----------------------------------------------------------------------------
def apikey():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if r.representation in shn_interactive_view_formats:
            if r.method == "update":
                table.name.writable = False

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

        return True
    response.s3.prep = prep

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def config():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        if r.representation in shn_interactive_view_formats:
            # Model options
            # In Model so that they're visible to person() as component
            # CRUD Strings (over-ride)
            s3.crud_strings[tablename].title_display = T("Defaults")
            s3.crud_strings[tablename].title_update = T("Edit Defaults")
            s3.crud_strings[tablename].msg_record_modified = T("Defaults updated")
        if deployment_settings.get_security_map() and r.id == 1 and r.method in ["create", "update"] and not s3_has_role("MapAdmin"):
            unauthorised()
        return True
    response.s3.prep = prep

    output = s3_rest_controller(module, resourcename)

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


def feature_class():
    """
        RESTful CRUD controller
        Deprecated? (How to link Symbology with Feature Queries?)
    """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Model options
    table.gps_marker.comment = DIV( _class="tooltip", _title=T("GPS Marker") + "|" + T("Defines the icon used for display of features on handheld GPS."))

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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

def layer_feature():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    # Pre-processor
    def prep(r):
        # Which tables have GIS Locations
        tables = []
        for table in db.tables:
            if "location_id" in db[table]:
                tables.append(table)
        db.gis_layer_feature.resource.requires = IS_IN_SET(tables)

        return True

    response.s3.prep = prep


    # Post-processor
    def postp(r, output):
        if r.record and r.record.resource:
            response.s3.feature_resource = "%s_%s" % (r.record.module, r.record.resource)
        return output

    response.s3.postp = postp

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

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

    s3xrc.model.configure(table,
        create_onvalidation = lambda form: feature_layer_query(form),
        update_onvalidation = lambda form: feature_layer_query(form))

    output = s3_rest_controller(module, resourcename)

    return output

def feature_layer_query(form):
    """
        OnValidation callback to strip the module from the resource
        - in future may build the simple Query from helpers
    """

    resource = None
    if "resource" in form.vars:
        resource = form.vars.resource
        # Remove the module from name
        form.vars.resource = resource[len(form.vars.module) + 1:]

    #if "advanced" in form.vars:
    #    # We should use the query field as-is
    #    pass

    #if resource:
    #    # We build query from helpers
    #    if "filter_field" in form.vars and "filter_value" in form.vars:
    #        if "deleted" in db[resource]:
    #            form.vars.query = "(db[%s].deleted == False) & (db[%s][%s] == '%s')" % (resource, resource, filter_field, filter_value)
    #        else:
    #            form.vars.query = "(db[%s][%s] == '%s')" % (resource, filter_field, filter_value)
    #    else:
    #        if "deleted" in db[resource]:
    #            # All undeleted members of the resource
    #            form.vars.query = "(db[%s].deleted == False)" % (resource)
    #        else:
    #            # All members of the resource
    #            form.vars.query = "(db[%s].id > 0)" % (resource)
    if not resource:
        # Resource is mandatory if not in advanced mode
        session.error = T("Need to specify a Resource!")

    return

def marker():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view and response.view != "popup.html":
        response.view = "gis/" + response.view

    return output

def projection():

    """ RESTful CRUD controller """

    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # CRUD Strings
    ADD_PROJECTION = T("Add Projection")
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def waypoint():

    """ RESTful CRUD controller for GPS Waypoints """

    tablename = "%s_%s" % (module, resourcename)

    return s3_rest_controller(module, resourcename)

def waypoint_upload():

    """
        Custom View
        Temporary: Likely to be refactored into the main waypoint controller
    """

    return dict()

def trackpoint():

    """ RESTful CRUD controller for GPS Track points """

    tablename = "%s_%s" % (module, resourcename)

    return s3_rest_controller(module, resourcename)

def track():

    """ RESTful CRUD controller for GPS Tracks (uploaded as files) """

    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

    # Model options
    # used in multiple controllers, so defined in model

    # CRUD Strings
    # used in multiple controllers, so defined in model

    return s3_rest_controller(module, resourcename)


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

def layer_openstreetmap():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

    # CRUD Strings
    type = "OpenStreetMap"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_google():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Model options

    # CRUD Strings
    type = "Google"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
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

    s3xrc.model.configure(table, deletable=False, listadd=False)
    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_yahoo():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # CRUD Strings
    type = "Yahoo"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
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

    s3xrc.model.configure(table, deletable=False, listadd=False)
    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_mgrs():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # CRUD Strings
    type = "MGRS"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
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

    s3xrc.model.configure(table, deletable=False, listadd=False)
    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_bing():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # CRUD Strings
    type = "Bing"
    LIST_LAYERS = T(LIST_TYPE_LAYERS_FMT % type)
    EDIT_LAYER = T(EDIT_TYPE_LAYER_FMT % type)
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

    s3xrc.model.configure(table, deletable=False, listadd=False)
    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_geojson():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

    # CRUD Strings
    type = "GeoJSON"
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_georss():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_gpx():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

    # Model options
    # Needed in multiple controllers, so defined in Model

    # CRUD Strings
    type = "GPX"
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_kml():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

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
    def user_postp(r, output):
        shn_action_buttons(r, copyable=True)
        return output
    response.s3.postp = user_postp

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_tms():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_wfs():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

    # CRUD Strings
    type = "WFS"
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_wms():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

@auth.s3_requires_membership("MapAdmin")
def layer_js():
    """ RESTful CRUD controller """

    tablename = "%s_%s" % (module, resourcename)

    # CRUD Strings
    type = "JS"
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

def layer_xyz():
    """ RESTful CRUD controller """
    if deployment_settings.get_security_map() and not s3_has_role("MapAdmin"):
        unauthorised()

    tablename = "%s_%s" % (module, resourcename)

    # CRUD Strings
    type = "XYZ"
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

    output = s3_rest_controller(module, resourcename)

    if not "gis" in response.view:
        response.view = "gis/" + response.view

    return output

# -----------------------------------------------------------------------------
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

    map = define_map(window=window, toolbar=toolbar, config=config)

    response.title = T("Map Viewing Client")
    return dict(map=map)

# -----------------------------------------------------------------------------
def display_feature():
    """
        Cut-down version of the Map Viewing Client.
        Used by shn_gis_location_represent() to show just this feature on the map.
        Called by the s3_viewMap() JavaScript
    """

    # The Feature
    feature_id = request.args(0)

    # Check user is authorised to access record
    if not s3_has_permission("read", db.gis_location, feature_id):
        session.error = T("No access to this record!")
        raise HTTP(401, body=s3xrc.xml.json_message(False, 401, session.error))

    query = db(db.gis_location.id == feature_id).select(limitby=(0, 1))
    feature = query.first()

    config = gis.get_config()

    try:
        # Centre on Feature
        lat = feature.lat
        lon = feature.lon
        if (lat is None) or (lon is None):
            if feature.get("parent"):
                # Skip the current record if we can
                latlon = gis.get_latlon(feature.parent)
            elif feature.get("id"):
                latlon = gis.get_latlon(feature.id)
            else:
                # nothing we can do!
                raise
            if latlon:
                lat = latlon["lat"]
                lon = latlon["lon"]
            else:
                # nothing we can do!
                raise
    except:
        lat = config.lat
        lon = config.lon

    # Calculate an appropriate BBox
    #bounds = gis.get_bounds(features=query)

    # Default zoom +2 (same as a single zoom on a cluster)
    zoom = config.zoom + 2

    map = gis.show_map(
        feature_queries = [{"name" : "Feature", "query" : query, "active" : True}],
        lat = lat,
        lon = lon,
        #bbox = bounds,
        zoom = zoom,
        window = True,
        closable = False,
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
        session.error = T("Insufficient vars: Need module, resource, jresource, instance")
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
    accessible = s3_accessible_query("read", db.gis_location)
    query2 = query2 & accessible

    features = db(query).select(db.gis_location.ALL, left = [db.gis_location.on(query2)])

    # Calculate an appropriate BBox
    bounds = gis.get_bounds(features=features)

    map = gis.show_map(
        feature_queries = [{"name" : "Features", "query" : features, "active" : True}],
        bbox = bounds,
        window = True,
        closable = False,
        collapsed = True
    )

    return dict(map=map)

# -----------------------------------------------------------------------------
def geocode():

    """
        Call a Geocoder service
    """

    if "location" in request.vars:
        location = request.vars.location
    else:
        session.error = T("Need to specify a location to search for.")
        redirect(URL(r=request, f="index"))

    if "service" in request.vars:
        service = request.vars.service
    else:
        # @ToDo: service=all should be default
        service = "google"

    if service == "google":
        return s3base.GoogleGeocoder(location, db).get_kml()

    if service == "yahoo":
        return s3base.YahooGeocoder(location, db).get_xml()

# -----------------------------------------------------------------------------
def geocode_manual():

    """
        Manually Geocode locations

        @ToDo: make this accessible by Anonymous users?
    """

    table = db.gis_location

    # Filter
    query = (table.level == None)
    # @ToDo: make this role-dependent
    # - Normal users do the Lat/Lons
    # - Special users do the Codes
    filter = (table.lat == None)
    response.s3.filter = (query & filter)

    # Hide unnecessary fields
    table.name_dummy.readable = table.name_dummy.writable = False
    table.code.readable = table.code.writable = False # @ToDo: Role-dependent
    table.level.readable = table.level.writable = False
    table.members.readable = table.members.writable = False
    table.gis_feature_type.readable = table.gis_feature_type.writable = False
    table.wkt.readable = table.wkt.writable = False
    table.url.readable = table.url.writable = False
    table.geonames_id.readable = table.geonames_id.writable = False
    table.osm_id.readable = table.osm_id.writable = False
    table.source.readable = table.source.writable = False
    table.comments.readable = table.comments.writable = False
    
    # Customise Labels for specific use-cases
    #table.name.label = T("Building Name") # Building Assessments-specific
    #table.parent.label = T("Suburb") # Christchurch-specific
    
    # For Special users doing codes
    #table.code.label = T("Property reference in the council system") # Christchurch-specific 'prupi'
    #table.code2.label = T("Polygon reference of the rating unit") # Christchurch-specific 'gisratingid'

    # Allow prep to pass vars back to the controller
    vars = {}

    # Pre-processor
    def prep(r, vars):
        def get_location_info():
            return db(db.gis_location.id == r.id).select(db.gis_location.lat,
                                                         db.gis_location.lon,
                                                         db.gis_location.level,
                                                         limitby=(0, 1)).first()

        if r.method in (None, "list") and r.record is None:
            # List
            pass
        elif r.method in ("delete", "search"):
            pass
        else:
            # Add Map to allow locations to be found this way
            # @ToDo: DRY with one in location()
            config = gis.get_config()
            lat = config.lat
            lon = config.lon
            zoom = config.zoom
            feature_queries = []

            if r.method == "create":
                add_feature = True
                add_feature_active = True
            else:
                if r.method == "update":
                    add_feature = True
                    add_feature_active = False
                else:
                    # Read
                    add_feature = False
                    add_feature_active = False

                try:
                    location
                except:
                    location = get_location_info()
                if location and location.lat is not None and location.lon is not None:
                    lat = location.lat
                    lon = location.lon
                # Same as a single zoom on a cluster
                zoom = zoom + 2

            # @ToDo: Does map make sense if the user is updating a group?
            # If not, maybe leave it out. OTOH, might be nice to select
            # admin regions to include in the group by clicking on them in
            # the map. Would involve boundaries...
            _map = gis.show_map(lat = lat,
                                lon = lon,
                                zoom = zoom,
                                feature_queries = feature_queries,
                                add_feature = add_feature,
                                add_feature_active = add_feature_active,
                                toolbar = True,
                                collapsed = True)

            # Pass the map back to the main controller
            vars.update(_map=_map)
        return True
    response.s3.prep = lambda r, vars=vars: prep(r, vars)

    s3xrc.model.configure(table, listadd=False,
                          list_fields=["id", "name", "address", "parent"])
    
    output = s3_rest_controller("gis", "location")

    _map = vars.get("_map", None)
    if _map and isinstance(output, dict):
        output.update(_map=_map)

    return output

# -----------------------------------------------------------------------------
def geoexplorer():

    """
        Embedded GeoExplorer: https://github.com/opengeo/GeoExplorer
    """

    _cache = (cache.ram, 60)
    config = gis.get_config()
    public_url = deployment_settings.get_base_public_url()

    # @ToDo: Optimise to a single query of table
    bing_key = gis.get_api_key("bing")
    google_key = gis.get_api_key("google")
    yahoo_key = gis.get_api_key("yahoo")

    # http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
    print_service = deployment_settings.get_gis_print_service()

    geoserver_url = deployment_settings.get_gis_geoserver_url()

    # 'normal', 'mgrs' or 'off'
    mouse_position = deployment_settings.get_gis_mouse_position()

    # Feature Layers
    marker_id_default = config.marker_id
    marker_default = db(db.gis_marker.id == marker_id_default).select(db.gis_marker.image,
                                                                      db.gis_marker.height,
                                                                      db.gis_marker.width,
                                                                      limitby=(0, 1),
                                                                      cache=_cache).first()
    marker_max_width = deployment_settings.get_gis_marker_max_width()
    marker_max_height = deployment_settings.get_gis_marker_max_height()

    # Internal Feature Layers
    layers_features = ""
    feature_queries = []
    feature_layers = db(db.gis_layer_feature.enabled == True).select()
    for layer in feature_layers:
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            continue
        _layer = gis.get_feature_layer(layer.module,
                                       layer.resource,
                                       layer.name,
                                       layer.popup_label,
                                       config=config,
                                       marker_id=layer.marker_id,
                                       active=layer.visible,
                                       polygons=layer.polygons,
                                       opacity=layer.opacity)
        if _layer:
            feature_queries.append(_layer)

    #if feature_queries or add_feature:
    if feature_queries:

        import urllib

        if deployment_settings.get_gis_duplicate_features():
            uuid_from_fid = """
            var uuid = fid.replace('_', '');
            """
        else:
            uuid_from_fid = """
            var uuid = fid;
            """

        layers_features += """
        function onFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var id = 'featureLayerPopup';
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            if (feature.cluster) {
                // Cluster
                var name, fid, uuid, url;
                var html = '""" + T("There are multiple records at this location") + """:<ul>';
                for (var i = 0; i < feature.cluster.length; i++) {
                    name = feature.cluster[i].attributes.name;
                    fid = feature.cluster[i].fid;
                    """ + uuid_from_fid + """
                    if ( feature.cluster[i].popup_url.match("<id>") != null ) {
                        url = feature.cluster[i].popup_url.replace("<id>", uuid)
                    }
                    else {
                        url = feature.cluster[i].popup_url + uuid;
                    }
                    html += "<li><a href='javascript:loadClusterPopup(" + "\\"" + url + "\\", \\"" + id + "\\"" + ")'>" + name + "</a></li>";
                }
                html += '</ul>';
                html += "<div align='center'><a href='javascript:zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    html,
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                feature.layer.map.addPopup(popup);
            } else {
                // Single Feature
                var popup_url = feature.popup_url;
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    """ + '"' + T("Loading") + """...<img src='""" + URL(r=request, c="static", f="img", args="ajax-loader.gif") + """' border=0>",
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                feature.layer.map.addPopup(popup);
                // call AJAX to get the contentHTML
                var fid = feature.fid;
                """ + uuid_from_fid + """
                if ( popup_url.match("<id>") != null ) {
                    popup_url = popup_url.replace("<id>", uuid)
                }
                else {
                    popup_url = popup_url + uuid;
                }
                loadDetails(popup_url, id, popup);
            }
        }
        """

    for layer in feature_queries:
        if "name" in layer:
            name = str(T(layer["name"]))
        else:
            name = "Query" + str(int(random.random()*1000))

        if "marker" in layer:
            marker = layer["marker"]
            try:
                # query
                marker_id = marker.id
                markerLayer = marker
            except:
                # integer (marker_id)
                markerLayer = db(db.gis_marker.id == layer["marker"]).select(db.gis_marker.image, db.gis_marker.height, db.gis_marker.width, limitby=(0, 1), cache=_cache).first()
        else:
            markerLayer = ""

        if "opacity" in layer:
            opacity = layer["opacity"]
        else:
            opacity = 1

        if "popup_url" in layer:
            _popup_url = urllib.unquote(layer["popup_url"])
        else:
            _popup_url = urllib.unquote(URL(r=request, c="gis", f="location", args=["read.popup?location.id="]))

        if "polygon" in layer and layer.polygon:
            polygons = True
        else:
            polygons = False

        # Generate HTML snippet
        name_safe = re.sub("\W", "_", name)
        if "active" in layer and layer["active"]:
            visibility = "featureLayer" + name_safe + ".setVisibility(true);"
        else:
            visibility = "featureLayer" + name_safe + ".setVisibility(false);"
        layers_features += """
            features = [];
            var popup_url = '""" + _popup_url + """';
            // Needs to be uniquely instantiated
            var style_cluster = new OpenLayers.Style(style_cluster_style, style_cluster_options);
            // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
            var featureClusterStyleMap = new OpenLayers.StyleMap({
                                            'default': style_cluster,
                                            'select': {
                                                fillColor: '#ffdc33',
                                                strokeColor: '#ff9933'
                                            }
            });

            // Needs to be uniquely instantiated per-layer
            var strategy_cluster = new OpenLayers.Strategy.Cluster({distance: s3_gis_cluster_distance, threshold: s3_gis_cluster_threshold})
            var featureLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
                '""" + name + """',
                {
                    strategies: [ strategy_cluster ],
                    styleMap: featureClusterStyleMap
                }
            );
            """ + visibility + """
            featureLayer""" + name_safe + """.events.on({
                "featureselected": onFeatureSelect,
                "featureunselected": onFeatureUnselect
            });
            featureLayers.push(featureLayer""" + name_safe + """);
            """
        features = layer["query"]
        for _feature in features:
            try:
                _feature.gis_location.id
                # Query was generated by a Join
                feature = _feature.gis_location
            except (AttributeError, KeyError):
                # Query is a simple select
                feature = _feature
            # Should we use Polygons or Points?
            if polygons:
                if feature.get("wkt"):
                    wkt = feature.wkt
                else:
                    # Deal with manually-imported Features which are missing WKT
                    try:
                        lat = feature.lat
                        lon = feature.lon
                        if (lat is None) or (lon is None):
                            # Zero is allowed but not None
                            if feature.get("parent"):
                                # Skip the current record if we can
                                latlon = gis.get_latlon(feature.parent)
                            elif feature.get("id"):
                                latlon = gis.get_latlon(feature.id)
                            else:
                                # nothing we can do!
                                continue
                            if latlon:
                                lat = latlon["lat"]
                                lon = latlon["lon"]
                            else:
                                # nothing we can do!
                                continue
                    except:
                        if feature.get("parent"):
                            # Skip the current record if we can
                            latlon = gis.get_latlon(feature.parent)
                        elif feature.get("id"):
                            latlon = gis.get_latlon(feature.id)
                        else:
                            # nothing we can do!
                            continue
                        if latlon:
                            lat = latlon["lat"]
                            lon = latlon["lon"]
                        else:
                            # nothing we can do!
                            continue
                    wkt = gis.latlon_to_wkt(lat, lon)
            else:
                # Just display Point data, even if we have Polygons
                # @ToDo: DRY with Polygon
                try:
                    lat = feature.lat
                    lon = feature.lon
                    if (lat is None) or (lon is None):
                        # Zero is allowed but not None
                        if feature.get("parent"):
                            # Skip the current record if we can
                            latlon = gis.get_latlon(feature.parent)
                        elif feature.get("id"):
                            latlon = gis.get_latlon(feature.id)
                        else:
                            # nothing we can do!
                            continue
                        if latlon:
                            lat = latlon["lat"]
                            lon = latlon["lon"]
                        else:
                            # nothing we can do!
                            continue
                except:
                    if feature.get("parent"):
                        # Skip the current record if we can
                        latlon = gis.get_latlon(feature.parent)
                    elif feature.get("id"):
                        latlon = gis.get_latlon(feature.id)
                    else:
                        # nothing we can do!
                        continue
                    if latlon:
                        lat = latlon["lat"]
                        lon = latlon["lon"]
                    else:
                        # nothing we can do!
                        continue
                wkt = gis.latlon_to_wkt(lat, lon)

            try:
                # Has a per-feature Vector Shape been added to the query?
                graphicName = feature.shape
                if graphicName not in ["circle", "square", "star", "x", "cross", "triangle"]:
                    # Default to Circle
                    graphicName = "circle"
                try:
                    pointRadius = feature.size
                    if not pointRadius:
                        pointRadius = 12
                except (AttributeError, KeyError):
                    pointRadius = 12
                try:
                    fillColor = feature.color
                    if not fillColor:
                        fillColor = "orange"
                except (AttributeError, KeyError):
                    fillColor = "orange"
                marker_url = ""
            except (AttributeError, KeyError):
                # Use a Marker not a Vector Shape
                try:
                    # Has a per-feature marker been added to the query?
                    _marker = feature.marker
                    if _marker:
                        marker = _marker
                    else:
                        marker = marker_default
                except (AttributeError, KeyError):
                    if markerLayer:
                        marker = markerLayer
                    else:
                        marker = marker_default
                # Faster to bypass the download handler
                #marker_url = URL(r=request, c="default", f="download", args=[marker.image])
                marker_url = URL(r=request, c="static", f="img", args=["markers", marker.image])

            try:
                # Has a per-feature popup_label been added to the query?
                popup_label = feature.popup_label
            except (AttributeError, KeyError):
                popup_label = feature.name

            # Allows map API to be used with Storage instead of Rows
            if not popup_label:
                popup_label = feature.name
            # Deal with apostrophes in Feature Names
            fname = re.sub("'", "\\'", popup_label)

            if marker_url:
                layers_features += """
            styleMarker.iconURL = '""" + marker_url + """';
            styleMarker.opacity = '""" + str(opacity) + """';
            // Need unique names
            // More reliable & faster to use the height/width calculated on upload
            var i = new Array();
            i.height = """ + str(marker.height) + """;
            i.width = """ + str(marker.width) + """;
            scaleImage(i);
            """
            else:
                layers_features += """
            var i = '';
            styleMarker.iconURL = '';
            styleMarker.opacity = '""" + str(opacity) + """';
            styleMarker.graphicName = '""" + graphicName + """';
            styleMarker.pointRadius = """ + str(pointRadius) + """;
            styleMarker.fillColor = '""" + fillColor + """';
            """
            layers_features += """
            geom = parser.read('""" + wkt + """').geometry;
            featureVec = addFeature('""" + str(feature.id) + """', '""" + fname + """', geom, styleMarker, i, popup_url)
            features.push(featureVec);
            """
            if deployment_settings.get_gis_duplicate_features():
                # Add an additional Point feature to provide wrapping around the Data Line
                # lon<0 have a duplicate at lon+360
                if lon < 0:
                    lon = lon + 360
                # lon>0 have a duplicate at lon-360
                else:
                    lon = lon - 360
                wkt = gis.latlon_to_wkt(lat, lon)
                layers_features += """
            geom = parser.read('""" + wkt + """').geometry;
            featureVec = addFeature('_""" + str(feature.id) + """', '""" + fname + """', geom, styleMarker, i, popup_url)
            features.push(featureVec);
            """
        # Append to Features layer
        layers_features += """
            featureLayer""" + name_safe + """.addFeatures(features);
            """
        # Add to Map
        layers_features += """
            this.mapPanel.map.addLayer(featureLayer""" + name_safe + """);
            """

    # Can we cache downloaded feeds?
    # Needed for unzipping & filtering as well
    cachepath = os.path.join(request.folder, "uploads", "gis_cache")
    if os.access(cachepath, os.W_OK):
        cacheable = True
        import urllib2      # for error handling
        from gluon.tools import fetch
    else:
        cacheable = False

    # GeoRSS
    layers_georss = ""
    georss_enabled = db(db.gis_layer_georss.enabled == True).select()
    for layer in georss_enabled:
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            continue
        name = layer["name"]
        url = layer["url"]
        visible = layer["visible"]
        georss_projection = db(db.gis_projection.id == layer["projection_id"]).select(db.gis_projection.epsg, limitby=(0, 1)).first().epsg
        if georss_projection == 4326:
            projection_str = "projection: s3_gis_proj4326,"
        else:
            projection_str = "projection: new OpenLayers.Projection('EPSG:" + georss_projection + "'),"
        marker_id = layer["marker_id"]
        if marker_id:
            marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, db.gis_marker.height, db.gis_marker.width, limitby=(0, 1)).first()
        else:
            marker = db(db.gis_marker.id == marker__id_default).select(db.gis_marker.image, db.gis_marker.height, db.gis_marker.width, limitby=(0, 1)).first()
        marker_url = URL(r=request, c="static", f="img", args=["markers", marker.image])
        height = marker.height
        width = marker.width

        if cacheable:
            # Download file
            try:
                file = fetch(url)
                warning = ""
            except urllib2.URLError:
                warning = "URLError"
            except urllib2.HTTPError:
                warning = "HTTPError"
            _name = name.replace(" ", "_")
            _name = _name.replace(",", "_")
            filename = "gis_cache.file." + _name + ".rss"
            filepath = os.path.join(cachepath, filename)
            f = open(filepath, "w")
            # Handle errors
            if "URLError" in warning or "HTTPError" in warning:
                # URL inaccessible
                if os.access(filepath, os.R_OK):
                    # Use cached version
                    date = db(db.gis_cache.name == name).select(db.gis_cache.modified_on, limitby=(0, 1)).first().modified_on
                    response.warning += url + " " + T("not accessible - using cached version from") + " " + str(date) + "\n"
                    url = URL(r=request, c="default", f="download", args=[filename])
                else:
                    # No cached version available
                    response.warning += url + " " + T("not accessible - no cached version available!") + "\n"
                    # skip layer
                    continue
            else:
                # Download was succesful
                # Write file to cache
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

        # Generate HTML snippet
        name_safe = re.sub("\W", "_", name)
        if visible:
            visibility = "georssLayer" + name_safe + ".setVisibility(true);"
        else:
            visibility = "georssLayer" + name_safe + ".setVisibility(false);"
        layers_georss += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = i.width;
        style_marker.graphicHeight = i.height;
        style_marker.graphicXOffset = -(i.width / 2);
        style_marker.graphicYOffset = -i.height;
        style_marker.externalGraphic = iconURL;
        // Needs to be uniquely instantiated per-layer
        var strategy_cluster = new OpenLayers.Strategy.Cluster({distance: s3_gis_cluster_distance, threshold: s3_gis_cluster_threshold})
        var georssLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                """ + projection_str + """
                strategies: [ new OpenLayers.Strategy.Fixed(), strategy_cluster ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_georss
                })
            }
        );
        """ + visibility + """
        this.mapPanel.map.addLayer(georssLayer""" + name_safe + """);
        georssLayers.push(georssLayer""" + name_safe + """);
        georssLayer""" + name_safe + """.events.on({ "featureselected": onGeorssFeatureSelect, "featureunselected": onFeatureUnselect });
        """

     # GPX
    layers_gpx = ""
    gpx_enabled = db(db.gis_layer_gpx.enabled == True).select()
    for layer in gpx_enabled:
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            continue
        name = layer["name"]
        track = db(db.gis_track.id == layer.track_id).select(db.gis_track.track, limitby=(0, 1)).first()
        if track:
            url = URL(r=request, c="default", f="download") + "/" + track.track
        else:
            url = ""
        visible = layer["visible"]
        waypoints = layer["waypoints"]
        tracks = layer["tracks"]
        routes = layer["routes"]
        marker_id = layer["marker_id"]
        if marker_id:
            marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, limitby=(0, 1)).first().image
        else:
            marker = marker_default.image
        marker_url = URL(r=request, c="static", f="img", args=["markers", marker])

        # Generate HTML snippet
        name_safe = re.sub("\W", "_", name)
        if visible:
            visibility = "gpxLayer" + name_safe + ".setVisibility(true);"
        else:
            visibility = "gpxLayer" + name_safe + ".setVisibility(false);"
        gpx_format = "extractAttributes:true"
        if not waypoints:
            gpx_format += ", extractWaypoints:false"
            style_marker = """
        style_marker.externalGraphic = '';
        """
        else:
            style_marker = """
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = i.width;
        style_marker.graphicHeight = i.height;
        style_marker.graphicXOffset = -(i.width / 2);
        style_marker.graphicYOffset = -i.height;
        style_marker.externalGraphic = iconURL;
        """
        if not tracks:
            gpx_format += ", extractTracks:false"
        if not routes:
            gpx_format += ", extractRoutes:false"
        layers_gpx += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        """ + style_marker + """
        style_marker.strokeColor = 'blue';
        style_marker.strokeWidth = 6;
        style_marker.strokeOpacity = 0.5;
        // Needs to be uniquely instantiated per-layer
        var strategy_cluster = new OpenLayers.Strategy.Cluster({distance: s3_gis_cluster_distance, threshold: s3_gis_cluster_threshold})
        var gpxLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                projection: s3_gis_proj4326,
                strategies: [ new OpenLayers.Strategy.Fixed(), strategy_cluster ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: new OpenLayers.Format.GPX({""" + gpx_format + """})
                })
            }
        );
        """ + visibility + """
        this.mapPanel.map.addLayer(gpxLayer""" + name_safe + """);
        gpxLayers.push(gpxLayer""" + name_safe + """);
        gpxLayer""" + name_safe + """.events.on({ 'featureselected': onGpxFeatureSelect, 'featureunselected': onFeatureUnselect });
        """

    # KML
    layers_kml = ""
    kml_enabled = db(db.gis_layer_kml.enabled == True).select()
    for layer in kml_enabled:
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            continue
        name = layer["name"]
        url = layer["url"]
        visible = layer["visible"]
        title = layer["title"] or "name"
        body = layer["body"] or "description"
        projection_str = "projection: s3_gis_proj4326,"
        marker_id = layer["marker_id"]
        if marker_id:
            marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, db.gis_marker.height, db.gis_marker.width, limitby=(0, 1)).first()
        else:
            marker = marker_default
        marker_url = URL(r=request, c="static", f="img", args=["markers", marker.image])
        height = marker.height
        width = marker.width
        if cacheable:
            # Download file
            file, warning = gis.download_kml(url, public_url)
            _name = name.replace(" ", "_")
            _name = _name.replace(",", "_")
            filename = "gis_cache.file." + _name + ".kml"
            filepath = os.path.join(cachepath, filename)
            f = open(filepath, "w")
            # Handle errors
            if "URLError" in warning or "HTTPError" in warning:
                # URL inaccessible
                if os.access(filepath, os.R_OK):
                    statinfo = os.stat(filepath)
                    if statinfo.st_size:
                        # Use cached version
                        date = db(db.gis_cache.name == name).select(db.gis_cache.modified_on, limitby=(0, 1)).first().modified_on
                        response.warning += url + " " + T("not accessible - using cached version from") + " " + str(date) + "\n"
                        url = URL(r=request, c="default", f="download", args=[filename])
                    else:
                        # 0k file is all that is available
                        response.warning += url + " " + T("not accessible - no cached version available!") + "\n"
                        # skip layer
                        continue
                else:
                    # No cached version available
                    response.warning += url + " " + T("not accessible - no cached version available!") + "\n"
                    # skip layer
                    continue
            else:
                # Download was succesful
                if "ParseError" in warning:
                    # @ToDo Parse detail
                    response.warning += T("Layer") + ": " + name + " " + T("couldn't be parsed so NetworkLinks not followed.") + "\n"
                if "GroundOverlay" in warning or "ScreenOverlay" in warning:
                    response.warning += T("Layer") + ": " + name + " " + T("includes a GroundOverlay or ScreenOverlay which aren't supported in OpenLayers yet, so it may not work properly.") + "\n"
                # Write file to cache
                f.write(file)
                f.close()
                record = db(db.gis_cache.name == name).select().first()
                if record:
                    record.update(modified_on=response.utcnow)
                else:
                    db.gis_cache.insert(name=name, file=filename)
                url = URL(r=request, c="default", f="download", args=[filename])
        else:
            # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
            pass

        # Generate HTML snippet
        name_safe = re.sub("\W", "_", name)
        layer_name = "kmlLayer" + name_safe
        if visible:
            visibility = layer_name + ".setVisibility(true);"
        else:
            visibility = layer_name + ".setVisibility(false);"
        layers_kml += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = i.width;
        style_marker.graphicHeight = i.height;
        style_marker.graphicXOffset = -(i.width / 2);
        style_marker.graphicYOffset = -i.height;
        style_marker.externalGraphic = iconURL;
        // Needs to be uniquely instantiated per-layer
        var strategy_cluster = new OpenLayers.Strategy.Cluster({distance: s3_gis_cluster_distance, threshold: s3_gis_cluster_threshold})
        var kmlLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name + """',
            {
                """ + projection_str + """
                strategies: [ new OpenLayers.Strategy.Fixed(), strategy_cluster ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_kml
                })
            }
        );
        """ + visibility + """
        kmlLayer""" + name_safe + """.title = '""" + title + """';
        kmlLayer""" + name_safe + """.body = '""" + body + """';
        this.mapPanel.map.addLayer(kmlLayer""" + name_safe + """);
        kmlLayers.push(kmlLayer""" + name_safe + """);
        kmlLayer""" + name_safe + """.events.on({ "featureselected": onKmlFeatureSelect, "featureunselected": onFeatureUnselect });
        """

    # Coordinate Grid
    layer_coordinategrid = ""
    coordinate_enabled = db(db.gis_layer_coordinate.enabled == True).select(db.gis_layer_coordinate.name, db.gis_layer_coordinate.visible, db.gis_layer_coordinate.role_required)
    if coordinate_enabled:
        layer = coordinate_enabled.first()
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            pass
        else:
            name = layer["name"]
            # Generate HTML snippet
            name_safe = re.sub("\W", "_", name)
            if "visible" in layer and layer["visible"]:
                visibility = ""
            else:
                visibility = ", visibility: false"
            layer_coordinategrid = """
        this.mapPanel.map.addLayer(new OpenLayers.Layer.cdauth.CoordinateGrid(null, { name: '""" + name_safe + """', shortName: 'grid' """ + visibility + """ }));
        """

    response.title = "GeoExplorer"
    return dict(
                config=config,
                marker_max_width = marker_max_width,
                marker_max_height = marker_max_height,
                bing_key=bing_key,
                google_key=google_key,
                yahoo_key=yahoo_key,
                print_service=print_service,
                geoserver_url=geoserver_url,
                mouse_position = mouse_position,
                layers_features = layers_features,
                layers_georss = layers_georss,
                layers_gpx = layers_gpx,
                layers_kml = layers_kml,
                layer_coordinategrid = layer_coordinategrid
               )

def about():
    """  Custom View for GeoExplorer """
    return dict()

def maps():

    """
        Map Save/Publish Handler for GeoExplorer
    """

    if request.env.request_method == "GET":
        # This is a request to read the config of a saved map

        # Which map are we updating?
        id = request.args(0)
        if not id:
            raise HTTP(501)

        # Read the WMC record
        record = db(db.gis_wmc.id == id).select(limitby=(0, 1)).first()
        # & linked records
        #projection = db(db.gis_projection.id == record.projection).select(limitby=(0, 1)).first()

        # Put details into the correct structure
        output = dict()
        output["map"] = dict()
        map = output["map"]
        map["center"] = [record.lat, record.lon]
        map["zoom"] = record.zoom
        # @ToDo: Read Projection (we generally use 900913 & no way to edit this yet)
        map["projection"] = "EPSG:900913"
        map["units"] = "m"
        map["maxResolution"] = 156543.0339
        map["maxExtent"] = [ -20037508.34, -20037508.34, 20037508.34, 20037508.34 ]
        # @ToDo: Read Layers
        map["layers"] = []
        #map["layers"].append(dict(source="google", title="Google Terrain", name="TERRAIN", group="background"))
        #map["layers"].append(dict(source="ol", group="background", fixed=True, type="OpenLayers.Layer", args=[ "None", {"visibility":False} ]))
        for _layer in record.layer_id:
            layer = db(db.gis_wmc_layer.id == _layer).select(limitby=(0, 1)).first()
            if layer.type_ == "OpenLayers.Layer":
                # Add args
                map["layers"].append(dict(source=layer.source, title=layer.title, name=layer.name, group=layer.group_, type=layer.type_, format=layer.img_format, visibility=layer.visibility, transparent=layer.transparent, opacity=layer.opacity, fixed=layer.fixed, args=[ "None", {"visibility":False} ]))
            else:
                map["layers"].append(dict(source=layer.source, title=layer.title, name=layer.name, group=layer.group_, type=layer.type_, format=layer.img_format, visibility=layer.visibility, transparent=layer.transparent, opacity=layer.opacity, fixed=layer.fixed))

        # @ToDo: Read Metadata (no way of editing this yet)

        # Encode as JSON
        output = json.dumps(output)

        # Output to browser
        response.headers["Content-Type"] = "application/json"
        return output

    elif request.env.request_method == "POST":
        # This is a request to save/publish a new map

        # Get the data from the POST
        source = request.body.read()
        if isinstance(source, basestring):
            from StringIO import StringIO
            source = StringIO(source)

        # Decode JSON
        source = json.load(source)
        # @ToDo: Projection (we generally use 900913 & no way to edit this yet)
        lat = source["map"]["center"][0]
        lon = source["map"]["center"][1]
        zoom = source["map"]["zoom"]
        # Layers
        layers = []
        for layer in source["map"]["layers"]:
            try:
                opacity = layer["opacity"]
            except:
                opacity = None
            try:
                name = layer["name"]
            except:
                name = None
            _layer = db((db.gis_wmc_layer.source == layer["source"]) &
                        (db.gis_wmc_layer.name == name) &
                        (db.gis_wmc_layer.visibility == layer["visibility"]) &
                        (db.gis_wmc_layer.opacity == opacity)
                       ).select(db.gis_wmc_layer.id,
                                limitby=(0, 1)).first()
            if _layer:
                # This is an existing layer
                layers.append(_layer.id)
            else:
                # This is a new layer
                try:
                    type_ = layer["type"]
                except:
                    type_ = None
                try:
                    group_ = layer["group"]
                except:
                    group_ = None
                try:
                    fixed = layer["fixed"]
                except:
                    fixed = None
                try:
                    format = layer["format"]
                except:
                    format = None
                try:
                    transparent = layer["transparent"]
                except:
                    transparent = None
                # Add a new record to the gis_wmc_layer table
                _layer = db.gis_wmc_layer.insert(source=layer["source"], name=name, visibility=layer["visibility"], opacity=opacity, type_=type_, title=layer["title"], group_=group_, fixed=fixed, transparent=transparent, img_format=format)
                layers.append(_layer)

        # @ToDo: Metadata (no way of editing this yet)

        # Save a record in the WMC table
        id = db.gis_wmc.insert(lat=lat, lon=lon, zoom=zoom, layer_id=layers)

        # Return the ID of the saved record for the Bookmark
        output = json.dumps(dict(id=id))
        return output

    elif request.env.request_method == "PUT":
        # This is a request to save/publish an existing map

        # Which map are we updating?
        id = request.args(0)
        if not id:
            raise HTTP(501)

        # Get the data from the PUT
        source = request.body.read()
        if isinstance(source, basestring):
            from StringIO import StringIO
            source = StringIO(source)

        # Decode JSON
        source = json.load(source)
        # @ToDo: Projection (unlikely to change)
        lat = source["map"]["center"][0]
        lon = source["map"]["center"][1]
        zoom = source["map"]["zoom"]
        # Layers
        layers = []
        for layer in source["map"]["layers"]:
            try:
                opacity = layer["opacity"]
            except:
                opacity = None
            try:
                name = layer["name"]
            except:
                name = None
            _layer = db((db.gis_wmc_layer.source == layer["source"]) &
                        (db.gis_wmc_layer.name == name) &
                        (db.gis_wmc_layer.visibility == layer["visibility"]) &
                        (db.gis_wmc_layer.opacity == opacity)
                       ).select(db.gis_wmc_layer.id,
                                limitby=(0, 1)).first()
            if _layer:
                # This is an existing layer
                layers.append(_layer.id)
            else:
                # This is a new layer
                try:
                    type_ = layer["type"]
                except:
                    type_ = None
                try:
                    group_ = layer["group"]
                except:
                    group_ = None
                try:
                    fixed = layer["fixed"]
                except:
                    fixed = None
                try:
                    format = layer["format"]
                except:
                    format = None
                try:
                    transparent = layer["transparent"]
                except:
                    transparent = None
                # Add a new record to the gis_wmc_layer table
                _layer = db.gis_wmc_layer.insert(source=layer["source"], name=name, visibility=layer["visibility"], opacity=opacity, type_=type_, title=layer["title"], group_=group_, fixed=fixed, transparent=transparent, img_format=format)
                layers.append(_layer)

        # @ToDo: Metadata (no way of editing this yet)

        # Update the record in the WMC table
        db(db.gis_wmc.id == id).update(lat=lat, lon=lon, zoom=zoom, layer_id=layers)

        # Return the ID of the saved record for the Bookmark
        output = json.dumps(dict(id=id))
        return output

    # Abort - we shouldn't get here
    raise HTTP(501)

# -----------------------------------------------------------------------------
def potlatch2():
    """
        Custom View for the Potlatch2 OpenStreetMap editor
        http://wiki.openstreetmap.org/wiki/Potlatch_2
    """

    if request.args(0) == "potlatch2.html":
        osm_oauth_consumer_key = deployment_settings.get_osm_oauth_consumer_key()
        osm_oauth_consumer_secret = deployment_settings.get_osm_oauth_consumer_secret()
        if osm_oauth_consumer_key and osm_oauth_consumer_secret:
            gpx_url = None
            if "gpx_id" in request.vars:
                # Pass in a GPX Track
                # @ToDo: Set the viewport based on the Track, if one is specified
                track = db(db.gis_track.id == request.vars.gpx_id).select(db.gis_track.track, limitby=(0, 1)).first()
                if track:
                    gpx_url = URL(r=request, c="default", f="download") + "/" + track.track

            if "lat" in request.vars:
                lat = request.vars.lat
                lon = request.vars.lon
            else:
                settings = gis.get_config()
                lat = settings.lat
                lon = settings.lon

            if "zoom" in request.vars:
                zoom = request.vars.zoom
            else:
                # This isn't good as it makes for too large an area to edit
                #zoom = settings.zoom
                zoom = 14

            #response.extra_styles = ["S3/potlatch2.css"]

            return dict(lat=lat, lon=lon, zoom=zoom, key=osm_oauth_consumer_key, secret=osm_oauth_consumer_secret, gpx_url=gpx_url)

        else:
            session.error = T("To edit OpenStreetMap, you need to edit the OpenStreetMap settings in models/000_config.py")
            redirect(URL(r=request, f="index"))

    else:
        # This is a hack for unconfigured servers.
        # Production instances should configure the server to bypass the Model loads completely
        # (Apache mod_rewrite or Web2Py routes.py)
        #('.*:/eden/gis/potlatch2/potlatch2.html', '/eden/gis/potlatch2/potlatch2.html'),
        #('.*:/eden/gis/potlatch2/(?P<file>[\w\./_-]+)', '/eden/static/potlatch2/\g<file>'),
        redirect(URL(a=request.application, c="static", f="potlatch2", args=request.args), how=301)

# -----------------------------------------------------------------------------
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

    # @ToDo: Link to map_service_catalogue to prevent Open Proxy abuse
    # (although less-critical since we restrict content type)
    allowedHosts = []
    #allowedHosts = ["www.openlayers.org", "demo.opengeo.org"]

    allowed_content_types = (
        "application/json", "text/json", "text/x-json",
        "application/xml", "text/xml",
        "application/vnd.ogc.se_xml",           # OGC Service Exception
        "application/vnd.ogc.se+xml",           # OGC Service Exception
        "application/vnd.ogc.success+xml",      # OGC Success (SLD Put)
        "application/vnd.ogc.wms_xml",          # WMS Capabilities
        "application/vnd.ogc.context+xml",      # WMC
        "application/vnd.ogc.gml",              # GML
        "application/vnd.ogc.sld+xml",          # SLD
        "application/vnd.google-earth.kml+xml", # KML
    )

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
        if "url" in request.vars:
            url = request.vars.url
        else:
            session.error = T("Need a 'url' argument!")
            raise HTTP(400, body=s3xrc.xml.json_message(False, 400, session.error))

    try:
        host = url.split("/")[2]
        if allowedHosts and not host in allowedHosts:
            raise(HTTP(403, "Host not permitted: %s" % host))

        elif url.startswith("http://") or url.startswith("https://"):
            if method == "POST":
                length = int(request["wsgi"].environ["CONTENT_LENGTH"])
                headers = {"Content-Type": request["wsgi"].environ["CONTENT_TYPE"]}
                body = request.body.read(length)
                r = urllib2.Request(url, body, headers)
                y = urllib2.urlopen(r)
            else:
                # GET
                y = urllib2.urlopen(url)

            # Check for allowed content types
            i = y.info()
            if i.has_key("Content-Type"):
                ct = i["Content-Type"]
                if not ct.split(";")[0] in allowed_content_types:
                    # @ToDo?: Allow any content type from allowed hosts (any port)
                    #if allowedHosts and not host in allowedHosts:
                    raise(HTTP(403, "Content-Type not permitted"))
            else:
                raise(HTTP(406, "Unknown Content"))

            msg = y.read()
            y.close()

            # Maintain the incoming Content-Type
            response.headers["Content-Type"] = ct
            return msg

        else:
            # Bad Request
            raise(HTTP(400))

    except Exception, E:
        raise(HTTP(500, "Some unexpected error occurred. Error text was: %s" % str(E)))

# -----------------------------------------------------------------------------
# Tests - not Production
def test():
    """
       Test Mapping API
    """

    # Will use default popup_url
    hospitals = {"feature_group" : "Hospitals"}

    if auth.is_logged_in():
        offices = {"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location", args="update.popup")}
    else:
        offices = {"feature_group" : "Offices", "popup_url" : URL(r=request, c="gis", f="location", args="read.popup")}

    query = db((db.gis_feature_class.name == "Town") & (db.gis_location.feature_class_id == db.gis_feature_class.id)).select()

    html = gis.show_map(
                add_feature = True,
                collapsed = True,
                #feature_groups = [offices, hospitals],
                #feature_queries = [{"name" : "Towns", "query" : query, "active" : True}],
                #wms_browser = {"name" : "OpenGeo Demo WMS", "url" : "http://demo.opengeo.org/geoserver/ows?service=WMS&request=GetCapabilities"},
                ##wms_browser = {"name" : "Risk Maps", "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
                ##wms_browser = {"name" : "Risk Maps", "url" : "http://www.pdc.org/wms/wmservlet/PDC_Active_Hazards?request=getcapabilities&service=WMS&version=1.1.1"},
                #catalogue_overlays = True,
                #catalogue_toolbar = True,
                #legend = True, # Stops Feature Layers from Printing
                #toolbar = True,
                #search = True,
                #print_tool = {
                #        #"url" : "http://localhost:8080/geoserver/pdf/",                    # Local GeoServer
                #        "url" : "http://localhost:8080/print-servlet-1.2-SNAPSHOT/pdf/",    # Local Windows Tomcat
                #        #"url" : "http://host.domain:8180/print-servlet-1.2-SNAPSHOT/pdf/", # Linux Tomcat
                #        "mapTitle" : "Title",
                #        "subTitle" : "SubTitle"
                #    },
                ##mgrs = {"name" : "MGRS Atlas PDFs", "url" : "http://www.sharedgeo.org/datasets/shared/maps/usng/pdf.map?VERSION=1.0.0&SERVICE=WFS&request=GetFeature&typename=wfs_all_maps"},
                #window = True,
                )

    return dict(map=html)

def test2():
    """
        Test new OpenLayers functionality in a RAD environment
        - currently being used to trial using GeoJSON for internal feature layers
    """

    # Internal Feature Layers
    feature_queries = []
    feature_layers = db(db.gis_layer_feature.resource == "office").select()
    for layer in feature_layers:
        if layer.role_required and not auth.s3_has_role(layer.role_required):
            continue
        _layer = gis.get_feature_layer(layer.module,
                                       layer.resource,
                                       layer.name,
                                       layer.popup_label,
                                       config=config,
                                       marker_id=layer.marker_id,
                                       active=layer.visible,
                                       polygons=layer.polygons,
                                       opacity=layer.opacity)
        if _layer:
            # Add a URL for downloading the GeoJSON
            # @ToDO: add to gis.get_feature_layer
            _layer["url"] = "%s.geojson" % URL(r=request, c=layer.module, f=layer.resource)
            marker = db(db.gis_marker.id == _layer["marker"]).select(db.gis_marker.image,
                                                                     db.gis_marker.height,
                                                                     db.gis_marker.width,
                                                                     limitby=(0, 1)).first()
            _layer["marker"] = marker
            feature_queries.append(_layer)

    return dict(feature_queries=feature_queries)

# -----------------------------------------------------------------------------