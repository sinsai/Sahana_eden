# -*- coding: utf-8 -*-

"""
    Shelter (Camp) Registry, model

    @author: Pat Tressel
    @author: Fran Boon
"""

module = "cr"
if deployment_settings.has_module(module):

    # -------------------------------------------------------------------------
    # Shelter types
    # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
    resourcename = "shelter_type"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("name", notnull=True),
                            comments(),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))

    table.name.requires = IS_NOT_ONE_OF(db, "%s.name" % tablename)

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
                                      requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                      "cr_shelter_type.id",
                                                                      "%(name)s")),
                                      represent = lambda id: (id and [db.cr_shelter_type[id].name] or ["None"])[0],
                                      comment = A(ADD_SHELTER_TYPE,
                                                  _class="colorbox",
                                                  _href=URL(r=request, c="cr",
                                                            f="shelter_type",
                                                            args="create",
                                                            vars=dict(format="popup")),
                                                  _target="top",
                                                  _title=ADD_SHELTER_TYPE),
                                      ondelete = "RESTRICT",
                                      label = T("Shelter Type")
                                     )

    # -------------------------------------------------------------------------
    # Shelter services
    # e.g. medical, housing, food, ...
    resourcename = "shelter_service"
    tablename = "%s_%s" % (module, resourcename)
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
            query = (db.cr_shelter_service.id.belongs(shelter_service_ids))
            shelter_services = db(query).select(db.cr_shelter_service.name)
            return ", ".join([s.name for s in shelter_services])
        else:
            query = (db.cr_shelter_service.id == shelter_service_ids)
            shelter_service = db(query).select(db.cr_shelter_service.name,
                                               limitby=(0, 1)).first()
            return shelter_service and shelter_service.name or NONE

    shelter_service_id = S3ReusableField("shelter_service_id",
                                         "list:reference cr_shelter_service",
                                         sortby="name",
                                         requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                         "cr_shelter_service.id",
                                                                         "%(name)s", multiple=True)),
                                         represent = shn_shelter_service_represent,
                                         label = T("Shelter Service"),
                                         comment = A(ADD_SHELTER_SERVICE,
                                                     _class="colorbox",
                                                     _href=URL(r=request, c="cr",
                                                               f="shelter_service",
                                                               args="create",
                                                               vars=dict(format="popup")),
                                                     _target="top",
                                                     _title=ADD_SHELTER_SERVICE),
                                         ondelete = "RESTRICT",
                                         #widget = SQLFORM.widgets.checkboxes.widget
                                         )

    # -------------------------------------------------------------------------
    resourcename = "shelter"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.org_site),
                            Field("name", notnull=True,
                                  label = T("Shelter Name")),
                            organisation_id(),
                            shelter_type_id(),          # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
                            shelter_service_id(),       # e.g. medical, housing, food, ...
                            location_id(),
                            Field("phone", label = T("Phone"),
                                  requires = shn_phone_requires),
                            Field("building_name", "text", label=T("Building Name"),
                                  writable=False), # Populated from location_id
                            Field("address", "text", label=T("Address"),
                                  writable=False), # Populated from location_id
                            Field("L4",
                                  label=deployment_settings.get_gis_locations_hierarchy("L4"),
                                  writable=False), # Populated from location_id
                            Field("L3",
                                  label=deployment_settings.get_gis_locations_hierarchy("L3"),
                                  writable=False), # Populated from location_id
                            Field("L2",
                                  label=deployment_settings.get_gis_locations_hierarchy("L2"),
                                  writable=False), # Populated from location_id
                            Field("L1",
                                  label=deployment_settings.get_gis_locations_hierarchy("L1"),
                                  writable=False), # Populated from location_id
                            Field("L0",
                                  label=deployment_settings.get_gis_locations_hierarchy("L0"),
                                  writable=False), # Populated from location_id
                            Field("postcode", label=T("Postcode"), writable=False), # Populated from location_id
                            person_id(label = T("Contact Person")),
                            Field("population", "integer",
                                  label = T("Population"),
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))),
                            Field("capacity", "integer",
                                  label = T("Capacity (Max Persons)"),
                                  requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))),
                            #Field("dwellings", "integer"),
                            #Field("persons_per_dwelling", "integer"),
                            #Field("area"),
                            Field("source",
                                  label = T("Source")),
                            document_id(),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    # Shelters don't have to have unique names
    # @ToDo: If we want to filter incoming reports automatically to see if
    # they apply to shelters, then we may need to reconsider whether names
    # can be non-unique, *especially* since location is not required.
    table.name.requires = IS_NOT_EMPTY()
    #table.dwellings.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    #table.dwellings.label = T("Dwellings")
    #table.persons_per_dwelling.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999))
    #table.persons_per_dwelling.label = T("Max Persons per Dwelling")
    #table.area.label = T("Area")

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

    # Reusable field
    shelter_id = S3ReusableField("shelter_id", db.cr_shelter,
                                 requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                 "cr_shelter.id",
                                                                 "%(name)s",
                                                                 sort=True)),
                                 represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0],
                                 ondelete = "RESTRICT",
                                 comment = DIV(A(ADD_SHELTER,
                                                 _class="colorbox",
                                                 _href=URL(r=request, c="cr",
                                                           f="shelter",
                                                           args="create",
                                                           vars=dict(format="popup")),
                                                 _target="top",
                                                 _title=ADD_SHELTER),
                                           DIV( _class="tooltip",
                                                _title="%s|%s" % (T("Shelter"),
                                                                  T("The Shelter this Request is from (optional).")))),
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
                          # Update the Address Fields
                          onvalidation=address_onvalidation,
                          # Create roles for each shelter
                          create_onaccept = staff_roles_create_func(tablename),
                          # Rename roles if record name changes
                          update_onaccept = staff_roles_update_func(tablename),
                          list_fields=["id",
                                       "name",
                                       "shelter_type_id",
                                       "shelter_service_id",
                                       "location_id",
                                       "person_id"])
    
    # -----------------------------------------------------------------------------
    def shn_shelter_rheader(r, tabs=[]):
    
        """ Resource Headers """
    
        if r.representation == "html":
            tablename, record = s3_rheader_resource(r)
            if tablename == "cr_shelter" and record:
                if not tabs:
                    tabs = [(T("Basic Details"), None),
                            (T("People"), "presence"),
                            (T("Staff"), "staff"),
                        ]
                    if deployment_settings.has_module("assess"):
                        tabs.append((T("Assessments"), "rat"))
                    if deployment_settings.has_module("req"):
                        tabs.append((T("Requests"), "req"))
                        tabs.append((T("Match Requests"), "req_match/")) 
                        tabs.append((T("Commit"), "commit"))
                    if deployment_settings.has_module("inv"):
                        tabs = tabs + shn_show_inv_tabs(r)
    
                rheader_tabs = s3_rheader_tabs(r, tabs)
    
                if r.name == "shelter":
                    location = shn_gis_location_represent(record.location_id)
    
                    rheader = DIV(TABLE(
                                        TR(
                                            TH("%s: " % T("Name")), record.name
                                          ),
                                        TR(
                                            TH("%s: " % T("Location")), location
                                          ),
                                        ),
                                  rheader_tabs)
                else:
                    rheader = DIV(TABLE(
                                        TR(
                                            TH("%s: " % T("Name")), record.name
                                          ),
                                        ),
                                  rheader_tabs)
    
                if r.component and r.component.name == "req":
                    # Inject the helptext script
                    rheader.append(req_helptext_script)
    
                return rheader
        return None

    # Link to shelter from pr_presence
    table = db.pr_presence
    table.shelter_id.requires = IS_NULL_OR(IS_ONE_OF(db, "cr_shelter.id",
                                                     "%(name)s",
                                                     sort=True))
    table.shelter_id.represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0]
    table.shelter_id.ondelete = "RESTRICT"
    table.shelter_id.comment = DIV(A(ADD_SHELTER,
                                     _class="colorbox",
                                     _href=URL(r=request, c="cr", f="shelter",
                                               args="create",
                                               vars=dict(format="popup")),
                                     _target="top",
                                     _title=ADD_SHELTER),
                                   DIV( _class="tooltip",
                                        _title="%s|%s" % (T("Shelter"),
                                                          T("The Shelter this person is checking into."))))
    table.shelter_id.label = T("Shelter")
    table.shelter_id.readable = True
    table.shelter_id.writable = True

    s3xrc.model.add_component("pr", "presence",
                              multiple=True,
                              joinby=dict(cr_shelter="shelter_id"))

# END -------------------------------------------------------------------------