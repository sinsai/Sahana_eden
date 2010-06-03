# -*- coding: utf-8 -*-

"""
    Global settings
    @ToDo: Use a global "deployment_settings" variable
"""

S3_PUBLIC_URL = "http://127.0.0.1:8000"
S3_UTC_OFFSET = "UTC +0000" # default UTC offset (timezone) of users
BREADCRUMB = ">> "
UNKNOWN_OPT = T("Unknown")

# Default strings are in English
T.current_languages = ["en", "en-us"]
# Check if user has selected a specific language
#if request.vars._language:
#    session._language = request.vars._language
#if session._language:
#    T.force(session._language)
#else:
    # Use what browser requests
#    T.force(T.http_accept_language)


######
# Mail
######

# These settings could be made configurable as part of the Messaging Module
# - however also need to be used by Auth (order issues), DB calls are overheads
# - as easy for admin to edit source here as to edit DB (although an admin panel can be nice)
mail.settings.server = "127.0.0.1:25"
#mail.settings.server = "smtp.gmail.com:587"
#mail.settings.login = "username:password"
mail.settings.sender = "sahana@your.org"

######
# Auth
######

#auth.settings.username_field = True
auth.settings.hmac_key = "akeytochange" # Change *before* registering 1st user!
auth.define_tables()
auth.settings.expiration = 3600  # seconds
# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key="PUBLIC_KEY", private_key="PRIVATE_KEY")
# Require Email Verification
auth.settings.registration_requires_verification = False # CHANGEME for Deployment!
# Email settings for registration verification
auth.settings.mailer = mail
auth.messages.verify_email = "Click on the link " + S3_PUBLIC_URL + "/" + request.application + "/default/user/verify_email/%(key)s to verify your email"
auth.settings.on_failed_authorization = URL(r=request, c="default", f="user", args="not_authorized")
auth.settings.reset_password_requires_verification = True
auth.messages.reset_password = "Click on the link "+S3_PUBLIC_URL + "/" + request.application + "/default/user/reset_password/%(key)s to reset your password"
# Require Admin approval for self-registered users
auth.settings.registration_requires_approval = False # CHANGEME for Deployment!
auth.messages.registration_pending = "Email address verified, however registration is still pending approval - please wait until confirmation received."
# Notify UserAdmin of new pending user registration to action
auth.settings.verify_email_onaccept = lambda form: auth.settings.mailer.send(to="useradmin@your.org", subject="Sahana Login Approval Pending", message="Your action is required. Please approve user %s asap: " % form.email + S3_PUBLIC_URL + "/" + request.application + "/admin/user")

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
#auth.settings.login_methods.append(ldap_auth(server="demo.sahanapy.org", base_dn="ou=users,dc=sahanapy,dc=org"))
# Allow use of Email accounts for login
#auth.settings.login_methods.append(email_auth("smtp.gmail.com:587", "@gmail.com"))
# We don't wish to clutter the groups list with 1 per user.
auth.settings.create_user_groups = False
# We need to allow basic logins for Webservices
auth.settings.allow_basic_login = True

auth.settings.lock_keys = False
auth.settings.logout_onlogout = shn_auth_on_logout
auth.settings.login_onaccept = shn_auth_on_login
auth.settings.login_next = URL(r=request, c='default', f='user',
        args='login_next')

# Extra startup roles for Admin:
auth.settings.admin_startup_roles = [
    #"AdvancedJS",
]
auth.settings.lock_keys = True

######
# Crud
######

# Breaks refresh of List after Create: http://groups.google.com/group/web2py/browse_thread/thread/d5083ed08c685e34
#crud.settings.keepvalues = True
crud.messages.submit_button = T("Save")

##########
# Messages
##########

from gluon.storage import Messages
s3.messages = Messages(T)
s3.messages.confirmation_email_subject = "Sahana access granted"
s3.messages.confirmation_email = "Welcome to the Sahana Portal at " + S3_PUBLIC_URL + ". Thanks for your assistance."
