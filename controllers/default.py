module='default'
# Current Module (for sidebar title)
module_name=db(db.module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# Login
def login():
    response.view='login.html'
    return dict(form=t2.login())
def logout(): t2.logout(next='login')
def register():
    response.view='register.html'
    return dict(form=t2.register())
def profile(): t2.profile()

def index():
    # Tab list at top-right
    #app=request.application
    #response.menu=[
    #  [T('Home'),request.function=='index','/%s/default/index'%app],
    #  [T('Admin'),request.function=='index','/%s/default/admin'%app]]
    
    response.title=T('Sahana FOSS Disaster Management System')
    return dict(module_name=module_name,modules=modules,options=options)

# Open Module
def open_module():
	id=request.vars.id
	modules=db(db.module.id==id).select()
	if not len(modules):
		redirect(URL(r=request,f='index'))
	module=modules[0].name
	redirect(URL(r=request,c=module,f='index'))

# Select Option
def open_option():
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    #option=options[0].name
    #_option=option.replace(' ','_')
    #option=_option.lower()
    redirect(URL(r=request,f=option))

# About Sahana
def apath(path=''):
    import os
    from gluon.fileutils import up
    opath=up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3]=='../': opath,path=up(opath),path[3:]
    return os.path.join(opath,path).replace('\\','/')

def about_sahana():
    import sys
    python_version=sys.version
    web2py_version=open(apath('../VERSION'),'r').read()[8:]
    sahana_version=open(apath('sahana/VERSION'),'r').read()
    return dict(module_name=module_name,modules=modules,options=options,python_version=python_version,sahana_version=sahana_version,web2py_version=web2py_version)
