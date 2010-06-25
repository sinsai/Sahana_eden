# coding: utf8
# try something like
module = 'importer'
# Current Module (for sidebar title)
module_name = 'Spreadsheet importer' 

response.menu_options = [
    [T('Spreadsheet'), False, URL(r=request, f='spreadsheet')
    ],
    [T('Google Documents'), False, URL(r=request, f='googledoc')]
]

exec('import applications.%s.modules.importer as importer' % (request.application))
#from applications.eden1.modules.importer import *

def index(): 
    return dict(module_name=module_name)
def googledoc():
    return dict(module_name=module_name)


def spreadsheet():
    return shn_rest_controller(module,'slist')
    
def slist():
    
    q=db.importer_slist.id>0
    s=db(q)
    initid=0
    rows=s.select()
    for row in rows:
        if(row.id>initid):
            initid=row.id
    k=db.executesql("select Path from importer_slist where id==%s;"%(initid))
    
    str=importer.pathfind(k)
    str=request.folder+str
    temp=importer.removerowcol(str)
    appname=request.application
    k=importer.json(str,request.folder);
    return dict(result=str,ss=temp,folder=request.folder)#,spreadsheet=spreadsheet)

def recvdata():
    formdata=request.body.read()
    loc=request.folder
    loc+="/static/finaldata.txt"
    f=open(loc,"wb")
    f.write(formdata)
    return dict(formdata=formdata)
