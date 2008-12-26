module='gis'
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
# Enable downloading of Markers & other Files
def download(): return t2.download()

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

# CRUD: Configs
def display_config():
    item=t2.display(db.gis_config)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

def list_configs():
    title=T("GIS Configs")
    list=t2.itemize(db.gis_config)
    if list=="No data":
        list="No Configs currently defined."
    form=t2.create(db.gis_config)
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list,form=form)

@t2.requires_login('login')
def update_config():
    form=t2.update(db.gis_config)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

@t2.requires_login('login')
def defaults():
    title=T("GIS Defaults")
    form=t2.update(db.gis_config,deletable=False)
    return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)
	
# CRUD: Features
def features():
    title=T("GIS Features")
    list=t2.itemize(db.gis_feature)
    if list=="No data":
        list="No Features currently defined."
    form=t2.create(db.gis_feature)
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
def add_feature():
    form=t2.create(db.gis_feature)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

def display_feature():
    item=t2.display(db.gis_feature)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

def list_features():
    title=T("GIS Features")
    list=t2.itemize(db.gis_feature)
    if list=="No data":
        list="No Features currently defined."
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list)

@t2.requires_login('login')
def update_feature():
    form=t2.update(db.gis_feature)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

# CRUD: Feature Classes
def list_feature_classes():
    title=T("GIS Feature Classes")
    list=t2.itemize(db.gis_feature_class)
    if list=="No data":
        list="No Feature Classes currently defined."
    form=t2.create(db.gis_feature_class)
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
def display_feature_class():
    item=t2.display(db.gis_feature_class)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_feature_class():
    form=t2.update(db.gis_feature_class)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

# CRUD: Key
def list_keys():
    title=T("GIS Keys")
    list=t2.itemize(db.gis_key)
    if list=="No data":
        list="No Keys currently defined."
    form=t2.create(db.gis_key)
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
def display_key():
    item=t2.display(db.gis_key)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_key():
    form=t2.update(db.gis_key)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

# CRUD: Markers
def list_markers():
    title=T("GIS Markers")
    list=t2.itemize(db.gis_marker)
    if list=="No data":
        list="No Markers currently defined."
    form=t2.create(db.gis_marker)
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
def display_marker():
    item=t2.display(db.gis_marker)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_marker():
    form=t2.update(db.gis_marker)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

# CRUD: Projections
def list_projections():
    title=T("GIS Projections")
    list=t2.itemize(db.gis_projection)
    if list=="No data":
        list="No Projections currently defined."
    form=t2.create(db.gis_projection)
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
def display_projection():
    item=t2.display(db.gis_projection)
    return dict(module_name=module_name,modules=modules,options=options,item=item)

@t2.requires_login('login')
def update_projection():
    form=t2.update(db.gis_projection)
    return dict(module_name=module_name,modules=modules,options=options,form=form)

# CRUD: Layers
def list_layers():
    title=T('GIS Layers')
    list=t2.itemize(db.gis_layer)
    if list=="No data":
        list="No Layers currently defined."
    return dict(title=title,module_name=module_name,modules=modules,options=options,list=list)
	
# Actions called by representations in Model
def display_layer():
    #db.gis_layer.displays=['name','description','type','enabled']
    #main=t2.display(db.gis_layer)

    # We want more control than T2 allows us (& we also want proper MVC separation)
    # - multiple tables
    # - names not numbers for type/subtype
    layer=db(db.gis_layer.id==t2.id).select()[0]
    type=layer.type
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

    return dict(module_name=module_name,modules=modules,options=options,layer=layer,type=type,subtype=subtype,key=key)

@t2.requires_login('login')
def update_layer():
    # Get a pointer to the Layer record (for getting default values out & saving updated values back)
    layer=db(db.gis_layer.id==t2.id).select()[0]
    
    # Pull out current settings to pre-populate form with
    type=layer.type
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
    	type_new=form.vars.type
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

    return dict(module_name=module_name,modules=modules,options=options,form=form,layer=layer,type=type,subtype=subtype,key=key,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority)

@t2.requires_login('login')
def delete_layer():
    layer=db(db.gis_layer.id==t2.id).select()[0]
    type=layer.type

    #if type=="wms":
    #    subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
    #    db(db['gis_layer_wms_%s' % subtype].layer==t2.id).delete{}
    
    # Delete Sub-Record:
    db(db['gis_layer_%s' % type].layer==t2.id).delete()
    
    # Delete Master Record
    db(db.gis_layer.id==t2.id).delete()
    
    # Notify user :)
    response.confirmation=T("Layer deleted")
    # No need for a dedicated view, we can re-use
    response.view="gis/list_layers.html"

    list=t2.itemize(db.gis_layer)
    if list=="No data":
        list="No Layers currently defined."

    return dict(module_name=module_name,modules=modules,options=options,list=list)

# Map Service Catalogue
# NB No login required: unidentified users can Read/Create (although they need to login to Update/Delete layers)
def map_service_catalogue():
    title=T('Map Service Catalogue')

    # Default to OpenStreetMap - promote Open Data!
    type="openstreetmap"
    subtype="Mapnik"
    options_subtype=["Mapnik","Osmarender","Aerial"]
    key="ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw" # Google Key for 127.0.0.1
    
    # Pull out options for dropdowns
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
            uuid=uuid.uuid4(),
            name=form.vars.name,
            description=form.vars.description,
            type=form.vars.type,
            priority=form.vars.priority,
            enabled=enabled
        )
        type_new=form.vars.type
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

    return dict(title=title,module_name=module_name,modules=modules,options=options,layers=layers,form=form,type=type,subtype=subtype,key=key,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority)

# Map Viewing Client
def map_viewing_client():
    title=T('Map Viewing Client')
    response.title=title

    # Get Config
    width=db(db.gis_config.id==1).select()[0].map_width
    height=db(db.gis_config.id==1).select()[0].map_height
    _projection=db(db.gis_config.id==1).select()[0].projection
    projection=db(db.gis_projection.uuid==_projection).select()[0].epsg
    lat=db(db.gis_config.id==1).select()[0].lat
    lon=db(db.gis_config.id==1).select()[0].lon
    zoom=db(db.gis_config.id==1).select()[0].zoom
    units=db(db.gis_projection.epsg==projection).select()[0].units
    maxResolution=db(db.gis_projection.epsg==projection).select()[0].maxResolution
    maxExtent=db(db.gis_projection.epsg==projection).select()[0].maxExtent
    
    # Get enabled Layers
    layers=db(db.gis_layer.enabled==True).select(db.gis_layer.ALL,orderby=db.gis_layer.priority)

    # Check for enabled Google layers
    google=0
    google_key=""
    for row in layers:
        if row.type=="google":
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
        if row.type=="virtualearth":
            virtualearth=1

    # Check for enabled Yahoo layers
    yahoo=0
    yahoo_key=""
    for row in layers:
        if row.type=="yahoo":
            yahoo=1
    if yahoo==1:
        # Check for Yahoo Key
        _yahoo_key=db(db.gis_key.service=='yahoo').select(db.gis_key.key)
        if len(_yahoo_key):
            yahoo_key=_yahoo_key[0].key
        else:
            response.flash=T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
            yahoo=0
            # Redirect to Key entry screen?

    return dict(title=title,module_name=module_name,modules=modules,options=options,layers=layers,google=google,google_key=google_key,virtualearth=virtualearth,yahoo=yahoo,yahoo_key=yahoo_key,width=width,height=height,projection=projection,lat=lat,lon=lon,zoom=zoom,units=units,maxResolution=maxResolution,maxExtent=maxExtent)
