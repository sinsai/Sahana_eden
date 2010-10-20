# -*- coding: utf-8 -*-

"""
    Organisation Registry - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions" Views)
response.menu_options = org_menu

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)


#==============================================================================
def cluster():
    "RESTful CRUD controller"
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    return shn_rest_controller(module, resourcename)    
#==============================================================================
def cluster_subsector():
    "RESTful CRUD controller"
    resourcename = request.function
    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    return shn_rest_controller(module, resourcename)    
#==============================================================================

def organisation():
    """ RESTful CRUD controller """

    resource = request.function

    rheader = lambda r: shn_org_rheader(r,
                                        tabs = [(T("Basic Details"), None),
                                                (T("Offices"), "office"),
                                                (T("Staff"), "staff"),
                                                (T("Activities"), "activity"),
                                                #(T("Projects"), "project"),
                                                #(T("Tasks"), "task"),
                                                #(T("Donors"), "organisation"),
                                                #(T("Sites"), "site"),  # Ticket 195
                                               ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 rheader=rheader)

    return output

def office():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    if isinstance(request.vars.organisation_id, list):
        request.vars.organisation_id = request.vars.organisation_id[0]

    # Pre-processor
    def prep(jr):
        # No point in downloading large dropdowns which we hide, so provide a smaller represent
        # the update forms are not ready. when they will - uncomment this and comment the next one
        #if jr.method in ("create", "update"):
        if jr.method == "create":
            table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
            if request.vars.organisation_id and request.vars.organisation_id != "None":
                session.s3.organisation_id = request.vars.organisation_id
                # Organisation name should be displayed on the form if organisation_id is pre-selected
                session.s3.organisation_name = db(db.org_organisation.id == int(session.s3.organisation_id)).select(db.org_organisation.name).first().name
        return True
    response.s3.prep = prep
    
    rheader = lambda r: shn_org_rheader(r,
                                        tabs = [(T("Basic Details"), None),
                                                (T("Contact Data"), "pe_contact"),
                                                (T("Staff"), "staff"),
                                               ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 #listadd=False,
                                 rheader=rheader)

    return output


def staff():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    # Pre-processor
    def prep(jr):
        # No point in downloading large dropdowns which we hide, so provide a smaller represent
        # the update forms are not ready. when they will - uncomment this and comment the next one
        #if jr.method in ("create", "update"):
        if jr.method == "create":
            # person_id mandatory for a staff!
            table.person_id.requires = IS_ONE_OF_EMPTY(db, "pr_person.id")
            table.organisation_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_organisation.id"))
            table.office_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "org_office.id"))
        return True
    response.s3.prep = prep

    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

def donor():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    response.s3.pagination = True
    output = shn_rest_controller(module, resource, listadd=False)
    
    return output

# Component Resources need these settings to be visible where they are linked from
# - so we put them outside their controller function
tablename = "%s_%s" % (module, "donor")
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

def project():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
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
                                           
    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False,
                                 main="code",
                                 rheader=rheader
                                )
    
    return output

def task():
    """ RESTful CRUD controller """
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    
    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 listadd=False
                                )
    
    return output

def shn_org_rheader(r, tabs=[]):
    " Organisation Registry page headers "

    if r.representation == "html":
        
        rheader_tabs = shn_rheader_tabs(r, tabs)
        
        if r.name == "organisation":
        
            #_next = r.here()
            #_same = r.same()

            organisation = r.record

            if organisation.cluster_id:
                _sectors = shn_sector_represent(organisation.cluster_id)
            else:
                _sectors = None

            try:
                _type = org_organisation_type_opts[organisation.type]
            except KeyError:
                _type = None
            
            rheader = DIV(TABLE(
                TR(
                    TH(T("Organization") + ": "),
                    organisation.name,
                    TH(T("Cluster(s)") + ": "),
                    _sectors
                    ),
                TR(
                    #TH(A(T("Edit Organization"),
                    #    _href=URL(r=request, c="org", f="organisation", args=[r.id, "update"], vars={"_next": _next})))
                    TH(T("Type") + ": "),
                    _type,
                    )
            ), rheader_tabs)

            return rheader

        elif r.name == "office":
        
            #_next = r.here()
            #_same = r.same()

            office = r.record
            organisation = db(db.org_organisation.id == office.organisation_id).select(db.org_organisation.name, limitby=(0, 1)).first()
            if organisation:
                org_name = organisation.name
            else:
                org_name = None

            rheader = DIV(TABLE(
                    TR(
                        TH(T("Name") + ": "),
                        office.name,
                        TH(T("Type") + ": "),
                        org_office_type_opts.get(office.type, UNKNOWN_OPT),
                        ),
                    TR(
                        TH(T("Organization") + ": "),
                        org_name,
                        TH(T("Location") + ": "),
                        shn_gis_location_represent(office.location_id),
                        ),
                    TR(
                        #TH(A(T("Edit Office"),
                        #    _href=URL(r=request, c="org", f="office", args=[r.id, "update"], vars={"_next": _next})))
                        )
                ), rheader_tabs)

            return rheader

    return None
