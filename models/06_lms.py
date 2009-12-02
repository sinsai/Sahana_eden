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


# Unit Option fields for both Length and Weight used throughout LMS
# Also an arbitrary measure of unit

# This part defines the types of Units we deal here. Categories of Units.
lms_unit_type_opts = {
    1:T('Length'),
    2:T('Weight'),
    3:T('Volume - Fluids'),
    4:T('Volume - Solids'),
	5:T('Real World Arbitrary Units')
    }

opt_lms_unit_type = SQLTable(None, 'opt_lms_unit_type',
                    db.Field('opt_lms_unit_type', 'integer',
                    requires = IS_IN_SET(lms_unit_type_opts),
                    default = 1,
                    label = T('Unit Set'),
                    represent = lambda opt: opt and lms_unit_type_opts[opt]))

resource = 'unit'
table = module + '_' + resource
db.define_table(table, timestamp, deletion_status,
                opt_lms_unit_type, #lms_unit_type_opts --> Type of Unit
                Field('label'), #short code of Unit for e.g. "m" for "meter"
                Field('name'),  #complete Unit - "meter" for "m"
                Field('base_unit'), #links to which unit
                Field('multiplicator', 'double', default=1.0), #by default 1 thisi s what links
                migrate=migrate)

if not db(db[table].id).count():
    db[table].insert(
        opt_lms_unit_type=1,
        label="m",
        name="Meters"
    )
    db[table].insert(
        opt_lms_unit_type=2,
        label="kg",
        name="Kilograms"
    )
    db[table].insert(
        opt_lms_unit_type=3,
        label="l",
        name="Litres"
    )
    db[table].insert(
        opt_lms_unit_type=4,
        label="cbm",
        name="Cubic Meters"
    )
    db[table].insert(
        opt_lms_unit_type=5,
        label="ton",
        name="Tonne"
    )

