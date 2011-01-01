# -*- coding: utf-8 -*-

""" Global settings:

    Those which are typically edited during a deployment are in
    000_config.py & their results parsed into here. Deployers
    shouldn't typically need to edit any settings here.

"""

# Keep all our configuration options off the main global variables

# Use response for one-off variables which are visible in views without explicit passing
response.s3 = Storage()
response.s3.countries = deployment_settings.get_L10n_countries()
response.s3.formats = Storage()
response.s3.gis = Storage()

# Use session for persistent per-user variables (beware of a user having multiple tabs open!)
if not session.s3:
    session.s3 = Storage()

########################
# Is it a mobile client?
########################
def ifmobile(request):
    if request.env.http_x_wap_profile or request.env.http_profile:
        return True
    if request.env.http_accept and (request.env.http_accept.find("text/vnd.wap.wml") > 0):
        return True
    keys = ["iphone", "ipod", "android", "opera mini", "blackberry", "palm", "windows ce", "iemobile", "smartphone", "medi", "sk-0", "vk-v", "aptu", "xda-", "mtv ", "v750", "p800", "opwv", "send", "xda2", "sage", "t618", "qwap", "veri", "t610", "tcl-", "vx60", "vx61", "lg-k", "lg-l", "lg-m", "lg-o", "lg-a", "lg-b", "lg-c", "xdag", "lg-f", "lg-g", "sl45", "emul", "lg-p", "lg-s", "lg-t", "lg-u", "lg-w", "6590", "t250", "qc21", "ig01", "port", "m1-w", "770s", "n710", "ez60", "mt50", "g1 u", "vk40", "bird", "tagt", "pose", "jemu", "beck", "go.w", "jata", "gene", "smar", "g-mo", "o2-x", "htc_", "hei-", "fake", "qc-7", "smal", "htcp", "htcs", "craw", "htct", "aste", "htca", "htcg", "teli", "telm", "kgt", "mwbp", "kwc-", "owg1", "htc ", "kgt/", "htc-", "benq", "slid", "qc60", "dmob", "blac", "smt5", "nec-", "sec-", "sec1", "sec0", "fetc", "spv ", "mcca", "nem-", "spv-", "o2im", "m50/", "ts70", "arch", "qtek", "opti", "devi", "winw", "rove", "winc", "talk", "pant", "netf", "pana", "esl8", "pand", "vite", "v400", "whit", "scoo", "good", "nzph", "mtp1", "doco", "raks", "wonu", "cmd-", "cell", "mode", "im1k", "modo", "lg-d", "idea", "jigs", "bumb", "sany", "vulc", "vx70", "psio", "fly_", "mate", "pock", "cdm-", "fly-", "i230", "lge-", "lge/", "argo", "qc32", "n701", "n700", "mc21", "n500", "midp", "t-mo", "airn", "bw-u", "iac", "bw-n", "lg g", "erk0", "sony", "alav", "503i", "pt-g", "au-m", "treo", "ipaq", "dang", "seri", "mywa", "eml2", "smb3", "brvw", "sgh-", "maxo", "pg-c", "qci-", "vx85", "vx83", "vx80", "vx81", "pg-8", "pg-6", "phil", "pg-1", "pg-2", "pg-3", "ds12", "scp-", "dc-s", "brew", "hipt", "kddi", "qc07", "elai", "802s", "506i", "dica", "mo01", "mo02", "avan", "kyoc", "ikom", "siem", "kyok", "dopo", "g560", "i-ma", "6310", "sie-", "grad", "ibro", "sy01", "nok6", "el49", "rim9", "upsi", "inno", "wap-", "sc01", "ds-d", "aur ", "comp", "wapp", "wapr", "waps", "wapt", "wapu", "wapv", "wapy", "newg", "wapa", "wapi", "wapj", "wapm", "hutc", "lg/u", "yas-", "hita", "lg/l", "lg/k", "i-go", "4thp", "bell", "502i", "zeto", "ez40", "java", "n300", "n302", "mmef", "pn-2", "newt", "1207", "sdk/", "gf-5", "bilb", "zte-", "maui", "qc-3", "qc-2", "blaz", "r600", "hp i", "qc-5", "moto", "cond", "motv", "virg", "ccwa", "audi", "shar", "i-20", "samm", "sama", "sams", "sch-", "mot ", "http", "505i", "mot-", "n502", "topl", "n505", "mobi", "3gso", "wmlb", "ezwa", "qc12", "abac", "tdg-", "neon", "mio8", "sp01", "rozo", "vx98", "dait", "t600", "anyw", "tx-9", "sava", "m-cr", "tsm-", "mioa", "tsm5", "klon", "capi", "tsm3", "hcit", "libw", "lg50", "mc01", "amoi", "lg54", "ez70", "se47", "n203", "vk52", "vk53", "vk50", "webc", "haie", "semc", "grun", "play", "palm", "a wa", "anny", "prox", "o2 x", "ezze", "symb", "hs-c", "pg13", "mits", "kpt ", "qa-a", "501i", "pdxg", "iris", "pluc", "acoo", "soft", "hpip", "iac/", "iac-", "aus ", "s55/", "vx53", "vx52", "chtm", "meri", "merc", "your", "huaw", "cldc", "voda", "smit", "x700", "mozz", "lexi", "up.b", "sph-", "keji", "jbro", "wig ", "attw", "pire", "r380", "lynx", "anex", "vm40", "hd-m", "504i", "w3c ", "c55/", "w3c-", "upg1", "t218", "tosh", "acer", "hd-t", "eric", "hd-p", "noki", "acs-", "dbte", "n202", "tim-", "alco", "ezos", "dall", "leno", "alca", "asus", "m3ga", "utst", "aiko", "n102", "n101", "n100", "oran"]
    ua = (request.env.http_user_agent or "").lower()
    if [key for key in keys if ua.find(key) >= 0]:
        return True
    return False

