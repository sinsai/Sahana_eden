# -*- coding: utf-8 -*-

""" Joint Initial Rapid Assessment Tool - Controllers

    @author: Fran Boon
    @author: Dominic König

    @see: http://eden.sahanafoundation.org/wiki/Pakistan
    @ToDo: Rename as 'assessment' (Deprioritised due to Data Migration issues being distracting for us currently)

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Assessments"), False, URL(r=request, f="assessment"),[
       [T("List"), False, URL(r=request, f="assessment")],
       [T("Add"), False, URL(r=request, f="assessment", args="create")],
       [T("Search"), False, URL(r=request, f="assessment", args="search")],
    ]],
    [T("Summary"), False, URL(r=request, f="assessment", args="summary")],
    #[T("Map"), False, URL(r=request, f="maps")],
]

def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)


def maps():

    """ Show a Map of all Assessments """

    freports = db(db.gis_location.id == db.rat_freport.location_id).select()
    freport_popup_url = URL(r=request, f="freport", args="read.popup?freport.location_id=")
    map = gis.show_map(feature_queries = [{"name":Tstr("Flood Reports"), "query":freports, "active":True, "popup_url": freport_popup_url}], window=True)

    return dict(map=map)


def assessment():

    """ Rapid Assessments, RESTful controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Villages only
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L4"),
                                                      "gis_location.id",
                                                      repr_select, sort=True))

    if auth.is_logged_in():
        staff_id = db((db.pr_person.uuid == session.auth.user.person_uuid) & \
                      (db.org_staff.person_id == db.pr_person.id)).select(
                       db.org_staff.id, limitby=(0, 1)).first()
        if staff_id:
            table.staff_id.default = staff_id.id

    # Post-processor
    def postp(r, output):
        shn_action_buttons(r, deletable=False)
        # Redirect to read/edit view rather than list view
        if r.representation == "html" and r.method == "create":
            r.next = r.other(method="",
                             record_id=s3xrc.get_session(session, "rat", "assessment"))
        return output
    response.s3.postp = postp

    # Subheadings in forms:
    subheadings = {
        "rat_section3" : {
            "houses_total": "Access to Shelter",
            "water_containers_available": "Water storage containers in households",
            "cooking_equipment_available": "Other non-food items",
            "nfi_assistance_available": "Shelter/NFI Assistance",
            "comments": "Comments"
        },
        "rat_section4" : {
            "water_source_pre_disaster_type": "Water supply",
            "water_coll_time": "Water collection",
            "defec_place_type": "Places for defecation",
            "close_industry": "Environment",
            "latrines_number": "Latrines"
        },
        "rat_section5" : {
            "health_services_pre_disaster": "Health services status",
            "health_problems_adults": "Current health problems",
            "malnutrition_present_pre_disaster": "Nutrition problems"
        }
    }

    crud.settings.create_next = None # Do not redirect from CRUD
    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: \
                                         shn_rat_rheader(r,
                                            tabs = [(T("Identification"), None),
                                                    (T("Demographic"), "section2"),
                                                    (T("Shelter & Essential NFIs"), "section3"),
                                                    (T("WatSan"), "section4"),
                                                    (T("Health"), "section5"),
                                                    (T("Nutrition"), "section6"),
                                                    (T("Livelihood"), "section7"),
                                                    (T("Education"), "section8"),
                                                    (T("Protection"), "section9") ]),
                                 listadd=False,
                                 sticky=True,
                                 subheadings=subheadings)

    response.extra_styles = ["S3/rat.css"]
    return output


# -----------------------------------------------------------------------------
def download():

    """ Download a file """

    return response.download(request, db)



# -----------------------------------------------------------------------------
def shn_rat_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs, paging=True)

        if r.name == "assessment":

            report = r.record
            location = report.location_id
            if location:
                location = shn_gis_location_represent(location)
            staff = report.staff_id
            if staff:
                organisation_id = db(db.org_staff.id == staff).select(db.org_staff.organisation_id).first().organisation_id
                organisation = shn_organisation_represent(organisation_id)
            else:
                organisation = None
            staff = report.staff2_id
            if staff:
                organisation_id = db(db.org_staff.id == staff).select(db.org_staff.organisation_id).first().organisation_id
                organisation2 = shn_organisation_represent(organisation_id)
            else:
                organisation2 = None
            if organisation2:
                orgs = organisation + ", " + organisation2
            else:
                orgs = organisation
            doc_name = doc_url = None
            document = db(db.doc_document.id == report.document_id).select(db.doc_document.name, db.doc_document.file, limitby=(0, 1)).first()
            if document:
                doc_name = document.name
                doc_url = URL(r=request, f="download", args=[document.file])
            rheader = DIV(TABLE(
                            TR(
                                TH(Tstr("Location") + ": "), location,
                                TH(Tstr("Date") + ": "), report.date
                              ),
                            TR(
                                TH(Tstr("Organisations") + ": "), orgs,
                                TH(Tstr("Document") + ": "), A(doc_name, _href=doc_url)
                              )
                            ),
                          rheader_tabs)

            return rheader

        else:
            return None
