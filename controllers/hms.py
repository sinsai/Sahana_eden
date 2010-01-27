# -*- coding: utf-8 -*-

"""
    HMS Hospital Status Assessment and Request Management System

    @author: nursix
"""

module = 'hms'


# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice


# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Hospitals'), False, URL(r=request, f='hospital'), [
        [T('List All'), False, URL(r=request, f='hospital')],
        #[T('List by Location'), False, URL(r=request, f='hospital', args='search_location')],
        [T('Find by Name'), False, URL(r=request, f='hospital', args='search_simple')],
        [T('Find by Bed Type'), False, URL(r=request, f='hospital', args='search_bedtype')],
        [T('Add Hospital'), False, URL(r=request, f='hospital', args='create')],
    ]],
    [T('Add Request'), False, URL(r=request, f='hrequest', args='create')],
    [T('Requests'), False, URL(r=request, f='hrequest')],
    [T('Pledges'), False, URL(r=request, f='pledge')],
]


def shn_hms_menu_ext():
    menu = [
        [T('Home'), False, URL(r=request, f='index')],
            [T('Hospitals'), False, URL(r=request, f='hospital'), [
                [T('List All'), False, URL(r=request, f='hospital')],
                #[T('List by Location'), False, URL(r=request, f='hospital', args='search_location')],
                [T('Find by Name'), False, URL(r=request, f='hospital', args='search_simple')],
                [T('Find by Bed Type'), False, URL(r=request, f='hospital', args='search_bedtype')],
                [T('Add Hospital'), False, URL(r=request, f='hospital', args='create')],
                [T('Shortages'), False, URL(r=request, f='shortage')],
            ]],
    ]
    if session.rcvars and 'hms_hospital' in session.rcvars:
        selection = db.hms_hospital[session.rcvars['hms_hospital']]
        if selection:
            menu_hospital = [
                    [selection.name, False, URL(r=request, f='hospital', args=[selection.id]), [
                        [T('Status Report'), False, URL(r=request, f='hospital', args=[selection.id])],
                        [T('Bed Capacity'), False, URL(r=request, f='hospital', args=[selection.id, 'bed_capacity'])],
                        [T('Services'), False, URL(r=request, f='hospital', args=[selection.id, 'services'])],
                        #[T('Resources'), False, URL(r=request, f='hospital', args=[selection.id, 'resources'])],
                        [T('Request'), False, URL(r=request, f='hospital', args=[selection.id, 'hrequest'])],
                        [T('Contacts'), False, URL(r=request, f='hospital', args=[selection.id, 'contact'])],
                    ]]
            ]
            menu.extend(menu_hospital)
    menu2 = [
        [T('Add Request'), False, URL(r=request, f='hrequest', args='create')],
        [T('Requests'), False, URL(r=request, f='hrequest')],
        [T('Pledges'), False, URL(r=request, f='pledge')],
    ]
    menu.extend(menu2)
    response.menu_options = menu


shn_hms_menu_ext()


def index():
    "Module's Home Page"
    return dict(module_name=module_name)


def hospital():

    """ Main controller for hospital data entry """

    output = shn_rest_controller(module , 'hospital', listadd=False,
        pheader = shn_hms_hospital_pheader,
        rss=dict(
            title="%(name)s",
            description=shn_hms_hospital_rss
        ),
        list_fields=['id', 'name', 'organisation_id', 'location_id', 'phone_business', 'ems_status', 'facility_status', 'clinical_status', 'security_status', 'total_beds', 'available_beds'])
    shn_hms_menu_ext()
    return output


def hrequest():

    """ Hospital Requests Controller """

    resource = 'hrequest'

    if request.args(0) and request.args(0) == 'search_simple':
        pass
    else:
        # Uncomment to enable Server-side pagination:
        #response.s3.pagination = True
        pass

    if auth.user is not None:
        print "Person UUID: %s" % auth.user.person_uuid
        person = db(db.pr_person.uuid==auth.user.person_uuid).select(db.pr_person.id)
        if person:
            db.hms_pledge.person_id.default = person[0].id

    output = shn_rest_controller(module , resource, listadd=False, deletable=False,
        pheader=shn_hms_hrequest_pheader,
        rss=dict(
            title="%(subject)s",
            description="%(message)s"
        ),
        list_fields=['id', 'timestamp', 'hospital_id', 'city', 'type', 'subject', 'priority', 'verified', 'completed'],
        onaccept = shn_hms_hrequest_onaccept)

    shn_hms_menu_ext()
    return output


def pledge():

    """ Pledges Controller """

    resource = 'pledge'

    # Uncomment to enable Server-side pagination:
    #response.s3.pagination = True

    pledges = db(db.hms_pledge.status == 3).select()
    for pledge in pledges:
        req = db(db.hms_hrequest.id == pledge.hrequest_id).update(completed = True)

    db.commit()

    if auth.user is not None:
        print "Person UUID: %s" % auth.user.person_uuid
        person = db(db.pr_person.uuid==auth.user.person_uuid).select(db.pr_person.id)
        if person:
            db.hms_pledge.person_id.default = person[0].id

    output = shn_rest_controller(module, resource, editable = True, listadd=False)

    shn_hms_menu_ext()
    return output


def shn_hms_hrequest_pheader(resource, record_id, representation, next=None, same=None):
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
                        TH(T('Priority: ')),
                        hms_hrequest_priority_opts.get(aid_request.priority, "unknown"),
                        TH(T('Source Type: ')),
                        hms_hrequest_source_type[aid_request.source_type],
                        ),
                    TR(
                        TH(T('Time of Request: ')),
                        aid_request.timestamp,
                        TH(T('Verified: ')),
                        aid_request.verified and T("yes") or T("no"),
                        TH(""),
                        ""
                        ),
                    TR(
                        TH(T('Hospital: ')),
                        db.hms_hospital[aid_request.hospital_id] and db.hms_hospital[aid_request.hospital_id].name or "unknown",
                        TH(T('Actionable: ')),
                        aid_request.actionable and T("yes") or T("no"),
                        TH(T('Completion status: ')),
                        aid_request.completed,
                        ),
                )
        return pheader

    else:
        return None

