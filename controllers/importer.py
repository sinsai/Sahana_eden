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
    return dict(ss=v)
def slist():
    return shn_rest_controller(module,'slist',listadd=False)
def recvdata():
    formdata=request.body.read()
    loc=request.folder
    loc+="/static/finaldata.json"
    f=open(loc,"wb")
    f.write(formdata)
    return dict(formdata=formdata)
