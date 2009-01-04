module='gis'
# Current Module (for sidebar title)
module_name=db(db.module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.module.enabled=='Yes').select(db.module.ALL,orderby=db.module.menu_priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# T2 framework functions
def login():
	response.view='login.html'
	return dict(form=t2.login(),module_name=module_name,modules=modules,options=options)
def logout(): t2.logout(next='login')
def register():
	response.view='register.html'
	t2.messages.record_created=T("You have been successfully registered")
	return dict(form=t2.register())
def profile(): t2.profile()
def download():
    "Enable downloading of Markers & other Files."
    return t2.download()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name,modules=modules,options=options)
def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))
def config():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'config')
def feature_class():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature_class')
def feature_metadata():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature_metadata')
def apikey():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'apikey')
def marker():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'marker')
def projection():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'projection')

# Module-specific functions

@t2.requires_login('login')
def defaults():
    """Defaults are a special case of Configs - the 1st entry.
    Don't want to be able to delete these!
    """
    title=T("GIS Defaults")
    form=t2.update(db.gis_config,deletable=False) # NB deletable=False
    return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)
	
#
# Features
#
# RESTful controller function **Non-Std**
#if isinstance(list,TABLE):
#                list.insert(0,TR('',B('Delete?')))
def feature():
    table=db.gis_feature
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Feature Details')
            edit=A(T("Edit"),_href=t2.action('feature',['update',t2.id]))
            list=A(T("List Features"),_href=t2.action('feature'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list=list)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Feature added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Feature')
                    list_btn=A(T("List Features"),_href=t2.action('feature'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature/create'})
            elif method=="display":
                t2.redirect('feature',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Feature updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Feature')
                    list_btn=A(T("List Features"),_href=t2.action('feature'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Feature deleted")
                    t2.delete(table,next='feature')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'feature/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        if t2.logged_in:
            db.gis_feature.represent=lambda table:shn_list_item(table,resource='feature',action='display',extra="INPUT(_type='checkbox',_class='delete_row',_name='delete_feature_ajax',_id='%i' % table.id)")
        else:
            db.gis_feature.represent=lambda table:shn_list_item(table,resource='feature',action='display')
        list=t2.itemize(table)
        if list=="No data":
            list="No Features currently defined."
        title=T('List Features')
        subtitle=T('Features')
        if t2.logged_in:
            if isinstance(list,TABLE):
                list.insert(0,TR('',B('Delete?')))
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Feature')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Feature"),_href=t2.action('feature','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

@t2.requires_login('login')
def delete_feature_ajax():
    "Designed to be called via AJAX to return the results into a list-container div."
    t2.delete(db.gis_feature,next='list_features_plain')
    return

def list_features_plain():
    "Designed to be called via AJAX to refresh a list-container div"
    if t2.logged_in:
        db.gis_feature.represent=lambda table:shn_list_item(table,resource='feature',action='display',extra="INPUT(_type='checkbox',_class='delete_row',_name='delete_feature_ajax',_id='%i' % table.id)")
    else:
        db.gis_feature.represent=lambda table:shn_list_item(table,resource='feature',action='display')
    list=t2.itemize(db.gis_feature)
    if list=="No data":
        list="No Features currently defined."
    if t2.logged_in:
        if isinstance(list,TABLE):
            list.insert(0,TR('',B('Delete?')))
    response.view='plain.html'
    return dict(item=list)

#
# Feature Groups
#
def feature_group():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'feature_group')

def display_feature_group_features_json():
    "Designed to be called via AJAX to be processed within JS client."
    list=db(db.gis_feature_group.id==t2.id).select(db.gis_feature_group.features).json()
    response.view='plain.html'
    return dict(item=list)

# Many-to-Many experiments
# currently using t2.tag_widget()
@t2.requires_login('login')
def feature_groups():
    title=T("GIS Feature Groups")
    subtitle=T("Add New Feature Group")
    list=t2.itemize(db.gis_feature_group)
    if list=="No data":
        list="No Feature Groups currently defined."
    # Get all available features
    _features=db(db.gis_feature.id > 0).select()
    # Put them into a list field (should be a dict to store uuid too, but t2.tag_widget doesn't support it)
    items=[]
    #items={}
    for i in range(len(_features)):
        items.append(_features[i].name)
        #items[_features[i].name]=_features[i].uuid
    db.gis_feature_group.features.widget=lambda s,v: t2.tag_widget(s,v,items)
    form=t2.create(db.gis_feature_group)
    response.view='gis/list_add.html'
    return dict(title=title,subtitle=subtitle,module_name=module_name,modules=modules,options=options,list=list,form=form)
	
@t2.requires_login('login')
def update_feature_group():
    # Get all available features
    _features=db(db.gis_feature.id > 0).select()
    items=[]
    for i in range(len(_features)):
        items.append(_features[i].name)
    db.gis_feature_group.features.widget=lambda s,v: t2.tag_widget(s,v,items)
    #form=SQLFORM(db.gis_feature_group)
    form=t2.update(db.gis_feature_group)
    db.gis_feature.represent=lambda table:shn_list_item(table,action='display')
    search=t2.search(db.gis_feature)
    return dict(module_name=module_name,modules=modules,options=options,form=form,search=search)

#
# Layers
#
# RESTful controller function for **** Multiple Tables ****
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def layer():
    resource='layer'
    table=db['%s_%s' % (module,resource)]
    crud_strings=shn_crud_strings_lookup(resource)
    
    # Which representation should output be in?
    if request.vars.format:
        representation=str.lower(request.vars.format)
    else:
        # Default to HTML
        representation="html"
    
    if len(request.args)==0:
        # No arguments => default to list (or list_create if logged_in)
        if representation=="html":
            if t2.logged_in:
                # Create Form before List to allow List to refresh after submission
                # Need to handle Multiple Tables, so go down a level of abstraction from T2
                # Function split-out to make code more readable & reusable (DRY)
                output=shn_gis_create_layer()
            list=t2.itemize(table)
            if list=="No data":
                list=crud_strings.msg_list_empty
            if isinstance(list,TABLE):
                list.insert(0,TR('',B('Enabled?'))) 
            title=crud_strings.title_list
            subtitle=crud_strings.subtitle_list
            if t2.logged_in:
                # Add a little extra context for the Form created earlier
                response.view='gis/list_create_layer.html'
                addtitle=crud_strings.subtitle_create
                output.update(dict(list=list,title=title,subtitle=subtitle,addtitle=addtitle))
                return output
            else:
                add_btn=A(crud_strings.label_create_button,_href=t2.action(resource,'create'))
                response.view='list.html'
                return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)
        elif representation=="plain":
            list=t2.itemize(table)
            response.view='plain.html'
            return dict(item=list)
        elif representation=="json":
            # ToDo supplementary tables
            list=db().select(table.ALL).json()
            response.view='plain.html'
            return dict(item=list)
        else:
            session.error=T("Unsupported format!")
            redirect(URL(r=request,f=resource))
    else:
        method=str.lower(request.args[0])
        if request.args[0].isdigit():
            # 1st argument is ID not method => display.
            if representation=="html":
                # We want more control than T2 allows us (& we also want proper MVC separation)
                # - multiple tables
                # - names not numbers for type/subtype
                resource=db(table.id==t2.id).select()[0]
                type=resource.type
                if type=="openstreetmap":
                    subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
                    apikey=0
                elif type=="google":
                    subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
                    apikey=db(db.gis_apikey.service==type).select(db.gis_apikey.ALL)[0].apikey
                elif type=="virtualearth":
                    subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
                    apikey=0
                elif type=="yahoo":
                    subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
                    apikey=db(db.gis_apikey.service==type).select(db.gis_apikey.ALL)[0].apikey
                else:
                    subtype=0
                    apikey=0

                response.view='gis/display_layer.html'
                title=crud_strings.title_display
                edit=A(T("Edit"),_href=t2.action('layer',['update',t2.id]))
                delete=A(T("Delete"),_href=t2.action('layer',['delete',t2.id]))
                list_btn=A(crud_strings.label_list_button,_href=t2.action('layer'))
                return dict(module_name=module_name,modules=modules,options=options,title=title,edit=edit,delete=delete,list_btn=list_btn,resource=resource,type=type,subtype=subtype,apikey=apikey)
            #ToDo
            #elif representation=="plain":
            elif representation=="json":
                # ToDo supplementary tables
                item=db(table.id==t2.id).select(table.ALL).json()
                response.view='plain.html'
                return dict(item=item)
            else:
                session.error=T("Unsupported format!")
                redirect(URL(r=request,f=resource))
        else:
            if method=="create":
                if t2.logged_in:
                    if representation=="html":
                        # Need to handle Multiple Tables, so go down a level of abstraction from T2
                        # Function split-out to make code more readable & reusable (DRY)
                        return shn_gis_create_layer()
                    # ToDo
                    #elif representation=="plain":
                    elif representation=="json":
                        # ToDo
                        item='{"Status":"failed","Error":{"StatusCode":501,"Message":"JSON creates not yet supported!"}}'
                        response.view='plain.html'
                        return dict(item=item)
                    else:
                        session.error=T("Unsupported format!")
                        redirect(URL(r=request,f=resource))
                else:
                    t2.redirect('login',vars={'_destination':'%s/create' % resource})
            elif method=="display":
                t2.redirect(resource,args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    if representation=="html":
                        # Need to handle Multiple Tables, so go down a level of abstraction from T2
                        # Function split-out to make code more readable
                        return shn_gis_update_layer()
                    # ToDo
                    #elif representation=="plain":
                    elif representation=="json":
                        # ToDo
                        item='{"Status":"failed","Error":{"StatusCode":501,"Message":"JSON updates not yet supported!"}}'
                        response.view='plain.html'
                        return dict(item=item)
                    else:
                        session.error=T("Unsupported format!")
                        redirect(URL(r=request,f=resource))
                else:
                    t2.redirect('login',vars={'_destination':'%s/update/%i' % (resource,t2.id)})
            elif method=="delete":
                if t2.logged_in:
                    # Need to handle Multiple Tables, so go down a level of abstraction from T2
                    layer=db(table.id==t2.id).select()[0]
                    type=layer.type
                    # Delete Sub-Record:
                    db(db['gis_layer_%s' % type].layer==t2.id).delete()
                    #if type=="wms":
                    #    subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
                    #    db(db['gis_layer_wms_%s' % subtype].layer==t2.id).delete{}
                    
                    # Delete Master Record
                    db(table.id==t2.id).delete()
                    t2.redirect(resource,flash=crud_strings.msg_record_deleted)
                else:
                    t2.redirect('login',vars={'_destination':'%s/delete/%i' % (resource,t2.id)})
            else:
                session.error=T("Unsupported method!")
                redirect(URL(r=request,f=resource))


@t2.requires_login('login')
def shn_gis_create_layer():
    """
    Create Layer records across Multiple Tables
    Designed to be called as a function from within the 'layer' RESTful controller.
    This breaks it apart for easier comprehension.
    It also allow re-use: DRY.
    """

    # Default to OpenStreetMap - promote Open Data!
    type="openstreetmap"
    subtype="Mapnik"
    options_subtype=["Mapnik","Osmarender","Aerial"]
    apikey="ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw" # Google Key for 127.0.0.1
    
    # Pull out options for dropdowns
    options_feature_group=db().select(db.gis_feature_group.ALL,orderby=db.gis_feature_group.name)
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
    # (We could make the main table a SQLFORM to be auto-validating & auto-processing leaving us to just do other tables manually)
    customform=FORM(INPUT(_name="name",requires=IS_NOT_EMPTY()),
            INPUT(_name="description"),
            SELECT(_name="type",requires=IS_NOT_EMPTY()),
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % type].ALL)])
            SELECT(_name="subtype"),
            #INPUT(_name="apikey",requires=IS_NOT_EMPTY()),
            INPUT(_name="apikey"),
            SELECT(_name="feature_group"),
            INPUT(_name="priority",requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]),
            INPUT(_name="enabled"),
            INPUT(_type="submit"))

    # Process form
    if customform.accepts(request.vars,session,keepvalues=True):
        if customform.vars.enabled=="on":
            enabled=True
        else:
            enabled=False
        # Insert Master Record
        id=db.gis_layer.insert(
            uuid=uuid.uuid4(),
            name=customform.vars.name,
            description=customform.vars.description,
            type=customform.vars.type,
            priority=customform.vars.priority,
            enabled=enabled
        )
        type_new=customform.vars.type
        # Insert Sub-Record(s):
        if type_new=="openstreetmap":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=customform.vars.subtype
            )
        elif type_new=="google":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=customform.vars.subtype
            )
            # Check to see whether a Key already exists for this service
            if len(db(db.gis_apikey.service==type_new).select()):
                # Update
                db(db.gis_apikey.service==type_new).select()[0].update_record(
                    apikey=customform.vars.apikey
                )
            else:
                # Insert
                db.gis_apikey.insert(
                    service=type_new,
                    apikey=customform.vars.apikey
                )
        elif type_new=="virtualearth":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=customform.vars.subtype
            )
        elif type_new=="yahoo":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                type=customform.vars.subtype
            )
            # Check to see whether a Key already exists for this service
            if len(db(db.gis_apikey.service==type_new).select()):
                # Update
                db(db.gis_apikey.service==type_new).select()[0].update_record(
                    apikey=customform.vars.apikey
                )
            else:
                # Insert
                db.gis_apikey.insert(
                    service=type_new,
                    apikey=customform.vars.apikey
                )
        elif type_new=="features":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                feature_group=customform.vars.feature_group
            )
        # Notify user :)
        response.confirmation=T("Layer updated")
    elif customform.errors: 
        response.error=T("Form is invalid")
    else: 
        response.notification=T("Please fill the form")

    # Layers listed after Form so they get refreshed after submission
    #layers=t2.itemize(db.gis_layer,orderby=db.gis_layer.priority)
    #if layers=="No data":
    #    layers="No Layers currently defined."
    #if isinstance(layers,TABLE):
    #    layers.insert(0,TR('',B('Enabled?'))) 

    response.view='gis/create_layer.html'
    title=T('Add Layer')
    list_btn=A(T("List Layers"),_href=t2.action('layer'))
    return dict(module_name=module_name,modules=modules,options=options,customform=customform,title=title,list_btn=list_btn,type=type,subtype=subtype,apikey=apikey,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority,options_feature_group=options_feature_group)


