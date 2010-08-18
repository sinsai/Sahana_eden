# -*- coding: utf-8 -*-

"""
    Camp Registry
"""

module = "cr"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = module + "_" + resource
    table = db.define_table(tablename,
                    Field("audit_read", "boolean"),
                    Field("audit_write", "boolean"),
                    migrate=migrate)

    # -----------------------------------------------------------------------------
    # Shelters
    resource = "shelter_type"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field("name", notnull=True),
                    comments,
                    migrate=migrate)
    
    ADD_SHELTER_TYPE = T("Add Shelter Type")
    LIST_SHELTER_TYPES = T("List Shelter Types")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Shelter Type"),
        title_display = ADD_SHELTER_TYPE,
        title_list = LIST_SHELTER_TYPES,
        title_update = T("Edit Shelter Type"),
        title_search = T("Search Shelter Types"),
        subtitle_create = T("Add New Shelter Type"),
        subtitle_list = T("Shelter Types"),
        label_list_button = LIST_SHELTER_TYPES,
        label_create_button = ADD_SHELTER_TYPE,
        msg_record_created = T("Shelter Type added"),
        msg_record_modified = T("Shelter Type updated"),
        msg_record_deleted = T("Shelter Type deleted"),
        msg_list_empty = T("No Shelter Types currently registered"))

    shelter_type_id = db.Table(None, "shelter_type_id",
                               Field("shelter_type_id", db.cr_shelter_type,
                                     requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter_type.id", "%(name)s")),
                                     represent = lambda id: (id and [db.cr_shelter_type[id].name] or ["None"])[0],
                                     comment = A(ADD_SHELTER_TYPE, _class="colorbox", _href=URL(r=request, c="cr", f="shelter_type", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER_TYPE),
                                     ondelete = "RESTRICT",
                                     label = T("Shelter Type")
                                    )
                              )

    # -----------------------------------------------------------------------------
    resource = "shelter_service"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field("name", notnull=True),
                    comments,
                    migrate=migrate)
    
    ADD_SHELTER_SERVICE = T("Add Shelter Service")
    LIST_SHELTER_SERVICES = T("List Shelter Services")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Shelter Service"),
        title_display = ADD_SHELTER_SERVICE,
        title_list = LIST_SHELTER_SERVICES,
        title_update = T("Edit Shelter Service"),
        title_search = T("Search Shelter Services"),
        subtitle_create = T("Add New Shelter Service"),
        subtitle_list = T("Shelter Services"),
        label_list_button = LIST_SHELTER_SERVICES,
        label_create_button = ADD_SHELTER_SERVICE,
        msg_record_created = T("Shelter Service added"),
        msg_record_modified = T("Shelter Service updated"),
        msg_record_deleted = T("Shelter Service deleted"),
        msg_list_empty = T("No Shelter Services currently registered"))

    def shn_shelter_service_represent(shelter_service_ids):
        if not shelter_service_ids:
            return "None"
        elif "|" in str(shelter_service_ids):
            shelter_services = [db(db.cr_shelter_service.id == id).select(db.cr_shelter_service.name, limitby=(0, 1)).first().name for id in shelter_service_ids.split("|") if id]
            return ", ".join(shelter_services)
        else:
            return db(db.cr_shelter_service.id == shelter_service_ids).select(db.cr_shelter_service.name, limitby=(0, 1)).first().name

    shelter_service_id = db.Table(None, "shelter_service_id",
                                  FieldS3("shelter_service_id", 
                                          requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter_service.id", "%(name)s", multiple=True)),
                                          represent = shn_shelter_service_represent,
                                          comment = A(ADD_SHELTER_SERVICE, _class="colorbox", _href=URL(r=request, c="cr", f="shelter_service", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER_SERVICE),
                                          ondelete = "RESTRICT",
                                          label = T("Shelter Service")
                                         )
                                 )

    # -----------------------------------------------------------------------------
    resource = "shelter"
    tablename = module + "_" + resource
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    Field("name", notnull=True),
                    shelter_type_id,
                    Field("description"),
                    location_id,
                    shelter_service_id,
                    person_id,
                    Field("address", "text"),
                    Field("capacity", "integer"),
                    Field("dwellings", "integer"),
                    Field("persons_per_dwelling", "integer"),
                    Field("area"),
                    comments,
                    migrate=migrate)
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()   # Shelters don't have to have unique names
    table.name.label = T("Shelter Name")
    table.name.comment = SPAN("*", _class="req")
    table.description.label = T("Description")
    table.person_id.label = T("Contact Person")
    table.address.label = T("Address")
    table.capacity.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))
    table.capacity.label = T("Capacity")
    table.dwellings.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.dwellings.label = T("Dwellings")
    table.persons_per_dwelling.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999))
    table.persons_per_dwelling.label = T("Persons per Dwelling")
    table.area.label = T("Area")

    ADD_SHELTER = T("Add Shelter")
    LIST_SHELTERS = T("List Shelters")
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Shelter"),
        title_display = ADD_SHELTER,
        title_list = LIST_SHELTERS,
        title_update = T("Edit Shelter"),
        title_search = T("Search Shelters"),
        subtitle_create = T("Add New Shelter"),
        subtitle_list = T("Shelters"),
        label_list_button = LIST_SHELTERS,
        label_create_button = ADD_SHELTER,
        msg_record_created = T("Shelter added"),
        msg_record_modified = T("Shelter updated"),
        msg_record_deleted = T("Shelter deleted"),
        msg_list_empty = T("No Shelters currently registered"))

    # reusable field
    shelter_id = db.Table(None, "shelter_id",
                          Field("shelter_id", db.cr_shelter,
                                requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id", "%(name)s")),
                                represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0],
                                ondelete = "RESTRICT",
                                comment = DIV(A(ADD_SHELTER, _class="colorbox", _href=URL(r=request, c="cr", f="shelte", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER),
                                          DIV( _class="tooltip", _title=Tstr("Shelter") + "|" + Tstr("The Shelter this Request is from (optional)."))),
                                label = T("Shelter")
                               )
                         )
    # Shelters as component of Services, Types & Locations
    s3xrc.model.add_component(module, resource,
                              multiple=True,
                              joinby=dict(cr_shelter_type="shelter_type_id", cr_shelter_service="shelter_service_id", gis_location="location_id"),
                              deletable=True,
                              editable=True)