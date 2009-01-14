def layer():
    """
    RESTlike controller function for Multiple Tables using Custom Forms
    Deprecated as of r52
    - kept as an example of how to process custom forms
    """
    resource='layer'
    table=db['%s_%s' % (module,resource)]
    s3.crud_strings=shn_crud_strings_lookup(resource)
    
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
                list=s3.crud_strings.msg_list_empty
            if isinstance(list,TABLE):
                list.insert(0,TR('',B('Enabled?'))) 
            title=s3.crud_strings.title_list
            subtitle=s3.crud_strings.subtitle_list
            if t2.logged_in:
                # Add a little extra context for the Form created earlier
                response.view='gis/list_create_layer.html'
                addtitle=s3.crud_strings.subtitle_create
                output.update(dict(list=list,title=title,subtitle=subtitle,addtitle=addtitle))
                return output
            else:
                add_btn=A(s3.crud_strings.label_create_button,_href=t2.action(resource,'create'))
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
                layertype=resource.type
                if layertype=="openstreetmap":
                    subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
                    apikey=0
                elif layertype=="google":
                    subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
                    apikey=db(db.gis_apikey.service==layertype).select(db.gis_apikey.ALL)[0].apikey
                elif layertype=="virtualearth":
                    subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
                    apikey=0
                elif layertype=="yahoo":
                    subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
                    apikey=db(db.gis_apikey.service==layertype).select(db.gis_apikey.ALL)[0].apikey
                else:
                    subtype=0
                    apikey=0

                response.view='gis/display_layer.html'
                title=s3.crud_strings.title_display
                edit=A(T("Edit"),_href=t2.action('layer',['update',t2.id]))
                delete=A(T("Delete"),_href=t2.action('layer',['delete',t2.id]))
                list_btn=A(s3.crud_strings.label_list_button,_href=t2.action('layer'))
                return dict(module_name=module_name,modules=modules,options=options,title=title,edit=edit,delete=delete,list_btn=list_btn,resource=resource,layertype=layertype,subtype=subtype,apikey=apikey)
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
                    layertype=layer.type
                    # Delete Sub-Record:
                    db(db['gis_layer_%s' % layertype].layer==t2.id).delete()
                    #if layertype=="wms":
                    #    subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
                    #    db(db['gis_layer_wms_%s' % subtype].layer==t2.id).delete{}
                    
                    # Delete Master Record
                    db(table.id==t2.id).delete()
                    t2.redirect(resource,flash=s3.crud_strings.msg_record_deleted)
                else:
                    t2.redirect('login',vars={'_destination':'%s/delete/%i' % (resource,t2.id)})
            else:
                session.error=T("Unsupported method!")
                redirect(URL(r=request,f=resource))


@t2.requires_login('login')
def shn_gis_create_layer():
    """
    Create Layer records across Multiple Tables
    Designed to be called as a function from within the 'layer' RESTlike controller.
    This breaks it apart for easier comprehension.
    It also allow re-use: DRY.
    
    Deprecated as of r52
    - kept as an example of how to process custom forms
    """

    # Default to OpenStreetMap - promote Open Data!
    layertype="openstreetmap"
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
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % layertype].ALL)])
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
    return dict(module_name=module_name,modules=modules,options=options,customform=customform,title=title,list_btn=list_btn,layertype=layertype,subtype=subtype,apikey=apikey,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority,options_feature_group=options_feature_group)

@t2.requires_login('login')
def shn_gis_update_layer():
    """
    Update Layer records across Multiple Tables.
    Designed to be called as a function from within the 'layer' RESTlike controller.
    This breaks it apart for easier comprehension.
    
    Deprecated as of r52
    - kept as an example of how to process custom forms
    """
    
    # Provide defaults for fields which only appear for some types
    subtype=0
    options_subtype = [""]
    feature_group=0
    apikey=0

    # Get a pointer to the Layer record (for getting default values out & saving updated values back)
    resource=db(db.gis_layer.id==t2.id).select()[0]
    
    # Pull out current settings to pre-populate form with
    layertype=resource.type
    if layertype=="openstreetmap":
        subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
        # Need here as well as gis_layers.js to populate the initial 'selected'
        options_subtype = ["Mapnik","Osmarender","Aerial"]
    elif layertype=="google":
        subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid", "Terrain"]
        apikey=db(db.gis_apikey.service==layertype).select(db.gis_apikey.ALL)[0].apikey
    elif layertype=="virtualearth":
        subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
    elif layertype=="yahoo":
        subtype=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
        apikey=db(db.gis_apikey.service==layertype).select(db.gis_apikey.ALL)[0].apikey
    elif layertype=="features":
        feature_group=db(db['gis_layer_%s' % layertype].layer==t2.id).select(db['gis_layer_%s' % layertype].ALL)[0].feature_group
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
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % layertype].ALL)])
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
    t2._stamp_many([db.gis_layer,db['gis_layer_%s' % layertype]],customform)
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
    return dict(module_name=module_name,modules=modules,options=options,customform=customform,title=title,list_btn=list_btn,resource=resource,layertype=layertype,subtype=subtype,apikey=apikey,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority,options_feature_group=options_feature_group,feature_group=feature_group)
