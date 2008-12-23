module='cr'

# Menu Options
db.define_table('%s_menu_option' % module,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s_menu_option' % module].name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.name' % module)]
db['%s_menu_option' % module].name.requires=IS_NOT_EMPTY()
db['%s_menu_option' % module].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.priority' % module)]


# CR Shelters
db.define_table('cr_shelter',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('address','text'),
                SQLField('capacity','integer'),
                SQLField('dwellings','integer'),
                SQLField('area'),
                SQLField('persons_per_dwelling','integer'),
                SQLField('contact',length=64),
                SQLField('location',length=64))
db.cr_shelter.displays=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']
db.cr_shelter.represent=lambda cr_shelter: A(cr_shelter.name,_href=t2.action('display_shelter',cr_shelter.id))
db.cr_shelter.name.requires=IS_NOT_EMPTY()
db.cr_shelter.name.label=T("Shelter Name")
db.cr_shelter.name.comment=SPAN("*",_class="req")
# Doesn't allow db entry:
#db.cr_shelter.name.widget=lambda self,value: DIV(INPUT(_type='text'),SPAN(_class='req'))
#db.cr_shelter.name.widget=lambda self,value: DIV(INPUT(_type='text', _id=field_id,_class=field.type,_name=fieldname,value=str(default),requires=field.requires),SPAN(_class='req'))
#db.cr_shelter.name.widget=t2.input_required_widget
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget
# Most promising, but need to fix scope for field_id:
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget('name')
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget(self,value)
#db.cr_shelter.name.widget=lambda self,value: t2.input_required_widget(value)
db.cr_shelter.contact.requires=IS_NULL_OR(IS_IN_DB(db,'person.uuid','person.full_name'))
db.cr_shelter.contact.label=T("Contact Person")
db.cr_shelter.location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db.cr_shelter.location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))

