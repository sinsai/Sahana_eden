# -*- coding: utf-8 -*-

"""
    Global menus
"""

# Language Menu (available in all screens)
s3.menu_lang = [ T("Language"), True, "#"]
_menu_lang = []
for language in s3.l10n_languages.keys():
    _menu_lang.append([s3.l10n_languages[language], False,
                       URL(r=request, args=request.args,
                           vars={"_language":language})])
s3.menu_lang.append(_menu_lang)

# Help Menu (available in all screens)
s3.menu_help = [ T("Help"), True, "#",
        [
            [T("Contact us"), False,
             URL(request.application, "default", "contact")],
            [T("About"), False, URL(request.application, "default", "about")],
        ]
    ]

# Auth Menu (available in all screens)
if not auth.is_logged_in():

    self_registration = deployment_settings.get_security_self_registration()

    if self_registration:
        s3.menu_auth = [T("Login"), True,
                        URL(request.application, "default", "user/login"),
                [
                    [T("Login"), False,
                     URL(request.application, "default", "user/login")],
                    [T("Register"), False,
                     URL(request.application, "default", "user/register")],
                    [T("Lost Password"), False,
                     URL(request.application, "default", "user/retrieve_password")]
                ]
            ]
    else:
        s3.menu_auth = [T("Login"), True,
                        URL(request.application, "default", "user/login"),
                [
                    [T("Lost Password"), False,
                     URL(request.application, "default", "user/retrieve_password")]
                ]
            ]
else:
    s3.menu_auth = [auth.user.email, True, None,
            [
                [T("Logout"), False,
                 URL(request.application, "default", "user/logout")],
                [T("User Profile"), False,
                 URL(request.application, "default", "user/profile")],
                [T("Personal Data"), False,
                 URL(request.application, c="pr", f="person",
                     vars={"person.uid" : auth.user.person_uuid})],
                [T("Contact details"), False,
                 URL(request.application, c="pr", f="person",
                     args="pe_contact",
                     vars={"person.uid" : auth.user.person_uuid})],
                [T("Subscriptions"), False,
                 URL(request.application, c="pr", f="person",
                     args="pe_subscription",
                     vars={"person.uid" : auth.user.person_uuid})],
                [T("Change Password"), False,
                 URL(request.application, "default", "user/change_password")]
            ]
        ]

# Menu for Admin module
# (defined here as used in several different Controller files)
admin_menu_messaging = [
            [T("Global Messaging Settings"), False,
             URL(r=request, c="msg", f="setting", args=[1, "update"])],
            [T("Email Settings"), False,
             URL(r=request, c="msg", f="email_settings", args=[1, "update"])],
            [T("Twitter Settings"), False,
             URL(r=request, c="msg", f="twitter_settings", args=[1, "update"])],
            [T("Modem Settings"), False,
             URL(r=request, c="msg", f="modem_settings", args=[1, "update"])],
            [T("Gateway Settings"), False,
             URL(r=request, c="msg", f="gateway_settings", args=[1, "update"])],
            [T("Tropo Settings"), False,
             URL(r=request, c="msg", f="tropo_settings", args=[1, "update"])],
    ]
