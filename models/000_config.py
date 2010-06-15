# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
"""

s3cfg = local_import("s3cfg")
deployment_settings = s3cfg.S3Config()

# Database settings
deployment_settings.database.db_type = "mysql"
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
# Comment/uncomment modules here to disable/enable them
deployment_settings.modules = [
    "gis",          # GIS
    "media",        # Media Manager
    "pr",           # Person Registry
    "or",           # Organisation Registry
    "budget",       # Budgetting
    "cr",           # Camp Registry
    "delphi",       # Delphi Decision Maker
    "dvi",          # Disaster Victim Identification
    #"dvr",         # Disaster Victim Registry
    "hms",          # Hospital Management
    #"hrm",         # Human Resources Management
    #"lms",         # Logistics
    "mpr",          # Missing Person Registry
    "msg",          # Messaging
    #"nim",         # Nursing Information Manager
    "rms",          # Request Management
    "ticket",       # Ticketing
    "vol"           # Volunteer Management
]
