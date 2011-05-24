# -*- coding: utf-8 -*-

""" Project

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25

    Project Management
"""

prefix = request.controller
resourcename = request.function

response.menu_options = [
    [T("Home"), False, URL(r=request, f="index")],
    [T("Gap Analysis"), False, URL(r=request, f="gap_report"),[
        [T("Report"), False, URL(r=request, f="gap_report")],
        [T("Map"), False, URL(r=request, f="gap_map")],
    ]],
    [T("Projects"), False, URL(r=request, f="project"),[
        [T("List"), False, URL(r=request, f="project")],
        [T("Add"), False, URL(r=request, f="project", args="create")],
        #[T("Search"), False, URL(r=request, f="organisation", args="search")]
    ]],
    [T("Activities"), False, URL(r=request, f="activity"),[
        [T("List"), False, URL(r=request, f="activity")],
        [T("Add"), False, URL(r=request, f="activity", args="create")],
        #[T("Search"), False, URL(r=request, f="project", args="search")]
    ]],
    [T("Tasks"), False, URL(r=request, f="task"),[
        [T("List"), False, URL(r=request, f="task")],
        [T("Add"), False, URL(r=request, f="task", args="create")],
        #[T("Search"), False, URL(r=request, f="office", args="search")]
    ]],
]

#==============================================================================
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name)

#==============================================================================
def need():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

#==============================================================================
def need_type():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

#==============================================================================
def project():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    db.org_staff.person_id.comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Person"),
                                                           T("Select the person assigned to this role for this project.")))

    rheader = lambda r: shn_project_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Staff"), "staff"),
                                                    (T("Tasks"), "task"),
                                                    #(T("Donors"), "organisation"),
                                                    #(T("Sites"), "site"),  # Ticket 195
                                                   ])

    return s3_rest_controller(prefix, resourcename, rheader=rheader)

#==============================================================================
# @ToDo: Create should be restricted to Admin
def activity_type():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    response.menu_options = org_menu

    s3xrc.model.configure(table, listadd=False)
    return s3_rest_controller(prefix, resourcename)

#==============================================================================
def shn_activity_rheader(r, tabs=[]):
    """ Resource Header for Activities"""

    if r.representation == "html":
        project_activity = r.record
        if project_activity:
            rheader_tabs = s3_rheader_tabs(r, tabs)
            rheader = DIV( TABLE(
                               TR( TH( "%s: " % T("Short Description")),
                                   project_activity.name,
                                  ),
                               TR( TH( "%s: " % T("Location")),
                                   shn_gis_location_represent(project_activity.location_id),
                                   TH( "%s: " % T("Duration")),
                                   "%s to %s" % (project_activity.start_date, project_activity.end_date),
                                  ),
                               TR( TH( "%s: " % T("Organization")),
                                   shn_organisation_represent(project_activity.organisation_id),
                                   TH( "%s: " % T("Sector")),
                                   shn_org_cluster_represent(project_activity.cluster_id),
                                 ),
                                ),
                            rheader_tabs
                            )
            return rheader
    return None
#==============================================================================
def activity():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    tabs = [
            #(T("Details"), None),
            #(T("Requests"), "req"),
            #(T("Shipments To"), "rms_req"),
           ]
    rheader = lambda r: shn_activity_rheader(r, tabs)

    if "create"  in request.args:
        #Default values (from gap_report) set for fields
        default_fieldnames = ["location_id", "need_type_id"]
        for fieldname in default_fieldnames:
            if fieldname in request.vars:
                table[fieldname].default = request.vars[fieldname]
                table[fieldname].writable = False
                table[fieldname].comment = None

    return s3_rest_controller(prefix,
                              resourcename,
                              rheader = rheader)

#==============================================================================
def task():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    return s3_rest_controller(prefix, resourcename)

