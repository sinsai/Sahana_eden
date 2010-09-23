# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System

    @author: nursix
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
def shn_menu():
    menu = [
        [T("Home"), False, URL(r=request, f="index")],
        [T("Hospitals"), False, URL(r=request, f="hospital"), [
            [T("List All"), False, URL(r=request, f="hospital")],
            [T("Find by Name"), False, URL(r=request, f="hospital", args="search_simple")],
            [T("Add Hospital"), False, URL(r=request, f="hospital", args="create")]
        ]],
    ]
    if session.rcvars and "hms_hospital" in session.rcvars:
        hospital = db.hms_hospital
        query = (hospital.id == session.rcvars["hms_hospital"])
        selection = db(query).select(hospital.id, hospital.name, limitby=(0, 1)).first()
        if selection:
            menu_hospital = [
                [selection.name, False, URL(r=request, f="hospital", args=[selection.id])],
                [T("Add Request"), False, URL(r=request, f="hospital", args=[selection.id, "req", "create"])],
            ]
            menu.extend(menu_hospital)
    menu2 = [
        [T("Requests"), False, URL(r=request, c="rms", f="req")],
        [T("Pledges"), False, URL(r=request, c="rms", f="pledge")],
    ]
    menu.extend(menu2)
    response.menu_options = menu

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    return dict(module_name=module_name, public_url=deployment_settings.base.public_url)

# -----------------------------------------------------------------------------
def hospital():

    """ Main controller for hospital data entry """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

     # Pre-processor
    def prep(r):
        if r.representation in shn_interactive_view_formats:
            # Don't send the locations list to client (pulled by AJAX instead)
            r.table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

            # Add comments
            table.gov_uuid.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Government UID") + "|" + Tstr("The Unique Identifier (UUID) as assigned to this facility by the government.")))
            table.name.comment = SPAN("*", _class="req")
            table.total_beds.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Total Beds") + "|" + Tstr("Total number of beds in this hospital. Automatically updated from daily reports.")))
            table.available_beds.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Available Beds") + "|" + Tstr("Number of vacant/available beds in this hospital. Automatically updated from daily reports.")))
            table.ems_status.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("EMS Status") + "|" + Tstr("Status of operations of the emergency department of this hospital.")))
            table.ems_reason.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("EMS Reason") + "|" + Tstr("Report the contributing factors for the current EMS status.")))
            table.or_status.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("OR Status") + "|" + Tstr("Status of the operating rooms of this hospital.")))
            table.or_reason.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("OR Reason") + "|" + Tstr("Report the contributing factors for the current OR status.")))
            table.facility_status.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Facility Status") + "|" + Tstr("Status of general operation of the facility.")))
            table.clinical_status.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Clinical Status") + "|" + Tstr("Status of clinical operation of the facility.")))
            table.morgue_status.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Morgue Status") + "|" + Tstr("Status of morgue capacity.")))
            table.security_status.comment = DIV(DIV(_class="tooltip",
                _title=Tstr("Security Status") + "|" + Tstr("Status of security procedures/access restrictions in the hospital.")))
            table.morgue_units.comment =  DIV(DIV(_class="tooltip",
                _title=Tstr("Morgue Units Available") + "|" + Tstr("Number of vacant/available units to which victims can be transported immediately.")))
            table.access_status.comment =  DIV(DIV(_class="tooltip",
                _title=Tstr("Road Conditions") + "|" + Tstr("Describe the condition of the roads to your hospital.")))

            # CRUD Strings
            LIST_HOSPITALS = T("List Hospitals")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_HOSPITAL,
                title_display = T("Hospital Details"),
                title_list = LIST_HOSPITALS,
                title_update = T("Edit Hospital"),
                title_search = T("Search Hospitals"),
                subtitle_create = T("Add New Hospital"),
                subtitle_list = T("Hospitals"),
                label_list_button = LIST_HOSPITALS,
                label_create_button = ADD_HOSPITAL,
                label_delete_button = T("Delete Hospital"),
                msg_record_created = T("Hospital information added"),
                msg_record_modified = T("Hospital information updated"),
                msg_record_deleted = T("Hospital information deleted"),
                msg_list_empty = T("No Hospitals currently registered"))
            
            if r.component and r.component.name == "req":
                # Hide the Implied fields
                db.rms_req.shelter_id.writable = db.rms_req.shelter_id.readable = False
                db.rms_req.organisation_id.writable = db.rms_req.organisation_id.readable = False
                db.rms_req.location_id.writable = False
                db.rms_req.location_id.default = r.record.location_id
                db.rms_req.location_id.comment = ""

        elif r.representation == "aadata":
            # Hide the Implied fields here too to make columns match
            db.rms_req.shelter_id.readable = False
            db.rms_req.organisation_id.readable = False
            
        return True
    response.s3.prep = prep

    #s3xrc.sync_resolve = shn_hospital_resolver

    def hospital_postp(jr, output):
        if jr.representation in shn_interactive_view_formats:
            if jr.component and jr.component.name == "bed_capacity":
                label = UPDATE
            else:
                label = READ
            linkto = shn_linkto(jr, sticky=True)("[id]")
            response.s3.actions = [
                dict(label=str(label), _class="action-btn", url=str(linkto))
            ]
        return output
    response.s3.postp = hospital_postp

    rheader = lambda r: shn_hms_hospital_rheader(r,
                                                 tabs=[(T("Status Report"), ""),
                                                       (T("Bed Capacity"), "bed_capacity"),
                                                       (T("Activity Report"), "hactivity"),
                                                       (T("Requests"), "req"),
                                                       (T("Images"), "himage"),
                                                       (T("Services"), "services"),
                                                       (T("Contacts"), "hcontact")
                                                      ])

    response.s3.pagination = True
    output = shn_rest_controller(module, resource,
                                 rheader=rheader,
                                 rss=dict(title="%(name)s",
                                          description=shn_hms_hospital_rss),
                                 #listadd=False
                                )

    shn_menu()

    return output


