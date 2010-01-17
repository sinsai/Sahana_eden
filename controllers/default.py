# -*- coding: utf-8 -*-

module = 'default'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions)
response.menu_options = [
    #[T('About Sahana'), False, URL(r=request, f='about')],
]

# Web2Py Tools functions
# (replaces T2)
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # If webservices don't use sessions, avoid cluttering up the storage
    #session.forget()
    return service()

def download():
    "Download a file."
    return response.download(request, db)

def user():
    "Auth functions based on arg. See gluon/tools.py"

    auth.settings.on_failed_authorization = URL(r=request, f='error')
    # Add newly-registered users to Person Registry & 'Authenticated' role
    auth.settings.register_onaccept = lambda form: auth.shn_register(form)

    if request.args and request.args[0]=="profile":
        auth.settings.table_user.utc_offset.readable = True
        auth.settings.table_user.utc_offset.writable = True

    form = auth()

    self_registration = db().select(db.s3_setting.self_registration)[0].self_registration

    # Use Custom Ext views
    # Best to not use an Ext form for login: can't save username/password in browser & can't hit 'Enter' to submit!
    #if request.args[0] == 'login':
    #    response.title = T('Login')
    #    response.view = 'auth/login.html'

    return dict(form=form, self_registration=self_registration)

# S3 framework functions
def index():
    "Module's Home Page"
    modules = db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL, orderby=db.s3_module.priority)
    admin_name = db().select(db.s3_setting.admin_name)[0].admin_name
    admin_email = db().select(db.s3_setting.admin_email)[0].admin_email
    admin_tel = db().select(db.s3_setting.admin_tel)[0].admin_tel
    response.title = T('Sahana FOSS Disaster Management System')
    return dict(module_name=module_name, modules=modules, admin_name=admin_name, admin_email=admin_email, admin_tel=admin_tel)

def source():
    "RESTlike CRUD controller"
    return shn_rest_controller('s3', 'source')

# NB These 4 functions are unlikely to get used in production
def header():
    "Custom view designed to be pulled into an Ext layout's North Panel"
    return dict()
def footer():
    "Custom view designed to be pulled into an Ext layout's South Panel"
    return dict()
def menu():
    "Custom view designed to be pulled into the 1st item of an Ext layout's Center Panel"
    return dict()
def list():
    "Custom view designed to be pulled into an Ext layout's Center Panel"
    return dict()

def open_module():
    "Select Module"
    id = request.vars.id
    modules = db(db.s3_module.id==id).select()
    if not len(modules):
        redirect(URL(r=request, f='index'))
    module = modules[0].name
    redirect(URL(r=request, c=module, f='index'))

# About Sahana
def apath(path=''):
    "Application path"
    import os
    from gluon.fileutils import up
    opath = up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3] == '../': opath, path=up(opath), path[3:]
    return os.path.join(opath,path).replace('\\','/')

def about():
    "About Sahana page provides details on component versions."
    import sys
    python_version = sys.version
    web2py_version = open(apath('../VERSION'), 'r').read()[8:]
    sahana_version = open(os.path.join(request.folder, 'VERSION'), 'r').read()
    return dict(module_name=module_name, python_version=python_version, sahana_version=sahana_version, web2py_version=web2py_version)

def help():
    "Custom View"
    response.title = T('Help')
    return dict()
