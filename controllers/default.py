module='default'
# Current Module (for sidebar title)
module_name=db(db.module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# T2 framework functions
def login():
    response.view='login.html'
    return dict(form=t2.login(),module_name=module_name,modules=modules,options=options)
def logout(): t2.logout(next='login')
def register():
    response.view='register.html'
    t2.messages.record_created=T("You have been successfully registered")
    return dict(form=t2.register())
def profile(): t2.profile()

# S3 framework functions
def index():
    "Module's Home Page"
    response.title=T('Sahana FOSS Disaster Management System')
    return dict(module_name=module_name,modules=modules,options=options)
def open_module():
    "Select Module"
    id=request.vars.id
    modules=db(db.module.id==id).select()
    if not len(modules):
        redirect(URL(r=request,f='index'))
    module=modules[0].name
    redirect(URL(r=request,c=module,f='index'))
def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))
def configuration():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'configuration')

    
# About Sahana
def apath(path=''):
    import os
    from gluon.fileutils import up
    opath=up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3]=='../': opath,path=up(opath),path[3:]
    return os.path.join(opath,path).replace('\\','/')

def about_sahana():
    "About Sahana page provides details on component versions."
    import sys
    python_version=sys.version
    web2py_version=open(apath('../VERSION'),'r').read()[8:]
    sahana_version=open(apath('sahana/VERSION'),'r').read()
    return dict(module_name=module_name,modules=modules,options=options,python_version=python_version,sahana_version=sahana_version,web2py_version=web2py_version)

# M2M Tests
def list_dogs():
    list=t2.itemize(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def display_dog():
    list=t2.display(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def update_dog():
    list=t2.update(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def delete_dog():
    list=t2.delete(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def delete_owner():
    list=t2.delete(db.owner)
    response.view='list_plain.html'
    return dict(list=list)
