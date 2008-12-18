module='cr'
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
    return dict(module_name=module_name,modules=modules,options=options)

# Select Option
def open():
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))

# NB No login required: unidentified users can Read/Create (although they need to login to Update/Delete)
def add_shelter():
    title=T('Register New Shelter')
    form=t2.create(db.cr_shelter)
    return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)

def list_shelters():
    title=T('List Shelters')
    list=t2.itemize(db.cr_shelter)
    if list=="No data":
        list="No Shelters currently registered."
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list)

def display_shelter():
    item=t2.display(db.cr_shelter)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_shelter():
    form=t2.update(db.cr_shelter)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

@t2.requires_login('login')
def delete_shelter():
    # Delete Record from Database
    db(db.cr_shelter.id==t2.id).delete()
    # Notify user :)
    response.confirmation=T("Shelter deleted")
    # No need for a dedicated view, we can re-use
    response.view="cr/list_shelters.html"

    list=t2.itemize(db.cr_shelter.id)
    if list=="No data":
        list="No Shelters currently defined."

    return dict(module_name=module_name,modules=modules,options=options,list=list)
