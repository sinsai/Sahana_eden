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

def configs():
	# Page Title
	title=T("GIS Configs")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	list=t2.itemize(db.gis_config)
	if list=="No data":
		list="No Configs currently defined."
	form=t2.create(db.gis_config)
	return dict(title=title,modules=modules,options=options,list=list,form=form)
	
# Actions called by representations in Model
def display_config():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.display(db.gis_config)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_config():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	form=t2.update(db.gis_config)
	return dict(modules=modules,options=options,form=form)

def features():
	# Page Title
	title=T("GIS Features")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	list=t2.itemize(db.gis_feature)
	if list=="No data":
		list="No Features currently defined."
	form=t2.create(db.gis_feature)
	return dict(title=title,modules=modules,options=options,list=list,form=form)
	
# Actions called by representations in Model
def add_feature():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	form=t2.create(db.gis_feature)
	return dict(modules=modules,options=options,form=form)

def display_feature():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.display(db.gis_feature)
	return dict(modules=modules,options=options,item=item)

def list_features():
	# Page Title
	title=T("GIS Features")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	list=t2.itemize(db.gis_feature)
	if list=="No data":
		list="No Features currently defined."
	return dict(title=title,modules=modules,options=options,list=list)

@t2.requires_login('login')
def update_feature():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	form=t2.update(db.gis_feature)
	return dict(modules=modules,options=options,form=form)

def feature_classes():
	# Page Title
	title=T("GIS Feature Classes")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	list=t2.itemize(db.gis_feature_class)
	if list=="No data":
		list="No Feature Classes currently defined."
	form=t2.create(db.gis_feature_class)
	return dict(title=title,modules=modules,options=options,list=list,form=form)
	
# Actions called by representations in Model
def display_feature_class():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.display(db.gis_feature_class)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_feature_class():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	form=t2.update(db.gis_feature_class)
	return dict(modules=modules,options=options,form=form)

def keys():
	# Page Title
	title=T("GIS Keys")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	list=t2.itemize(db.gis_key)
	if list=="No data":
		list="No Keys currently defined."
	form=t2.create(db.gis_key)
	return dict(title=title,modules=modules,options=options,list=list,form=form)
	
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
	
	form=t2.update(db.gis_key)
	return dict(modules=modules,options=options,form=form)

def markers():
	# Page Title
	title=T("GIS Markers")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	list=t2.itemize(db.gis_marker)
	if list=="No data":
		list="No Markers currently defined."
	form=t2.create(db.gis_marker)
	return dict(title=title,modules=modules,options=options,list=list,form=form)
	
# Actions called by representations in Model
def display_marker():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.display(db.gis_marker)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_marker():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	form=t2.update(db.gis_marker)
	return dict(modules=modules,options=options,form=form)

def projections():
	# Page Title
	title=T("GIS Projections")
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
	# List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
    
	list=t2.itemize(db.gis_projection)
	if list=="No data":
		list="No Projections currently defined."
	form=t2.create(db.gis_projection)
	return dict(title=title,modules=modules,options=options,list=list,form=form)
	
# Actions called by representations in Model
def display_projection():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	item=t2.display(db.gis_projection)
	return dict(modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_projection():
	# List Modules (from which to build Menu of Modules)
	modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
	options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)
	
	form=t2.update(db.gis_projection)
	return dict(modules=modules,options=options,form=form)

def layers():
    # Page Title
    title=T('GIS Layers')
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)

    list=t2.itemize(db.gis_layer)
    if list=="No data":
        list="No Layers currently defined."

    return dict(title=title,modules=modules,options=options,list=list)
	
# Actions called by representations in Model
def display_layer():
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)

    #db.gis_layer.displays=['name','description','type','enabled']
    #main=t2.display(db.gis_layer)

    # We want more control than T2 allows us (& we also want proper MVC separation)
    # - multiple tables
    # - names not numbers for type/subtype
    layer=db(db.gis_layer.id==t2.id).select()[0]
    type=db(db.gis_layer_type.id==layer.type).select(db.gis_layer_type.ALL)[0].name
    if type=="openstreetmap":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        key=0
    elif type=="google":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        key=db(db.gis_key.service==type).select(db.gis_key.ALL)[0].key
    elif type=="virtualearth":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        key=0
    elif type=="yahoo":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        key=db(db.gis_key.service==type).select(db.gis_key.ALL)[0].key
    else:
        subtype=0
        key=0

    return dict(modules=modules,options=options,layer=layer,type=type,subtype=subtype,key=key)

