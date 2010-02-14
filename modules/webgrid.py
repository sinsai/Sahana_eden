#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
   WebGrid for web2py 
   Developed by Nathan Freeze (Copyright � 2009)
   Email <nathan@freezable.com>
   License: GPL v2
   
   This file contains code to build a table that supports
   paging, sorting, editing and totals.
"""

from gluon.sql import Rows, Field, Set
from gluon.sqlhtml import *
from gluon.html import *
from gluon.storage import *

class WebGrid(object):    
    def __init__(self, crud, name=None, datasource=None):
        self.crud = crud
        self.environment = crud.environment
        self.name = name
        if not self.name:
            self.name = self.crud.environment.request.function

        self.datasource = datasource
        self.crud_function = 'data'
        self.download_function = 'download'
        self.css_prefix = self.name
        self.id = 'list'
        
        self.messages = Messages(self.crud.environment.T)
        self.messages.confirm_delete = 'Are you sure?'
        self.messages.no_records = 'No records'
        self.messages.add_link = '[add %s]'
        self.messages.page_total = "Total:"
        
        self.action_links = ['view', 'edit', 'delete']
        self.action_headers = ['view', 'edit', 'delete'] 
               
        self.field_headers = self.fields = self.totals = []     
        self.enabled_rows = ['header', 'pager', 'totals', 'footer', 'add_links']
        self.allowed_vars = ['pagesize', 'pagenum', 'sortby', 'ascending', 'groupby', 'totals']
        
        self.pagenum = self.pagecount = self.pagesize = 0
        self.sortby = self.groupby = self.page_total = None
        
        self.view_link = self.edit_link = self.delete_link = self.add_links = None
        self.action_header = self.header = self.footer = self.pager = self.datarow = None
        self.ascending = False
    
    def get_header(self, c):
        try:
            return self.field_headers[self.fields.index(c)]
        except:
            return c

    def get_value(self, f, r):
        (_t, _f) = f.split('.')
        v = r[_t][_f] if self.joined else r[_f]
        return v
    
    def __call__(self):
           
        request = self.crud.environment.request
        db = self.crud.db
        datasource = self.datasource
        
        # Set defaults
        vars = request.vars
        if vars.pagesize and 'pagesize' in self.allowed_vars: 
            self.pagesize = int(vars.pagesize)
        if not self.pagesize:
            self.pagesize = 0
        
        if vars.pagenum and 'pagenum' in self.allowed_vars : 
            self.pagenum = int(vars.pagenum)
        if not self.pagenum:
            self.pagenum = 1
        
        if vars.sortby and 'sortby' in self.allowed_vars:
            self.sortby = vars.sortby
        
        if vars.groupby and 'groupby' in self.allowed_vars: 
            self.groupby = vars.groupby
        
        if vars.totals and 'totals' in self.allowed_vars:
            self.totals = vars.totals
        
        if vars.ascending and 'ascending' in self.allowed_vars:
            self.ascending = vars.ascending == "True"
        
        page = sortby = groupby = None
        # Build limitby
        if self.pagesize > 0:
            pagenum = self.pagenum - 1
            page = (self.pagesize * pagenum, 
                    self.pagesize * pagenum + self.pagesize)
        else: self.pagenum = 0
 
        # Build sortby
        if self.sortby:
            if isinstance(self.sortby, Field):
                (ts, fs) = (self.sortby._tablename, self.sortby.name)
            else:
                (ts, fs) = self.sortby.split('.')
            if self.ascending:
                sortby = db[ts][fs]
            else:
                sortby = ~db[ts][fs]
            
        if self.groupby: 
            if isinstance(self.groupby, Field):
                (tg, fg) = (self.groupby._tablename, self.groupby.name)
            else:
                (tg, fg) = self.groupby.split('.')
            groupby = db[tg][fg]
           
        # Get rows
        rows = total = None        
        if isinstance(datasource, Rows):            
            rows = datasource
            total = len(rows)     
            joined = len(set(map(lambda c: c.split('.')[0], rows.colnames))) > 1  
            if sortby and joined:
               rows = rows.sort(lambda row: row[ts][fs], reverse=self.ascending)
            elif sortby:
               rows = rows.sort(lambda row: row[fs], reverse=self.ascending)
            if self.pagesize > 0:
                rows = rows[page[0]:page[1]]            
        elif isinstance(datasource, Set):
            rows = datasource.select(limitby=page, orderby=sortby, groupby=groupby)
            total = datasource.count()
        elif isinstance(datasource, Table):
            rows = db().select(datasource.ALL, limitby=page, orderby=sortby, groupby=groupby) 
            total = db(datasource.id > 0).count()
        elif isinstance(datasource, list) and isinstance(datasource[0], Table):
            rows = db().select(limitby=page, orderby=sortby, groupby=groupby,
                                    *[t.ALL for t in datasource])
            total = db(datasource[0].id > 0).count()
        else: 
            raise AttributeError("Invalid datasource for WebGrid")        
        
        self.tablenames = list(set(map(lambda c: c.split('.')[0], rows.colnames)))
        joined = len(self.tablenames) > 1        
        self.response = rows
        self.colnames = rows.colnames        
        self.joined = joined
        self.total = total
        
        if not self.fields:
            self.fields = rows.colnames
        
        if isinstance(self.fields[0], Field):
            self.fields = ['%s.%s' % (f._tablename, f.name) for f in self.fields]
            
        if self.totals and isinstance(self.totals[0], Field):
            self.totals = ['%s.%s' % (f._tablename, f.name) for f in self.totals]
            
        if not self.field_headers:
            self.field_headers = [f.split('.')[1].replace("_", " ").capitalize() for f in self.fields ]
            
        if not self.action_headers:
            self.action_headers = self.action_links
       
        if not self.view_link:            
            self.view_link = lambda row: A('view', _href=self.crud.url(f=self.crud_function, 
                                                       args=['read', self.tablenames[0], 
                                                             row[self.tablenames[0]]['id'] \
                                                              if self.joined else row['id']]))          
        if not self.edit_link:             
            self.edit_link = lambda row: A('edit', _href=self.crud.url(f=self.crud_function, 
                                                       args=['update', self.tablenames[0],
                                                             row[self.tablenames[0]]['id'] \
                                                              if self.joined else row['id']]))
        if not self.delete_link:            
            self.delete_link = lambda row: A('delete', _href=self.crud.url(f=self.crud_function,
                                                       args=['delete', self.tablenames[0],
                                                             row[self.tablenames[0]]['id'] \
                                                              if self.joined else row['id']]),
                                                                 _onclick="return confirm('%s');" % \
                                                                    self.messages.confirm_delete)
        if not self.add_links:            
            self.add_links = lambda tables: TR(TD([A(self.messages.add_link % t,
                                                         _href=self.crud.url(f=self.crud_function, 
                                                       args=['create', t])) for t in self.tablenames],
                                                       _colspan=len(self.action_headers)+
                                                                len(self.field_headers)),
                                                                _class=self.css_prefix + '-webgrid add_links')           

        if not self.header:
            self.header = lambda fields : THEAD(TR([TH(c) for c in self.action_headers] + 
                                                   [TH(A(self.get_header(c), 
                                                       _href=self.crud.url(vars=dict(request.get_vars, pagenum=1, 
                                                           sortby=c, ascending=not self.ascending)))) 
                                              for c in fields]), 
                                              _class=self.css_prefix + '-webgrid header')
        if not self.footer:
            if not self.groupby:
                pageinfo = lambda : 'page %s of %s (total records: %s)' % \
                                     (self.pagenum, self.pagecount, self.total)
            else:
                pageinfo = lambda: ''
            self.footer = lambda fields : TR(TD(pageinfo() , 
                                                    _colspan=len(self.fields) + len(self.action_links),
                                                     _style="text-align:center;"),
                                                 _class=self.css_prefix + '-webgrid footer')                        
        if not self.pager:
            prev = A('<prev-', _href="#")
            next = A('next>', _href="#")
            if self.pagesize > 0:
                if pagenum > 0:
                    prev = A(B('<prev-'), _href=self.crud.url(vars=dict(request.get_vars,
                                                                  pagenum=self.pagenum - 1)))
                if pagenum < total / self.pagesize and len(self.response) >= self.pagesize:
                    next = A(B('next>'), _href=self.crud.url(vars=dict(request.get_vars,
                                                                 pagenum=self.pagenum + 1)))
            self.pager = lambda pagecount : TR(TD(prev, SPAN([A(x, '-', _href=self.crud.url(vars=dict(request.get_vars, pagenum=x))) 
                                                                 for x in xrange(1, pagecount + 1) if not self.groupby]), next,
                                                      _colspan=len(self.fields) + len(self.action_links),
                                                      _style="text-align:center;"),
                                                      _class=self.css_prefix + '-webgrid pager')
        if not self.page_total:
            def page_total():
                pagetotal = TR(['' for l in self.action_links],
                               _class=self.css_prefix + '-webgrid totals')
                pagetotal.components[-1] = TD(self.messages.page_total)
                for f in self.fields:
                    if f in self.totals:
                        fieldtotal = sum([self.get_value(f, r) for r in self.response]) 
                        pagetotal.components.append(TD(fieldtotal)) 
                    else:
                        pagetotal.components.append(TD()) 
                return pagetotal                       
            self.page_total = page_total     
          
        table_field = re.compile('[\w_]+\.[\w_]+')
        table = TABLE(_id=self.id)
        if 'header' in self.enabled_rows:
            table.components.append(self.header(self.fields))
        if len(rows) == 0:
            table.components.append(TR(TD(self.messages.no_records,
                                       _colspan=len(self.fields) + len(self.action_links),
                                       _style="text-align:center;")))
        for (rc, row) in enumerate(rows):            
            if self.datarow:
                table.components.append(self.datarow(row))
                continue
            _class = 'even' if rc % 2 == 0 else 'odd'
            tr = TR(_class=self.css_prefix + '-webgrid-row %s' % _class) 
            if 'view' in self.action_links:
                tr.components.append(TD(self.view_link(row), 
                                        _class=self.css_prefix + '-webgrid view_link'))
            if 'edit' in self.action_links:
                tr.components.append(TD(self.edit_link(row), 
                                        _class=self.css_prefix + '-webgrid edit_link'))
            if 'delete' in self.action_links:
                tr.components.append(TD(self.delete_link(row), 
                                        _class=self.css_prefix + '-webgrid delete_link'))

            for colname in self.fields:
                if not table_field.match(colname):
                    r = row._extra[colname]
                    tr.components.append(TD(r))
                    continue
                (tablename, fieldname) = colname.split('.')
                field = rows.db[tablename][fieldname]
                r = row[tablename][fieldname] if joined else row[fieldname]
#                if not r:
#                    raise SyntaxError, 'something wrong in SQLRows object'
                if field.represent:
                    r = field.represent(r)
                    tr.components.append(TD(r))
                    continue
                if field.type == 'blob' and r:
                    tr.components.append(TD('DATA'))
                    continue
                r = str(field.formatter(r))
                if field.type == 'upload':
                    if r:
                        tr.components.append(TD(A('file', _href=URL(r=self.environment.request
                                                                    , f=self.download_function, args=r))))
                    else:
                        tr.components.append(TD('file'))
                    continue
                tr.components.append(TD(r))
            table.components.append(tr)
            
        if self.pagesize > 0:
            pagecount = int(total / self.pagesize)
            if total % self.pagesize != 0: pagecount += 1
        else:
            pagecount = 1
            
        self.pagecount = pagecount
        
        footer_wrap = TFOOT()
        if 'totals' in self.enabled_rows and len(rows): 
            footer_wrap.components.append(self.page_total())
        if 'add_links' in self.enabled_rows: 
            footer_wrap.components.append(self.add_links(self.tablenames))        
        if 'pager' in self.enabled_rows and len(rows): 
            footer_wrap.components.append(self.pager(pagecount))        
        if 'footer' in self.enabled_rows and len(rows): 
            footer_wrap.components.append(self.footer(self.fields))        
        table.components.append(footer_wrap)
           
        return table
