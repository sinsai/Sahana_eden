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
def shelterrpc(method):
    if method == 'list':
        return db(db.cr_shelter.id>0).select()
    else:
        return 'Method not implemented'

@service.rss
def rss(resource):
    " http://127.0.0.1:8000/sahana/cr/call/rss/rss/resource "
    table=module+'_'+resource
    if request.env.remote_addr=='127.0.0.1':
        server='http://127.0.0.1:' + request.env.server_port
    else:
        server='http://' + request.env.server_name + ':' + request.env.server_port
    link='/%s/%s/%s' % (request.application,module,resource)
    entries=[]
    rows=db(db[table].id>0).select()
    for row in rows:
        entries.append(dict(title=row.name,link=server+link+'/%d' % row.id,description=row.description or '',created_on=row.created_on))
    return dict(title=str(s3.crud_strings[table].subtitle_list),link=server+link,description='',created_on=request.now,entries=entries)