response.s3.mobile = ifmobile(request)

# Use WURFL for browser compatibility detection
def populate_browser_compatibility(request):
    try:
        from pywurfl.algorithms import TwoStepAnalysis
    except ImportError:
        s3_debug("pywurfl python module has not been installed, browser compatibility listing will not be populated. Download pywurfl from http://pypi.python.org/pypi/pywurfl/")
        return False
    wurfl = local_import("wurfl")
    device = wurfl.devices.select_ua(unicode(request.env.http_user_agent), search=TwoStepAnalysis(wurfl.devices))

    browser = Storage()
    category_list = []
    for feature in device:
        if feature[0] not in category_list:
            category_list.append(feature[0])
    for category in category_list:
        browser[category] = Storage()

    for feature in device:
        browser[feature[0]][feature[1]] = feature[2]
    
    return browser

response.s3.browser = populate_browser_compatibility(request)

##################
# Global variables
##################

# Interactive view formats
shn_interactive_view_formats = ("html", "popup", "iframe")
s3.interactive_view_formats = shn_interactive_view_formats

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

# Default Language for authenticated users
db.auth_user.language.default = deployment_settings.get_L10n_default_language()

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
auth.messages.registration_pending_approval = T("Account registered, however registration is still pending approval - please wait until confirmation received.")
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
    row.append(TR(TD(label, _class="w2p_fl"), TD(""), _id=id + "1"))
    # Widget & Comment on the 2nd Row
    row.append(TR(widget, TD(comment, _class="w2p_fc"), _id=id))

    return tuple(row)

s3_formstyle_mobile = s3_formstyle

s3.crud.formstyle = s3_formstyle
s3.crud.submit_button = T("Save")
s3.crud.confirm_delete = T("Do you really want to delete these records?")

s3.crud.archive_not_delete = deployment_settings.get_security_archive_not_delete()
s3.crud.navigate_away_confirm = deployment_settings.get_ui_navigate_away_confirm()

s3.base_url = "%s/%s" % (deployment_settings.get_base_public_url(),
                         request.application)
s3.download_url = "%s/default/download" % s3.base_url

#############
# Web2py/Crud
#############

# Breaks refresh of List after Create: http://groups.google.com/group/web2py/browse_thread/thread/d5083ed08c685e34
#crud.settings.keepvalues = True
crud.messages.submit_button = s3.crud.submit_button
crud.settings.formstyle = s3.crud.formstyle

##################
# XML/JSON Formats
##################

s3xrc.XSLT_FILE_EXTENSION = "xsl" #: File extension of XSLT templates
s3xrc.XSLT_IMPORT_TEMPLATES = "static/xslt/import" #: Path to XSLT templates for data import
s3xrc.XSLT_EXPORT_TEMPLATES = "static/xslt/export" #: Path to XSLT templates for data export

# Content Type Headers, default is application/xml for XML formats
# and text/x-json for JSON formats, other content types must be
# specified here:
s3xrc.content_type = Storage(
    tc = "application/atom+xml", # TableCast feeds
    rss = "application/rss+xml", # RSS
    georss = "application/rss+xml", # GeoRSS
    kml = "application/vnd.google-earth.kml+xml", # KML
)

# JSON Formats
s3xrc.json_formats = ["geojson"]

s3xrc.ROWSPERPAGE = 20

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
    "AX": "Åland Islands",
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
    "CI": "Côte d'Ivoire",
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
    "RE": "Réunion",
    "RO": "Romania",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "BL": "Saint Barthélemy",
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
