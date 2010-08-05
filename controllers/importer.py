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
    gd_client = importer.gdata.spreadsheet.service.SpreadsheetsService()
    getvars=repr(request.get_vars)
    auth_url='http://'+request.env.http_host+request.url+'?auth_sub_scopes='+request.get_vars['auth_sub_scopes']+'&token='+request.get_vars['token']
    f = file("/home/shikhar/Desktop/abc.txt","wb")
    f.write(auth_url)
    f.close() 
    authsub_token = importer.gdata.auth.extract_auth_sub_token_from_url(auth_url)
    
    authsub_token = importer.gdata.auth.AuthSubTokenFromUrl(auth_url) 
    #gd_client.token_store.add_token(authsub_token)
    gd_client.token_store.add_token(request.get_vars['token'])
    user_sreadsheets = gd_client.AuthSubTokenInfo()
    gd_client.UpgradeToSessionToken()
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
    f = file("/home/shikhar/Desktop/abc.txt","wb")
    from StringIO import StringIO
    spreadsheet_json = StringIO(spreadsheet)
    f.write("The recd JSON is " + repr(spreadsheet_json.read()))
    spreadsheet_json.seek(0)
    #j = json.load(spreadsheet_json,encoding = 'ascii')
    j = json.loads(spreadsheet)
    f.write("\n"+repr(len(j['spreadsheet']))+"\n")
    similar_rows = []
    importable_rows = []
    if j.has_key('header_row'):
         j['spreadsheet'].pop(j['header_row'])
    j['rows'] -= 1
    for x in range(0,len(j['spreadsheet'])):
	for y in range(x+1,len(j['spreadsheet'])):
 	    k = importer.jaro_winkler_distance_row(j['spreadsheet'][x],j['spreadsheet'][y])
	    if k is True:
	       similar_rows.append(j['spreadsheet'][x])
	       similar_rows.append(j['spreadsheet'][y])
	    else:
	       pass 
    session.similar_rows = similar_rows
    for k in j['spreadsheet']:
        if k in similar_rows:
	    j['spreadsheet'].remove(k)
	    j['rows'] -= 1
    i=k=0
    send_dict = {}
    resource = j['resource'].encode('ascii')
    send_dict[resource] = []
    while (i < j['rows']):
	res = {}
	k = 0
	while (k < j['columns']):
	    if ' --> ' in j['map'][k][2]:
		field,nested_resource,nested_field = j['map'][k][2].split(' --> ')
		field = "$k_" + field
		nr = nested_resource
		nested_resource= "$_" + nested_resource
		if res.has_key(field) is False: 
		   res[field] = {}
		   res[field]['@resource'] = nr 
		   res[field][nested_resource] = [{}]
		res[field][nested_resource][0][nested_field] = j['spreadsheet'][i][k].encode('ascii')
		k += 1
		#f.write("res-->" + repr(res) + "\n")
		continue
	    if "opt_" in j['map'][k][2]:
		res[j['map'][k][2].encode('ascii')]['@value'] = j['spreadsheet'][i][k].encode('ascii')
	    	res[j['map'][k][2].encode('ascii')]["$"] = j['spreadsheet'][i][k].encode('ascii')
	    else:
		res[j['map'][k][2].encode('ascii')] = j['spreadsheet'][i][k].encode('ascii')
		if j['map'][k][2].encode('ascii') == 'comments':
			res[j['map'][k][2].encode('ascii')] = j['map'][k][1] + '-->' + j['spreadsheet'][i][k].encode('ascii')
	    res['@modified_at'] = j['modtime']
	    k += 1
	send_dict[resource].append(res)
	i += 1
	
    word = json.dumps(send_dict[resource])
    #f.write("hihih" + repr(send_dict))
    #Removing all white spaces and newlines in the JSON
    new_word = ""
    cntr = 1
    for i in range(0,len(word)):
   	if word[i] == "\"":
           cntr = cntr + 1
      	   cntr = cntr % 2
        if cntr == 0:
           new_word += word[i]
        if cntr == 1:
           if word[i] == " " or word[i] == "\n":
	      continue
           else:
    	      new_word += word[i] 
     #new_word is without newlines and whitespaces	  
    new_word  = "{\"$_" + resource + "\":"+ new_word + "}"
    #added resource name
    f.write("The outgoing json is " + "\n\n" + new_word)
    send = StringIO(new_word)
    tree = s3xrc.xml.json2tree(send)
    prefix, name = resource.split('_')
    res = s3xrc.resource(prefix, name)
    if res.import_xml(source = tree,ignore_errors = True):
        session.import_success = 1 
    else:
        f.write("IMPORT DID NOT SUCCEED")
    	session.import_success = 0
    	incorrect_rows = []
    	correct_rows = []
    	returned_tree = tree
    	returned_json = s3xrc.xml.tree2json(returned_tree)
    	returned_json = returned_json.encode('ascii')
    	returned_json = json.loads(returned_json,encoding = 'ascii')
    	for resource_name in returned_json:
		for record in returned_json[resource_name]:
		     if '@error' in repr(record):
			incorrect_rows.append(record)
		     else:
			f.write("\n\n\n" + repr(record))
			correct_rows.append(record)
			
    	correct_rows_send = {}
    	correct_rows_send['$_'+prefix+'_'+name] = correct_rows
    	f.write("The correct rows are " + repr(incorrect_rows))
    	for k in incorrect_rows:
		 del k['@modified_at']
    	send_json = json.dumps(correct_rows_send)
    	send_json = StringIO(send_json)
    	tree = s3xrc.xml.json2tree(send_json)
	if len(correct_rows) and res.import_xml(tree):
	    f.write("RE_IMPORT SUCCEEDED\n\n\n")
	else:
	    f.write("DID NOT SUCCEED AGAIN")
    	session.fields = incorrect_rows[0].keys()
    	for i in range(0,len(session.fields)):
       	    session.fields[i]=session.fields[i].encode('ascii')
    	f.write(repr(session.fields)+"\n\n\n")
    	session.import_rows = len(incorrect_rows)
    	for record in incorrect_rows:
       	   for field in record:
               if '@error' in record[field]:
                  f.write(repr(record[field]))
		  record[field] = '*_error_*' + record[field]['@error'] + '. You entered ' + record[field]['@value']
	       else:
	          f.write("in else " + repr(record[field]))
	          record[field] = record[field]['@value'] 
    	f.write("These rows are incorrect "+repr(incorrect_rows))
    	incorrect_rows = json.dumps(incorrect_rows,ensure_ascii=True)
    	session.invalid_rows = incorrect_rows
    	session.import_success = 0
    	session.import_columns = j['columns']
    	session.import_map = json.dumps(j['map'],ensure_ascii=True)
    	session.import_resource = resource.encode('ascii') 
    f.close()	
    return dict(module_name = module_name)

def re_import():
	return dict(module_name=module_name)

def similar_rows():
    return dict(module_name = module_name)
