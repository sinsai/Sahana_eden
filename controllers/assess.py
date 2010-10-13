# -*- coding: utf-8 -*-

"""
    Assessment - COntroller
    
    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-25    
    
"""

module = request.controller

#==============================================================================
def shn_assess_rheader(jr, tabs=[]):
    if jr.representation == "html":
        rheader_tabs = shn_rheader_tabs(jr, tabs)
        assess = jr.record        
        rheader = DIV(TABLE(TR(
                               TH(T("Date & Time") + ": "), assess.datetime,
                               TH(T("Location") + ": "), shn_gis_location_represent(assess.location_id),
                               TH(T("Assessor") + ": "), shn_pr_person_represent(assess.assessor_person_id),
                              ),
                           ),
                      rheader_tabs
                     )
        return rheader
    return None
# ---------------------------------------------------------------------
def assess():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    tabs = [
            (T("Edit Details"), None),
            (T("Impacts"), "impact"),  
            (T("Baselines"), "baseline"),  
            (T("Summary"), "summary"),  
            #(T("Requested"), "ritem"),                                                                                                  
           ]

    rheader = lambda r: shn_assess_rheader(r, tabs)    

    return shn_rest_controller(module, resource, rheader=rheader)    
#==============================================================================
def baseline_type():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================
def baseline():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================
def summary():
    "RESTful CRUD controller"
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    return shn_rest_controller(module, resource)    
#==============================================================================
def assess_short_mobile():
    assess_short_fields = (("baseline", 1),
                           ("baseline", 2),
                           ("baseline", 4),
                           ("baseline", 3),
                           ("impact", 3),
                           ("impact", 4),
                           ("title", "Cluster Indicators:"),
                           ("summary", 4),
                           ("summary", 3),
                           ("summary", 10),
                           ("summary", 11),          
                           ("summary", 9),               
                           ("assess", "comments"),
                           )
    form_row = []
    comment = ""
    for field in assess_short_fields:
        name = "assess_short_%s_%s" % (field[0], field[1])
        if field[0] == "assess":
            id = "assess_short_assess_%s" % field[1]
            label = "%s:" % db.assess_assess[ field[1] ].label
            #widget = db.assess_assess[ field[1] ].widget
            widget = TEXTAREA(_name = id,
                              _class = "double",
                              _type = "text")            
        elif field[0] == "baseline":
            id = name
            label = shn_get_db_field_value(db = db,
                                           table = "assess_baseline_type",
                                           field = "name",
                                           look_up = field[1]
                                           )
            widget = INPUT(_name = id,
                           _class = "double",
                           _type = "text")           
        elif field[0] == "impact":
            id = name
            label = "%s:" % shn_get_db_field_value(db = db,
                                                   table = "impact_type",
                                                   field = "name",
                                                   look_up = field[1]
                                                   )
            widget = INPUT(_name = id,
                           _class = "double",
                           _type = "text")   
        elif field[0] == "summary":
            id = name
            label = "%s:" % shn_get_db_field_value(db = db,
                                                   table = "cluster_subsector",
                                                   field = "abrv",
                                                   look_up = field[1]
                                                   )
            widget = db.assess_summary.value.widget(db.assess_summary.value,
                                                       None,
                                                       _name = name
                                                       )
            for option in widget:
                option[0][0].__setitem__("_name", name)
            
        if field[0] == "title":        
            form_row.append(TR(H3( field[1] )))    
        else:
            form_row = form_row + list( s3_formstyle(id, label, widget, comment) ) 
        
    form = FORM(H1("Sahana Eden"),
                H2("Short Assessment"),
                TABLE(*form_row),
                INPUT(_value = T("Save"),
                      _type = "submit"  
                      ),
                _class = "mobile"
                )
    
    if auth.is_logged_in():
        if form.accepts(request.vars, session):
            record_dict = {}
            
            #Add Assess (must happen first)
            for field in assess_short_fields:
                if field[0] != "assess":
                    continue
                name = "assess_short_assess_%s" % field[1]
                if name in request.vars:
                    record_dict[field[1]] = request.vars[name]
            asssess_id = db.assess_assess.insert(**record_dict)
            
            fk_dict = dict(baseline = "baseline_type_id",
                           impact = "impact_type_id",
                           summary = "cluster_subsector_id"
                           )
            
            component_dict = dict(baseline = "assess_baseline",
                           impact = "impact_impact",
                           summary = "assess_summary"
                           )
    
            #Add Assess Components
            for field in assess_short_fields:
                if field[0] == "assess":
                    continue            
                record_dict = {}
                name = "assess_short_%s_%s" % (field[0], field[1])
                if name in request.vars:
                    record_dict["assess_id"] = asssess_id
                    record_dict[fk_dict[ field[0] ] ] = field[1]
                    record_dict["value"] = request.vars[name]
                    db[component_dict[ field[0] ] ].insert(**record_dict)
                    
            form = FORM(H1("Sahana Eden"),
                        H2("Short Assessment"),
                        P(T("Assessment Reported")),
                        A(T("Report Another Assessment..."),
                          _href = URL(r=request)
                          ),
                        _class = "mobile",
                        )   
    else:
         redirect(URL(r=request, c = "default", f = "index"))            
        
    return dict(form = form)
#ef s3_formstyle(id, label, widget, comment):
