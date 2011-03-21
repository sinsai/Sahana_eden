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
        #[T("Home"), False, URL(r=request, f="index")],
        #[T("Search for a Person"), False, URL(r=request, f="person", args="search")],
        [T("Person"), False, None, [
            [T("New"), False, URL(r=request, f="person", args="create")],
            [T("Search"), False, URL(r=request, f="index")],
            [T("List All"), False, URL(r=request, f="person")],
        ]],
        [T("Groups"), False, URL(r=request, f="group"), [
            [T("New"), False, URL(r=request, f="group", args="create")],
            [T("List All"), False, URL(r=request, f="group")],
        ]],
        #[T("Help"), False, URL(r=request, f="guide")],
    ]

    #De-activating until fixed:
    #if s3_has_role(1):
        #response.menu_options.append([T("De-duplicator"), False, URL(r=request, f="person_duplicates")])

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
            if not r.id and not r.method:
                r.method = "search"
            else:
               redirect(URL(r=request, f="person", args=request.args))
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

    output = s3_rest_controller("pr", "person")
    response.view = "pr/index.html"
    response.title = module_name
    shn_menu()
    return output


# -----------------------------------------------------------------------------
def person():

    """ RESTful CRUD controller """

    def prep(r):

        # Test code (to be removed):
        #trackable = s3tracker(db.pr_pentity, 1)
        #print "Original location"
        #location = trackable.get_location()
        #if location:
            #print "Trackable location: %s lat=%s, lon=%s" % (location.name, location.lat, location.lon)
        #else:
            #print "No location found"
        #trackable.check_in(db.hms_hospital, 1)
        #location = trackable.get_location()
        #print "After check-in"
        #if location:
            #print "Trackable location: %s lat=%s, lon=%s" % (location.name, location.lat, location.lon)
        #else:
            #print "No location found"
        #trackable.check_out(db.hms_hospital)
        #location = trackable.get_location()
        #print "After check-out"
        #if location:
            #print "Trackable location: %s lat=%s, lon=%s" % (location.name, location.lat, location.lon)
        #else:
            #print "No location found"

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

    tablename = "pr_group"
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
def presence():

    """
        RESTful CRUD controller
        - needed for Map Popups (no Menu entry for direct access)
    """

    table = db.pr_presence

    # Settings suitable for use in Map Popups

    # This filter should be added to the gis_layer_feature query
    #response.s3.filter = ((table.presence_condition.belongs(vita.PERSISTANT_PRESENCE)) & \
    #                      (table.closed == False))

    table.pe_id.readable = True
    table.pe_id.label = "Name"
    table.pe_id.represent = shn_pr_person_represent
    table.observer.readable = False
    table.presence_condition.readable = False
    # @ToDo: Add Skills

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

#------------------------------------------------------------------------------
def guide():
    return dict()