#==============================================================================
def gap_report():

    """ Provide a Report on Gaps between Activities & Needs Assessments """

    #Get all assess_summary
    assess_need_rows = db((db.project_need.id > 0) &\
                          (db.project_need.assess_id == db.assess_assess.id) &\
                          (db.assess_assess.location_id > 0) &\
                          (db.assess_assess.deleted != True)
                          ).select(db.assess_assess.id,
                                   db.assess_assess.location_id,
                                   db.assess_assess.datetime,
                                   db.project_need.need_type_id,
                                   db.project_need.value
                                   )

    activity_rows = db((db.project_activity.id > 0) &\
                       (db.project_activity.location_id > 0) &\
                       (db.project_activity.deleted != True)
                       ).select(db.project_activity.id,
                                db.project_activity.location_id,
                                db.project_activity.need_type_id,
                                db.project_activity.organisation_id,
                                db.project_activity.total_bnf,
                                db.project_activity.start_date,
                                db.project_activity.end_date
                                )

    def map_assess_to_gap(row):
        return Storage( assess_id = row.assess_assess.id,
                        location_id = row.assess_assess.location_id,
                        datetime = row.assess_assess.datetime,
                        need_type_id = row.project_need.need_type_id,
                        value = row.project_need.value,
                        activity_id = None,
                        organisation_id = None,
                        start_date = NONE,
                        end_date = NONE,
                        total_bnf = NONE,
                        )

    gap_rows = map(map_assess_to_gap, assess_need_rows)

    for activity_row in activity_rows:
        add_new_gap_row = True
        # Check if there is an Assessment of this location & cluster_subsector_id
        for gap_row in gap_rows:
            if activity_row.location_id == gap_row.location_id and \
               activity_row.need_type_id == gap_row.need_type_id:

                add_new_gap_row = False

                gap_row.activity_id = activity_row.id,
                gap_row.organisation_id = activity_row.organisation_id
                gap_row.start_date = activity_row.start_date
                gap_row.end_date = activity_row.end_date
                gap_row.total_bnf = activity_row.total_bnf
                break

        if add_new_gap_row:
            gap_rows.append(Storage(location_id = activity_row.location_id,
                                    need_type_id = activity_row.need_type_id,
                                    activity_id = activity_row.id,
                                    organisation_id = activity_row.organisation_id,
                                    start_date = activity_row.start_date,
                                    end_date = activity_row.end_date,
                                    total_bnf = activity_row.total_bnf,
                                    )
                            )

    headings = ("Location",
                "Needs",
                "Assessment",
                "Date",
                "Activity",
                "Start Date",
                "End Date",
                "Total Beneficiaries",
                "Organization",
                "Gap (% Needs Met)",
                )
    gap_table = TABLE(THEAD(TR(*[TH(header) for header in headings])),
                      _id = "list",
                      _class = "dataTable display"
                      )

    for gap_row in gap_rows:
        if gap_row.assess_id:
            assess_action_btn = A(T("Open"),
                                  _href = URL(r=request,
                                              c="assess",
                                              f="assess",
                                              args = (gap_row.assess_id, "need")
                                              ),
                                  _target = "blank",
                                  _id = "show-add-btn",
                                  _class="action-btn"
                                  )
        else:
            assess_action_btn = NONE

        if gap_row.activity_id:
            activity_action_btn =A(T("Open"),
                                   _href = URL(r=request,
                                               c="project",
                                               f="activity",
                                               args = (gap_row.activity_id)
                                               ),
                                   _target = "blank",
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),
        else:
            activity_action_btn = A(T("Add"),
                                   _href = URL(r=request,
                                               c="project",
                                               f="activity",
                                               args = ("create"),
                                               vars = {"location_id":gap_row.location_id,
                                                       "need_type_id":gap_row.need_type_id,
                                                       }
                                               ),
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),

        need_str = shn_need_type_represent(gap_row.need_type_id)
        if gap_row.value:
            need_str = "%d %s" % (gap_row.value, need_str)

        #Calculate the Gap
        if not gap_row.value:
            gap_str = NONE
        elif gap_row.total_bnf and gap_row.total_bnf != NONE:
            gap_str = "%d%%" % min((gap_row.total_bnf / gap_row.value) * 100, 100)
        else:
            gap_str = "0%"

        gap_table.append(TR( shn_gis_location_represent(gap_row.location_id),
                             need_str,
                             assess_action_btn,
                             gap_row.datetime or NONE,
                             activity_action_btn,
                             gap_row.start_date or NONE,
                             gap_row.end_date or NONE,
                             gap_row.total_bnf or NONE,
                             shn_organisation_represent(gap_row.organisation_id),
                             gap_str
                            )
                        )

    return dict(title = T("Gap Analysis Report"),
                subtitle = T("Assessments Needs vs. Activities"),
                gap_table = gap_table,
                )

