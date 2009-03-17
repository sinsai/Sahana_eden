module='cr'
# Current Module (for sidebar title)
module_name=db(db.s3_module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL,orderby=db.s3_module.priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# http://groups.google.com/group/web2py/browse_thread/thread/53086d5f89ac3ae2
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name,modules=modules,options=options)

def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))

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
    return shn_rest_controller(module,'shelter')

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
    id=db.cr_shelter.insert(name=name)
    return id

@service.xmlrpc
def update(id,name):
    # Need to do validation manually!
    status=db(db.cr_shelter.id==id).update(name=name)
    if status:
        return 'Success - record %d updated!' % id
    else:
        return 'Failed - no record %d!' % id
