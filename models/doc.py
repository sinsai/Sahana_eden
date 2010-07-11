# -*- coding: utf-8 -*-

"""
    Document Library
"""

module = "doc"

# Settings
resource = "setting"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field("audit_read", "boolean"),
                Field("audit_write", "boolean"),
                migrate=migrate)

resource = "metadata"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                location_id,
                Field("description"),
                person_id,
                #Field("organisation.id", "reference org_organisation"),
                Field("source"),
                Field("sensitivity"),    # Should be turned into a drop-down by referring to AAA's sensitivity table
                Field("event_time", "datetime"),
                Field("expiry_time", "datetime"),
                Field("url"),
                migrate=migrate)
table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
table.event_time.requires = IS_NULL_OR(IS_DATETIME())
table.expiry_time.requires = IS_NULL_OR(IS_DATETIME())
table.url.requires = IS_NULL_OR(IS_URL())
ADD_METADATA = Tstr("Add Metadata")
metadata_id = db.Table(None, "metadata_id",
            Field("metadata_id", db.doc_metadata,
                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_metadata.id", "%(name)s")),
                represent = lambda id: (id and [db(db.doc_metadata.id==id).select()[0].name] or ["None"])[0],
                label = T("Metadata"),
                comment = DIV(A(ADD_METADATA, _class="colorbox", _href=URL(r=request, c="doc", f="metadata", args="create", vars=dict(format="popup")), _target="top", _title=ADD_METADATA),
                          DIV( _class="tooltip", _title=ADD_METADATA + "|" + "Add some metadata for the file, such as Soure, Sensitivity, Event Time.")),
                ondelete = "RESTRICT"
                ))

resource = "image"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
                Field("name", length=128, notnull=True, unique=True),
                location_id,
                metadata_id,
                Field("image", "upload"),
                migrate=migrate)
table.name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.name.comment = SPAN("*", _class="req")
# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "uploads/images")
IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "tif", "TIF", "tiff", "TIFF", "bmp", "BMP", "raw", "RAW"]
table.image.requires = IS_IMAGE(extensions=(IMAGE_EXTENSIONS))
ADD_IMAGE = Tstr("Add Image")
image_id = db.Table(None, "image_id",
            Field("image_id", db.doc_image,
                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_image.id", "%(name)s")),
                represent = lambda id: (id and [DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=db(db.doc_image.id == id).select(db.doc_image.image, limitby=(0, 1)).first().image), _height=40), _class="zoom", _href="#zoom-media_image-%s" % id), DIV(IMG(_src=URL(r=request, c="default", f="download", args=db(db.doc_image.id == id).select(db.doc_image.image, limitby=(0, 1)).first().image),_width=600), _id="zoom-media_image-%s" % id, _class="hidden"))] or [""])[0],
                label = T("Image"),
                comment = DIV(A(ADD_IMAGE, _class="colorbox", _href=URL(r=request, c="doc", f="image", args="create", vars=dict(format="popup")), _target="top", _title=ADD_IMAGE),
                          DIV( _class="tooltip", _title=ADD_IMAGE + "|" + Tstr("Add an image, such as a Photo."))),
                ondelete = "RESTRICT"
                ))
