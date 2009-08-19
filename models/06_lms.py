# -*- coding: utf-8 -*-
#
# LMS Logistics Management System
#
# created 2009-07-08 by ajuonline
#
module = 'lms'

# Settings
resource = 'setting'
table = module + '_' + resource
db.define_table(table,
                db.Field('audit_read', 'boolean'),
                db.Field('audit_write', 'boolean'),
                migrate=migrate)
# Populate table with Default options
# - deployments can change these live via appadmin
if not len(db().select(db[table].ALL)): 
   db[table].insert(
        # If Disabled at the Global Level then can still Enable just for this Module here
        audit_read = False,
        audit_write = False
    )
''' Sites Category
resource = 'site_category'
table = module + '_' + resource
db.define_table(table,timestamp,uuidstamp,
                db.Field('name', notnull=True),
                db.Field('description', length=256),
                db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Sites don't have to have unique names
db[table].name.label = T("Site Category")
db[table].name.comment = SPAN("*", _class="req")
title_create = T('Add Site Category')
title_display = T('Site Category Details')
title_list = T('List Categories')
title_update = T('Edit Category')
title_search = T('Search Category(s)')
subtitle_create = T('Add New Site Category')
subtitle_list = T('Site Categories')
label_list_button = T('List Categories')
label_create_button = T('Add Site Category')
msg_record_created = T('Category  added')
msg_record_modified = T('Category updated')
msg_record_deleted = T('Category deleted')
msg_list_empty = T('No Categories currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
'''
# Sites
resource = 'site'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('name', notnull=True),
                db.Field('description', length=256),
				db.Field('category'),
                admin_id,
                person_id,
                db.Field('address', 'text'),
				location_id,
				db.Field('attachment', 'upload', autodelete=True),
                db.Field('comments'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Sites don't have to have unique names
# db[table].site_category_id.requires = IS_IN_DB(db, 'lms_site_category.id', 'lms_site_category.name')
db[table].category.requires=IS_IN_SET(['warehouse'])
# db[table].site_category_id.comment = DIV(A(T('Add Category'), _class='popup', _href=URL(r=request, c='lms', f='site_category', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site Category|The Category of Site.")))
db[table].name.label = T("Site Name")
DIV(A(T('Add Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the main Warehouse/Site information where this Storage location is.")))
db[table].name.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Site Name|A Warehouse/Site is a physical location with an address and GIS data where Items are Stored. It can be a Building, a particular area in a city or anything similar."))
db[table].description.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Site Description|Use this space to add a description about the warehouse/site."))
#db[table].name.comment = SPAN("*", _class="req")
db[table].admin.label = T("Site Manager")
db[table].person_id.label = T("Contact Person")
#db[table].person_id.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Contact Person|The point of contact for this Site. You can create a contact entry by clicking 'Add Person' and enter more details about the person if it does not exists."))
db[table].person_id.represent = lambda id: (id and [(db(db.pr_person.id==id).select()[0].first_name)+' '+(db(db.pr_person.id==id).select()[0].last_name)] or ["None"])[0]
db[table].address.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Site Address|Detailed address of the site for informational/logistics purpose. Please note that you can add GIS/Mapping data about this site in the 'Location' field mentioned below."))
db[table].attachment.label = T("Image/Other Attachment")
db[table].attachment.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Image/Attachment|A snapshot of the location or additional documents that contain supplementary information about the Site can be uploaded here."))
db[table].comments.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Additional Comments|Use this space to add additional comments and notes about the Site/Warehouse."))
title_create = T('Add Site ')
title_display = T('Site Details')
title_list = T('List Sites')
title_update = T('Edit Site')
title_search = T('Search Site(s)')
subtitle_create = T('Add New Site')
subtitle_list = T('Sites')
label_list_button = T('List Sites')
label_create_button = T('Add Site')
msg_record_created = T('Site added')
msg_record_modified = T('Site updated')
msg_record_deleted = T('Site deleted')
msg_list_empty = T('No Sites currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Storage Locations
resource = 'storage_loc'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('site_id', db.lms_site),
                db.Field('name', notnull=True),
                db.Field('description', length=256),
                location_id,
                db.Field('capacity'),
                db.Field('max_weight'),
				db.Field('attachment', 'upload', autodelete=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Storage Locations don't have to have unique names
db[table].site_id.label = T("Site")
db[table].site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name')
db[table].site_id.comment = DIV(A(T('Add Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the main Warehouse/Site information where this Storage location is.")))
db[table].name.label = T("Storage Location Name")
db[table].name.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Site Location Name|A place within a Site like a Shelf, room, bin number etc."))
db[table].description.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Site Location Description|Use this space to add a description about the site location."))
db[table].capacity.label = T("Capacity (W x D X H)")
db[table].capacity.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Volume Capacity|Dimensions of the storage location. Input in the following format 1 x 2 x 3 for width x depth x height followed by choosing the unit from the drop down list."))
db[table].max_weight.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Maximum Weight| Maximum weight capacity of the Storage Location followed by choosing the unit from the drop down list."))
db[table].attachment.label = T("Image/Other Attachment")
db[table].attachment.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Image/Attachment|A snapshot of the location or additional documents that contain supplementary information about the Site Location can be uploaded here."))
title_create = T('Add Storage Location ')
title_display = T('Storage Location Details')
title_list = T('List Storage Location')
title_update = T('Edit Storage Location')
title_search = T('Search Storage Location(s)')
subtitle_create = T('Add New Site')
subtitle_list = T('Storage Locations')
label_list_button = T('List Storage Locations')
label_create_button = T('Add Storage Location')
msg_record_created = T('Storage Location added')
msg_record_modified = T('Storage Location updated')
msg_record_deleted = T('Storage Location deleted')
msg_list_empty = T('No Storage Locations currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Storage Bin Type
resource = 'storage_bin_type'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('name', notnull=True),
                db.Field('description'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Storage Bin Type|Name of Storage Bin Type."))
db[table].description.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Description of Bin Type|Use this space to add a description about the Bin Type."))
title_create = T('Add Storage Bin Type')
title_display = T('Storage Bin Type Details')
title_list = T('List Storage Bin Type(s)')
title_update = T('Edit Storage Bin Type(s)')
title_search = T('Search Storage Bin Type(s)')
subtitle_create = T('Add New Bin Type')
subtitle_list = T('Storage Bin Types')
label_list_button = T('List Storage Bin Type(s)')
label_create_button = T('Add Storage Bin Type(s)')
msg_record_created = T('Storage Bin Type added')
msg_record_modified = T('Storage Bin Type updated')
msg_record_deleted = T('Storage Bin Type deleted')
msg_list_empty = T('No Storage Bin Type currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Storage Bins
resource = 'storage_bin'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('number', notnull=True),
				db.Field('storage_id', db.lms_storage_loc),
                db.Field('bin_type', db.lms_storage_bin_type),
                db.Field('capacity', length=256),
				db.Field('max_weight'),
				db.Field('attachment', 'upload', autodelete=True),
				db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].number.requires = IS_NOT_EMPTY()   # Storage Bin Numbers don't have to have unique names
db[table].bin_type.requires = IS_IN_DB(db, 'lms_storage_bin_type.id', 'lms_storage_bin_type.name')
db[table].bin_type.comment = DIV(A(T('Add Storage Bin Type'), _class='popup', _href=URL(r=request, c='lms', f='storage_bin_type', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Storage Bin|Add the Storage Bin Type.")))
db[table].storage_id.requires = IS_IN_DB(db, 'lms_storage_loc.id', 'lms_storage_loc.name')
db[table].storage_id.comment = DIV(A(T('Add Storage Location'), _class='popup', _href=URL(r=request, c='lms', f='storage_loc', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the Storage Location where this bin is located.")))
db[table].number.label = T("Storage Bin Number")
db[table].number.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Storage Bin Number|Identification label of the Storage bin."))
db[table].storage_id.label = T("Storage Location ID")
db[table].attachment.label = T("Image/Other Attachment")
db[table].capacity.label = T("Capacity (W x D X H)")
db[table].capacity.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Volume Capacity|Dimensions of the storage bin. Input in the following format 1 x 2 x 3 for width x depth x height followed by choosing the unit from the drop down list."))
db[table].max_weight.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Maximum Weight| Maximum weight capacity of the items the storage bin can contain. followed by choosing the unit from the drop down list."))
db[table].attachment.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Image/Attachment|A snapshot of the bin or additional documents that contain supplementary information about it can be uploaded here."))
title_create = T('Add Storage Bin ')
title_display = T('Storage Bin Details')
title_list = T('List Storage Bins')
title_update = T('Edit Storage Bins')
title_search = T('Search Storage Bin(s)')
subtitle_create = T('Add New Bin')
subtitle_list = T('Storage Bins')
label_list_button = T('List Storage Bins')
label_create_button = T('Add Storage Bins')
msg_record_created = T('Storage Bin added')
msg_record_modified = T('Storage Bin updated')
msg_record_deleted = T('Storage Bin deleted')
msg_list_empty = T('No Storage Bins currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Relief Item Catalogue Category
resource = 'catalogue_cat'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('name'),
                db.Field('description'),
				db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T("Relief Item Category")
db[table].name.comment = SPAN("*", _class="req")
title_create = T('Add Relief Item Category ')
title_display = T('Relief Item Category Details')
title_list = T('List Relief Item Categories')
title_update = T('Edit Relief Item Categories')
title_search = T('Search Relief Item Category(s)')
subtitle_create = T('Add New Relief Item Category')
subtitle_list = T('Relief Item Categories')
label_list_button = T('List Relief Item Categories')
label_create_button = T('Add Relief Item Categories')
msg_record_created = T('Relief Item Category added')
msg_record_modified = T('Relief Item Category updated')
msg_record_deleted = T('Relief Item Category deleted')
msg_list_empty = T('No Relief Item Category currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Relief Item Catalogue Sub-Category
resource = 'catalogue_subcat'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('parent_category', db.lms_catalogue_cat),
				db.Field('name'),
                db.Field('description'),
				db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T("Relief Item Sub-Category")
db[table].name.comment = SPAN("*", _class="req")
db[table].parent_category.requires = IS_IN_DB(db, 'lms_catalogue_cat.id', 'lms_catalogue_cat.name')
db[table].parent_category.comment = DIV(A(T('Add Relief Item Category'), _class='popup', _href=URL(r=request, c='lms', f='catalogue_cat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Relief Item Category.")))
title_create = T('Add Relief Item Sub-Category ')
title_display = T('Relief Item Sub-Category Details')
title_list = T('List Relief Item Sub-Categories')
title_update = T('Edit Relief Item Sub-Categories')
title_search = T('Search Relief Item Sub-Category(s)')
subtitle_create = T('Add New Relief Item Sub-Category')
subtitle_list = T('Relief Item Sub-Categories')
label_list_button = T('List Relief Item Sub-Categories')
label_create_button = T('Add Relief Item Sub-Categories')
msg_record_created = T('Relief Item Sub-Category added')
msg_record_modified = T('Relief Item Sub-Category updated')
msg_record_deleted = T('Relief Item Sub-Category deleted')
msg_list_empty = T('No Relief Item Sub-Category currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Items
resource = 'item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('ordered_list_item'),
				db.Field('airway_bill'),
				db.Field('name'),
                db.Field('description'),
				db.Field('category', db.lms_catalogue_cat),
				db.Field('sub_category', db.lms_catalogue_subcat),
				db.Field('sender', db.or_organisation),
				db.Field('recipient', db.or_organisation),
				db.Field('designated'),
				db.Field('quantity', 'double', default=0.00),
				db.Field('shortage', 'double', default=0.00),
				db.Field('net_quantity', default=0.00, writable=False),
				db.Field('measure_unit'),
				db.Field('specifications'),
				db.Field('unit_size', 'integer', default=1, notnull=True),
				db.Field('weight', 'double', default=0.00),
				db.Field('date_time', 'datetime'),
				db.Field('comments', 'text'),
				db.Field('attachment', 'upload', autodelete=True),
				db.Field('price', 'double', default=0.00),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].ordered_list_item.requires = IS_NOT_EMPTY()
db[table].name.requires = IS_NOT_EMPTY()
db[table].ordered_list_item.label = T("Ordered List Item")
db[table].ordered_list_item.comment = SPAN("*", _class="req")
db[table].airway_bill.label = T("Air Way Bill (AWB)")
db[table].airway_bill.comment = SPAN("*", _class="req")
db[table].name.label = T("Product Name")
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T("Product Description")
db[table].category.requires = IS_IN_DB(db, 'lms_catalogue_cat.id', 'lms_catalogue_cat.name')
db[table].category.comment = DIV(A(T('Add Relief Item Category'), _class='popup', _href=URL(r=request, c='lms', f='catalogue_cat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Relief Item Category.")))
db[table].sub_category.requires = IS_IN_DB(db, 'lms_catalogue_subcat.id', 'lms_catalogue_subcat.name')
db[table].sub_category.comment = DIV(A(T('Add Relief Item Sub-Category'), _class='popup', _href=URL(r=request, c='lms', f='catalogue_subcat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Relief Item Sub-Category.")))
db[table].sender.requires = IS_IN_DB(db, 'or_organisation.id', 'or_organisation.name')
db[table].sender.comment = DIV(A(T('Add Sender Organisation'), _class='popup', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sender.")))
db[table].recipient.requires = IS_IN_DB(db, 'or_organisation.id', 'or_organisation.name')
db[table].recipient.comment = DIV(A(T('Add Recipient/Organisation'), _class='popup', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Recipient.")))
db[table].designated.label = T("Designated for")
db[table].measure_unit.label = T("Unit of measure")
db[table].designated.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Designated for|The item is designated to be sent for specific project, population, village or other earmarking of the donation such as a Grant Code."))
db[table].measure_unit.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Unit of Measure|Packing Type/Unit Size for e.g. A Case, A ton, Dozen etc."))
db[table].specifications.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Specifications|additional quantity quantifier – i.e. “4mx5m”."))
db[table].date_time.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Date/Time|Date and Time of Goods receipt. By default shows the current time but can be modified by editing in the drop down list."))
title_create = T('Add Relief Item')
title_display = T('Relief Item Details')
title_list = T('List Relief Item(s)')
title_update = T('Edit Relief Item(s)')
title_search = T('Search Relief Item(s)')
subtitle_create = T('Add New Relief Item')
subtitle_list = T('Relief Items')
label_list_button = T('List Relief Item')
label_create_button = T('Add Relief Item')
msg_record_created = T('Relief Item added')
msg_record_modified = T('Relief Item updated')
msg_record_deleted = T('Relief Item deleted')
msg_list_empty = T('No Relief Item currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)