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
    return dict(module_name=module_name)

#==============================================================================
def project():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    db.org_staff.person_id.comment[1] = DIV(DIV(_class="tooltip",
        _title=T("Person") + "|" + T("Select the person assigned to this role for this project.")))

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
    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)
        project_activity = r.record
        rheader = DIV( TABLE(
                           TR( TH( T("Short Description") + ": "), 
                               project_activity.name,
                              ),
                           TR( TH( T("Location") + ": "), 
                               shn_gis_location_represent(project_activity.location_id),
                               TH( T("Duration") + ": "),
                               "%s to %s" % (project_activity.start_date, project_activity.end_date),
                              ),                                      
                           TR( TH( T("Organisation") + ": "),
                               shn_organisation_represent(project_activity.organisation_id),                                       
                               TH( T("Cluster") + ": "),
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
            (T("Details"), None),
            (T("Requests"), "req"),
            #(T("Shipments To"), "rms_req"),
           ]
    rheader = lambda r: shn_activity_rheader(r, tabs)
    
    #Default values (from gap_report) set for fields 
    default_fieldnames = ["location_id", "cluster_id"]
    for fieldname in default_fieldnames:
        if fieldname in request.vars:
            table[fieldname].default = request.vars[fieldname]
            table[fieldname].writable = False

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
    assess_rows = db((db.assess_summary.id > 0) &\
                     (db.assess_summary.assess_id == db.assess_assess.id) &\
                     (db.assess_assess.location_id > 0) &\
                     (db.assess_assess.deleted != True)
                     ).select(db.assess_assess.id,
                              db.assess_assess.location_id,
                              db.assess_assess.datetime,
                              db.assess_summary.cluster_id,
                              db.assess_summary.value
                              )

    activity_rows = db((db.project_activity.id > 0) &\
                       (db.project_activity.location_id > 0) &\
                       (db.project_activity.deleted != True)
                       ).select(db.project_activity.id,
                                db.project_activity.location_id,
                                db.project_activity.cluster_id,
                                db.project_activity.organisation_id,
                                db.project_activity.total_bnf,
                                db.project_activity.start_date,
                                db.project_activity.end_date
                                )

    def map_assess_to_gap(row):
        return Storage( assess_id = row.assess_assess.id,
                        location_id = row.assess_assess.location_id,
                        cluster_id = row.assess_summary.cluster_id,
                        datetime = row.assess_assess.datetime,
                        assess_value = row.assess_summary.value,
                        activity_id = None,
                        organisation_id = None,
                        start_date = NONE,
                        end_date = NONE,
                        total_bnf = NONE,
                        )

    gap_rows = map(map_assess_to_gap, assess_rows)

    for activity_row in activity_rows:
        add_new_gap_row = True
        # Check if there is an Assessment of this location & cluster_subsector_id
        for gap_row in gap_rows:
            if activity_row.location_id == gap_row.location_id and \
               activity_row.cluster_id == gap_row.cluster_id:

                add_new_gap_row = False

                gap_row.activity_id = activity_row.id,
                gap_row.organisation_id = activity_row.organisation_id
                gap_row.start_date = activity_row.start_date
                gap_row.end_date = activity_row.end_date
                gap_row.total_bnf = activity_row.total_bnf
                break

        if add_new_gap_row:
            gap_rows.append(Storage(location_id = activity_row.location_id,
                                    cluster_id = activity_row.cluster_id,
                                    activity_id = activity_row.id,
                                    organisation_id = activity_row.organisation_id,
                                    start_date = activity_row.start_date,
                                    end_date = activity_row.end_date,
                                    total_bnf = activity_row.total_bnf,
                                    )
                            )

    headings = ("Date",
                "Location",
                "Clusters",
                "Assessment",
                "Severity",
                "Activity",
                "Organisation",
                "Start Date",
                "End Date",
                "Total Beneficiaries"
                )
    gap_table = TABLE(THEAD(TR(*[TH(header) for header in headings])),
                      _id = "list",
                      _class = "display"
                      )

    for gap_row in gap_rows:
        if gap_row.assess_id:
            assess_action_btn = A(T("Assessment"),
                                  _href = URL(r=request,
                                              c="assess",
                                              f="assess",
                                              args = (gap_row.assess_id, "impact")
                                              ),
                                  _target = "blank",
                                  _id = "show-add-btn",
                                  _class="action-btn"
                                  )
        else:
            assess_action_btn = NONE

        if gap_row.activity_id:
            activity_action_btn =A(T("Activity"),
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
                                                       "cluster_id":gap_row.cluster_id,
                                                       }
                                               ),
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),
            
            
        #Displaying NONE
        if gap_row.datetime:
            datetime = gap_row.datetime
        else:
            datetime = NONE
                    
        if gap_row.start_date:
            start_date = gap_row.start_date
        else:
            start_date = NONE

        if gap_row.end_date:
            end_date = gap_row.end_date
        else:
            end_date = NONE

        if gap_row.total_bnf:
            total_bnf = gap_row.total_bnf
        else:
            total_bnf = NONE

        gap_table.append(TR( datetime, 
                             shn_gis_location_represent(gap_row.location_id),
                             shn_org_cluster_represent(gap_row.cluster_id),
                             assess_action_btn,
                             shn_assess_severity_represent(gap_row.assess_value),
                             activity_action_btn,
                             shn_organisation_represent(gap_row.organisation_id),
                             start_date,
                             end_date,
                             total_bnf,
                            )
                        )

    return dict(title = T("Gap Analysis Report"),
                subtitle = T("Assessments and Activities"),
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
    cluster_rows = db(db.org_cluster.id > 0).select()
    for cluster_rows in cluster_rows:
        cluster_id = cluster_rows.id
        cluster = shn_org_cluster_represent(cluster_id)

        #Add activity row
        activity_rows = db((db.project_activity.id > 0) &\
                           (db.project_activity.cluster_id == cluster_id) &\
                           (db.project_activity.location_id > 0) &\
                           (db.project_activity.deleted != True) &
                           (db.project_activity.location_id == db.gis_location.id)
                           ).select(db.project_activity.id,
                                    db.project_activity.location_id,
                                    db.project_activity.cluster_id,
                                    db.gis_location.uuid,
                                    db.gis_location.id,
                                    db.gis_location.name,
                                    db.gis_location.code,
                                    db.gis_location.lat,
                                    db.gis_location.lon,
                                    )
        if len(activity_rows):
            for i in range( 0 , len( activity_rows) ):
                # 'gis_location' is needed because the quiery isn't simple due to the count - this could be fixed in s3gis.py
                activity_rows[i].gis_location.shape = "circle"
                activity_rows[i].gis_location.size = 6
                activity_rows[i].gis_location.color = "#0000FF" #blue

            feature_queries.append({ "name": "%s: Activities" % cluster,
                                     "query": activity_rows,
                                     "active": False,
                                     "popup_url" : "#",
                                    })

        #Add assess layer
        assess_rows = db((db.assess_summary.id > 0) &\
                         (db.assess_summary.cluster_id == cluster_id) &\
                         (db.assess_summary.assess_id == db.assess_assess.id) &\
                         (db.assess_assess.location_id > 0) &\
                         (db.assess_assess.deleted != True) &
                         (db.assess_assess.location_id == db.gis_location.id)
                         ).select(db.assess_assess.id,
                                  db.assess_assess.location_id,
                                  db.assess_assess.datetime,
                                  db.assess_summary.cluster_id,
                                  db.assess_summary.value,
                                  db.gis_location.uuid,
                                  db.gis_location.id,
                                  db.gis_location.name,
                                  db.gis_location.code,
                                  db.gis_location.lat,
                                  db.gis_location.lon,
                                  )

        if len(assess_rows):
            for i in range( 0 , len( assess_rows) ):
                # 'gis_location' is needed because the quiery isn't simple due to the count - this could be fixed in s3gis.py
                assess_rows[i].gis_location.shape = "circle"
                assess_rows[i].gis_location.size = 4
                assess_rows[i].gis_location.color = \
                    assess_summary_colour_code[assess_rows[i].assess_summary.value]

            feature_queries.append({ "name": "%s: Assessments" % cluster,
                                     "query": assess_rows,
                                     "active": False,
                                     "popup_url" : "#",
                                    })

    map = gis.show_map(
                feature_queries = feature_queries,
                # Take defaults from Catalogue rather than hardcoding
                #wms_browser = {"name" : "Risk Maps",
                #               "url" : "http://preview.grid.unep.ch:8080/geoserver/ows?service=WMS&request=GetCapabilities"},
                #width               = 866,
                #lat                 = 1.9,
                #lon                 = -180,
                #zoom                = 2
                )

    return dict(map = map,
                title = T("Gap Analysis Map"),
                subtitle = T("Assessments and Activities") )


#==============================================================================