admin_menu_options = [
    [T("Settings"), False, URL(r=request, c="admin", f="setting", args=[1, "update"]), [
        [T("Edit Themes"), False, URL(r=request, c="admin", f="theme")]
    ]],
    [T("User Management"), False, URL(r=request, c="admin", f="user"), [
        [T("Users"), False, URL(r=request, c="admin", f="user")],
        [T("Roles"), False, URL(r=request, c="admin", f="role")],
        [T("Organisations"), False, URL(r=request, c="admin", f="organisation")],
        #[T("Roles"), False, URL(r=request, c="admin", f="group")],
        #[T("Membership"), False, URL(r=request, c="admin", f="membership")],
    ]],
    [T("Database"), False, "#", [
        [T("Import"), False, URL(r=request, c="admin", f="import_data")],
        [T("Export"), False, URL(r=request, c="admin", f="export_data")],
        #[T("Import Jobs"), False, URL(r=request, c="admin", f="import_job")],
        [T("Raw Database access"), False, URL(r=request, c="appadmin", f="index")]
    ]],
    [T("Synchronization"), False, URL(r=request, c="sync", f="index"), [
            [T("Manual Synchronization"), False, URL(r=request, c="sync", f="now")],
            #[T("Offline Sync"), False, URL(r=request, c="sync", f="offline")],
            [T("Settings"), False,
             URL(r=request, c="sync", f="setting", args=[1, "update"])],
            [T("Peers"), False, URL(r=request, c="sync", f="peer")],
            [T("Schedule"), False, URL(r=request, c="sync", f="job")],
            #[T("Sync Pools"), False, URL(r=request, c="sync", f="pool")],
            [T("Peer Registration"), False,
             URL(r=request, c="sync", f="registration")],
            #[T("Conflict Resolution"), False,
            # URL(r=request, c="sync", f="conflict")],
            [T("History"), False, URL(r=request, c="sync", f="log")]
    ]],
    [T("Messaging"), False, "#", admin_menu_messaging],
    #[T("Edit Application"), False,
    # URL(r=request, a="admin", c="default", f="design", args=[request.application])],
    [T("Tickets"), False, URL(r=request, c="admin", f="errors")],
]

# Modules Menu (available in all Controllers)
# NB This is just a default menu - most deployments will customise this
s3.menu_modules = []
# Home always 1st
_module = deployment_settings.modules["default"]
s3.menu_modules.append([_module.name_nice, False,
                        URL(r=request, c="default", f="index")])

# Modules to hide due to insufficient permissions
hidden_modules = auth.permission.hidden_modules()

# The Modules to display at the top level
for module_type in [1, 2, 3, 4, 5]:
    for module in deployment_settings.modules:
        if module in hidden_modules:
            continue
        _module = deployment_settings.modules[module]
        if (_module.module_type == module_type):
            if not _module.access:
                s3.menu_modules.append([_module.name_nice, False,
                                        URL(r=request, c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module.access)[1:-1]
                for group in groups:
                    if s3_has_role(group):
                        authorised = True
                if authorised == True:
                    s3.menu_modules.append([_module.name_nice, False,
                                            URL(r=request, c=module, f="index")])

# Modules to display off the 'more' menu
modules_submenu = []
for module in deployment_settings.modules:
    if module in hidden_modules:
        continue
    _module = deployment_settings.modules[module]
    if (_module.module_type == 10):
        if not _module.access:
            modules_submenu.append([_module.name_nice, False,
                                    URL(r=request, c=module, f="index")])
        else:
            authorised = False
            groups = re.split("\|", _module.access)[1:-1]
            for group in groups:
                if s3_has_role(group):
                    authorised = True
            if authorised == True:
                modules_submenu.append([_module.name_nice, False,
                                        URL(r=request, c=module, f="index")])
if modules_submenu:
    # Only show the 'more' menu if there are entries in the list
    module_more_menu = ([T("more"), False, "#"])
    module_more_menu.append(modules_submenu)
    s3.menu_modules.append(module_more_menu)

# Admin always last
_module = deployment_settings.modules["admin"]
authorised = False
groups = re.split("\|", _module.access)[1:-1]
for group in groups:
    if int(group) in session.s3.roles:
        authorised = True
if authorised == True:
    s3.menu_admin = [_module.name_nice, True,
                     URL(r=request, c="admin", f="index")]
else:
    s3.menu_admin = []

# Build overall menu out of components
response.menu = s3.menu_modules
response.menu.append(s3.menu_help)
response.menu.append(s3.menu_auth)
if deployment_settings.get_L10n_display_toolbar():
    response.menu.append(s3.menu_lang)
if s3.menu_admin:
    response.menu.append(s3.menu_admin)
