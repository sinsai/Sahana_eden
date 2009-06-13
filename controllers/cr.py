# -*- coding: utf-8 -*-

module = 'cr'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Home'), False, URL(r=request, f='index')],
    [T('Add Shelter'), False, URL(r=request, f='shelter', args='create')],
    [T('List Shelters'), False, URL(r=request, f='shelter')],
    [T('Search Shelters'), False, URL(r=request, f='shelter', args='search')]
]
        
# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def shelter():
    """ RESTlike CRUD controller
    >>> resource='shelter'
    >>> from applications.sahana.modules.s3_test import WSGI_Test
    >>> test=WSGI_Test(db)
    >>> '200 OK' in test.getPage('/sahana/%s/%s' % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody('List Shelters')
    >>> '200 OK' in test.getPage('/sahana/%s/%s/create' % (module,resource))    #doctest: +SKIP
    True
    >>> test.assertHeader("Content-Type", "text/html")                          #doctest: +SKIP
    >>> test.assertInBody('Add Shelter')                                        #doctest: +SKIP
    >>> '200 OK' in test.getPage('/sahana/%s/%s?format=json' % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/html")
    >>> test.assertInBody('[')
    >>> '200 OK' in test.getPage('/sahana/%s/%s?format=csv' % (module,resource))
    True
    >>> test.assertHeader("Content-Type", "text/csv")
    """
    return shn_rest_controller(module, 'shelter')

# http://groups.google.com/group/web2py/browse_thread/thread/53086d5f89ac3ae2
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()

@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def rpc(method,id=0):
    if method == 'list':
        return db().select(db.cr_shelter.ALL).as_list()
    if method == 'read':
        return db(db.cr_shelter.id==id).select().as_list()
    if method == 'delete':
        status=db(db.cr_shelter.id==id).delete()
        if status:
            return 'Success - record %d deleted!' % id
        else:
            return 'Failed - no record %d!' % id
    else:
        return 'Method not implemented!'

@service.xmlrpc
def create(name):
    # Need to do validation manually!
    id = db.cr_shelter.insert(name=name)
    return id

@service.xmlrpc
def update(id, name):
    # Need to do validation manually!
    status = db(db.cr_shelter.id==id).update(name=name)
    if status:
        return 'Success - record %d updated!' % id
    else:
        return 'Failed - no record %d!' % id
