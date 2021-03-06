# -*- coding: utf-8 -*-

""" HMS Hospital Status Assessment and Request Management System

    @author: nursix

"""

module = request.controller
resourcename = request.function

if not deployment_settings.has_module(module):
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
def shn_menu():
    public_url = deployment_settings.base.public_url
    if len(request.args) > 0 and request.args[0].isdigit():
        newreq = dict(from_record="hms_hospital.%s" % request.args[0],
                      from_fields="hospital_id$id")
        #selreq = {"req.hospital_id":request.args[0]}
    else:
        newreq = dict()
    selreq = {"req.hospital_id__ne":"NONE"}
    response.menu_options = [
        [T("Hospital"), False, aURL(r=request, f="hospital", args="search"), [
            [T("New"), False, aURL(p="create", r=request, f="hospital", args="create")],
            [T("Search"), False, aURL(r=request, f="hospital", args="search")],
            [T("List All"), False, aURL(r=request, f="hospital")],
            #["----", False, None],
            #[T("Show Map"), False, URL(r=request, c="gis", f="map_viewing_client",
                                       #vars={"kml_feed" : "%s/%s/hms/hospital.kml" %
                                             #(public_url, request.application),
                                             #"kml_name" : "Hospitals_"})],
        ]],
    ]
    if deployment_settings.has_module("rms"):
        response.menu_options.append( \
            [T("Requests"), False, aURL(r=request, c="rms", f="req",
                                    vars=selreq), [
            [T("New"), False, aURL(p="create", r=request, c="rms", f="req",
                                   args="create", vars=newreq)],
            [T("Manage"), False, aURL(r=request, c="rms", f="req",
                                      vars=selreq)],
        ]])
    response.menu_options.append([T("Help"), False, URL(r=request, f="index")])
    menu_selected = []
    if session.rcvars and "hms_hospital" in session.rcvars:
        hospital = db.hms_hospital
        query = (hospital.id == session.rcvars["hms_hospital"])
        record = db(query).select(hospital.id, hospital.name, limitby=(0, 1)).first()
        if record:
            name = record.name
            menu_selected.append(["%s: %s" % (T("Hospital"), name), False,
                                 URL(r=request, f="hospital", args=[record.id])])
    if menu_selected:
        menu_selected = [T("Open recent"), True, None, menu_selected]
        response.menu_options.append(menu_selected)

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name, public_url=deployment_settings.base.public_url)

# -----------------------------------------------------------------------------
def hospital():

    """ Main controller for hospital data entry """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-processor
    def prep(r):
        # Filter out people which are already staff for this warehouse
        shn_staff_prep(r)
        if deployment_settings.has_module("inv"):
            # Filter out items which are already in this inventory
            shn_inv_prep(r)

        # Cascade the organisation_id from the Warehouse to the staff
        if r.record:
            db.org_staff.organisation_id.default = r.record.organisation_id
            db.org_staff.organisation_id.writable = False

        if r.interactive:
            # Don't send the locations list to client (pulled by AJAX instead)
            r.table.location_id.requires = IS_NULL_OR(IS_ONE_OF_EMPTY(db, "gis_location.id"))

            # Add comments
            table.gov_uuid.comment = DIV(DIV(_class="tooltip",
                _title=T("Government UID") + "|" + T("The Unique Identifier (UUID) as assigned to this facility by the government.")))
            table.total_beds.comment = DIV(DIV(_class="tooltip",
                _title=T("Total Beds") + "|" + T("Total number of beds in this hospital. Automatically updated from daily reports.")))
            table.available_beds.comment = DIV(DIV(_class="tooltip",
                _title=T("Available Beds") + "|" + T("Number of vacant/available beds in this hospital. Automatically updated from daily reports.")))
            table.ems_status.comment = DIV(DIV(_class="tooltip",
                _title=T("EMS Status") + "|" + T("Status of operations of the emergency department of this hospital.")))
            table.ems_reason.comment = DIV(DIV(_class="tooltip",
                _title=T("EMS Reason") + "|" + T("Report the contributing factors for the current EMS status.")))
            table.or_status.comment = DIV(DIV(_class="tooltip",
                _title=T("OR Status") + "|" + T("Status of the operating rooms of this hospital.")))
            table.or_reason.comment = DIV(DIV(_class="tooltip",
                _title=T("OR Reason") + "|" + T("Report the contributing factors for the current OR status.")))
            table.facility_status.comment = DIV(DIV(_class="tooltip",
                _title=T("Facility Status") + "|" + T("Status of general operation of the facility.")))
            table.clinical_status.comment = DIV(DIV(_class="tooltip",
                _title=T("Clinical Status") + "|" + T("Status of clinical operation of the facility.")))
            table.morgue_status.comment = DIV(DIV(_class="tooltip",
                _title=T("Morgue Status") + "|" + T("Status of morgue capacity.")))
            table.security_status.comment = DIV(DIV(_class="tooltip",
                _title=T("Security Status") + "|" + T("Status of security procedures/access restrictions in the hospital.")))
            table.morgue_units.comment =  DIV(DIV(_class="tooltip",
                _title=T("Morgue Units Available") + "|" + T("Number of vacant/available units to which victims can be transported immediately.")))
            table.access_status.comment =  DIV(DIV(_class="tooltip",
                _title=T("Road Conditions") + "|" + T("Describe the condition of the roads to your hospital.")))

            if r.component and r.component.name == "req":
                if r.method != "update" and r.method != "read":
                    # Hide fields which don't make sense in a Create form
                    # inc list_create (list_fields over-rides)
                    shn_req_create_form_mods()

        elif r.representation == "aadata":
            pass
            # Hide the Implied fields here too to make columns match
            #db.rms_req.shelter_id.readable = False
            #db.rms_req.organisation_id.readable = False

        return True
    response.s3.prep = prep

    # Post-processor
    def postp(r, output):
        if r.component_name == "staff" and \
                isinstance(output, dict) and \
                deployment_settings.get_aaa_has_staff_permissions():
            addheader = "%s %s." % (STAFF_HELP,
                                    T("Hospital"))
            output.update(addheader=addheader)
        return output
    response.s3.postp = postp

    rheader = lambda r: shn_hms_hospital_rheader(r)

    output = s3_rest_controller(module, resourcename, rheader=rheader)
    shn_menu()
    return output
# -----------------------------------------------------------------------------
def req_match():
    return s3_req_match()
# -----------------------------------------------------------------------------
