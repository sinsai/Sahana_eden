# Login
def login():
	response.view='login.html'
	return dict(form=t2.login())
def logout(): t2.logout(next='login')
def register():
	response.view='register.html'
	return dict(form=t2.register())
def profile(): t2.profile()
# Enable downloading of Markers & other Files
def download(): return t2.download()

def index():
    # Page Title
    title=db(db.module.name=='gis').select()[0].name_nice
	#title=T('Situation Awareness')
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    return dict(title=title,modules=modules,options=options)

# Select Option
def open():
    id=request.vars.id
    options=db(db.gis_menu_option.id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].name
    _option=option.replace(' ','_')
    option=_option.lower()
    redirect(URL(r=request,f=option))

# Map Service Catalogue
def map_service_catalogue():
	# Page Title
	title=T('Map Service Catalogue')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	#layers=t2.itemize(db.gis_layer,query='gis_layer.id==gis_layer_openstreetmap.layer')
	layers=t2.itemize(db.gis_layer)
	if layers=="No data":
		layers="No Layers currently defined."
	
	#form=t2.create(db.gis_layer)
	#[OPTION(x.name,_value=x.id)for x in db().select(db.gis_layer_type.ALL)]
	#types=['openstreetmap','google']
	# We'll update this list dynamically using jQuery
	subtypes=['mapnik','osmarender']
	form=FORM(TABLE(TR(T("Name:"),INPUT(_type="text",_name="name")),
				TR(T("Description:"),INPUT(_type="text",_name="description")),
				TR(T("Type:"),SELECT(_type="select",_name="type",*[OPTION(x.name,_value=x.id)for x in db().select(db.gis_layer_type.ALL)])),
				TR(T("Sub-type:"),SELECT(_type="select",_name="subtype",*subtypes)),
                TR(T("Priority:"),INPUT(_type="text",_name="priority")),
				TR(T("Enabled:"),INPUT(_type="checkbox",_name="enabled",value=True)),
				TR("",INPUT(_type="submit",_value=T("Submit")))))
	if form.accepts(request.vars,session):
		db.gis_layer.insert(
			name=form.vars.name,
			description=form.vars.description,
			type=form.vars.type,
			priority=form.vars.priority,
			enabled=form.vars.enabled
		)
		#type=db(db.gis_layer_type.id==form.vars.type).select()[0].name
		#id=db(db.gis_layer.name==form.vars.name).select()[0].id
		#if type=="openstreetmap":
		#	db.gis_layer_openstreetmap.insert(
		#		layer=id,
		#		type=form.vars.subtype
		#	)
		#if type=="google":
		#	db.gis_layer_google.insert(
		#		layer=id,
		#		type=form.vars.subtype
		#	)
		#	db.gis_key.insert(
		#		layer=id,
		#		key=form.vars.key
		#	)
		response.confirmation=T("Layer added")
		# Need to refresh the layer list using jQuery
	elif form.errors: 
		response.error=T("Form is invalid")
	else: 
		response.notification=T("Please fill the form")

	return dict(title=title,modules=modules,options=options,layers=layers,form=form)

def keys():
	# Page Title
	title=T('GIS Keys')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	keys=t2.itemize(db.gis_key)
	if keys=="No data":
		keys="No Keys currently defined."
	form=t2.create(db.gis_key)
	return dict(title=title,modules=modules,options=options,keys=keys,form=form)
	
def layers():
	# Page Title
	title=T('GIS Layers')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	layers=t2.itemize(db.gis_layer)
	if layers=="No data":
		layers="No Layers currently defined."

	#form=t2.create(db.gis_layer)
	form=FORM(TABLE(TR(T("Name:"),INPUT(_type="text",_name="name")),
				TR(T("Description:"),INPUT(_type="text",_name="description")),
				TR(T("Type:"),SELECT(_type="select",_name="type",*[OPTION(x.name,_value=x.id)for x in db().select(db.gis_layer_type.ALL)])),
				TR(T("Sub-type:"),SELECT(_type="select",_name="subtype",*[OPTION("mapnik","osmarender","satellite","hybrid","terrain")])),
                TR(T("Priority:"),INPUT(_type="text",_name="priority")),
				TR(T("Enabled:"),INPUT(_type="checkbox",_name="enabled",value=True)),
				TR("",INPUT(_type="submit",_value=T("Submit")))))
	if form.accepts(request.vars,session,keepvalues=True):
		db(db.gis_layer.id==t2.id).update(
			name=form.vars.name,
			description=form.vars.description,
			type=form.vars.type,
			priority=form.vars.priority,
			enabled=form.vars.enabled
		)
		type=db(db.gis_layer_type.id==form.vars.type).select()[0].name
		if type=="openstreetmap":
			db(db.gis_layer_openstreetmap.layer==t2.id).update(
				type=form.vars.subtype
			)
		if type=="google":
			db(db.gis_layer_google.layer==t2.id).update(
				type=form.vars.subtype
			)
		#	db.gis_key.insert(
		#		key=form.vars.key
		#	)
		response.confirmation=T("Layer added")
	elif form.errors: 
		response.error=T("Form is invalid")
	else: 
		response.notification=T("Please fill the form")

	return dict(title=title,modules=modules,options=options,layers=layers,form=form)
	
# Actions called by representations in Model
def display_key():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.display(db.gis_key)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_key():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.update(db.gis_key)
	return dict(modules=modules,options=options,item=item)

