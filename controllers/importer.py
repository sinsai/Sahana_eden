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
    return shn_rest_controller(module,'slist')
    
def slist():
    
    k=db(db.importer_slist.id>0).select().last()
    k=k.Path;
    str=importer.pathfind(k)
    str=request.folder+str
    temp=importer.removerowcol(str)
    #appname=request.application
    v=importer.json(str,request.folder)
    return dict(ss=v)

def recvdata():
    formdata=request.body.read()
    loc=request.folder
    loc+="/static/finaldata.json"
    f=open(loc,"wb")
    f.write(formdata)
    return dict(formdata=formdata)