db[table].base_unit.requires = IS_NULL_OR(IS_ONE_OF(db, "lms_unit.label", "lms_unit.name"))
#db[table].base_unit.requires=IS_NULL_OR(IS_UNIT(db))
db[table].label.requires=IS_NOT_IN_DB(db, '%s.label' % table)
db[table].label.label = T('Unit')
db[table].label.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Label| Unit Short Code for e.g. m for meter."))
db[table].name.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Unit Name| Complete Unit Label for e.g. meter for m."))
db[table].base_unit.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Base Unit| The entered unit links to this unit. For e.g. if you are entering m for meter then choose kilometer(if it exists) and enter the value 0.001 as multiplicator."))
db[table].multiplicator.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Multiplicator| If Unit = m, Base Unit = Km, then multiplicator is 0.0001 since 1m = 0.001 km."))
title_create = T('Add Unit ')
title_display = T('Unit Details')
title_list = T('List Units')
title_update = T('Edit Unit')
title_search = T('Search Unit(s)')
subtitle_create = T('Add New Unit')
subtitle_list = T('Units of Measure')
label_list_button = T('List Units')
label_create_button = T('Add Unit')
msg_record_created = T('Unit added')
msg_record_modified = T('Unit updated')
msg_record_deleted = T('Unit deleted')
msg_list_empty = T('No Units currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Sites
site_category_opts = {
    1:T('Donor'),
    2:T('Miscellaneous'),
	3:T('Office'),
	4:T('Project'),
	5:T('Vendor'),
	6:T('Warehouse')
    }
opt_site_category = SQLTable(None, 'site_category_type',
                        Field('category', 'integer', notnull=True,
                            requires = IS_IN_SET(site_category_opts),
                            default = 1,
                            label = T('Category'),
                            represent = lambda opt: opt and site_category_opts[opt]))
resource = 'site'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('name', notnull=True),
                db.Field('description'),
				opt_site_category,
                admin_id,
                person_id,
				db.Field('organisation', db.or_organisation),
                db.Field('address', 'text'),
				db.Field('site_phone'),
				db.Field('site_fax'),
				location_id,
				db.Field('attachment', 'upload', autodelete=True),
                db.Field('comments'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Sites don't have to have unique names
# db[table].category.requires = IS_IN_DB(db, 'lms_site_category.id', 'lms_site_category.name')
#db[table].category.requires=IS_IN_SET(['warehouse'])
# db[table].site_category_id.comment = DIV(A(T('Add Category'), _class='popup', _href=URL(r=request, c='lms', f='site_category', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site Category|The Category of Site.")))
db[table].name.label = T("Site Name")
DIV(A(T('Add Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the main Warehouse/Site information where this Storage location is.")))
db[table].name.comment = SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Site Name|A Warehouse/Site is a physical location with an address and GIS data where Items are Stored. It can be a Building, a particular area in a city or anything similar."))
db[table].description.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Site Description|Use this space to add a description about the warehouse/site."))
#db[table].name.comment = SPAN("*", _class="req")
db[table].admin.label = T("Site Manager")
db[table].person_id.label = T("Contact Person")
#db[table].person_id.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Contact Person|The point of contact for this Site. You can create a contact entry by clicking 'Add Person' and enter more details about the person if it does not exists."))
db[table].address.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Site Address|Detailed address of the site for informational/logistics purpose. Please note that you can add GIS/Mapping data about this site in the 'Location' field mentioned below."))
db[table].organisation.requires = IS_IN_DB(db, 'or_organisation.id', 'or_organisation.name')
db[table].organisation.comment = DIV(A(T('Add Organisation'), _class='popup', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sender|Add sender to which the site belongs to.")))
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
                db.Field('description'),
                location_id,
                db.Field('capacity'),
				db.Field('capacity_unit'),
                db.Field('max_weight'),
				db.Field('weight_unit'),
				db.Field('attachment', 'upload', autodelete=True),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()   # Storage Locations don't have to have unique names
db[table].site_id.label = T("Site")
db[table].site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name')
db[table].capacity_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[1])
#db[table].capacity_unit.requires=IS_UNIT(db, filter_opts=[1])
db[table].capacity_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
db[table].weight_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[2])
#db[table].weight_unit.requires=IS_UNIT(db, filter_opts=[2])
db[table].weight_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
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
                db.Field('site_id', db.lms_site),
				db.Field('storage_id', db.lms_storage_loc),
				db.Field('number', notnull=True),
                db.Field('bin_type', db.lms_storage_bin_type),
                db.Field('capacity'),
				db.Field('capacity_unit'),
				db.Field('max_weight'),
				db.Field('weight_unit'),
				db.Field('attachment', 'upload', autodelete=True),
				db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name')
db[table].site_id.label = T("Site/Warehouse")
db[table].site_id.comment = DIV(A(T('Add Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the main Warehouse/Site information where this Bin belongs to.")))
db[table].storage_id.label = T("Storage Location")
db[table].storage_id.requires = IS_IN_DB(db, 'lms_storage_loc.id', 'lms_storage_loc.name')
db[table].storage_id.comment = DIV(A(T('Add Storage Location'), _class='popup', _href=URL(r=request, c='lms', f='storage_loc', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Storage Location|Add the Storage Location where this this Bin belongs to.")))
db[table].number.requires = IS_NOT_EMPTY()   # Storage Bin Numbers don't have to have unique names
db[table].capacity_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[1])
#db[table].capacity_unit.requires=IS_UNIT(db, filter_opts=[1])
db[table].capacity_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
db[table].weight_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[2])
#db[table].weight_unit.requires=IS_UNIT(db, filter_opts=[2])
db[table].weight_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
db[table].bin_type.requires = IS_IN_DB(db, 'lms_storage_bin_type.id', 'lms_storage_bin_type.name')
db[table].bin_type.comment = DIV(A(T('Add Storage Bin Type'), _class='popup', _href=URL(r=request, c='lms', f='storage_bin_type', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Storage Bin|Add the Storage Bin Type.")))
db[table].storage_id.requires = IS_IN_DB(db, 'lms_storage_loc.id', 'lms_storage_loc.name')
db[table].storage_id.comment = DIV(A(T('Add Storage Location'), _class='popup', _href=URL(r=request, c='lms', f='storage_loc', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Storage Location|Add the Storage Location where this bin is located.")))
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
msg_record_modified = T('Storage Bin updated')
msg_record_deleted = T('Storage Bin deleted')
msg_list_empty = T('No Storage Bins currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Item Catalog Master
resource = 'catalog'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('organisation', db.or_organisation),
				db.Field('name'),
                db.Field('description'),
				db.Field('comments', 'text'),
                migrate=migrate)
if not db(db[table].id).count():
    db[table].insert(
        name="Default",
        description="Default Catalog",
		comments="All items are by default added to this Catalog"
    )
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].organisation.requires = IS_IN_DB(db, 'or_organisation.id', 'or_organisation.name')
db[table].organisation.comment = DIV(A(T('Add Organisation'), _class='popup', _href=URL(r=request, c='or', f='organisation', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Organisation|Add the name and additional information about the Organisation if it does not exists already.")))
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T("Catalog Name")
db[table].name.comment = SPAN("*", _class="req")
title_create = T('Add Item Catalog ')
title_display = T('Item Catalog Details')
title_list = T('List Item Catalogs')
title_update = T('Edit Item Catalog')
title_search = T('Search Item Catalog(s)')
subtitle_create = T('Add New Item Catalog')
subtitle_list = T('Item Catalogs')
label_list_button = T('List Item Catalogs')
label_create_button = T('Add Item Catalog')
msg_record_created = T('Item Catalog added')
msg_record_modified = T('Item Catalog updated')
msg_record_deleted = T('Item Catalog deleted')
msg_list_empty = T('No Item Catalog currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Item Catalog Category
resource = 'catalog_cat'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('name'),
                db.Field('description'),
				db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T("Item Catalog Category")
db[table].name.comment = SPAN("*", _class="req")
title_create = T('Add Item Catalog Category ')
title_display = T('Item Catalog Category Details')
title_list = T('List Item Catalog Categories')
title_update = T('Edit Item Catalog Categories')
title_search = T('Search Item Catalog Category(s)')
subtitle_create = T('Add New Item Catalog Category')
subtitle_list = T('Item Catalog Categories')
label_list_button = T('List Item Catalog Categories')
label_create_button = T('Add Item Catalog Categories')
msg_record_created = T('Item Catalog Category added')
msg_record_modified = T('Item Catalog Category updated')
msg_record_deleted = T('Item Catalog Category deleted')
msg_list_empty = T('No Item Catalog Category currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Item Catalog Sub-Category
resource = 'catalog_subcat'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('parent_category', db.lms_catalog_cat),
				db.Field('name'),
                db.Field('description'),
				db.Field('comments', 'text'),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()
db[table].name.label = T("Item Sub-Category")
db[table].name.comment = SPAN("*", _class="req")
db[table].parent_category.requires = IS_IN_DB(db, 'lms_catalog_cat.id', 'lms_catalog_cat.name')
db[table].parent_category.comment = DIV(A(T('Add Item Category'), _class='popup', _href=URL(r=request, c='lms', f='catalog_cat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Item Category.")))
title_create = T('Add Item Sub-Category ')
title_display = T('Item Sub-Category Details')
title_list = T('List Item Sub-Categories')
title_update = T('Edit Item Sub-Categories')
title_search = T('Search Item Sub-Category(s)')
subtitle_create = T('Add New Item Sub-Category')
subtitle_list = T('Item Sub-Categories')
label_list_button = T('List Item Sub-Categories')
label_create_button = T('Add Item Sub-Categories')
msg_record_created = T('Item Sub-Category added')
msg_record_modified = T('Item Sub-Category updated')
msg_record_deleted = T('Item Sub-Category deleted')
msg_list_empty = T('No Item Sub-Category currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Category<>Sub-Category<>Catalog Relation between all three.

resource = 'category_master'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('category_id', db.lms_catalog_cat),
                Field('subcategory_id', db.lms_catalog_subcat),
                Field('catalog_id', db.lms_catalog),
                migrate=migrate)
db[table].category_id.requires = IS_IN_DB(db, 'lms_catalog_cat.id', 'lms_catalog_cat.name')
db[table].category_id.label = T('Category')
db[table].category_id.represent = lambda category_id: db(db.lms_catalog_cat.id==category_id).select()[0].name
db[table].category_id.comment = DIV(A(T('Add Item Category'), _class='popup', _href=URL(r=request, c='lms', f='catalog_cat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Item Category.")))
db[table].subcategory_id.requires = IS_IN_DB(db, 'lms_catalog_subcat.id', 'lms_catalog_subcat.name')
db[table].subcategory_id.label = T('Sub Category')
db[table].subcategory_id.represent = lambda subcategory_id: db(db.lms_catalog_subcat.id==subcategory_id).select()[0].name
db[table].subcategory_id.comment = DIV(A(T('Add Item Sub-Category'), _class='popup', _href=URL(r=request, c='lms', f='catalog_subcat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Item Sub-Category.")))
db[table].catalog_id.requires = IS_IN_DB(db, 'lms_catalog.id', 'lms_catalog.name')
db[table].catalog_id.label = T('Catalog')
db[table].catalog_id.represent = lambda catalog_id: db(db.lms_catalog.id==catalog_id).select()[0].name
db[table].catalog_id.comment = DIV(A(T('Add Item Catalog'), _class='popup', _href=URL(r=request, c='lms', f='catalog', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Catalog.")))
title_create = T('Add Category<>Sub-Category<>Catalog Relation ')
title_display = T('Category<>Sub-Category<>Catalog Relation')
title_list = T('List Category<>Sub-Category<>Catalog Relation')
title_update = T('Edit Category<>Sub-Category<>Catalog Relation')
title_search = T('Search Category<>Sub-Category<>Catalog Relation')
subtitle_create = T('Add Category<>Sub-Category<>Catalog Relation')
subtitle_list = T('Category<>Sub-Category<>Catalog Relation')
label_list_button = T('List Category<>Sub-Category<>Catalog Relation')
label_create_button = T('Add Category<>Sub-Category<>Catalog Relation')
msg_record_created = T('Category<>Sub-Category<>Catalog Relation added')
msg_record_modified = T('Category<>Sub-Category<>Catalog Relation updated')
msg_record_deleted = T('Category<>Sub-Category<>Catalog Relation deleted')
msg_list_empty = T('No Category<>Sub-Category<>Catalog Relation currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Shipment
resource = 'shipment'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
				db.Field('way_bill', notnull=True),
				db.Field('sender_site', db.lms_site),
				db.Field('sender_person'),
				db.Field('sent_date', 'datetime'),
				db.Field('recipient_site', db.lms_site),
				db.Field('recieving_person'),
				db.Field('recieved_date', 'datetime'),
				db.Field('cost', 'double', default=0.00),
				db.Field('currency'),
				db.Field('track_status', readable='False'), #Linked to Shipment Transit Log table
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].way_bill.requires = IS_NOT_EMPTY()
db[table].way_bill.label = T("Shipment/Way Bills")
db[table].way_bill.comment = SPAN("*", _class="req")
db[table].sender_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
db[table].sender_site.comment = DIV(A(T('Add Sender Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Site|Add a new Site from where the Item is being sent.")))
db[table].recipient_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
db[table].recipient_site.comment = DIV(A(T('Add Recipient Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Recipient|Add a new Site where the Item is being sent to.")))
title_create = T('Add Shipment/Way Bills')
title_display = T('Shipment/Way Bills Details')
title_list = T('List Shipment/Way Bills')
title_update = T('Edit Shipment/Way Bills')
title_search = T('Search Shipment/Way Bills')
subtitle_create = T('Add Shipment/Way Bills')
subtitle_list = T('Shipment/Way Bills')
label_list_button = T('List Shipment/Way Bills')
label_create_button = T('Add Shipment/Way Bills')
msg_record_created = T('Shipment/Way Bill added')
msg_record_modified = T('Shipment/Way Bills updated')
msg_record_deleted = T('Shipment/Way Bills deleted')
msg_list_empty = T('No Shipment/Way Bills currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Items
resource = 'item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                db.Field('site_id', db.lms_site),
				db.Field('storage_id', db.lms_storage_loc, writable=False, default=0), #No storage location assigned
				db.Field('bin_id', db.lms_storage_bin, writable=False, default=0), #No Storage Bin assigned
				db.Field('catalog', db.lms_catalog, writable=False, default=1), #default catalog assigned
				#db.Field('ordered_list_item', notnull=True, unique=True),
				#Shipment Details
				db.Field('way_bill'),
				db.Field('sender_site', db.lms_site),
				db.Field('sender_person'),
				db.Field('recipient_site', db.lms_site),
				db.Field('recieving_person'),
				#Item Details
				db.Field('name'), #Item Catalog
                db.Field('description'), #Item Catalog
				db.Field('category', db.lms_catalog_cat), #Item Catalog
				db.Field('sub_category', db.lms_catalog_subcat), #Item Catalog
				db.Field('designated'), #More details to be added, maybe a new table.
				db.Field('quantity_sent', 'double', default=0.00),
				db.Field('quantity_received', 'double', default=0.00),
				db.Field('quantity_shortage', default=0.00),
				db.Field('quantity_unit'), #Item Catalog
				db.Field('specifications'), #Item Catalog
				db.Field('specifications_unit'), #Item Catalog
				db.Field('weight', 'double', default=0.00), #Item Catalog
				db.Field('weight_unit'), #Item Catalog
				db.Field('date_time', 'datetime'),
				db.Field('comments', 'text'),
				db.Field('attachment', 'upload', autodelete=True),
                db.Field('unit_cost', 'double', default=0.00),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].site_id.requires = IS_IN_DB(db, 'lms_site.id', 'lms_storage_loc.name') #this should be automatically done. Using LMS User Preferences
db[table].site_id.label = T("Site/Warehouse")
db[table].site_id.comment = DIV(A(T('Add Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Site|Add the main Warehouse/Site information where this Item is to be added.")))
db[table].quantity_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[5])
#db[table].quantity_unit.requires=IS_UNIT(db, filter_opts=[5])
db[table].quantity_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
db[table].specifications_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[1])
#db[table].specifications_unit.requires=IS_UNIT(db, filter_opts=[1])
db[table].specifications_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
db[table].weight_unit.requires = IS_ONE_OF(db, "lms_unit.id", "%(name)s", filterby='opt_lms_unit_type', filter_opts=[2])
#db[table].weight_unit.requires=IS_UNIT(db, filter_opts=[2])
db[table].weight_unit.comment = DIV(A(T('Add Unit'), _class='popup', _href=URL(r=request, c='lms', f='unit', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Unit|Add the unit of measure if it doesnt exists already.")))
#db[table].ordered_list_item.requires = IS_NOT_EMPTY()
db[table].name.requires = IS_NOT_EMPTY()
#db[table].ordered_list_item.label = T("Ordered List Item")
#db[table].ordered_list_item.comment = SPAN("*", _class="req")
#db[table].way_bill.label = T("Air Way Bill (AWB)")
db[table].way_bill.comment = SPAN("*", _class="req")
db[table].name.label = T("Product Name")
db[table].name.comment = SPAN("*", _class="req")
db[table].description.label = T("Product Description")
db[table].category.requires = IS_IN_DB(db, 'lms_catalog_cat.id', 'lms_catalog_cat.name')
db[table].category.comment = DIV(A(T('Add Item Category'), _class='popup', _href=URL(r=request, c='lms', f='catalog_cat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Item Category.")))
db[table].sub_category.requires = IS_IN_DB(db, 'lms_catalog_subcat.id', 'lms_catalog_subcat.name')
db[table].sub_category.comment = DIV(A(T('Add Item Sub-Category'), _class='popup', _href=URL(r=request, c='lms', f='catalog_subcat', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add main Item Sub-Category.")))
db[table].sender_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
db[table].sender_site.comment = DIV(A(T('Add Sender Organisation'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Sender Site.")))
db[table].recipient_site.requires = IS_IN_DB(db, 'lms_site.id', 'lms_site.name')
db[table].recipient_site.comment = DIV(A(T('Add Recipient Site'), _class='popup', _href=URL(r=request, c='lms', f='site', args='create', vars=dict(format='plain')), _target='top'), A(SPAN("[Help]"), _class="tooltip", _title=T("Add Recipient Site.")))
db[table].designated.label = T("Designated for")
db[table].specifications.label = T("Volume/Dimensions")
db[table].designated.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Designated for|The item is designated to be sent for specific project, population, village or other earmarking of the donation such as a Grant Code."))
db[table].specifications.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Volume/Dimensions|Additional quantity quantifier – i.e. “4x5”."))
db[table].date_time.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Date/Time|Date and Time of Goods receipt. By default shows the current time but can be modified by editing in the drop down list."))
db[table].unit_cost.label = T('Unit Cost')
title_create = T('Add Item')
title_display = T('Item Details')
title_list = T('List Item(s)')
title_update = T('Edit Item(s)')
title_search = T('Search Item(s)')
subtitle_create = T('Add New Item')
subtitle_list = T('Items')
label_list_button = T('List Item')
label_create_button = T('Add Item')
msg_record_created = T('Item added')
msg_record_modified = T('Item updated')
msg_record_deleted = T('Item deleted')
msg_list_empty = T('No Item currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Shipment<>Item - A shipment can have many items under it.
# And an Item can have multiple shipment way bills, for e.g. during transit at multiple exchanges/transits

resource = 'shipment_item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
				db.Field('shipment_id', db.lms_shipment),
				db.Field('item_id', db.lms_item),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].shipment_id.requires = IS_IN_DB(db, 'lms_shipment.id', 'lms_shipment.way_bill')
db[table].item_id.requires = IS_IN_DB(db, 'lms_item.id', 'lms_item.name') #This needs to be represented as Name+Brand+Model+Description+Size
title_create = T('Link Item & Shipment')
title_display = T('Shipment<>Item Relations Details')
title_list = T('List Shipment<>Item Relation')
title_update = T('Edit Shipment<>Item Relation')
title_search = T('Search Shipment<>Item Relation')
subtitle_create = T('Link Item & Shipment')
subtitle_list = T('Shipment/Way Bills')
label_list_button = T('Shipment<>Item Relations')
label_create_button = T('Link an Item & Shipment')
msg_record_created = T('Shipment<>Item Relation added')
msg_record_modified = T('Shipment<>Item Relation updated')
msg_record_deleted = T('Shipment<>Item Relation deleted')
msg_list_empty = T('No Shipment<>Item Relation currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Shipment<>Item - A shipment can have many items under it.
# And an Item can have multiple shipment way bills, for e.g. during transit at multiple exchanges/transits

resource = 'shipment_transit_logs'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
				db.Field('shipment_id', db.lms_shipment),
				db.Field('item_id', db.lms_item),
                migrate=migrate)
db[table].uuid.requires = IS_NOT_IN_DB(db,'%s.uuid' % table)
db[table].shipment_id.requires = IS_IN_DB(db, 'lms_shipment.id', 'lms_shipment.way_bill')
db[table].item_id.requires = IS_IN_DB(db, 'lms_item.id', 'lms_item.name') #This needs to be represented as Name+Brand+Model+Description+Size
title_create = T('Link Item & Shipment')
title_display = T('Shipment<>Item Relations Details')
title_list = T('List Shipment<>Item Relation')
title_update = T('Edit Shipment<>Item Relation')
title_search = T('Search Shipment<>Item Relation')
subtitle_create = T('Link Item & Shipment')
subtitle_list = T('Shipment/Way Bills')
label_list_button = T('Shipment<>Item Relations')
label_create_button = T('Link an Item & Shipment')
msg_record_created = T('Shipment<>Item Relation added')
msg_record_modified = T('Shipment<>Item Relation updated')
msg_record_deleted = T('Shipment<>Item Relation deleted')
msg_list_empty = T('No Shipment<>Item Relation currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Kits
resource = 'kit'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('code', length=128, notnull=True, unique=True),
                Field('description'),
                Field('total_unit_cost', 'double', writable=False),
                Field('total_monthly_cost', 'double', writable=False),
                Field('total_minute_cost', 'double', writable=False),
                Field('total_megabyte_cost', 'double', writable=False),
                Field('comments'),
                migrate=migrate)
db[table].code.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.code' % table)]
db[table].code.label = T('Code')
db[table].code.comment = SPAN("*", _class="req")
db[table].description.label = T('Description')
db[table].total_unit_cost.label = T('Total Unit Cost')
db[table].total_monthly_cost.label = T('Total Monthly Cost')
db[table].total_minute_cost.label = T('Total Cost per Minute')
db[table].total_megabyte_cost.label = T('Total Cost per Megabyte')
db[table].comments.label = T('Comments')
title_create = T('Add Kit')
title_display = T('Kit Details')
title_list = T('List Kits')
title_update = T('Edit Kit')
title_search = T('Search Kits')
subtitle_create = T('Add New Kit')
subtitle_list = T('Kits')
label_list_button = T('List Kits')
label_create_button = T('Add Kit')
msg_record_created = T('Kit added')
msg_record_modified = T('Kit updated')
msg_record_deleted = T('Kit deleted')
msg_list_empty = T('No Kits currently registered')
s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)

# Kit<>Item Many2Many
resource = 'kit_item'
table = module + '_' + resource
db.define_table(table, timestamp, uuidstamp, deletion_status,
                Field('kit_id', db.lms_kit),
                Field('item_id', db.lms_item, ondelete='RESTRICT'),
                Field('quantity', 'integer', default=1, notnull=True),
                migrate=migrate)
db[table].kit_id.requires = IS_IN_DB(db, 'lms_kit.id', 'lms_kit.code')
db[table].kit_id.label = T('Kit')
db[table].kit_id.represent = lambda kit_id: db(db.budget_kit.id==kit_id).select()[0].code
db[table].item_id.requires = IS_IN_DB(db, 'lms_item.id', 'lms_item.description')
db[table].item_id.label = T('Item')
db[table].item_id.represent = lambda item_id: db(db.lms_item.id==item_id).select()[0].description
db[table].quantity.requires = IS_NOT_EMPTY()
db[table].quantity.label = T('Quantity')
db[table].quantity.comment = SPAN("*", _class="req")