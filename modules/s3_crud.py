class CrudController():
    """
    RESTlike Crud controller converted to a class so that it can be extended for Many<>Many, etc
    
    Work-in-progress
    """
    
    def __init__(self, request, response, session, T, db, s3, crud, auth):
        self.request=request
        self.response=response
        self.session=session
        self.T=T
        self.db=db
        self.s3=s3
        self.crud=crud
        self.auth=auth
        
     def _globals(self):
        """
        Returns (request,response,session,T,db,s3,crud,auth)
        """
        return self.request, self.response, self.session, self.T, self.db, self.s3, self.crud, self.auth
        
     def shn_crud_strings_lookup(self,resource):
        "Look up CRUD strings for a given resource based on the definitions in models/module.py."
        return getattr(self.s3.crud_strings,'%s' % resource)

    @staticmethod
    def import_csv(table,file):
        "Import CSV file into Database. Comes from appadmin.py. Modified to do Validation on UUIDs"
        table.import_from_csv_file(file)

    @staticmethod
    def import_json(table,file):
        "Import JSON into Database."
        import gluon.contrib.simplejson as sj
        reader=sj.loads(file)
        # ToDo
        # Get column names (like for SQLTable.import_from_csv_file() )
        # Insert records (or Update if unique field duplicated)
        #table.insert(**dict(items))
        return
                
    def shn_rest_controller(self,module,resource,deletable=True,listadd=True,main='name',extra=None,onvalidation=None,format=None):
        """
        RESTlike controller function.

        Provides CRUD operations for the given module/resource.
        Optional parameters:
        deletable=False: don't provide visible options for deletion
        listadd=False: don't provide an add form in the list view
        main='field': main field to display in the list view (defaults to 'name')
        extra='field': extra field to display in the list view
        format='table': display list in tabular format

        Anonymous users can Read.
        Authentication required for Create/Update/Delete.

        Auditing options for Read &/or Write.

        Supported Representations:
            HTML is the default (including full Layout)
            PLAIN is HTML with no layout
             - can be inserted into DIVs via AJAX calls
             - can be useful for clients on low-bandwidth or small screen sizes
            JSON (designed to be accessed via JavaScript)
             - responses in JSON format
             - create/update/delete done via simple GET vars (no form displayed)
            CSV (useful for synchronization)
             - List/Display/Create for now
            RSS (list only)
            XML (list/read only)
            AJAX (designed to be run asynchronously to refresh page elements)
            POPUP
        ToDo:
            Alternate Representations
                CSV update
                SMS,PDF,LDIF
            Customisable Security Policy
        """

        # Avoid adding 'self' before all these variables
        request,response,session,T,db,s3,crud,auth=self._globals()
        
        _table='%s_%s' % (module,resource)
        table=db[_table]
        if resource=='setting':
            s3.crud_strings=shn_crud_strings_lookup(resource)
        else:
            s3.crud_strings=shn_crud_strings_lookup(table)

        try:
            crud.messages.record_created=s3.crud_strings.msg_record_created
            crud.messages.record_updated=s3.crud_strings.msg_record_modified
            crud.messages.record_deleted=s3.crud_strings.msg_record_deleted
        except:
            pass

        # Which representation should output be in?
        if request.vars.format:
            representation=str.lower(request.vars.format)
        else:
            # Default to HTML
            representation="html"

        # Is user authorised to C/U/D?
        # Currently this is simplified as just whether user is logged in!
        authorised = auth.is_logged_in()

        if len(request.args)==0:
            # No arguments => default to List (or list_create if authorised)
            if session.s3.audit_read:
                db.s3_audit.insert(
                    person=auth.user.id if authorised else 0,
                    operation='list',
                    module=request.controller,
                    resource=resource,
                    old_value='',
                    new_value=''
                )
            if representation=="html":
                # Default list format is a simple list, not tabular
                tabular=0
                if format=='table':
                    tabular=1
                    fields = [table[f] for f in table.fields if table[f].readable]
                    headers={}
                    for field in fields:
                       # Use custom or prettified label
                       headers[str(field)]=field.label
                    items=crud.select(table,fields=fields,headers=headers)
                else:
                    self.shn_represent(table,module,resource,deletable,main,extra)
                    items=t2.itemize(table)
                if not items:
                    try:
                        items=s3.crud_strings.msg_list_empty
                    except:
                        items=T('None')
                try:
                    title=s3.crud_strings.title_list
                except:
                    title=T('List')
                try:
                    subtitle=s3.crud_strings.subtitle_list
                except:
                    subtitle=''
                if authorised and listadd:
                    # Display the Add form below List
                    if deletable and not tabular:
                        # Add extra column header to explain the checkboxes
                        if isinstance(items,TABLE):
                            items.insert(0,TR('',B('Delete?')))
                    form=crud.create(table,onvalidation=onvalidation)
                    # Check for presence of Custom View
                    custom_view='%s_list_create.html' % resource
                    _custom_view=os.path.join(request.folder,'views',module,custom_view)
                    if os.path.exists(_custom_view):
                        response.view=module+'/'+custom_view
                    else:
                        if tabular:
                            response.view='table_list_create.html'
                        else:
                            response.view='list_create.html'
                    try:
                        addtitle=s3.crud_strings.subtitle_create
                    except:
                        addtitle=T('Add New')
                    return dict(module_name=module_name,modules=modules,options=options,items=items,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
                else:
                    # List only
                    if listadd:
                        try:
                            label_create_button=s3.crud_strings.label_create_button
                        except:
                            label_create_button=T('Add')
                        add_btn=A(label_create_button,_href=URL(r=request,f=resource,args='create'),_id='add-btn')
                    else:
                        add_btn=''
                    # Check for presence of Custom View
                    custom_view='%s_list.html' % resource
                    _custom_view=os.path.join(request.folder,'views',module,custom_view)
                    if os.path.exists(_custom_view):
                        response.view=module+'/'+custom_view
                    else:
                        if tabular:
                            response.view='table_list.html'
                        else:
                            response.view='list.html'
                    return dict(module_name=module_name,modules=modules,options=options,items=items,title=title,subtitle=subtitle,add_btn=add_btn)
            elif representation=="ajax":
                #items=crud.select(table,fields=fields,headers=headers)
                self.shn_represent(table,module,resource,deletable,main,extra)
                items=t2.itemize(table)
                if not items:
                    try:
                        items=s3.crud_strings.msg_list_empty
                    except:
                        items=T('None')
                if deletable:
                    # Add extra column header to explain the checkboxes
                    if isinstance(items,TABLE):
                        items.insert(0,TR('',B('Delete?')))
                response.view='plain.html'
                return dict(item=items)
            elif representation=="plain":
                items=crud.select(table)
                response.view='plain.html'
                return dict(item=items)
            elif representation=="json":
                items=db().select(table.ALL).json()
                response.headers['Content-Type']='text/x-json'
                return items
            elif representation=="xml":
                items=db().select(table.ALL).as_list()
                response.headers['Content-Type']='text/xml'
                return str(service.xml_serializer(items))
            elif representation=="csv":
                import gluon.contenttype
                response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
                query=db[table].id>0
                response.headers['Content-disposition']="attachment; filename=%s_%s_list.csv" % (request.env.server_name,resource)
                return str(db(query).select())
            elif representation=="rss":
                if request.env.remote_addr=='127.0.0.1':
                    server='http://127.0.0.1:' + request.env.server_port
                else:
                    server='http://' + request.env.server_name + ':' + request.env.server_port
                link='/%s/%s/%s' % (request.application,module,resource)
                entries=[]
                rows=db(table.id>0).select()
                for row in rows:
                    entries.append(dict(title=row.name,link=server+link+'/%d' % row.id,description=row.description or '',created_on=row.created_on))
                import gluon.contrib.rss2 as rss2
                items = [ rss2.RSSItem(title = entry['title'], link = entry['link'], description = entry['description'], pubDate = entry['created_on']) for entry in entries]
                rss = rss2.RSS2(title = str(s3.crud_strings.subtitle_list), link = server+link+'/%d' % row.id, description = '', lastBuildDate = request.now, items = items)
                response.headers['Content-Type']='application/rss+xml'
                return rss2.dumps(rss)
            else:
                session.flash=DIV(T("Unsupported format!"),_class="error")
                redirect(URL(r=request))
        else:
            if request.args[0].isdigit():
                # 1st argument is ID not method => Read.
                s3.id=request.args[0]
                if session.s3.audit_read:
                    db.s3_audit.insert(
                        person=auth.user.id if authorised else 0,
                        operation='read',
                        representation=representation,
                        module=request.controller,
                        resource=resource,
                        record=s3.id,
                        old_value='',
                        new_value=''
                    )
                if representation=="html":
                    item=crud.read(table,s3.id)
                    # Check for presence of Custom View
                    custom_view='%s_display.html' % resource
                    _custom_view=os.path.join(request.folder,'views',module,custom_view)
                    if os.path.exists(_custom_view):
                        response.view=module+'/'+custom_view
                    else:
                        response.view='display.html'
                    try:
                        title=s3.crud_strings.title_display
                    except:
                        title=T('Details')
                    edit=A(T("Edit"),_href=URL(r=request,f=resource,args=['update',s3.id]),_id='edit-btn')
                    if deletable:
                        delete=A(T("Delete"),_href=URL(r=request,f=resource,args=['delete',s3.id]),_id='delete-btn')
                    else:
                        delete=''
                    try:
                        label_list_button=s3.crud_strings.label_list_button
                    except:
                        label_list_button=T('List All')
                    list_btn=A(label_list_button,_href=URL(r=request,f=resource),_id='list-btn')
                    return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,delete=delete,list_btn=list_btn)
                elif representation=="plain":
                    item=crud.read(table,s3.id)
                    response.view='plain.html'
                    return dict(item=item)
                elif representation=="json":
                    item=db(table.id==s3.id).select(table.ALL).json()
                    response.view='plain.html'
                    return dict(item=item)
                elif representation=="xml":
                    item=db(table.id==s3.id).select(table.ALL).as_list()
                    response.headers['Content-Type']='text/xml'
                    return str(service.xml_serializer(item))
                elif representation=="csv":
                    import gluon.contenttype
                    response.headers['Content-Type']=gluon.contenttype.contenttype('.csv')
                    query=db[table].id==s3.id
                    response.headers['Content-disposition']="attachment; filename=%s_%s_%d.csv" % (request.env.server_name,resource,s3.id)
                    return str(db(query).select())
                elif representation=="rss":
                    #if request.args and request.args[0] in settings.rss_procedures:
                    #   feed=eval('%s(*request.args[1:],**dict(request.vars))'%request.args[0])
                    #else:
                    #   t2._error()
                    #import gluon.contrib.rss2 as rss2
                    #rss = rss2.RSS2(
                    #   title=feed['title'],
                    #   link = feed['link'],
                    #   description = feed['description'],
                    #   lastBuildDate = feed['created_on'],
                    #   items = [
                    #      rss2.RSSItem(
                    #        title = entry['title'],
                    #        link = entry['link'],
                    #        description = entry['description'],
                    #        pubDate = entry['created_on']) for entry in feed['entries']]
                    #   )
                    #response.headers['Content-Type']='application/rss+xml'
                    #return rss2.dumps(rss)
                    entries[0]=dict(title=table.name,link=URL(r=request,c='module',f='resource',args=[table.id]),description=table.description,created_on=table.created_on)
                    item=service.rss(entries=entries)
                    response.view='plain.html'
                    return dict(item=item)
                else:
                    session.flash=DIV(T("Unsupported format!"),_class="error")
                    redirect(URL(r=request))
            else:
                method=str.lower(request.args[0])
                try:
                    s3.id=request.args[1]
                except:
                    pass
                if method=="create":
                    if authorised:
                        if session.s3.audit_write:
                            audit_id=db.s3_audit.insert(
                                person=auth.user.id,
                                operation='create',
                                representation=representation,
                                module=request.controller,
                                resource=resource,
                                record=s3.id,
                                old_value='',
                                new_value=''
                            )
                        if representation=="html":
                            form=crud.create(table,onvalidation=onvalidation)
                            #form[0].append(TR(TD(),TD(INPUT(_type="reset",_value="Reset form"))))
                            # Check for presence of Custom View
                            custom_view='%s_create.html' % resource
                            _custom_view=os.path.join(request.folder,'views',module,custom_view)
                            if os.path.exists(_custom_view):
                                response.view=module+'/'+custom_view
                            else:
                                response.view='create.html'
                            try:
                                title=s3.crud_strings.title_create
                            except:
                                title=T('Add')
                            try:
                                label_list_button=s3.crud_strings.label_list_button
                            except:
                                label_list_button=T('List All')
                            list_btn=A(label_list_button,_href=URL(r=request,f=resource),_id='list-btn')
                            return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                        elif representation=="plain":
                            form=crud.create(table,onvalidation=onvalidation)
                            response.view='plain.html'
                            return dict(item=form)
                        elif representation=="popup":
                            form=crud.create(table,onvalidation=onvalidation)
                            response.view='popup.html'
                            return dict(module_name=module_name,form=form,module=module,resource=resource,main=main,caller=request.vars.caller)
                        elif representation=="json":
                            record=Storage()
                            for var in request.vars:
                                if var=='format':
                                    pass
                                else:
                                    record[var] = request.vars[var]
                            item=''
                            for var in record:
                                # Validate request manually
                                if table[var].requires(record[var])[1]:
                                    item+='{"Status":"failed","Error":{"StatusCode":403,"Message":"'+var+' invalid: '+table[var].requires(record[var])[1]+'"}}'
                            if item:
                                pass
                            else:
                                try:
                                    id=table.insert(**dict (record))
                                    item='{"Status":"success","Error":{"StatusCode":201,"Message":"Created as '+URL(r=request,c=module,f=resource,args=id)+'"}}'
                                except:
                                    item='{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
                            response.view='plain.html'
                            return dict(item=item)
                        elif representation=="csv":
                            # Read in POST
                            file=request.vars.filename.file
                            try:
                                import_csv(table,file)
                                reply=T('Data uploaded')
                            except: 
                                reply=T('Unable to parse CSV file!')
                            return reply
                        else:
                            session.flash=DIV(T("Unsupported format!"),_class="error")
                            redirect(URL(r=request))
                    else:
                        redirect(URL(r=request,c='default',f='user',args='login',vars={'_next':URL(r=request,c=module,f=resource,args='create')}))
                elif method=="display" or method=="read":
                    redirect(URL(r=request,args=s3.id))
                elif method=="update":
                    if authorised:
                        if session.s3.audit_write:
                            old_value = []
                            _old_value=db(db[table].id==s3.id).select()[0]
                            for field in _old_value:
                                old_value.append(field+':'+str(_old_value[field]))
                            audit_id=db.s3_audit.insert(
                                person=auth.user.id,
                                operation='update',
                                representation=representation,
                                module=request.controller,
                                resource=resource,
                                record=s3.id,
                                old_value=old_value,
                                new_value=''
                            )
                        if representation=="html":
                            form=crud.update(table,s3.id,onvalidation=onvalidation)
                            # Check for presence of Custom View
                            custom_view='%s_update.html' % resource
                            _custom_view=os.path.join(request.folder,'views',module,custom_view)
                            if os.path.exists(_custom_view):
                                response.view=module+'/'+custom_view
                            else:
                                response.view='update.html'
                            title=s3.crud_strings.title_update
                            if s3.crud_strings.label_list_button:
                                list_btn=A(s3.crud_strings.label_list_button,_href=URL(r=request,f=resource),_id='list-btn')
                                return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                            else:
                                return dict(module_name=module_name,modules=modules,options=options,form=form,title=title)
                        elif representation=="plain":
                            form=crud.update(table,s3.id,onvalidation=onvalidation)
                            response.view='plain.html'
                            return dict(item=form)
                        elif representation=="json":
                            record=Storage()
                            uuid=0
                            for var in request.vars:
                                if var=='format':
                                    pass
                                elif var=='uuid':
                                    uuid=1
                                else:
                                    record[var] = request.vars[var]
                            if uuid:
                                item=''
                                for var in record:
                                    # Validate request manually
                                    if table[var].requires(record[var])[1]:
                                        item+='{"Status":"failed","Error":{"StatusCode":403,"Message":"'+var+' invalid: '+table[var].requires(record[var])[1]+'"}}'
                                if item:
                                    pass
                                else:
                                    try:
                                        result=db(table.uuid==request.vars.uuid).update(**dict (record))
                                        if result:
                                            item='{"Status":"success","Error":{"StatusCode":200,"Message":"Record updated."}}'
                                        else:
                                            item='{"Status":"failed","Error":{"StatusCode":404,"Message":"Record '+request.vars.uuid+' does not exist."}}'
                                    except:
                                        item='{"Status":"failed","Error":{"StatusCode":400,"Message":"Invalid request!"}}'
                            else:
                                item='{"Status":"failed","Error":{"StatusCode":400,"Message":"UUID required!"}}'
                            response.view='plain.html'
                            return dict(item=item)
                        else:
                            session.flash=DIV(T("Unsupported format!"),_class="error")
                            redirect(URL(r=request))
                    else:
                        redirect(URL(r=request,c='default',f='user',args='login',vars={'_next':URL(r=request,c=module,f=resource,args=['update',s3.id])}))
                elif method=="delete":
                    if authorised:
                        if session.s3.audit_write:
                            old_value = []
                            _old_value=db(db[table].id==s3.id).select()[0]
                            for field in _old_value:
                                old_value.append(field+':'+str(_old_value[field]))
                            db.s3_audit.insert(
                                person=auth.user.id,
                                operation='delete',
                                representation=representation,
                                module=request.controller,
                                resource=resource,
                                record=s3.id,
                                old_value=old_value,
                                new_value=''
                            )
                        if representation=="ajax":
                            #crud.delete(table,s3.id,next='%s?format=ajax' % resource)
                            t2.delete(table,next='%s?format=ajax' % resource)
                        else:
                            crud.delete(table,s3.id)
                    else:
                        redirect(URL(r=request,c='default',f='user',args='login',vars={'_next':URL(r=request,c=module,f=resource,args=['delete',s3.id])}))
                elif method=="search":
                    if session.s3.audit_read:
                        db.s3_audit.insert(
                            person=auth.user.id if authorised else 0,
                            operation='search',
                            module=request.controller,
                            resource=resource,
                            old_value='',
                            new_value=''
                        )
                    if representation=="html":
                        self.shn_represent(table,module,resource,deletable,main,extra)
                        search=t2.search(table)
                        # Check for presence of Custom View
                        custom_view='%s_search.html' % resource
                        _custom_view=os.path.join(request.folder,'views',module,custom_view)
                        if os.path.exists(_custom_view):
                            response.view=module+'/'+custom_view
                        else:
                            response.view='search.html'
                        title=s3.crud_strings.title_search
                        return dict(module_name=module_name,modules=modules,options=options,search=search,title=title)
                    if representation=="json":
                        if request.vars.field and request.vars.filter and request.vars.value:
                            field=str.lower(request.vars.field)
                            filter=str.lower(request.vars.filter)
                            if filter == '=':
                                query=(table['%s' % field]==request.vars.value)
                                item = db(query).select().json()
                            else:
                                item='{"Status":"failed","Error":{"StatusCode":501,"Message":"Unsupported filter! Supported filters: ="}}'
                        else:
                            item='{"Status":"failed","Error":{"StatusCode":501,"Message":"Search requires specifying Field, Filter & Value!"}}'
                        response.view='plain.html'
                        return dict(item=item)
                    else:
                        session.flash=DIV(T("Unsupported format!"),_class="error")
                        redirect(URL(r=request))
                else:
                    session.flash=DIV(T("Unsupported method!"),_class="error")
                    redirect(URL(r=request))
    
    def shn_represent(self,table,module,resource,deletable=True,main='name',extra=None):
        "Designed to be called via table.represent to make t2.itemize() output useful"
        db[table].represent=lambda table:shn_list_item(table,resource,action='display',main=main,extra=self.shn_represent_extra(table,module,resource,deletable,extra))
        return

    def shn_represent_extra(self,table,module,resource,deletable=True,extra=None):
        "Display more than one extra field (separated by spaces)"
        # Is user authorised to C/U/D?
        # Currently this is simplified as just whether user is logged in!
        authorised = auth.is_logged_in()
        
        item_list=[]
        if extra:
            extra_list = extra.split()
            for any_item in extra_list:
                item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % (module,resource,table.id,any_item))
        if authorised and deletable:
            item_list.append("TD(INPUT(_type='checkbox',_class='delete_row',_name='%s',_id='%i'))" % (resource,table.id))
        return ','.join( item_list )

    def shn_list_item(self,table,resource,action,main='name',extra=None):
        "Display nice names with clickable links & optional extra info"
        item_list = [TD(A(table[main],_href=URL(r=request,f=resource,args=[action,table.id])))]
        if extra:
            item_list.extend(eval(extra))
        items=DIV(TABLE(TR(item_list)))
        return DIV(*items)

        