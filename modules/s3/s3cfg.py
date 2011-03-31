# -*- coding: utf-8 -*-

""" Deployment Settings

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__all__ = ["S3Config"]

from gluon.http import HTTP
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict

class S3Config(Storage):

    """
        Deployment Settings Helper Class
    """

    def __init__(self, T):
        self.auth = Storage()
        self.base = Storage()
        self.database = Storage()
        self.frontpage = Storage()
        self.frontpage.rss = []
        self.gis = Storage()
        self.mail = Storage()
        self.twitter = Storage()
        self.L10n = Storage()
        self.options = Storage()
        self.osm = Storage()
        self.security = Storage()
        self.aaa = Storage()
        self.ui = Storage()
        self.req = Storage()
        self.T = T  
        # These are copied from modules/s3/s3aaa.py
        self.aaa.acl =  Storage(CREATE = 0x0001,
                                READ   = 0x0002,
                                UPDATE = 0x0004,
                                DELETE = 0x0008,
                                ALL = 0x000F    # CREATE | READ | UPDATE | DELETE
                                )

    # Auth settings
    def get_auth_hmac_key(self):
        return self.auth.get("hmac_key", "akeytochange")
    def get_auth_openid(self):
        return self.auth.get("openid", False)
    def get_auth_registration_requires_verification(self):
        return self.auth.get("registration_requires_verification", False)
    def get_auth_registration_requires_approval(self):
        return self.auth.get("registration_requires_approval", False)
    def get_auth_registration_requests_mobile_phone(self):
        return self.auth.get("registration_requests_mobile_phone", True)
    def get_auth_registration_requests_organisation(self):
        return self.auth.get("registration_requests_organisation", False)

    # Base settings
    def get_base_debug(self):
        return self.base.get("debug", False)
    def get_base_migrate(self):
        return self.base.get("migrate", True)
    def get_base_prepopulate(self):
        return self.base.get("prepopulate", True)
    def get_base_public_url(self):
        return self.base.get("public_url", "http://127.0.0.1:8000")
    def get_base_cdn(self):
        return self.base.get("cdn", False)

    # Database settings
    def get_database_string(self):
        db_type = self.database.get("db_type", "sqlite")
        pool_size = self.database.get("pool_size", 0)
        if (db_type == "sqlite"):
            db_string = "sqlite://storage.db"
        elif (db_type == "mysql"):
            db_string = "mysql://%s:%s@%s:%s/%s" % \
                        (self.database.get("username", "sahana"),
                         self.database.get("password", "password"),
                         self.database.get("host", "localhost"),
                         self.database.get("port", None) or "3306",
                         self.database.get("database", "sahana"))
        elif (db_type == "postgres"):
            db_string = "postgres://%s:%s@%s:%s/%s" % \
                        (self.database.get("username", "sahana"),
                         self.database.get("password", "password"),
                         self.database.get("host", "localhost"),
                         self.database.get("port", None) or "5432",
                         self.database.get("database", "sahana"))
        else:
            raise HTTP(501, body="Database type '%s' not recognised - please correct file models/000_config.py." % db_type)
        if pool_size:
            return (db_string, pool_size)
        else:
            return db_string

    # GIS (Map) Settings
    # Which countries the deployment cover (used in GIS Location Selector)
    def get_gis_countries(self):
        countries = self.gis.get("countries", "")
        if not countries:
            # Backwards-compatibility for old 000_config
            countries = self.L10n.get("countries", "")
        return countries

    def get_gis_map_selector(self):
        return self.gis.get("map_selector", True)
    def get_gis_display_l0(self):
        return self.gis.get("display_L0", False)
    def get_gis_display_l1(self):
        return self.gis.get("display_L1", True)
    def get_gis_duplicate_features(self):
        return self.gis.get("duplicate_features", False)
    def get_gis_edit_l0(self):
        return self.gis.get("edit_L0", False)
    def get_gis_edit_l1(self):
        return self.gis.get("edit_L1", True)
    def get_gis_edit_l2(self):
        return self.gis.get("edit_L2", True)
    def get_gis_edit_l3(self):
        return self.gis.get("edit_L3", True)
    def get_gis_edit_l4(self):
        return self.gis.get("edit_L4", True)
    def get_gis_edit_l5(self):
        return self.gis.get("edit_L5", True)
    def get_gis_edit_group(self):
        return self.gis.get("edit_GR", False)
    def get_gis_marker_max_height(self):
        return self.gis.get("marker_max_height", 35)
    def get_gis_marker_max_width(self):
        return self.gis.get("marker_max_width", 30)
    def get_gis_mouse_position(self):
        return self.gis.get("mouse_position", "normal")
    def get_gis_print_service(self):
        return self.gis.get("print_service", "")
    def get_gis_geoserver_url(self):
        return self.gis.get("geoserver_url", "")
    def get_gis_geoserver_username(self):
        return self.gis.get("geoserver_username", "admin")
    def get_gis_geoserver_password(self):
        return self.gis.get("geoserver_password", "password")
    def get_gis_spatialdb(self):
        return self.gis.get("spatialdb", False)

    # OpenStreetMap settings
    def get_osm_oauth_consumer_key(self):
        return self.osm.get("oauth_consumer_key", "")
    def get_osm_oauth_consumer_secret(self):
        return self.osm.get("oauth_consumer_secret", "")

    # Twitter settings
    def get_twitter_oauth_consumer_key(self):
        return self.twitter.get("oauth_consumer_key", "")
    def get_twitter_oauth_consumer_secret(self):
        return self.twitter.get("oauth_consumer_secret", "")

    # L10N Settings
    def get_L10n_default_country_code(self):
        return self.L10n.get("default_country_code", 1)
    def get_L10n_default_language(self):
        return self.L10n.get("default_language", "en")
    def get_L10n_display_toolbar(self):
        return self.L10n.get("display_toolbar", True)
    def get_L10n_languages(self):
        return self.L10n.get("languages", { "en":self.T("English") })
    def get_L10n_religions(self):
        return self.L10n.get("religions", { "none":self.T("None"), "other":self.T("Other") })
    def get_L10n_utc_offset(self):
        return self.L10n.get("utc_offset", "UTC +0000")

    # Mail settings
    def get_mail_server(self):
        return self.mail.get("server", "127.0.0.1:25")
    def get_mail_server_login(self):
        return self.mail.get("login", False)
    def get_mail_sender(self):
        return self.mail.get("sender", "sahana@your.org")
    def get_mail_approver(self):
        return self.mail.get("approver", "useradmin@your.org")

    # Security Settings
    def get_security_archive_not_delete(self):
        return self.security.get("archive_not_delete", True)
    def get_security_audit_read(self):
        return self.security.get("audit_read", False)
    def get_security_audit_write(self):
        return self.security.get("audit_write", False)
    def get_security_policy(self):
        return self.security.get("policy", 1)
    def get_security_map(self):
        return self.security.get("map", False)
    def get_security_self_registration(self):
        return self.security.get("self_registration", True)
    
    # AAA Settings
    def get_aaa_default_acl(self):
        return self.aaa.get("default_acl", self.aaa.acl.READ)  
    def get_aaa_default_uacl(self):
        return self.aaa.get("default_user_acl", self.aaa.acl.READ)  
    def get_aaa_default_oacl(self):
        return self.aaa.get("default_user_acl", self.aaa.acl.CREATE | 
                                                self.aaa.acl.READ | 
                                                self.aaa.acl.UPDATE)          
    def get_aaa_has_staff_permissions(self):
        return self.aaa.get("has_staff_permissions", False)    
    def get_aaa_staff_acl(self):
        return self.aaa.get("staff_acl", self.aaa.acl.CREATE | 
                                         self.aaa.acl.READ | 
                                         self.aaa.acl.UPDATE ) 
    def get_aaa_supervisor_acl(self):
        return self.aaa.get("supervisor_acl", self.aaa.acl.ALL)    

    # Options
    def get_options_support_requests(self):
        return self.options.get("support_requests", False)

    # UI/Workflow Settings
    def get_ui_navigate_away_confirm(self):
        return self.ui.get("navigate_away_confirm", True)
    def get_ui_autocomplete(self):
        return self.ui.get("autocomplete", False)

    # Request Settings
    def get_req_status_writable(self):
        return self.req.get("status_writable", True) 

    # Active modules list
    def has_module(self, module_name):
        if not self.modules:
            _modules = [
                "admin",        # Admin
                "gis",          # GIS
                "doc",          # Document Library
                "pr",           # Person Registry
                "org",          # Organisation Registry
                "budget",       # Budgetting
                "cr",           # Camp Registry
		        "delphi",       # Delphi Decision Maker
                "dvi",          # Disaster Victim Identification
                #"dvr",          # Disaster Victim Registry
                "hms",          # Hospital Management
                "inv",          # Logistics
                "pf",           # Person Finder
                "msg",          # Messaging
                "project",      # Project Tracking
                "assess",       # Assessments Tool
                "rms",          # Request Management
                "vol",          # Volunteer Management
                #"importer",     # Spreadsheet Importer
                #"survey",       # Surveys
                #"ticket",       # Ticketing
            ]
        else:
            _modules = self.modules

        return module_name in _modules

    # S3OCR
    def get_s3ocr_fieldtype_properties(self):
        fieldtype_properties = {
        # Example configuration
        #    "reference document_id": {
        #        "fieldtype"="string",
        #        "readable"="True",
        #        .
        #        .
        #        }
            }
        return fieldtype_properties
