# -*- coding: utf-8 -*-

"""
    Buildings Assessments module

    @author Fran Boon <fran@aidiq.com>

    Data model from:
    http://www.atcouncil.org/products/downloadable-products/placards

    Postearthquake Safety Evaluation of Buildings: ATC-20
    http://www.atcouncil.org/pdfs/rapid.pdf
    This is actually based on the New Zealand variant:
    http://eden.sahanafoundation.org/wiki/BluePrintBuildingAssessments
    
    @ToDo: add other forms
    Urgent: Level 2 of the ~ATC-20
    - make this a 1-1 component of the rapid form?
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
            [T("Report"), False, aURL(r=request, f="atc20_report")],
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
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

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

    # Subheadings in forms:
    s3xrc.model.configure(table,
        subheadings = {
            ".": "name", # Description in ATC-20
            "%s / %s" % (T("Overall Hazards"), T("Damage")): "collapse",
            ".": "posting",
            "%s:" % T("Further Action Recommended"): "barricades",
            ".": "estimated_damage",
            })

    rheader = lambda r: shn_atc20_rheader(r)

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
                    pe_id = db(db.pr_person.id == person).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
                    query = (db.pr_pe_contact.pe_id == pe_id) & (db.pr_pe_contact.contact_method == 2)
                    mobile = db(query).select(db.pr_pe_contact.value, limitby=(0, 1)).first()
                    if mobile:
                        mobile = mobile.value
                    person = vita.fullname(person)
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Person")), person,
                                    TH("%s: " % T("Mobile")), mobile
                                  ),
                                TR(
                                    TH("%s: " % T("Location")), location,TH("%s: " % T("Date")), assess.date
                                  ),
                                ),
                              rheader_tabs)

                return rheader
    return None

# -----------------------------------------------------------------------------
def atc20_report():
    """
        A report providing assessment totals, and breakdown by assessment type and status.
        e.g. Level 1 (red, yellow, green) Level 2 (R1-R3, Y1-Y2, G1-G2)

        @ToDo: Make into a Custom Method to be able to support Table ACLs
        (currently protected by Controller ACL)
    """

    table = db.building_atc20
    level1 = Storage()
    # Which is more efficient?
    # A) 4 separate .count() in DB
    # B) Pulling all records into Python & doing counts in Python
    query = (table.deleted == False)
    level1.total = db(query).count()
    filter = (table.posting == 1)
    level1.green = db(query & filter).count()
    filter = (table.posting == 2)
    level1.yellow = db(query & filter).count()
    filter = (table.posting == 3)
    level1.red = db(query & filter).count()
    
    level2 = Storage()
    
    return dict(level1=level1,
                level2=level2)
# -----------------------------------------------------------------------------