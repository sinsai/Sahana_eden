# -*- coding: utf-8 -*-

# 1st-run initialisation
# designed to be called from Crontab's @reboot
# however this isn't reliable so still in models for now...

# Deployments can change settings live via appadmin

if empty:

    # Theme
    table = 'admin_theme'
    if not db(db[table].id).count():
        db[table].insert(
            name = T('Sahana Blue'),
            logo = 'img/sahanapy_logo.png',
            footer = 'footer.html',
            text_direction = 'ltr',
            col_background = '336699',
            col_menu = '0066cc',
            col_highlight = '0077aa',
            col_txt_background = 'f3f6ff',
            col_txt_border = 'c6d1f5',
            col_txt_underline = '003366',
            col_txt = '006699',
            col_input = 'ffffcc',
            col_border_btn_out = '6699cc',
            col_border_btn_in = '4589ce',
            col_btn_hover = '3377bb',
        )
        db[table].insert(
            name = T('Sahana Green'),
            logo = 'img/sahanapy_logo_green.png',
            footer = 'footer.html',
            text_direction = 'ltr',
            col_background = '337733',
            col_menu = 'cc7722',
            col_highlight = '338833',
            col_txt_background = 'f3f6ff',
            col_txt_border = 'c6d1f5',
            col_txt_underline = '003366',
            col_txt = '006699',
            col_input = 'ffffcc',
            col_border_btn_out = '6699cc',
            col_border_btn_in = '4589ce',
            col_btn_hover = '3377bb',
        )
        db[table].insert(
            # Needs work
            # - some colours need changing independently of each other
            # - logo size needs storing
            name = T('Sahana Steel'),
            logo = 'img/sahanapy_logo_ideamonk.png',
            footer = 'footer.html',
            text_direction = 'ltr',
            col_background = 'dbdbdb',
            col_menu = '0066cc',
            col_highlight = '0077aa',
            col_txt_background = 'f3f6ff',
            col_txt_border = 'c6d1f5',
            col_txt_underline = '003366',
            col_txt = 'eeeeee',
            col_input = 'ffffcc',
            col_border_btn_out = 'c6d1f5',
            col_border_btn_in = '4589ce',
            col_btn_hover = '3377bb',
        )

    # Settings
    table = 's3_setting'
    if not db(db[table].id).count():
        db[table].insert(
            admin_name = T("Sahana Haiti Support Team"),
            admin_email = T("haiti@sahanapy.org"),
            admin_tel = T("+44-7789-746281"),
            theme = 1
        )

    table = 'admin_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    table = 'appadmin_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Budget Module
    table = 'budget_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Shelter Registry
    table = 'cr_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Disaster Victim Identification
    table = 'dvi_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Disaster Victim Registration
    table = 'dvr_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    table = 'gis_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Human Remains Management
    table = 'hrm_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Logistics
    table = 'lms_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    table = 'lms_catalog'
    if not db(db[table].id).count():
        db[table].insert(
            name="Default",
            description="Default Catalog",
            comments="All items are by default added to this Catalog"
        )

    # Messaging
    table = 'mobile_setting'
    if not db(db[table].id).count():
        db[table].insert(baud=115200)

    table = 'msg_setting'
    if not db(db[table].id).count():
        db[table].insert(
            inbound_mail_server = 'imap.gmail.com',
            inbound_mail_type = 'imap',
            inbound_mail_ssl = True,
            inbound_mail_port = '993',
            inbound_mail_username = 'username',
            inbound_mail_password = 'password',
            inbound_mail_delete = False,
            #outbound_mail_server = 'mail:25',
            #outbound_mail_from = 'demo@sahanapy.org',
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Missing Person Registry
    table = 'mpr_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Organisation Registry
    table = 'or_setting'
    if not db(db[table].id).count():
        db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    table = 'or_sector'
    if not db(db[table].id).count():
        db[table].insert( name = 'Agriculture' )
        db[table].insert( name = 'Shelter and Non-Food Items' )
        db[table].insert( name = 'Coordination and Support Services' )
        db[table].insert( name = 'Food' )
        db[table].insert( name = 'Infrastructure and Rehabilitation' )
        db[table].insert( name = 'Security' )
        db[table].insert( name = 'Water and Sanitation' )
        db[table].insert( name = 'Education' )
        db[table].insert( name = 'Health' )
        db[table].insert( name = 'Protection and Human Rights and Rule of Law' )
        db[table].insert( name = 'Urban Search and Rescue' )
        
    # Person Registry
    table = 'pr_setting'
    if not db(db[table].id).count():
       db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Request Management System
    table = 'rms_setting'
    if not db(db[table].id).count():
       db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # Synchronisation
    table = 'sync_setting'
    if not db(db[table].id).count():
       db[table].insert(
            uuid = uuid.uuid4()
        )

    # Volunteer Management
    table = 'vol_setting'
    if not db(db[table].id).count():
       db[table].insert(
            # If Disabled at the Global Level then can still Enable just for this Module here
            audit_read = False,
            audit_write = False
        )

    # GIS Module
    table = 'gis_marker'
    # Can't do sub-folders :/
    # need a script to read in the list of default markers from the filesystem, copy/rename & populate the DB 1 by 1
    if not db(db[table].id).count():
        # We want to start at ID 1
        db[table].truncate()
        db[table].insert(
            name = "marker",
            image = "gis_marker.image.marker.png"
        )
        #db[table].insert(
        #    name = "marker_r1",
        #    image = "marker_r1.png"
        #)
        db[table].insert(
            name = "earthquake",
            image = "gis_marker.image.Geo_Earth_Quake_Epicenter.png"
        )
        db[table].insert(
            name = "volcano",
            image = "gis_marker.image.Geo_Volcanic_Threat.png"
        )
        db[table].insert(
            name = "shelter",
            image = "gis_marker.image.Emergency_Shelters_S1.png"
        )
        db[table].insert(
            name = "office",
            image = "gis_marker.image.Emergency_Operations_Center_S1.png"
        )
        db[table].insert(
            name = "hospital",
            image = "gis_marker.image.E_Med_Hospital_S1.png"
        )
        db[table].insert(
            name = "airport",
            image = "gis_marker.image.Trans_Airport_S1.png"
        )
        db[table].insert(
            name = "port",
            image = "gis_marker.image.Trans_Port_S1.png"
        )
        db[table].insert(
            name = "bridge",
            image = "gis_marker.image.Trans_Bridge_S1.png"
        )
        db[table].insert(
            name = "rail_station",
            image = "gis_marker.image.Trans_Rail_Station_S1.png"
        )
        db[table].insert(
            name = "helicopter",
            image = "gis_marker.image.Trans_Helicopter_Landing_Site_S1.png"
        )
        db[table].insert(
            name = "school",
            image = "gis_marker.image.Edu_Schools_S1.png"
        )
        db[table].insert(
            name = "church",
            image = "gis_marker.image.Public_Venue_Church_S1.png"
        )
        db[table].insert(
            name = "temple",
            image = "gis_marker.image.Public_Venue_Temple_S1.png"
        )
        db[table].insert(
            name = "mosque",
            image = "gis_marker.image.Public_Venue_Mosque_S1.png"
        )
        db[table].insert(
            name = "food",
            image = "gis_marker.image.Emergency_Food_Distribution_Centers_S1.png"
        )
        db[table].insert(
            name = "water",
            image = "gis_marker.image.Water_Supply_Infrastructure_Theme_S1.png"
        )

    table = 'gis_projection'
    if not db(db[table].id).count():
       # We want to start at ID 1
       db[table].truncate()
       db[table].insert(
            uuid = uuid.uuid4(),
            name = "Spherical Mercator",
            epsg = 900913,
            maxExtent = "-20037508, -20037508, 20037508, 20037508.34",
            maxResolution = 156543.0339,
            units = "m"
        )
       db[table].insert(
            uuid = uuid.uuid4(),
            name = "WGS84",
            epsg = 4326,
            maxExtent = "-180,-90,180,90",
            maxResolution = 1.40625,
            units = "degrees"
        )

    table = 'gis_config'
    if not db(db[table].id).count():
       # We want to start at ID 1
       db[table].truncate()
       db[table].insert(
            lat = "18.58",
            lon = "-72.42",
            zoom = 10,
            # Doesn't work on Postgres!
            projection_id = 1,
            marker_id = 1,
            map_height = 600,
            map_width = 800
        )

    table = 'gis_feature_class'
    if not db(db[table].id).count():
        db[table].insert(
            name = 'Track',
            #marker_id = db(db.gis_marker.name=='shelter').select()[0].id,
            module = 'gis',
            resource = 'track'
        )
        db[table].insert(
            name = 'Country',
        )
        db[table].insert(
            name = 'Region',
        )
        db[table].insert(
            name = 'District',
        )
        db[table].insert(
            name = 'Town',
        )
        db[table].insert(
            name = 'Incident',
        )
        db[table].insert(
            name = 'Shelter',
            marker_id = db(db.gis_marker.name=='shelter').select()[0].id,
            module = 'cr',
            resource = 'shelter'
        )
        db[table].insert(
            name = 'Office',
            marker_id = db(db.gis_marker.name=='office').select()[0].id,
            module = 'or',
            resource = 'office'
        )
        db[table].insert(
            name = 'Warehouse',
        )
        db[table].insert(
            name = 'Airport',
            marker_id = db(db.gis_marker.name=='airport').select()[0].id,
        )
        db[table].insert(
            name = 'Bridge',
            marker_id = db(db.gis_marker.name=='bridge').select()[0].id,
        )
        db[table].insert(
            name = 'Port',
            marker_id = db(db.gis_marker.name=='port').select()[0].id,
        )
        db[table].insert(
            name = 'Hospital',
            marker_id = db(db.gis_marker.name=='hospital').select()[0].id,
        )
        db[table].insert(
            name = 'Church',
            marker_id = db(db.gis_marker.name=='church').select()[0].id,
        )
        db[table].insert(
            name = 'School',
            marker_id = db(db.gis_marker.name=='school').select()[0].id,
        )
        db[table].insert(
            name = 'Food',
            marker_id = db(db.gis_marker.name=='food').select()[0].id,
        )
        db[table].insert(
            name = 'Water',
            marker_id = db(db.gis_marker.name=='water').select()[0].id,
        )

    table = 'gis_feature_group'
    if not db(db[table].id).count():
        db[table].insert(
            name = 'Towns',
        )
        db[table].insert(
            name = 'Transport',
        )
        db[table].insert(
            name = 'Infrastructure',
        )
        db[table].insert(
            name = 'Programme',
        )
        db[table].insert(
            name = 'Offices',
        )
        db[table].insert(
            name = 'Hospitals',
        )
        
    table = 'gis_feature_class_to_feature_group'
    if not db(db[table].id).count():
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Towns').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Town').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Transport').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Airport').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Transport').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Bridge').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Transport').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Port').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Hospitals').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Hospital').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Infrastructure').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Church').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Infrastructure').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'School').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Programme').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Food').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Programme').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Water').select()[0].id,
        )
        db[table].insert(
            feature_group_id = db(db.gis_feature_group.name == 'Offices').select()[0].id,
            feature_class_id = db(db.gis_feature_class.name == 'Office').select()[0].id,
        )

    table = 'gis_apikey'
    if not db(db[table].id).count():
       db[table].insert(
            name = "google",
            apikey = "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw",
            description = "localhost"
        )
       db[table].insert(
            name = "yahoo",
            apikey = "euzuro-openlayers",
            description = "trial - replace for Production use"
        )
       db[table].insert(
            name = "multimap",
            apikey = "metacarta_04",
            description = "trial - replace for Production use"
        )

    table = 'gis_layer_openstreetmap'
    if not db(db[table].id).count():
        # Populate table
        for subtype in gis_layer_openstreetmap_subtypes:
            db[table].insert(
                    name = 'OSM ' + subtype,
                    subtype = subtype
                )

    table = 'gis_layer_google'
    if not db(db[table].id).count():
        # Populate table
        for subtype in gis_layer_google_subtypes:
            db[table].insert(
                    name = 'Google ' + subtype,
                    subtype = subtype,
                    enabled = False
                )

    table = 'gis_layer_yahoo'
    if not db(db[table].id).count():
        # Populate table
        for subtype in gis_layer_yahoo_subtypes:
            db[table].insert(
                    name = 'Yahoo ' + subtype,
                    subtype = subtype,
                    enabled = False
                )

    #table = 'gis_layer_bing'
    #if not db(db[table].id).count():
        # Populate table
    #    for subtype in gis_layer_bing_subtypes:
    #        db[table].insert(
    #                name = 'Bing ' + subtype,
    #                subtype = subtype,
    #                enabled = False
    #            )

    table = 'gis_layer_wms'
    if not db(db[table].id).count():
        # Populate table
        db[table].insert(
                name = 'VMap0',
                description = 'A Free low-resolution Vector Map of the whole world',
                url = 'http://labs.metacarta.com/wms/vmap0',
                layers = 'basic',
                enabled = False
            )

    table = 'gis_layer_georss'
    if not db(db[table].id).count():
        # Populate table
        db[table].insert(
                name = 'Earthquakes',
                description = 'USGS: Global 7-day',
                url = 'http://earthquake.usgs.gov/eqcenter/catalogs/eqs7day-M2.5.xml',
                projection_id = db(db.gis_projection.epsg == 4326).select()[0].id,
                marker_id = db(db.gis_marker.name == 'earthquake').select()[0].id,
                enabled = False
            )
        db[table].insert(
                name = 'Volcanoes',
                description = 'USGS: US recent',
                url = 'http://volcano.wr.usgs.gov/rss/vhpcaprss.xml',
                projection_id = db(db.gis_projection.epsg == 4326).select()[0].id,
                marker_id = db(db.gis_marker.name == 'volcano').select()[0].id,
                enabled = False
            )

    # Authorization
    # User Roles (uses native Web2Py Auth Groups)
    table = auth.settings.table_group_name
    if not db(db[table].id).count():
        auth.add_group('Administrator', description = 'System Administrator - can access & make changes to any data')
        # Doesn't work on Postgres!
        auth.add_membership(1, 1) # 1st person created will be System Administrator (can be changed later)
        auth.add_group('Anonymous', description = 'Anonymous - dummy group to grant permissions')
        auth.add_group('Authenticated', description = 'Authenticated - all logged-in users')
        auth.add_group('Editor', description = 'Editor - can access & make changes to any unprotected data')
        auth.add_group('Restricted', description = 'Restricted - is given a simplified full-screen view so as to minimise the possibility of errors')
        auth.add_group('DVI', description = 'DVI - allowed access to the DVI module')
        auth.add_group('AdvancedJS', description = 'AdvancedJS - allowed access to edit the Advanced JS layers')
        
    # Security Defaults for all tables
    # For performance we only populate this once (at system startup)
    # => need to populate manually when adding new tables to the database! (less RAD)
    table = auth.settings.table_permission_name
    if not db(db[table].id).count():
        authenticated = auth.id_group('Authenticated')
        editors = auth.id_group('Editor')
        for table in db.tables:
            # allow all registered users the ability to Read all records
            auth.add_permission(authenticated, 'read', db[table])
            # allow anonymous users the ability to Read all records
            #auth.add_permission(anonymous, 'read', db[table])
            # Editors can make changes
            auth.add_permission(editors, 'create', db[table])
            auth.add_permission(editors, 'update', db[table])
            auth.add_permission(editors, 'delete', db[table])

        # Module-specific defaults can be set here
        #table = pr_person
        # Clear out defaults
        #auth.del_permission(authenticated, 'read', db[table])
        #auth.del_permission(editors, 'create', db[table])
        #auth.del_permission(editors, 'update', db[table])
        #auth.del_permission(editors, 'delete', db[table])
        # Add specific Role(s)
        #id = auth.id_group('myrole')
        #auth.add_permission(id, 'read', db[table])
        #auth.add_permission(id, 'create', db[table])
        #auth.add_permission(id, 'update', db[table])
        #auth.add_permission(id, 'delete', db[table])

