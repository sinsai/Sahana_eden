# -*- coding: utf-8 -*-

"""
    Cluster

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-10-12

    Data model for Clusters and Cluster Sectors
"""

module = "cluster"
if deployment_settings.has_module("assess") or deployment_settings.has_module("project"):
    # -----------------------------------------------------------------------------
    # Cluster
    resource = "cluster"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("abrv", length=64, notnull=True, unique=True),
                            Field("name", length=128, notnull=True, unique=True),
                            migrate=migrate, *s3_meta_fields()
                            )        
    
    # CRUD strings
    ADD_CLUSTER = T("Add Cluster")
    LIST_CLUSTER = T("List Cluster")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_CLUSTER,
        title_display = T("Cluster Details"),
        title_list = LIST_CLUSTER,
        title_update = T("Edit Cluster"),
        title_search = T("Search Clusters"),
        subtitle_create = T("Add New Cluster"),
        subtitle_list = T("Clusters"),
        label_list_button = LIST_CLUSTER,
        label_create_button = ADD_CLUSTER,
        label_delete_button = T("Delete Cluster"),
        msg_record_created = T("Cluster added"),
        msg_record_modified = T("Cluster updated"),
        msg_record_deleted = T("Cluster deleted"),
        msg_list_empty = T("No Clusters currently registered"))  
    
    cluster_id = S3ReusableField("cluster_id", db.cluster_cluster, sortby="abrv",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "cluster_cluster.id","%(abrv)s", sort=True)),
                                       represent = lambda id: shn_get_db_field_value(db = db,
                                                                                     table = "cluster_cluster",
                                                                                     field = "abrv",
                                                                                     look_up = id),
                                       label = T("Cluster"),
                                       #comment = Script to filter the cluster_subsector drop down
                                       ondelete = "RESTRICT"
                                       )    
    
    shn_import_table("cluster_cluster")
    # -----------------------------------------------------------------------------
    # Cluster Subsector
    resource = "subsector"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            cluster_id(),
                            Field("abrv", length=64, notnull=True, unique=True),
                            Field("name", length=128),
                            migrate=migrate, *s3_meta_fields()
                            )        

    
    # CRUD strings
    ADD_CLUSTER_SUBSECTOR = T("Add Cluster Subsector")
    LIST_CLUSTER_SUBSECTOR = T("List Cluster Subsectors")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_CLUSTER_SUBSECTOR,
        title_display = T("Cluster Subsector Details"),
        title_list = LIST_CLUSTER_SUBSECTOR,
        title_update = T("Edit Cluster Subsector"),
        title_search = T("Search Cluster Subsectors"),
        subtitle_create = T("Add New Cluster Subsector"),
        subtitle_list = T("Cluster Subsectors"),
        label_list_button = LIST_CLUSTER_SUBSECTOR,
        label_create_button = ADD_CLUSTER_SUBSECTOR,
        label_delete_button = T("Delete Cluster Subsector"),
        msg_record_created = T("Cluster Subsector added"),
        msg_record_modified = T("Cluster Subsector updated"),
        msg_record_deleted = T("Cluster Subsector deleted"),
        msg_list_empty = T("No Cluster Subsectors currently registered"))     
    
    
    def shn_cluster_subsector_represent(id):
        record = db(db.cluster_subsector.id == id).select(db.cluster_subsector.cluster_id,
                                                          db.cluster_subsector.abrv,
                                                          limitby = (0,1) ).first()
        return shn_cluster_subsector_requires_represent( record) 
        
    def shn_cluster_subsector_requires_represent(record):
        if record:
            cluster_record = db(db.cluster_cluster.id == record.cluster_id).select(db.cluster_cluster.abrv,
                                                          limitby = (0,1) ).first()
            if cluster_record:
                cluster = cluster_record.abrv
            else:
                cluster = NONE
            return "%s:%s" %(cluster,record.abrv)
        else:
            return NONE        


    cluster_subsector_id = S3ReusableField("cluster_subsector_id", db.cluster_subsector, sortby="abrv",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, 
                                                                       "cluster_subsector.id",
                                                                       shn_cluster_subsector_requires_represent, 
                                                                       sort=True)),
                                       represent = shn_cluster_subsector_represent,
                                       label = T("Cluster Subsector"),
                                       #comment = Script to filter the cluster_subsector drop down
                                       ondelete = "RESTRICT"
                                       ) 
        
    shn_import_table("cluster_subsector")  
    # -----------------------------------------------------------------------------
                        