module='msg'
# Current Module (for sidebar title)
module_name=db(db.s3_module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL,orderby=db.s3_module.priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

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
def outgoing_sms():
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
    return shn_rest_controller(module,'outgoing_sms')
def incoming_sms():
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
    return shn_rest_controller(module,'incoming_sms')
