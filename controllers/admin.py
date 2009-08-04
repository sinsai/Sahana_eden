# -*- coding: utf-8 -*-

module = 'admin'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
# - can Insert/Delete items from default menus within a function, if required.
# NB Sync manually with the copy in 'appadmin.py'
response.menu_options = [
    [T('Home'), False, URL(r=request, c='admin', f='index')],
    [T('Settings'), False, URL(r=request, c='admin', f='setting', args=['update', 1])],
    [T('User Management'), False, '#', [
        [T('Users'), False, URL(r=request, c='admin', f='user')],
        [T('Roles'), False, URL(r=request, c='admin', f='group')],
        #[T('Membership'), False, URL(r=request, c='admin', f='membership')]
    ]],
    [T('Database'), False, '#', [
        [T('Import'), False, URL(r=request, c='admin', f='import_data')],
        [T('Export'), False, URL(r=request, c='admin', f='export_data')],
        [T('Raw Database access'), False, URL(r=request, c='appadmin', f='index')]
    ]],
    [T('Synchronisation'), False, '#', [
            [T('Sync History'), False, URL(r=request, c='admin', f='autosync')],
            [T('Sync Partners'), False, URL(r=request, c='admin', f='sync_partners')],
            [T('Sync Settings'), False, URL(r=request, c='admin', f='sync_settings')]
    ]],
    [T('Edit Application'), False, URL(r=request, a='admin', c='default', f='design', args=['sahana'])],
    [T('Functional Tests'), False, URL(r=request, c='static', f='selenium', args=['core', 'TestRunner.html'], vars=dict(test='../tests/TestSuite.html', auto='true', resultsUrl=URL(r=request, c='admin', f='handleResults')))]
]

# Web2Py Tools functions
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

@auth.requires_membership('Administrator')
def setting():
    "RESTlike CRUD controller"
    s3.crud_strings.setting.title_update = T('Edit Settings')
    s3.crud_strings.setting.msg_record_modified = T('Settings updated')
    s3.crud_strings.setting.label_list_button = None
    crud.settings.update_next = URL(r=request, args=['update', 1])
    return shn_rest_controller('s3', 'setting', deletable=False, listadd=False)

@auth.requires_membership('Administrator')
def user():
    "RESTlike CRUD controller"
    # Add users to Person Registry & 'Authenticated' role
    crud.settings.create_onaccept = lambda form: auth.shn_register(form)
    # Allow the ability for admin to Disable logins
    db.auth_user.registration_key.writable = True
    db.auth_user.registration_key.label = T('Disabled?')
    db.auth_user.registration_key.requires = IS_IN_SET(['','disabled'])
    return shn_rest_controller('auth', 'user', main='first_name')
    
@auth.requires_membership('Administrator')
def group():
    "RESTlike CRUD controller"
    return shn_rest_controller('auth', 'group', main='role')
    
# Unused as poor UI
@auth.requires_membership('Administrator')
def membership():
    "RESTlike CRUD controller"
    return shn_rest_controller('auth', 'membership', main='user_id')
    
@auth.requires_membership('Administrator')
def users():
    "List/amend which users are in a Group"
    if len(request.args) == 0:
        session.error = T("Need to specify a role!")
        redirect(URL(r=request, f='group'))
    group = request.args[0]
    table = db.auth_membership
    query = table.group_id==group
    title = str(T('Role')) + ': ' + db.auth_group[group].role
    description = db.auth_group[group].description
    # Start building the Return
    output = dict(module_name=module_name, title=title, description=description, group=group)

    # Audit
    crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'membership', 'html')
    # Many<>Many selection (Deletable, no Quantity)
    item_list = []
    sqlrows = db(query).select()
    forms = Storage()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.user_id
        item_first = db.auth_user[id].first_name
        item_second = db.auth_user[id].last_name
        item_description = db.auth_user[id].email
        id_link = A(id,_href=URL(r=request,f='user',args=['read', id]))
        checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
        item_list.append(TR(TD(id_link), TD(item_first), TD(item_second), TD(item_description), TD(checkbox), _class=theclass))
        
    table_header = THEAD(TR(TH('ID'), TH(T('First Name')), TH(T('Last Name')), TH(T('Email')), TH(T('Remove'))))
    table_footer = TFOOT(TR(TD(_colspan=4), TD(INPUT(_id='submit_delete_button', _type='submit', _value=T('Remove')))))
    items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='group_remove_users', args=[group])))
        
    subtitle = T("Users")
    crud.messages.submit_button=T('Add')
    crud.messages.record_created = T('Role Updated')
    form = crud.create(table, next=URL(r=request, args=[group]))
    addtitle = T("Add New User to Role")
    output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form))
    return output

