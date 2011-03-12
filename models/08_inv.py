# -*- coding: utf-8 -*-
"""
    Inventory Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    A module to record inventories of items at a location (site)
"""
#==============================================================================
inv_menu = [
            #[T("Home"), False, URL(r=request, c="inv", f="index")],
            [T("Catalog Items"), False, URL(r=request, c="supply", f="item"),
            [
                [T("List"), False, URL(r=request, c="supply", f="item")],
                [T("Add"), False, URL(r=request, c="supply", f="item", args="create")],
            ]],            
            [T("Sites"), False, URL(r=request, c="org", f="site"),
            [
                [T("List"), False, URL(r=request, c="org", f="site")],
                [T("Add"), False, URL(r=request, c="org", f="site", args="create")],
            ]],
            [T("Request"), False, URL(r=request, c="req", f="req"),
            [
                [T("List"), False, URL(r=request, c="req", f="req")],
          #      [T("Add"), False, URL(r=request, c="inv", f="req", args="create")],
            ]],
           # [T("Receive"), False, URL(r=request, c="inv", f="recv"),
           # [
           #     [T("List"), False, URL(r=request, c="inv", f="recv")],
           #     [T("Add"), False, URL(r=request, c="inv", f="recv", args="create")],
           # ]],
           # [T("Send"), False, URL(r=request, c="inv", f="send"),
           # [
           #     [T("List"), False, URL(r=request, c="inv", f="send")],
           #     [T("Add"), False, URL(r=request, c="inv", f="send", args="create")],
           # ]],
            ]
if s3_has_role(1):
    inv_menu.append(
        [T("Item Categories"), False, URL(r=request, c="supply", f="item_category"),[
            [T("List"), False, URL(r=request, c="supply", f="item_category")],
            [T("Add"), False, URL(r=request, c="supply", f="item_category", args="create")]
        ]]
    )
