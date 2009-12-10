# -*- coding: utf-8 -*-

module = 'media'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                Field('audit_read', 'boolean'),
                Field('audit_write', 'boolean'),
                migrate=migrate)

resource = 'metadata'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                location_id,
                Field('description'),
                person_id,
                #Field('organisation.id', 'reference or_organisation'),
                Field('source'),
                Field('accuracy'),       # Drop-down on a IS_IN_SET[]?
                Field('sensitivity'),    # Should be turned into a drop-down by referring to AAA's sensitivity table
                Field('event_time', 'datetime'),
                Field('expiry_time', 'datetime'),
                Field('url'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].description.label = T('Description')
db[table].person_id.label = T("Contact")
db[table].source.label = T('Source')
db[table].accuracy.label = T('Accuracy')
db[table].sensitivity.label = T('Sensitivity')
db[table].event_time.requires = IS_NULL_OR(IS_DATETIME())
db[table].event_time.label = T('Event Time')
db[table].expiry_time.requires = IS_NULL_OR(IS_DATETIME())
db[table].expiry_time.label = T('Expiry Time')
db[table].url.requires = IS_NULL_OR(IS_URL())
db[table].url.label = 'URL'
ADD_METADATA = T('Add Metadata')
metadata_id = SQLTable(None, 'metadata_id',
            Field('metadata_id', db.media_metadata,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'media_metadata.id', '%(name)s')),
                represent = lambda id: (id and [db(db.media_metadata.id==id).select()[0].name] or ["None"])[0],
                label = T('Metadata'),
                comment = DIV(A(ADD_METADATA, _class='thickbox', _href=URL(r=request, c='media', f='metadata', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_METADATA), A(SPAN("[Help]"), _class="tooltip", _title=T("Metadata|FIXME: Add some useful text here."))),
                ondelete = 'RESTRICT'
                ))

resource = 'image'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, authorstamp, deletion_status,
                location_id,
                metadata_id,
                Field('image', 'upload'),
                migrate=migrate)
# upload folder needs to be visible to the download() function as well as the upload
db[table].image.uploadfolder = os.path.join(request.folder, "uploads/images")
IMAGE_EXTENSIONS = ['png', 'PNG', 'jpg', 'JPG', 'jpeg', 'JPEG', 'gif', 'GIF', 'tif', 'TIF', 'bmp', 'BMP']
db[table].image.requires = IS_IMAGE(extensions=(IMAGE_EXTENSIONS))
ADD_IMAGE = T('Add Image')
image_id = SQLTable(None, 'image_id',
            Field('image_id', db.media_image,
                requires = IS_NULL_OR(IS_ONE_OF(db, 'media_image.id', '%(name)s')),
                represent = lambda id: (id and [DIV(A(IMG(_src=URL(r=request, c='default', f='download', args=db(db.media_image.id==id).select()[0].image), _height=40), _class='zoom', _href='#zoom-media_image-%s' % id), DIV(IMG(_src=URL(r=request, c='default', f='download', args=db(db.media_image.id==id).select()[0].image),_width=600), _id='zoom-media_image-%s' % id, _class='hidden'))] or [''])[0],
                label = T('Image'),
                comment = DIV(A(ADD_IMAGE, _class='thickbox', _href=URL(r=request, c='media', f='image', args='create', vars=dict(format='popup', KeepThis='true'))+"&TB_iframe=true", _target='top', _title=ADD_IMAGE), A(SPAN("[Help]"), _class="tooltip", _title=T("Photo|Add a Photo to describe this."))),
                ondelete = 'RESTRICT'
                ))