@auth.requires_membership('Administrator')
def group_remove_users():
    "Remove users from a group"
    if len(request.args) == 0:
        session.error = T("Need to specify a group!")
        redirect(URL(r=request, f='group'))
    group = request.args[0]
    table = db.auth_membership
    for var in request.vars:
        user = var
        query = (table.group_id==group) & (table.user_id==user)
        db(query).delete()
    # Audit
    #crud.settings.update_onaccept = lambda form: shn_audit_update(form, 'membership', 'html')
    session.flash = T("Users removed")
    redirect(URL(r=request, f='users', args=[group]))

@auth.requires_membership('Administrator')
def groups():
    "List/amend which groups a User is in"
    if len(request.args) == 0:
        session.error = T("Need to specify a user!")
        redirect(URL(r=request, f='user'))
    user = request.args[0]
    table = db.auth_membership
    query = table.user_id==user
    title = db.auth_user[user].first_name + ' ' + db.auth_user[user].last_name
    description = db.auth_user[user].email
    # Start building the Return
    output = dict(module_name=module_name, title=title, description=description, user=user)

    # Audit
    crud.settings.create_onaccept = lambda form: shn_audit_create(form, 'membership', 'html')
    # Many<>Many selection (Deletable, no Quantity)
    item_list = []
    sqlrows = db(query).select()
    forms = Storage()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.group_id
        forms[id] = SQLFORM(table, id)
        if forms[id].accepts(request.vars, session):
            response.flash = T("Membership Updated")
        item_first = db.auth_group[id].role
        item_description = db.auth_group[id].description
        id_link = A(id, _href=URL(r=request, f='group', args=['read', id]))
        checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
        item_list.append(TR(TD(id_link), TD(item_first), TD(item_description), TD(checkbox), _class=theclass))
        
    table_header = THEAD(TR(TH('ID'), TH(T('Role')), TH(T('Description')), TH(T('Remove'))))
    table_footer = TFOOT(TR(TD(_colspan=3), TD(INPUT(_id='submit_delete_button', _type='submit', _value=T('Remove')))))
    items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='user_remove_groups', args=[user])))
        
    subtitle = T("Roles")
    crud.messages.submit_button = T('Add')
    crud.messages.record_created = T('User Updated')
    form = crud.create(table, next=URL(r=request, args=[user]))
    addtitle = T("Add New Role to User")
    output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form))
    return output

@auth.requires_membership('Administrator')
def user_remove_groups():
    "Remove groups from a user"
    if len(request.args) == 0:
        session.error = T("Need to specify a user!")
        redirect(URL(r=request, f='user'))
    user = request.args[0]
    table = db.auth_membership
    for var in request.vars:
        group = var
        query = (table.group_id==group) & (table.user_id==user)
        db(query).delete()
    # Audit
    #crud.settings.update_onaccept = lambda form: shn_audit_update(form, 'membership', 'html')
    session.flash = T("Groups removed")
    redirect(URL(r=request, f='groups', args=[user]))

# Import Data
@auth.requires_membership('Administrator')
def import_data():
    "Import data via POST upload to CRUD controller."
    title = T('Import Data')
    return dict(module_name=module_name, title=title)

# Export Data
@auth.requires_login()
def export_data():
    "Export data via CRUD controller."
    title = T('Export Data')
    return dict(module_name=module_name, title=title)

#
# Sync
#

logtable = "sync_log"
    
@auth.requires_membership('Administrator')
def sync_partners():
    form = crud.create(db.sync_partner)
    records = db().select(db.sync_partner.ALL)
    return dict(form = form, records = records)

@auth.requires_membership('Administrator')
def sync_settings():
    #avoiding joins, for GAE
    rows = db().select(db.sync_partner.uuid)
    options = [row.uuid for row in rows]
    rows = db().select(db.sync_setting.uuid)
    for row in rows:
        options.remove(row.uuid)

    form = FORM(TABLE(
            #TR('Uuid', SELECT(*options, _name='uuid', requires=IS_IN_SET(options))),
            TR('Sync Policy', SELECT('Newer Timestamp', 'Keep All', 'Replace All', _name="policy")), #if this set is changed, then its corresponding set in admin model should also be changed
            TR('', INPUT(_name = 'submit', _type = 'submit', _value='Submit'))
            ))
    if form.accepts(request.vars, session):
        db.sync_setting.insert(uuid = form.vars.uuid,
                                    policy = form.vars.policy
                                    )
        response.flash = 'Inserted'

    records = db().select(db.sync_setting.ALL)
    return dict(form = form, records = records)