@t2.requires_login('login')
def update_layer():
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)

    # Get a pointer to the Layer record (for getting default values out & saving updated values back)
    layer=db(db.gis_layer.id==t2.id).select()[0]
    
    # Pull out current settings to pre-populate form with
    type=db(db.gis_layer_type.id==layer.type).select()[0].name
    if type=="openstreetmap":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        # Need here as well as gis_layers.js to populate the initial 'selected'
        options_subtype = ["Mapnik","Osmarender","Aerial"]
        key=0
    elif type=="google":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid", "Terrain"]
        key=db(db.gis_key.service==type).select(db.gis_key.ALL)[0].key
    elif type=="virtualearth":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
        key=0
    elif type=="yahoo":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
        key=db(db.gis_key.service==type).select(db.gis_key.ALL)[0].key
    else:
        subtype=0
        options_subtype = [""]
        key=0

    # Pull out options for dropdowns
    options_type = db().select(db.gis_layer_type.ALL)
    # 0-99, take away all used priorities, add back the current priority
    options_priority = range(100)
    options_used = db().select(db.gis_layer.priority)
    for row in options_used:
        options_priority.remove(row.priority)
    priority=layer.priority
    options_priority.insert(0,priority)
    
    # Build form
    # Neither SQLFORM nor T2 support multiple tables
    #form=SQLFORM(db.gis_layer,record,deletable=True)
    #form=t2.update(db.gis_layer)
    # Customised method could be developed by extending T2, but wouldn't give us MVC separation, so best to port it to here & view
    #form=t2.update_layer(db.gis_layer)
    # HTML is built manually in the view...this provides a hook for processing
    # we need to add validation here because this form doesn't know about the database
    form=FORM(INPUT(_name="id",requires=IS_NOT_EMPTY()),
            INPUT(_name="modified_on"),
            INPUT(_name="name",requires=IS_NOT_EMPTY()),
            INPUT(_name="description"),
            SELECT(_name="type",requires=IS_NOT_EMPTY()),
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % type].ALL)])
            SELECT(_name="subtype",requires=IS_NOT_EMPTY()),
            INPUT(_name="key",requires=IS_NOT_EMPTY()),
            # Should develop an IS_THIS_OR_IS_NOT_IN_DB(this,table) validator (so as to not rely on View)
            #INPUT(_name="priority",requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]),
            INPUT(_name="priority",requires=IS_NOT_EMPTY()),
            INPUT(_name="enabled"),
            INPUT(_type="submit"))
    
    # use T2 for conflict detection
    t2._stamp_many([db.gis_layer,db['gis_layer_%s' % type]],form)
    hidden={'modified_on__original':str(layer.get('modified_on',None))}
    if request.vars.modified_on__original and request.vars.modified_on__original!=hidden['modified_on__original']:
            session.flash=self.messages.record_was_altered
            redirect(self.action(args=request.args))
    
    # Process form
    if form.accepts(request.vars,session,keepvalues=True):
    	if form.vars.enabled=="on":
            enabled=True
        else:
            enabled=False
        # Update Database
        layer.update_record(
    		name=form.vars.name,
    		description=form.vars.description,
    		type=form.vars.type,
    		priority=form.vars.priority,
    		enabled=enabled
    	)
    	type_new=db(db.gis_layer_type.id==form.vars.type).select()[0].name
    	if type_new=="openstreetmap":
    		db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
    			type=form.vars.subtype
    		)
    	elif type_new=="google":
    		db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
    			type=form.vars.subtype
    		)
    		db(db.gis_key.service==type_new).select()[0].update_record(
    			key=form.vars.key
    		)
    	elif type_new=="virtualearth":
    		db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
    			type=form.vars.subtype
    		)
    	elif type_new=="yahoo":
    		db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
    			type=form.vars.subtype
    		)
    		db(db.gis_key.service==type_new).select()[0].update_record(
    			key=form.vars.key
    		)
    	# Notify user :)
        response.confirmation=T("Layer updated")
    elif form.errors: 
    	response.error=T("Form is invalid")
    else: 
    	response.notification=T("Please fill the form")

    return dict(modules=modules,options=options,form=form,layer=layer,type=type,subtype=subtype,key=key,options_type=options_type,options_subtype=options_subtype,options_priority=options_priority)

