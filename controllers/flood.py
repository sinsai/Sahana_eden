# -*- coding: utf-8 -*-

"""
    Flood Alerts Module - Controllers

    @author: Fran Boon
    @see: http://eden.sahanafoundation.org/wiki/Pakistan
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
    #[T("Map"), False, URL(r=request, f="maps")],
]

def index():

    """ Custom View """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name)


def maps():

    """ Show a Map of all Flood Alerts """

    freports = db(db.gis_location.id == db.flood_freport.location_id).select()
    freport_popup_url = URL(r=request, f="freport", args="read.popup?freport.location_id=")
    map = gis.show_map(feature_queries = [{"name":Tstr("Flood Reports"), "query":freports, "active":True, "popup_url": freport_popup_url}], window=True)

    return dict(map=map)


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
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    resource = request.function
    
    # Disable legacy fields, unless updating, so the data can be manually transferred to new fields
    if "update" not in request.args:
        table.document.readable = table.document.writable = False    
        
    # Post-processor
    def postp(jr, output):
        shn_action_buttons(jr, deletable=False)
        return output
    response.s3.postp = postp

    rheader = lambda r: shn_flood_rheader(r, tabs = [(T("Basic Details"), None),
                                                     (T("Locations"), "freport_location")
                                                    ])
    response.s3.pagination = True
    output = shn_rest_controller(module, resource, rheader=rheader, sticky=True)
    return output

# -----------------------------------------------------------------------------
def download():

    """ Download a file """

    return response.download(request, db)


# -----------------------------------------------------------------------------
def shn_flood_rheader(r, tabs=[]):

    """ Resource Headers """

    if r.representation == "html":
        rheader_tabs = shn_rheader_tabs(r, tabs)

        if r.name == "freport":

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

        else:
            return None
