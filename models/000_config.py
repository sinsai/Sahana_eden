# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
"""

def Tstr(text):
    """Convenience function for non web2py modules"""
    return str(T(text))

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
deployment_settings.auth.openid = False

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
# Useful for Windows Laptops:
#deployment_settings.mail.server = "smtp.gmail.com:587"
#deployment_settings.mail.login = "username:password"
# From Address
deployment_settings.mail.sender = "sahana@your.org"
# Address to which mails get sent to approve new users
deployment_settings.mail.approver = "useradmin@your.org"


# L10n settings
# Default timezone for users
deployment_settings.L10n.utc_offset = "UTC +0000"

# Comment/uncomment modules here to disable/enable them
# Modules menu is defined in 01_menu.py
from gluon.storage import Storage
deployment_settings.modules = Storage(
    default = Storage(
            name_nice = Tstr("Home"),
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = 0     # This item is always 1st in the menu
        ),
    admin = Storage(
            name_nice = Tstr("Administration"),
            description = Tstr("Site Administration"),
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = 0     # This item is handled separately in the menu
        ),
    gis = Storage(
            name_nice = Tstr("Map"),
            description = Tstr("Situation Awareness & Geospatial Analysis"),
            module_type = 1     # 1st item in the menu
        ),
    mpr = Storage(
            name_nice = Tstr("Missing Persons"),
            description = Tstr("Helps to report and search for Missing Persons"),
            module_type = 2
        ),
    rms = Storage(
            name_nice = Tstr("Requests"),
            description = Tstr("Tracks requests for aid and matches them against donors who have pledged aid"),
            module_type = 3
        ),
    hms = Storage(
            name_nice = Tstr("Hospitals"),
            description = Tstr("Helps to monitor status of hospitals"),
            module_type = 4
        ),
    vol = Storage(
            name_nice = Tstr("Volunteers"),
            description = Tstr("Manage volunteers by capturing their skills, availability and allocation"),
            module_type = 5
        ),
    msg = Storage(
            name_nice = Tstr("Messaging"),
            description = Tstr("Sends & Receives Alerts via Email & SMS"),
            module_type = 10
        ),
    sitrep = Storage(
            name_nice = Tstr("Situation Reports"),
            description = Tstr("Assessments & Flood Reports"),
            module_type = 10
        ),
    pr = Storage(
            name_nice = Tstr("Person Registry"),
            description = Tstr("Central point to record details on People"),
            module_type = 10
        ),
    dvi = Storage(
            name_nice = Tstr("Disaster Victim Identification"),
            description = Tstr("Disaster Victim Identification"),
            module_type = 10,
        ),
    #dvr = Storage(
    #        name_nice = Tstr("Disaster Victim Registry"),
    #        description = Tstr("Traces internally displaced people (IDPs) and their needs"),
    #        module_type = 10
    #    ),
    budget = Storage(
            name_nice = Tstr("Budgeting Module"),
            description = Tstr("Allows a Budget to be drawn up"),
            module_type = 10
        ),
    cr = Storage(
            name_nice = Tstr("Shelter Registry"),
            description = Tstr("Tracks the location, distibution, capacity and breakdown of victims in Shelters"),
            module_type = 10,
        ),
    delphi = Storage(
            name_nice = Tstr("Delphi Decision Maker"),
            description = Tstr("Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list."),
            module_type = 10
        ),
    doc = Storage(
            name_nice = Tstr("Document Library"),
            description = Tstr("A library of digital resources, such as Photos, signed contracts and Office documents."),
            module_type = 10
        ),
    irs = Storage(
        name_nice = Tstr("Incident Reporting"),
        description = Tstr("Incident Reporting System"),
        module_type = 10
    ),
    org = Storage(
            name_nice = Tstr("Organization Registry"),
            description = Tstr('Lists "who is doing what & where". Allows relief agencies to coordinate their activities'),
            module_type = 10
        ),
    ticket = Storage(
            name_nice = Tstr("Ticketing Module"),
            description = Tstr("Master Message Log to process incoming reports & requests"),
            module_type = 10
        ),
    #lms = Storage(
    #        name_nice = Tstr("Logistics Management System"),
    #        description = Tstr("An intake system, a warehouse management system, commodity tracking, supply chain management, procurement and other asset and resource management capabilities."),
    #        module_type = 10
    #    ),
)