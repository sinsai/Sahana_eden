# -*- coding: utf-8 -*-

# This file is used to test out various ideas or new Web2Py features
module = 'test'

def index():
    "Shows request/session state for debugging"
    return dict()
    
def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # If webservices don't use sessions, avoid cluttering up the storage
    #session.forget()
    return service()

def test():
    items = None
    form = None
    return dict(items=items, form=form)

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

def feature():
    row = TR(TD(T('Type:')), TD(LABEL(T('Feature Class'), INPUT(_type="radio", _name="fg1", _value="FeatureClass", value="FeatureClass")), LABEL(T('Feature'), INPUT(_type="radio", _name="fg1", _value="Feature", value="FeatureClass"))))
    return dict(row=row)

def refresh():
    response.refresh = '<noscript><meta http-equiv="refresh" content="2; url=' + URL(r=request, c='budget', f='item') + '" /></noscript>' 
    return dict()

def photo():
    form = crud.create(db.test_photo)
    return dict(form=form)

def user():
    if auth.is_logged_in() or auth.basic():
        user = auth.user.id if session.auth else 0
    else:
        user = None
    return user
    
def css():
    items = crud.select(db.pr_person, _id='myid', _class='myclass')
    form = crud.create(db.pr_person)
    form['_class'] = 'my2class'
    form['_id'] = 'my2id'
    return dict(items=items, form=form)
    
def type():
    table = db.msg_group_type
    table.name.represent = lambda name: T(name)
    items = crud.select(table)
    table = db.msg_group
    form = crud.create(table)
    return dict(form=form, items=items)