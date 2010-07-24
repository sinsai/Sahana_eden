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
            resources = Storage()
            
        ),
    gis = Storage(
            name_nice = "Map",
            description = "Situation Awareness & Geospatial Analysis",
            module_type = 1,     # 1st item in the menu
            resources = Storage(
                  gis_setting = {'importer' : False},
	          gis_marker = {'importer' : False},
		  gis_projection = {'importer' : True},
		  gis_symbology = {'importer' : False},
		  gis_config = {'importer' : False},
		  gis_feature_class = {'importer' : False},
		  gis_symbology_to_feature_class = {'importer' : False},
		  gis_location = {'importer' : True},
		  gis_landmark = {'importer' : False},
		  gis_feature_layer = {'importer' : False},
		  gis_feature_group = {'importer' : False},
		  gis_feature_class_to_feature_group = {'importer' : False},
		  gis_apikey = {'importer' : False},
		  gis_track = {'importer' : False},
		  gis_layer_openstreetmap = {'importer' : False},
		  gis_layer_georss = {'importer' : False},
		  gis_layer_google = {'importer' : False},
		  gis_layer_gpx = {'importer' : False},
		  gis_layer_js = {'importer' : False},
		  gis_layer_kml = {'importer' : False},
		  gis_layer_mgrs = {'importer' : False},
		  gis_layer_tms = {'importer' : False},
		  gis_layer_wms = {'importer' : False},
		  gis_layer_xyz = {'importer' : False},
		  gis_layer_yahoo = {'importer' : False}
		 )
        ),
    mpr = Storage(
            name_nice = "Missing Persons",
            description = "Helps to report and search for Missing Persons",
            module_type = 2,
            resources = Storage(
              mpr_setting = {'importer' : False},
 	      mpr_missing_report = {'importer' : False}
 	     )
        ),
    rms = Storage(
            name_nice = "Requests",
            description = "Tracks requests for aid and matches them against donors who have pledged aid",
            module_type = 3,
            resources = Storage(
              rms_setting = {'importer' : False},
  	      rms_req = {'importer' : True},
	      rms_pledge = {'importer' : False},
	      rms_req_detail = {'importer' : False}
	     )
        ),
    hms = Storage(
            name_nice = "Hospitals",
            description = "Helps to monitor status of hospitals",
            module_type = 4,
            resources = Storage(
             hms_setting={'importer' : False},
 	     hms_hospital = {'importer' : True},
 	     hms_hcontact = {'importer' : False},
 	     hms_hactivity = {'importer' : False},
             hms_bed_capacity = {'importer' : False},
	     hms_services = {'importer' : False},
	     hms_himage = {'importer' : False},
	     hms_resources = {'importer' : False},
	     hms_hrequest = {'importer' : True},
	     hms_hpledge = {'importer' : True}
	     )
        ),
    vol = Storage(
            name_nice = "Volunteers",
            description = "Manage volunteers by capturing their skills, availability and allocation",
            module_type = 5,
            rsources = Storage(
             vol_setting = {'importer' : False},
 	     vol_volunteer = {'importer' : False},
 	     vol_resource = {'importer' : False}
 	     )
        ),
    msg = Storage(
            name_nice = "Messaging",
            description = "Sends & Receives Alerts via Email & SMS",
            module_type = 10,
            resources = Storage(
              msg_setting = {'importer' : False},
 	      msg_email_settings = {'importer' : False},
 	      msg_email_inbound_status = {'importer' : False},
 	      msg_xforms_store = {'importer' : False},
 	      msg_modem_settings = {'importer' : False},
 	      msg_gateway_settings = {'importer' : False},
 	      msg_log = {'importer' : False},
 	      msg_tag = {'importer' : False},
 	      msg_outbox = {'importer' : False},
 	      msg_read_status = {'importer' : False},
 	      msg_report = {'importer' : False}
 	     )
        ),
    pr = Storage(
            name_nice = "Person Registry",
            description = "Central point to record details on People",
            module_type = 10,
            resources = Storage(
                 pr_address = {'importer' : True},
 		 pr_pe_contact = {'importer' : True},
		 pr_image = {'importer' : False},
		 pr_presence = {'importer' : True},
	 	 pr_pe_subscription = {'importer' : False},
 		 pr_identity = {'importer' : True},
 		 pr_pd_general  = {'importer' : False},
 		 pr_pd_head  = {'importer' : False},
 		 pr_pd_face = {'importer' : False},
 		 pr_pd_teeth = {'importer' : False},
 		 pr_pd_body = {'importer' : False},
 		 pr_setting = {'importer' : False},
 		 pr_pentity = {'importer' : False},
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
              dvi_setting = {'importer' : False},
 	      dvi_recreq = {'importer' : True},
  	      dvi_body = {'importer' : False},
 	      dvi_checklist = {'importer' : False},
 	      dvi_effects = {'importer' : False},
	      dvi_identification = {'importer' : False}
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
              budget_setting = {'importer' : False},
 	      budget_parameter = {'importer' : True},
 	      budget_item = {'importer' : True},
 	      budget_kit = {'importer' : True},
 	      budget_kit_item = {'importer' : False},
 	      budget_bundle = {'importer' : True},
	      budget_bundle_kit = {'importer' : False},
	      budget_bundle_item = {'importer' : False},
	      budget_staff = {'importer' : False},
 	      budget_location = {'importer' : False},
 	      budget_budget = {'importer' : False},
 	      budget_budget_bundle = {'importer' : False},
 	      budget_budget_staff = {'importer' : False}
 	     )
        ),
    cr = Storage(
            name_nice = "Shelter Registry",
            description = "Tracks the location, distibution, capacity and breakdown of victims in Shelters",
            module_type = 10,
            resource = Storage(
              cr_setting = {'importer' : False},
 	     cr_shelter = {'importer' : True }
 	    )
        ),
    delphi = Storage(
            name_nice = "Delphi Decision Maker",
            description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            module_type = 10,
            resources = Storage(
              delphi_group = {'importer' : True},
              delphi_user_to_group = {'importer' : True},
 	      delphi_problem = {'importer' : True},
 	      delphi_solution = {'importer' : False},
     	      delphi_vote = {'importer' : False},
 	      delphi_forum_post = {'importer' : False}
 	     )
        ),
    doc = Storage(
            name_nice = "Document Library",
            description = "A library of digital resources, such as Photos, signed contracts and Office documents.",
            module_type = 10,
            resources = Storage(
            	  doc_setting = {'importer' : False},
		  doc_metadata = {'importer' : True},
		  doc_image = {'importer' : False},
		 )
        ),
    org = Storage(
            name_nice = "Organization Registry",
            description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            module_type = 10,
            resources = Storage(
        	  org_setting = {'importer' : False},
	 	  org_sector = {'importer' : False},
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