# Map Service Catalogue
# NB No login required: unidentified users can Read/Create layers (although they need to login to Update/Delete layers)
def map_service_catalogue():
    # Page Title
    title=T('Map Service Catalogue')
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)

    # Default to OpenStreetMap - promote Open Data!
    type="openstreetmap"
    subtype="Mapnik"
    options_subtype=["Mapnik","Osmarender","Aerial"]
    key="ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw" # Google Key for 127.0.0.1
    
    # Pull out options for dropdowns
    options_type = db().select(db.gis_layer_type.ALL)
    # 0-99, take away all used priorities
    options_priority = range(100)
    options_used = db().select(db.gis_layer.priority)
    for row in options_used:
        options_priority.remove(row.priority)
    
    # Build form
    # Neither SQLFORM nor T2 support multiple tables
    # Customised method could be developed by extending T2, but wouldn't give us MVC separation, so best to port it to here & view
    # HTML is built manually in the view...this provides a hook for processing
    # we need to add validation here because this form doesn't know about the database
    form=FORM(INPUT(_name="name",requires=IS_NOT_EMPTY()),
            INPUT(_name="description"),
            SELECT(_name="type",requires=IS_NOT_EMPTY()),
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % type].ALL)])
            SELECT(_name="subtype"),
            INPUT(_name="key",requires=IS_NOT_EMPTY()),
            INPUT(_name="priority",requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]),
            INPUT(_name="enabled"),
            INPUT(_type="submit"))

    # Process form
    if form.accepts(request.vars,session,keepvalues=True):
        if form.vars.enabled=="on":
            enabled=True
        else:
            enabled=False
        # Update Database
        id=db.gis_layer.insert(
            name=form.vars.name,
            description=form.vars.description,
            type=form.vars.type,
            priority=form.vars.priority,
            enabled=enabled
        )
        type_new=db(db.gis_layer_type.id==form.vars.type).select()[0].name
        if type_new=="openstreetmap":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=form.vars.subtype
            )
        elif type_new=="google":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=form.vars.subtype
            )
            # Check to see whether a Key already exists for this service
            if len(db(db.gis_key.service==type_new).select()):
                # Update
                db(db.gis_key.service==type_new).select()[0].update_record(
                    key=form.vars.key
                )
            else:
                # Insert
                db.gis_key.insert(
                    service=type_new,
                    key=form.vars.key
                )
        elif type_new=="virtualearth":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=form.vars.subtype
            )
        elif type_new=="yahoo":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=form.vars.subtype
            )
            # Check to see whether a Key already exists for this service
            if len(db(db.gis_key.service==type_new).select()):
                # Update
                db(db.gis_key.service==type_new).select()[0].update_record(
                    key=form.vars.key
                )
            else:
                # Insert
                db.gis_key.insert(
                    service=type_new,
                    key=form.vars.key
                )
        # Notify user :)
        response.confirmation=T("Layer updated")
    elif form.errors: 
        response.error=T("Form is invalid")
    else: 
        response.notification=T("Please fill the form")

    # Layers listed after Form so they get refreshed after submission
    layers=t2.itemize(db.gis_layer,orderby=db.gis_layer.priority)
    if layers=="No data":
        layers="No Layers currently defined."

    return dict(title=title,modules=modules,options=options,layers=layers,form=form,type=type,subtype=subtype,key=key,options_type=options_type,options_subtype=options_subtype,options_priority=options_priority)

# Map Viewing Client
def map_viewing_client():
    # Page Title
    title=T('Map Viewing Client')
    response.title=title
    # List Modules (from which to build Menu of Modules)
    modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
    # List Options (from which to build Menu for this Module)
    options=db(db.gis_menu_option.enabled=='True').select(db.gis_menu_option.ALL,orderby=db.gis_menu_option.priority)

    # Get Config
    width=db(db.gis_config.setting=='map_width').select(db.gis_config.value)[0].value
    height=db(db.gis_config.setting=='map_height').select(db.gis_config.value)[0].value
    projection=db(db.gis_config.setting=='projection').select(db.gis_config.value)[0].value
    lat=db(db.gis_config.setting=='lat').select(db.gis_config.value)[0].value
    lon=db(db.gis_config.setting=='lon').select(db.gis_config.value)[0].value
    zoom=db(db.gis_config.setting=='zoom').select(db.gis_config.value)[0].value
    units=db(db.gis_projection.epsg==projection).select()[0].units
    maxResolution=db(db.gis_projection.epsg==projection).select()[0].maxResolution
    maxExtent=db(db.gis_projection.epsg==projection).select()[0].maxExtent
    
    # Get enabled Layers
    layers=db(db.gis_layer.enabled==True).select(db.gis_layer.ALL,orderby=db.gis_layer.priority)

    # Check for enabled Google layers
    google=0
    google_key=""
    for row in layers:
        if row.type=="2":
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

    # Check for enabled Virtual Earth layers
    virtualearth=0
    for row in layers:
        if row.type=="3":
            virtualearth=1

    # Check for enabled Yahoo layers
    yahoo=0
    yahoo_key=""
    for row in layers:
        if row.type=="4":
            yahoo=1
    if yahoo==1:
        # Check for Yahoo Key
        _yahoo_key=db(db.gis_key.service=='yahoo').select(db.gis_key.key)
        if len(_yahoo_key):
            yahoo_key=_yahoo_key[0].key
        else:
            response.flash=T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
            google=0
            # Redirect to Key entry screen?

    return dict(title=title,modules=modules,options=options,layers=layers,google=google,google_key=google_key,virtualearth=virtualearth,yahoo=yahoo,yahoo_key=yahoo_key,width=width,height=height,projection=projection,lat=lat,lon=lon,zoom=zoom,units=units,maxResolution=maxResolution,maxExtent=maxExtent)
