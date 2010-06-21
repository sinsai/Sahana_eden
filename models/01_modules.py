# -*- coding: utf-8 -*-

"""
    Module configuration
"""

module = "s3"

# Modules
s3_module_type_opts = {
    1:T("Home"),
    2:T("Situation Awareness"),
    3:T("Person Management"),
    4:T("Aid Management"),
    5:T("Communications")
    }

s3.modules = Storage()
modules = s3.modules

modules.default = {
            "name_nice":"Sahana Home",
            "module_type":1,
            "access":"",
            "description":"",
        }
modules.admin = {
            "name_nice":"Administration",
            "module_type":1,
            "access":"|1|",   # Administrator
            "description":"Site Administration",
        }
modules.gis = {
            "name_nice":"Mapping",
            "module_type":2,
            "access":"",
            "description":"Situation Awareness & Geospatial Analysis",
        }
modules.pr = {
            "name_nice":"Person Registry",
            "module_type":3,
            "access":"",
            "description":"Central point to record details on People",
        }
modules["or"] = {
            "name_nice":"Organization Registry",
            "module_type":4,
            "access":"",
            "description":'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
        }
modules.lms = {
            "name_nice":"Logistics Management System",
            "module_type":4,
            "access":"",
            "description":"An intake system, a warehouse management system, commodity tracking, supply chain management, procurement and other asset and resource management capabilities.",
        }
modules.mpr = {
            "name_nice":"Missing Persons Registry",
            "module_type":3,
            "access":"",
            "description":"Helps to report and search for Missing Persons",
        }
modules.dvr = {
            "name_nice":"Disaster Victim Registry",
            "module_type":3,
            "access":"",
            "description":"Traces internally displaced people (IDPs) and their needs",
        }
modules.hrm = {
            "name_nice":"Human Resources",
            "module_type":4,
            "access":"",
            "description":"Helps to manage human resources",
        }
modules.dvi = {
            "name_nice":"Disaster Victim Identification",
            "module_type":3,
            "access":"",
            "description":"Disaster Victim Identification",
        }
modules.cr = {
            "name_nice":"Shelter Registry",
            "module_type":4,
            "access":"",
            "description":"Tracks the location, distibution, capacity and breakdown of victims in Shelters",
        }
modules.vol = {
            "name_nice":"Volunteer Registry",
            "module_type":4,
            "access":"",
            "description":"Manage volunteers by capturing their skills, availability and allocation",
        }
modules.rms = {
            "name_nice":"Request Management",
            "module_type":4,
            "access":"",
            "description":"Tracks requests for aid and matches them against donors who have pledged aid",
        }
modules.budget = {
            "name_nice":"Budgeting Module",
            "module_type":4,
            "access":"",
            "description":"Allows a Budget to be drawn up",
        }
modules.msg = {
            "name_nice":"Messaging Module",
            "module_type":5,
            "access":"",
            "description":"Sends & Receives Alerts via Email & SMS",
        }
modules.delphi = {
            "name_nice":"Delphi Decision Maker",
            "module_type":4,
            "access":"",
            "description":"Supports the decision making of large groups of Crisis Management Experts by helping the groups create ranked list.",
        }
modules.media = {
            "name_nice":"Media Manager",
            "module_type":4,
            "access":"",
            "description":"A library of digital resources, such as Photos.",
        }
modules.nim = {
            "name_nice":"Nursing Information Manager",
            "module_type":3,
            "access":"",
            "description":"Module to assist disaster nurses.",
        }
modules.hms = {
            "name_nice":"Hospital Management",
            "module_type":4,
            "access":"",
            "description":"Helps to monitor status of hospitals",
        }
modules.ticket = {
            "name_nice":"Ticketing Module",
            "module_type":4,
            "access":"",
            "description":"Master Message Log to process incoming reports & requests",
        }

# Modules Menu (available in all Controllers)
s3.menu_modules = []
module_type = 1
# Always enabled
for module in modules:
    _module = modules[module]
    if (_module["module_type"] == module_type):
        if not _module["access"]:
            s3.menu_modules.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
        else:
            authorised = False
            groups = re.split("\|", _module["access"])[1:-1]
            for group in groups:
                if int(group) in session.s3.roles:
                    authorised = True
            if authorised == True:
                s3.menu_modules.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
module_type = 2
# No sub-menus
for module in modules:
    _module = modules[module]
    if (_module["module_type"] == module_type):
        if deployment_settings.has_module(module):
            if not _module["access"]:
                s3.menu_modules.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module["access"])[1:-1]
                for group in groups:
                    if int(group) in session.s3.roles:
                        authorised = True
                if authorised == True:
                    s3.menu_modules.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
module_type = 3
# Person Management sub-menu
module_type_name = str(s3_module_type_opts[module_type])
module_type_menu = ([module_type_name, False, "#"])
modules_submenu = []
for module in modules:
    _module = modules[module]
    if (_module["module_type"] == module_type):
        if deployment_settings.has_module(module):
            if not _module["access"]:
                modules_submenu.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module["access"])[1:-1]
                for group in groups:
                    if int(group) in session.s3.roles:
                        authorised = True
                if authorised == True:
                    modules_submenu.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
module_type_menu.append(modules_submenu)
s3.menu_modules.append(module_type_menu)
module_type = 4
# Aid Management sub-menu
module_type_name = str(s3_module_type_opts[module_type])
module_type_menu = ([module_type_name, False, "#"])
modules_submenu = []
for module in modules:
    _module = modules[module]
    if (_module["module_type"] == module_type):
        if deployment_settings.has_module(module):
            if not _module["access"]:
                modules_submenu.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module["access"])[1:-1]
                for group in groups:
                    if int(group) in session.s3.roles:
                        authorised = True
                if authorised == True:
                    modules_submenu.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
module_type_menu.append(modules_submenu)
s3.menu_modules.append(module_type_menu)
module_type = 5
# No sub-menus
for module in modules:
    _module = modules[module]
    if (_module["module_type"] == module_type):
        if deployment_settings.has_module(module):
            if not _module["access"]:
                s3.menu_modules.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])
            else:
                authorised = False
                groups = re.split("\|", _module["access"])[1:-1]
                for group in groups:
                    if int(group) in session.s3.roles:
                        authorised = True
                if authorised == True:
                    s3.menu_modules.append([_module["name_nice"], False, URL(r=request, c=module, f="index")])

#s3.menu_home = [T("Home"), False, URL(request.application, "default", "index"), s3.menu_modules]
#response.menu = [
#            s3.menu_home,
#            s3.menu_auth,
#            s3.menu_help,
#        ]
response.menu = s3.menu_modules
response.menu.append(s3.menu_auth)
response.menu.append(s3.menu_help)
