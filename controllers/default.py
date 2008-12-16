# Login
def login(): return dict(form=t2.login())
def logout(): t2.logout(next='login')
def register(): return dict(form=t2.register())
def profile(): t2.profile()

def index():
    # Tab list at top-right
    #app=request.application
    #response.menu=[
    #  [T('Home'),request.function=='index','/%s/default/index'%app],
    #  [T('Admin'),request.function=='index','/%s/default/admin'%app]]
    
    response.title=T('Sahana FOSS Disaster Management System')
    
    # Message to flash up
    #response.flash=T('Proof of Concept for a rewrite in Web2Py')

    # Page Title
    title=db(db.module.name=='default').select()[0].name_nice
	#title=T('Sahana Home')
    
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.home_menu_option.enabled=='True').select(db.home_menu_option.ALL,orderby=db.home_menu_option.priority)
    return dict(title=title,modules=modules,options=options)

# Open Module
def open_mod():
	id=request.vars.id
	modules=db(db.module.id==id).select()
	if not len(modules):
		redirect(URL(r=request,f='index'))
	module=modules[0].name
	redirect(URL(r=request,c=module,f='index'))

# Select Option
def open():
	id=request.vars.id
	options=db(db.home_menu_option.id==id).select()
	if not len(options):
		redirect(URL(r=request,f='index'))
	option=options[0].name
	_option=option.replace(' ','_')
	option=_option.lower()
	redirect(URL(r=request,f=option))

# About Sahana
def about_sahana():
	# Page Title
	title=T('About Sahana')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.home_menu_option.enabled=='True').select(db.home_menu_option.ALL,orderby=db.home_menu_option.priority)
	return dict(title=title,modules=modules,options=options)

# NB No login required: unidentified users can Read/Create people (although they need to login to Update/Delete)
def add_person():
	# Page Title
	title=T('Add Person')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
    
	form=t2.create(db.person)
	return dict(title=title,modules=modules,options=options,form=form)

def list_persons():
	# Page Title
	title=T('List People')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
    
	list=t2.itemize(db.person)
	if list=="No data":
		list="No People currently registered."
	return dict(title=title,modules=modules,options=options,list=list)

# Actions called by representations in Model
def display_person():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)

	item=t2.display(db.person)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_person():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)

	form=t2.update(db.person)
	return dict(modules=modules,options=options,form=form)

