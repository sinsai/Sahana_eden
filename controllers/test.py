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
