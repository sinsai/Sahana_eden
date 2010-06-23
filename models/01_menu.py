# -*- coding: utf-8 -*-

"""
    Global menus
"""

# Help Menu (available in all screens)
s3.menu_help = [
        T("Contact us"), True, URL(request.application, "default", "contact")
        , [
            [T("About"), False, URL(request.application, "default", "about")],
        ]
    ]

# Auth Menu (available in all screens)
if not auth.is_logged_in():

    self_registration = s3_settings.self_registration if s3_settings else True

    if self_registration:
        s3.menu_auth = [T("Login"), True, URL(request.application, "default", "user/login"),
             [
                    [T("Register"), False,
                     URL(request.application, "default", "user/register")],
                    [T("Lost Password"), False,
                     URL(request.application, "default", "user/retrieve_password")]]
             ]
    else:
        s3.menu_auth = [T("Login"), True, URL(request.application, "default", "user/login"),
             [
                    [T("Lost Password"), False,
                     URL(request.application, "default", "user/retrieve_password")]]
             ],
else:
    s3.menu_auth = ["%s: %s %s" % (T("Logged-in as: "),
                                  auth.user.first_name,
                                  auth.user.last_name), True, None,
         [
                [T("Logout"), False,
                 URL(request.application, "default", "user/logout")],
                [T("User Profile"), False,
                 URL(request.application, "default", "user/profile")],
                [T("Personal Data"), False,
                 URL(request.application, c="pr", f="person", vars={"person.uid" : auth.user.person_uuid})],
                [T("Contact details"), False,
                 URL(request.application, c="pr", f="person", args="pe_contact", vars={"person.uid" : auth.user.person_uuid})],
                [T("Subscriptions"), False,
                 URL(request.application, c="pr", f="person", args="pe_subscription", vars={"person.uid" : auth.user.person_uuid})],
                [T("Change Password"), False,
                 URL(request.application, "default", "user/change_password")]]
         ]

# Menu for Admin module
# (defined here as used in several different Controller files)
admin_menu_options = [
    [T("Settings"), False, URL(r=request, c="admin", f="setting", args=[1, "update"]), [
        [T("Edit Themes"), False, URL(r=request, c="admin", f="theme")]
    ]],
    [T("User Management"), False, URL(r=request, c="admin", f="user"), [
        [T("Users"), False, URL(r=request, c="admin", f="user")],
        [T("Roles"), False, URL(r=request, c="admin", f="group")],
        #[T("Membership"), False, URL(r=request, c="admin", f="membership")]
    ]],
    [T("Database"), False, "#", [
        [T("Import"), False, URL(r=request, c="admin", f="import_data")],
        [T("Export"), False, URL(r=request, c="admin", f="export_data")],
        [T("Import Jobs"), False, URL(r=request, c="admin", f="import_job")],
        [T("Raw Database access"), False, URL(r=request, c="appadmin", f="index")]
    ]],
    [T("Synchronisation"), False, URL(r=request, c="sync", f="index"), [
            [T("Sync History"), False, URL(r=request, c="sync", f="history")],
            [T("Sync Partners"), False, URL(r=request, c="sync", f="partner")],
            [T("Sync Settings"), False, URL(r=request, c="sync", f="setting", args=[1, "update"])]
    ]],
    [T("Messaging"), False, "#",[
            [T("Global Messaging Settings"), False, URL(r=request, c="msg", f="setting", args=[1, "update"])],
            [T("Email Settings"), False, URL(r=request, c="msg", f="email_settings", args=[1, "update"])],
            [T("Modem Settings"), False, URL(r=request, c="msg", f="modem_settings", args=[1, "update"])],
            [T("Gateway Settings"), False, URL(r=request, c="msg", f="gateway_settings", args=[1, "update"])]
    ]],
    [T("Edit Application"), False, URL(r=request, a="admin", c="default", f="design", args=[request.application])],
    [T("Tickets"), False, URL(r=request, c="admin", f="errors")],
    [T("Functional Tests"), False, URL(r=request, c="static", f="selenium", args=["core", "TestRunner.html"], vars=dict(test="../tests/TestSuite.html", auto="true", resultsUrl=URL(r=request, c="admin", f="handleResults")))]
]

# Modules Menu (available in all Controllers)
# NB This is just a default menu - most deployments will customise this
s3.menu_modules = []
module_type = 1
# Always enabled
for module in deployment_settings.modules:
    _module = deployment_settings.modules[module]
    if (_module.module_type == module_type):
        if not _module.access:
            s3.menu_modules.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
        else:
            authorised = False
            groups = re.split("\|", _module.access)[1:-1]
            for group in groups:
                if shn_has_role(group):
                    authorised = True
            if authorised == True:
                s3.menu_modules.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
module_type = 2
# No sub-menus
for module in deployment_settings.modules:
    _module = deployment_settings.modules[module]
    if (_module.module_type == module_type):
        if not _module.access:
            s3.menu_modules.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
        else:
            authorised = False
            groups = re.split("\|", _module.access)[1:-1]
            for group in groups:
                if shn_has_role(group):
                    authorised = True
            if authorised == True:
                s3.menu_modules.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
module_type = 3
# Person Management sub-menu
module_type_name = str(s3_module_type_opts[module_type])
module_type_menu = ([module_type_name, False, "#"])
modules_submenu = []
for module in deployment_settings.modules:
    _module = deployment_settings.modules[module]
    if (_module.module_type == module_type):
        if not _module.access:
            modules_submenu.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
        else:
            authorised = False
            groups = re.split("\|", _module.access)[1:-1]
            for group in groups:
                if shn_has_role(group):
                    authorised = True
            if authorised == True:
                modules_submenu.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
module_type_menu.append(modules_submenu)
s3.menu_modules.append(module_type_menu)
module_type = 4
# Aid Management sub-menu
module_type_name = str(s3_module_type_opts[module_type])
module_type_menu = ([module_type_name, False, "#"])
modules_submenu = []
for module in deployment_settings.modules:
    _module = deployment_settings.modules[module]
    if (_module.module_type == module_type):
        if not _module.access:
            modules_submenu.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
        else:
            authorised = False
            groups = re.split("\|", _module.access)[1:-1]
            for group in groups:
                if shn_has_role(group):
                    authorised = True
            if authorised == True:
                modules_submenu.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
module_type_menu.append(modules_submenu)
s3.menu_modules.append(module_type_menu)
module_type = 5
# No sub-menus
for module in modules:
    _module = modules[module]
    if (_module.module_type == module_type):
        if deployment_settings.has_module(module):
            if not _module.access:
                s3.menu_modules.append([_module.name_nice, False, URL(r=request, c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module.access)[1:-1]
                for group in groups:
                    if int(group) in session.s3.roles:
                        authorised = True
                if authorised == True:
                    s3.menu_modules.append([_module.name_nice, False, URL(r=request, c=module, f="index")])

response.menu = s3.menu_modules
response.menu.append(s3.menu_auth)
response.menu.append(s3.menu_help)
