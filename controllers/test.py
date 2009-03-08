# This file is used to test out various ideas or new Web2Py features

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
@service.run
@service.json
@service.jsonrpc
@service.xmlrpc
@service.amfrpc
def f(a,b):
    return a+b

@service.rss
def myfeed():
    return dict(title='title',link='link',description='description',created_on=request.now,entries=[dict(title='title',link='link',description='description',created_on=request.now)])

def call():
    return service()

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
    list=t2.itemize(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def display_dog():
    "Test for M2M widget"
    list=t2.display(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def update_dog():
    "Test for M2M widget"
    list=t2.update(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def delete_dog():
    "Test for M2M widget"
    list=t2.delete(db.dog)
    response.view='list_plain.html'
    return dict(list=list)

def delete_owner():
    "Test for M2M widget"
    list=t2.delete(db.owner)
    response.view='list_plain.html'
    return dict(list=list)
