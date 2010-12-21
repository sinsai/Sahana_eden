# -*- coding: utf-8 -*-

"""
    Document Library - Controllers

    @author: Fran Boon
    @author: Michael Howden
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [ [T("Documents"), False, URL(r=request, f="document"),[
                            [T("List"), False, URL(r=request, f="document")],
                            [T("Add"), False, URL(r=request, f="document", args="create")],
                            #[T("Search"), False, URL(r=request, f="ireport", args="search")]
                        ]],
                          [T("Photos"), False, URL(r=request, f="image"),[
                            [T("List"), False, URL(r=request, f="image")],
                            [T("Add"), False, URL(r=request, f="image", args="create")],
                            #[T("Search"), False, URL(r=request, f="ireport", args="search")]
                        ]],
                          #[T("Bulk Uploader"), False, URL(r=request, f="bulk_upload")]
                        ]

#==============================================================================
# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db)

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

#==============================================================================
# Used to display the number of Components in the tabs
def shn_document_tabs(jr):

    tab_opts = [{"tablename": "assess_rat",
                 "resource": "rat",
                 "one_title": T("1 Assessment"),
                 "num_title": " Assessments",
                },
                {"tablename": "irs_ireport",
                 "resource": "ireport",
                 "one_title": "1 Incident Report",
                 "num_title": " Incident Reports",
                },
                {"tablename": "inventory_store",
                 "resource": "store",
                 "one_title": "1 Warehouse",
                 "num_title": " Warehouses",
                },
                {"tablename": "cr_shelter",
                 "resource": "shelter",
                 "one_title": "1 Shelter",
                 "num_title": " Shelters",
                },
                {"tablename": "flood_freport",
                 "resource": "freport",
                 "one_title": "1 Flood Report",
                 "num_title": " Flood Reports",
                },
                {"tablename": "rms_req",
                 "resource": "req",
                 "one_title": "1 Request",
                 "num_title": " Requests",
                },
                ]
    tabs = [(T("Details"), None)]
    for tab_opt in tab_opts:
        tablename = tab_opt["tablename"]
        if tablename in db and document_id in db[tablename]:
            tab_count = db( (db[tablename].deleted == False) & (db[tablename].document_id == jr.id) ).count()
            if tab_count == 0:
                label = shn_get_crud_string(tablename, "title_create")
            elif tab_count == 1:
                label = tab_opt["one_title"]
            else:
                label = T(str(tab_count) + tab_opt["num_title"] )
            tabs.append( (label, tab_opt["resource"] ) )

    return tabs

def shn_document_rheader(r):
    if r.representation == "html":
        doc_document = r.record
        if doc_document:
            rheader_tabs = shn_rheader_tabs(r, shn_document_tabs(r))
            table = db.doc_document
            rheader = DIV(B(T("Name") + ": "),doc_document.name,
                        TABLE(TR(
                                TH("%s: " % T("File")), table.file.represent( doc_document.file ),
                                TH("%s: " % T("URL")), table.url.represent( doc_document.url ),
                                ),
                                TR(
                                TH(T("Organization") + ": "), table.organisation_id.represent( doc_document.organisation_id ),
                                TH(T("Person") + ": "), table.person_id.represent( doc_document.organisation_id ),
                                ),
                            ),
                        rheader_tabs
                        )
            return rheader
    return None

def document():
    """ RESTful CRUD controller """

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    # used in multiple controllers, so in the model

    rheader = lambda r: shn_document_rheader(r)

    output = s3_rest_controller(module, resource,
                                 rheader=rheader)

    return output
#==============================================================================
def image():
    """ RESTful CRUD controller """

    s3xrc.model.configure(db.doc_image,
        create_onvalidation=image_onvalidation,
        update_onvalidation=image_onvalidation)

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    # used in multiple controllers, so in the model

    output = s3_rest_controller(module, resource)

    return output
#==============================================================================
def bulk_upload():
    """
        Custom view to allow bulk uploading of Photos

        @ToDo: Allow creation of a GIS Feature Layer to view on the map
        @ToDo: Allow uploading of associated GPX track for timestamp correlation.
        See r1595 for the previous draft of this work
    """

    response.extra_styles = ["S3/fileuploader.css"]
    return dict()

def upload_bulk():
    """
        Receive the Uploaded data from bulk_upload()

        https://github.com/valums/file-uploader/blob/master/server/readme.txt

        @ToDo: Read EXIF headers to locate the Photos
    """

    import cgi

    source = request.post_vars.get("qqfile", None)
    if isinstance(source, cgi.FieldStorage) and source.filename:
        # For IE6-8, Opera, older versions of other browsers you get the file as you normally do with regular form-base uploads.
        name = source.filename
        image = source.file

    else:
        # For browsers which upload file with progress bar, you will need to get the raw post data and write it to the file.
        if "name" in request.vars:
            name = request.vars.name
        else:
            HTTP(400, "Invalid Request: Need a Name!")

        image = request.body.read()
        # Convert to StringIO for onvalidation/import
        import StringIO
        image = StringIO.StringIO(image)

    form = Storage()
    form.vars = Storage()
    form.vars.name = name
    form.vars.image = image

    # onvalidation callback
    # @ToDo: Generalise by reading s3xrc.model
    image_onvalidation(form)
        
    # Add the file to the database
    # @ToDo handle theimage: currently it's a str
    #success = db.doc_image.insert(name=name, image=image)
    if form.accepts():
        success = True
    else:
        success = False

    # onaccept callback
    # @ToDo: Generalise in case available

    if success:
        msg = "{'success':true}"
    else:
        msg = "{'error':'sorry, no dice'}"

    response.headers["Content-Type"] = "text/html"  # This is what the file-uploader widget expects
    return msg

#==============================================================================
# END - Following code is not utilised
#==============================================================================
def upload(module, resource, table, tablename, onvalidation=None, onaccept=None):
    # Receive file ( from import_url() )
    record = Storage()

    for var in request.vars:

        # Skip the Representation
        if var == "format":
            continue
        elif var == "uuid":
            uuid = request.vars[var]
        elif table[var].type == "upload":
            # Handle file uploads (copied from gluon/sqlhtml.py)
            field = table[var]
            fieldname = var
            f = request.vars[fieldname]
            fd = fieldname + "__delete"
            if f == "" or f is None:
                #if request.vars.get(fd, False) or not self.record:
                if request.vars.get(fd, False):
                    record[fieldname] = ""
                else:
                    #record[fieldname] = self.record[fieldname]
                    pass
            elif hasattr(f, "file"):
                (source_file, original_filename) = (f.file, f.filename)
            elif isinstance(f, (str, unicode)):
                ### do not know why this happens, it should not
                (source_file, original_filename) = \
                    (cStringIO.StringIO(f), "file.txt")
            newfilename = field.store(source_file, original_filename)
            request.vars["%s_newfilename" % fieldname] = record[fieldname] = newfilename
            if field.uploadfield and not field.uploadfield==True:
                record[field.uploadfield] = source_file.read()
        else:
            record[var] = request.vars[var]

    # Validate record
    for var in record:
        if var in table.fields:
            value = record[var]
            (value, error) = s3xrc.xml.validate(table, original, var, value)
        else:
            # Shall we just ignore non-existent fields?
            # del record[var]
            error = "Invalid field name."
        if error:
            raise HTTP(400, body=s3xrc.xml.json_message(False, 400, var + " invalid: " + error))
        else:
            record[var] = value

    form = Storage()
    form.method = method
    form.vars = record

    # Onvalidation callback
    if onvalidation:
        onvalidation(form)

    # Create/update record
    try:
        if jr.component:
            record[jr.fkey]=jr.record[jr.pkey]
        if method == "create":
            id = table.insert(**dict(record))
            if id:
                error = 201
                item = s3xrc.xml.json_message(True, error, "Created as " + str(jr.other(method=None, record_id=id)))
                form.vars.id = id
                if onaccept:
                    onaccept(form)
            else:
                error = 403
                item = s3xrc.xml.json_message(False, error, "Could not create record!")

        elif method == "update":
            result = db(table.uuid==uuid).update(**dict(record))
            if result:
                error = 200
                item = s3xrc.xml.json_message(True, error, "Record updated.")
                form.vars.id = original.id
                if onaccept:
                    onaccept(form)
            else:
                error = 403
                item = s3xrc.xml.json_message(False, error, "Could not update record!")

        else:
            error = 501
            item = s3xrc.xml.json_message(False, error, "Unsupported Method!")
    except:
        error = 400
        item = s3xrc.xml.json_message(False, error, "Invalid request!")

    raise HTTP(error, body=item)
