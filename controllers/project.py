# -*- coding: utf-8 -*-

"""
    Project 
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25    
    
    Project Management
"""

module = request.controller

# Not wanted in Gap, just Activities
#response.menu_options = org_menu

#==============================================================================
# @ToDo: Create should be restricted to Admin
def activity_type():
    "RESTful CRUD controller"
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    response.menu_options = org_menu

    return shn_rest_controller(module, resourcename, listadd=False)

#==============================================================================
def activity():
    "RESTful CRUD controller"
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    response.menu_options = org_menu

    return shn_rest_controller(module, resourcename)

#==============================================================================
def gap():
    
    #Get all assess_summary
    assess_rows = db((db.assess_summary.id > 0) &\
                     (db.assess_summary.assess_id == db.assess_assess.id) &\
                     (db.assess_assess.location_id > 0) &\
                     (db.assess_assess.deleted != True)
                     ).select(db.assess_assess.id,
                              db.assess_assess.location_id,
                              db.assess_assess.datetime,
                              db.assess_summary.cluster_subsector_id,                              
                              db.assess_summary.value
                              )
    
    activity_rows = db((db.project_activity.id > 0) &\
                       (db.project_activity.location_id > 0) &\
                       (db.project_activity.deleted != True)
                       ).select(db.project_activity.id,
                                db.project_activity.location_id,
                                db.project_activity.cluster_subsector_id,
                                db.project_activity.organisation_id,
                                db.project_activity.total_bnf_reach,
                                db.project_activity.start_date,
                                db.project_activity.end_date
                                )
                       
    def map_gap(row):
        return Storage( assess_id = row.assess_assess.id,
                        location_id = row.assess_assess.location_id,
                        cluster_subsector_id = row.assess_summary.cluster_subsector_id,
                        datetime = row.assess_assess.datetime,
                        assess_value = row.assess_summary.value,
                        activity_id = None,
                        organisation_id = None,
                        start_date = NONE,
                        end_date = NONE,
                        total_bnf_reach = NONE,
                        )
        
    gap_rows = map(map_gap, assess_rows)
    
    for activity_row in activity_rows:
        add_new_gap_row = True
        #check if there is an assess of this location & cluster_subsector_id
        for gap_row in gap_rows:
            if activity_row.location_id == gap_row.location_id and \
               activity_row.cluster_subsector_id == gap_row.cluster_subsector_id:
                
                add_new_gap_row = False
                
                gap_row.activity_id = activity_row.id,
                gap_row.organisation_id = activity_row.organisation_id
                gap_row.start_date = activity_row.start_date
                gap_row.end_date = activity_row.end_date
                gap_row.total_bnf_reach = activity_row.total_bnf_reach
                break
        
        if add_new_gap_row:
            gap_rows.append(Storage(location_id = activity_row.location_id,
                                    cluster_subsector_id = activity_row.cluster_subsector_id,
                                    activity_id = activity_row.id,
                                    organisation_id = activity_row.organisation_id,
                                    start_date = activity_row.start_date,
                                    end_date = activity_row.end_date,
                                    total_bnf_reach = activity_row.total_bnf_reach,
                                    )
                            )
            
    headings = ("Location",
                "Cluster Subsector",
                "Assessment",
                "Severity",
                "Activity",
                "Organisation",
                "Start Date",
                "End Date",
                "# Beneficiaries"
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
                                              args = (gap_row.assess_id, "summary")
                                              ),
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
                                   _id = "show-add-btn",
                                   _class="action-btn"
                                   ),   
        else:
            activity_action_btn = NONE
            
        if gap_row.start_date:
            start_date = gap_row.start_date
        else:
            start_date = NONE
            
        if gap_row.end_date:
            end_date = gap_row.end_date
        else:
            end_date = NONE
            
        if gap_row.total_bnf_reach:
            total_bnf_reach = gap_row.total_bnf_reach
        else:
            total_bnf_reach = NONE
                   
        gap_table.append(TR( shn_gis_location_represent(gap_row.location_id),
                             shn_org_cluster_subsector_represent(gap_row.cluster_subsector_id),
                             assess_action_btn,
                             shn_assess_summary_value_represent(gap_row.assess_value),
                             activity_action_btn,
                             shn_organisation_represent(gap_row.organisation_id),
                             start_date,
                             end_date,
                             total_bnf_reach,
                            )
                        )        
                       
    return dict(title = T("Gap Analysis"),                 
                gap_table = gap_table)
    
#==============================================================================
def gap_map():
    feature_queries = []
    cluster_subsector_rows = db(db.org_cluster_subsector.id > 0).select()
    for cluster_subsector_rows in cluster_subsector_rows:
        cluster_subsector_id = cluster_subsector_rows.id
        cluster_subsector = shn_org_cluster_subsector_represent(cluster_subsector_id)
        
        #Add activity row
        activity_rows = db((db.project_activity.id > 0) &\
                           (db.project_activity.cluster_subsector_id == cluster_subsector_id) &\
                           (db.project_activity.location_id > 0) &\
                           (db.project_activity.deleted != True) &
                           (db.project_activity.location_id == db.gis_location.id)
                           ).select(db.project_activity.id,
                                    db.project_activity.location_id,
                                    db.project_activity.cluster_subsector_id,
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
                
            feature_queries.append({ "name": "Activities - %s" % cluster_subsector,
                                     "query": activity_rows,
                                     "active": False,
                                     "popup_url" : "#",
                                    })                          
        
        #Add assess layer
        assess_rows = db((db.assess_summary.id > 0) &\
                         (db.assess_summary.cluster_subsector_id == cluster_subsector_id) &\
                         (db.assess_summary.assess_id == db.assess_assess.id) &\
                         (db.assess_assess.location_id > 0) &\
                         (db.assess_assess.deleted != True) &
                         (db.assess_assess.location_id == db.gis_location.id)
                         ).select(db.assess_assess.id,
                                  db.assess_assess.location_id,
                                  db.assess_assess.datetime,
                                  db.assess_summary.cluster_subsector_id,                              
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
                if assess_rows[i].assess_summary.value == 0:
                    assess_rows[i].gis_location.color = "#008000" #green 
                elif assess_rows[i].assess_summary.value == 1:
                    assess_rows[i].gis_location.color = "#FFFF00" #yellow
                elif assess_rows[i].assess_summary.value == 2:
                    assess_rows[i].gis_location.color = "#FFA500" #orange
                elif assess_rows[i].assess_summary.value == 3:
                    assess_rows[i].gis_location.color = "#FF0000" #red  

            feature_queries.append({ "name": "Assessments - %s" % cluster_subsector,
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
                title = T("Assessment and Activities Map") )
#==============================================================================