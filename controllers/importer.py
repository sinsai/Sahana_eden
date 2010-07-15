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

gd_client = importer.gdata.spreadsheet.service.SpreadsheetsService()

def index(): 
    return dict(module_name=module_name)

def googledoc():
    next = 'http://' + request.env.http_host + '/' + \
		    request.application + '/importer/gettoken'
    scope = 'https://spreadsheets.google.com/feeds/'
    secure = False
    sessionval = True
    url2token = gd_client.GenerateAuthSubURL(next, scope, \
		    secure, sessionval)
    return dict(module_name=module_name,auth_url=url2token)	


def gettoken():
    #gd_client = importer.gdata.spreadsheet.service.SpreadsheetsService()
    authsub_token = request.vars['token']
    authsub_token.replace('\r','')
    authsub_token.replace('\n','')
    gd_client.SetAuthSubToken(authsub_token)
    '''Google documentation is outdated on this, gd_client.auth_token doesn't work'''
    
    user_spreadsheets = getspreadsheetlist()
    return dict(module_name=module_name,k=user_spreadsheets)

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
    
def getspreadsheetlist():		
	'''
	Get list of spreadsheets from Google Docs
	client is the gdata spreadsheets client
	'''
	l=[]
	feed=gd_client.GetSpreadsheetsFeed()
	for i, entry in enumerate(feed.entry):
		if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
			l.append('%s %s\n' % (entry.title.text, entry.content.text))
		elif isintance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
	 		l.append('%s %s %s' %(i, entry.title.text. entry.content.text))
	        	for key in entry.custom:
	        		l.append(' %s: %s' % (key, entry.custom[key].text))
	        else:
			l.append('%s %s\n' % (i,entry.title.text))
	f=file("/home/shikhar/Desktop/test.txt")
	f.write(repr(l))
	f.close()
	return l
'''
def allfields(prefix,name):
    table = prefix+'_'+name
    fields = db.table.fields
    #remove first seven field names
    fields = fields[8:]
'''

    

'''def recvdata():
    spreadsheet=request.body
    tree=s3xrc.xml.json2tree(spreadsheet)
    s3xrc.import_xml(tree=tree,prefix=request.args[0],name=request.args[1],id=None)
    return dict(spreadsheet=spreadsheet)'''