#==============================================================================
module = "inv"
if deployment_settings.has_module("org"):

    #==============================================================================
    # Inventory Item
    #
    resourcename = "inv_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.org_site), # site_id
                            item_id(),
                            item_pack_id(),
                            Field("quantity", 
                                  "double",
                                  notnull = True),
                            #Field("pack_quantity",
                            #      "double",
                            #      compute = shn_record_pack_quantity),   
                            Field("expiry_date",
                                  "date"),                            
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    
    db.inv_inv_item.virtualfields.append(item_pack_virtualfields(tablename = "inv_inv_item"))    

    # CRUD strings
    INV_ITEM = T("Inventory Item")
    ADD_INV_ITEM = T("Add Inventory Item")
    LIST_INV_ITEMS = T("List Inventory Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INV_ITEM,
        title_display = T("Inventory Item Details"),
        title_list = LIST_INV_ITEMS,
        title_update = T("Edit Inventory Item"),
        title_search = T("Search Inventory Items"),
        subtitle_create = T("Add New Inventory Item"),
        subtitle_list = T("Inventory Items"),
        label_list_button = LIST_INV_ITEMS,
        label_create_button = ADD_INV_ITEM,
        label_delete_button = T("Delete Inventory Item"),
        msg_record_created = T("Inventory Item added"),
        msg_record_modified = T("Inventory Item updated"),
        msg_record_deleted = T("Inventory Item deleted"),
        msg_list_empty = T("No Inventory Items currently registered"))
    
    def shn_inv_item_represent (id):
        record = db( (db.inv_inv_item.id == id) & \
                     (db.inv_inv_item.item_id == db.supply_item.id) 
                    ).select( db.supply_item.name,
                              limitby = [0,1]).first()
        if record:
            return record.name
        else:
            return None  

    # Reusable Field
    inv_item_id = S3ReusableField("inv_item_id", db.inv_inv_item,
                                    requires = IS_ONE_OF(db, 
                                                         "inv_inv_item.id", 
                                                         shn_inv_item_represent, 
                                                         orderby="inv_inv_item.id", 
                                                         sort=True),
                                    represent = shn_inv_item_represent,
                                    label = INV_ITEM,
                                    comment = DIV( _class="tooltip",
                                                   _title="%s|%s" % (INV_ITEM,
                                                                     T("Select Items from this Inventory"))),
                                    ondelete = "RESTRICT"
                                    )    

    # Inv item as component of Sites
    s3xrc.model.add_component(module, 
                              resourcename,
                              multiple = True,
                              joinby = super_key(db.org_site)
                              )
    
    # Store items as components of Supply Items 
    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=dict(supply_item = "item_id")
                              )     
    
    #Store Items as component of packs
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(supply_item_pack = "item_pack_id")) 
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the site's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = shn_component_copy_role_func(component_name = tablename, 
                                                resource_name = "org_site", 
                                                fk = "site_id",
                                                pk = "site_id")
    )      


    #==============================================================================
    # Received (In/Receive / Donation / etc)
    #
    
    inv_recv_type = {0:NONE,
                      1:"Another Store",
                      2:"Donation",
                      3:"Supplier"}
    
    SHIP_STATUS_IN_PROCESS = 0
    SHIP_STATUS_RECEIVED   = 1
    SHIP_STATUS_SENT       = 2
    
    shipment_status = { SHIP_STATUS_IN_PROCESS: T("In Process"),
                        SHIP_STATUS_RECEIVED:   T("Received"),
                        SHIP_STATUS_SENT:       T("Sent")
                        }    
     
    resourcename = "recv"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("datetime",
                                  "datetime",
                                  label = "Date Received",
                                  writable = False,
                                  readable = False #unless the record is locked
                                  ),
                            Field("type",
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(inv_recv_type)),
                                  represent = lambda type: inv_recv_type[type] if type else NONE,
                                  default = 0,
                                  ),                                  
                            super_link(db.org_site), #(label = T("By Warehouse")),
                            organisation_id("from_organisation_id",
                                            label = T("From Organisation")),
                            location_id("from_location_id",
                                        label = T("From Location")),
                            Field("from_person"), #Text field, because lookup to pr_person record is unnecessary complex workflow                                              
                            Field("status", 
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(shipment_status)),
                                  represent = lambda status: shipment_status.get(status),       
                                  default = SHIP_STATUS_IN_PROCESS,                           
                                  writable = False,
                                  ),
                            person_id(name = "recipient_id",
                                      label = T("Received By")),
                            comments(),
                            migrate=migrate, *s3_meta_fields()
                            )

    # -----------------------------------------------------------------------------
    # CRUD strings
    ADD_RECV = T("Receive Shipment")
    LIST_RECV = T("List Received Shipments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RECV,
        title_display = T("Received Shipment Details"),
        title_list = LIST_RECV,
        title_update = T("Edit Received Shipment"),
        title_search = T("Search Received Shipments"),
        subtitle_create = ADD_RECV,
        subtitle_list = T("Received Shipments"),
        label_list_button = LIST_RECV,
        label_create_button = ADD_RECV,
        label_delete_button = T("Delete Received Shipment"),
        msg_record_created = T("Shipment Created"),
        msg_record_modified = T("Received Shipment updated"),
        msg_record_deleted = T("Received Shipment canceled"),
        msg_list_empty = T("No Received Shipments")
    )

    # -----------------------------------------------------------------------------
    def shn_recv_represent(id):
        if id:
            inv_recv_row = db(db.inv_recv.id == id).\
                              select(db.inv_recv.datetime,
                                     db.inv_recv.from_location_id,
                                     limitby=(0, 1))\
                              .first()
            return SPAN( shn_gis_location_represent( inv_recv_row.from_location_id),
                         " - ",
                        inv_recv_row.datetime)
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    recv_id = S3ReusableField("recv_id", db.inv_recv, sortby="datetime",
                                 requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                 "inv_recv.id",
                                                                 shn_recv_represent,
                                                                 orderby="inv_recv.datetime", sort=True)),
                                 represent = shn_recv_represent,
                                 label = T("Receive Shipment"),
                                 #comment = DIV(A(ADD_DISTRIBUTION, _class="colorbox", _href=URL(r=request, c="inv", f="distrib", args="create", vars=dict(format="popup")), _target="top", _title=ADD_DISTRIBUTION),
                                 #          DIV( _class="tooltip", _title=T("Distribution") + "|" + T("Add Distribution."))),
                                 ondelete = "RESTRICT"
                                 )

    #------------------------------------------------------------------------------
    # Recv as a component of Sites
    s3xrc.model.add_component(module, 
                              resourcename,
                              multiple = True,
                              joinby = super_key(db.org_site)
                              )

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after creation
    recv_item_url = URL(r=request, c="inv", f="recv", args=["[id]", "recv_item"])
    s3xrc.model.configure(table,
                          create_next = recv_item_url,
                          update_next = recv_item_url)
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the site's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = shn_component_copy_role_func(component_name = tablename, 
                                                resource_name = "org_site", 
                                                fk = "site_id",
                                                pk = "site_id")
    )    
      
    # -------------------------------------------------------------------------        
    def shn_inv_recv_form (xrequest, **attr):   
        db.inv_recv.datetime.readable = True  
        db.inv_recv.site_id.readable = True  
        db.inv_recv.site_id.label = T("By Inventory")
        db.inv_recv.site_id.represent = shn_site_represent
        return shn_component_form( xrequest, 
                                   componentname = "recv_item", 
                                   formname = T("Goods Received Note"),
                                   filename = T("GRN"),
                                   **attr)
        
    s3xrc.model.set_method(module, resourcename, 
                           method='form', action=shn_inv_recv_form ) 
    
    # -------------------------------------------------------------------------        
    def shn_inv_recv_donation_cert (xrequest, **attr):   
        db.inv_recv.datetime.readable = True  
        db.inv_recv.type.readable = False
        db.inv_recv.site_id.readable = True  
        db.inv_recv.site_id.label = T("By Inventory")
        db.inv_recv.site_id.represent = shn_site_represent
        return shn_component_form( xrequest, 
                                   componentname = "recv_item", 
                                   formname = T("Donation Certificate"),
                                   filename = T("DC"),
                                   **attr)
        
    s3xrc.model.set_method(module, resourcename, 
                           method='cert', action=shn_inv_recv_donation_cert )     
        
    # -------------------------------------------------------------------------
    def shn_component_form( xrequest, **attr):     
        """
        Copied from modules/s3/s3export.py:pdf
        """
        module, resourcename, table, tablename = xrequest.target()
        resource = xrequest.resource             
        componentname = attr.get("componentname") 
        formname = attr.get("formname")
        filename = attr.get("filename")        
        component = resource.components[componentname].resource
        
        xml = s3xrc.xml
        
        import StringIO
        from gluon.contenttype import contenttype

        # Import ReportLab
        try:
            from reportlab.lib.units import cm
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            session.error = self.ERROR.REPORTLAB_ERROR
            redirect(URL(r=request, extension=""))

        # Import Geraldo
        try:
            from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
            from geraldo.generators import PDFGenerator
        except ImportError:
            session.error = self. ERROR.GERALDO_ERROR
            redirect(URL(r=request, extension=""))

        # Create output stream
        output = StringIO.StringIO()
        
        # Settings
        COLWIDTH = 3.0
        LEFTMARGIN = 0.2
        TITLEHEIGHT = 1.0
        LINEHEIGTH = 0.5
        LABELWIDTH = 4.0
        VALUEWIDTH = 16.0
        clean_str = lambda text: s3xrc.xml.xml_encode(str(text)
                                                      ).decode("utf-8")

        # Add Title
        header_ele = [ SystemField(
                            expression = "%(report_title)s",
                            top = 0.1 * cm,
                            left = 0,
                            height = TITLEHEIGHT * cm,
                            width = 20 * cm, # BAND_WIDTH,
                            style = {
                                "fontName": "Helvetica-Bold",
                                "fontSize": 14,
                                #"alignment": TA_CENTER
                                }
                            )]
        detail_ele = []
         
        #Add values of the primary resource      
        fields = resource.readable_fields()#subset=list_fields)
        line = 0;
        for field in fields:
            if field.name == "id":
                continue
            header_ele.append(Label(text= clean_str( field.label ),
                                       top= (TITLEHEIGHT + line * LINEHEIGTH) * cm, 
                                       left=LEFTMARGIN*cm, 
                                       width=LABELWIDTH*cm,
                                       style={'fontName': 'Helvetica-Bold'})
                              )
            value = xrequest.record[field.name]
            header_ele.append(Label(text=clean_str( 
                                            s3xrc.represent(field,
                                                            value=value,
                                                            strip_markup=True,
                                                            xml_escape=True)
                                            ),
                                       top= (TITLEHEIGHT + line * LINEHEIGTH) * cm, 
                                       left=(LEFTMARGIN + LABELWIDTH) * cm,
                                       width=VALUEWIDTH*cm,
                                       style={'fontName': 'Helvetica'})
                              )
            line += 1

        #Add table for component resource
        fields = component.readable_fields()
        

        component_represent = lambda field, value, table=component.table: \
                                     clean_str( s3xrc.represent(table[field],
                                                     value=value,
                                                     strip_markup=True,
                                                     xml_escape=True)
                                               )   
        line += 1 #blank line before component table           
        column = 0
        for field in fields:
            if field.name == "id":
                continue            
            # Append component table column headers
            label = Label(text= clean_str( field.label ),
                          top = (TITLEHEIGHT + line * LINEHEIGTH) * cm, 
                          left = (LEFTMARGIN + column * COLWIDTH) *cm,
                          style={'fontName': 'Helvetica-Bold'}
                          )
            header_ele.append(label)

            # Append value
            value = ObjectValue(attribute_name = field.name,
                                left = (LEFTMARGIN + column * COLWIDTH) *cm,
                                width = COLWIDTH * cm,
                                get_value = lambda instance, 
                                                   column = field.name: \
                                            component_represent(column, 
                                                                instance[column]),
                                style={'fontName': 'Helvetica'}
                                )
            detail_ele.append(value)

            # Increase left margin
            column += 1

        component_records = xrequest.record[component.tablename].select()

        class MyReport(Report):
            title = clean_str ( formname )
            page_size = A4
            class band_page_header(ReportBand):
                height = (TITLEHEIGHT + (line+1) * LINEHEIGTH) * cm
                auto_expand_height = True
                elements = header_ele
                borders = {"bottom": True}              
            class band_page_footer(ReportBand):
                height = 0.5*cm
                elements = [
                    Label(text="%s" % request.utcnow.date(), top=0.1*cm, left=0),
                    SystemField(expression="Page: %(page_number)d of %(page_count)d", top=0.1*cm,
                        width=BAND_WIDTH, style={"alignment": TA_RIGHT}),
                ]
                borders = {"top": True}
            class band_detail(ReportBand):
                height = LINEHEIGTH * cm
                auto_expand_height = True
                elements = detail_ele
        report = MyReport(queryset=component_records)
        report.generate_by(PDFGenerator, filename=output)

        # Set content type and disposition headers
        if response:
            filename = "%s.pdf" % filename
            response.headers["Content-Type"] = contenttype(".pdf")
            response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename

        # Return the stream
        output.seek(0)
        return output.read()        
    
    #==============================================================================
    # In (Receive / Donation / etc) Items
    #
    resourcename = "recv_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            recv_id(),
                            item_id(),
                            item_pack_id(),
                            Field("quantity", "double",
                                  notnull = True),
                            comments(),
                            req_item_id(readable = False,
                                             writable = False),
                            migrate=migrate, *s3_meta_fields())
        
    #pack_quantity virtual field
    table.virtualfields.append(item_pack_virtualfields(tablename = tablename))      

    # CRUD strings
    ADD_RECV_ITEM = T("Add Item to Shipment")
    LIST_RECV_ITEMS = T("List Received Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_RECV_ITEM,
        title_display = T("Received Item Details"),
        title_list = LIST_RECV_ITEMS,
        title_update = T("Edit Received Item"),
        title_search = T("Search Received Items"),
        subtitle_create = T("Add New Received Item"),
        subtitle_list = T("Shipment Items"),
        label_list_button = LIST_RECV_ITEMS,
        label_create_button = ADD_RECV_ITEM,
        label_delete_button = T("Delete Received Item"),
        msg_record_created = T("Item added to shipment"),
        msg_record_modified = T("Received Item updated"),
        msg_record_deleted = T("Received Item deleted"),
        msg_list_empty = T("No Received Items currently registered"))

    #------------------------------------------------------------------------------
    # In Items as component of In
    # In Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(inv_recv = "recv_id",
                                          supply_item = "item_id")) 
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the recv's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = shn_component_copy_role_func(component_name = tablename, 
                                                resource_name = "inv_recv", 
                                                fk = "recv_id")
    )     

    #==============================================================================
    def shn_location_id_to_site_id(r, field = "location_id"):
        if r[field]:
            return shn_get_db_field_value(db,
                                          "org_site",
                                          "site_id",
                                          r[field],
                                          "location_id")
        else:
            return None        

    #==============================================================================
    # Send (Outgoing / Dispatch / etc)
    #       
    shn_to_location_id_to_site_id = lambda r, field = "to_location_id": \
                                       shn_location_id_to_site_id(r,field)
    resourcename = "send"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field( "datetime", 
                                   "datetime",
                                   label = T("Date Sent")),
                            super_link(db.org_site), #( label = T("From Warehouse")),
                            location_id( "to_location_id",
                                         label = T("To Location") ),
                            Field("to_site_id",                                  
                                  db.org_site,
                                  label = T("To Site"),
                                  compute = shn_to_location_id_to_site_id
                                  ),                               
                            Field("status", 
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(shipment_status)),
                                  represent = lambda status: shipment_status.get(status),       
                                  default = SHIP_STATUS_IN_PROCESS,                           
                                  writable = False,
                                  ),
                            person_id(name = "recipient_id",
                                      label = T("To Person")),
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    
    # -----------------------------------------------------------------------------
    # CRUD strings
    ADD_SEND = T("Add New Shipment to Send")
    LIST_SEND = T("List Shipments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SEND,
        title_display = T("Shipment Details"),
        title_list = LIST_SEND,
        title_update = T("Edit Shipment to Send"),
        title_search = T("Search Sent Shipments"),
        subtitle_create = ADD_SEND,
        subtitle_list = T("Shipments"),
        label_list_button = LIST_SEND,
        label_create_button = ADD_SEND,
        label_delete_button = T("Delete Sent Shipment"),
        msg_record_created = T("Shipment Created"),
        msg_record_modified = T("Sent Shipment updated"),
        msg_record_deleted = T("Sent Shipment canceled"),
        msg_list_empty = T("No Sent Shipments"))

    # -----------------------------------------------------------------------------
    def shn_send_represent(id):
        if id:
            send_row = db(db.inv_send.id == id).\
                              select(db.inv_send.datetime,
                                     db.inv_send.to_location_id,
                                     limitby=(0, 1))\
                              .first()
            return SPAN( shn_gis_location_represent( send_row.to_location_id),
                         " - ",
                        send_row.datetime)
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    send_id = S3ReusableField( "send_id", db.inv_send, sortby="datetime",
                               requires = IS_NULL_OR(IS_ONE_OF(db,
                                                               "inv_send.id",
                                                               shn_send_represent,
                                                               orderby="inv_send_id.datetime", 
                                                               sort=True)),
                               represent = shn_send_represent,
                               label = T("Send Shipment"),
                               ondelete = "RESTRICT"
                               )

    #------------------------------------------------------------------------------
    # Inv Send added as a component of Inventory Store in controller

    #------------------------------------------------------------------------------
    # Redirect to the Items tabs after create & update
    url_send_items = URL(r=request, c="inv", f="send", args=["[id]", "send_item"])
    s3xrc.model.configure(table,
                          create_next = url_send_items,
                          update_next = url_send_items
                          )
    
    #------------------------------------------------------------------------------
    # Update owned_by_role to the site's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = shn_component_copy_role_func(component_name = tablename, 
                                                resource_name = "org_site", 
                                                fk = "site_id",
                                                pk = "site_id")
    ) 
    
    # send set as a component of Sites in controller, depending if it is outgoing or incoming
    
    # -------------------------------------------------------------------------        
    def shn_inv_send_form (xrequest, **attr):   
        db.inv_recv.datetime.readable = True  
        return shn_component_form( xrequest, 
                                   componentname = "send_item", 
                                   formname = T("Consignment Note"),
                                   filename = T("CN"),
                                   **attr)
        
    s3xrc.model.set_method(module, resourcename, 
                           method='form', action=shn_inv_send_form ) 
    
    #==============================================================================
    # Send (Outgoing / Dispatch / etc) Items
    #
    log_sent_item_status = {0: NONE,
                            1: "Invalid Quantity"
                            }

    resourcename = "send_item"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            send_id(),
                            inv_item_id(),
                            item_pack_id(),
                            Field("quantity", "double",
                                  notnull = True),
                            comments(),
                            Field("status",
                                  "integer",
                                  requires = IS_NULL_OR(IS_IN_SET(log_sent_item_status)),
                                  represent = lambda status: log_sent_item_status[status] if status else log_sent_item_status[0],
                                  writable = False),
                            req_item_id(readable = False,
                                        writable = False),      
                            migrate=migrate, *s3_meta_fields())
    
    #pack_quantity virtual field
    table.virtualfields.append(item_pack_virtualfields(tablename = tablename))       

    # CRUD strings
    ADD_SEND_ITEM = T("Add Item to Shipment")
    LIST_SEND_ITEMS = T("List Sent Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SEND_ITEM,
        title_display = T("Sent Item Details"),
        title_list = LIST_SEND_ITEMS,
        title_update = T("Edit Sent Item"),
        title_search = T("Search Sent Items"),
        subtitle_create = T("Add New Sent Item"),
        subtitle_list = T("Shipment Items"),
        label_list_button = LIST_SEND_ITEMS,
        label_create_button = ADD_SEND_ITEM,
        label_delete_button = T("Delete Sent Item"),
        msg_record_created = T("Item Added to Shipment"),
        msg_record_modified = T("Sent Item updated"),
        msg_record_deleted = T("Sent Item deleted"),
        msg_list_empty = T("No Sent Items currently registered"))

    #------------------------------------------------------------------------------
    # Send Items as component of Send
    # Send Items as a component of Items
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(inv_send = "send_id",
                                          inv_item = "inv_item_id"))
    #------------------------------------------------------------------------------
    # Update owned_by_role to the send's owned_by_role    
    s3xrc.model.configure(
        table, 
        onaccept = shn_component_copy_role_func(component_name = tablename, 
                                                resource_name = "inv_send", 
                                                fk = "send_id")
    ) 
    #==============================================================================    
            
    #==============================================================================
    # Inventory Controller Helper functions

    #------------------------------------------------------------------------------
    def shn_add_dynamic_inv_components():
        """
        Add inv_send as component joinby field according to tab selected
        and returns prep function 
        """
        if "send" in request.args:
            if request.get_vars.get("select","sent") == "incoming":
                s3xrc.model.add_component(
                    "inv",
                    "send",
                    multiple=True,
                    joinby= {"org_site.site_id": "to_site_id" #super_key(db.org_site)
                             }
                    )
                
                # Hide the Add button for incoming shipments
                s3xrc.model.configure(db.inv_send, insertable=False)
                
                # Probably need to adjust some more CRUD strings:
                s3.crud_strings["inv_send"].update(
                    msg_record_modified = T("Incoming Shipment updated"),
                    msg_record_deleted = T("Incoming Shipment canceled"),
                    msg_list_empty = T("No Incoming Shipments"))
                
                response.s3.actions = [dict(url = str(URL(r=request,
                                                      c = "inv",
                                                      f = "recv_sent",
                                                      args = ["[id]"]
                                                      )
                                                   ),
                                            _class = "action-btn",
                                            label = "Receive")
                                        ]                    
            else:
                s3xrc.model.add_component(
                    "inv",
                    "send",
                    multiple=True,
                    joinby=super_key(db.org_site)
                    )                                              
                s3.crud_strings["inv_send"].update(
                    msg_record_modified = T("Sent Shipment updated"),
                    msg_record_deleted = T("Sent Shipment canceled"),
                    msg_list_empty = T("No Sent Shipments"))    
            
    #------------------------------------------------------------------------------   
    def shn_inv_prep(r):      
        if "inv_item" in request.args:
            #Filter out items which are already  in this inventory
            inv_item_rows =  db((db.inv_inv_item.site_id == r.record.site_id) &
                                (db.inv_inv_item.deleted == False)           
                                ).select(db.inv_inv_item.item_id)
            item_ids = [r.item_id for r in inv_item_rows]
            db.inv_inv_item.item_id.requires.set_filter(not_filterby = "id",
                                                        not_filter_opts = item_ids)
        
        
        if "send" in request.args and \
            request.get_vars.get("select","sent") == "incoming":        
            #Display only incoming shipments which haven't been received yet
            filter = (db.inv_send.status == SHIP_STATUS_SENT)
            r.resource.add_component_filter("send", filter)  

    #------------------------------------------------------------------------------
    #Session dictionary to indicate if a site inv should be shown
    if session.s3.show_inv == None:
        session.s3.show_inv = {}
        
    def shn_show_inv_tabs(r):
        """
        """
        try:
            show_inv = eval(r.request.vars.show_inv)
        except:
            show_inv = None
        if show_inv == True or show_inv == False:
            session.s3.show_inv["%s_%s" %  (r.name,r.id)] = show_inv
        else:
            show_inv = session.s3.show_inv.get("%s_%s" %  (r.name,r.id))
            
        if show_inv:
            inv_btn = A(T("Hide Inventory"),
                        _href = URL(r = request, 
                                    args = r.id,
                                    vars = dict(show_inv = False)),
                        _class = "action-btn"
                        )
            inv_tabs = [(T("Inventory Items"), "inv_item"),
                        (T("Request"), "req"),
                        (T("Match Requests"), "match_req"),
                        (T("Incoming"), "send", dict(select="incoming")),
                        (T("Receive" ), "recv"),
                        (T("Send"), "send", dict(select="sent")),
                        (T("Commit"), "commit"),
                        (T("- Inventory"), None, dict(show_inv="False")),
                        ]                        
        else:
            inv_tabs = [(T("+ Inventory"), None, dict(show_inv="True"))]
                        
        return inv_tabs 