#------------------------------------------------------------------------------
def person_duplicates():

    """ Handle De-duplication of People

        @todo: permissions, audit, update super entity, PEP8, optimization?
        @todo: check for component data!
        @todo: user accounts, subscriptions?
    """

    # Shortcut
    persons = db.pr_person

    table_header = THEAD(TR(TH(T("Person 1")),
                            TH(T("Person 2")),
                            TH(T("Match Percentage")),
                            TH(T("Resolve"))))

    # Calculate max possible combinations of records
    # To handle the AJAX requests by the dataTables jQuery plugin.
    totalRecords = db(persons.id > 0).count()

    item_list = []
    if request.vars.iDisplayStart:
        end = int(request.vars.iDisplayLength) + int(request.vars.iDisplayStart)
        records = db((persons.id > 0) & \
                     (persons.deleted == False) & \
                     (persons.first_name != None)).select(persons.id,         # Should this be persons.ALL?
                                                          persons.pe_label,
                                                          persons.missing,
                                                          persons.first_name,
                                                          persons.middle_name,
                                                          persons.last_name,
                                                          persons.preferred_name,
                                                          persons.local_name,
                                                          persons.age_group,
                                                          persons.gender,
                                                          persons.date_of_birth,
                                                          persons.nationality,
                                                          persons.country,
                                                          persons.religion,
                                                          persons.marital_status,
                                                          persons.occupation,
                                                          persons.tags,
                                                          persons.comments)

        # Calculate the match percentage using Jaro wrinkler Algorithm
        count = 1
        i = 0
        for onePerson in records: #[:len(records)/2]:
            soundex1= soundex(onePerson.first_name)
            array1 = []
            array1.append(onePerson.pe_label)
            array1.append(str(onePerson.missing))
            array1.append(onePerson.first_name)
            array1.append(onePerson.middle_name)
            array1.append(onePerson.last_name)
            array1.append(onePerson.preferred_name)
            array1.append(onePerson.local_name)
            array1.append(pr_age_group_opts.get(onePerson.age_group, T("None")))
            array1.append(pr_gender_opts.get(onePerson.gender, T("None")))
            array1.append(str(onePerson.date_of_birth))
            array1.append(pr_nations.get(onePerson.nationality, T("None")))
            array1.append(pr_nations.get(onePerson.country, T("None")))
            array1.append(pr_religion_opts.get(onePerson.religion, T("None")))
            array1.append(pr_marital_status_opts.get(onePerson.marital_status, T("None")))
            array1.append(onePerson.occupation)

            # Format tags into an array
            if onePerson.tags != None:
                tagname = []
                for item in onePerson.tags:
                    tagname.append(pr_impact_tags.get(item, T("None")))
                array1.append(tagname)

            else:
                array1.append(onePerson.tags)

            array1.append(onePerson.comments)
            i = i + 1
            j = 0
            for anotherPerson in records: #[len(records)/2:]:
                soundex2 = soundex(anotherPerson.first_name)
                if j >= i:
                    array2 =[]
                    array2.append(anotherPerson.pe_label)
                    array2.append(str(anotherPerson.missing))
                    array2.append(anotherPerson.first_name)
                    array2.append(anotherPerson.middle_name)
                    array2.append(anotherPerson.last_name)
                    array2.append(anotherPerson.preferred_name)
                    array2.append(anotherPerson.local_name)
                    array2.append(pr_age_group_opts.get(anotherPerson.age_group, T("None")))
                    array2.append(pr_gender_opts.get(anotherPerson.gender, T("None")))
                    array2.append(str(anotherPerson.date_of_birth))
                    array2.append(pr_nations.get(anotherPerson.nationality, T("None")))
                    array2.append(pr_nations.get(anotherPerson.country, T("None")))
                    array2.append(pr_religion_opts.get(anotherPerson.religion, T("None")))
                    array2.append(pr_marital_status_opts.get(anotherPerson.marital_status, T("None")))
                    array2.append(anotherPerson.occupation)

                    # Format tags into an array
                    if anotherPerson.tags != None:
                        tagname = []
                        for item in anotherPerson.tags:
                            tagname.append(pr_impact_tags.get(item, T("None")))
                        array2.append(tagname)
                    else:
                        array2.append(anotherPerson.tags)

                    array2.append(anotherPerson.comments)
                    if count > end and request.vars.max != "undefined":
                        count = int(request.vars.max)
                        break;
                    if onePerson.id == anotherPerson.id:
                        continue
                    else:
                        mpercent = jaro_winkler_distance_row(array1, array2)
                        # Pick all records with match percentage is >50 or whose soundex values of first name are equal
                        if int(mpercent) > 50 or (soundex1 == soundex2):
                            count = count + 1
                            item_list.append([onePerson.first_name,
                                              anotherPerson.first_name,
                                              mpercent,
                                              "<a href=\"../pr/person_resolve?perID1=%i&perID2=%i\", class=\"action-btn\">Resolve</a>" % (onePerson.id, anotherPerson.id)
                                             ])
                        else:
                            continue
                j = j + 1
        item_list = item_list[int(request.vars.iDisplayStart):end]
        # Convert data to JSON
        result  = []
        result.append({
                    "sEcho" : request.vars.sEcho,
                    "iTotalRecords" : count,
                    "iTotalDisplayRecords" : count,
                    "aaData" : item_list
                    })
        output = json.dumps(result)
        # Remove unwanted brackets
        output = output[1:]
        output = output[:-1]
        return output

    else:
        # Don't load records except via dataTables (saves duplicate loading & less confusing for user)
        items = DIV((TABLE(table_header, TBODY(), _id="list", _class="display")))
        return(dict(items=items))

#----------------------------------------------------------------------------------------------------------
def delete_person():

    """ To delete references to the old record and replace it with the new one.

        @todo: components??? cannot simply be re-linked!
        @todo: user accounts?
        @todo: super entity not updated!
    """

    # @ToDo: Error gracefully if conditions not satisfied
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

#------------------------------------------------------------------------------------------------------------------
def person_resolve():

    """ This opens a popup screen where the de-duplication process takes place.

        @todo: components??? cannot simply re-link!
        @todo: user accounts linked to these records?
        @todo: update the super entity!
        @todo: use S3Resources, implement this as a method handler

    """

    # @ToDo: Error gracefully if conditions not satisfied
    perID1 = request.vars.perID1
    perID2 = request.vars.perID2

    # Shortcut
    persons = db.pr_person

    count = 0
    for field in persons:
        id1 = str(count) + "Right"      # Gives a unique number to each of the arrow keys
        id2 = str(count) + "Left"
        count  = count + 1;
        # Comment field filled with buttons
        field.comment = DIV(TABLE(TR(TD(INPUT(_type="button", _id=id1, _class="rightArrows", _value="-->")),
                                     TD(INPUT(_type="button", _id=id2, _class="leftArrows", _value="<--")))))
        record = persons[perID1]
    myUrl = URL(r=request, c="pr", f="person")
    form1 = SQLFORM(persons, record, _id="form1", _action=("%s/%s" % (myUrl, perID1)))

    # For the second record remove all the comments to save space.
    for field in persons:
        field.comment = None
    record = persons[perID2]
    form2 = SQLFORM(persons, record, _id="form2", _action=("%s/%s" % (myUrl, perID2)))
    return dict(form1=form1, form2=form2, perID1=perID1, perID2=perID2)

# -----------------------------------------------------------------------------
