# This file is used to test out various ideas or new Web2Py features
module='test'

def index():
    " http://groups.google.com/group/web2py/browse_thread/thread/9ce0253451ab63db "
    person=db(db.pr_person.id>0).select()[0]
    form1=SQLFORM(db.pr_person,person)
    def f(form): form.vars.secret='oops'  ### NEW
    if form1.accepts(request.vars,onvalidation=f):
        response.flash='done!'
    form2=SQLFORM(db.pr_person,person,readonly=True) ### NEW
    persons=db(db.pr_person.id>0).select()
    return dict(form1=form1,form2=form2,persons=persons)

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
    table=module+'_'+resource
    if request.env.remote_addr=='127.0.0.1':
        server='http://127.0.0.1:' + request.env.server_port
    else:
        server='http://' + request.env.server_name + ':' + request.env.server_port
    link='/%s/%s/%s' % (request.application,module,resource)
    entries=[]
    rows=db(db[table].id>0).select()
    for row in rows:
        entries.append(dict(title=row.name,link=server+link+'/%d' % row.id,description=row.description or '',created_on=row.created_on))
    return dict(title=str(s3.crud_strings[table].subtitle_list),link=server+link,description='',created_on=request.now,entries=entries)

def kit():
    table=db.test_kit
    item_list=[]
    sqlrows=db(table.id>0).select()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.id
        description = row.item_id
        quantity_box = INPUT(_value=row.quantity,_size=4)
        checkbox = INPUT(_type="checkbox",_value="on",_name=kit,_id=id,_class="remove_item")
        item_list.append(TR(TD(id),TD(description),TD(quantity_box),TD(checkbox),_class=theclass))
    table_header=THEAD(TR(TH('ID'),TH(table.item_id.label),TH(table.quantity.label),TH(T('Delete'))))
    table_footer=TFOOT(TR(TD(_colspan=2),TD(INPUT(_id='submit_quantity_button', _type='submit', _value=T('Update'))),TD(INPUT(_id='submit_delete_button', _type='submit', _value=T('Delete')))))
    items=DIV(FORM(TABLE(table_header,TBODY(item_list),table_footer,_id="table-container"),_method='post', _enctype='multipart/form-data', _action=''))
    return dict(table=table,items=items)
    
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
    items=t2.itemize(db.dog)
    response.view='list_plain.html'
    return dict(items=items)

def display_dog():
    "Test for M2M widget"
    items=t2.display(db.dog)
    response.view='list_plain.html'
    return dict(items=items)

def update_dog():
    "Test for M2M widget"
    items=t2.update(db.dog)
    response.view='list_plain.html'
    return dict(items=items)

def delete_dog():
    "Test for M2M widget"
    items=t2.delete(db.dog)
    response.view='list_plain.html'
    return dict(items=items)

def delete_owner():
    "Test for M2M widget"
    items=t2.delete(db.owner)
    response.view='list_plain.html'
    return dict(items=items)
