# -*- coding: utf-8 -*-

"""
    Default Controllers

    @author: Fran Boon
"""

module = 'default'

# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select().first().name_nice
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

    if request.args and request.args(0)=="login_next":
        # The following redirects the user to contacts page on first login - can
        # be updated for a workflow on login. This also notes the timestamp
        # of last login through the browser
        if auth.is_logged_in():
            if not auth.user.timestamp:
                db(db.auth_user.id == auth.user.id).update(timestamp = request.utcnow)
                redirect(URL(r=request, c='msg', f='pe_contact'))
            db(db.auth_user.id == auth.user.id).update(timestamp = request.utcnow)
            redirect(URL(r=request, f='index'))

    if request.args and request.args(0)=="profile":
        #auth.settings.table_user.organisation.writable = False
        auth.settings.table_user.utc_offset.readable = True
        auth.settings.table_user.utc_offset.writable = True

    auth.settings.table_user.language.label = T("Language")
    auth.settings.table_user.language.default = "en"
    auth.settings.table_user.language.comment = DIV(_class="tooltip",
        _title=T("Language|The language to use for notifications."))
    auth.settings.table_user.language.requires = IS_IN_SET(shn_languages)
    auth.settings.table_user.language.represent = lambda opt: shn_languages.get(opt, UNKNOWN_OPT)

    form = auth()

    self_registration = db().select(db.s3_setting.self_registration)[0].self_registration

    # Use Custom Ext views
    # Best to not use an Ext form for login: can't save username/password in browser & can't hit 'Enter' to submit!
    #if request.args(0) == 'login':
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
    import subprocess
    import string
    python_version = sys.version
    web2py_version = open(apath('../VERSION'), 'r').read()[8:]
    sahana_version = open(os.path.join(request.folder, 'VERSION'), 'r').read()
    try:
        sqlite_version = (subprocess.Popen(["sqlite3", "-version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()
    except:
        sqlite_version = "Not installed or available"
    try:
        mysql_version = (subprocess.Popen(["mysql", "--version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()[10:]    
    except:
        mysql_version = "Not installed or available"
    try:    
        pgsql_reply = (subprocess.Popen(["psql", "--version"], stdout=subprocess.PIPE).communicate()[0]) 
        pgsql_version = string.split(pgsql_reply)[2]
    except:
        pgsql_version = "Not installed or available"
    try:
        import MySQLdb
        pymysql_version = MySQLdb.__revision__
    except:
        pymysql_version = "Not installed or available"
    try:
        import reportlab
        reportlab_version = reportlab.Version
    except:
        reportlab_version = "Not installed or available"
    try:
        import xlwt
        xlwt_version = xlwt.__VERSION__
    except:
        xlwt_version = "Not installed or available"
    return dict(module_name=module_name,
                python_version=python_version, 
                sahana_version=sahana_version, 
                web2py_version=web2py_version, 
                sqlite_version=sqlite_version,
                mysql_version=mysql_version,
                pgsql_version=pgsql_version,
                pymysql_version=pymysql_version,
                reportlab_version=reportlab_version, 
                xlwt_version=xlwt_version)

def help():
    "Custom View"
    response.title = T('Help')
    return dict()

def contact():
    "Custom View"
    response.title = T('Contact us')
    return dict()
