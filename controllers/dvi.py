# -*- coding: utf-8 -*-

module = 'dvi'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Find Reports'), False, URL(r=request, f='find'),[
        [T('List'), False, URL(r=request, f='find')],
        [T('Add'), False, URL(r=request, f='find', args='create')],
    ]],
    [T('Body Recovery'), False, URL(r=request, f='body'),[
        [T('List Bodies'), False, URL(r=request, f='body')],
        [T('Trace Body'), False, URL(r=request, f='body', args='presence')],
        [T('Add Body'), False, URL(r=request, f='body', args='create')],
        [T('Add Image'), False, URL(r=request, f='body', args='image')],
    ]],
    [T('Physical Description'), False, URL(r=request, f='body', args=['pd_general']),[
        [T('Appearance'), False, URL(r=request, f='body', args=['pd_general'])],
        [T('Head'), False, URL(r=request, f='body', args=['pd_head'])],
        [T('Face'), False, URL(r=request, f='body', args=['pd_face'])],
        [T('Teeth'), False, URL(r=request, f='body', args=['pd_teeth'])],
        [T('Body'), False, URL(r=request, f='body', args=['pd_body'])],
    ]]
#    [T('Checklist Of Operations'), False, URL(r=request, f='operation_checklist'),[
#        [T('Personal Effects'), False, URL(r=request, f='personal_effects')],
#        [T('Radiology'), False, URL(r=request, f='radiology')],
#        [T('Fingerprints'), False, URL(r=request, f='fingerprints')],
#        [T('Anthropology'), False, URL(r=request, f='anthropology')],
#        [T('Pathology'), False, URL(r=request, f='pathology')],
#        [T('DNA'), False, URL(r=request, f='dna')],
#        [T('Dental'), False, URL(r=request, f='dental')],
#        [T('Identification'), False, URL(r=request, f='identification')]
#    ]]
]

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def find():
    "RESTlike CRUD controller"
    return shn_rest_controller(module, 'find')

def body():
    crud.settings.delete_onaccept = shn_pentity_ondelete
    output = shn_rest_controller(module, 'body', main='pr_pe_label', extra='opt_pr_gender',
        pheader=shn_dvi_pheader,
        onaccept=lambda form: shn_pentity_onaccept(form, table=db.dvi_body, entity_type=3))

    return output

def image():
    db.pr_image.pr_pe_id.requires = IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_entity_type',filter_opts=(3,)))
    response.s3.filter=(db.pr_image.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_entity_type==3)
    "RESTlike CRUD controller"
    return shn_rest_controller('pr', 'image')

def presence():
    db.pr_presence.pr_pe_id.requires =  IS_NULL_OR(IS_ONE_OF(db,'pr_pentity.id',shn_pentity_represent,filterby='opt_pr_entity_type',filter_opts=(3,)))
    response.s3.filter=(db.pr_presence.pr_pe_id==db.pr_pentity.id)&(db.pr_pentity.opt_pr_entity_type==3)
    "RESTlike CRUD controller"
    return shn_rest_controller('pr', 'presence')

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
