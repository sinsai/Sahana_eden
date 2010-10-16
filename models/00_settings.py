# -*- coding: utf-8 -*-

""" Global settings:

    Those which are typically edited during a deployment are in
    000_config.py & their results parsed into here. Deployers
    shouldn't typically need to edit any settings here.

"""

##################
# Global variables
##################

# Interactive view formats
shn_interactive_view_formats = ("html", "popup", "iframe")

# Error messages
UNAUTHORISED = T("Not authorised!")
BADFORMAT = T("Unsupported data format!")
BADMETHOD = T("Unsupported method!")
BADRECORD = T("Record not found!")
INVALIDREQUEST = T("Invalid request!")
XLWT_ERROR = T("xlwt module not available within the running Python - this needs installing for XLS output!")
GERALDO_ERROR = T("Geraldo module not available within the running Python - this needs installing for PDF output!")
REPORTLAB_ERROR = T("ReportLab module not available within the running Python - this needs installing for PDF output!")

# Common Labels
BREADCRUMB = ">> "
UNKNOWN_OPT = T("Unknown")
NONE = "-"
READ = T("Open")
#READ = T("Details")
UPDATE = T("Open")
#UPDATE = T("Edit")
#UPDATE = T("Update")
DELETE = T("Delete")
COPY = T("Copy")
NOT_APPLICABLE = T("N/A")

# Data Export Settings
ROWSPERPAGE = 20
PRETTY_PRINT = False

# Keep all our configuration options in a single pair of global variables

# Use response for one-off variables which are visible in views without explicit passing
response.s3 = Storage()
response.s3.countries = deployment_settings.get_L10n_countries()
response.s3.formats = Storage()
response.s3.gis = Storage()

# Use session for persistent per-user variables
if not session.s3:
    session.s3 = Storage()

###########
# Languages
###########

s3.l10n_languages = deployment_settings.get_L10n_languages()

# Default strings are in US English
T.current_languages = ["en", "en-us"]
# Check if user has selected a specific language
if request.vars._language:
    session.s3.language = request.vars._language
if session.s3.language:
    T.force(session.s3.language)
elif auth.is_logged_in():
    # Use user preference
    language = auth.user.language
    T.force(language)
#else:
#    # Use what browser requests (default web2py behaviour)
#    T.force(T.http_accept_language)

# List of Languages which use a Right-to-Left script (Arabic, Hebrew, Farsi, Urdu)
s3_rtl_languages = ["ur"]

if T.accepted_language in s3_rtl_languages:
    response.s3.rtl = True
else:
    response.s3.rtl = False

######
# Mail
######

# These settings could be made configurable as part of the Messaging Module
# - however also need to be used by Auth (order issues), DB calls are overheads
# - as easy for admin to edit source here as to edit DB (although an admin panel can be nice)
mail.settings.server = deployment_settings.get_mail_server()
mail_server_login = deployment_settings.get_mail_server_login()
if mail_server_login:
    mail.settings.login = mail_server_login
mail.settings.sender = deployment_settings.get_mail_sender()

######
# Auth
######

#auth.settings.username_field = True
auth.settings.hmac_key = deployment_settings.get_auth_hmac_key()
auth.define_tables()

if deployment_settings.get_auth_openid():
    # Requires http://pypi.python.org/pypi/python-openid/
    try:
        from gluon.contrib.login_methods.openid_auth import OpenIDAuth
        openid_login_form = OpenIDAuth(auth)
        from gluon.contrib.login_methods.extended_login_form import ExtendedLoginForm
        extended_login_form = ExtendedLoginForm(auth, openid_login_form, signals=["oid", "janrain_nonce"])
        auth.settings.login_form = extended_login_form
    except ImportError:
        session.warning = T("Library support not available for OpenID")

