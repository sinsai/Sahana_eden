module='default'
# Current Module (for sidebar title)
module_name=db(db.module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

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
    return dict(module_name=module_name,modules=modules,options=options)

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
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    #option=options[0].name
    #_option=option.replace(' ','_')
    #option=_option.lower()
    redirect(URL(r=request,f=option))

# About Sahana
def about_sahana():
	title=T('About Sahana')
	return dict(title=title,module_name=module_name,modules=modules,options=options)

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

# Actions called by representations in Model
def display_person():
	item=t2.display(db.person)
	return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_person():
	form=t2.update(db.person)
	return dict(module_name=module_name,modules=modules,options=options,form=form)
