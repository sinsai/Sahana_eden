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
	title=db(db.module.name=='or').select()[0].name_nice
	#title=T('Organization Registry')
    # List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.or_menu_option.enabled=='Yes').select(db.or_menu_option.ALL,orderby=db.or_menu_option.priority)
	return dict(title=title,modules=modules,options=options)

# Select Option
def open():
    id=request.vars.id
    options=db(db.or_menu_option.id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].name
    _option=option.replace(' ','_')
    option=_option.lower()
    redirect(URL(r=request,f=option))

def register_an_organisation():
	# Page Title
	title=T('Register an Organisation')
    # List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.cr_menu_option.enabled=='True').select(db.cr_menu_option.ALL,orderby=db.cr_menu_option.priority)
    
	orgs=t2.itemize(db.or_organisation)
	if orgs=="No data":
		orgs="No Organizations currently registered."
	form=t2.create(db.or_organisation)
	return dict(title=title,modules=modules,options=options,orgs=orgs,form=form)

