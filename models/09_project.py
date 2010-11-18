# -*- coding: utf-8 -*-

"""
    Project

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25

    Project Tracking
    
    project_project and project_task moved from 05_org.py
"""

application = "project"
if deployment_settings.has_module("project"):
    #==============================================================================
    # Need Type
    # Component of assses_assess too
    resourcename = "need_type"
    tablename = "%s_%s" % (application, resourcename)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            cluster_id(),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    # CRUD strings
    ADD_BASELINE_TYPE = T("Add Need Type")
    LIST_BASELINE_TYPE = T("List Need Types")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_BASELINE_TYPE,
        title_display = T("Need Type Details"),
        title_list = LIST_BASELINE_TYPE,
        title_update = T("Edit Need Type"),
        title_search = T("Search Need Type"),
        subtitle_create = T("Add New Need Type"),
        subtitle_list = T("Need Types"),
        label_list_button = LIST_BASELINE_TYPE,
        label_create_button = ADD_BASELINE_TYPE,
        label_delete_button = T("Delete Need Type"),
        msg_record_created = T("Need Type added"),
        msg_record_modified = T("Need Type updated"),
        msg_record_deleted = T("Need Type deleted"),
        msg_list_empty = T("No Need Types currently registered"))  
    
    def need_type_comment():
        if auth.has_membership(auth.id_group("'Administrator'")):
            return DIV(A(ADD_BASELINE_TYPE,
                         _class="colorbox",
                         _href=URL(r=request, c="assess", f="need_type", args="create", vars=dict(format="popup")),
                         _target="top",
                         _title=ADD_BASELINE_TYPE
                         )
                       )
        else:
            return None    

    need_type_id = S3ReusableField("need_type_id", db.project_need_type, sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "project_need_type.id","%(name)s", sort=True)),
                                       represent = lambda id: shn_get_db_field_value(db = db,
                                                                                     table = "project_need_type",
                                                                                     field = "name",
                                                                                     look_up = id),
                                       label = T("Need Type"),
                                       comment = need_type_comment(),
                                       ondelete = "RESTRICT"
                                       ) 
    
    def shn_need_type_represent(id):
        return shn_get_db_field_value(db = db,
                                      table = "project_need_type",
                                      field = "name",
                                      look_up = id)   
         
    #This should be moved to zz_1st_run / CSV 
    if not db(table.id > 0).count():
        table.insert( name = T("People Needing Food") )
        table.insert( name = T("People Needing Water") )
        table.insert( name = T("People Needing Shelter") )
    
    #==============================================================================
    # Need
    resourcename = "need"
    tablename = "%s_%s" % (application, resourcename)
    table = db.define_table(tablename,
                            assess_id(),
                            need_type_id(),
                            Field("value", "double"),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    # Hide FK fields in forms
    table.assess_id.readable = table.assess_id.writable = False    
    
    table.value.label = "#"
    table.value.represent = lambda value: "%d" % value
    
    # CRUD strings
    ADD_BASELINE = T("Add Need")
    LIST_BASELINE = T("List Needs")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_BASELINE,
        title_display = T("Needs Details"),
        title_list = LIST_BASELINE,
        title_update = T("Edit Need"),
        title_search = T("Search Needs"),
        subtitle_create = T("Add New Need"),
        subtitle_list = T("Needs"),
        label_list_button = LIST_BASELINE,
        label_create_button = ADD_BASELINE,
        label_delete_button = T("Delete Need"),
        msg_record_created = T("Need added"),
        msg_record_modified = T("Need updated"),
        msg_record_deleted = T("Need deleted"),
        msg_list_empty = T("No Needs currently registered"))     
    
    # Need as component of assessments
    s3xrc.model.add_component(application, resourcename,
                              multiple=True,
                              joinby=dict(assess_assess="assess_id"),
                              deletable=True,
                              editable=True)      
        
    #==============================================================================
    # Projects:
    #   the projects which each organization is engaged in
    #
    project_project_status_opts = {
        1: T("active"),
        2: T("completed"),
        99: T("inactive")
        }
    resourcename = "project"
    tablename = application + "_" + resourcename
    table = db.define_table(tablename,
                            Field("code"),
                            Field("name"),
                            organisation_id(),
                            location_id(),
                            cluster_id(),
                            Field("status", "integer",
                                    requires = IS_IN_SET(project_project_status_opts, zero=None),
                                    # default = 99,
                                    label = T("Project Status"),
                                    represent = lambda opt: project_project_status_opts.get(opt, UNKNOWN_OPT)),
                            Field("description", "text"),
                            Field("beneficiaries", "integer"), #@todo: change this field name to total_bnf
                            Field("start_date", "date"),
                            Field("end_date", "date"),
                            Field("funded", "boolean"),
                            donor_id(),
                            Field("budgeted_cost", "double"),
                            migrate=migrate, *s3_meta_fields())
    
    #@todo: Fix the widget for this before displaying - should donor  be component?
    table.donor_id.readable = table.donor_id.writable = False
    
    # Field settings
    table.code.requires = [IS_NOT_EMPTY(error_message=T("Please fill this!")),
                             IS_NOT_IN_DB(db, "project_project.code")]
    table.start_date.requires = IS_NULL_OR(IS_DATE())
    table.end_date.requires = IS_NULL_OR(IS_DATE())
    table.budgeted_cost.requires = IS_NULL_OR(IS_FLOAT_IN_RANGE(0, 999999999))
    
    # Project Resource called from multiple controllers
    # - so we define strings in the model
    table.code.label = T("Code")
    table.name.label = T("Title")
    table.start_date.label = T("Start date")
    table.end_date.label = T("End date")
    table.description.label = T("Description")
    table.beneficiaries.label = T("Total Beneficiaries")
    
    table.status.label = T("Status")
    
    ADD_PROJECT = T("Add Project")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_PROJECT,
        title_display = T("Project Details"),
        title_list = T("List Projects"),
        title_update = T("Edit Project"),
        title_search = T("Search Projects"),
        subtitle_create = T("Add New Project"),
        subtitle_list = T("Projects"),
        label_list_button = T("List Projects"),
        label_create_button = ADD_PROJECT,
        label_delete_button = T("Delete Project"),
        msg_record_created = T("Project added"),
        msg_record_modified = T("Project updated"),
        msg_record_deleted = T("Project deleted"),
        msg_list_empty = T("No Projects currently registered"))
    
    # Reusable field
    project_id = S3ReusableField("project_id", db.project_project, sortby="name",
                            requires = IS_NULL_OR(IS_ONE_OF(db, "project_project.id", "%(code)s")),
                            represent = lambda id: (id and [db.project_project[id].code] or [NONE])[0],
                            comment = DIV(A(ADD_PROJECT, _class="colorbox", _href=URL(r=request, c="org", f="project", args="create", vars=dict(format="popup")), _target="top", _title=ADD_PROJECT),
                                      DIV( _class="tooltip", _title=ADD_PROJECT + "|" + T("Add new project."))),
                            label = "Project",
                            ondelete = "RESTRICT"
                            )
    
    # Projects as component of Orgs & Locations
    s3xrc.model.add_component(application, resourcename,
                              multiple=True,
                              #joinby=dict(project_organisation="organisation_id", gis_location="location_id"),
                              joinby=dict(org_organisation="organisation_id"))
    
    s3xrc.model.configure(table,
                          #listadd=False,
                          main="code",
                          list_fields=["id",
                                       "organisation_id",
                                       "location_id",
                                       "cluster_id",
                                       "code",
                                       "name",
                                       "status",
                                       "start_date",
                                       "end_date",
                                       "budgeted_cost"])  
    
    # -----------------------------------------------------------------------------
    # shn_project_search_location:
    #   form function to search projects by location
    #
    def shn_project_search_location(xrequest, **attr):
    
        if attr is None:
            attr = {}
    
        if not shn_has_permission("read", db.project_project):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_location", vars=request.vars)}))
    
        if xrequest.representation == "html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = URL(r=request, c="org", f="project", args="[id]")
    
            # Custom view
            response.view = "%s/project_search.html" % xrequest.prefix
    
            # Title and subtitle
            title = T("Search for a Project")
            subtitle = T("Matching Records")
    
            # Select form:
            l_opts = [OPTION(_value="")]
            l_opts += [OPTION(location.name, _value=location.id)
                    for location in db(db.gis_location.deleted == False).select(db.gis_location.ALL, cache=(cache.ram, 3600))]
            form = FORM(TABLE(
                    TR(T("Location: "),
                    SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db, "gis_location.id"))))),
                    TR("", INPUT(_type="submit", _value=T("Search")))
                    ))
    
            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)
    
            # Accept action
            items = None
            if form.accepts(request.vars, session):
    
                table = db.project_project
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
                            result.start_date or NONE,
                            result.end_date or NONE,
                            result.description or NONE,
                            result.status and project_project_status_opts[result.status] or "unknown",
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("ID"),
                        TH("Organization"),
                        TH("Location"),
                        TH("Sector(s)"),
                        TH("Code"),
                        TH("Name"),
                        TH("Status"),
                        TH("Start date"),
                        TH("End date"),
                        TH("Budgeted Cost"))),
                        TBODY(records), _id="list", _class="display"))
                else:
                        items = T(NONE)
    
            try:
                label_create_button = s3.crud_strings["project_project"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button
    
            add_btn = A(label_create_button, _href=URL(r=request, f="project", args="create"), _class="action-btn")
    
            output.update(dict(items=items, add_btn=add_btn))
    
            return output
    
        else:
            session.error = BADFORMAT
            redirect(URL(r=request))
    
    # Plug into REST controller
    s3xrc.model.set_method(application, "project", method="search_location", action=shn_project_search_location )
    
    # -----------------------------------------------------------------------------
    def shn_project_rheader(jr, tabs=[]):
    
        if jr.representation == "html":
    
            rheader_tabs = shn_rheader_tabs(jr, tabs)
    
            if jr.name == "project":
    
                _next = jr.here()
                _same = jr.same()
    
                project = jr.record
    
                sectors = TABLE()
                if project.cluster_id:
                    # @ToDo@ Fix for list: type
                    _sectors = re.split("\|", project.cluster_id)[1:-1]
                    for sector in _sectors:
                        sectors.append(TR(db(db.org_cluster.id == sector).select(db.org_cluster.name, limitby=(0, 1)).first().name))
    
                if project:
                    rheader = DIV(TABLE(
                        TR(
                            TH(T("Code") + ": "),
                            project.code,
                            TH(A(T("Clear Selection"),
                                _href=URL(r=request, f="project", args="clear", vars={"_next": _same})))
                            ),
                        TR(
                            TH(T("Name") + ": "),
                            project.name,
                            TH(T("Location") + ": "),
                            location_id.location_id.represent(project.location_id),
                            ),
                        TR(
                            TH(T("Status") + ": "),
                            "%s" % project_project_status_opts[project.status],
                            TH(T("Cluster(s)") + ": "),
                            sectors,
                            #TH(A(T("Edit Project"),
                            #    _href=URL(r=request, f="project", args=[jr.id, "update"], vars={"_next": _next})))
                            )
                    ), rheader_tabs)
                    return rheader
    
        return None      
    
    #==============================================================================
    # Activity Type
    # Redundant???
    resourcename = "activity_type"
    tablename = "%s_%s" % (application, resourcename)
    table = db.define_table(tablename,
                            Field("name", length=128, notnull=True, unique=True),
                            migrate=migrate, *s3_meta_fields())


    ADD_ACTIVITY_TYPE = T("Add Activity Type")
    
    def activity_type_comment():
        if auth.has_membership(auth.id_group(1)):
            return DIV(A(ADD_ACTIVITY_TYPE,
                         _class="colorbox",
                         _href=URL(r=request, c="project", f="activity_type", args="create", vars=dict(format="popup")),
                         _target="top",
                         _title=ADD_ACTIVITY_TYPE
                         )
                       )
        else:
            return None    

    activity_type_id = S3ReusableField("activity_type_id", db.project_activity_type, sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "project_activity_type.id","%(name)s", sort=True)),
                                       represent = lambda id: shn_get_db_field_value(db = db,
                                                                                     table = "project_activity_type",
                                                                                     field = "name",
                                                                                     look_up = id),
                                       label = T("Activity Type"),
                                       comment = activity_type_comment(),
                                       ondelete = "RESTRICT"
                                       )

    #==============================================================================
    # Activity
    #
    opt_bnf_type = { 1: T("Individuals"),
                     2: T("Families/HH")
                   }

    resourcename = "activity"
    tablename = "%s_%s" % (application, resourcename)
    table = db.define_table(tablename,
                            Field("name"),
                            organisation_id("donor_id",
                                            label = T("Funding Organization"),
                                            comment = DIV(A(ADD_ORGANIZATION,
                                                            _class="colorbox",
                                                            _href=organisation_popup_url,
                                                            _target="top",
                                                            _title=ADD_ORGANIZATION),
                                                          DIV(DIV(_class="tooltip",
                                                                  _title=ADD_ORGANIZATION + "|" + T("The Organization which is funding this Activity."))))
                                           ),
                            organisation_id(),
                            cluster_id(),
                            need_type_id(),
                            #cluster_subsector_id(),
                            #Field("quantity"),
                            #Field("unit"), # Change to link to supply
                            Field("start_date","date"),
                            Field("end_date","date"),
                            location_id(),
                            #shelter_id(),
                            Field("total_bnf","integer"),
                            #Field("bnf_type","integer"),
                            #Field("bnf_date","date"),
                            #Field("total_bnf_target","integer"),
                            #Field("male","integer"),
                            #Field("female","integer"),
                            #Field("child_2","integer"),
                            #Field("child_5","integer"),
                            #Field("child_15","integer"),
                            #Field("cba_women","integer"),
                            #Field("pl_women","integer"),
                            person_id(),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    table.name.label = T("Short Description")
    table.total_bnf.label = T("Total Beneficiaries")
    #table.bnf_type.label = T("Beneficiary Type")
    #table.bnf_date.label = T("Date of Latest Information on Beneficiaries Reached")
    #table.total_bnf_target.label = T("Total # of Target Beneficiaries")
    #table.child_2.label = T("Children (< 2 years)")
    #table.child_5.label = T("Children (2-5 years)")
    #table.child_15.label = T("Children (5-15 years)")
    #table.cba_women.label = T("CBA Women")
    #table.cba_women.comment = DIV( _class="tooltip", _title= T("Women of Child Bearing Age"))
    #table.pl_women.label = T("PL Women")
    #table.pl_women.comment = DIV( _class="tooltip", _title= T("Women who are Pregnant or in Labour"))

    table.person_id.label = T("Contact Person")

    #table.comments.comment = T("(Constraints Only)")

    for field in table:
        if field.type == "integer":
            field.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )

    #table.bnf_type.requires = IS_NULL_OR(IS_IN_SET(opt_bnf_type))
    #table.bnf_type.represent = lambda opt: opt_bnf_type.get(opt, NONE)

    # CRUD Strings
    ADD_ACTIVITY = T("Add Activity")
    LIST_ACTIVITIES = T("List Activities")
    s3.crud_strings[tablename] = Storage(title_create = ADD_ACTIVITY,
                                         title_display = T("Activity Details"),
                                         title_list = LIST_ACTIVITIES,
                                         title_update = T("Edit Activity"),
                                         title_search = T("Search Activities"),
                                         subtitle_create = T("Add New Activity"),
                                         subtitle_list = T("Activities"),
                                         label_list_button = LIST_ACTIVITIES,
                                         label_create_button = ADD_ACTIVITY,
                                         msg_record_created = T("Activity Added"),
                                         msg_record_modified = T("Activity Updated"),
                                         msg_record_deleted = T("Activity Deleted"),
                                         msg_list_empty = T("No Activities Found")
                                         )

    activity_id = S3ReusableField( "activity_id", db.project_activity, sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "project_activity.id","%(name)s", sort=True)),
                                   represent = lambda id: shn_get_db_field_value(db = db,
                                                                                 table = "project_activity",
                                                                                 field = "name",
                                                                                 look_up = id),
                                   label = T("Activity"),
                                   comment = DIV(A(ADD_ACTIVITY,
                                                   _class="colorbox",
                                                   _href=URL(r=request, c="project", f="activity", args="create", vars=dict(format="popup")),
                                                   _target="top",
                                                   _title=ADD_ACTIVITY
                                                   )
                                                 ),
                                   ondelete = "RESTRICT"
                                   )    
    
    # Activities as component of Orgs
    s3xrc.model.add_component(application, resourcename,
                              multiple=True,
                              joinby=dict(org_organisation="organisation_id"))
    
    #==============================================================================
    # project_task:
    #   a task within a project/activity
    #
    project_task_status_opts = {
        1: T("new"),
        2: T("assigned"),
        3: T("completed"),
        4: T("postponed"),
        5: T("feedback"),
        6: T("cancelled"),
        99: T("unspecified")
    }
    
    project_task_priority_opts = {
        4: T("normal"),
        1: T("immediately"),
        2: T("urgent"),
        3: T("high"),
        5: T("low")
    }
    
    resourcename = "task"
    tablename = application + "_" + resourcename
    table = db.define_table(tablename,
                            Field("priority", "integer",
                                requires = IS_IN_SET(project_task_priority_opts, zero=None),
                                # default = 4,
                                label = T("Priority"),
                                represent = lambda opt: project_task_priority_opts.get(opt, UNKNOWN_OPT)),
                            Field("subject", length=80, notnull=True),
                            Field("description", "text"),
                            project_id(),
                            office_id(),
                            person_id(),
                            Field("status", "integer",
                                requires = IS_IN_SET(project_task_status_opts, zero=None),
                                # default = 1,
                                label = T("Status"),
                                represent = lambda opt: project_task_status_opts.get(opt, UNKNOWN_OPT)),
                            migrate=migrate, *s3_meta_fields())
    
    
    # Task Resource called from multiple controllers
    # - so we define strings in the model
    table.subject.requires = IS_NOT_EMPTY()
    table.subject.label = T("Subject")
    
    table.person_id.label = T("Assigned to")
    
    
    def shn_project_task_onvalidation(form):
    
        """ Task form validation """
    
        if str(form.vars.status) == "2" and not form.vars.person_id:
            form.errors.person_id = T("Select a person in charge for status 'assigned'")
    
        return False
    
    
    # CRUD Strings
    ADD_TASK = T("Add Task")
    LIST_TASKS = T("List Tasks")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TASK,
        title_display = T("Task Details"),
        title_list = LIST_TASKS,
        title_update = T("Edit Task"),
        title_search = T("Search Tasks"),
        subtitle_create = T("Add New Task"),
        subtitle_list = T("Tasks"),
        label_list_button = LIST_TASKS,
        label_create_button = ADD_TASK,
        msg_record_created = T("Task added"),
        msg_record_modified = T("Task updated"),
        msg_record_deleted = T("Task deleted"),
        msg_list_empty = T("No tasks currently registered"))
    
    # Task as Component of Project, Office, (Organisation to come? via Project? Can't rely on that as multi-Org projects)
    s3xrc.model.add_component(application, resourcename,
                              multiple=True,
                              joinby=dict(project_project="project_id",
                                          project_office="office_id"))
    
    s3xrc.model.configure(table,
                          listadd=False,
                          onvalidation = lambda form: shn_project_task_onvalidation(form),
                          list_fields=["id",
                                       "project_id",
                                       "office_id",
                                       "priority",
                                       "subject",
                                       "person_id",
                                       "status"],
                          main="subject", extra="description")    

