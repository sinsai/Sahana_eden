module='cr'

# Menu Options
db.define_table('%s_menu_option' % module,
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db['%s_menu_option' % module].name.requires=IS_NOT_IN_DB(db,'%s_menu_option.name' % module)
db['%s_menu_option' % module].name.requires=IS_NOT_EMPTY()
db['%s_menu_option' % module].priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'%s_menu_option.priority' % module)]


# Shelters
db.define_table('cr_shelter',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('description',length=256),
                SQLField('address','text'),
                SQLField('capacity','integer',default=0),
                SQLField('dwellings','integer',default=0),
                SQLField('area'),
                SQLField('persons_per_dwelling','integer',default=0),
                SQLField('contact',length=64),
                SQLField('location',length=64))
db.cr_shelter.exposes=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']
db.cr_shelter.displays=['name','description','address','capacity','dwellings','area','persons_per_dwelling','contact','location']
db.cr_shelter.represent=lambda table:shn_list_item(table,resource='shelter',action='display')
db.cr_shelter.name.requires=IS_NOT_EMPTY()
db.cr_shelter.name.label=T("Shelter Name")
db.cr_shelter.name.comment=SPAN("*",_class="req")
db.cr_shelter.contact.requires=IS_NULL_OR(IS_IN_DB(db,'pr_person.uuid','pr_person.full_name'))
db.cr_shelter.contact.display=lambda uuid: (uuid and [db(db.pr_person.uuid==uuid).select()[0].full_name] or ["None"])[0]
db.cr_shelter.contact.label=T("Contact Person")
db.cr_shelter.location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db.cr_shelter.location.display=lambda uuid: (uuid and [db(db.gis_feature.uuid==uuid).select()[0].name] or ["None"])[0]
db.cr_shelter.location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))