def display_layer():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	#db.gis_layer.displays=['name','description','type','enabled']
	#main=t2.display(db.gis_layer)
	# We want more control than T2 allows us
	# - type_nice
	# - Req fields
	layer=db(db.gis_layer.id==t2.id).select()[0]
	type_nice=db(db.gis_layer_type.id==layer.type).select()[0].name
	# !!! This has been moved to the View!!!
	main=DIV(TABLE(TR(LABEL(T("Name:")),layer.name),
				TR(LABEL(T("Description:")),T(layer.description)),
				TR(LABEL(T("Type:")),type_nice),
				#TR(LABEL(T("Sub-type:")),layer.name),
				#TR(LABEL(T("Priority:")),layer.priority),
				TR(LABEL(T("Enabled:")),layer.enabled)),_class="t2-display")
	
	#type=db(db.gis_layer.id==t2.id).select()[0].type
	#if type=='google':
	#	type_display=t2.display(db.gis_layer_google,query='gis_layer_google.layer==id')
	#elif type=='openstreetmap':
	#	type_display=t2.display(db.gis_layer_openstreetmap,query='gis_layer_openstreetmap.layer==id')
		
	#return dict(modules=modules,options=options,main=main,type=type_display)
	return dict(modules=modules,options=options,layer=layer,type_nice=type_nice)

@t2.requires_login('login')
def update_layer():
    # List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	# T2 form doesn't handle multiple tables :/
	#form=t2.update(db.gis_layer)
	# SQLFORM not good either: http://groups.google.com/group/web2py/browse_thread/thread/292e4ed76de9889b
	#form=SQLFORM(db.gis_layer,fields=['name','description','type','priority','enabled'])
	#form=form_factory(SQLField('type', label='Type:',requires=IS_IN_SET(['openstreetmap','google']))) 
	
	# Pull out current settings to pre-populate form with
	layer=db(db.gis_layer.id==t2.id).select()[0]
	types=['openstreetmap','google']
	subtypes=['mapnik','osmarender']
	# Build form
	form=FORM(TABLE(TR(T("Name:"),INPUT(_type="text",_name="name",_value=layer.name)),
                    TR(T("Description:"),INPUT(_type="text",_name="description",_value=layer.description)),
					# How to get list of options & yet also set default?
                    #[OPTION(x.name,_value=x.id)for x in db().select(db.gis_layer_type.ALL)]
					TR(T("Type:"),SELECT(_type="select",_name="type",*types)),
                    TR(T("Sub-type:"),SELECT(_type="select",_name="subtype",*subtypes)),
					TR(T("Priority:"),INPUT(_type="text",_name="priority",_value=layer.priority)),
					TR(T("Enabled:"),INPUT(_type="checkbox",_name="enabled",value=layer.enabled)),
                    TR("",INPUT(_type="submit",_value=T("Submit")))))
	# Add link to AJAX for hiding/unhiding rows
	#_onclick="ajax('ajaxwiki_onclick',['text'],'html')"
	if form.accepts(request.vars,session,keepvalues=True):
		db(db.gis_layer.id==t2.id).update(
			name=form.vars.name,
			description=form.vars.description,
			type=form.vars.type,
			priority=form.vars.priority,
			enabled=form.vars.enabled
		)
		type=db(db.gis_layer_type.id==form.vars.type).select()[0].name
		if type=="openstreetmap":
			db(db.gis_layer_openstreetmap.layer==t2.id).update(
				type=form.vars.subtype
			)
		if type=="google":
			db(db.gis_layer_google.layer==t2.id).update(
				type=form.vars.subtype
			)
		#	db.gis_key.insert(
		#		key=form.vars.key
		#	)
		response.confirmation=T("Layer updated")
	elif form.errors: 
		response.error=T("Form is invalid")
	else: 
		response.notification=T("Please fill the form")

	return dict(modules=modules,options=options,form=form)

# Map Viewing Client
def map_viewing_client():
    # Page Title
	title=T('Map Viewing Client')
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	# Get Config
	projection=db(db.gis_config.setting=='projection').select(db.gis_config.value)[0].value
	
    # Get enabled Layers
	layers=db(db.gis_layer.enabled==True).select(db.gis_layer.ALL,orderby=db.gis_layer.priority)
	
	# Check for enabled Google layers
	google=0
	google_key=""
	for row in layers:
		if row.type=='google':
			google=1
	if google==1:
		# Check for Google Key
		_google_key=db(db.gis_key.service=='google').select(db.gis_key.key)
		if len(_google_key):
			google_key=_google_key[0].key
		else:
			response.flash=T('Please enter a Google Key if you wish to use Google Layers')
			google=0
			# Redirect to Key entry screen?
	
	return dict(title=title,modules=modules,options=options,layers=layers,google=google,google_key=google_key,projection=projection)

#def map_viewing_client_ext():
    # Get enabled Layers
#	layers=db((db.gis_layer.enabled==True)).select(db.gis_layer.ALL,orderby=db.gis_layer.name)
    
	# Check for enabled Google layers
#	google=0
#	google_key=""
#	for row in base_layers:
#		if row.type=='google':
#			google=1
#	if google==1:
		# Check for Google Key
#		_google_key=db(db.gis_key.service=='google').select(db.gis_key.key)
#		if len(_google_key):
#			google_key=_google_key[0].key
#		else:
#			response.flash=T('Please enter a Google Key if you wish to use Google Layers')
#			google=0
			# Redirect to Key entry screen?
	
#	return dict(google=google,google_key=google_key)
