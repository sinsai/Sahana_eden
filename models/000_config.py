# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
"""

s3cfg = local_import("s3cfg")
deployment_settings = s3cfg.S3Config()

# Database settings
deployment_settings.database.db_type = "sqlite"
deployment_settings.database.host = "localhost"
deployment_settings.database.port = "" # use default
deployment_settings.database.database = "sahana"
deployment_settings.database.username = "sahana"
deployment_settings.database.password = "password"
deployment_settings.database.pool_size = 30

# Authentication settings
# This setting should be changed _before_ registering the 1st user
deployment_settings.auth.hmac_key = "akeytochange"
# These settings should be changed _after_ the 1st (admin) user is
# registered in order to secure the deployment
deployment_settings.auth.registration_requires_verification = False
deployment_settings.auth.registration_requires_approval = False

# Base settings
# Set this to the Public URL of the instance
deployment_settings.base.public_url = "http://127.0.0.1:8000"

# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when Table definitions are changed)
deployment_settings.base.migrate = True

# Enable/disable pre-population of the database.
# Set to False during first run for manual DB migration in case this
# is explicitly required for a code upgrade, otherwise leave at True
# NOTE: the web UI will not be accessible while the DB is empty,
# instead run:
#   python web2py.py -S eden -M
# to create the db structure, then exit and re-import the data.
deployment_settings.base.prepopulate = True


# Email settings
# Outbound server
deployment_settings.mail.server = "127.0.0.1:25"
# From Address
deployment_settings.mail.sender = "sahana@your.org"
# Address to which mails get sent to approve new users
deployment_settings.mail.approver = "useradmin@your.org"


# L10n settings
# Default timezone for users
deployment_settings.L10n.utc_offset = "UTC +0000"

# Module settings
s3_module_type_opts = {
    1:T("Home"),
    2:T("Situation Awareness"),
    3:T("Person Management"),
    4:T("Aid Management"),
    5:T("Communications")
    }
# Comment/uncomment modules here to disable/enable them
# Modules menu is defined in 01_menu.py
from gluon.storage import Storage
deployment_settings.modules = Storage(
    default = Storage(
            name_nice = "Home",
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = 0,     # This item is always 1st in the menu
            
            ),
    admin = Storage(
            name_nice = "Administration",
            description = "Site Administration",
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = 0,     # This item is handled separately in the menu
            resources = [
            ]
            
        ),
    gis = Storage(
            name_nice = "Map",
            description = "Situation Awareness & Geospatial Analysis",
            module_type = 1,     # 1st item in the menu
            resources = [
                 'gis_setting',
	         'gis_marker',
		 'gis_projection',
		 'gis_symbology',
		 'gis_config',
		 'gis_feature_class',
		 'gis_symbology_to_feature_class',
		 'gis_location',
		 'gis_landmark',
		 'gis_feature_layer',
		 'gis_feature_group',
		 'gis_feature_class_to_feature_group',
		 'gis_apikey',
		 'gis_track',
		 'gis_layer_openstreetmap',
		 'gis_layer_georss',
		 'gis_layer_google',
		 'gis_layer_gpx',
		 'gis_layer_js',
		 'gis_layer_kml',
		 'gis_layer_mgrs',
		 'gis_layer_tms',
		 'gis_layer_wms',
		 'gis_layer_xyz',
		 'gis_layer_yahoo',
		 ]
        ),
    mpr = Storage(
            name_nice = "Missing Persons",
            description = "Helps to report and search for Missing Persons",
            module_type = 2,
            resources = [
             'mpr_setting',
 	     'mpr_missing_report'
 	     ]
        ),
    rms = Storage(
            name_nice = "Requests",
            description = "Tracks requests for aid and matches them against donors who have pledged aid",
            module_type = 3,
            resources = [
             'rms_setting',
 	     'rms_req',
	     'rms_pledge',
	     'rms_req_detail'
	     ]
        ),
    hms = Storage(
            name_nice = "Hospitals",
            description = "Helps to monitor status of hospitals",
            module_type = 4,
            resources = Storage(
             hms_setting={},
 	     hms_hospital = {'importer' : True},
 	     hms_hcontact = {},
 	     hms_hactivity = {},
             hms_bed_capacity = {},
	     hms_services = {},
	     hms_himage = {},
	     hms_resources = {},
	     hms_hrequest = {'importer' : True},
	     hms_hpledge = {'importer' : True}
	     )
        ),
    vol = Storage(
            name_nice = "Volunteers",
            description = "Manage volunteers by capturing their skills, availability and allocation",
            module_type = 5,
            rsources = Storage(
             vol_setting = {},
 	     vol_volunteer = {},
 	     vol_resource = {}
 	     )
        ),
    msg = Storage(
            name_nice = "Messaging",
            description = "Sends & Receives Alerts via Email & SMS",
            module_type = 10,
            resources = [
             'msg_setting',
 	     'msg_email_settings',
 	     'msg_email_inbound_status',
 	     'msg_xforms_store',
 	     'msg_modem_settings',
 	     'msg_gateway_settings',
 	     'msg_log',
 	     'msg_tag',
 	     'msg_outbox',
 	     'msg_read_status',
 	     'msg_report'
 	     ]
        ),
    pr = Storage(
            name_nice = "Person Registry",
            description = "Central point to record details on People",
            module_type = 10,
            resources = Storage(
                 pr_address = {},
 		 pr_pe_contact = {},
		 pr_image = {},
		 pr_presence = {'importer' : True},
	 	 pr_pe_subscription = {},
 		 pr_identity = {},
 		 pr_pd_general  = {},
 		 pr_pd_head  = {},
 		 pr_pd_face = {},
 		 pr_pd_teeth = {},
 		 pr_pd_body = {},
 		 pr_setting = {},
 		 pr_pentity = {},
 		 pr_person = {'importer' : True},
 		 pr_group = {'importer' : True},
        	 pr_group_membership = {'importer' : True},
 		)

        ),
    dvi = Storage(
            name_nice = "Disaster Victim Identification",
            description = "Disaster Victim Identification",
            module_type = 10,
            resources = Storage(
              dvi_setting = {},
 	      dvi_recreq = {'importer' : True},
  	      dvi_body = {},
 	      dvi_checklist = {},
 	      dvi_effects = {},
	      dvi_identification = {}
	     )
        ),
    #dvr = Storage(
    #        name_nice = "Disaster Victim Registry",
    #        description = "Traces internally displaced people (IDPs) and their needs",
    #        module_type = 10
    #    ),
    #nim = Storage(
    #        name_nice = "Nursing Information Manager",
    #        description = "Module to assist disaster nurses.",
    #        module_type = 10
    #    ),
    budget = Storage(
            name_nice = "Budgeting Module",
            description = "Allows a Budget to be drawn up",
            module_type = 10,
            resources = Storage(
              budget_setting = {},
 	      budget_parameter = {'importer' : True},
 	      budget_item = {'importer' : True},
 	      budget_kit = {'importer' : True},
 	      budget_kit_item = {},
 	      budget_bundle = {'importer' : True},
	      budget_bundle_kit = {},
	      budget_bundle_item = {},
	      budget_staff = {},
 	      budget_location = {},
 	      budget_budget = {},
 	      budget_budget_bundle = {},
 	      budget_budget_staff = {}
 	     )
        ),
    cr = Storage(
            name_nice = "Shelter Registry",
            description = "Tracks the location, distibution, capacity and breakdown of victims in Shelters",
            module_type = 10,
            resource = Storage(
              cr_setting = {},
 	     cr_shelter = {'importer' : True }
 	    )
        ),
    delphi = Storage(
            name_nice = "Delphi Decision Maker",
            description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            module_type = 10,
            resources = Storage(
              delphi_group = {},
              delphi_user_to_group = {},
 	      delphi_problem = {},
 	      delphi_solution = {},
     	      delphi_vote = {},
 	      delphi_forum_post = {}
 	     )
        ),
    doc = Storage(
            name_nice = "Document Library",
            description = "A library of digital resources, such as Photos, signed contracts and Office documents.",
            module_type = 10,
            resources = Storage(
            	  doc_setting = {},
		  doc_metadata = {'importer' : True},
		  doc_image = {},
		 )
        ),
    org = Storage(
            name_nice = "Organization Registry",
            description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            module_type = 10,
            resources = Storage(
        	  org_setting = {},
	 	  org_sector = {},
		  org_organisation = {'importer' : True},
		  org_office = {'importer' : True},
		  org_project = {'importer' : True},
		  org_staff = {'importer' : True},
		  org_task = {'importer' : True}
		 )
        ),
    ticket = Storage(
            name_nice = "Ticketing Module",
            description = "Master Message Log to process incoming reports & requests",
            module_type = 10,
            resources = Storage(
              ticket_setting = {'importer' : False},
 	      ticket_category = {'importer' : False},
	      ticket_log = {'importer' : False},
	     )
        ),
    importer = Storage(
    	     name_nice = "Spreadsheet importer",
    	     description = "Used to extract data from spreadsheets and input it to the Eden database",
    	     module_type = 5,
    	     resources = Storage(
    	      importer_slist = {'importer' : True}
    	     )
    )
    )
