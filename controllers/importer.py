# coding: utf8
# try something like
module = 'importer'
# Current Module (for sidebar title)
module_name = 'Spreadsheet importer' 

import gluon.contrib.simplejson as json

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
    scope = 'https://spreadsheets.google.com/feeds'
    secure = True
    sessionval = True
    url2token = gd_client.GenerateAuthSubURL(next, scope, \
		    secure=secure, session = sessionval)
    return dict(module_name=module_name,auth_url=url2token)	


def gettoken():
    #gd_client = importer.gdata.spreadsheet.service.SpreadsheetsService()
    getvars=repr(request.get_vars)
    auth_url='http://'+request.env.http_host+request.url+'?auth_sub_scopes='+request.get_vars['auth_sub_scopes']+'&token='+request.get_vars['token']
    f = file("/home/shikhar/Desktop/abc.txt","wb")
    f.write(auth_url)
    f.close() 
    #authsub_token = importer.gdata.auth.extract_auth_sub_token_from_url(auth_url)
    
    authsub_token = importer.gdata.auth.AuthSubTokenFromUrl(auth_url) 
    #gd_client.token_store.add_token(authsub_token)
    user_sreadsheets = gd_client.AuthSubTokenInfo()
    #gd_client.UpgradeToSessionToken()
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
	return l

def import_spreadsheet():
    spreadsheet = request.body.read()
    #tree=s3xrc.xml.json2tree(spreadsheet)
    #s3xrc.import_xml(tree=tree,prefix=request.args[0],name=request.args[1],id=None)
    f = file("/home/shikhar/Desktop/abc.txt","wb")
    from StringIO import StringIO
    f.write(spreadsheet)
    spreadsheet_json = StringIO(spreadsheet)
    f.write("\n\n\n\n"+spreadsheet_json.read())
    spreadsheet_json.seek(0)
    j = json.load(spreadsheet_json)
    i=k=0
    resource = j['resource']
    resource = resource.encode('ascii')
    send_dict={};
    send_dict[resource]=[]
    while (i < j['rows']):
	temp = {}
	k = 0
	while (k < j['columns']) :
            temp[j['map'][k][2]] = {}
	    if "opt_" in j['map'][k][2]:
		    temp[j['map'][k][2]]["@value"] = j['spreadsheet'][i][k].encode('ascii')
	    	    temp[j['map'][k][2]]["$"]=j['spreadsheet'][i][k].encode('ascii')
	    else:
	    	temp[j['map'][k][2].encode('ascii')]=j['spreadsheet'][i][k].encode('ascii')
	    k+=1
	    temp["@modified_on"] = j['modtime']
        send_dict[resource].append(temp)
	i+=1
    word = json.dumps(send_dict)
    new_word = ""
    k = 1
    for i in range(0,len(word)):
	if word[i] == "\"":
	    k = k + 1
	    k = k % 2
	if k == 0:
	    new_word += word[i]
	if k == 1:
	    if word[i] == " " or word[i] == "\n":
	 	continue
	    else:
	        new_word += word[i]
    f.write(new_word)
    send = StringIO(new_word)
    f.write("\n\n\n\n"+send.read())
    send.seek(0)
    tree = s3xrc.xml.json2tree(send)
    symbol, prefix, name = resource.split('_')
    res = s3xrc.resource(prefix, name)
    if res.import_xml(source = tree, id = None):#, resource = resource, push_limit = j['rows']):
	    session.import_success = 1 
    else:
	    incorrect_rows = []
	    correct_rows = []
	    success = False
	    returned_tree = tree
	    returned_json = s3xrc.xml.tree2json(returned_tree)
	    returned_json = returned_json.encode('ascii')
	    returned_json = json.loads(returned_json)
	    #f.write(repr(returned_json[resource]))
	    '''for i in returned_json:
		    #f.write(repr(i)+"\n")
		    #for j in returned_json[i]:
		#	    f.write("-------------------------\n")
			    for k in range(0,len(returned_json[i])):
			    	#f.write(repr(returned_json[i][k])+"\n")
				for j in returned_json[i][k]:
					#f.write("--------->"+j)
					for l in returned_json[i][k][j]:
						if '@error' in l:
							#f.write("\n-> "+repr(returned_json[i][k][j])+" <-\n")
							f.write("-------->>>>>"+repr(k)+"<<<<<------\n")
							incorrect_rows.append(returned_json[i][k])
						else:
							correct_rows.append(returned_json[i][k])
	    '''
	    for i in returned_json.keys():
		    for k in range(0,len(returned_json[i])):
	    		   if '@error' in repr(returned_json[i][k]):
				   f.write("Error flagged at "+repr(k))
	    			   incorrect_rows.append(returned_json[i][k])
		           else:
				   correct_rows.append(returned_json[i][k])
	    #f.write("\nCorrect rows -> "+repr(correct_rows))
	    correct_rows_send={}
	    correct_rows_send[resource]=correct_rows
	    f.write("And the incorrect rows are...\n")
	    #f.write(repr(incorrect_rows))
	    for k in incorrect_rows:
		    del k['@modified_on']
	    send_json = json.dumps(correct_rows_send)
	    send_json = StringIO(send_json)
	    tree = s3xrc.xml.json2tree(send_json)
	    s3xrc.import_xml(tree = tree, id = None, prefix = prefix, name = name)
	    json_test = s3xrc.xml.tree2json(tree)
	    session.fields = incorrect_rows[0].keys()
	    #session.fields.remove(u'@modified_on')
	    for i in range(0,len(session.fields)):
		    session.fields[i]=session.fields[i].encode('ascii')
	    f.write(repr(session.fields))
	    session.import_rows = len(incorrect_rows)
	    for record in incorrect_rows:
		    for field in record.keys():
			    if '@error' in record[field].keys():
				    record[field] = record[field]['@error']
				    record[field] = "*_error_*" + record[field]
			    else:
				    record[field] = record[field]['@value']
	    #f.write("\nTHE RETURNED JSON IS --->\n"+json.dumps(json_test))
	    incorrect_rows = json.dumps(incorrect_rows,ensure_ascii=True)
	    session.invalid_rows = incorrect_rows
	    session.import_success = 0
	    session.import_columns = j['columns']
	    session.import_map = json.dumps(j['map'],ensure_ascii=True)
	    session.import_resource = resource.encode('ascii') 
	    #session.columns = j['columns']
    f.close()	
    return dict(success=success,spreadsheet=incorrect_rows)

def re_import():
	return dict(module_name=module_name)
