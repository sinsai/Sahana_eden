# -*- coding: utf-8 -*-

""" Organisation Registry - Controllers

    @author: Fran Boon
    @author: Michael Howden

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions" Views)
response.menu_options = org_menu

#==============================================================================
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    response.title = module_name
    return dict(module_name=module_name)


#==============================================================================
def cluster():

    """ RESTful CRUD controller """

    #tablename = "%s_%s" % (prefix, resourcename)
    #table = db[tablename]

    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def cluster_subsector():

    """ RESTful CRUD controller """

    #tablename = "%s_%s" % (prefix, resourcename)
    #table = db[tablename]

    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def organisation():

    """ RESTful CRUD controller """

    tabs = [(T("Basic Details"), None),
            (T("Staff"), "staff"),
            (T("Offices"), "office"),                                                
            #(T("Donors"), "organisation"),
            #(T("Sites"), "site"),  # Ticket 195
           ]
    
    if deployment_settings.has_module("assess"):
        tabs.append((T("Assessments"), "assess"))
    if deployment_settings.has_module("project"):
        tabs.append((T("Projects"), "project"))
        tabs.append((T("Activities"), "activity"))
        #tabs.append((T("Tasks"), "task"))

    rheader = lambda r: shn_org_rheader(r,
                                        tabs = tabs)

    output = s3_rest_controller(prefix, resourcename, rheader=rheader)
    return output

#==============================================================================
def office():

    """ RESTful CRUD controller """

    tablename = "org_office"
    table = db[tablename]

    if isinstance(request.vars.organisation_id, list):
        request.vars.organisation_id = request.vars.organisation_id[0]

    shn_add_dynamic_inv_components()

    # Pre-processor
    def prep(r): 
        # Filter out people which are already staff for this inventory
        shn_staff_prep(r) 
        # Filter out items which are already in this inventory
        shn_inv_prep(r)
          
        if r.representation == "popup":
            organisation = request.vars.organisation_id or session.s3.organisation_id or ""
            if organisation:
                table.organisation_id.default = organisation
        
        # Cascade the organisation_id from the office to the staff
        if r.record:
            db.org_staff.organisation_id.default = r.record.organisation_id
            db.org_staff.organisation_id.writable = False
            
        # No point in downloading large dropdowns which we hide, so provide a smaller represent
        # the update forms are not ready. when they will - uncomment this and comment the next one
        #if r.method in ("create", "update"):
        if r.method == "create":
            table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db,
                                                                        "org_organisation.id"))
            if request.vars.organisation_id and request.vars.organisation_id != "None":
                table.organisation_id.default = request.vars.organisation_id
        return True
    response.s3.prep = prep

    rheader = shn_office_rheader

    return s3_rest_controller(prefix, resourcename, rheader=rheader)

#==============================================================================
def staff():
    """ 
        RESTful CRUD controller
        @ToDo: This function may be removed, to restrict the view of staff to only 
        as components within site instances and organisations
    """

    tablename = "org_staff"
    table = db[tablename]

    # Pre-processor
    def prep(r):
        # No point in downloading large dropdowns which we hide, so provide a smaller represent
        # the update forms are not ready. when they will - uncomment this and comment the next one
        #if r.method in ("create", "update"):
        if r.method == "create":
            table.organisation_id.widget = S3AutocompleteWidget(request, "org",
                                                                "organisation",
                                                                post_process="load_offices(false);")
        return True
    response.s3.prep = prep

    return s3_rest_controller(prefix, resourcename)


#==============================================================================
def donor():

    """ RESTful CRUD controller """

    tablename = "org_donor"
    table = db[tablename]

    s3xrc.model.configure(table, listadd=False)
    output = s3_rest_controller(prefix, resourcename)

    return output


#==============================================================================
# Component Resources need these settings to be visible where they are linked from
# - so we put them outside their controller function
tablename = "org_donor"
s3.crud_strings[tablename] = Storage(
    title_create = ADD_DONOR,
    title_display = T("Donor Details"),
    title_list = T("Donors Report"),
    title_update = T("Edit Donor"),
    title_search = T("Search Donors"),
    subtitle_create = T("Add New Donor"),
    subtitle_list = T("Donors"),
    label_list_button = T("List Donors"),
    label_create_button = ADD_DONOR,
    label_delete_button = T("Delete Donor"),
    msg_record_created = T("Donor added"),
    msg_record_modified = T("Donor updated"),
    msg_record_deleted = T("Donor deleted"),
    msg_list_empty = T("No Donors currently registered"))

#==============================================================================
def shn_org_rheader(r, tabs=[]):

    """ Organisation Registry page headers """

    if r.representation == "html":

        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        rheader_tabs = shn_rheader_tabs(r, tabs)

        #_next = r.here()
        #_same = r.same()

        organisation = r.record
        if organisation:
            if organisation.cluster_id:
                _sectors = shn_org_cluster_represent(organisation.cluster_id)
            else:
                _sectors = None

            try:
                _type = org_organisation_type_opts[organisation.type]
            except KeyError:
                _type = None

            rheader = DIV(TABLE(
                TR(
                    TH("%s: " % T("Organization")),
                    organisation.name,
                    TH("%s: " % T("Cluster(s)")),
                    _sectors
                    ),
                TR(
                    #TH(A(T("Edit Organization"),
                    #    _href=URL(r=request, c="org", f="organisation", args=[r.id, "update"], vars={"_next": _next})))
                    TH("%s: " % T("Type")),
                    _type,
                    )
            ), rheader_tabs)

            return rheader

    return None

#==============================================================================


#==============================================================================
