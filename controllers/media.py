# -*- coding: utf-8 -*-

module = 'media'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Bulk Uploader'), False, URL(r=request, f='bulk_upload')]
]

# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db) 

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def metadata():
    "RESTlike CRUD controller"
    resource = 'metadata'
    table = module + '_' + resource
    
    # Model options
    # used in multiple controllers, so in the model
    
    # CRUD Strings
    title_create = T('Add Metadata')
    title_display = T('Metadata Details')
    title_list = T('List Metadata')
    title_update = T('Edit Metadata')
    title_search = T('Search Metadata')
    subtitle_create = T('Add New Metadata')
    subtitle_list = T('Metadata')
    label_list_button = T('List Metadata')
    label_create_button = ADD_METADATA
    msg_record_created = T('Metadata added')
    msg_record_modified = T('Metadata updated')
    msg_record_deleted = T('Metadata deleted')
    msg_list_empty = T('No Metadata currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def image():
    "RESTlike CRUD controller"
    resource = 'image'
    table = module + '_' + resource
    
    # Model options
    # used in multiple controllers, so in the model

    # CRUD Strings
    title_create = T('Add Image')
    title_display = T('Image Details')
    title_list = T('List Image')
    title_update = T('Edit Image')
    title_search = T('Search Image')
    subtitle_create = T('Add New Image')
    subtitle_list = T('Image')
    label_list_button = T('List Image')
    label_create_button = ADD_IMAGE
    msg_record_created = T('Image added')
    msg_record_modified = T('Image updated')
    msg_record_deleted = T('Image deleted')
    msg_list_empty = T('No Image currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def bulk_upload():
    """
    Custom view to allow bulk uploading of photos which are made into GIS Features.
    Lat/Lon can be pulled from an associated GPX track with timestamp correlation.
    """
    
    crud.messages.submit_button = T('Upload')

    form = crud.create(db.media_metadata)
    
    gpx_tracks = OptionsWidget()
    gpx_widget = gpx_tracks.widget(track_id.track_id, track_id.track_id.default)
    gpx_label = track_id.track_id.label
    gpx_comment = track_id.track_id.comment
    #form_gpx = crud.create(db.gis_track)

    response.title = T('Bulk Uploader')
    
    return dict(form=form, gpx_label=gpx_label, gpx_widget=gpx_widget, gpx_comment=gpx_comment, IMAGE_EXTENSIONS=IMAGE_EXTENSIONS)
 