module='or'

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


# OR Organisation Types
db.define_table('or_organisation_type',
				SQLField('name'),
				SQLField('description',length=256))

db.or_organisation_type.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_organisation_type.name')]

# OR Organisations
db.define_table('or_organisation',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('parent',length=64), # No need for 'db.or_organisation' here as this is only used for cascading deletions (if you delete the table it's referring it to it will delete all the corresponding records)
                SQLField('type', db.or_organisation_type),
                SQLField('registration'),	# Registration Number
                SQLField('manpower'),
                SQLField('equipment'),
                SQLField('privacy','integer',default=0),
                SQLField('archived','boolean',default=False),
                SQLField('address','text'),
                SQLField('contact',length=64),
                SQLField('location',length=64))
db.or_organisation.represent=lambda or_organisation: A(or_organisation.name,_href=t2.action('display_organisation',or_organisation.id))
db.or_organisation.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_organisation.name')]
db.or_organisation.name.comment=SPAN("*",_class="req")
db.or_organisation.type.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation_type.id','or_organisation_type.name'))
db.or_organisation.parent.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation.uuid','or_organisation.name'))
db.or_organisation.contact.requires=IS_NULL_OR(IS_IN_DB(db,'person.uuid','person.full_name'))
db.or_organisation.contact.label=T("Contact Person")
db.or_organisation.location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.uuid','gis_feature.name'))
db.or_organisation.location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))

