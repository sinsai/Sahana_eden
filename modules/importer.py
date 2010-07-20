#!/usr/bin/env python 
# coding: utf8 
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
# request, response, session, cache, T, db(s) 
# must be passed and cannot be imported!

#For google spreadsheets
try:
	from xml.etree import ElementTree
	import gdata.spreadsheet.service
	import gdata.service
	import atom.service
	import gdata.spreadsheet
	import atom

except ImportError:
	print >> sys.stderr, "WARNING: %s:GData Spreadsheets library is not installed" % __name__

try:
	from xlrd import *
except ImportError:
	print >> sys.stderr, "WARNING: %s: XLRD not installed" % __name__

import os
def removerowcol(path_to_file):
    
    spreadsheet=list()
    wb=open_workbook(path_to_file)
    s=wb.sheet_by_index(0)  
    for r in range(0,s.nrows):
        l=list()
        for c in range(0,s.ncols):
            l.append(s.cell(r,c).value)
        check=0
        for k in range(0,len(l)):
            if l[k] is not '':
                check+=1
        if check is not 0:
            spreadsheet.append(l)
        l=list()
    new_col=len(spreadsheet[0])
    new_row=len(spreadsheet)
    empty_column=list()
    for x in range(0,new_col):
        l=list()
        for y in range(0,new_row):
            l.append(spreadsheet[y][x])
        ck=0
        for k in l:
            if k is not '':
                ck+=1
        if ck is 0:
            empty_column.append(x)
    #removing empty columns
    new_spreadsheet=list()
    for x in range(0,new_row):
        l=list()
        for y in range(0,new_col):
            if y not in empty_column:
                l.append(spreadsheet[x][y])
        new_spreadsheet.append(l)
    return new_spreadsheet

def json(path_to_file,appname):
    spreadsheet=removerowcol(path_to_file)
    nrow=len(spreadsheet)
    ncol=len(spreadsheet[0])
    json="{"
    json+="\"rows\": %i,\n" % nrow
    json+="\"columns\": %i,\n" %ncol
    json+="\"data\": [\n"
    for x in range(0,nrow):
        json+="{\n"
        json+="\t\"id\":%i," % (x)
        for y in range(0,ncol):
            temp="\n\t\"column%i\":" % y
            try:
		cell=str(spreadsheet[x][y])    
            	cell=cell.replace("\n","")
		temp+="\""+cell+"\""
            except:
            	temp+="\"\""
            if(y is not ncol-1): 
                temp+=","
            json+=temp
        json+="\n\t}"
        if x is not nrow-1:
            json+="\n\t,"


    json+="\n]}"
    '''jsonfile=open("/%s/static/test1.json" % appname,"wb")
    jsonfile.write(json)
    jsonfile.close()
    '''
    return json

def pathfind(filename):
    str = os.path.join("uploads",filename)
    return str

def getspreadsheetlist(client):		
	'''
	Get list of spreadsheets from Google Docs
	client is the gdata spreadsheets client
	'''
	l=[]
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
