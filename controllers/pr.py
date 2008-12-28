module='pr'
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
def open_option():
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))

# NB No login required: unidentified users can Read/Create people (although they need to login to Update/Delete)
def add_person():
	title=T('Add Person')
	form=t2.create(db.person)
	return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)

def list_persons():
	title=T('List People')
	list=t2.itemize(db.person)
	if list=="No data":
		list="No People currently registered."
	return dict(title=title,module_name=module_name,modules=modules,options=options,list=list)

def display_person():
	item=t2.display(db.person)
	return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_person():
	form=t2.update(db.person)
	return dict(module_name=module_name,modules=modules,options=options,form=form)

def add_contact():
	title=T('Add Contact')
    # This needs to be amended to include the Contact table fields...
	form=t2.create(db.person)
	return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)
