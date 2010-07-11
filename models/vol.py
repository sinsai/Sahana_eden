# -*- coding: utf-8 -*-

"""
    Volunteer Management System

    @author: zubair assad
    @author: nursix
"""

module = "vol"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = module + "_" + resource
    table = db.define_table(tablename,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_volunteer (Component of pr_person)
    #   describes a person's availability as a volunteer
    #
    vol_volunteer_status_opts = {
    1: T("active"),
    2: T("retired")
    }

    resource = "volunteer"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                    person_id,
                    organisation_id,
                    Field("date_avail_start", "date"),
                    Field("date_avail_end", "date"),
                    Field("hrs_avail_start", "time"),
                    Field("hrs_avail_end", "time"),
                    Field("status", "integer",
                        requires = IS_IN_SET(vol_volunteer_status_opts, zero=None),
                        # default = 1,
                        label = T("Status"),
                        represent = lambda opt: vol_volunteer_status_opts.get(opt, UNKNOWN_OPT)),
                    Field("special_needs", "text"),
                    migrate=migrate)

    # Settings and Restrictions

    # Field labels
    table.date_avail_start.label = T("Available from")
    table.date_avail_end.label = T("Available until")
    table.hrs_avail_start.label = T("Working hours start")
    table.hrs_avail_end.label = T("Working hours end")
    table.special_needs.label = T("Special needs")

    # Representation function
    def shn_vol_volunteer_represent(id):
        person = db((db.vol_volunteer.id == id) & (db.pr_person.id == db.vol_volunteer.person_id)).select(
                    db.pr_person.first_name,
                    db.pr_person.middle_name,
                    db.pr_person.last_name,
                    limitby=(0, 1))
        if person:
            return vita.fullname(person.first())
        else:
            return None

    # CRUD Strings
    ADD_VOLUNTEER = T("Add Volunteer Registration")
    VOLUNTEERS = T("Volunteer Registrations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VOLUNTEER,
        title_display = T("Volunteer Registration"),
        title_list = VOLUNTEERS,
        title_update = T("Edit Volunteer Registration"),
        title_search = T("Search Volunteer Registrations"),
        subtitle_create = ADD_VOLUNTEER,
        subtitle_list = VOLUNTEERS,
        label_list_button = T("List Registrations"),
        label_create_button = T("Add Volunteer Registration"),
        msg_record_created = T("Volunteer registration added"),
        msg_record_modified = T("Volunteer registration updated"),
        msg_record_deleted = T("Volunteer registration deleted"),
        msg_list_empty = T("No volunteer information registered"))

    # Reusable field
    vol_volunteer_id = db.Table(None, "vol_volunteer_id",
                                FieldS3("vol_volunteer_id", db.vol_volunteer, sortby=["first_name", "middle_name", "last_name"],
                                requires = IS_NULL_OR(IS_ONE_OF(db(db.vol_volunteer.status == 1), "vol_volunteer.id", shn_vol_volunteer_represent)),
                                represent = lambda id: (id and [shn_vol_volunteer_represent(id)] or ["None"])[0],
                                comment = DIV(A(s3.crud_strings.vol_volunteer.label_create_button, _class="colorbox", _href=URL(r=request, c="vol", f="volunteer", args="create", vars=dict(format="popup")), _target="top", _title=s3.crud_strings.vol_volunteer.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Volunteer|Add new volunteer)."))),
                                ondelete = "RESTRICT"
                            ))

    s3xrc.model.add_component(module, resource,
                              multiple=False,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True,
                              main="person_id", extra="organisation_id")

    s3xrc.model.configure(table,
                          list_fields=["organisation_id",
                                       "status"])

    # -----------------------------------------------------------------------------
    # vol_resource (Component of pr_person)
    #   describes resources (skills, tools) of a volunteer
    #
    vol_resource_type_opts = {
        1:T("General Skills"),
        2:T("Resources"),
        3:T("Restrictions"),
        4:T("Site Manager"),
        5:T("Unskilled"),
        99:T("Other")
    }

    vol_resource_subject_opts = {
        1:T("Animals"),
        2:T("Automotive"),
        3:T("Baby And Child Care"),
        4:T("Tree"),
        5:T("Warehouse"),
        99:T("Other")
    }

    vol_resource_deployment_opts = {
        1:T("Building Aide"),
        2:T("Vehicle"),
        3:T("Warehouse"),
        99:T("Other")
    }

    vol_resource_status_opts = {
        1:T("approved"),
        2:T("unapproved"),
        3:T("denied")
    }

    resource = "resource"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp,
                    person_id,
                    Field("type", "integer",
                        requires = IS_IN_SET(vol_resource_type_opts, zero=None),
                        # default = 99,
                        label = T("Resource"),
                        represent = lambda opt: vol_resource_type_opts.get(opt, UNKNOWN_OPT)),
                    Field("subject", "integer",
                        requires = IS_IN_SET(vol_resource_subject_opts, zero=None),
                        # default = 99,
                        label = T("Subject"),
                        represent = lambda opt: vol_resource_subject_opts.get(opt, UNKNOWN_OPT)),
                    Field("deployment", "integer",
                        requires = IS_IN_SET(vol_resource_deployment_opts, zero=None),
                        # default = 99,
                        label = T("Deployment"),
                        represent = lambda opt: vol_resource_deployment_opts.get(opt, UNKNOWN_OPT)),
                    Field("status", "integer",
                        requires = IS_IN_SET(vol_resource_status_opts, zero=None),
                        # default = 2,
                        label = T("Status"),
                        represent = lambda opt: vol_resource_status_opts.get(opt, UNKNOWN_OPT)),
                    migrate=migrate)

    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(pr_person="person_id"),
                              deletable=True,
                              editable=True,
                              main="person_id", extra="subject")

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "type",
                                       "subject",
                                       "deployment",
                                       "status"])

    # CRUD Strings
    ADD_RESOURCE = T("Add Resource")
    RESOURCES = T("Resources")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RESOURCE,
        title_display = T("Resource Details"),
        title_list = RESOURCES,
        title_update = T("Edit Resource"),
        title_search = T("Search Resources"),
        subtitle_create = T("Add New Resource"),
        subtitle_list = RESOURCES,
        label_list_button = T("List Resources"),
        label_create_button = ADD_RESOURCE,
        msg_record_created = T("Resource added"),
        msg_record_modified = T("Resource updated"),
        msg_record_deleted = T("Resource deleted"),
        msg_list_empty = T("No resources currently registered"))

    # -----------------------------------------------------------------------------
    # vol_hours:
    #   documents the hours a volunteer has a position
    #
    #resource = "hours"
    #table = module + "_" + resource
    #db.define_table(table,
    #                person_id,
    #                vol_position_id,
    #                Field("shift_start", "datetime", label=T("shift_start"), notnull=True),
    #                Field("shift_end", "datetime", label=T("shift_end"), notnull=True),
    #                migrate=migrate)

    #db[table].shift_start.requires=[IS_NOT_EMPTY(),
    #                                      IS_DATETIME]
    #db[table].shift_end.requires=[IS_NOT_EMPTY(),
    #                                      IS_DATETIME]

    # -----------------------------------------------------------------------------
    # vol_mailbox
    #
    #resource = "mailbox"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp, deletion_status,
    #                person_id,
    #                Field("message_id", "integer", notnull=True,label=T("message_id"), default=0),
    #    Field("box", "integer", notnull=True, label=T("box"), default=0),
    #    Field("checked", "integer", label=T("checked"), default=0),
    #    migrate=migrate)


    # -----------------------------------------------------------------------------
    # vol_message
    #   a text message
    #
    #resource = "message"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp, deletion_status,
    #                Field("message", "text", label=T("message")),
    #                Field("time", "datetime", label=T("time"), notnull=True, default=request.now),
    #                migrate=migrate)

    # -----------------------------------------------------------------------------
    # courier
    #resource = "courier"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #db.define_table("vol_courier", timestamp, uuidstamp,
    #    Field("message_id", "integer", label=T("message_id"), notnull=True),
    #    Field("to_id", "string", label=T("to_id"), notnull=True),
    #    Field("from_id", "string", label=T("from_id"), notnull=True),
    #    migrate=migrate)

    #db[table].message_id.requires = IS_NOT_EMPTY()
    #db[table].to_id.requires = IS_NOT_EMPTY()
    #db[table].from_id.requires = IS_NOT_EMPTY()
    #db[table].message_id.requires = IS_NOT_NULL()

    # -----------------------------------------------------------------------------
    # vol_access_request
    #resource = "access_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", "integer", notnull=True),
    #    Field("act", "string", length=100, label=T("act")),
    #    Field("vm_action", "string", length=100, label=T("vm_action")),
    #    Field("description", "string", length=300, label=T("description")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_constraint
    #resource = "access_constraint"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("constraint_id","string", length=30, notnull=True, default=" ", label=T("constraint_id")),
    #    Field("description","string", length=200,label=T("description")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_constraint_to_request
    #resource = "access_constraint_to_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", db.vol_access_request),
    #    Field("constraint_id", db.vol_access_constraint),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # vol_access_classification_to_request
    #resource = "access_classification_to_request"
    #table = module + "_" + resource
    #db.define_table(table, timestamp, uuidstamp,
    #    Field("request_id", "integer", length=11, notnull=True, default=0),
    #    Field("table_name", "string", length=200, notnull=True, default=" ", label=T("table_name")),
    #    Field("crud", "string", length=4, notnull=True, default=" ", label=T("crud")),
    #    migrate=migrate)

    # -----------------------------------------------------------------------------
    # shn_vol_project_search_location:
    #   form function to search projects by location
    #
    def shn_vol_project_search_location(xrequest, **attr):

        if attr is None:
            attr = {}

        if not shn_has_permission('read', db.vol_project):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_location', vars=request.vars)}))

        if xrequest.representation=="html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = str.lower(URL(r=request, f='project', args='[id]'))

            # Custom view
            response.view = '%s/project_search.html' % xrequest.prefix

            # Title and subtitle
            title = T('Search for a Project')
            subtitle = T('Matching Records')

            # Select form:
            l_opts = [OPTION(_value='')]
            l_opts += [OPTION(location.name, _value=location.id)
                    for location in db(db.gis_location.deleted == False).select(db.gis_location.ALL, cache=(cache.ram, 3600))]
            form = FORM(TABLE(
                    TR(T('Location: '),
                    SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db, 'gis_location.id'))))),
                    TR("", INPUT(_type="submit", _value="Search"))
                    ))

            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                table = db.vol_project
                query = (table.deleted == False)

                if form.vars.location is None:
                    results = db(query).select(table.ALL)
                else:
                    query = query & (table.location_id == form.vars.location)
                    results = db(query).select(table.ALL)

                if results and len(results):
                    records = []
                    for result in results:
                        href = next.replace("%5bid%5d", "%s" % result.id)
                        records.append(TR(
                            A(result.name, _href=href),
                            result.start_date or "None",
                            result.end_date or "None",
                            result.description or "None",
                            result.status and vol_project_status_opts[result.status] or "unknown",
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("Name"),
                        TH("Start date"),
                        TH("End date"),
                        TH("Description"),
                        TH("Status"))),
                        TBODY(records), _id='list', _class="display"))
                else:
                        items = T("None")

            try:
                label_create_button = s3.crud_strings["vol_project"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button

            add_btn = A(label_create_button, _href=URL(r=request, f="project", args="create"), _class='action-btn')

            output.update(dict(items=items, add_btn=add_btn))

            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, "project", method="search_location", action=shn_vol_project_search_location )

    # -----------------------------------------------------------------------------
    # shn_vol_project_search_location:
    #   form function to search projects by location
    #
    def shn_vol_project_rheader(jr):

        if jr.name == "project":
            if jr.representation == "html":

                _next = jr.here()
                _same = jr.same()

                project = jr.record
                if project:
                    rheader = TABLE(
                        TR(
                            TH(T('Name: ')),
                            project.name,
                            TH(A(T('Clear Selection'),
                                _href=URL(r=request, f='project', args='clear', vars={'_next': _same})))
                            ),
                        TR(
                            TH(T('Location: ')),
                            location_id.location_id.represent(project.location_id),
                            TH(""),
                            ),
                        TR(
                            TH(T('Status: ')),
                            "%s" % vol_project_status_opts[project.status],
                            TH(A(T('Edit Project'),
                                _href=URL(r=request, f='project', args=['update', jr.id], vars={'_next': _next})))
                            )
                    )
                    return rheader

        return None

    # -----------------------------------------------------------------------------
    # vol_skill_types
    #   Customize to add more client defined Skill
    #

    resource = 'skill_types'
    tablename = module + '_' + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
            Field('name',  length=128,notnull=True),                      
            Field('category', 'string', length=50),
            Field('description'),
            migrate=migrate)

    # Field settings
    table.uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % tablename)
    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % tablename)]
    table.name.label = T('Name')
    table.name.comment = SPAN("*", _class="req")

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = T('Add Skill Type'),
        title_display = T('Skill Type Details'),
        title_list = T('Skill Type'),
        title_update = T('Edit Skill Type'),
        title_search = T('Search Skill Type'),
        subtitle_create = T('Add New Skill Type'),
        subtitle_list = T('Skill Type'),
        label_list_button = T('List Skill Types'),
        label_create_button = T('Add Skill Types'),
        label_delete_button = T('Delete Skill Type'),
        msg_record_created = T('Skill Type added'),
        msg_record_modified = T('Skill Type updated'),
        msg_record_deleted = T('Skill Type deleted'),
        msg_list_empty = T('No Skill Types currently set'))

    field_settings = S3CheckboxesWidget(db = db, 
                                        lookup_table_name = "vol_skill_types", 
                                        lookup_field_name = "name",
                                        multiple = True,
                                        num_column=3
                                        )

    # Reusable field
    skill_ids = db.Table(None, 'skill_ids',
                         FieldS3('skill_ids',
                         requires = field_settings.requires,
                         widget = field_settings.widget,
                         represent = field_settings.represent,
                         label = T("skills"),
                         ondelete = "RESTRICT"))

    # Representation function
    def vol_skill_types_represent(id):
        if id:
            record = db(db.vol_skill_types.id == id).select().first()
            category = record.category
            name = record.name
            if category:
                return "%s: %s" % (category, name)
            else:
                return name
        else:
            return None


    # -----------------------------------------------------------------------------
    # vol_skill
    #   Selecting a Skill
    #

    def multiselect_widget(f,v):
	import uuid
	d_id = "multiselect-" + str(uuid.uuid4())[:8]
	wrapper = DIV(_id=d_id)
	inp = SQLFORM.widgets.options.widget(f,v)
	inp['_multiple'] = 'multiple'
	inp['_style'] = 'min-width: %spx;' % (len(f.name) * 20 + 50)
	if v:
	    if not isinstance(v,list): v = str(v).split('|')
	    opts = inp.elements('option')
	    for op in opts:
	        if op['_value'] in v:
	            op['_selected'] = 'selected'            
	scr = SCRIPT('jQuery("#%s select").multiSelect({'\
	             'noneSelected:"Select %ss"});' % (d_id,f.name))
	wrapper.append(inp)
	wrapper.append(scr)
	if request.vars.get(inp['_id']+'[]',None):
	    var = request.vars[inp['_id']+'[]']
	    if not isinstance(var,list): var = [var]
	    request.vars[f.name] = '|'.join(var)
	    del request.vars[inp['_id']+'[]']
	return wrapper

    resource = 'skill'
    tablename = module + '_' + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                person_id,
        Field('skill_types_id'),   
        Field('status',requires=IS_IN_SET(['approved','unapproved','denied']),label=T('status'), notnull=True, default='unapproved'),             
                    migrate=migrate)  
   
    db.vol_skill.skill_types_id.widget = multiselect_widget
    db.vol_skill.skill_types_id.requires = IS_ONE_OF(db, 'vol_skill_types.id', vol_skill_types_represent, multiple=True)
    #db.vol_skill.skill_types_id.represent = vol_skill_types_represent

    s3xrc.model.add_component(module, resource,
        multiple=True,
        joinby=dict(pr_person='person_id'),
        deletable=True,
        editable=True,
        main='person_id',
        )

    s3xrc.model.configure(table,
                          list_fields=['id',
                                       'skill_types_id',
                                       'status'])

    # CRUD Strings
    ADD_SKILL = T('Add Skill')
    SKILL = T('Skill')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SKILL,
        title_display = T('Skill Details'),
        title_list = SKILL,
        title_update = T('Edit Skill'),
        title_search = T('Search Skill'),
        subtitle_create = T('Add New Skill'),
        subtitle_list = SKILL,
        label_list_button = T('List Skill'),
        label_create_button = ADD_SKILL,
        msg_record_created = T('Skill added'),
        msg_record_modified = T('Skill updated'),
        msg_record_deleted = T('Skill deleted'),
        msg_list_empty = T('No skills currently set'))

# shn_pr_group_represent -----------------------------------------------------
#
def teamname(record):
    """
        Returns the Team Name
    """

    tname = ""
    if record and record.group_name:
        tname = "%s " % record.group_name.strip()
    return tname

def shn_pr_group_represent(id):

    def _represent(id):
        table = db.pr_group
        group = db(table.id == id).select(table.group_name)
        if group:
            return teamname(group[0])
        else:
            return None

    name = cache.ram("pr_group_%s" % id, lambda: _represent(id))
    return name
