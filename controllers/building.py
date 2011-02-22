# -*- coding: utf-8 -*-

"""
    Buildings Assessments module

    @author Fran Boon <fran@aidiq.com>

    Data model from:
    http://www.atcouncil.org/products/downloadable-products/placards

    Postearthquake Safety Evaluation of Buildings: ATC-20
    http://www.atcouncil.org/pdfs/rapid.pdf
    
    @ToDo: add other forms
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
def shn_menu():
    menu = [
        [T("ATC-20"), False, aURL(r=request, f="atc20"), [
            [T("List"), False, aURL(r=request, f="atc20")],
            [T("Add"), False, aURL(p="create", r=request, f="atc20", args="create")],
            #[T("Search"), False, URL(r=request, f="atc20", args="search")],
        ]],
    ]
    response.menu_options = menu

shn_menu()

# S3 framework functions
# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# ATC-20 Rapid Evaluation Safety Assessment Form ------------------------------
def atc20():

    """
        RESTful CRUD controller
    """

    resource = request.function

    # Pre-populate Inspector ID
    if auth.is_logged_in():
        person_id = db((db.pr_person.uuid == session.auth.user.person_uuid)).select(db.pr_person.id,
                                                                                    limitby=(0, 1)).first()
        if person_id:
            table.person_id.default = person_id.id

    # Post-processor
    def postp(r, output):
        shn_action_buttons(r, deletable=False)
        # Redirect to read/edit view rather than list view
        if r.representation == "html" and r.method == "create":
            r.next = r.other(method="",
                             record_id=s3xrc.get_session("building", "atc20"))
        return output
    response.s3.postp = postp

    # Over-ride the listadd since we're not a component here
    s3xrc.model.configure(table, create_next="", listadd=True)

    rheader = lambda r: shn_atc20_rheader(r,
                                          tabs = [(T("Inspection"), None),
                                                  (T("Building Description"), "atc20_description"),
                                                  (T("Evaluation"), "atc20_evaluation"),
                                                  (T("Posting"), "atc20_posting"),
                                                  (T("Further Actions"), "atc20_actions"),
                                                ])

    output = s3_rest_controller(module, resource,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def shn_atc20_rheader(r, tabs=[]):
    """ Resource Headers """

    if r.representation == "html":
        if r.name == "atc20":
            assess = r.record
            if assess:
                rheader_tabs = shn_rheader_tabs(r, tabs)
                location = assess.location_id
                if location:
                    location = shn_gis_location_represent(location)
                person = assess.person_id
                if person:
                    person = vita.fullname(person)
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Location")), location,
                                    TH("%s: " % T("Person")), person
                                  ),
                                TR(
                                    TH("%s: " % T("Date")), assess.date
                                  )
                                ),
                              rheader_tabs)

                return rheader
    return None

# -----------------------------------------------------------------------------