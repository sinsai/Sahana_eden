# -*- coding: utf-8 -*-

module = 'vol'

#
# SahanaPy Volunteer Management System
#
# created 2009-12-20 by zubair assad
# modified 2010-01-17 by nursix
#

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# -----------------------------------------------------------------------------
# vol_project
#   describes a project
#
vol_project_status_opts = {
  1: T('active'),
  2: T('completed'),
  99: T('inactive')
}

resource = 'project'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('name', 'string', length=50),
                location_id,
                Field('start_date', 'date'),
                Field('end_date', 'date'),
                Field('description','text', notnull=True),
                Field('status', 'integer',
                      requires = IS_IN_SET(vol_project_status_opts),
                      default = 99,
                      label = T('Project Status'),
                      represent = lambda opt: opt and vol_project_status_opts[opt]),
                migrate=migrate)

# Settings and Restrictions
db[table].name.requires=[IS_NOT_EMPTY( error_message=T('Please fill this!')), IS_NOT_IN_DB(db,'vol_project.name')]

db[table].description.requires = IS_NOT_EMPTY()

# Labels
db[table].name.label = T('Name')
db[table].start_date.label = T('Start date')
db[table].end_date.label = T('End date')
db[table].description.label = T('Description')

# CRUD Strings
title_create = T('Add Project')
title_display = T('Project Details')
title_list = T('Projects')
title_update = T('Edit Project')
title_search = T('Search Projects')
subtitle_create = T('Add New Project')
subtitle_list = T('Projects')
label_list_button = T('List Projects')
label_create_button = T('Add Project')
msg_record_created = T('Project added')
msg_record_modified = T('Project updated')
msg_record_deleted = T('Project deleted')
msg_list_empty = T('No projects currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reusable field
vol_project_id = db.Table(None, 'vol_project_id',
                          Field('vol_project_id', db.vol_project,
                          requires = IS_NULL_OR(IS_ONE_OF(db, 'vol_project.id', '%(name)s')),
                          represent = lambda id: (id and [db.vol_project[id].name] or ["None"])[0],
                          comment = DIV(A(s3.crud_strings.vol_project.label_create_button, _class='thickbox', _href=URL(r=request, c='vol', f='project', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=s3.crud_strings.vol_project.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Project|Add new project)."))),
                          label = "Project",
                          ondelete = 'RESTRICT'
                         ))

# -----------------------------------------------------------------------------
# vol_position (component of vol_project)
#   describes a position in a project
#
vol_position_type_opts = {
  1: T('Site Manager'),
  2: T('Team Leader'),
  3: T('Assistant'),
  99: T('Other')
}

resource = 'position'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                vol_project_id,
                Field('type', 'integer',
                      requires = IS_IN_SET(vol_position_type_opts),
                      default = 99,
                      label = T('Position type'),
                      represent = lambda opt: opt and vol_position_type_opts[opt]),
                Field('title', length=30),
                Field('description', 'text'),
                Field('slots', 'integer', default=1),
                Field('payrate', 'double', default=0.0),
                #Field('status')?
                migrate=migrate)

# CRUD Strings
title_create = T('Add Position')
title_display = T('Position Details')
title_list = T('Position')
title_update = T('Edit Position')
title_search = T('Search Positions')
subtitle_create = T('Add New Position')
subtitle_list = T('Positions')
label_list_button = T('List Positions')
label_create_button = T('Add Position')
msg_record_created = T('Position added')
msg_record_modified = T('Position updated')
msg_record_deleted = T('Position deleted')
msg_list_empty = T('No positions currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reusable field
vol_position_id = db.Table(None, 'vol_position_id',
                           Field('vol_position_id', db.vol_position,
                           requires = IS_NULL_OR(IS_ONE_OF(db, 'vol_position.id', '%(title)s')),
                           represent = lambda id: lambda id: (id and [db.vol_position[id].title] or ["None"])[0],
                           comment = DIV(A(s3.crud_strings.vol_project.label_create_button, _class='thickbox', _href=URL(r=request, c='vol', f='project', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=s3.crud_strings.vol_project.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Position|Add new position)."))),
                           ondelete = 'RESTRICT'
                          ))

s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(vol_project='vol_project_id'),
    deletable=True,
    editable=True,
    main='title', extra='description',
    list_fields = ['type', 'title', 'description', 'slots', 'payrate'])

# -----------------------------------------------------------------------------
# vol_volunteer (Component of pr_person)
#   describes a person's availability as volunteer
#
vol_volunteer_status_opts = {
  1: T('active'),
  2: T('retired')
}

resource = 'volunteer'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                person_id,
                organisation_id,
                Field('date_avail_start', 'date'),
                Field('date_avail_end', 'date'),
                Field('hrs_avail_start', 'time'),
                Field('hrs_avail_end', 'time'),
                Field('status', 'integer',
                      requires = IS_IN_SET(vol_volunteer_status_opts),
                      default = 1,
                      label = T('Status'),
                      represent = lambda opt: opt and vol_volunteer_status_opts[opt]),
                Field('special_needs', 'text'),
                migrate=migrate)

# Settings and Restrictions

# Field labels
db[table].date_avail_start.label = T('Available from')
db[table].date_avail_end.label = T('Available until')
db[table].hrs_avail_start.label = T('Working hours start')
db[table].hrs_avail_end.label = T('Working hours end')
db[table].special_needs.label = T('Special needs')

# Representation function
def shn_vol_volunteer_represent(id):
    person = db((db.pr_volunteer.id==id)&(db.pr_person.id==db.pr_volunteer.person_id)).select(
                db.pr_person.first_name,
                db.pr_person.middle_name,
                db.pr_person.last_name,
                limitby=(0,1))
    if person:
        return vita.fullname(person[0])
    else:
        return None

# CRUD Strings
title_create = T('Add Volunteer Status')
title_display = T('Volunteer Details')
title_list = T('Volunteers')
title_update = T('Edit Volunteer Status')
title_search = T('Search Volunteers')
subtitle_create = T('Add Volunteer Status')
subtitle_list = T('Volunteers')
label_list_button = T('List Volunteers')
label_create_button = T('Add Volunteer Status')
msg_record_created = T('Volunteer status added')
msg_record_modified = T('Volunteer status updated')
msg_record_deleted = T('Volunteer status deleted')
msg_list_empty = T('No volunteer information registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Reusable field
vol_volunteer_id = db.Table(None, 'vol_project_id',
                            Field('vol_project_id', db.vol_volunteer,
                            requires = IS_NULL_OR(IS_ONE_OF(db, 'vol_volunteer.id', shn_vol_volunteer_represent)),
                            represent = lambda id: lambda id: (id and [shn_vol_volunteer_represent(id)] or ["None"])[0],
                            comment = DIV(A(s3.crud_strings.vol_volunteer.label_create_button, _class='thickbox', _href=URL(r=request, c='vol', f='volunteer', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=s3.crud_strings.vol_volunteer.label_create_button), A(SPAN("[Help]"), _class="tooltip", _title=T("Volunteer|Add new volunteer)."))),
                            ondelete = 'RESTRICT'
                           ))

s3xrc.model.add_component(module, resource,
    multiple=False,
    joinby=dict(pr_person='person_id'),
    deletable=True,
    editable=True,
    main='person_id', extra='organisation_id',
    list_fields = ['organisation_id', 'status'])

# -----------------------------------------------------------------------------
# vol_skills (Component of pr_person)
#   describes Capabilities/Restrictions of a Volunteer
#
vol_skills_resource_opts = {
    1:T('General Skills'),
    2:T('Resources'),
    3:T('Restrictions'),
    4:T('Site Manager'),
    5:T('Unskilled'),
    99:T('Other')
}

vol_skills_subject_opts = {
    1:T('Animals'),
    2:T('Automotive'),
    3:T('Baby And Child Care'),
    4:T('Tree'),
    5:T('Warehouse'),
    99:T('Other')
}

vol_skills_deployment_opts = {
    1:T('Building Aide'),
    2:T('Vehicle'),
    3:T('Warehouse'),
    99:T('Other')
}

vol_skills_status_opts = {
    1:T('approved'),
    2:T('unapproved'),
    3:T('denied')
}

resource = 'skills'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp,
                person_id,
                Field('resource', 'integer',
                      requires = IS_IN_SET(vol_skills_resource_opts),
                      default = 99,
                      label = T('Resource'),
                      represent = lambda opt: opt and vol_skills_resource_opts[opt]),
                Field('subject', 'integer',
                      requires = IS_IN_SET(vol_skills_subject_opts),
                      default = 99,
                      label = T('Subject'),
                      represent = lambda opt: opt and vol_skills_subject_opts[opt]),
                Field('deployment', 'integer',
                      requires = IS_IN_SET(vol_skills_deployment_opts),
                      default = 99,
                      label = T('Deployment'),
                      represent = lambda opt: opt and vol_skills_deployment_opts[opt]),
                Field('status', 'integer',
                      requires = IS_IN_SET(vol_skills_status_opts),
                      default = 2,
                      label = T('Status'),
                      represent = lambda opt: opt and vol_skills_status_opts[opt]),
                migrate=migrate)

s3xrc.model.add_component(module, resource,
    multiple=True,
    joinby=dict(pr_person='person_id'),
    deletable=True,
    editable=True,
    main='person_id', extra='subject',
    list_fields = ['id', 'resource', 'subject', 'deployment', 'status'])

# CRUD Strings
title_create = T('Add Skills')
title_display = T('Skills Details')
title_list = T('Skills')
title_update = T('Edit Skills')
title_search = T('Search Skills')
subtitle_create = T('Add New Skills')
subtitle_list = T('Skills')
label_list_button = T('List Skills')
label_create_button = T('Add Skills')
msg_record_created = T('Skills added')
msg_record_modified = T('Skills updated')
msg_record_deleted = T('Skills deleted')
msg_list_empty = T('No skills currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# -----------------------------------------------------------------------------
# courier
#resource = 'courier'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#db.define_table('vol_courier', timestamp, uuidstamp,
#    Field('message_id','integer',label=T('message_id'), notnull=True),
#    Field('to_id','string',label=T('to_id'), notnull=True),
#    Field('from_id','string',label=T('from_id'), notnull=True),
#    migrate=migrate)

#db[table].message_id.requires=IS_NOT_EMPTY()
#db[table].to_id.requires=IS_NOT_EMPTY()
#db[table].from_id.requires=IS_NOT_EMPTY()
#db[table].message_id.requires = IS_NOT_NULL()


# -----------------------------------------------------------------------------
# vol_hours:
#   documents the hours a volunteer has a position
#
resource = 'hours'
table = module + '_' + resource
db.define_table(table,
                person_id,
                vol_position_id,
                Field('shift_start','datetime',label=T('shift_start'), notnull=True),
                Field('shift_end','datetime',label=T('shift_end'), notnull=True),
                migrate=migrate)

db[table].shift_start.requires=[IS_NOT_EMPTY(),
                                      IS_DATETIME]
db[table].shift_end.requires=[IS_NOT_EMPTY(),
                                      IS_DATETIME]

# -----------------------------------------------------------------------------
# vol_mailbox
#resource = 'mailbox'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
    #db.Field('p_uuid','string', length=60, notnull=True, default=' '),
#    db.Field('message_id','integer', notnull=True,label=T('message_id'), default=0),
#    db.Field('box','integer', notnull=True,label=T('box'), default=0),
#    db.Field('checked','integer',label=T('checked'), default=0),
#    migrate=migrate)


# -----------------------------------------------------------------------------
# vol_message
#resource = 'message'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#    db.Field('message_id','integer', notnull=True),
#    db.Field('message','text',label=T('message')),
#    db.Field('time','datetime', label=T('time'),notnull=True, default=request.now),
#    migrate=migrate)


# -----------------------------------------------------------------------------
# vol_access_classification_to_request
#resource = 'access_classification_to_request'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#    db.Field('request_id','integer', length=11, notnull=True, default=0),
#    db.Field('table_name','string', length=200, notnull=True, default=' ',label=T('table_name')),
#    db.Field('crud','string', length=4, notnull=True, default=' ',label=T('crud')),
#    migrate=migrate)


# -----------------------------------------------------------------------------
# vol_access_constraint
#resource = 'access_constraint'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#    db.Field('constraint_id','string', length=30, notnull=True, default=' ',label=T('constraint_id')),
#    db.Field('description','string', length=200,label=T('description')),
#    migrate=migrate)


# -----------------------------------------------------------------------------
# vol_access_request
#resource = 'access_request'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#    db.Field('request_id','integer', notnull=True),
#    db.Field('act','string', length=100,label=T('act')),
#    db.Field('vm_action','string', length=100,label=T('vm_action')),
#    db.Field('description','string', length=300,label=T('description')),
#    migrate=migrate)

# -----------------------------------------------------------------------------
# vol_access_constraint_to_request
#resource = 'access_constraint_to_request'
#table = module + '_' + resource
#db.define_table(table, timestamp, uuidstamp,
#    db.Field('request_id',db.vol_access_request),
#    db.Field('constraint_id',db.vol_access_constraint),
#    migrate=migrate)

def shn_vol_project_search_location(xrequest, onvalidation=None, onaccept=None):

    if not shn_has_permission('read', db.vol_project):
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next':URL(r=request, args='search_location', vars=request.vars)}))

    if xrequest.representation=="html":
        # Check for redirection
        if request.vars._next:
            next = str.lower(request.vars._next)
        else:
            next = str.lower(URL(r=request, f='project', args='[id]'))

        # Custom view
        response.view = '%s/project_search.html' % xrequest.prefix

        # Title and subtitle
        title = T('Search for a Project')
        subtitle = T('Matching Records')

        # Select form:
        l_opts = [OPTION(_value='')]
        l_opts += [OPTION(location.name, _value=location.id)
                  for location in db(db.gis_location.deleted==False).select(db.gis_location.ALL,cache=(cache.ram,3600))]
        form = FORM(TABLE(
                TR(T('Location: '),
                SELECT(_name="location", *l_opts, **dict(name="location", requires=IS_NULL_OR(IS_IN_DB(db,'gis_location.id'))))),
                TR("", INPUT(_type="submit", _value="Search"))
                ))

        output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

        # Accept action
        items = None
        if form.accepts(request.vars, session):

            table = db.vol_project
            query = (table.deleted==False)

            if form.vars.location is None:
                results = db(query).select(table.ALL)
            else:
                query = query & (table.location_id==form.vars.location)
                results = db(query).select(table.ALL)

            if results and len(results):
                records = []
                for result in results:
                    href = next.replace('%5bid%5d', '%s' % result.id)
                    records.append(TR(
                        A(result.name, _href=href),
                        result.start_date or "None",
                        result.end_date or "None",
                        result.description or "None",
                        result.status and vol_project_status_opts[result.status] or "unknown",
                        ))
                items=DIV(TABLE(THEAD(TR(
                    TH("Name"),
                    TH("Start date"),
                    TH("End date"),
                    TH("Description"),
                    TH("Status"))),
                    TBODY(records), _id='list', _class="display"))
            else:
                    items = T('None')

        try:
            label_create_button = s3.crud_strings['vol_project'].label_create_button
        except:
            label_create_button = s3.crud_strings.label_create_button

        add_btn = A(label_create_button, _href=URL(r=request, f='project', args='create'), _id='add-btn')

        output.update(dict(items=items, add_btn=add_btn))

        return output

    else:
        session.error = BADFORMAT
        redirect(URL(r=request))

# Plug into REST controller
s3xrc.model.set_method(module, 'project', method='search_location', action=shn_vol_project_search_location )
