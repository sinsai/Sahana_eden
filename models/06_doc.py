# -*- coding: utf-8 -*-

"""
    Document Library
"""

module = "doc"
#==============================================================================
resourcename = "document"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("file", "upload", autodelete=True,),
                        Field("url"),
                        person_id(),
                        organisation_id(),
                        location_id(),
                        Field("date", "date"),
                        comments(),
                        Field("entered", "boolean"),
                        Field("checksum", readable=False, writable=False),
                        migrate=migrate, *s3_meta_fields())


table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
#table.name.label = T("Name")

def shn_file_represent( file, table):
    if file:
        return A(table.file.retrieve(file)[0],
                 _href=URL(r=request, f="download", args=[file]))
    else:
        return NONE

table.file.represent = lambda file, table=table: shn_file_represent(file, table)
table.url.label = T("URL")
table.url.represent = lambda url: url and A(url,_href=url) or NONE

table.url.requires = [IS_NULL_OR(IS_URL()), IS_NULL_OR(IS_NOT_ONE_OF(db, "%s.url" % tablename))]

table.person_id.label = T("Author")
table.person_id.comment = shn_person_comment(T("Author"), T("The Author of this Document (optional)"))

table.location_id.readable = table.location_id.writable = False

table.entered.comment = DIV( _class="tooltip",
                             _title="Entered" + "|" + T("Has data from this Reference Document been entered into Sahana?")
                             )

# -----------------------------------------------------------------------------
def document_represent(id):
    if not id:
        return NONE
    represent = shn_get_db_field_value(db = db,
                                       table = "doc_document",
                                       field = "name",
                                       look_up = id)
    #File
    #Website
    #Person
    return A ( represent,
               _href = URL(r=request, c="doc", f="document", args = [id], extension = ""),
               _target = "blank"
               )

DOCUMENT = T("Reference Document")
ADD_DOCUMENT = T("Add Reference Document")

document_comment = DIV( A( ADD_DOCUMENT,
                           _class="colorbox",
                           _href=URL(r=request, c="doc", f="document", args="create", vars=dict(format="popup")),
                           _target="top",
                           _title=T("If you need to add a new document then you can click here to attach one."),
                           ),
                        DIV( _class="tooltip",
                             _title=DOCUMENT + "|" + \
                             T("A Reference Document such as a file, URL or contact person to verify this data. You can type the 1st few characters of the document name to link to an existing document."),
                             #T("Add a Reference Document such as a file, URL or contact person to verify this data. If you do not enter a Reference Document, your email will be displayed instead."),
                             ),
                        #SPAN( I( T("If you do not enter a Reference Document, your email will be displayed to allow this data to be verified.") ),
                        #     _style = "color:red"
                        #     )
                        )

# CRUD Strings
LIST_DOCUMENTS = T("List Documents")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_DOCUMENT,
    title_display = T("Document Details"),
    title_list = LIST_DOCUMENTS,
    title_update = T("Edit Document"),
    title_search = T("Search Documents"),
    subtitle_create = T("Add New Document"),
    subtitle_list = DOCUMENT,
    label_list_button = LIST_DOCUMENTS,
    label_create_button = ADD_DOCUMENT,
    label_delete_button = T("Delete Document"),
    msg_record_created = T("Document added"),
    msg_record_modified = T("Document updated"),
    msg_record_deleted = T("Document deleted"),
    msg_list_empty = T("No Documents found"))

document_id = S3ReusableField("document_id",
                              table,
                              requires = IS_NULL_OR(IS_ONE_OF(db, "doc_document.id", document_represent, orderby="doc_document.name")),
                              represent = document_represent,
                              label = DOCUMENT,
                              comment = document_comment,
                              ondelete = "RESTRICT",
                              widget = S3AutocompleteWidget(request, module, resourcename)
                             )

def document_onvalidation(form):

    import cgi

    table = db.doc_document

    doc = form.vars.file
    url = form.vars.url

    if not hasattr(doc, "file"):
        id = request.post_vars.id
        if id:
            record = db(table.id == id).select(table.file, limitby=(0, 1)).first()
            if record:
                doc = record.file

    if not hasattr(doc, "file") and not doc and not url:
        form.errors.file = \
        form.errors.url = T("Either file upload or document URL required.")

    if isinstance(doc, cgi.FieldStorage) and doc.filename:
        f = doc.file
        form.vars.checksum = docChecksum(f.read())
        f.seek(0)
    if form.vars.checksum is not None:
        result = db(table.checksum == form.vars.checksum).select(table.name, limitby=(0, 1)).first()
        if result:
            doc_name = result.name
            form.errors["file"] = T("This file already exists on the server as") + " %s" % (doc_name)
    return

