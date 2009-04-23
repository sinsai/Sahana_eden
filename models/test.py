def shn_m2m_widget(self,value,options=[]):
    """Many-to-Many widget
    Currently this is just a renamed copy of t2.tag_widget"""
    
    script=SCRIPT("""
    function web2py_m2m(self,other,option) {
       var o=document.getElementById(other)
       if(self.className=='option_selected') {
          self.setAttribute('class','option_deselected');
          o.value=o.value.replace('['+option+']','');
       }
       else if(self.className=='option_deselected') {
          self.setAttribute('class','option_selected');
          o.value=o.value+'['+option+']';
       }
    }
    """)
    id=self._tablename+'_'+self.name
    def onclick(x):
        return "web2py_m2m(this,'%s','%s');"%(id,x.lower())
    buttons=[SPAN(A(x,_class='option_selected' if value and '[%s]'%x.lower() in value else 'option_deselected',_onclick=onclick(x)),' ') for x in options]
    return DIV(script,INPUT(_type='hidden',_id=id,_name=self.name,_value=value),*buttons) 

# SQLTable .represent Test
db.define_table('test_kit',db.Field('item_id'),db.Field('quantity'))
            
# JSON Tests
db.define_table('test_post',db.Field('name'))
db.define_table('test_get',db.Field('name'))

# M2M Tagging test
#db.define_table('owner',db.Field('name'),db.Field('uuid',length=64,default=uuid.uuid4()))
#db.define_table('dog',db.Field('name'),db.Field('owner','text'))
##db.dog.owner.requires=IS_IN_DB(db,'owner.uuid','owner.name',multiple=True)
#db.dog.owner.requires=IS_IN_DB(db,'owner.id','owner.name',multiple=True)
##db.dog.owner.display=lambda x: ', '.join([db(db.owner.id==id).select()[0].name for id in x[1:-1].split('|')])
##db.dog.owner.display=lambda x: map(db(db.owner.id==id).select()[0].name,x[1:-1].split('|'))
#db.dog.represent=lambda dog: A(dog.name,_href=t2.action('display_dog',dog.id))

# Web2Py new Features in Trunk
# http://groups.google.com/group/web2py/browse_thread/thread/9ce0253451ab63db
#db.define_table('person',db.Field('name'),db.Field('secret'))
#db.person.secret.writable=False ### NEW
#db.person.secret.readable=False ### NEW
#db.person.name.comment='(your full name)'  ### NEW
#db.person.name.represent=lambda value: H2(value) ### NEW
