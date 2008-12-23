# This scaffolding model makes your app work on Google App Engine too   #
#try:
#    from gluon.contrib.gql import *         # if running on Google App Engine
#except:
db=SQLDB('sqlite://storage.db')         # if not, use SQLite or other DB
#else:
#    db=GQLDB()                              # connect to Google BigTable
#    session.connect(request,response,db=db) # and store sessions there

# Define 'now'
# 'modified_on' fields used by T2 to do edit conflict-detection & by DBSync to check which is more recent
import datetime; now=datetime.datetime.today()

# We need UUIds for database synchronization
import uuid

# Use T2 plugin for AAA & CRUD
# At top of file rather than usual bottom as we refer to it within our tables
#from applications.sahana.modules.t2 import T2
#t2=T2(request,response,session,cache,T,db)

# Custom classes which extend default T2
from applications.sahana.modules.sahana import T2SAHANA
t2=T2SAHANA(request,response,session,cache,T,db)

# Custom validators
from applications.sahana.modules.validators import *

#
# Core Framework
#

# Modules
db.define_table('module',
                SQLField('name'),
                SQLField('name_nice'),
                SQLField('menu_priority','integer'),
                SQLField('description',length=256),
                SQLField('enabled','boolean',default='True'))
db.module.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name')]
db.module.name_nice.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.name_nice')]
db.module.menu_priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'module.menu_priority')]

# Home Menu Options
db.define_table('default_menu_option',
                SQLField('name'),
                SQLField('function'),
                SQLField('description',length=256),
                SQLField('priority','integer'),
                SQLField('enabled','boolean',default='True'))
db.default_menu_option.name.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'default_menu_option.name')]
db.default_menu_option.function.requires=IS_NOT_EMPTY()
db.default_menu_option.priority.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'default_menu_option.priority')]

# Field options meta table
# Give a custom list of options for each field in this schema 
# prefixed with opt_. This is customizable then at deployment
# See the field_options.py for default customizations
# Modules: cr
# Actually for S3 we have a per-module table for 'config'
#db.define_table('field_option',
#                SQLField('field_name'),
#                SQLField('option_code',length=20),
#                SQLField('option_description',length=50))
#db.field_option.field_name.requires=IS_NOT_EMPTY()
#db.field_option.option_code.requires=IS_NOT_EMPTY()
#db.field_option.option_description.requires=IS_NOT_EMPTY()

# System Config
db.define_table('system_config',
				SQLField('setting'),
				SQLField('description',length=256),
				SQLField('value'))
# We want a THIS_NOT_IN_DB here: admin_name, admin_email, admin_tel
db.system_config.setting.requires=[IS_NOT_EMPTY(),IS_NOT_IN_DB(db,'system_config.setting')]

# Persons
# Modules: cr,dvr,mpr
db.define_table('person',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('full_name'),
                SQLField('family_name'),
                SQLField('l10_name'))
db.person.represent=lambda person: A(person.full_name,_href=t2.action('display_person',person.id))
db.person.full_name.requires=IS_NOT_EMPTY()

# Person Contacts
# Modules: cr,dvr,mpr
db.define_table('person_contact',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('opt_contact_type'),	# mobile, home phone, email, IM, etc
                SQLField('contact_value'))
db.person_contact.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Identity
# Modules: dvr,mpr
db.define_table('person_identity',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('opt_id_type'),		# ID card, Passport, Driving License, etc
                SQLField('id_value'))
db.person_identity.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Details
# Modules: cr,dvr,mpr
db.define_table('person_details',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('next_kin',length=64),
                SQLField('birth_date','date'),
                SQLField('opt_age_group'),
                SQLField('relation'),
                SQLField('opt_country'),
                SQLField('opt_race'),
                SQLField('opt_religion'),
                SQLField('opt_marital_status'),
                SQLField('opt_gender'),
                SQLField('occupation'))
db.person_details.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_details.next_kin.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_details.birth_date.requires=IS_DATE(T("%Y-%m-%d")) # Can use Translation to provide localised formatting

# Person Status
# Modules: dvr,mpr
db.define_table('person_status',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('isReliefWorker','boolean',default=False),
                SQLField('isVictim','boolean',default=True),
                SQLField('opt_status'),	# missing, injured, etc. customizable
                SQLField('id_value'))
db.person_status.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Physical
# Modules: dvr,mpr
db.define_table('person_physical',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('height'),
                SQLField('weight'),
                SQLField('opt_blood_type'),
                SQLField('opt_eye_color'),
                SQLField('opt_skin_color'),
                SQLField('opt_hair_color'),
                SQLField('injuries'),
                SQLField('comments',length=256))
db.person_physical.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Missing
# Modules: dvr,mpr
db.define_table('person_missing',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('last_seen'),
                SQLField('last_clothing'),
                SQLField('comments',length=256))
db.person_missing.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Deceased
# Modules: dvr,mpr
db.define_table('person_deceased',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('details'),
                SQLField('date_of_death','date'),
                SQLField('place_of_death'),
                SQLField('comments',length=256))
db.person_deceased.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Reporter
# (The person who reported about this person)
# Modules: dvr,mpr
db.define_table('person_report',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('reporter',length=64),
                SQLField('relation'))
db.person_report.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_report.reporter.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person Group
# Modules: dvr,mpr
db.define_table('person_group',
                SQLField('modified_on','datetime',default=now),
                SQLField('uuid',length=64,default=uuid.uuid4()),
                SQLField('name'),
                SQLField('opt_group_type'))

# Person Group Details
# Modules: dvr,mpr
db.define_table('person_group_details',
                SQLField('modified_on','datetime',default=now),
                SQLField('person_group',length=64),
                SQLField('head',length=64),
                SQLField('no_of_adult_males','integer'),
                SQLField('no_of_adult_females','integer'),
                SQLField('no_of_children','integer'),
                SQLField('no_displaced','integer'),
                SQLField('no_missing','integer'),
                SQLField('no_dead','integer'),
                SQLField('no_rehabilitated','integer'),
                SQLField('checklist'),
                SQLField('description',length=256))
db.person_group_details.person_group.requires=IS_IN_DB(db,'person_group.uuid')
db.person_group_details.head.requires=IS_IN_DB(db,'person.uuid','person.full_name')

# Person to Group
# (A person can belong to multiple groups)
# Modules: dvr,mpr
db.define_table('person_to_group',
                SQLField('modified_on','datetime',default=now),
                SQLField('person',length=64),
                SQLField('person_group',length=64))
db.person_to_group.person.requires=IS_IN_DB(db,'person.uuid','person.full_name')
db.person_to_group.person_group.requires=IS_IN_DB(db,'person_group.uuid')
