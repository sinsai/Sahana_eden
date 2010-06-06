# -*- coding: utf-8 -*-

"""
    Deployment settings
    All settings which are typically edited for a deployment should be done here
    Deployers shouldn't typically need to edit any other files.
"""

from gluon.storage import Storage
deployment_settings = Storage()

# Authentication settings
deployment_settings.auth = Storage()

# This setting should be changed _before_ registering the 1st user
deployment_settings.auth.hmac_key = "akeytochange"

# These settings should be changed _after_ the 1st (admin) user is registered in order to secure the deployment
deployment_settings.auth.registration_requires_verification = False
deployment_settings.auth.registration_requires_approval = False

# Base settings
deployment_settings.base = Storage()

# Set this to the Public URL of the instance
deployment_settings.base.public_url = "http://127.0.0.1:8000"

# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when Table definitions are changed)
deployment_settings.base.migrate = True

# Email settings
deployment_settings.mail = Storage()

# Outbound server
deployment_settings.mail.server = "127.0.0.1:25"
# From Address
deployment_settings.mail.sender = "sahana@your.org"
# Address to which mails get sent to approve new users
deployment_settings.mail.approver = "useradmin@your.org"

# L10n settings
deployment_settings.L10n = Storage()

# Default timezone for users
deployment_settings.L10n.utc_offset = "UTC +0000"