s3xrc.model.configure(table,
                      mark_required=["file"],
                      onvalidation=document_onvalidation)
#==============================================================================
resourcename = "image"
tablename = "%s_%s" % (module, resourcename)
table = db.define_table(tablename,
                        Field("name", length=128, notnull=True, unique=True),
                        Field("image", "upload", autodelete=True),
                        # Web2Py r2867+ includes this functionality by default
                        #Field("image", "upload", autodelete=True, widget=S3UploadWidget.widget),
                        Field("url"),
                        person_id(),
                        organisation_id(),
                        location_id(),
                        Field("date", "date"),
                        comments(),
                        Field("checksum", readable=False, writable=False),
                        migrate=migrate, *s3_meta_fields())

table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]
table.name.label = T("Name")
table.url.requires = IS_NULL_OR(IS_URL())
table.url.label = T("URL")
table.person_id.label = T("Person")

# upload folder needs to be visible to the download() function as well as the upload
table.image.uploadfolder = os.path.join(request.folder, "uploads/images")
IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "tif", "TIF", "tiff", "TIFF", "bmp", "BMP", "raw", "RAW"]
table.image.requires = IS_IMAGE(extensions=(IMAGE_EXTENSIONS))
#table.image.requires = IS_EMPTY_OR(IS_IMAGE(extensions=(IMAGE_EXTENSIONS)))
table.image.represent = lambda image: image and \
        DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=image),_height=60, _alt=T("View Image")),
              _href=URL(r=request, c="default", f="download", args=image))) or \
        T("No Image")

ADD_IMAGE = T("Add Photo")
image_id = S3ReusableField("image_id", db.doc_image,
                requires = IS_NULL_OR(IS_ONE_OF(db, "doc_image.id", "%(name)s")),
                represent = lambda id: (id and [DIV(A(IMG(_src=URL(r=request, c="default", f="download", args=db(db.doc_image.id == id).select(db.doc_image.image, limitby=(0, 1)).first().image), _height=40), _class="zoom", _href="#zoom-media_image-%s" % id), DIV(IMG(_src=URL(r=request, c="default", f="download", args=db(db.doc_image.id == id).select(db.doc_image.image, limitby=(0, 1)).first().image),_width=600), _id="zoom-media_image-%s" % id, _class="hidden"))] or [""])[0],
                label = T("Image"),
                comment = DIV(A(ADD_IMAGE, _class="colorbox", _href=URL(r=request, c="doc", f="image", args="create", vars=dict(format="popup")), _target="top", _title=ADD_IMAGE),
                          DIV( _class="tooltip", _title=ADD_IMAGE + "|" + T("Add an Photo."))),
                ondelete = "RESTRICT"
                )

# CRUD Strings
LIST_IMAGES = T("List Photos")
s3.crud_strings[tablename] = Storage(
    title_create = ADD_IMAGE,
    title_display = T("Photo Details"),
    title_list = LIST_IMAGES,
    title_update = T("Edit Photo"),
    title_search = T("Search Photos"),
    subtitle_create = T("Add New Photo"),
    subtitle_list = T("Photo"),
    label_list_button = LIST_IMAGES,
    label_create_button = ADD_IMAGE,
    label_delete_button = T("Delete Photo"),
    msg_record_created = T("Photo added"),
    msg_record_modified = T("Photo updated"),
    msg_record_deleted = T("Photo deleted"),
    msg_list_empty = T("No Photos found"))

def image_onvalidation(form):

    import cgi

    table = db.doc_image

    img = form.vars.image

    if not hasattr(img, "file"):
        id = request.post_vars.id
        if id:
            record = db(table.id == id).select(table.image, limitby=(0, 1)).first()
            if record:
                img = record.image

    if isinstance(img, cgi.FieldStorage) and img.filename:
        f = img.file
        form.vars.checksum = docChecksum(f.read())
        f.seek(0)
    if form.vars.checksum is not None:
        result = db(table.checksum == form.vars.checksum).select(table.name, limitby=(0, 1)).first()
        if result:
            image_name = result.name
            form.errors["image"] = T("This file already exists on the server as") + " %s" % (image_name)
    return

s3xrc.model.configure(table,
                      onvalidation=image_onvalidation)

#==============================================================================
