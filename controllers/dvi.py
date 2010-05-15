# -*- coding: utf-8 -*-

"""
    DVI Module - Controllers
"""

module = 'dvi'

# Only people with the DVI role should be able to access this module
#try:
#    dvi_group = db(db[auth.settings.table_group_name].role == 'DVI').select().first().id
#    if auth.has_membership(dvi_group):
#        pass
#    else:
#        session.error = T('Not Authorised!')
#        redirect(URL(r=request, c='default', f='user', args='login'))
#except:
#    session.error=T('Not Authorised!')
#    redirect(URL(r=request, c='default', f='user', args='login'))

# Current Module (for sidebar title)
try:
    module_name = db(db.s3_module.name==module).select().first().name_nice
except:
    module_name = T('Disaster Victim Identification')

# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Body Find'), False, URL(r=request, f='find', args='create'),[
        [T('New Report'), False, URL(r=request, f='find', args='create')],
        [T('List Reports'), False, URL(r=request, f='find')],
    ]],
    [T('Body Recovery'), False, URL(r=request, f='body', args='create'),[
        [T('New Report'), False, URL(r=request, f='body', args='create')],
        [T('List Reports'), False, URL(r=request, f='body')],
    ]],
    [T('Select Body'), False, URL(r=request, f='body', args='search_simple')]
]

def shn_dvi_module_menu_ext():
    if session.rcvars and 'dvi_body' in session.rcvars:
        selection = db.dvi_body[session.rcvars['dvi_body']]
        if selection:
            selection = selection.pr_pe_label
            response.menu_options = [
                [T('Body Find'), False, URL(r=request, f='find', args='create'),[
                    [T('New Report'), False, URL(r=request, f='find', args='create')],
                    [T('List Reports'), False, URL(r=request, f='find')],
                ]],
                [T('Body Recovery'), False, URL(r=request, f='body', args='create'),[
                    [T('New Report'), False, URL(r=request, f='body', args='create')],
                    [T('List Reports'), False, URL(r=request, f='body')],
                ]],
                [T('Select Body'), False, URL(r=request, f='body', args='search_simple')],
                [str(T('Body:')) + ' ' + selection, False, URL(r=request, f='body', args='read'),[
                    [T('Recovery'), False, URL(r=request, f='body', args='read')],
                    [T('Tracing'), False, URL(r=request, f='body', args='presence')],
                    [T('Images'), False, URL(r=request, f='body', args='image')],
                    [T('Effects Inventory'), False, URL(r=request, f='body', args='effects')],
                ]],
                [T('Physical Description'), False, URL(r=request, f='body', args=['pd_general']),[
                    [T('Appearance'), False, URL(r=request, f='body', args=['pd_general'])],
                    [T('Head'), False, URL(r=request, f='body', args=['pd_head'])],
                    [T('Face'), False, URL(r=request, f='body', args=['pd_face'])],
                    [T('Teeth'), False, URL(r=request, f='body', args=['pd_teeth'])],
                    [T('Body'), False, URL(r=request, f='body', args=['pd_body'])],
                ]],
                [T('Identification'), False, URL(r=request, f='body', args=['identification']),[
                    [T('Report'), False, URL(r=request, f='body', args=['identification'])],
                    [T('Checklist'), False, URL(r=request, f='body', args=['checklist'])],
                ]]
            ]

shn_dvi_module_menu_ext()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def find():
    "RESTlike CRUD controller"
    output = shn_rest_controller(module, 'find',
        list_fields = [
            'id',
            'find_date',
            'location_id',
            'location_details',
            'description',
            'bodies_est',
            'bodies_rcv',
            'opt_dvi_task_status'
        ]
    )
    return output

def body():
    crud.settings.delete_onaccept = shn_pentity_ondelete
    output = shn_rest_controller(module, 'body', main='pr_pe_label', extra='opt_pr_gender',
        pheader=shn_dvi_pheader,
        list_fields=[
            'id',
            'pr_pe_label',
            'opt_pr_gender',
            'opt_pr_age_group',
            'date_of_recovery',
            'location_id',
        ]
    )
    shn_dvi_module_menu_ext()
    return output

def personal_effects():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'personal_effects')

def case():
    "Restlike CRUD controller"
    return shn_rest_controller(module, 'case')

def radiology():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'radiology')

def fingerprints():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'fingerprints')

def anthropology():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'anthropology')

def pathology():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'pathology')

def dna():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'dna')

def dental():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'dental')


def operation_checklist():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'operation_checklist')

def identification():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'identification')