@auth.requires_login()
def autosync():
    "Shows history of database synchronizations"
    title = T('Automatic Database Synchronization History')
    #http://groups.google.com/group/web2py/browse_thread/thread/cc6180d335b14d62/c78affba95fcd4b5?lnk=gst&q=database+selection+unique#c78affba95fcd4b5
    #there is no good way of avoiding this, we can't restrict 'distinct' to fewer attributes
    history = db().select(db[logtable].ALL, orderby=db[logtable].timestamp)
    functions = ['getdata', 'putdata'] #as of two, only two funtions require for true syncing
    synced = {}
    for i in history:
        synced[i.uuid+i.function] = i
    todel = [i for i,j in synced.iteritems() if not ( j.uuid+functions[0] in synced.keys() and j.uuid+functions[1] in synced.keys() )]
    for each in todel:
        del synced[each]
    synced = synced.values()
    syncedids = [i.id for i in synced]
    #sort by time
    timestamps = [i.timestamp for i in synced]

    # insertion_sort
    for i in range(1, len(timestamps)):
        save = timestamps[i]
        saverow = synced[i]
        j = i
        while j > 0 and timestamps[j - 1] > save:
            timestamps[j] = timestamps[j - 1]
            synced[j] = synced[j-1]
            j -= 1
        timestamps[j] = save
        synced[j] = saverow
    synced.reverse()
    
    #SQLRows to list so that we can reverse it
    history = [i for i in history]
    history.reverse()
    return dict(title=title, synced=synced, syncedids=syncedids, history=history)

