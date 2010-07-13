# coding: utf8
# try something like
module = 'importer'
# Current Module (for sidebar title)
module_name = 'Spreadsheet importer' 

response.menu_options = [
    [
	    T('Spreadsheet'), False, URL(r=request, f='spreadsheet/create')
    ],
    [
	    T('Google Documents'), False, URL(r=request, f='googledoc')
    ]
]

importer=local_import("importer")

def index(): 
    return dict(module_name=module_name)
def googledoc():
    return dict(module_name=module_name)


def spreadsheet():
    crud.settings.create_onaccept = lambda form : redirect(URL(r=request, c="importer", f="spreadsheetview")) 
    return shn_rest_controller(module,'slist')

def spreadsheetview():
    
    k=db(db.importer_slist.id>0).select().last()
    k=k.Path;
    str=importer.pathfind(k)
    str=request.folder+str
    temp=importer.removerowcol(str)
    #appname=request.application
    v=importer.json(str,request.folder)
    #fields=shn_get_writecolumns(
    return dict(ss=v)

def slist():
    return shn_rest_controller(module,'slist',listadd=False)

'''def recvdata():
    spreadsheet=request.body
    tree=s3xrc.xml.json2tree(spreadsheet)
    s3xrc.import_xml(tree=tree,prefix=request.args[0],name=request.args[1],id=None)
    return dict(spreadsheet=spreadsheet)'''
