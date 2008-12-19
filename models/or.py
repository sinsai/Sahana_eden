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
                SQLField('modified_on','datetime'), # Used by T2 to do edit conflict-detection
                SQLField('name'),
                #SQLField('parent',db.organisation),
                SQLField('type', db.or_organisation_type),
                SQLField('registration'),	# Registration Number
                SQLField('manpower'),
                SQLField('equipment'),
                SQLField('privacy','integer',default=0),
                SQLField('archived','boolean',default=False),
                SQLField('address','text'),
                SQLField('contact',db.person),
                SQLField('location',db.gis_feature))
db.or_organisation.represent=lambda or_organisation: A(or_organisation.name,_href=t2.action('display_organisation',or_organisation.id))
db.or_organisation.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'or_organisation.name')]
db.or_organisation.name.comment=SPAN("*",_class="req")
db.or_organisation.type.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation_type.id','or_organisation_type.name'))
#db.or_organisation.parent.requires=IS_NULL_OR(IS_IN_DB(db,'or_organisation.id','or_organisation.name'))
db.or_organisation.contact.requires=IS_NULL_OR(IS_IN_DB(db,'person.id','person.full_name'))
db.or_organisation.contact.label=T("Contact Person")
db.or_organisation.location.requires=IS_NULL_OR(IS_IN_DB(db,'gis_feature.id','gis_feature.name'))
db.or_organisation.location.comment=A(SPAN("[Help]"),_class="popupLink",_id="tooltip",_title=T("Location|The GIS Feature associated with this Shelter."))

