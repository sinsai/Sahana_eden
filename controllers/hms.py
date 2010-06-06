# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System

    @author: nursix
"""

module = "hms"

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# -----------------------------------------------------------------------------
# Options Menu (available in all Functions' Views)
def shn_menu():
    menu = [
        [T('Home'), False, URL(r=request, f='index')],
        [T('Hospitals'), False, URL(r=request, f='hospital'), [
            [T('List All'), False, URL(r=request, f='hospital')],
            [T('Find by Name'), False, URL(r=request, f='hospital', args='search_simple')],
            [T('Add Hospital'), False, URL(r=request, f='hospital', args='create')]
        ]],
    ]
    if session.rcvars and 'hms_hospital' in session.rcvars:
        selection = db.hms_hospital[session.rcvars['hms_hospital']]
        if selection:
            menu_hospital = [
                    [selection.name, False, URL(r=request, f='hospital', args=[selection.id]), [
                        [T('Status Report'), False, URL(r=request, f='hospital', args=[selection.id])],
                        [T('Bed Capacity'), False, URL(r=request, f='hospital', args=[selection.id, 'bed_capacity'])],
                        [T('Activity Report'), False, URL(r=request, f='hospital', args=[selection.id, 'hactivity'])],
                        [T('Requests'), False, URL(r=request, f='hospital', args=[selection.id, 'hrequest'])],
                        #[T('Resources'), False, URL(r=request, f='hospital', args=[selection.id, 'resources'])],
                        [T('Images'), False, URL(r=request, f='hospital', args=[selection.id, 'himage'])],
                        [T('Services'), False, URL(r=request, f='hospital', args=[selection.id, 'services'])],
                        [T('Contacts'), False, URL(r=request, f='hospital', args=[selection.id, 'hcontact'])],
                    ]]
            ]
            menu.extend(menu_hospital)
    menu2 = [
        [T('Add Request'), False, URL(r=request, f='hrequest', args='create')],
        [T('Requests'), False, URL(r=request, f='hrequest')],
        [T('Pledges'), False, URL(r=request, f='hpledge')],
    ]
    menu.extend(menu2)
    response.menu_options = menu

shn_menu()

# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = s3.modules[module]["name_nice"]
    
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def hospital():

    """ Main controller for hospital data entry """

    response.s3.pagination = True

    output = shn_rest_controller(module , 'hospital',
        pheader = shn_hms_hospital_pheader,
        list_fields=['id',
            'gov_uuid',
            'name',
            'organisation_id',
            'location_id',
            'phone_business',
            'ems_status',
            'facility_status',
            'clinical_status',
            'security_status',
            'total_beds',
            'available_beds'
        ],
        rss=dict(
            title="%(name)s",
            description=shn_hms_hospital_rss
        ),
        listadd=False)

    shn_menu()

    return output

# -----------------------------------------------------------------------------
def hrequest():

    """ Hospital Requests Controller """

    resource = 'hrequest'

    if auth.user is not None:
        person = db(db.pr_person.uuid==auth.user.person_uuid).select(db.pr_person.id)
        if person:
            db.hms_hpledge.person_id.default = person[0].id

    response.s3.pagination = True

    output = shn_rest_controller(module , resource, listadd=False, deletable=False,
        pheader=shn_hms_hrequest_pheader,
        list_fields=['id',
            'timestamp',
            'hospital_id',
            'city',
            'type',
            'subject',
            'priority',
            'status'],
        rss=dict(
            title="%(subject)s",
            description="%(message)s"
        ))

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def hpledge():

    """ Pledges Controller """

    resource = 'hpledge'

    # Uncomment to enable Server-side pagination:
    #response.s3.pagination = True

    pledges = db(db.hms_hpledge.status == 3).select()
    for pledge in pledges:
        db(db.hms_hrequest.id == pledge.hrequest_id).update(status = 6)

    db.commit()

    if auth.user is not None:
        person = db(db.pr_person.uuid==auth.user.person_uuid).select(db.pr_person.id)
        if person:
            db.hms_hpledge.person_id.default = person[0].id

    output = shn_rest_controller(module, resource, editable = True, listadd=False)

    shn_menu()
    return output

# -----------------------------------------------------------------------------
def shn_hms_hrequest_pheader(resource, record_id, representation, next=None, same=None):

    """ Request PHeader """

    if representation == "html":

        if next:
            _next = next
        else:
            _next = URL(r=request, f=resource, args=['read'])

        if same:
            _same = same
        else:
            _same = URL(r=request, f=resource, args=['read', '[id]'])

        aid_request = db(db.hms_hrequest.id == record_id).select().first()
        try:
            hospital_represent = hospital_id.hospital_id.represent(aid_request.hospital.id)
        except:
            hospital_represent = None

        pheader = TABLE(
                    TR(
                        TH(T('Message: ')),
                        TD(aid_request.message, _colspan=3),
                        ),
                    TR(
                        TH(T('Hospital: ')),
                        db.hms_hospital[aid_request.hospital_id] and db.hms_hospital[aid_request.hospital_id].name or "unknown",
                        TH(T('Source Type: ')),
                        hms_hrequest_source_type.get(aid_request.source_type, "unknown"),
                        TH(T('Completed: ')),
                        aid_request.completed and T("yes") or T("no"),
                        ),
                    TR(
                        TH(T('Time of Request: ')),
                        aid_request.timestamp,
                        TH(T('Status: ')),
                        hms_hrequest_review_opts.get(aid_request.status, "unknown"),
                        TH(""),
                        ""
                        ),
                    TR(
                        TH(T('Priority: ')),
                        hms_hrequest_priority_opts.get(aid_request.priority, "unknown"),
                        TH(""),
                        "",
                        ),
                )
        return pheader

    else:
        return None

#
# -----------------------------------------------------------------------------