auth.settings.expiration = 14400  # seconds
# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key="PUBLIC_KEY", private_key="PRIVATE_KEY")
# Require Email Verification
auth.settings.registration_requires_verification = deployment_settings.get_auth_registration_requires_verification()
# Email settings for registration verification
auth.settings.mailer = mail
auth.messages.verify_email = T("Click on the link ") + deployment_settings.get_base_public_url() + "/" + request.application + "/default/user/verify_email/%(key)s " + T("to verify your email")
auth.settings.on_failed_authorization = URL(r=request, c="default", f="user", args="not_authorized")
auth.settings.reset_password_requires_verification = True
auth.messages.reset_password = T("Click on the link ") + deployment_settings.get_base_public_url() + "/" + request.application + "/default/user/reset_password/%(key)s " + T("to reset your password")
# Require Admin approval for self-registered users
auth.settings.registration_requires_approval = deployment_settings.get_auth_registration_requires_approval()
auth.messages.registration_pending = T("Email address verified, however registration is still pending approval - please wait until confirmation received.")
# Notify UserAdmin of new pending user registration to action
if deployment_settings.get_auth_registration_requires_approval():
    auth.settings.verify_email_onaccept = lambda form: \
        auth.settings.mailer.send(to=deployment_settings.get_mail_approver(),
                                  subject=T("Sahana Login Approval Pending"),
                                  message=T("Your action is required. Please approve user %s asap: " % form.email) +
                                  deployment_settings.get_base_public_url() + "/" + request.application + "/admin/user")

# Allow use of LDAP accounts for login
# NB Currently this means that change password should be disabled:
#auth.settings.actions_disabled.append("change_password")
# (NB These are not automatically added to PR or to Authenticated role since they enter via the login() method not register())
#from gluon.contrib.login_methods.ldap_auth import ldap_auth
# Require even alternate login methods to register users 1st
#auth.settings.alternate_requires_registration = True
# Active Directory
#auth.settings.login_methods.append(ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org"))
# or if not wanting local users at all (no passwords saved within DB):
#auth.settings.login_methods = [ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org")]
# Domino
#auth.settings.login_methods.append(ldap_auth(mode="domino", server="domino.domain.org"))
# OpenLDAP
#auth.settings.login_methods.append(ldap_auth(server="directory.sahanafoundation.org", base_dn="ou=users,dc=sahanafoundation,dc=org"))
# Allow use of Email accounts for login
#auth.settings.login_methods.append(email_auth("smtp.gmail.com:587", "@gmail.com"))
# We don't wish to clutter the groups list with 1 per user.
auth.settings.create_user_groups = False
# We need to allow basic logins for Webservices
auth.settings.allow_basic_login = True

auth.settings.lock_keys = False
auth.settings.logout_onlogout = shn_auth_on_logout
auth.settings.login_onaccept = shn_auth_on_login
# Uncomment to have complex redirects post login
#if not request.vars._next:
#	auth.settings.login_next = URL(r=request, c="default", f="user",
#		args="login_next")
#if not deployment_settings.auth.registration_requires_verification:
#    auth.settings.register_next = URL(r=request, c="default", f="user",
#            args="login_next")

auth.settings.lock_keys = True

########
# S3CRUD
########

def s3_formstyle(id, label, widget, comment):

    """ Provide the Sahana Eden Form Style

        Label above the Inputs:
        http://uxmovement.com/design-articles/faster-with-top-aligned-labels

    """

    row = []

    # Label on the 1st row
    row.append(TR(TD(label, _class="w2p_fl", _colspan="2"), _id=id + "1"))
    # Widget & Comment on the 2nd Row
    row.append(TR(widget, TD(comment, _class="w2p_fc"), _id=id))

    return tuple(row)

#s3.crud = Storage()
s3.crud.formstyle = s3_formstyle
s3.crud.submit_buttom = T("Save")

s3.crud.archive_not_delete = deployment_settings.get_security_archive_not_delete()
s3.crud.navigate_away_confirm = deployment_settings.get_ui_navigate_away_confirm()

#############
# Web2py/Crud
#############

# Breaks refresh of List after Create: http://groups.google.com/group/web2py/browse_thread/thread/d5083ed08c685e34
#crud.settings.keepvalues = True
crud.messages.submit_button = T("Save")
crud.settings.formstyle = s3_formstyle

##################
# XML/JSON Formats
##################

XSLT_FILE_EXTENSION = "xsl" #: File extension of XSLT templates
XSLT_IMPORT_TEMPLATES = "static/xslt/import" #: Path to XSLT templates for data import
XSLT_EXPORT_TEMPLATES = "static/xslt/export" #: Path to XSLT templates for data export