@t2.requires_login('login')
def shn_gis_update_layer():
    """
    Update Layer records across Multiple Tables.
    Designed to be called as a function from within the 'layer' RESTful controller.
    This breaks it apart for easier comprehension.
    """
    
    # Provide defaults for fields which only appear for some types
    subtype=0
    options_subtype = [""]
    feature_group=0
    apikey=0

    # Get a pointer to the Layer record (for getting default values out & saving updated values back)
    resource=db(db.gis_layer.id==t2.id).select()[0]
    
    # Pull out current settings to pre-populate form with
    type=resource.type
    if type=="openstreetmap":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        # Need here as well as gis_layers.js to populate the initial 'selected'
        options_subtype = ["Mapnik","Osmarender","Aerial"]
    elif type=="google":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid", "Terrain"]
        apikey=db(db.gis_apikey.service==type).select(db.gis_apikey.ALL)[0].apikey
    elif type=="virtualearth":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
    elif type=="yahoo":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
        apikey=db(db.gis_apikey.service==type).select(db.gis_apikey.ALL)[0].apikey
    elif type=="features":
        feature_group=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].feature_group
    else:
        # Invalid! We should trap & give a nice error message (although Web2Py's Tracebacks are pretty good really)
        pass
        
    # Pull out options for dropdowns
    options_feature_group=db().select(db.gis_feature_group.ALL,orderby=db.gis_feature_group.name)
    # 0-99, take away all used priorities, add back the current priority
    options_priority = range(100)
    options_used = db().select(db.gis_layer.priority)
    for row in options_used:
        options_priority.remove(row.priority)
    priority=resource.priority
    options_priority.insert(0,priority)
    
    # Build form
    # Neither SQLFORM nor T2 support multiple tables
    # Customised method could be developed by extending T2, but wouldn't give us MVC separation, so best to port it to here & view
    # HTML is built manually in the view...this provides a hook for processing
    # we need to add validation here because this form doesn't know about the database
    # (We could make the main table a SQLFORM to be auto-validating & auto-processing leaving us to just do other tables manually)
    customform=FORM(INPUT(_name="id",requires=IS_NOT_EMPTY()),
            INPUT(_name="modified_on"),
            INPUT(_name="name",requires=IS_NOT_EMPTY()),
            INPUT(_name="description"),
            SELECT(_name="type",requires=IS_NOT_EMPTY()),
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % type].ALL)])
            SELECT(_name="subtype",requires=IS_NOT_EMPTY()),
            SELECT(_name="feature_group"),
            INPUT(_name="apikey",requires=IS_NOT_EMPTY()),
            # Should develop an IS_THIS_OR_IS_NOT_IN_DB(this,table) validator (so as to not rely on View)
            #INPUT(_name="priority",requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]),
            INPUT(_name="priority",requires=IS_NOT_EMPTY()),
            INPUT(_name="enabled"),
            INPUT(_type="submit"))
    
    # use T2 for conflict detection
    # This mod needs testing!
    t2._stamp_many([db.gis_layer,db['gis_layer_%s' % type]],customform)
    hidden={'modified_on__original':str(resource.get('modified_on',None))}
    if request.vars.modified_on__original and request.vars.modified_on__original!=hidden['modified_on__original']:
            session.flash=self.messages.record_was_altered
            redirect(self.action(args=request.args))
    
    # Process form
    if customform.accepts(request.vars,session,keepvalues=True):
        if customform.vars.enabled=="on":
            enabled=True
        else:
            enabled=False
        # Update Master Record
        resource.update_record(
            name=customform.vars.name,
            description=customform.vars.description,
            type=customform.vars.type,
            priority=customform.vars.priority,
            enabled=enabled
        )
        type_new=customform.vars.type
        # Update Sub-Record(s):
        if type_new=="openstreetmap":
            db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
                type=customform.vars.subtype
            )
        elif type_new=="google":
            db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
                type=customform.vars.subtype
            )
            db(db.gis_apikey.service==type_new).select()[0].update_record(
                apikey=customform.vars.apikey
            )
        elif type_new=="virtualearth":
            db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
                type=customform.vars.subtype
            )
        elif type_new=="yahoo":
            db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
                type=customform.vars.subtype
            )
            db(db.gis_apikey.service==type_new).select()[0].update_record(
                apikey=customform.vars.apikey
            )
        elif type_new=="features":
            db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
                feature_group=customform.vars.feature_group
            )
        # Notify user :)
        response.confirmation=T("Layer updated")
    elif customform.errors: 
        response.error=T("Form is invalid")
    else: 
        response.notification=T("Please fill the form")

    response.view='gis/update_layer.html'
    title=T('Edit Layer')
    list_btn=A(T("List Layers"),_href=t2.action('layer'))
    return dict(module_name=module_name,modules=modules,options=options,customform=customform,title=title,list_btn=list_btn,resource=resource,type=type,subtype=subtype,apikey=apikey,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority,options_feature_group=options_feature_group,feature_group=feature_group)

