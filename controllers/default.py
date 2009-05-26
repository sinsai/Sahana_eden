module = 'default'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions)
response.menu_options = []
options = db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL, orderby=db['%s_menu_option' % module].priority)
for option in options:
    if not option.access or (option.access in session.s3.roles):
        response.menu_options.append([T(option.name), False, URL(r=request,f='open_option',vars=dict(id='%d' % option.id))])

# Web2Py Tools functions
# (replaces T2)
def user():
    "Auth functions based on arg. See gluon/tools.py"
    return dict(form=auth(), module_name=module_name)

def download():
    "Download a file."
    return response.download(request, db) 

def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()
    
# S3 framework functions
def index():
    "Module's Home Page"
    admin_name = db().select(db.s3_setting.admin_name)[0].admin_name
    admin_email = db().select(db.s3_setting.admin_email)[0].admin_email
    admin_tel = db().select(db.s3_setting.admin_tel)[0].admin_tel
    response.title = T('Sahana FOSS Disaster Management System')
    return dict(module_name=module_name, options=options, admin_name=admin_name, admin_email=admin_email, admin_tel=admin_tel)

def open_module():
    "Select Module"
    id = request.vars.id
    modules = db(db.s3_module.id==id).select()
    if not len(modules):
        redirect(URL(r=request, f='index'))
    module = modules[0].name
    redirect(URL(r=request, c=module, f='index'))

def open_option():
    "Select Option from Module Menu"
    id = request.vars.id
    options = db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request, f='index'))
    option = options[0].function
    redirect(URL(r=request, f=option))

# About Sahana
def apath(path=''):
    "Application path"
    import os
    from gluon.fileutils import up
    opath = up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3] == '../': opath, path=up(opath), path[3:]
    return os.path.join(opath,path).replace('\\','/')

def about_sahana():
    "About Sahana page provides details on component versions."
    import sys
    python_version = sys.version
    web2py_version = open(apath('../VERSION'), 'r').read()[8:]
    sahana_version = open(apath('sahana/VERSION'), 'r').read()
    return dict(module_name=module_name, python_version=python_version, sahana_version=sahana_version, web2py_version=web2py_version)
