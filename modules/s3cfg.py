# -*- coding: utf-8 -*-

from gluon.storage import Storage

class S3Config(Storage):

    def __init__(self):
        self.auth = Storage()
        self.base = Storage()
        self.mail = Storage()
        self.L10n = Storage()

    # Auth settings
    def get_auth_hmac_key(self):
        return self.auth.get("hmac_key", "akeytochange")
    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)
    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)

    # Base settings
    def get_base_public_url(self):
        return self.base.get("public_url", "http://127.0.0.1:8000")
    def get_base_migrate(self):
        return self.base.get("migrate", True)

    # Mail settings
    def get_mail_server(self):
        return self.mail.get("server", "127.0.0.1:25")
    def get_mail_sender(self):
        return self.mail.get("sender", "sahana@your.org")
    def get_mail_approver(self):
        return self.mail.get("approver", "useradmin@your.org")

    # L10N Settings
    def get_L10n_utc_offset(self):
        return self.L10n.get("utc_offset", "UTC +0000")

    # Active modules list
    def get_modules(self):
        return self.get(modules, [
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
        ])
