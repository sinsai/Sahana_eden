module='default'
# Current Module (for sidebar title)
module_name=db(db.s3_module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL,orderby=db.s3_module.menu_priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# T2 framework functions
def login():
    """ Login
    >>> from applications.sahana.modules.s3_test import WSGI_Test
    >>> test=WSGI_Test(db)
    >>> '200 OK' in test.getPage('/sahana/%s/login' % module)
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody('Login')
    """
    return dict(form=t2.login(),module_name=module_name,modules=modules,options=options)
def logout():
    t2.logout(next='login')
# Self-registration can be disabled by amending the setting in the s3_settings table
def register():
    if session.s3.self_registration:
        t2.messages.record_created=T("You have been successfully registered")
        # To enable email verification, set verification=True
        return dict(form=t2.register(verification=False),module_name=module_name,modules=modules,options=options)
    else:
        redirect(URL(r=request,c='default',f='index'))
def profile():
    return dict(form=t2.profile(),module_name=module_name,modules=modules,options=options)

# S3 framework functions
def index():
    "Module's Home Page"
    admin_name=db().select(db.s3_setting.admin_name)[0].admin_name
    admin_email=db().select(db.s3_setting.admin_email)[0].admin_email
    admin_tel=db().select(db.s3_setting.admin_tel)[0].admin_tel
    response.title=T('Sahana FOSS Disaster Management System')
    return dict(module_name=module_name,modules=modules,options=options,admin_name=admin_name,admin_email=admin_email,admin_tel=admin_tel)
def open_module():
    "Select Module"
    id=request.vars.id
    modules=db(db.s3_module.id==id).select()
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
def setting():
    """RESTlike CRUD controller
    Access only permitted to admins.
    """
    if 1 in session.s3.roles:
        return shn_rest_controller(module,'setting')
    else:
        redirect(URL(r=request,f='index'))

    
# About Sahana
def apath(path=''):
    "Application path"
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

# Administration Page
def admin():
    """Administration Page.
    For now just redirect to appadmin's site view.
    """
    redirect(URL(r=request,a='admin',c='default',f='site'))
    
# Database Page
def database():
    """Database Page.
    Redirect to appadmin.
    """
    redirect(URL(r=request,c='appadmin',f='index'))
    
# Test Page
def test():
    """Test Page.
    Redirect to Selenium.
    """
    redirect(URL(r=request,c='static',f='selenium',args=['core','TestRunner.html'],vars=dict(test='../tests/TestSuite.html',auto='true')))
    
# Import Data
def import_data():
    "Import data via POST upload to CRUD controller."
    title=T('Import Data')
    return dict(module_name=module_name,modules=modules,options=options,title=title)

# Export Data
def export_data():
    "Export data via CRUD controller."
    title=T('Export Data')
    return dict(module_name=module_name,modules=modules,options=options,title=title)