def shn_hospital_resolver(vector):

    """ Example for a simple Sync resolver - not for production use """

    # Default resolution: import data from peer if newer
    vector.default_resolution = vector.RESOLUTION.NEWER

    if vector.tablename == "hms_hospital":
        # Do not update hospital Gov-UUIDs or names
        vector.resolution = dict(
            gov_uuid = vector.RESOLUTION.THIS,
            name = vector.RESOLUTION.THIS
        )
    else:
        vector.resolution = vector.RESOLUTION.NEWER

    # Allow both, update of existing and create of new records:
    vector.strategy = [vector.METHOD.UPDATE, vector.METHOD.CREATE]

# -----------------------------------------------------------------------------
#
def shn_hms_hospital_rheader(jr, tabs=[]):

    """ Page header for component resources """

    if jr.name == "hospital":
        if jr.representation == "html":

            _next = jr.here()
            _same = jr.same()

            rheader_tabs = shn_rheader_tabs(jr, tabs)

            hospital = jr.record
            if hospital:
                rheader = DIV(TABLE(

                    TR(TH(T("Name: ")),
                        hospital.name,
                        TH(T("EMS Status: ")),
                        "%s" % db.hms_hospital.ems_status.represent(hospital.ems_status)),

                    TR(TH(T("Location: ")),
                        db.gis_location[hospital.location_id] and db.gis_location[hospital.location_id].name or "unknown",
                        TH(T("Facility Status: ")),
                        "%s" % db.hms_hospital.facility_status.represent(hospital.facility_status)),

                    TR(TH(T("Total Beds: ")),
                        hospital.total_beds,
                        TH(T("Clinical Status: ")),
                        "%s" % db.hms_hospital.clinical_status.represent(hospital.clinical_status)),

                    TR(TH(T("Available Beds: ")),
                        hospital.available_beds,
                        TH(T("Security Status: ")),
                        "%s" % db.hms_hospital.security_status.represent(hospital.security_status))

                        ), rheader_tabs)

                return rheader

    return None
