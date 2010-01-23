# -*- coding: utf-8 -*-

module = 'admin'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

# Import Jobs
resource = 'import_job'
table = '%s_%s' % (module, resource)
db.define_table(table,
                Field('module', 'string',
                      default='or', notnull=True),
                Field('resource', 'string',
                      widget=SQLFORM.widgets.options.widget,
                      default='organization', notnull=True),
                Field('description', 'string', notnull=True),
                Field('source_file', 'upload', notnull=True),
                Field('status', 'string', default='new', writable=False),
                )
db[table].module.requires = IS_IN_DB(db, 's3_module.name', '%(name_nice)s')
db[table].resource.requires = IS_IN_SET(['organization', 'office', 'contact'])
db[table].status.requires = IS_IN_SET(['new', 'failed', 'processing', 'completed'])
