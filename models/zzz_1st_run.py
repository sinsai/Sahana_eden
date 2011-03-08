# -*- coding: utf-8 -*-

# 1st-run initialisation
# designed to be called from Crontab's @reboot
# however this isn't reliable (doesn't work on Win32 Service) so still in models for now...

# Deployments can change settings live via appadmin

# Set deployment_settings.base.prepopulate to False in Production (to save 1x DAL hit every page)
if not deployment_settings.get_base_prepopulate() or db(db["s3_setting"].id > 0).count():
    populate = False
else:
    populate = True

if populate:

    # Themes
    tablename = "admin_theme"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            name = T("Sahana Blue"),
            logo = "img/sahanapy_logo.png",
            #header_background = "img/header_bg.png",
            #footer = "footer.html",
            col_background = "336699",
            col_menu = "0066cc",
            col_highlight = "0077aa",
            col_txt_background = "f3f6ff",
            col_txt_border = "c6d1f5",
            col_txt_underline = "003366",
            col_txt = "006699",
            col_input = "ffffcc",
            col_border_btn_out = "6699cc",
            col_border_btn_in = "4589ce",
            col_btn_hover = "3377bb",
        )
        table.insert(
            name = T("Sahana Green"),
            logo = "img/sahanapy_logo_green.png",
            #header_background = "img/header_bg.png",
            #footer = "footer.html",
            col_background = "337733",
            col_menu = "cc7722",
            col_highlight = "338833",
            col_txt_background = "f3f6ff",
            col_txt_border = "c6d1f5",
            col_txt_underline = "003366",
            col_txt = "006699",
            col_input = "ffffcc",
            col_border_btn_out = "6699cc",
            col_border_btn_in = "4589ce",
            col_btn_hover = "3377bb",
        )
        table.insert(
            # Needs work
            # - some colours need changing independently of each other
            # - logo size needs storing
            name = T("Sahana Steel"),
            logo = "img/sahanapy_logo_ideamonk.png",
            #header_background = "img/header_bg.png",
            #footer = "footer.html",
            col_background = "dbdbdb",
            col_menu = "0066cc",
            col_highlight = "0077aa",
            col_txt_background = "f3f6ff",
            col_txt_border = "c6d1f5",
            col_txt_underline = "003366",
            col_txt = "eeeeee",
            col_input = "ffffcc",
            col_border_btn_out = "c6d1f5",
            col_border_btn_in = "4589ce",
            col_btn_hover = "3377bb",
        )

    # Global Settings
    tablename = "s3_setting"
    table = db[tablename]
    # Ensure that the theme we defined is in the DB ready to be used as a FK
    db.commit()
    if not db(table.id > 0).count():
        table.insert(
            admin_name = T("Sahana Administrator").xml(),
            admin_email = "support@Not Set",
            admin_tel = T("Not Set").xml(),
            theme = 1
        )

    # Organisation Registry
    tablename = "org_cluster"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            abrv = T("Agriculture"),
            name = T("Agriculture")
        )
        table.insert(
            abrv = T("Camp"),
            name = T("Camp Coordination/Management")
        )
        table.insert(
            abrv = T("Recovery"),
            name = T("Early Recovery")
        )
        table.insert(
            abrv = T("Education"),
            name = T("Education")
        )
        table.insert(
            abrv = T("Shelter"),
            name = T("Emergency Shelter")
        )
        table.insert(
            abrv = T("Telecommunications"),
            name = T("Emergency Telecommunications")
        )
        table.insert(
            abrv = T("Health"),
            name = T("Health")
        )
        table.insert(
            abrv = T("Logistics"),
            name = T("Logistics")
        )
        table.insert(
            abrv = T("Nutrition"),
            name = T("Nutrition")
        )
        table.insert(
            abrv = T("Protection"),
            name = T("Protection")
        )
        table.insert(
            abrv = T("WASH"),
            name = T("Water Sanitation Hygiene")
        )
    tablename = "org_cluster_subsector"
    table = db[tablename]
    # Ensure that the clusters we defined are in the DB ready to be used as a FK
    db.commit()
    if not db(table.id > 0).count():
        cluster_shelter = db(db.org_cluster.abrv == "Shelter").select(db.org_cluster.id, limitby=(0, 1)).first().id
        cluster_nutrition = db(db.org_cluster.abrv == "Nutrition").select(db.org_cluster.id, limitby=(0, 1)).first().id
        cluster_wash = db(db.org_cluster.abrv == "WASH").select(db.org_cluster.id, limitby=(0, 1)).first().id
        table.insert(
            cluster_id = cluster_shelter,
            abrv = T("Clothing")
        )
        table.insert(
            cluster_id = cluster_shelter,
            abrv = T("Shelter")
        )
        table.insert(
            cluster_id = cluster_nutrition,
            abrv = T("Cooking NFIs")
        )
        table.insert(
            cluster_id = cluster_nutrition,
            abrv = T("Food Supply")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Aggravating factors")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Disease vectors")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Drainage")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Excreta disposal")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Hygiene NFIs")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Hygiene practice")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Solid waste")
        )
        table.insert(
            cluster_id = cluster_wash,
            abrv = T("Water supply")
        )

    # Person Registry
    tablename = "pr_person"
    table = db[tablename]
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    field = "first_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    field = "middle_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    field = "last_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

    # Synchronisation
    tablename = "sync_setting"
    table = db[tablename]
    if not db(table.id > 0).count():
       table.insert(proxy="")

    # Incident Reporting System
    if "irs" in deployment_settings.modules:
        # Categories visible to ends-users by default
        tablename = "irs_icategory"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(code = "flood")
            table.insert(code = "geophysical.landslide")
            table.insert(code = "roadway.bridgeClosure")
            table.insert(code = "roadway.roadwayClosure")
            table.insert(code = "other.buildingCollapsed")
            table.insert(code = "other.peopleTrapped")
            table.insert(code = "other.powerFailure")

    # Messaging Module
    if "msg" in deployment_settings.modules:
        tablename = "msg_email_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                inbound_mail_server = "imap.gmail.com",
                inbound_mail_type = "imap",
                inbound_mail_ssl = True,
                inbound_mail_port = 993,
                inbound_mail_username = "username",
                inbound_mail_password = "password",
                inbound_mail_delete = False,
                #outbound_mail_server = "mail:25",
                #outbound_mail_from = "demo@sahanafoundation.org",
            )
        # Need entries for the Settings/1/Update URLs to work
        tablename = "msg_setting"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( outgoing_sms_handler = "Gateway" )
        tablename = "msg_modem_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( modem_baud = 115200 )
        tablename = "msg_gateway_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( to_variable = "to" )
        tablename = "msg_tropo_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( token_messaging = "" )
        tablename = "msg_twitter_settings"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( pin = "" )

    # Assessment
    if "assess" in deployment_settings.modules:
        tablename = "assess_baseline_type"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( name = "# of population")
            table.insert( name = "# of households" )
            table.insert( name = "# of children under 5" )
            table.insert( name = "# of children" )
            table.insert( name = "# of cattle" )
            table.insert( name = "Ha. of fields" )

    # Impacts
    if deployment_settings.has_module("irs") or deployment_settings.has_module("assess"):
        tablename = "impact_type"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( name = "# of People Affected" )
            table.insert( name = "# People Needing Food",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "Food",
                                                     look_up_field = "abrv")
                          )
            table.insert( name = "# People at Risk From Vector-Borne Diseases",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "Health",
                                                     look_up_field = "abrv")
                          )
            table.insert( name = "# People without Access to Safe Drinking-Water",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "WASH",
                                                     look_up_field = "abrv")
                          )
            table.insert( name = "# Houses Damaged",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "Shelter",
                                                     look_up_field = "abrv")
                          )
            table.insert( name = "# Houses Flooded",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "Shelter",
                                                     look_up_field = "abrv")
                          )
            table.insert( name = "Water Level still high?",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "Shelter",
                                                     look_up_field = "abrv")
                          )
            table.insert( name = "Ha. Fields Flooded",
                          cluster_id = \
                              shn_get_db_field_value(db = db,
                                                     table = "org_cluster",
                                                     field = "id",
                                                     look_up = "Agriculture",
                                                     look_up_field = "abrv")
                          )

    if deployment_settings.has_module("inv"):
        # Supply / Inventory
        tablename = "supply_item_category"
        table = db[tablename]
        if not db(table.id > 0).count():
            #shn_import_table("supply_item_category")
            table.insert( name = "Agriculture" )
            #table.insert( name = "Clothing" )
            #table.insert( name = "Equipment" )
            table.insert( name = "Food" )
            table.insert( name = "Health" )
            #table.insert( name = "NFIs" )
            table.insert( name = "Shelter" )
            #table.insert( name = "Transport" )
            table.insert( name = "WASH" )
        tablename = "supply_item"
        table = db[tablename]
        if not db(table.id > 0).count():
            #shn_import_table("supply_item_pakistan")
            agriculture = db(db.supply_item_category.name == "Agriculture").select(db.supply_item_category.id, limitby=(0, 1)).first().id
            food = db(db.supply_item_category.name == "Food").select(db.supply_item_category.id, limitby=(0, 1)).first().id
            health = db(db.supply_item_category.name == "Health").select(db.supply_item_category.id, limitby=(0, 1)).first().id
            shelter = db(db.supply_item_category.name == "Shelter").select(db.supply_item_category.id, limitby=(0, 1)).first().id
            wash = db(db.supply_item_category.name == "WASH").select(db.supply_item_category.id, limitby=(0, 1)).first().id
            table.insert(
                item_category_id = agriculture,
                name = "Rice Seed",
                base_unit = "sack20kg",
                comments = "This should provide enough seed for 1 Hectare of land"
                )
            table.insert(
                item_category_id = food,
                name = "Rice",
                base_unit = "sack50kg",
                comments = "This should feed 125 people for 1 day"
                )
            table.insert(
                item_category_id = food,
                name = "Cooking Utensils",
                base_unit = "kit",
                comments = "Cooking Utensils for a Household"
                )
            table.insert(
                item_category_id = health,
                name = "First Ait Kit",
                base_unit = "kit",
                comments = "This should provide basic first aid (bandages, oral rehydration salts, etc) for 100 people to self-administer"
                )
            table.insert(
                item_category_id = health,
                name = "Medical Kit",
                base_unit = "kit",
                comments = "This should provide medical supplies (medicines, vaccines) for a professional clinic to provide assistance to a total community of 10,000 people."
                )
            table.insert(
                item_category_id = shelter,
                name = "Shelter Kit",
                base_unit = "kit",
                comments = "This kit is suitable to provide emergency repair to a damaged home. It contains a tarpaulin, zinc sheet, wooden poles, hammer & nails"
                )
            table.insert(
                item_category_id = shelter,
                name = "Tent",
                base_unit = "piece",
                comments = "This should house a family of up to 8 people"
                )
            table.insert(
                item_category_id = wash,
                name = "Hygiene Kit",
                base_unit = "kit",
                comments = "Personal Hygiene supplies for 100 Households (5 persons/household): Each get 2x Buckets, 10x Soap, Cotton cloth"
                )
            table.insert(
                item_category_id = wash,
                name = "Water Purification Sachets",
                base_unit = "kit",
                comments = "Designed to provide a 1st phase drinking water purification solution at the household level. Contains 600 sachets to provide sufficient drinking water (4l) for 100 people for 30 days."
                )

            # enter base_unit as packets
            item_rows = db(table.id > 0).select(table.id, table.base_unit)
            for item_row in item_rows:
                db.supply_item_packet.insert(
                    item_id = item_row.id,
                    name = item_row.base_unit,
                    quantity = 1
                   )

    # Project Module
    if deployment_settings.has_module("project"):
        tablename = "project_need_type"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( name = T("People Needing Food") )
            table.insert( name = T("People Needing Water") )
            table.insert( name = T("People Needing Shelter") )

    # Budget Module
    if "budget" in deployment_settings.modules:
        tablename = "budget_parameter"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
            )

    # Logistics (old)
    if "lms" in deployment_settings.modules:
        tablename = "lms_catalog"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert(
                name="Default",
                description="Default Catalog",
                comments="All items are by default added to this Catalog"
            )

    # Ticketing System
    if "ticket" in deployment_settings.modules:
        tablename = "ticket_category"
        table = db[tablename]
        if not db(table.id > 0).count():
            table.insert( name = "Report Missing Person" )
            table.insert( name = "Report Security Incident" )
            table.insert( name = "Report Information" )
            table.insert( name = "Request for Assistance" )
            table.insert( name = "Offer of Help" )

    # GIS Module
    tablename = "gis_marker"
    table = db[tablename]
    # Can't do sub-folders :/
    # need a script to read in the list of default markers from the filesystem, copy/rename & populate the DB 1 by 1
    if not db(table.id > 0).count():
        # We want to start at ID 1, but postgres won't let us truncate() & not needed anyway this is only run on 1st_run.
        #table.truncate()
        table.insert(
            name = "marker_red",
            height = 34,
            width = 20,
            image = "gis_marker.image.marker_red.png"
        )
        table.insert(
            name = "marker_yellow",
            height = 34,
            width = 20,
            image = "gis_marker.image.marker_yellow.png"
        )
        table.insert(
            name = "marker_amber",
            height = 34,
            width = 20,
            image = "gis_marker.image.marker_amber.png"
        )
        table.insert(
            name = "marker_green",
            height = 34,
            width = 20,
            image = "gis_marker.image.marker_green.png"
        )
        table.insert(
            name = "person",
            height = 50,
            width = 50,
            image = "gis_marker.image.Civil_Disturbance_Theme.png"
        )
        table.insert(
            name = "school",
            height = 33,
            width = 44,
            image = "gis_marker.image.Edu_Schools_S1.png"
        )
        table.insert(
            name = "food",
            height = 40,
            width = 40,
            image = "gis_marker.image.Emergency_Food_Distribution_Centers_S1.png"
        )
        table.insert(
            name = "office",
            height = 40,
            width = 40,
            image = "gis_marker.image.Emergency_Operations_Center_S1.png"
        )
        table.insert(
            name = "shelter",
            height = 40,
            width = 40,
            image = "gis_marker.image.Emergency_Shelters_S1.png"
        )
        table.insert(
            name = "activity",
            height = 40,
            width = 40,
            image = "gis_marker.image.Emergency_Teams_S1.png"
        )
        table.insert(
            name = "hospital",
            height = 40,
            width = 40,
            image = "gis_marker.image.E_Med_Hospital_S1.png"
        )
        table.insert(
            name = "earthquake",
            height = 50,
            width = 50,
            image = "gis_marker.image.Geo_Earth_Quake_Epicenter.png"
        )
        table.insert(
            name = "volcano",
            height = 50,
            width = 50,
            image = "gis_marker.image.Geo_Volcanic_Threat.png"
        )
        table.insert(
            name = "tsunami",
            height = 50,
            width = 50,
            image = "gis_marker.image.Hydro_Meteor_Tsunami_ch.png"
        )
        table.insert(
            name = "church",
            height = 33,
            width = 44,
            image = "gis_marker.image.Public_Venue_Church_S1.png"
        )
        table.insert(
            name = "mosque",
            height = 33,
            width = 44,
            image = "gis_marker.image.Public_Venue_Mosque_S1.png"
        )
        table.insert(
            name = "temple",
            height = 33,
            width = 44,
            image = "gis_marker.image.Public_Venue_Temple_S1.png"
        )
        table.insert(
            name = "phone",
            height = 10,
            width = 5,
            image = "gis_marker.image.SMS_Message_Phone.png"
        )
        table.insert(
            name = "orphanage",
            height = 33,
            width = 44,
            image = "gis_marker.image.Special_Needs_Child_Day_Care_S1.png"
        )
        table.insert(
            name = "airport",
            height = 33,
            width = 44,
            image = "gis_marker.image.Trans_Airport_S1.png"
        )
        table.insert(
            name = "bridge",
            height = 33,
            width = 44,
            image = "gis_marker.image.Trans_Bridge_S1.png"
        )
        table.insert(
            name = "helicopter",
            height = 33,
            width = 44,
            image = "gis_marker.image.Trans_Helicopter_Landing_Site_S1.png"
        )
        table.insert(
            name = "port",
            height = 33,
            width = 44,
            image = "gis_marker.image.Trans_Port_S1.png"
        )
        table.insert(
            name = "rail_station",
            height = 33,
            width = 44,
            image = "gis_marker.image.Trans_Rail_Station_S1.png"
        )
        table.insert(
            name = "vehicle",
            height = 50,
            width = 50,
            image = "gis_marker.image.Transport_Vehicle_Theme.png"
        )
        table.insert(
            name = "water",
            height = 33,
            width = 44,
            image = "gis_marker.image.Water_Supply_Infrastructure_Theme_S1.png"
        )
        table.insert(
            name = "volunteer",
            height = 40,
            width = 39,
            image = "gis_marker.image.Volunteer.png"
        )
    tablename = "gis_symbology"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            name = "Australasia"
        )
        table.insert(
            name = "Canada"
        )
        table.insert(
            name = "US"
        )
    tablename = "gis_projection"
    table = db[tablename]
    if not db(table.id > 0).count():
        # We want to start at ID 1, but postgres won't let us truncate() & not needed anyway this is only run on 1st_run.
        #table.truncate()
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-PROJECTION-900913",
            name = "Spherical Mercator",
            epsg = 900913,
            maxExtent = "-20037508, -20037508, 20037508, 20037508.34",
            maxResolution = 156543.0339,
            units = "m"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-PROJECTION-4326",
            name = "WGS84",
            epsg = 4326,
            maxExtent = "-180,-90,180,90",
            maxResolution = 1.40625,
            units = "degrees"
            # OSM use these:
            #maxResolution = 156543.0339,
            #units = "m"
        )

    tablename = "gis_config"
    table = db[tablename]
    # Ensure that the projection/marker we defined are in the DB ready to be used as FKs
    db.commit()
    symbology_us = db(db.gis_symbology.name == "US").select(db.gis_symbology.id, limitby=(0, 1)).first().id
    if not db(table.id > 0).count():
        # We want to start at ID 1, but postgres won't let us truncate() & not needed anyway this is only run on 1st_run.
        #table.truncate()
        table.insert(
            lat = "51.8",
            lon = "-1.3",
            zoom = 7,
            projection_id = 1,
            marker_id = 1,
            map_height = 600,
            map_width = 1000,
            symbology_id = symbology_us,
            wmsbrowser_url = "http://geo.eden.sahanafoundation.org/geoserver/wms?service=WMS&request=GetCapabilities"
        )

    tablename = "gis_feature_class"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-TRACK",
            name = "Track",
            gps_marker = "TracBack Point",
            resource = "gis_track"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L0",
            name = "Country",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L1",
            name = "Province",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L2",
            name = "District",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L3",
            name = "Town",
            gps_marker = "City (Medium)",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-L4",
            name = "Village",
            gps_marker = "City (Small)",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-AIRPORT",
            name = "Airport",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "airport").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Airport",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-BRIDGE",
            name = "Bridge",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "bridge").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Bridge",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-CHURCH",
            name = "Church",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "church").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Church",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-FOOD",
            name = "Food",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "food").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Restaurant",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-HOSPITAL",
            name = "Hospital",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "hospital").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Medical Facility",
            resource = "hms_hospital"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-INCIDENT",
            name = "Incident",
            gps_marker = "Danger Area",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-OFFICE",
            name = "Office",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "office").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Building",
            resource = "org_office"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PERSON",
            name = "Person",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "person").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Contact, Dreadlocks",
            resource = "pr_person"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PORT",
            name = "Port",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "port").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Marina",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-PROJECT",
            name = "Project",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SCHOOL",
            name = "School",
            marker_id = db(db.gis_marker.name == "school").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "School",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SHELTER",
            name = "Shelter",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "shelter").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Campground",
            resource = "cr_shelter"
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-SMS",
            name = "SMS",
            marker_id = db(db.gis_marker.name == "phone").select(db.gis_marker.id, limitby=(0, 1)).first().id,
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-VEHICLE",
            name = "Vehicle",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "vehicle").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Car",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-VOLUNTEER",
            name = "Volunteer",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "volunteer").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Contact, Dreadlocks",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-WAREHOUSE",
            name = "Warehouse",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "office").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Building",
        )
        table.insert(
            uuid = "www.sahanafoundation.org/GIS-FEATURE-CLASS-WATER",
            name = "Water",
            symbology_id = symbology_us,
            marker_id = db(db.gis_marker.name == "water").select(db.gis_marker.id, limitby=(0, 1)).first().id,
            gps_marker = "Drinking Water",
        )
    tablename = "gis_apikey"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            name = "google",
            apikey = "ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw",
            description = "localhost"
        )
        table.insert(
            name = "yahoo",
            apikey = "euzuro-openlayers",
            description = "trial - replace for Production use"
        )
        table.insert(
            name = "multimap",
            apikey = "metacarta_04",
            description = "trial - replace for Production use"
        )
    tablename = "gis_layer_feature"
    table = db[tablename]
    if not db(table.id > 0).count():
        table.insert(
            name = "Incident Reports",
            module = "irs",
            resource = "ireport",
            popup_label = "Incident",
            # Default (but still better to define here as otherwise each feature needs to check it's feature_class)
            marker_id = db(db.gis_marker.name == "marker_red").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Hospitals",
            module = "hms",
            resource = "hospital",
            popup_label = "Hospital",
            marker_id = db(db.gis_marker.name == "hospital").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Shelters",
            module = "cr",
            resource = "shelter",
            popup_label = "Shelter",
            marker_id = db(db.gis_marker.name == "shelter").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Offices",
            module = "org",
            resource = "office",
            popup_label = "Office",
            marker_id = db(db.gis_marker.name == "office").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Requests",
            module = "rms",
            resource = "req",
            popup_label = "Request",
            marker_id = db(db.gis_marker.name == "marker_yellow").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Assessments",
            module = "assess",
            resource = "rat",
            popup_label = "Rapid Assessment",
            marker_id = db(db.gis_marker.name == "marker_green").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Activities",
            module = "project",
            resource = "activity",
            popup_label = "Activity",
            marker_id = db(db.gis_marker.name == "activity").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
        table.insert(
            name = "Warehouses",
            module = "inventory",
            resource = "store",
            popup_label = "Warehouse",
            marker_id = db(db.gis_marker.name == "office").select(db.gis_marker.id, limitby=(0, 1)).first().id
        )
    tablename = "gis_layer_coordinate"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "Coordinate Grid",
                enabled = False,
                visible = False
            )
    tablename = "gis_layer_openstreetmap"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "OpenStreetMap (Mapnik)",
                url1 = "http://a.tile.openstreetmap.org/",
                url2 = "http://b.tile.openstreetmap.org/",
                url3 = "http://c.tile.openstreetmap.org/",
                attribution = '<a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>'
            )
        table.insert(
                name = "OpenStreetMap (CycleMap)",
                url1 = "http://a.tile.opencyclemap.org/cycle/",
                url2 = "http://b.tile.opencyclemap.org/cycle/",
                url3 = "http://c.tile.opencyclemap.org/cycle/",
                attribution = '<a href="http://www.opencyclemap.org/" target="_blank">OpenCycleMap</a>'
            )
        table.insert(
                name = "OpenStreetMap (Labels)",
                url1 = "http://tiler1.censusprofiler.org/labelsonly/",
                attribution = 'Labels overlay CC-by-SA by <a href="http://oobrien.com/oom/" target="_blank">OpenOrienteeringMap</a>/<a href="http://www.openstreetmap.org/">OpenStreetMap</a> data',
                base = False,
                visible = False
            )
        table.insert(
                name = "OpenStreetMap (Relief)",
                url1 = "http://toolserver.org/~cmarqu/hill/",
                attribution = 'Relief by <a href="http://hikebikemap.de/" target="_blank">Hike &amp; Bike Map</a>',
                base = False,
                visible = False
            )
        table.insert(
                name = "OpenStreetMap (MapQuest)",
                url1 = "http://otile1.mqcdn.com/tiles/1.0.0/osm/",
                url2 = "http://otile2.mqcdn.com/tiles/1.0.0/osm/",
                url3 = "http://otile3.mqcdn.com/tiles/1.0.0/osm/",
                attribution = 'Tiles Courtesy of <a href="http://open.mapquest.co.uk/" target="_blank">MapQuest</a> <img src="http://developer.mapquest.com/content/osm/mq_logo.png" border="0">',
                enabled = False
            )
        table.insert(
                name = "OpenStreetMap (Osmarender)",
                url1 = "http://a.tah.openstreetmap.org/Tiles/tile/",
                url2 = "http://b.tah.openstreetmap.org/Tiles/tile/",
                url3 = "http://c.tah.openstreetmap.org/Tiles/tile/",
                attribution = '<a href="http://www.openstreetmap.org/" target="_blank">OpenStreetMap</a>',
                enabled = False
            )
        table.insert(
                name = "OpenStreetMap (Taiwan)",
                url1 = "http://tile.openstreetmap.tw/tiles/",
                enabled = False
            )
        table.insert(
                name = "OpenStreetMap (Sahana)",
                url1 = "http://geo.eden.sahanafoundation.org/tiles/",
                enabled = False
            )
        #table.insert(
        #        name = "OpenAerialMap",
        #        url1 = "http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/",
        #        enabled = False
        #    )
    tablename = "gis_layer_google"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        for subtype in gis_layer_google_subtypes:
            table.insert(
                    name = "Google " + subtype,
                    subtype = subtype,
                    enabled = False
                )
    tablename = "gis_layer_yahoo"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        for subtype in gis_layer_yahoo_subtypes:
            table.insert(
                    name = "Yahoo " + subtype,
                    subtype = subtype,
                    enabled = False
                )
    tablename = "gis_layer_bing"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        for subtype in gis_layer_bing_subtypes:
            table.insert(
                    name = "Bing " + subtype,
                    subtype = subtype,
                    enabled = False
                )
    tablename = "gis_layer_mgrs"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "MGRS Atlas PDFs",
                description = "http://en.wikipedia.org/wiki/Military_grid_reference_system",
                url = "http://www.sharedgeo.org/datasets/shared/maps/usng/pdf.map?VERSION=1.0.0&SERVICE=WFS&request=GetFeature&typename=wfs_all_maps",
                enabled = False
            )
    tablename = "gis_layer_wms"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "VMap0",
                description = "A Free low-resolution Vector Map of the whole world",
                url = "http://labs.metacarta.com/wms/vmap0",
                #projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                layers = "basic",
                enabled = False
            )
        table.insert(
                name = "Blue Marble",
                description = "A composite of four months of MODIS observations with a spatial resolution (level of detail) of 1 square kilometer per pixel.",
                url = "http://maps.opengeo.org/geowebcache/service/wms",
                #projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                layers = "bluemarble",
                enabled = False
            )
    tablename = "gis_layer_georss"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table
        table.insert(
                name = "Earthquakes",
                description = "USGS: Global 7-day",
                url = "http://earthquake.usgs.gov/eqcenter/catalogs/eqs7day-M2.5.xml",
                projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                marker_id = db(db.gis_marker.name == "earthquake").select(limitby=(0, 1)).first().id,
                enabled = False
            )
        table.insert(
                name = "Volcanoes",
                description = "USGS: US recent",
                url = "http://volcano.wr.usgs.gov/rss/vhpcaprss.xml",
                projection_id = db(db.gis_projection.epsg == 4326).select(limitby=(0, 1)).first().id,
                marker_id = db(db.gis_marker.name == "volcano").select(limitby=(0, 1)).first().id,
                enabled = False
            )

    tablename = "gis_wmc_layer"
    table = db[tablename]
    if not db(table.id > 0).count():
        # Populate table with the layers currently-supported by GeoExplorer
        table.insert(
                source = "ol",
                type_ = "OpenLayers.Layer",
                title = "None",
                visibility = False,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "osm",
                name = "mapnik",
                title = "OpenStreetMap",
                visibility = True,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "osm",
                name = "osmarender",
                title = "Tiles@home",
                visibility = False,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "google",
                name = "ROADMAP",
                title = "Google Maps",
                visibility = False,
                opacity = 1,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "google",
                name = "SATELLITE",
                title = "Google Satellite",
                visibility = False,
                opacity = 1,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "google",
                name = "HYBRID",
                title = "Google Hybrid",
                visibility = False,
                opacity = 1,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "google",
                name = "TERRAIN",
                title = "Google Terrain",
                visibility = False,
                opacity = 1,
                group_ = "background",
                fixed = True
            )
        table.insert(
                source = "sahana",
                name = "Pakistan:level3",
                title = "L3: Tehsils",
                visibility = False,
                opacity = 0.74,
                img_format = "image/png",
                styles = "",
                transparent = True
            )
        table.insert(
                source = "sahana",
                name = "Pakistan:pak_flood_17Aug",
                title = "Flood Extent - 17 August",
                visibility = False,
                opacity = 0.45,
                img_format = "image/png",
                styles = "",
                transparent = True
            )

    tablename = "gis_location"
    table = db[tablename]
    if not db(table.id > 0).count():
        # L0 Countries
        import_file = os.path.join(request.folder,
                                   "private", "import",
                                   "countries.csv")
        table.import_from_csv_file(open(import_file, "r"))
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    field = "name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

    # Authorization
    # User Roles (uses native Web2Py Auth Groups)
    acl = auth.permission
    table = auth.settings.table_group_name
    if not db(db[table].id > 0).count():
        create_role = auth.s3_create_role
        # Do not remove or change order of these 5 definitions (System Roles):
        create_role("Administrator", "System Administrator - can access & make changes to any data")
        create_role("Authenticated", "Authenticated - all logged-in users",
                    dict(c="gis", uacl=acl.ALL, oacl=acl.ALL),
                    dict(c="gis", f="location", uacl=acl.READ, oacl=acl.ALL),
                    dict(c="org", uacl=acl.READ, oacl=acl.ALL),
                    dict(c="inv", uacl=acl.READ, oacl=acl.ALL),       
                    dict(c="req", uacl=acl.READ, oacl=acl.ALL),               
                    )
        create_role("Anonymous", "Unauthenticated users",
                    dict(c="gis", uacl=acl.READ, oacl=acl.READ))
        create_role("Editor", "Editor - can access & make changes to any unprotected data")
        create_role("MapAdmin", "MapAdmin - allowed access to edit the MapService Catalogue",
                    dict(c="gis", uacl=acl.ALL, oacl=acl.ALL),
                    dict(c="gis", f="location", uacl=acl.ALL, oacl=acl.ALL))

        # Additional roles + ACLs
        create_role("DVI", "Role for DVI staff - permission to access the DVI module",
                    dict(c="dvi", uacl=acl.ALL, oacl=acl.ALL))
        create_role("HMS Staff", "Hospital Staff - permission to add/update own records in the HMS",
                    dict(c="hms", uacl=acl.CREATE, oacl=acl.ALL))
        create_role("HMS Admin", "Hospital Admin - permission to add/update all records in the HMS",
                    dict(c="hms", uacl=acl.ALL, oacl=acl.ALL))


    # Security Defaults for all tables (if using 'full' security policy: i.e. native Web2Py)
    if session.s3.security_policy not in (1, 2, 3, 4, 5):
        table = auth.settings.table_permission_name
        if not db(db[table].id > 0).count():
            # For performance we only populate this once (at system startup)
            # => need to populate manually when adding new tables to the database! (less RAD)
            authenticated = auth.id_group("Authenticated")
            editors = auth.id_group("Editor")
            for tablename in db.tables:
                table = db[tablename]
                # allow all registered users the ability to Read all records
                auth.add_permission(authenticated, "read", table)
                # allow anonymous users the ability to Read all records
                #auth.add_permission(anonymous, "read", table)
                # Editors can make changes
                auth.add_permission(editors, "create", table)
                auth.add_permission(editors, "update", table)
                auth.add_permission(editors, "delete", table)

            # Module-specific defaults can be set here
            #table = pr_person
            # Clear out defaults
            #auth.del_permission(authenticated, "read", table)
            #auth.del_permission(editors, "create", table)
            #auth.del_permission(editors, "update", table)
            #auth.del_permission(editors, "delete", table)
            # Add specific Role(s)
            #id = auth.id_group("myrole")
            #auth.add_permission(id, "read", table)
            #auth.add_permission(id, "create", table)
            #auth.add_permission(id, "update", table)
            #auth.add_permission(id, "delete", table)

    # Ensure DB population committed when running through shell
    db.commit()