def map_service_catalogue():
    """Map Service Catalogue.
    Extends layer/list_create for improved user UI."""

    output=shn_gis_create_layer()
    # Layers listed after Form so they get refreshed after submission
    list=t2.itemize(db.gis_layer)
    if list=="No data":
        list="No Layers currently defined."
    if isinstance(list,TABLE):
        list.insert(0,TR('',B('Enabled?'))) 
    
    response.view='gis/list_create_layer.html'
    title=T('Map Service Catalogue')
    subtitle=T('Layers')
    addtitle=T('Add New Layer')
    output.update(dict(list=list,title=title,subtitle=subtitle,addtitle=addtitle))
    return output

def map_viewing_client():
    """Map Viewing Client.
    Main user UI for viewing the Maps."""
    
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
        _google_key=db(db.gis_apikey.service=='google').select(db.gis_apikey.apikey)
        if len(_google_key):
            google_key=_google_key[0].apikey
        else:
            response.warning=T('Please enter a Google Key if you wish to use Google Layers')
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
        _yahoo_key=db(db.gis_apikey.service=='yahoo').select(db.gis_apikey.apikey)
        if len(_yahoo_key):
            yahoo_key=_yahoo_key[0].apikey
        else:
            response.warning=T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
            yahoo=0
            # Redirect to Key entry screen?

    return dict(title=title,module_name=module_name,modules=modules,options=options,layers=layers,google=google,google_key=google_key,virtualearth=virtualearth,yahoo=yahoo,yahoo_key=yahoo_key,width=width,height=height,projection=projection,lat=lat,lon=lon,zoom=zoom,units=units,maxResolution=maxResolution,maxExtent=maxExtent)
