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
            name_nice = "Sahana Home",
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = 1     # Used to locate the module in the default menu
        ),
    admin = Storage(
            name_nice = "Administration",
            description = "Site Administration",
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = 1
        ),
    gis = Storage(
            name_nice = "Mapping",
            description = "Situation Awareness & Geospatial Analysis",
            module_type = 2
        ),
    pr = Storage(
            name_nice = "Person Registry",
            description = "Central point to record details on People",
            module_type = 3
        ),
    mpr = Storage(
            name_nice = "Missing Persons Registry",
            description = "Helps to report and search for Missing Persons",
            module_type = 3
        ),
    dvi = Storage(
            name_nice = "Disaster Victim Identification",
            description = "Disaster Victim Identification",
            module_type = 3,
        ),
    #dvr = Storage(
    #        name_nice = "Disaster Victim Registry",
    #        description = "Traces internally displaced people (IDPs) and their needs",
    #        module_type = 3
    #    ),
    #nim = Storage(
    #        name_nice = "Nursing Information Manager",
    #        description = "Module to assist disaster nurses.",
    #        module_type = 3
    #    ),
    budget = Storage(
            name_nice = "Budgeting Module",
            description = "Allows a Budget to be drawn up",
            module_type = 4
        ),
    cr = Storage(
            name_nice = "Shelter Registry",
            description = "Tracks the location, distibution, capacity and breakdown of victims in Shelters",
            module_type = 4,
        ),
    delphi = Storage(
            name_nice = "Delphi Decision Maker",
            description = "Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
            module_type = 4
        ),
    hms = Storage(
            name_nice = "Hospital Management",
            description = "Helps to monitor status of hospitals",
            module_type = 4
        ),
    media = Storage(
            name_nice = "Media Manager",
            description = "A library of digital resources, such as Photos.",
            module_type = 4
        ),
    org = Storage(
            name_nice = "Organization Registry",
            description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            module_type = 4
        ),
    rms = Storage(
            name_nice = "Request Management",
            description = "Tracks requests for aid and matches them against donors who have pledged aid",
            module_type = 4
        ),
    ticket = Storage(
            name_nice = "Ticketing Module",
            description = "Master Message Log to process incoming reports & requests",
            module_type = 4
        ),
    vol = Storage(
            name_nice = "Volunteer Registry",
            description = "Manage volunteers by capturing their skills, availability and allocation",
            module_type = 4
        ),
    #hrm = Storage(
    #        name_nice = "Human Resources",
    #        description = "Helps to manage human resources",
    #        module_type = 4
    #    ),
    #lms = Storage(
    #        name_nice = "Logistics Management System",
    #        description = "An intake system, a warehouse management system, commodity tracking, supply chain management, procurement and other asset and resource management capabilities.",
    #        module_type = 4
    #    ),
    msg = Storage(
            name_nice = "Messaging Module",
            description = "Sends & Receives Alerts via Email & SMS",
            module_type = 5
        ),
    importer = Storage(
    	     name_nice = "Spreadsheet importer",
    	     description = "Used to extract data from spreadsheets and input it to the Eden database",
    	     module_type = 5)
)
