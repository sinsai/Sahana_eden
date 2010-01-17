# -*- coding: utf-8 -*-

module = 'vol'

#
# Sahanapy Volunteer Management System
#
# created 2009-12-20 by zubair assad
#

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# MODEL

# courier
resource = 'courier'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
#db.define_table('vol_courier', timestamp, uuidstamp,
    Field('message_id','integer',label=T('message_id'), notnull=True),
    Field('to_id','string',label=T('to_id'), notnull=True),
    Field('from_id','string',label=T('from_id'), notnull=True),
    migrate=migrate)

db[table].message_id.requires=IS_NOT_EMPTY()
db[table].to_id.requires=IS_NOT_EMPTY()
db[table].from_id.requires=IS_NOT_EMPTY()
#db[table].message_id.requires = IS_NOT_NULL()
    

# vol_hours
resource = 'hours'
table = module + '_' + resource
db.define_table(table,
    #Field('p_uuid','string',length=60, notnull=True),
    #Field('proj_id','string',length=60,label=T('proj_id'), notnull=True),
    #Field('pos_id','string',length=60,label=T('pos_id'), notnull=True),
    Field('shift_start','datetime',label=T('shift_start'), notnull=True),
    Field('shift_end','datetime',label=T('shift_end'), notnull=True),
    migrate=migrate)

db[table].shift_start.requires=[IS_NOT_EMPTY(),
                                      IS_DATETIME]
db[table].shift_end.requires=[IS_NOT_EMPTY(),
                                      IS_DATETIME]

# vol_mailbox
resource = 'mailbox'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #db.Field('p_uuid','string', length=60, notnull=True, default=' '),
    db.Field('message_id','integer', notnull=True,label=T('message_id'), default=0),
    db.Field('box','integer', notnull=True,label=T('box'), default=0),
    db.Field('checked','integer',label=T('checked'), default=0),
    migrate=migrate)


# vol_message
resource = 'message'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    db.Field('message_id','integer', notnull=True),
    db.Field('message','text',label=T('message')),
    db.Field('time','datetime', label=T('time'),notnull=True, default=request.now),
    migrate=migrate)



# vol_position
resource = 'position'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #db.Field('pos_id','string', length=60, notnull=True),
    #db.Field('proj_id','string', length=60, notnull=True),
    #db.Field('ptype_id','string', length=60, notnull=True),
    db.Field('title','string', length=30,label=T('title'), notnull=True),
    db.Field('slots','integer', length =6,label=T('slots'), notnull=True),
    db.Field('description','text', label=T('description'),notnull=True),
    db.Field('status',requires=IS_IN_SET(['active','retired']),label=T('status'), notnull=True, default ='active'),
    db.Field('payrate','double', label=T('payrate'),default=0),
    migrate=migrate)



# vol_positiontype
resource = 'positiontype'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #db.Field('ptype_id','string', length=60, notnull=True),
    db.Field('title','string', length=20,label=T('title'), notnull=True),
    db.Field('description','string', 
                length=300,
                label=T('description'), 
                comment = DIV(A(SPAN("[Help]"), _class="tooltip", _title=T("Description|Add a Description to describe this."))), 
                notnull=True),
    db.Field('skill_code','string', 
                length=20,
                label=T('skill_code'), 
                comment = DIV(A(SPAN("[Help]"), _class="tooltip", _title=T("Skill|Add a Skill Code to describe this."))),
                notnull=True),
    migrate=migrate)



# vol_vposition
resource = 'vol_position'
table = module + '_' + resource
db.define_table(table,  timestamp, uuidstamp,
    #db.Field('p_uuid','string', length=60, notnull=True, default=' '),
    #db.Field('pos_id','string', length=60, notnull=True),
    db.Field('status',requires=IS_IN_SET(['active','retired']), notnull=True,label=T('status'), default ='active'),
    db.Field('payrate','double',label=T('payrate')),
    db.Field('hours','integer',label=T('hours')),
    db.Field('task','string',label=T('task'), length=20),
    db.Field('date_assigned','datetime',label=T('date_assigned'),requires=IS_DATETIME(), notnull=True),
    migrate=migrate)



# vol_projects
resource = 'projects'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #Field('project_id','integer', length=20, notnull=True),
    Field('name','string', length=50,label=T('name')),
    location_id,
    Field('start_date','date',label=T('start_date')),
    Field('end_date','date',label=T('end_date')),
    Field('description','text', notnull=True,label=T('description')),
    Field('status', requires=IS_IN_SET(['active','completed']), notnull=True, default ='active',label=T('status')),
    migrate=migrate)

