module='default'
# Current Module (for sidebar title)
module_name=db(db.s3_module.name==module).select()[0].name_nice
# List Modules (from which to build Menu of Modules)
modules=db(db.s3_module.enabled=='Yes').select(db.s3_module.ALL,orderby=db.s3_module.priority)
# List Options (from which to build Menu for this Module)
options=db(db['%s_menu_option' % module].enabled=='Yes').select(db['%s_menu_option' % module].ALL,orderby=db['%s_menu_option' % module].priority)

# Web2Py Tools functions
# (replaces T2)
def user():
    "Auth functions based on arg. See gluon/tools.py"
    return dict(form=auth(),module_name=module_name,modules=modules,options=options)
def data():
    "Crud functions based on arg. See gluon/tools.py"
    return dict(form=crud(),module_name=module_name,modules=modules,options=options)
def download():
    "Download a file."
    return response.download(request,db) 

# S3 framework functions
def index():
    "Module's Home Page"
    admin_name=db().select(db.s3_setting.admin_name)[0].admin_name
    admin_email=db().select(db.s3_setting.admin_email)[0].admin_email
    admin_tel=db().select(db.s3_setting.admin_tel)[0].admin_tel
    response.title=T('Sahana FOSS Disaster Management System')
    return dict(module_name=module_name,modules=modules,options=options,admin_name=admin_name,admin_email=admin_email,admin_tel=admin_tel)
def open_module():
    "Select Module"
    id=request.vars.id
    modules=db(db.s3_module.id==id).select()
    if not len(modules):
        redirect(URL(r=request,f='index'))
    module=modules[0].name
    redirect(URL(r=request,c=module,f='index'))
def open_option():
    "Select Option from Module Menu"
    id=request.vars.id
    options=db(db['%s_menu_option' % module].id==id).select()
    if not len(options):
        redirect(URL(r=request,f='index'))
    option=options[0].function
    redirect(URL(r=request,f=option))
def menu_open():
    if not session.menu_open:
        session.menu_open=Storage()
        session.menu_open.open_menus=[]
    if not (session.menu_open.module_name==request.vars.module_name):
        session.menu_open.module_name=request.vars.module_name
        session.menu_open.open_menus=[]
    session.menu_open.open_menus.append(request.vars.option_name)
    return dict(module_name=session.menu_open.module_name)
def menu_close():
    if session.menu_open:
        if session.menu_open.module_name==request.vars.module_name:
            try:
                session.menu_open.open_menus.remove(request.vars.option_name)
            except:
                pass
    response.view='default/menu_open.html'
    return dict(module_name=session.menu_open.module_name)
@auth.requires_membership('Administrator')
def setting():
    "RESTlike CRUD controller"
    return shn_rest_controller(module,'setting')
@auth.requires_membership('Administrator')
def role():
    "RESTlike CRUD controller"
    return shn_rest_controller('auth','group')

    
# About Sahana
def apath(path=''):
    "Application path"
    import os
    from gluon.fileutils import up
    opath=up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3]=='../': opath,path=up(opath),path[3:]
    return os.path.join(opath,path).replace('\\','/')

def about_sahana():
    "About Sahana page provides details on component versions."
    import sys
    python_version=sys.version
    web2py_version=open(apath('../VERSION'),'r').read()[8:]
    sahana_version=open(apath('sahana/VERSION'),'r').read()
    return dict(module_name=module_name,modules=modules,options=options,python_version=python_version,sahana_version=sahana_version,web2py_version=web2py_version)

# Administration Page
def admin():
    """Administration Page.
    For now just redirect to appadmin's site view.
    """
    redirect(URL(r=request,a='admin',c='default',f='site'))
    
# Database Page
def database():
    """Database Page.
    Redirect to appadmin.
    """
    redirect(URL(r=request,c='appadmin',f='index'))
    
# Import Data
@auth.requires_membership('Administrator')
def import_data():
    "Import data via POST upload to CRUD controller."
    title=T('Import Data')
    return dict(module_name=module_name,modules=modules,options=options,title=title)

# Export Data
@auth.requires_login()
def export_data():
    "Export data via CRUD controller."
    title=T('Export Data')
    return dict(module_name=module_name,modules=modules,options=options,title=title)

# Test Page
@auth.requires_membership('Administrator')
def test():
    """Test Page.
    Redirect to Selenium TestRunner.
    """
    redirect(URL(r=request,c='static',f='selenium',args=['core','TestRunner.html'],vars=dict(test='../tests/TestSuite.html',auto='true',resultsUrl=URL(r=request,c='default',f='handleResults'))))
    
def handleResults():
    """Process the POST data returned from Selenium TestRunner.
    The data is written out to 2 files.  The overall results are written to 
    date-time-browserName-metadata.txt as a list of key: value, one per line.  The 
    suiteTable and testTables are written to date-time-browserName-results.html.
    """
    
    if not request.vars.result:
        # No results
        return
    
    # Read in results
    result = request.vars.result
    totalTime = request.vars.totalTime
    numberOfSuccesses = request.vars.numTestPasses
    numberOfFailures = request.vars.numTestFailures
    numberOfCommandSuccesses = request.vars.numCommandPasses
    numberOfCommandFailures = request.vars.numCommandFailures
    numberOfCommandErrors = request.vars.numCommandErrors

    suiteTable = ''
    if request.vars.suite:
        suiteTable = request.vars.suite
    
    testTables = []
    testTableNum = 1
    while request.vars['testTable.%s' % testTableNum]:
        testTable = request.vars['testTable.%s' % testTableNum]
        testTables.append(testTable)
        testTableNum += 1
        try:
            request.vars['testTable.%s' % testTableNum]
            pass
        except:
            break
    
    # Unescape the HTML tables
    import urllib
    suiteTable = urllib.unquote(suiteTable)
    testTables = map(urllib.unquote, testTables)

    # We want to store results separately for each browser
    browserName = getBrowserName(request.env.http_user_agent)
    date=str(request.now)[:-16]
    time=str(request.now)[11:-10]
    time=time.replace(':','-')

    # Write out results
    outputDir = os.path.join(request.folder,'static','selenium','results')
    metadataFile = '%s-%s-%s-metadata.txt' % (date,time,browserName)
    dataFile = '%s-%s-%s-results.html' % (date,time,browserName)
    
    #xmlText = '<selenium result="' + result + '" totalTime="' + totalTime + '" successes="' + numberOfCommandSuccesses + '" failures="' + numberOfCommandFailures + '" errors="' + numberOfCommandErrors + '" />'
    f = open(os.path.join(outputDir, metadataFile), 'w')
    for key in request.vars.keys():
        if 'testTable' in key or key in ['log','suite']:
            pass
        else:
            print >> f, '%s: %s' % (key, request.vars[key])
    f.close()

    f = open(os.path.join(outputDir, dataFile), 'w')
    print >> f, suiteTable
    for testTable in testTables:
        print >> f, '<br/><br/>'
        print >> f, testTable
    f.close()
    
    message = DIV(P('Results have been successfully posted to the server here:'),
        P(A(metadataFile,_href=URL(r=request,c='static',f='selenium',args=['results',metadataFile]))),
        P(A(dataFile,_href=URL(r=request,c='static',f='selenium',args=['results',dataFile]))))
    
    response.view='display.html'
    title=T('Test Results')
    return dict(module_name=module_name,modules=modules,options=options,title=title,item=message)
    