# Supported XML Output Formats
shn_xml_export_formats = dict(
    xml = "application/xml", # Native S3XML (must be included here!)
    gpx = "application/xml", # GPX
    lmx = "application/xml", # NOKIA Landmarks
    pfif = "application/xml", # Person Finder Interchange Format
    have = "application/xml", # EDXL-HAVE
    osm = "application/xml", # Open Street Map
    rss = "application/rss+xml", # RSS
    georss = "application/rss+xml", # GeoRSS
    kml = "application/vnd.google-earth.kml+xml", # KML
)

# Supported XML Import Formats
shn_xml_import_formats = ["xml", # native S3XML (must be included here!)
                          "lmx", # Nokia Landmarks
                          "osm", # Open Street Map
                          "pfif", # Person Finder Interchange Format
                          "ushahidi", # Ushahidi
                          "odk",
                          "agasti", # Sahana Agasti
                          "fods" # Flat Open Document Spreadsheet
                         ]

# Supported JSON Export Formats
shn_json_export_formats = dict(
    json = "text/x-json", # Native S3XML-JSON (must be included here!)
    geojson = "text/x-json" # GeoJSON
)

# Supported JSON Import Formats
shn_json_import_formats = ["json", # native S3XML-JSON (must be included here!)
                          ]

# Register formats with resource controller
s3xrc.xml_import_formats = shn_xml_import_formats
s3xrc.xml_export_formats = shn_xml_export_formats
s3xrc.json_import_formats = shn_json_import_formats
s3xrc.json_export_formats = shn_json_export_formats


##########
# Messages
##########

from gluon.storage import Messages
s3.messages = Messages(T)
s3.messages.confirmation_email_subject = T("Sahana access granted")
s3.messages.confirmation_email = T("Welcome to the Sahana Portal at ") + deployment_settings.get_base_public_url() + ". " + T("Thanks for your assistance") + "."

auth.settings.table_user.language.requires = IS_IN_SET(s3.l10n_languages, zero=None)


