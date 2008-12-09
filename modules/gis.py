"""
This file was developed by Fran Boon as a web2py extension.
This file is released under the BSD license (you can include it in bytecode compiled web2py apps as long as you acknowledge the author). web2py (required to run this file) is released under the GPLv2 license.
"""

from gluon.storage import Storage
from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.contrib.markdown import WIKI
try: from gluon.contrib.gql import SQLTable
except ImportError: from gluon.sql import SQLTable

from applications.sahana.modules.t2 import T2

class T2GIS(T2):

	def create_layer(self,table,next=None,vars={},onaccept=None):
		"""
		gis.create_layer(db.table,next='index',flash='done',vars={},onaccept=None)
		makes a SQLFORM and processing logic for table. Upon success it 
		redrects to "next" and flashes "flash". 
		vars are additional variables that should be placed in the form.
		onaccept=lambda form: pass is a callback executed after form accepted
		"""
		request,response,session,cache,T,db=self._globals()
		if not next: next=request.function
		fields=self._filter_fields(table.get('exposes',table.fields))
		labels=self._get_labels(table)
		col3=self._get_col3(table)
		form=SQLFORM(table,fields=fields,labels=labels,showid=False,col3=col3,_class='t2-create')
		self._stamp(table,form,create=True)
		if type(vars)==type(lambda:0): vars(form)
		else: form.vars.update(vars)
		if form.accepts(request.vars,session):
			session.flash=self.messages.record_created
			if onaccept: onaccept(form)
			self.redirect(f=next.replace('[id]',str(form.vars.id)))
		return form

	def update_layer(self,table,query=None,next=None,deletable=True,vars={},onaccept=None,ondelete=None):
		"""
		gis.update_layer(db.table,query,next='index',flash='done',vars={},onaccept=None,ondelete=None)
		makes a SQLFORM and processing logic for table and the record 
		identified by the query. If no query: query=table.id==t2.id
		Upon success it redrects to "next" and flashes "flash". 
		vars are additional variables that should be placed in the form.
		onaccept=lambda form: pass is a callback executed after form accepted
		"""
		request,response,session,cache,T,db=self._globals()
		if not next: next='%s/[id]'%request.function
		if query:
			rows=table._db(query).select(table.ALL,limitby=(0,1))
		else:
			id=self.id or self._error()
			rows=table._db(table.id==id).select(table.ALL,limitby=(0,1))
		if not rows: self._error()
		fields=self._filter_fields(table.get('exposes',table.fields))
		labels=self._get_labels(table)
		col3=self._get_col3(table)
		self.record=record=rows[0]
		hidden={'modified_on__original':str(record.get('modified_on',None))}
		form=SQLFORM(table,record,upload=URL(r=request,f='download'),deletable=deletable,fields=fields,labels=labels,showid=False,col3=col3,_class='t2-update',hidden=hidden)
		self._stamp(table,form)
		if type(vars)==type(lambda:0): vars(form)
		else: form.vars.update(vars)
		if request.vars.modified_on__original and request.vars.modified_on__original!=hidden['modified_on__original']:
			session.flash=self.messages.record_was_altered
			redirect(self.action(args=request.args))
		if form.accepts(request.vars,session):
			form.old=record
			session.flash=self.messages.record_modified
			if request.vars.delete_this_record:
				session.flash=self.messages.record_modified
				for f in table.fields:
					if table[f].type=='upload' and table[f].uploadfield is True:
						name=os.path.join(request.folder,'uploads',record[f])
						if os.path.exists(name): os.unlink(name)
				if ondelete:                    
					ondelete(form)
			elif onaccept:                
				onaccept(form)            
			self.redirect(f=next.replace('[id]',str(form.vars.id)))
		return form

	def delete_layer(self,table,query=None,next=None):
		"""
		Deletes the result of the query. If no query: query=table.id==t2.id
		"""
		request,response,session,cache,T,db=self._globals()
		if not next: next=request.function
		if not query:
			id=self.id or self._error()  
			query=table.id==id
		table._db(query).delete()
		if next: self.redirect(f=next,flash=self.messages.record_deleted)
		return True

	def display_layer(self,table,query=None):
		"""
		Shows one record of table for query
		Also shows associated tables
		"""
		rows=self.read(table,query)
		request,response,session,cache,T,db=self._globals()
		if not rows: self._error()
		self.record=record=rows[0]
		if table.get('display',None): return table.display(record)
		fields=table.get('displays',table.fields)
		labels=self._get_labels(table)
		items=[]
		for field in fields:
			label=labels[field] if labels.has_key(field) else self._capitalize(field)
			value=record[field]
			if hasattr(table[field],'display'):
				value=table[field].display(value)
			elif table[field].type=='blob':
				continue
			elif table[field].type=='upload' and value and value[-4:].lower() in self.IMAGE_EXT:
				u=URL(r=request,f='download',args=[value])
				k='zoom-%s-%s-%i' % (table,field,record.id)
				value=DIV(A(IMG(_src=u,_height=100),_class='zoom',_href='#'+k),DIV(IMG(_src=u,_width=600),_id=k,_class='hidden'))
			elif table[field].type=='upload' and value:
				u=URL(r=request,f='download',args=[value])
				value=A('download',_href=u)
			items.append(TR(LABEL(label,':'),value))
		return DIV(TABLE(*items),_class='t2-display')

	def itemize_layer(self,*tables,**opts):
		"""
		Lists all records from tables. 
		opts include: query, orderby, nitems
		where nitems is items per page;
		"""
		### FIX - ADD PAGINATION BUTTONS
		import re
		request,response,session,cache,T,db=self._globals()
		if not len(tables): raise SyntaxError
		query=opts.get('query',None)
		orderby=opts.get('orderby',None)
		nitems=opts.get('nitems',25)
		g=re.compile('^(?P<min>\d+)$').match(request.vars.get('_page',''))
		page=int(g.group('min')) if g else 0
		limitby=opts.get('limitby',(page*nitems,page*nitems+nitems))
		if not query:
			query=tables[0].id>0
		rows_count=tables[0]._db(query).count()
		rows=tables[0]._db(query).select(orderby=orderby,limitby=limitby,*[t.ALL for t in tables])
		if not rows: return 'No data'
		def represent(t,r):
			try: return t.represent(r)
			except KeyError: return '[#%i] %s' % (r.id,r[t.fields[1]])
		nav=[TR(TD(A('[prevous page]',_href=self.action(args=request.args,vars={'_page':page-1})) if page else '',A('[next page]',_href=self.action(args=request.args,vars={'_page':page+1})) if page*nitems+len(rows)<rows_count else ''))]
		if len(tables)==1:
			return TABLE(_class='t2-itemize',*nav+[TR(represent(tables[0],row)) for row in rows]+nav)
		else:
			return TABLE(_class='t2-itemize',*nav+[TR(*[represent(table,row[table._tablename]) \
				for table in tables]) for row in rows]+nav)

	def search_layer(self,*tables,**opts):    
		"""
		Makes a search widgets to search records in tables.
		opts can be query, orderby, limitby
		"""
		request,response,session,cache,T,db=self._globals()
		if self.is_gae and len(tables)!=1: self._error()
		def is_integer(x):
			try: int(x)
			except: return False
			else: return True
		def is_double(x):
			try: float(x)
			except: return False
			else: return True
		from gluon.sqlhtml import form_factory
		options=[]
		orders=[]
		query=opts.get('query',None)
		def option(s): return OPTION(s if s[:3]!='t2_' else s[3:],_value=s)
		for table in tables:
			for field in table.get('displays',table.fields):
				tf=str(table[field])
				t=table[field].type
				if not self.is_gae and (t=='string' or t=='text'): 
					options.append(option('%s contains' % tf))
					options.append(option('%s starts with' % tf))
				if t!='upload':
					options.append(option('%s greater than' % tf))
				options.append(option('%s equal to' % tf))
				options.append(option('%s not equal to' % tf))
				if t!='upload':
					options.append(option('%s less than' % tf))
				orders.append(option('%s ascending' % tf))
				orders.append(option('%s descending' % tf))
		form=FORM(SELECT(_name='cond',*options),INPUT(_name='value',value=request.vars.value or '0'),' ordered by ',
                  SELECT(_name='order',*orders),' refine? ',
                  INPUT(_type='checkbox',_name='refine'),
                  INPUT(_type='submit'))
		if form.accepts(request.vars,formname='search'):
			db=tables[0]._db
			p=(request.vars.cond,request.vars.value,request.vars.order)
			if not request.vars.refine: session.t2.query=[]
			session.t2.query.append(p)
			orderby,message1,message2=None,'',''
			prev=[None,None,None]        
			for item in session.t2.query:
				c,value,order=item
				if c!=prev[0] or value!=prev[1]:
					tf,cond=c.split(' ',1)                
					table,field=tf.split('.')
					f=db[table][field]
					if (f.type=='integer' or f.type=='id') and not is_integer(value):
						session.flash=self.messages.invalid_value
						self.redirect(args=request.args)
					elif f.type=='double' and not is_double(value):
						session.flash=self.messages.invalid_value
						self.redirect(args=request.args)
					elif cond=='contains':
						q=f.lower().like('%%%s%%' %value.lower())
					elif cond=='starts with':
						q=f.lower().like('%s%%' % value.lower())
					elif cond=='less than': 
						q=f<value
					elif cond=='equal to':
						q=f==value
					elif cond=='not equal to':
						q=f!=value
					elif cond=='greater than': 
						q=f>value
					query=query&q if query else q
					message1+='%s "%s" AND ' % (c,value)
				if order!=prev[2]:
					p=None
					c,d=request.vars.order.split(' ')
					table,field=c.split('.')
					if d=='ascending': p=f
					elif d=='descending': p=~f
					orderby=orderby|p if orderby else p
					message2+='%s '% order
				prev=item
			message='QUERY %s ORDER %s' % (message1,message2)
			return DIV(TABLE(TR(form),TR(message),TR(self.itemize(query=query,orderby=orderby,*tables))),_class='t2-search')
		else:
			session.t2.query=[]
		return DIV(TABLE(TR(form)),_class='t2-search')