@service.json
@service.xml
@service.jsonrpc
@service.xmlrpc
def putdata(uuid, username, password, nicedbdump): #uuid of the system which is calling, wrong uuid can be provided?
    "Import data using weservices"
    #authentication is must here
    user = auth.login_bare(username, password)
    if not user:
        return "authentication failed"
    if uuid == None: #this should be extended and uuid should be made standard, like 16 bit blah blah
        return "invalid uuid"
    
    #parsing nicedbdump to see if it valid, unless we will throw error    
    #validator: validates if nicedbdump adhears to protocol defined by us
    #we never check nicedbdump size because its size reflects number of tables to be synced, as sahana is developing fastly so syncable tables can increase, moreover it doesnt fixin sync protocol
    if type(nicedbdump) == list:
        for nicetabledump in nicedbdump:
            if type(nicetabledump) == list:
                if len(nicetabledump) == 3: #size of this must be three
                    #table, table_attributes, table_data = nicetabledump #this gives same result as line under this
                    table, table_attributes, table_data = nicetabledump[0], nicetabledump[1], nicetabledump[2]
                    if (type(table) == str or type(table) == unicode) and type(table_attributes) == list and type(table_data) == list:
                        for attrib in table_attributes:
                            if not (type(attrib) == str or type(attrib) == unicode):
                                return 'atleast one attribute name is not of string type'
                        if not 'uuid' in table_attributes:
                            return 'atleast one table doesnt have "uuid" as attribute'
                        if not 'modified_on' in table_attributes:
                            return 'atleast one table doesnt have "modified_on" attribute'
                        if not 'id' in table_attributes:
                            return 'atleast one table doesnt have "id" attribute'
                        size = 0
                        isfirstiter = True
                        for row in table_data:
                            if type(row) == list:
                                if isfirstiter == True:
                                    size = len(row)
                                    isfirstiter = False
                                if not size == len(row):
                                    return 'all rows in ' + table + ' dont have same length'
                            else:
                                return 'row type can only be a list, atleast one element in ' + table + ' isnt of list type'
                        if not((size == 0) or (size == len(table_attributes))):
                            return 'you havent stated exact number of attribute names as attributes present in ' + table
                    else:
                        #return str(type(table)), str(type(table_attributes)), str(type(table_data))
                        return 'first element is each table is name of table(string), second is attribute names(list), third is data(list of list), atleast one of them in ' + table + ' is not of accepted data type'
                else:
                    return 'each table must have three elements, you havnt passed three'
            else:
                return 'each table is a list, you havnt passed atleast one table as list'
    else:
        return 'data can only in form of list'

    #now data object is validated, lets put it in object
    for table in nicedbdump:
        tablename = str(table[0]) #it might be unicode here
        tableattrib = table[1]
        tablerows = table[2]
            
        if tablename in db: #if a table in sent data is not present in local database, it is simply ignored
            ##check if user has right to insert in this table
            canupdate = shn_has_permission('update', tablename)
            caninsert = shn_has_permission('insert', tablename)
            if not (canupdate or caninsert):
                #build error return if required
                continue
            indexesavaliable = []
            for anattrib in tableattrib:
                if anattrib in db[tablename]["fields"]:
                    indexesavaliable.append(tableattrib.index(anattrib))
            for row in tablerows:
                rowuuid = row[tableattrib.index('uuid')]
                #rowid = row[tableattrib.index('id')]
                query = (db[tablename]['uuid'] == rowuuid)
                uuidcount = db(query).count()
                vals = {}
                for eachattribindex in indexesavaliable:
                    vals[tableattrib[eachattribindex]] = row[eachattribindex]
                if 'id' in vals: #ids are assigned by web2py itself
                    del vals['id']
                #now vals has insert dictionary
                
                if uuidcount == 0 and caninsert: #it means this row isnt present in current database
                    #direct db insert call
                    rowid = db[tablename].insert(**vals)
                    shn_audit_noform(resource = tablename, record = rowid, operation='create', representation='json')
                    #which audit function to call here?
                elif uuidcount == 1 and canupdate: #it means this particular tuple is present but might need modification, lets set to the one which has newer timestamp
                    security_policy_temp = db(db.sync_setting.uuid=='testing').select(db.sync_setting.policy)#[0].policy
                    if not len(security_policy_temp) == 0:
                        security_policy = security_policy_temp[0].policy
                    
                    if security_policy == 'Newer Timestamp':
                        #update only if given row is newer
                        a = row[tableattrib.index('modified_on')]
                        a = datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
                        b = db(db[tablename].uuid == row[tableattrib.index('uuid')]).select(db[tablename].modified_on)                
                        b = b[0].modified_on
                        if a > b:
                            rowid = db(query).update(**vals)
                            #shn_audit_update_m2m(resource = tablename, record = rowid, representation='json')
                            shn_audit_noform(resource = tablename, record = rowid, operation='update', representation='json')
                    elif security_policy == 'Replace All':
                        rowid = db(query).update(**vals)
                        #shn_audit_update_m2m(resource = tablename, record = rowid, representation='json')
                        shn_audit_noform(resource = tablename, record = rowid, operation='update', representation='json')
                else:
                    #uuidcount can never be more than 2, if we reach this place it means user is restricted by authentication
                    #if interpreter reached this line then either I am bad coder or you are hacker
                    return "error code number ..."
    
    #logging (not auditing)
    db[logtable].insert(
        uuid=uuid,
        function='putdata',
        timestamp=request.now,
        )
    
    return True

