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
	return dict(form=t2.login(),module_name=module_name,modules=modules,options=options)
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

#
# Configs
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def config():
    table=db.gis_config
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Config Details')
            edit=A(T("Edit"),_href=t2.action('config',['update',t2.id]))
            list_btn=A(T("List Configs"),_href=t2.action('config'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Config added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Config')
                    list_btn=A(T("List Configs"),_href=t2.action('config'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'config/create'})
            elif method=="display":
                t2.redirect('config',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Config updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Config')
                    list_btn=A(T("List Configs"),_href=t2.action('config'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'config/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Config deleted")
                    t2.delete(table,next='config')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'config/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Configs currently defined."
        title=T('List Configs')
        subtitle=T('Configs')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Config')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Config"),_href=t2.action('config','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

# Defaults are a special case of Configs - the 1st entry
@t2.requires_login('login')
def defaults():
    title=T("GIS Defaults")
    form=t2.update(db.gis_config,deletable=False) # NB deletable=False
    return dict(title=title,module_name=module_name,modules=modules,options=options,form=form)
	
#
# Features
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
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
# Designed to be called via AJAX to return the results into a list-container div
def delete_feature_ajax():
    t2.delete(db.gis_feature,next='list_features_plain')
    return

# Designed to be called via AJAX to refresh a list-container div
def list_features_plain():
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
    response.view='list_plain.html'
    return dict(list=list)

#
# Feature Classes
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def feature_class():
    table=db.gis_feature_class
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Feature Class Details')
            edit=A(T("Edit"),_href=t2.action('feature_class',['update',t2.id]))
            list_btn=A(T("List Feature Classes"),_href=t2.action('feature_class'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Feature Class added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Feature Class')
                    list_btn=A(T("List Feature Classes"),_href=t2.action('feature_class'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature_class/create'})
            elif method=="display":
                t2.redirect('feature_class',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Feature Class updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Feature Class')
                    list_btn=A(T("List Feature Classes"),_href=t2.action('feature_class'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature_class/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Feature Class deleted")
                    t2.delete(table,next='feature_class')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'feature_class/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Feature Classes currently defined."
        title=T('List Feature Classes')
        subtitle=T('Feature Classes')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Feature Class')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Feature Class"),_href=t2.action('feature_class','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

#
# Feature Groups
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def feature_group():
    table=db.gis_feature_group
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Feature Class Details')
            edit=A(T("Edit"),_href=t2.action('feature_group',['update',t2.id]))
            list_btn=A(T("List Feature Groups"),_href=t2.action('feature_group'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Feature Group added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Feature Group')
                    list_btn=A(T("List Feature Groups"),_href=t2.action('feature_group'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature_group/create'})
            elif method=="display":
                t2.redirect('feature_group',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Feature Group updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Feature Group')
                    list_btn=A(T("List Feature Groups"),_href=t2.action('feature_group'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature_group/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Feature Group deleted")
                    t2.delete(table,next='feature_group')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'feature_group/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Feature Groups currently defined."
        title=T('List Feature Groups')
        subtitle=T('Feature Groups')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Feature Group')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Feature Group"),_href=t2.action('feature_group','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

# Designed to be called via AJAX to be processed within JS client
def display_feature_group_features_json():
    list=db(db.gis_feature_group.id==t2.id).select(db.gis_feature_group.features).json()
    response.view='list_plain.html'
    return dict(list=list)

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
# Feature Metadata
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def feature_metadata():
    table=db.gis_feature_metadata
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Feature Metadata Details')
            edit=A(T("Edit"),_href=t2.action('feature_metadata',['update',t2.id]))
            list_btn=A(T("List Feature Metadata"),_href=t2.action('feature_metadata'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Feature Metadata added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Feature Metadata')
                    list_btn=A(T("List Feature Metadata"),_href=t2.action('feature_metadata'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature_metadata/create'})
            elif method=="display":
                t2.redirect('feature_metadata',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Feature Metadata updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Feature Metadata')
                    list_btn=A(T("List Feature Metadata"),_href=t2.action('feature_metadata'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'feature_metadata/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Feature Metadata deleted")
                    t2.delete(table,next='feature_metadata')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'feature_metadata/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Feature Metadata currently defined."
        title=T('List Feature Metadata')
        subtitle=T('Feature Metadata')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Feature Metadata')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Feature Metadata"),_href=t2.action('feature_metadata','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)


#
# Keys
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def key():
    table=db.gis_key
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Key Details')
            edit=A(T("Edit"),_href=t2.action('key',['update',t2.id]))
            list_btn=A(T("List Keys"),_href=t2.action('key'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Key added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Key')
                    list_btn=A(T("List Keys"),_href=t2.action('key'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'key/create'})
            elif method=="display":
                item=t2.display(table)
                response.view='display.html'
                title=T('Key Details')
                edit=A(T("Edit"),_href=t2.action('key',['update',t2.id]))
                list_btn=A(T("List Keys"),_href=t2.action('key'))
                return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Key updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Key')
                    list_btn=A(T("List Keys"),_href=t2.action('key'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'key/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Key deleted")
                    t2.delete(table,next='key')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'key/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Keys currently defined."
        title=T('List Keys')
        subtitle=T('Keys')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Key')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Key"),_href=t2.action('key','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

#
# Markers
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def marker():
    table=db.gis_marker
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Marker Details')
            edit=A(T("Edit"),_href=t2.action('marker',['update',t2.id]))
            list_btn=A(T("List Markers"),_href=t2.action('marker'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Marker added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Marker')
                    list_btn=A(T("List Markers"),_href=t2.action('marker'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'marker/create'})
            elif method=="display":
                t2.redirect('marker',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Marker updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Marker')
                    list_btn=A(T("List Markers"),_href=t2.action('marker'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'marker/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Marker deleted")
                    t2.delete(table,next='marker')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'marker/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Markers currently defined."
        title=T('List Markers')
        subtitle=T('Markers')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Marker')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Marker"),_href=t2.action('marker','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

#
# Projections
#
# RESTful controller function
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def projection():
    table=db.gis_projection
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            item=t2.display(table)
            response.view='display.html'
            title=T('Projection Details')
            edit=A(T("Edit"),_href=t2.action('projection',['update',t2.id]))
            list_btn=A(T("List Projections"),_href=t2.action('projection'))
            return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
        except:
            if method=="create":
                if t2.logged_in:
                    t2.messages.record_created=T("Projection added")
                    form=t2.create(table)
                    response.view='create.html'
                    title=T('Add Projection')
                    list_btn=A(T("List Projections"),_href=t2.action('projection'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'projection/create'})
            elif method=="display":
                item=t2.display(table)
                response.view='display.html'
                title=T('Projection Details')
                edit=A(T("Edit"),_href=t2.action('projection',['update',t2.id]))
                list_btn=A(T("List Projections"),_href=t2.action('projection'))
                return dict(module_name=module_name,modules=modules,options=options,item=item,title=title,edit=edit,list_btn=list_btn)
            elif method=="update":
                if t2.logged_in:
                    t2.messages.record_modified=T("Projection updated")
                    form=t2.update(table)
                    response.view='update.html'
                    title=T('Edit Projection')
                    list_btn=A(T("List Projections"),_href=t2.action('projection'))
                    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn)
                else:
                    t2.redirect('login',vars={'_destination':'projection/update/%i' % t2.id})
            elif method=="delete":
                if t2.logged_in:
                    t2.messages.record_deleted=T("Projection deleted")
                    t2.delete(table,next='projection')
                    return
                else:
                    t2.redirect('login',vars={'_destination':'projection/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Projections currently defined."
        title=T('List Projections')
        subtitle=T('Projections')
        if t2.logged_in:
            form=t2.create(table)
            response.view='list_create.html'
            addtitle=T('Add New Projection')
            return dict(module_name=module_name,modules=modules,options=options,list=list,form=form,title=title,subtitle=subtitle,addtitle=addtitle)
        else:
            add_btn=A(T("Add Projection"),_href=t2.action('projection','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

#
# Layers
#
# RESTful controller function for Multiple Tables
# Anonymous users can Read
# Authentication required for Create/Update/Delete
def layer():
    table=db.gis_layer
    if request.args:
        method=request.args[0]
        try:
            # 1st argument is ID not method => display
            id = int(method)
            # We want more control than T2 allows us (& we also want proper MVC separation)
            # - multiple tables
            # - names not numbers for type/subtype
            layer=db(table.id==t2.id).select()[0]
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
            response.view='gis/display_layer.html'
            title=T('Layer Details')
            edit=A(T("Edit"),_href=t2.action('layer',['update',t2.id]))
            list_btn=A(T("List Layers"),_href=t2.action('layer'))
            return dict(module_name=module_name,modules=modules,options=options,title=title,edit=edit,list_btn=list_btn,layer=layer,type=type,subtype=subtype,key=key)
        except:
            if method=="create":
                if t2.logged_in:
                    # Need to handle Multiple Tables, so go down a level of abstraction from T2
                    # Function split-out to make code more readable & reusable (DRY)
                    return shn_gis_create_layer()
                else:
                    t2.redirect('login',vars={'_destination':'layer/create'})
            elif method=="display":
                t2.redirect('layer',args=t2.id)
            elif method=="update":
                if t2.logged_in:
                    # Need to handle Multiple Tables, so go down a level of abstraction from T2
                    # Function split-out to make code more readable
                    return shn_gis_update_layer()
                else:
                    t2.redirect('login',vars={'_destination':'layer/update/%i' % t2.id})
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
                    
                    t2.redirect('layer',flash=T("Layer deleted"))
                else:
                    t2.redirect('login',vars={'_destination':'layer/delete/%i' % t2.id})
            else:
                # Invalid!
                return
    else:
        # No arguments => default to list
        list=t2.itemize(table)
        if list=="No data":
            list="No Layers currently defined."
        if isinstance(list,TABLE):
            list.insert(0,TR('',B('Enabled?'))) 
        title=T('List Layers')
        subtitle=T('Layers')
        if t2.logged_in:
            # Need to handle Multiple Tables, so go down a level of abstraction from T2
            # Function split-out to make code more readable & reusable (DRY)
            # just need to add a little extra context
            output=shn_gis_create_layer()
            response.view='gis/list_create_layer.html'
            addtitle=T('Add New Layer')
            output.update(dict(list=list,title=title,subtitle=subtitle,addtitle=addtitle))
            return output
        else:
            add_btn=A(T("Add Layer"),_href=t2.action('layer','create'))
            response.view='list.html'
            return dict(module_name=module_name,modules=modules,options=options,list=list,title=title,subtitle=subtitle,add_btn=add_btn)

# Designed to be called as a function from within the above RESTful controller
# This breaks it apart for easier comprehension
# It also allow re-use: DRY
@t2.requires_login('login')
def shn_gis_create_layer():

    # Default to OpenStreetMap - promote Open Data!
    type="openstreetmap"
    subtype="Mapnik"
    options_subtype=["Mapnik","Osmarender","Aerial"]
    key="ABQIAAAAgB-1pyZu7pKAZrMGv3nksRRi_j0U6kJrkFvY4-OX2XYmEAa76BSH6SJQ1KrBv-RzS5vygeQosHsnNw" # Google Key for 127.0.0.1
    
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
    form=FORM(INPUT(_name="name",requires=IS_NOT_EMPTY()),
            INPUT(_name="description"),
            SELECT(_name="type",requires=IS_NOT_EMPTY()),
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % type].ALL)])
            SELECT(_name="subtype"),
            INPUT(_name="key",requires=IS_NOT_EMPTY()),
            SELECT(_name="feature_group"),
            INPUT(_name="priority",requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]),
            INPUT(_name="enabled"),
            INPUT(_type="submit"))

    # Process form
    if form.accepts(request.vars,session,keepvalues=True):
        if form.vars.enabled=="on":
            enabled=True
        else:
            enabled=False
        # Insert Master Record
        id=db.gis_layer.insert(
            uuid=uuid.uuid4(),
            name=form.vars.name,
            description=form.vars.description,
            type=form.vars.type,
            priority=form.vars.priority,
            enabled=enabled
        )
        type_new=form.vars.type
        # Insert Sub-Record(s):
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
        elif type_new=="features":
            db['gis_layer_%s' % type_new].insert(
                layer=id,
                feature_group=form.vars.feature_group
            )
        # Notify user :)
        response.confirmation=T("Layer updated")
    elif form.errors: 
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
    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn,type=type,subtype=subtype,key=key,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority,options_feature_group=options_feature_group)


# Designed to be called as a function from within the above RESTful controller
# This breaks it apart for easier comprehension
@t2.requires_login('login')
def shn_gis_update_layer():
    # Provide defaults for fields which only appear for some types
    subtype=0
    options_subtype = [""]
    feature_group=0
    key=0

    # Get a pointer to the Layer record (for getting default values out & saving updated values back)
    layer=db(db.gis_layer.id==t2.id).select()[0]
    
    # Pull out current settings to pre-populate form with
    type=layer.type
    if type=="openstreetmap":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        # Need here as well as gis_layers.js to populate the initial 'selected'
        options_subtype = ["Mapnik","Osmarender","Aerial"]
    elif type=="google":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid", "Terrain"]
        key=db(db.gis_key.service==type).select(db.gis_key.ALL)[0].key
    elif type=="virtualearth":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
    elif type=="yahoo":
        subtype=db(db['gis_layer_%s' % type].layer==t2.id).select(db['gis_layer_%s' % type].ALL)[0].type
        options_subtype = ["Satellite", "Maps", "Hybrid"]
        key=db(db.gis_key.service==type).select(db.gis_key.ALL)[0].key
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
    priority=layer.priority
    options_priority.insert(0,priority)
    
    # Build form
    # Neither SQLFORM nor T2 support multiple tables
    # Customised method could be developed by extending T2, but wouldn't give us MVC separation, so best to port it to here & view
    # HTML is built manually in the view...this provides a hook for processing
    # we need to add validation here because this form doesn't know about the database
    # (We could make the main table a SQLFORM to be auto-validating & auto-processing leaving us to just do other tables manually)
    form=FORM(INPUT(_name="id",requires=IS_NOT_EMPTY()),
            INPUT(_name="modified_on"),
            INPUT(_name="name",requires=IS_NOT_EMPTY()),
            INPUT(_name="description"),
            SELECT(_name="type",requires=IS_NOT_EMPTY()),
            #SELECT(_type="select",_name="subtype",*[OPTION(x.name,_value=x.id)for x in db().select(db['gis_layer_%s_type' % type].ALL)])
            SELECT(_name="subtype",requires=IS_NOT_EMPTY()),
            SELECT(_name="feature_group"),
            INPUT(_name="key",requires=IS_NOT_EMPTY()),
            # Should develop an IS_THIS_OR_IS_NOT_IN_DB(this,table) validator (so as to not rely on View)
            #INPUT(_name="priority",requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'gis_layer.priority')]),
            INPUT(_name="priority",requires=IS_NOT_EMPTY()),
            INPUT(_name="enabled"),
            INPUT(_type="submit"))
    
    # use T2 for conflict detection
    # This mod needs testing!
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
        # Update Master Record
        layer.update_record(
            name=form.vars.name,
            description=form.vars.description,
            type=form.vars.type,
            priority=form.vars.priority,
            enabled=enabled
        )
        type_new=form.vars.type
        # Update Sub-Record(s):
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
        elif type_new=="features":
            db(db['gis_layer_%s' % type_new].layer==t2.id).select()[0].update_record(
                feature_group=form.vars.feature_group
            )
        # Notify user :)
        response.confirmation=T("Layer updated")
    elif form.errors: 
        response.error=T("Form is invalid")
    else: 
        response.notification=T("Please fill the form")

    response.view='gis/update_layer.html'
    title=T('Edit Layer')
    list_btn=A(T("List Layers"),_href=t2.action('layer'))
    return dict(module_name=module_name,modules=modules,options=options,form=form,title=title,list_btn=list_btn,layer=layer,type=type,subtype=subtype,key=key,options_type=gis_layer_types,options_subtype=options_subtype,options_priority=options_priority,options_feature_group=options_feature_group,feature_group=feature_group)

# Map Service Catalogue
# extends list_create_layer for real user UI
def map_service_catalogue():
    output=shn_gis_create_layer()
    # Layers listed after Form so they get refreshed after submission
    list=t2.itemize(db.gis_layer)
    if list=="No data":
        list="No Layers currently defined."
    if isinstance(list,TABLE):
        list.insert(0,TR('',B('Enabled?'))) 
    
    response.view='gis/map_service_catalogue.html'
    title=T('Map Service Catalogue')
    subtitle=T('Layers')
    addtitle=T('Add New Layer')
    output.update(dict(list=list,title=title,subtitle=subtitle,addtitle=addtitle))
    return output

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
