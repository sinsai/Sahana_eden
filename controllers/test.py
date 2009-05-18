# This file is used to test out various ideas or new Web2Py features
module = 'test'

def index():
    " http://groups.google.com/group/web2py/browse_thread/thread/9ce0253451ab63db "
    person = db(db.pr_person.id>0).select()[0]
    form1 = SQLFORM(db.pr_person,person)
    def f(form): form.vars.secret = 'oops'  ### NEW
    if form1.accepts(request.vars,onvalidation=f):
        response.flash = 'done!'
    form2 = SQLFORM(db.pr_person,person,readonly=True) ### NEW
    persons = db(db.pr_person.id>0).select()
    return dict(form1=form1, form2=form2, persons=persons)

# http://groups.google.com/group/web2py/browse_thread/thread/53086d5f89ac3ae2
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    return service()

@service.run
@service.json
@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def f(a,b):
    return a+b

@service.rss
def rss(resource):
    " http://127.0.0.1:8000/sahana/test/call/rss/rss/resource "
    table = module+'_'+resource
    if request.env.remote_addr == '127.0.0.1':
        server = 'http://127.0.0.1:' + request.env.server_port
    else:
        server = 'http://' + request.env.server_name + ':' + request.env.server_port
    link = '/%s/%s/%s' % (request.application,module,resource)
    entries = []
    rows = db(db[table].id>0).select()
    for row in rows:
        entries.append(dict(title=row.name, link=server+link+'/%d' % row.id, description=row.description or '', created_on=row.created_on))
    return dict(title=str(s3.crud_strings[table].subtitle_list), link=server+link, description='', created_on=request.now, entries=entries)

def test():
    form = FORM('username:',INPUT(_name='username'),
            'password:',INPUT(_name='password',_type='password'),
            INPUT(_type='submit',_value='login'))
    if form.accepts(request.vars, session):
        user = self.settings.table_user
        users = self.db (user.username==form.vars.username).select()
        if not users:
            session.error = self.messages.invalid_login
            redirect(URL(r=request,args=request.args))
        else:
            pass
    return dict(form=form)
    
def kit_item():
    table = db.test_kit
    if len(request.args) == 0:
        form = SQLFORM(table)
    else:
        item_list = []
        kit = request.args[0]
        #form=SQLFORM(table,kit)
        query = table.id==kit
        sqlrows = db(query).select()
        for row in sqlrows:
            id = row.item_id
            id_link = A(id,_href=URL(r=request,f='item',args=['read',id]))
            quantity_box = INPUT(_value=row.quantity,_size=4)
            item_list.append(TR(TD(id_link),TD(quantity_box)))
        table_header = THEAD(TR(TH(table.item_id.label),TH(table.quantity.label)))
        table_footer = TFOOT(TR(TD(_colspan=2),TD(INPUT(_id='submit_quantity_button', _type='submit', _value=T('Update')))))
        items = DIV(FORM(TABLE(table_header,TBODY(item_list),table_footer,_id="table-container"),_name='custom',_method='post', _enctype='multipart/form-data', _action=''))
        
    #if form.accepts(request.vars,session):
    #    response.flash="ok"
    #elif form.errors:
    #    response.flash="please correct and re-submit"
    if not items:
        items = form
    return dict(items=items)


def kit():
    db.test_kit.quantity.represent = lambda value: TABLE(TR(TD(str(value),_rowspan=2),TD(TABLE(
        TR(A(T('adjust'),_href=URL(r=request, f='kit/update', args=str(value)))),
        TR(A(T('delete'),_href=URL(r=request, f='kit/delete', args=str(value))))))))
    table=SQLTABLE(db(db.test_kit.id>0).select())
    return dict(table=table)
    
def kit2():
    " http://groups.google.com/group/web2py/browse_thread/thread/31b4f2c1ce2ea66b "
    table = 'budget_item'
    rows = db(db[table].id>0).select()
    db[table].id.represent = lambda id: DIV(id, INPUT(_type='checkbox', _name='check%i' % id))
    form = FORM(SQLTABLE(rows),INPUT(_type='submit'))
    if form.accepts(request.vars):
        # do something
        pass
    return dict(form=form) 

def jquery_upload():
    return dict()

def post():
    """Test for JSON POST
    #curl -i -X POST http://127.0.0.1:8000/sahana/test/post -H "Content-Type: application/json" -d {"name": "John"}
    #curl -i -X POST http://127.0.0.1:8000/sahana/test/post -H "Content-Type: application/json" -d @test.json
    Web2Py forms are multipart/form-data POST forms
    curl -i -X POST http://127.0.0.1:8000/sahana/test/post -F name=john
    curl -i -X POST --data-urlencode "name=Colombo Shelter" http://127.0.0.1:8000/sahana/test/post
    """
    #file=request.body.read()
    #import gluon.contrib.simplejson as sj
    #reader=sj.loads(file)
    #name = reader["name"]
    #return db.test_post.insert(name=name)
    return db.test_post.insert(**dict (request.vars))

def get():
    """Test for JSON GET
    curl -i http://127.0.0.1:8000/sahana/test/get -F name=john
    """
    #import gluon.contrib.simplejson as sj
    #return db.test_get.insert(**sj.loads(request.vars.fields))
    return db.test_get.insert(**dict (request.vars))

# M2M Tests
def list_dogs():
    "Test for M2M widget"
    items = t2.itemize(db.dog)
    response.view = 'list_plain.html'
    return dict(items=items)

def display_dog():
    "Test for M2M widget"
    items = t2.display(db.dog)
    response.view = 'list_plain.html'
    return dict(items=items)

def update_dog():
    "Test for M2M widget"
    items = t2.update(db.dog)
    response.view = 'list_plain.html'
    return dict(items=items)

def delete_dog():
    "Test for M2M widget"
    items = t2.delete(db.dog)
    response.view = 'list_plain.html'
    return dict(items=items)

def delete_owner():
    "Test for M2M widget"
    items = t2.delete(db.owner)
    response.view = 'list_plain.html'
    return dict(items=items)
