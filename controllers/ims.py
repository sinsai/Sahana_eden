module = 'ims'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions)
response.menu_options = []
options = db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL, orderby=db['%s_menu_option' % module].priority)
for option in options:
    if not option.access or (option.access in session.s3.roles):
        response.menu_options.append([T(option.name), False, URL(r=request,f='open_option',vars=dict(id='%d' % option.id))])

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
