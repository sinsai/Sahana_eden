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
    # Page Title
	title=db(db.module.name=='cr').select()[0].name_nice
	#title=T('Shelter Registry')
    # List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='Yes').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
	return dict(title=title,modules=modules,options=options)

# Select Option
def open():
    id=request.vars.id
    options=db(db.cr_menu_option.id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].name
    _option=option.replace(' ','_')
    option=_option.lower()
    redirect(URL(r=request,f=option))

def add_shelter():
	# Page Title
	title=T('Add Shelter')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
    
	shelters=t2.itemize(db.cr_shelter)
	if shelters=="No data":
		shelters="No Shelters currently registered."
	form=t2.create(db.cr_shelter)
	return dict(title=title,modules=modules,options=options,shelters=shelters,form=form)

# Actions called by representations in Model
def display_shelter():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
	item=t2.display(db.cr_shelter)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('../login')
def update_shelter():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
	item=t2.update(db.cr_shelter)
	return dict(modules=modules,options=options,item=item)

