module='pr'
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
    response.view='default/login.html'
    return dict(form=t2.login(),module_name=module_name,modules=modules,options=options)
def logout(): t2.logout(next='login')
def register(): redirect(URL(r=request,c='default',f='register'))
def profile(): redirect(URL(r=request,c='default',f='profile'))

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name,modules=modules,options=options)
def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))
def person():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'person')
def contact():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'contact')
