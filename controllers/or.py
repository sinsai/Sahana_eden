module='or'
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
def add_organisation():
	title=T('Register New Organisation')
	form=t2.create(db.or_organisation)
	return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)

def list_organisations():
	title=T('List Organisations')
	list=t2.itemize(db.or_organisation)
	if list=="No data":
		list="No Organisations currently registered."
	return dict(title=title,module_name=module_name,modules=modules,options=options,list=list)

# Actions called by representations in Model
def display_organisation():
	item=t2.display(db.or_organisation)
	return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_organisation():
	form=t2.update(db.or_organisation)
	return dict(module_name=module_name,modules=modules,options=options,form=form)

@t2.requires_login('login')
def delete_organisation():
    # Delete Record from Database
    db(db.or_organisation.id==t2.id).delete()
    # Notify user :)
    response.confirmation=T("Organisation deleted")
    # No need for a dedicated view, we can re-use
    response.view="or/list_organisations.html"

    list=t2.itemize(db.or_organisation.id)
    if list=="No data":
        list="No Organisations currently defined."

    return dict(module_name=module_name,modules=modules,options=options,list=list)