#function will take a date and uuid to caller and return new data only
#this is build on S3 (?)
#service.json traslates SQL into json but json-rpc doesnt, so we convert it into lists
@service.json
@service.xml
@service.jsonrpc
@service.xmlrpc
def getdata(uuid, username, password, timestamp = None): #if no timestamp is passed, system will return new data after last sync operation
    "Export data using webserices"
    "this funtion will never be called by foriegn service, so it doesnt requires authentication, but for the sack of API, we add this facility"
    "http://localhost:8000/sahana/admin/call/json/getdata?timestamp=0&uuid=asd&username=hasanatkazmi@gmail.com&password=asdfadsf"
    
    #we use this if we want to use export_json or export_xml functions
    #if 'json' in request['args'] or 'jsonrpc' in request['args']:
    #    function = export_json
    #    format ='json'
    #elif 'xml' in request['args'] or 'xmlrpc' in request['args']:
    #    function = export_xml
    #    format ='xml'
    #else:
    #    return "invalid call -- json/xml?" #invalid call
    
    if not IS_DATETIME(timestamp):
        return "invalid call -- time?" #invalid call

    #authentication across username and password, if local service calls the service, this shouldnt be raised
    if not request.client == "127.0.0.1": #local machine gets exzeption
        user = auth.login_bare(username, password)
        if not user:
            return "authentication failed"
    
    
    #this is bugy, check it
    #timestamp detemination
    if timestamp == None:
        lastsynctime = db(db[logtable].uuid == uuid).select(db[logtable].timestamp, orderby=~db[logtable].id)
        if len(lastsynctime) == 0: #there is no sync operation with this uuid
            timestamp = 0 # so return every thing
        else:
            timestamp = lastsynctime[0] 

    tables = [['budget', 'item'],
            ['budget', 'kit'],
            ['or', 'organisation'],
            ['or', 'office'],
            ['pr', 'person'],
            ['cr', 'shelter'],
            ['gis', 'feature'],
            ['gis', 'location']]

    nicedbdump = []
    for module, resource in tables:
        _table = '%s_%s' % (module, resource)
        table = db[_table]
        query = shn_accessible_query('read', table)
        query = query & (db[_table].modified_on > timestamp) #the date after last sync
        sqltabledump = db(query).select(db[_table].ALL) 
        nicetabledump = []
        nicetabledump.append(_table)
        nicetabledump.append(db[_table]["fields"])
        nicetabledumpdata = []
        for row in sqltabledump:
            temp = [row[col] for col in db[_table]["fields"]]
            nicetabledumpdata.append(temp)
        shn_audit_read(operation = 'read', resource = _table, record=None, representation= 'json') #this json must be replaced with generic term
        nicetabledump.append(nicetabledumpdata)
        #nicetabledump.append(function(table, query)) #we arent using this function because then we will have to manually translate json back into objects, lets web2py do it for ourlselves
        nicedbdump.append(nicetabledump)
    
    #logging (not auditing)
    db[logtable].insert(
        uuid=uuid,
        function='getdata',
        timestamp=request.now,
        )
    
    return nicedbdump

 
# Functional Testing
def handleResults():
    """Process the POST data returned from Selenium TestRunner.
    The data is written out to 2 files.  The overall results are written to 
    date-time-browserName-metadata.txt as a list of key: value, one per line.  The 
    suiteTable and testTables are written to date-time-browserName-results.html.
    """
    
    if not request.vars.result:
        # No results
        return
    
    # Read in results
    result = request.vars.result
    totalTime = request.vars.totalTime
    numberOfSuccesses = request.vars.numTestPasses
    numberOfFailures = request.vars.numTestFailures
    numberOfCommandSuccesses = request.vars.numCommandPasses
    numberOfCommandFailures = request.vars.numCommandFailures
    numberOfCommandErrors = request.vars.numCommandErrors

    suiteTable = ''
    if request.vars.suite:
        suiteTable = request.vars.suite
    
    testTables = []
    testTableNum = 1
    while request.vars['testTable.%s' % testTableNum]:
        testTable = request.vars['testTable.%s' % testTableNum]
        testTables.append(testTable)
        testTableNum += 1
        try:
            request.vars['testTable.%s' % testTableNum]
            pass
        except:
            break
    
    # Unescape the HTML tables
    import urllib
    suiteTable = urllib.unquote(suiteTable)
    testTables = map(urllib.unquote, testTables)

    # We want to store results separately for each browser
    browserName = getBrowserName(request.env.http_user_agent)
    date = str(request.now)[:-16]
    time = str(request.now)[11:-10]
    time = time.replace(':','-')

    # Write out results
    outputDir = os.path.join(request.folder, 'static', 'selenium', 'results')
    metadataFile = '%s-%s-%s-metadata.txt' % (date, time, browserName)
    dataFile = '%s-%s-%s-results.html' % (date, time, browserName)
    
    #xmlText = '<selenium result="' + result + '" totalTime="' + totalTime + '" successes="' + numberOfCommandSuccesses + '" failures="' + numberOfCommandFailures + '" errors="' + numberOfCommandErrors + '" />'
    f = open(os.path.join(outputDir, metadataFile), 'w')
    for key in request.vars.keys():
        if 'testTable' in key or key in ['log','suite']:
            pass
        else:
            print >> f, '%s: %s' % (key, request.vars[key])
    f.close()

    f = open(os.path.join(outputDir, dataFile), 'w')
    print >> f, suiteTable
    for testTable in testTables:
        print >> f, '<br/><br/>'
        print >> f, testTable
    f.close()
    
    message = DIV(P('Results have been successfully posted to the server here:'),
        P(A(metadataFile, _href=URL(r=request, c='static', f='selenium', args=['results', metadataFile]))),
        P(A(dataFile, _href=URL(r=request, c='static', f='selenium', args=['results', dataFile]))))
    
    response.view = 'display.html'
    title = T('Test Results')
    return dict(module_name=module_name, title=title, item=message)
