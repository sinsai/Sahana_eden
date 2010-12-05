# -*- coding: utf-8 -*-

""" VITA Person Registry, Controllers

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

prefix = request.controller
resourcename = request.function

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
def shn_menu():
    response.menu_options = [
        [T("Home"), False, URL(r=request, f="index")],
        [T("Search for a Person"), False, URL(r=request, f="person", args="search_simple")],
        [T("Persons"), False, URL(r=request, f="person"), [
            [T("List"), False, URL(r=request, f="person")],
            [T("Add"), False, URL(r=request, f="person", args="create")],
        ]],
        [T("Groups"), False, URL(r=request, f="group"), [
            [T("List"), False, URL(r=request, f="group")],
            [T("Add"), False, URL(r=request, f="group", args="create")],
        ]],
        [T("Deduplicator"), False, URL(r=request, f="people_duplicates")]]
    menu_selected = []
    if session.rcvars and "pr_group" in session.rcvars:
        group = db.pr_group
        query = (group.id == session.rcvars["pr_group"])
        record = db(query).select(group.id, group.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Group"), name), False,
                                 URL(r=request, f="group", args=[record.id])])
    if session.rcvars and "pr_person" in session.rcvars:
        person = db.pr_person
        query = (person.id == session.rcvars["pr_person"])
        record = db(query).select(person.id, limitby=(0, 1)).first()
        if record:
            name = shn_pr_person_represent(record.id)
            menu_selected.append(["%s: %s" % (T("Person"), name), False,
                                 URL(r=request, f="person", args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

shn_menu()


# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    try:
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Person Registry")

    def prep(r):
        if r.representation == "html":
            if not r.id:
                r.method = "search_simple"
                r.custom_action = shn_pr_person_search_simple
            else:
               redirect(URL(r=request, f="person", args=[r.id]))
        return True
    response.s3.prep = prep

    def postp(r, output):
        if isinstance(output, dict):
            gender = []
            for g_opt in pr_gender_opts:
                count = db((db.pr_person.deleted == False) & \
                        (db.pr_person.gender == g_opt)).count()
                gender.append([str(pr_gender_opts[g_opt]), int(count)])

            age = []
            for a_opt in pr_age_group_opts:
                count = db((db.pr_person.deleted == False) & \
                        (db.pr_person.age_group == a_opt)).count()
                age.append([str(pr_age_group_opts[a_opt]), int(count)])

            total = int(db(db.pr_person.deleted == False).count())
            output.update(module_name=module_name, gender=gender, age=age, total=total)
        if r.representation in shn_interactive_view_formats:
            if not r.component:
                label = READ
            else:
                label = UPDATE
            linkto = r.resource.crud._linkto(r)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        r.next = None
        return output
    response.s3.postp = postp

    if auth.shn_logged_in():
        add_btn = A(T("Add Person"),
                    _class="action-btn",
                    _href=URL(r=request, f="person", args="create"))
    else:
        add_btn = None

    output = s3_rest_controller("pr", "person",
                                add_btn=add_btn)
    response.view = "pr/index.html"

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    def prep(r):
        if r.component_name == "config":
            _config = db.gis_config
            defaults = db(_config.id == 1).select(limitby=(0, 1)).first()
            for key in defaults.keys():
                if key not in ["id", "uuid", "mci", "update_record", "delete_record"]:
                    _config[key].default = defaults[key]
        if r.representation == "popup":
            # Hide "pe_label" and "missing" fields in person popups
            r.table.pe_label.readable = False
            r.table.pe_label.writable = False
            r.table.missing.readable = False
            r.table.missing.writable = False
        return True
    response.s3.prep = prep

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "group_id",
                                       "group_head",
                                       "description"])

    table = db.pr_person
    s3xrc.model.configure(table, listadd = False, insertable = True)

    output = s3_rest_controller(prefix, resourcename,
                                main="first_name",
                                extra="last_name",
                                rheader=lambda r: shn_pr_rheader(r,
                                    tabs = [(T("Basic Details"), None),
                                            (T("Images"), "image"),
                                            (T("Identity"), "identity"),
                                            (T("Address"), "address"),
                                            (T("Contact Data"), "pe_contact"),
                                            (T("Memberships"), "group_membership"),
                                            (T("Presence Log"), "presence"),
                                            (T("Subscriptions"), "pe_subscription"),
                                            (T("Map Settings"), "config")
                                            ]))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def group():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    response.s3.filter = (db.pr_group.system == False) # do not show system groups

    s3xrc.model.configure(db.pr_group_membership,
                          list_fields=["id",
                                       "person_id",
                                       "group_head",
                                       "description"])

    output = s3_rest_controller(prefix, resourcename,
                rheader=lambda r: shn_pr_rheader(r,
                    tabs = [(T("Group Details"), None),
                            (T("Address"), "address"),
                            (T("Contact Data"), "pe_contact"),
                            (T("Members"), "group_membership")]))

    shn_menu()
    return output


# -----------------------------------------------------------------------------
def image():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def pe_contact():

    """ RESTful CRUD controller """

    table = db.pr_pe_contact

    table.pe_id.label = T("Person/Group")
    table.pe_id.readable = True
    table.pe_id.writable = True

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
#def group_membership():

    #""" RESTful CRUD controller """

    #return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def pentity():

    """ RESTful CRUD controller """

    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
def download():

    """ Download a file.

        @todo: deprecate? (individual download handler probably not needed)

    """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def tooltip():

    """ Ajax tooltips """

    if "formfield" in request.vars:
        response.view = "pr/ajaxtips/%s.html" % request.vars.formfield
    return dict()

#----------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------
#To delete references to a old record and replace it with the new one.
def delete_person():
    old = request.vars.old
    new = request.vars.new
    # Find all tables which link to the pr_person table
    
    tables = shn_table_links("pr_person")
    
    for table in tables:
        for count in range(len(tables[table])):
            field = tables[str(db[table])][count]
            query = db[table][field] == old
            db(query).update(**{field:new})

    # Remove the record
    db(db.pr_person.id == old).update(deleted=True)
    return "Other Record Deleted, Linked Records Updated Successfully"

#This opens a popup screen where the deduplication process takes place.
def person_resolve():
    count = 0
    
    for field in db["pr_person"]:
        id1 = str(count) + "Right"      #Gives a unique number to each of the arrow keys
        id2 = str(count) + "Left"
        count  = count + 1;
        #Comment field filled with buttons
        field.comment = DIV(TABLE(TR(TD(INPUT(_type="button", _id=id1,_class="rightArrows",_value="-->")),TD(INPUT(_type="button", _id=id2,_class="leftArrows",_value="<--")))))
        record = db.pr_person[request.vars.perID1]
    myUrl = URL(r=request, c="pr", f="person")
    #create sqlform for the record
    form1 = SQLFORM(db.pr_person, record,_id="form1",_action=(myUrl+"/"+request.vars.perID1))
    
    #For the second record remove all the comments to save space.
    for field in db["pr_person"]:
        field.comment = None
    record = db.pr_person[request.vars.perID2]
    form2 = SQLFORM(db.pr_person, record,_id="form2",_action=(myUrl+"/"+request.vars.perID2))
    return dict(form1=form1,form2=form2,perID1=request.vars.perID1,perID2=request.vars.perID2)    
#------------------------------------------------------------------------------------------------------------------
#                                 S08 - person De-Duplicator Module                                               #
#------------------------------------------------------------------------------------------------------------------

def people_duplicates():
    """
        Handle De-duplication of People
    """
    #Import the s3deduplicator module necessary to find the soundex and match percentage of records
    
    s3deduplicator = local_import("s3deduplicator")
    table_header = THEAD(TR(TH("Person 1"),TH("Person 2"),TH("Match Percentage"),TH("Resolve")))
    totalRecords = db(db.pr_person.id > 0).count()
    #Calculating max possible combinations of records
    #To handle the AJAX requests by the table plugin to jquery.
    item_list = []
    if request.vars.iDisplayStart:
        end = int(request.vars.iDisplayLength)+int(request.vars.iDisplayStart)
        records = db((db.pr_person.id>0)&(db.pr_person.deleted==False)&(db.pr_person.first_name!=None)).select(db.pr_person.id, db.pr_person.pe_label, db.pr_person.missing, db.pr_person.first_name, db.pr_person.middle_name, db.pr_person.last_name, db.pr_person.preferred_name, db.pr_person.local_name, db.pr_person.age_group, db.pr_person.gender, db.pr_person.date_of_birth, db.pr_person.nationality, db.pr_person.country, db.pr_person.religion, db.pr_person.marital_status, db.pr_person.occupation, db.pr_person.tags, db.pr_person.comments)
        count = 1
        i=0
        
        #calculating the match percentage using Jaro wrinkler Algo
        for onePerson in records: #[:len(records)/2]:
            soundex1= s3deduplicator.soundex(onePerson.first_name)
            array1 =[]
            array1.append(onePerson.pe_label)
            array1.append(str(onePerson.missing))
            array1.append(onePerson.first_name)
            array1.append(onePerson.middle_name)
            array1.append(onePerson.last_name)
            array1.append(onePerson.preferred_name)
            array1.append(onePerson.local_name)
            array1.append(pr_age_group_opts.get(onePerson.age_group,T('None')))        
            array1.append(pr_gender_opts.get(onePerson.gender, T('none')))
            array1.append(str(onePerson.date_of_birth))
            array1.append(pr_nations.get(onePerson.nationality,T('None')))
            array1.append(pr_nations.get(onePerson.country,T('None')))
            array1.append(pr_religion_opts.get(onePerson.religion,T('None')))
            array1.append(pr_marital_status_opts.get(onePerson.marital_status,T('None')))
            array1.append(onePerson.occupation)
            #formatting tags into an array
            if onePerson.tags !=None:
               tagname = []
               for item in onePerson.tags:
                   tagname.append(pr_impact_tags.get(item,T('None')))
                   
               array1.append(tagname)
            else:
                   array1.append(onePerson.tags)
            
            array1.append(onePerson.comments)
            print "Array1*************************"   
            print array1
            i=i+1
            j = 0
            for anotherPerson in records: #[len(records)/2:]:
              soundex2= s3deduplicator.soundex(anotherPerson.first_name)
              if j >= i:
                array2 =[]
       		array2.append(anotherPerson.pe_label)
                array2.append(str(anotherPerson.missing))
                array2.append(anotherPerson.first_name)
                array2.append(anotherPerson.middle_name)
                array2.append(anotherPerson.last_name)
                array2.append(anotherPerson.preferred_name)
                array2.append(anotherPerson.local_name)
                array2.append(pr_age_group_opts.get(anotherPerson.age_group,T('None')))        
                array2.append(pr_gender_opts.get(anotherPerson.gender, T('None')))
                array2.append(str(anotherPerson.date_of_birth))
                array2.append(pr_nations.get(anotherPerson.nationality,T('None')))
                array2.append(pr_nations.get(anotherPerson.country,T('None')))
                array2.append(pr_religion_opts.get(anotherPerson.religion,T('None')))
                array2.append(pr_marital_status_opts.get(anotherPerson.marital_status,T('None')))
                array2.append(anotherPerson.occupation)
                #formatting tags into an array
                if anotherPerson.tags !=None:
                   tagname = []
                   for item in anotherPerson.tags:
                       tagname.append(pr_impact_tags.get(item,T('None')))
                       print item
                   array2.append(tagname)
                else:
                   array2.append(anotherPerson.tags)
                
                array2.append(anotherPerson.comments)
                print "Array2*************************"   
                print array2
                if count > end and request.vars.max != "undefined":
                    count = int(request.vars.max)
                    break;
                if onePerson.id == anotherPerson.id:
                    continue
                else:
                    mpercent = s3deduplicator.jaro_winkler_distance_row(array1,array2)
                    #print int(mpercent)
                    #pick all records with match percentage is >50 or whose soundex values of first name are equal
                    if int(mpercent) > 50 or soundex1==soundex2:
                        count = count + 1
                        item_list.append([onePerson.first_name,anotherPerson.first_name,mpercent,"<a href=\"../pr/person_resolve?perID1="+str(onePerson.id)+"&perID2="+str(anotherPerson.id)+"\", class=\"action-btn\">Resolve</a>"])
                    else:
                        continue
              j = j + 1
        item_list = item_list[int(request.vars.iDisplayStart):end]
        #Need to convert data to JSON
        import gluon.contrib.simplejson as json
        result  = []
        result.append({
                    "sEcho" : request.vars.sEcho,
                    "iTotalRecords" : count,
                    "iTotalDisplayRecords" : count,
                    "aaData" : item_list
                    })
        output = json.dumps(result)
        output = output[1:] #remove unwanted brackets
        output = output[:-1]
        return output
    else:
        records = db((db.pr_person.id>0)&(db.pr_person.deleted==False)&(db.pr_person.first_name!=None)).select(db.pr_person.id, db.pr_person.pe_label, db.pr_person.missing, db.pr_person.first_name, db.pr_person.middle_name, db.pr_person.last_name, db.pr_person.preferred_name, db.pr_person.local_name, db.pr_person.age_group, db.pr_person.gender, db.pr_person.date_of_birth, db.pr_person.nationality, db.pr_person.country, db.pr_person.religion, db.pr_person.marital_status, db.pr_person.occupation, db.pr_person.tags, db.pr_person.comments)
        item_list1 = []
        count = 1
        #Just for the initial look
        for onePerson in records:
            array1 =[]
            array1.append(onePerson.pe_label)
            array1.append(str(onePerson.missing))
            array1.append(onePerson.first_name)
            array1.append(onePerson.middle_name)
            array1.append(onePerson.last_name)
            array1.append(onePerson.preferred_name)
            array1.append(onePerson.local_name)
            array1.append(pr_age_group_opts.get(onePerson.age_group,T('None')))        
            array1.append(pr_gender_opts.get(onePerson.gender, T('none')))
            array1.append(str(onePerson.date_of_birth))
            array1.append(pr_nations.get(onePerson.nationality,T('None')))
            array1.append(pr_nations.get(onePerson.country,T('None')))
            array1.append(pr_religion_opts.get(onePerson.religion,T('None')))
            array1.append(pr_marital_status_opts.get(onePerson.marital_status,T('None')))
            array1.append(onePerson.occupation)
            #formatting tags into an array
            if onePerson.tags !=None:
               tagname = []
               for item in onePerson.tags:
                   tagname.append(pr_impact_tags.get(item,T('None')))
                   print item
               array1.append(tagname)
            else:
               array1.append(onePerson.tags)
            
            array1.append(onePerson.comments)
            print "Array1*************************" 
            print array1  
            for anotherPerson in records:
                array2 =[]
       		array2.append(anotherPerson.pe_label)
                array2.append(str(anotherPerson.missing))
                array2.append(anotherPerson.first_name)
                array2.append(anotherPerson.middle_name)
                array2.append(anotherPerson.last_name)
                array2.append(anotherPerson.preferred_name)
                array2.append(anotherPerson.local_name)
                array2.append(pr_age_group_opts.get(anotherPerson.age_group,T('None')))        
                array2.append(pr_gender_opts.get(anotherPerson.gender, T('None')))
                array2.append(str(anotherPerson.date_of_birth))
                array2.append(pr_nations.get(anotherPerson.nationality,T('None')))
                array2.append(pr_nations.get(anotherPerson.country,T('None')))
                array2.append(pr_religion_opts.get(anotherPerson.religion,T('None')))
                array2.append(pr_marital_status_opts.get(anotherPerson.marital_status,T('None')))
                array2.append(anotherPerson.occupation)
                if anotherPerson.tags !=None:
                   tagname = []
                   for item in anotherPerson.tags:
                       tagname.append(pr_impact_tags.get(item,T('None')))
                       print item
                   array2.append(tagname)
                else:
                   array2.append(anotherPerson.tags)
                #array2.append(anotherPerson.tags)
                array2.append(anotherPerson.comments)  
                print "Array2*************************"   
                print array2            
                count = count + 1
                if count  > 20:
                    break
                if onePerson.id == anotherPerson.id:
                    continue
                else:
                    mpercent = s3deduplicator.jaro_winkler_distance_row(array1,array2)
                    item_list1.append(TR(TD(onePerson.first_name),TD(anotherPerson.first_name),TD(mpercent),TD(A("Resolve",_href=URL(r=request, f="person_resolve"),_class="action-btn"))))
        items = DIV((TABLE(table_header,TBODY(item_list1),_id="list",_class="display")))
        return(dict(items=items))

# -----------------------------------------------------------------------------


