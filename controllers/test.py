# This file is used to test out various ideas or new Web2Py features

def index():
    " http://groups.google.com/group/web2py/browse_thread/thread/9ce0253451ab63db "
    person=db(db.person.id>0).select()[0]
    form1=SQLFORM(db.person,person)
    def f(form): form.vars.secret='oops'  ### NEW
    if form1.accepts(request.vars,onvalidation=f):
        response.flash='done!'
    form2=SQLFORM(db.person,person,readonly=True) ### NEW
    persons=db(db.person.id>0).select()
    return dict(form1=form1,form2=form2,persons=persons)
    