#==============================================================================
def gap_map():
    """ @todo: fix docstring """

    assess_summary_colour_code = {0:"#008000", #green
                                  1:"#FFFF00", #yellow
                                  2:"#FFA500", #orange
                                  3:"#FF0000", #red
                                  }

    feature_queries = []
    need_type_rows = db(db.project_need_type.id > 0).select()
    for need_type_rows in need_type_rows:

        layer_rows = []

        need_type_id = need_type_rows.id
        need_type = shn_need_type_represent(need_type_id)

        #Add activity row
        activity_rows = db((db.project_activity.id > 0) &\
                           (db.project_activity.need_type_id == need_type_id) &\
                           (db.project_activity.location_id > 0) &\
                           (db.project_activity.deleted != True) &
                           (db.project_activity.location_id == db.gis_location.id)
                           ).select(db.project_activity.id,
                                    db.project_activity.location_id,
                                    #db.project_activity.need_type_id,
                                    db.gis_location.uuid,
                                    db.gis_location.id,
                                    db.gis_location.name,
                                    db.gis_location.code,
                                    db.gis_location.lat,
                                    db.gis_location.lon,
                                    )
        if len(activity_rows):
            for i in range( 0 , len( activity_rows) ):
                #layer_rows.append(Storage(gis_location =
                #                      Storage(uuid = activity_rows[i].gis_location.uuid,
                #                              id = activity_rows[i].gis_location.id,
                #                              name = activity_rows[i].gis_location.name,
                #                              lat = activity_rows[i].gis_location.lat,
                #                              lon = activity_rows[i].gis_location.lon,
                #                              shape = "circle",
                #                              size = 6,
                #                              color = "#0000FF", #blue
                #                              )
                #                          )
                #                  )
                activity_rows[i].gis_location.shape = "circle"
                activity_rows[i].gis_location.size = 6
                activity_rows[i].gis_location.color = "#0000FF" #blue
            feature_queries.append({ "name": "%s: Activities" % need_type,
                                     "query": activity_rows,
                                     "active": False,
                                     "popup_url" : "#",
                                    })

#Add assess layer
        assess_need_rows = db((db.project_need.id > 0) &\
                              (db.project_need.need_type_id == need_type_id) &\
                              (db.project_need.assess_id == db.assess_assess.id) &\
                              (db.assess_assess.location_id > 0) &\
                              (db.assess_assess.deleted != True) &
                              (db.assess_assess.location_id == db.gis_location.id)
                              ).select(db.assess_assess.id,
                                       db.assess_assess.location_id,
                                       db.assess_assess.datetime,
                                       #db.project_need.need_type_id,
                                       #db.project_need.value,
                                       db.gis_location.uuid,
                                       db.gis_location.id,
                                       db.gis_location.name,
                                       db.gis_location.code,
                                       db.gis_location.lat,
                                       db.gis_location.lon,
                                       )

        if len(assess_need_rows):
            for i in range( 0 , len( assess_need_rows) ):
                #layer_rows.append(dict(gis_location =
                #                      dict(uuid = assess_need_rows[i].gis_location.uuid,
                #                              id = assess_need_rows[i].gis_location.id,
                #                              name = assess_need_rows[i].gis_location.name,
                #                              lat = assess_need_rows[i].gis_location.lat,
                #                              lon = assess_need_rows[i].gis_location.lon,
                #                              shape = "circle",
                #                              size = 4,
                #                              color = assess_summary_colour_code[3]
                #                              )
                #                          )
                #                  )
                assess_need_rows[i].gis_location.shape = "circle"
                assess_need_rows[i].gis_location.size = 4
                assess_need_rows[i].gis_location.color = assess_summary_colour_code[3]
                    #assess_summary_colour_code[assess_need_rows[i].assess_summary.value]
            feature_queries.append({ "name": "%s: Assessments" % need_type,
                                     "query": assess_need_rows,
                                     "active": False,
                                     "popup_url" : "#",
                                    })

    map = gis.show_map(
                feature_queries = feature_queries,
                )

    return dict(map = map,
                title = T("Gap Analysis Map"),
                subtitle = T("Assessments and Activities") )
