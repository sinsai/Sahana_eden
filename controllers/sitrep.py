# -*- coding: utf-8 -*-

""" Assessments Module - Controllers

    @author: Fran Boon
    @see: http://eden.sahanafoundation.org/wiki/Pakistan
    @ToDo: Rename as 'assessment' (Deprioritised due to Data Migration issues being distracting for us currently)

"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T("Flood Reports"), False, URL(r=request, f="freport"),[
        [T("List"), False, URL(r=request, f="freport")],
        [T("Add"), False, URL(r=request, f="freport", args="create")],
        #[T("Search"), False, URL(r=request, f="freport", args="search")]
    ]],
    [T("WFP Assessments"), False, URL(r=request, f="assessment"),[
        [T("List"), False, URL(r=request, f="assessment")],
        [T("Add"), False, URL(r=request, f="assessment", args="create")],
        #[T("Search"), False, URL(r=request, f="assessment", args="search")]
    ]],
    [T("Schools"), False, URL(r=request, f="school_district"),[
        [T("List"), False, URL(r=request, f="school_district")],
        [T("Add"), False, URL(r=request, f="school_district", args="create")],
        #[T("Search"), False, URL(r=request, f="school_district", args="search")]
    ]],
    #[T("Rapid Assessments"), False, URL(r=request, f="rassessment"),[
    #    [T("List"), False, URL(r=request, f="rassessment")],
    #    [T("Add"), False, URL(r=request, f="rassessment", args="create")],
        #[T("Search"), False, URL(r=request, f="rassessment", args="search")]
    #]],
    #[T("Map"), False, URL(r=request, f="maps")],
]

def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)


def maps():

    """ Show a Map of all Assessments """

    freports = db(db.gis_location.id == db.sitrep_freport.location_id).select()
    freport_popup_url = URL(r=request, f="freport", args="read.popup?freport.location_id=")
    map = gis.show_map(feature_queries = [{"name":Tstr("Flood Reports"), "query":freports, "active":True, "popup_url": freport_popup_url}], window=True)

    return dict(map=map)


def rassessment():

    """ 
        Rapid Assessments, RESTful controller 
        http://www.ecbproject.org/page/48
    """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Villages only
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L4"), "gis_location.id", repr_select, sort=True))

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: \
                                         shn_sitrep_rheader(r,
                                            tabs = [(T("Section 1"), None),
                                                    (T("Section 2"), "section2"),
                                                    (T("Section 3"), "section3"),
                                                    (T("Section 4"), "section4"),
                                                    (T("Section 5"), "section5"),
                                                    (T("Section 6"), "section6"),
                                                    (T("Section 7"), "section7"),
                                                    (T("Section 8"), "section8"),
                                                    (T("Section 9"), "section9") ]),
                                                    sticky=True)
    return output

def river():

    """ Rivers, RESTful controller """

    resource = request.function

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)
    return output


def freport():

    """ Flood Reports, RESTful controller """

    resource = request.function
    response.s3.pagination = True

    # Post-processor
    def postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = postp

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: \
                                         shn_sitrep_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("Locations"), "freport_location")  ]),
                                                    sticky=True)
    return output


def assessment():

    """ Assessments, RESTful controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Villages only
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L4"), "gis_location.id", repr_select, sort=True))

    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource)
    return output


def school_district():

    """
        REST Controller
        @ToDo: Move to CR
    """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Districts only
    table.location_id.requires = IS_NULL_OR(IS_ONE_OF(db(db.gis_location.level == "L2"), "gis_location.id", repr_select, sort=True))
    table.location_id.comment = DIV(A(ADD_LOCATION,
                                       _class="colorbox",
                                       _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
                                       _target="top",
                                       _title=ADD_LOCATION),
                                     DIV( _class="tooltip",
                                       _title=Tstr("District") + "|" + Tstr("The District for this Report."))),
    response.s3.pagination = True

    # Post-processor
    def user_postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = user_postp

    output = shn_rest_controller(module, resource,
                                 rheader=lambda r: \
                                         shn_sitrep_rheader(r,
                                            tabs = [(T("Basic Details"), None),
                                                    (T("School Reports"), "school_report")]),
                                                    sticky=True)
    return output


# -----------------------------------------------------------------------------
def download():

    """ Download a file """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def shn_sitrep_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        if r.name == "rassessment":

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
            doc_url = URL(r=request, f="download", args=[report.document])
            try:
                doc_name, file = r.table.document.retrieve(report.document)
                if hasattr(file, "close"):
                    file.close()
            except:
                doc_name = report.document
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
                          
        elif r.name == "freport":

            report = r.record
            location = report.location_id
            if location:
                location = shn_gis_location_represent(location)
            doc_url = URL(r=request, f="download", args=[report.document])
            try:
                doc_name, file = r.table.document.retrieve(report.document)
                if hasattr(file, "close"):
                    file.close()
            except:
                doc_name = report.document
            rheader = DIV(TABLE(
                            TR(
                                TH(Tstr("Location") + ": "), location,
                                TH(Tstr("Date") + ": "), report.datetime
                              ),
                            TR(
                                TH(Tstr("Document") + ": "), A(doc_name, _href=doc_url)
                              )
                            ),
                          rheader_tabs)

            return rheader

        elif r.name == "school_district":

            report = r.record
            doc_url = URL(r=request, f="download", args=[report.document])
            try:
                doc_name, file = r.table.document.retrieve(report.document)
                if hasattr(file, "close"):
                    file.close()
            except:
                doc_name = report.document

            rheader = DIV(TABLE(
                            TR(
                                TH(Tstr("Date") + ": "), report.date
                              ),
                            TR(
                                TH(Tstr("Document") + ": "), A(doc_name, _href=doc_url)
                              )
                            ),
                          rheader_tabs)

            return rheader
        else:
            return None
