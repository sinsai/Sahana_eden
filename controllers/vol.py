# -*- coding: utf-8 -*-

module = 'vol'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions)
response.menu_options = [
    [module_name, False, URL(r=request, f='index')],
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name, options=options)
def open_option():
    "Select Option from Module Menu"
    id = request.vars.id
    options = db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request, f='index'))
    option = options[0].function
    redirect(URL(r=request, f=option))
