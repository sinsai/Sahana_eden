module='budget'
# Current Module (for sidebar title)
module_name=db(db.s3_module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL,orderby=db.s3_module.priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

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

def parameter():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'parameter')
def item():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'item',main='code',list='table')
def kit():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'kit',main='code',list='table')
def bundle():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'bundle')
def staff_type():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'staff_type')
def location():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'location',main='code')
def project():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'project',main='code',extra='title')
def budget():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'budget')
def budget_equipment():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'budget_equipment')
def budget_staff():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'budget_staff')
