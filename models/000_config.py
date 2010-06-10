# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
"""

s3cfg = local_import("s3cfg")
deployment_settings = s3cfg.S3Config()

# Authentication settings
# This setting should be changed _before_ registering the 1st user
deployment_settings.auth.hmac_key = "akeytochange"
# These settings should be changed _after_ the 1st (admin) user is registered in order to secure the deployment
deployment_settings.auth.registration_requires_verification = False
deployment_settings.auth.registration_requires_approval = False


# Base settings
# Set this to the Public URL of the instance
deployment_settings.base.public_url = "http://127.0.0.1:8000"
# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when Table definitions are changed)
deployment_settings.base.migrate = True


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

#########################################################################################

# Typically you wont need to change the following settings.
# If you donot understand any of the following setting - It probably doesnt need a change

#########################################################################################

# Sysadmin maintenance and upgrade settings

# Control auto import of default data 

# Warning use the following only if 
# 1) You have a sql dump of the data 
# 2) You are aware of the schema changes if the code was updated after the above SQL dump was taken.
# 3) Wish to prevent zzz_1st run from running.
# The web UI is not accessible if you have an empty database - Run via 
# python web2py.py -S eden -M
# and exit to create the db structure


deployment_settings.maintenance.zzz_1st_run_disable = False