# -----------------------------------------------------------------------------
# List of Nations (ISO-3166-1 Country Codes)
# @ToDo Add Telephone codes (need to convert to Storage())
#
s3_list_of_nations = {
    "AF": "Afghanistan",
    "AX": "�land Islands",
    "AL": "Albania",
    "DZ": "Algeria",
    "AS": "American Samoa",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AQ": "Antarctica",
    "AG": "Antigua and Barbuda",
    "AR": "Argentina",
    "AM": "Armenia",
    "AW": "Aruba",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BS": "Bahamas",
    "BH": "Bahrain",
    "BD": "Bangladesh",
    "BB": "Barbados",
    "BY": "Belarus",
    "BE": "Belgium",
    "BZ": "Belize",
    "BJ": "Benin",
    "BM": "Bermuda",
    "BT": "Bhutan",
    "BO": "Bolivia, Plurinational State of",
    "BA": "Bosnia and Herzegovina",
    "BW": "Botswana",
    "BV": "Bouvet Island",
    "BR": "Brazil",
    "IO": "British Indian Ocean Territory",
    "BN": "Brunei Darussalam",
    "BG": "Bulgaria",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "KH": "Cambodia",
    "CM": "Cameroon",
    "CA": "Canada",
    "CV": "Cape Verde",
    "KY": "Cayman Islands",
    "CF": "Central African Republic",
    "TD": "Chad",
    "CL": "Chile",
    "CN": "China",
    "CX": "Christmas Island",
    "CC": "Cocos (Keeling) Islands",
    "CO": "Colombia",
    "KM": "Comoros",
    "CG": "Congo",
    "CD": "Congo, The Democratic Republic of the",
    "CK": "Cook Islands",
    "CR": "Costa Rica",
    "CI": "C�te d'Ivoire",
    "HR": "Croatia",
    "CU": "Cuba",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "EC": "Ecuador",
    "EG": "Egypt",
    "SV": "El Salvador",
    "GQ": "Equatorial Guinea",
    "ER": "Eritrea",
    "EE": "Estonia",
    "ET": "Ethiopia",
    "FK": "Falkland Islands (Malvinas)",
    "FO": "Faroe Islands",
    "FJ": "Fiji",
    "FI": "Finland",
    "FR": "France",
    "GF": "French Guiana",
    "PF": "French Polynesia",
    "TF": "French Southern Territories",
    "GA": "Gabon",
    "GM": "Gambia",
    "GE": "Georgia",
    "DE": "Germany",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GR": "Greece",
    "GL": "Greenland",
    "GD": "Grenada",
    "GP": "Guadeloupe",
    "GU": "Guam",
    "GT": "Guatemala",
    "GG": "Guernsey",
    "GN": "Guinea",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HT": "Haiti",
    "HM": "Heard Island and McDonald Islands",
    "VA": "Holy See (Vatican City State)",
    "HN": "Honduras",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "IS": "Iceland",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Iran, Islamic Republic of",
    "IQ": "Iraq",
    "IE": "Ireland",
    "IM": "Isle of man",
    "IL": "Israel",
    "IT": "Italy",
    "JM": "Jamaica",
    "JP": "Japan",
    "JE": "Jersey",
    "JO": "Jordan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KI": "Kiribati",
    "KP": "Korea, Democratic People's Republic of",
    "KR": "Korea, Republic of",
    "KW": "Kuwait",
    "KG": "Kyrgyzstan",
    "LA": "Lao People's Democratic Republic",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LS": "Lesotho",
    "LR": "Liberia",
    "LY": "Libyan Arab Jamahiriya",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MO": "Macao",
    "MK": "Macedonia, the former Yugoslav Republic of",
    "MG": "Madagascar",
    "MW": "Malawi",
    "MY": "Malaysia",
    "MV": "Maldives",
    "ML": "Mali",
    "MT": "Malta",
    "MH": "Marshall Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MU": "Mauritius",
    "YT": "Mayotte",
    "MX": "Mexico",
    "FM": "Micronesia, Federated States of",
    "MD": "Moldova, Republic of",
    "MC": "Monaco",
    "MN": "Mongolia",
    "ME": "Montenegro",
    "MS": "Montserrat",
    "MA": "Morocco",
    "MZ": "Mozambique",
    "MM": "Myanmar",
    "NA": "Namibia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Netherlands",
    "AN": "Netherlands Antilles",
    "NC": "New Caledonia",
    "NZ": "New Zealand",
    "NI": "Nicaragua",
    "NE": "Niger",
    "NG": "Nigeria",
    "NU": "Niue",
    "NF": "Norfolk Island",
    "MP": "Northern Mariana Islands",
    "NO": "Norway",
    "OM": "Oman",
    "PK": "Pakistan",
    "PW": "Palau",
    "PS": "Palestinian Territory, occupied",
    "PA": "Panama",
    "PG": "Papua New Guinea",
    "PY": "Paraguay",
    "PE": "Peru",
    "PH": "Philippines",
    "PN": "Pitcairn",
    "PL": "Poland",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Qatar",
    "RE": "R�union",
    "RO": "Romania",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "BL": "Saint Barth�lemy",
    "SH": "Saint Helena, Ascension and Tristan da Cunha",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "MF": "Saint Martin",
    "PM": "Saint Pierre and Miquelon",
    "VC": "Saint Vincent and the Grenadines",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia",
    "SN": "Senegal",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SL": "Sierra Leone",
    "SG": "Singapore",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "SB": "Solomon Islands",
    "SO": "Somalia",
    "ZA": "South Africa",
    "GS": "South Georgia and the South Sandwich Islands",
    "ES": "Spain",
    "LK": "Sri Lanka",
    "SD": "Sudan",
    "SR": "Suriname",
    "SJ": "Svalbard and Jan Mayen",
    "SZ": "Swaziland",
    "SE": "Sweden",
    "CH": "Switzerland",
    "SY": "Syrian Arab Republic",
    "TW": "Taiwan, Province of China",
    "TJ": "Tajikistan",
    "TZ": "Tanzania, United Republic of",
    "TH": "Thailand",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TK": "Tokelau",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Tunisia",
    "TR": "Turkey",
    "TM": "Turkmenistan",
    "TC": "Turks and Caicos Islands",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States",
    "UM": "United States Minor Outlying Islands",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VU": "Vanuatu",
    "VE": "Venezuela, Bolivarian Republic of",
    "VN": "Vietnam",
    "VG": "Virgin Islands, british",
    "VI": "Virgin Islands, U.S.",
    "WF": "Wallis and Futuna",
    "EH": "Western Sahara",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
    "XX": "Unknown"
}