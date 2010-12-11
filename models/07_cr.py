# -*- coding: utf-8 -*-

"""
    Shelter (Camp) Registry, model

    @author: Pat Tressel

"""

module = "cr"
if deployment_settings.has_module(module):

    # -------------------------------------------------------------------------
    # Shelter types
    resourcename = "shelter_type"
    tablename = module + "_" + resourcename
    table = db.define_table(tablename,
                            Field("name", notnull=True),
                            comments(),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))
    ADD_SHELTER_TYPE = T("Add Shelter Type")
    LIST_SHELTER_TYPES = T("List Shelter Types")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHELTER_TYPE,
        title_display = T("Shelter Type Details"),
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

    shelter_type_id = S3ReusableField("shelter_type_id", db.cr_shelter_type,
                                      requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter_type.id", "%(name)s")),
                                      represent = lambda id: (id and [db.cr_shelter_type[id].name] or ["None"])[0],
                                      comment = A(ADD_SHELTER_TYPE, _class="colorbox", _href=URL(r=request, c="cr", f="shelter_type", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER_TYPE),
                                      ondelete = "RESTRICT",
                                      label = T("Shelter Type")
                                     )

    # -------------------------------------------------------------------------
    resourcename = "shelter_service"
    tablename = module + "_" + resourcename
    table = db.define_table(tablename,
                            Field("name", notnull=True),
                            comments(),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))
    ADD_SHELTER_SERVICE = T("Add Shelter Service")
    LIST_SHELTER_SERVICES = T("List Shelter Services")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHELTER_SERVICE,
        title_display = T("Shelter Service Details"),
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
            return NONE
        elif isinstance(shelter_service_ids, (list, tuple)):
            shelter_services = db(db.cr_shelter_service.id.belongs(shelter_service_ids)).select(db.cr_shelter_service.name)
            return ", ".join([s.name for s in shelter_services])
        else:
            shelter_service = db(db.cr_shelter_service.id == shelter_service_ids).select(db.cr_shelter_service.name, limitby=(0, 1)).first()
            return shelter_service and shelter_service.name or NONE

    shelter_service_id = S3ReusableField("shelter_service_id", "list:reference cr_shelter_service", sortby="name",
                                          requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter_service.id", "%(name)s", multiple=True)),
                                          represent = shn_shelter_service_represent,
                                          label = T("Shelter Service"),
                                          comment = A(ADD_SHELTER_SERVICE, _class="colorbox", _href=URL(r=request, c="cr", f="shelter_service", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER_SERVICE),
                                          ondelete = "RESTRICT",
                                          #widget = SQLFORM.widgets.checkboxes.widget
                                         )

    # -------------------------------------------------------------------------
    resourcename = "shelter"
    tablename = module + "_" + resourcename

    # If the HMS module is enabled, we include a hospital_id field, so if the
    # shelter is co-located with a hospital, the hospital can be identified.
    # To get the fields in the correct order in the table, get the fields
    # before and after where hospital_id should go.
    #
    # Caution:  If you start with HMS enabled, and fill in hospital info, then disable HMS,
    # the hospital_id column will get dropped.  If HMS is re-enabled, the hospital_id links will be gone.
    # If this is a production site, do not disable HMS unless you really mean it...

    fields_before_hospital = db.Table(None, None,
                                      super_link(db.org_site),
                                      Field("name", notnull=True),
                                      shelter_type_id(),
                                      shelter_service_id(),
                                      location_id(),
                                      Field("phone"),
                                      person_id(),
                                      # Don't show this field -- it will be going away in favor of
                                      # location -- but preserve it for converting to a location.
                                      # @ToDo This address field is free format.  If we don't
                                      # want to try to parse it, could let users convert it to a
                                      # location by providing a special (temporary) update form.
                                      Field("address", "text", readable=False, writable=False),
                                      Field("capacity", "integer"),
                                      Field("dwellings", "integer"),
                                      Field("persons_per_dwelling", "integer"),
                                      Field("area"),
                                      document_id())

    fields_after_hospital = db.Table(None, None,
                                     comments())

    # Only include hospital_id if the hms module is enabled.
    if deployment_settings.has_module("hms"):
        table = db.define_table(tablename,
                                fields_before_hospital,
                                hospital_id(comment = shn_hospital_id_comment),
                                fields_after_hospital,
                                migrate=migrate, *s3_meta_fields())

    else:
        table = db.define_table(tablename,
                                fields_before_hospital,
                                fields_after_hospital,
                                migrate=migrate, *s3_meta_fields())

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    # Shelters don't have to have unique names
    # @ToDo If we want to filter incoming reports automatically to see if
    # they apply to shelters, then we may need to reconsider whether names
    # can be non-unique, *especially* since location is not required.
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Shelter Name")
    table.person_id.label = T("Contact Person")
    table.address.label = T("Address")
    table.capacity.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))
    table.capacity.label = T("Capacity (Max Persons)")
    table.dwellings.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.dwellings.label = T("Dwellings")
    table.persons_per_dwelling.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999))
    table.persons_per_dwelling.label = T("Max Persons per Dwelling")
    table.area.label = T("Area")
    table.phone.label = T("Phone")
    table.phone.requires = shn_phone_requires

    ADD_SHELTER = T("Add Shelter")
    LIST_SHELTERS = T("List Shelters")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SHELTER,
        title_display = T("Shelter Details"),
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
    shelter_id = S3ReusableField("shelter_id", db.cr_shelter,
                                 requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id", "%(name)s", sort=True)),
                                 represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0],
                                 ondelete = "RESTRICT",
                                 comment = DIV(A(ADD_SHELTER, _class="colorbox", _href=URL(r=request, c="cr", f="shelter", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER),
                                           DIV( _class="tooltip", _title=T("Shelter") + "|" + T("The Shelter this Request is from (optional)."))),
                                 label = T("Shelter"),
                                 widget = S3AutocompleteWidget(request, module, resourcename)
                                )

    # Add Shelters as component of Services, Types, Locations as a simple way
    # to get reports showing shelters per type, etc.
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(cr_shelter_type="shelter_type_id",
                                          cr_shelter_service="shelter_service_id",
                                          #gis_location="location_id",
                                          doc_document="document_id"))

    s3xrc.model.configure(table,
                          #listadd=False,
                          super_entity=db.org_site,
                          list_fields=["id",
                                       "name",
                                       "shelter_type_id",
                                       "shelter_service_id",
                                       "location_id"])

    # Link to shelter from pr_presence
    table = db.pr_presence
    table.shelter_id.requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id", "%(name)s", sort=True))
    table.shelter_id.represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0]
    table.shelter_id.ondelete = "RESTRICT"
    table.shelter_id.comment = DIV(A(ADD_SHELTER, _class="colorbox", _href=URL(r=request, c="cr", f="shelter", args="create", vars=dict(format="popup")), _target="top", _title=ADD_SHELTER),
                                   DIV( _class="tooltip", _title=T("Shelter") + "|" + T("The Shelter this Request is from (optional).")))
    table.shelter_id.label = T("Shelter")
    table.shelter_id.readable = True
    table.shelter_id.writable = True

    s3xrc.model.add_component("pr", "presence",
        multiple=True,
        joinby=dict(cr_shelter="shelter_id"))