db[table].name.requires=[IS_NOT_EMPTY( error_message=T('Please fill this!')),
                                 IS_NOT_IN_DB(db,'vol_projects.name')]


# SKILLS
skills_type_opts = {
    1:T('General Skills'),
    2:T('Resources'),
    3:T('Restrictions'),
    4:T('Site Manager'),
    5:T('Unskilled')
    }

skills1_type_opts = {
    1:T('Animals'),
    2:T('Automotive'),
    3:T('Baby And Child Care'),
    4:T('Tree'),
    5:T('Warehouse')
    }    

skills2_type_opts = {
    1:T('Building Aide'),
    2:T('Vehicle'),
    3:T('Warehouse')
    }

# vol_skills

resource = 'skills'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #db.Field('p_uuid','string', length=60),
    Field('type', 'integer'),
    Field('type1', 'integer'),
    Field('type2', 'integer'),
    #db.Field('opt_skill_code','string', length=100,label=T('opt_skill_code')),
    Field('status',requires=IS_IN_SET(['approved','unapproved','denied']),label=T('status'), notnull=True, default='unapproved'),
    migrate=migrate)
db[table].type.requires = IS_NULL_OR(IS_IN_SET(skills_type_opts))
db[table].type.represent = lambda opt: opt and skills_type_opts[opt]

db[table].type1.requires = IS_NULL_OR(IS_IN_SET(skills1_type_opts))
db[table].type1.represent = lambda opt: opt and skills1_type_opts[opt]

db[table].type2.requires = IS_NULL_OR(IS_IN_SET(skills2_type_opts))
db[table].type2.represent = lambda opt: opt and skills2_type_opts[opt]

# vol_access_classification_to_request
resource = 'access_classification_to_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    db.Field('request_id','integer', length=11, notnull=True, default=0),
    db.Field('table_name','string', length=200, notnull=True, default=' ',label=T('table_name')),
    db.Field('crud','string', length=4, notnull=True, default=' ',label=T('crud')),
    migrate=migrate)


# vol_access_constraint
resource = 'access_constraint'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    db.Field('constraint_id','string', length=30, notnull=True, default=' ',label=T('constraint_id')),
    db.Field('description','string', length=200,label=T('description')),
    migrate=migrate)


# vol_access_request
resource = 'access_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    db.Field('request_id','integer', notnull=True),
    db.Field('act','string', length=100,label=T('act')),
    db.Field('vm_action','string', length=100,label=T('vm_action')),
    db.Field('description','string', length=300,label=T('description')),
    migrate=migrate)

# vol_access_constraint_to_request
resource = 'access_constraint_to_request'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    db.Field('request_id',db.vol_access_request),
    db.Field('constraint_id',db.vol_access_constraint),
    migrate=migrate)




# vol_details
resource = 'details'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #db.Field('p_uuid','string', length=60, notnull=True, default=0),
    #db.Field('org_id','string', length=60, notnull=True, default=0,label=T('org_id')),
    organisation_id,
    #db.Field('photo','text', notnull=True,label=T('photo')),
    db.Field('date_avail_start','date', notnull=True,label=T('date_avail_start')),
    db.Field('date_avail_end','date', notnull=True,label=T('date_avail_end')),
    db.Field('hrs_avail_start','datetime', notnull=True,requires=IS_DATETIME(),label=T('hrs_avail_start')),
    db.Field('hrs_avail_end','datetime', notnull=True,label=T('hrs_avail_end')),
    Field('status',requires=[IS_IN_SET(['active','retired'])], notnull=True, default ='active',label=T('status')),
    db.Field('special_needs','text',label=T('special_needs')),
    migrate=migrate)


# vol_1position
resource = 'vol'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
    #db.Field('pos_id','string', length=60, notnull=True),
    #db.Field('proj_id','string', length=60, notnull=True),
    #db.Field('ptype_id','string', length=60, notnull=True),
    db.Field('Name','string', length=30,label=T('Name'), notnull=True),
    db.Field('Date_Of_Birth','date', notnull=True,label=T('Date_Of_Birth')),
    Field('Gender',requires=IS_IN_SET(['Male','Female']), notnull=True, default ='Male',label=T('Gender')),
    Field('Identification',requires=IS_IN_SET(['National Identity Card','Passport','Driving License','Other']), notnull=True, default ='National Identity Card',label=T('Identification')),
    db.Field('Identification_No','integer', notnull=True, default=0),
    migrate=migrate)
