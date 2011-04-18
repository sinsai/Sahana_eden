"""
    Request Management

    @author: Michael Howden (michael@sahanafoundation.org)
    @author: Fran Boon
    @date-created: 2010-08-16

    A module to record requests for:
     - supplies (items)
     - staff
     - assets
     - other
"""

module = "req"
if deployment_settings.has_module(module) or deployment_settings.has_module("inv"):
    req_menu = [
                    [T("Requests"), False, aURL(r=request, c="req", f="req"), [
                        [T("New"), False, aURL(r=request, c="req", f="req", args="create")]
                    ]],
                    [T("Request Items"), False, aURL(r=request, c="req", f="req_item")],
                    [T("Commitments"), False, aURL(r=request, c="req", f="commit")],
                    #[T("Search Requested Items"), False, aURL(r=request, c="req", f="req_item", args="search")],
                ]

    REQ_STATUS_NONE       = 0
    REQ_STATUS_PARTIAL    = 1
    REQ_STATUS_COMPLETE   = 2

    req_status_opts = { REQ_STATUS_NONE:       T("None"),
                        REQ_STATUS_PARTIAL:    T("Partial"),
                        REQ_STATUS_COMPLETE:   T("Complete")
                       }

    req_status= S3ReusableField("req_status",
                                "integer",
                                label = T("Request Status"),
                                requires = IS_NULL_OR(IS_IN_SET(req_status_opts,
                                                                zero = None)),
                                represent = lambda opt: req_status_opts.get(opt, UNKNOWN_OPT),
                                default = REQ_STATUS_NONE,
                                writable = deployment_settings.get_req_status_writable(),
                                )

    req_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }

    req_type_opts = {
        #1:T("Supplies"),
        #2:T("Assets"),
        #3:T("Staff"),
        #4:T("Shelter"),
        9:T("Other")
    }
    if deployment_settings.has_module("inv"):
        req_type_opts[1] = T("Supplies")
    #if deployment_settings.has_module("asset"):
    #    req_type_opts[2] = T("Assets")
    #if deployment_settings.has_module("hrm"):
    #    req_type_opts[3] = T("Staff")
    #if deployment_settings.has_module("cr"):
    #    req_type_opts[4] = T("Shelter")

    def shn_req_priority_represent(id):
        src = "/%s/static/img/priority/priority_%d.gif" % \
                  (request.application, (id or 4))
        return DIV(IMG(_src= src))

    # -------------------------------------------------------------------------
    # Requests
    resourcename = "req"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link( db.org_site, 
                                        writable = True,
                                        readable = True,
                                        label = T("Requested By Site"),
                                        represent = shn_site_represent
                                        ),                            
                            Field("date", #DO NOT CHANGE THIS
                                  "date",
                                  label = T("Date Requested"),
                                  default = request.utcnow),
                            Field("date_required",
                                  "date",
                                  label = T("Date Required"),
                                  requires = [IS_EMPTY_OR(IS_DATE_IN_RANGE(
                                                minimum=request.utcnow.date(),
                                                error_message="%s %%(min)s!" %
                                                    T("Enter a valid future date")))],
                                  widget = S3DateWidget(past=0, future=120)),  # Months, so 10 years
                            person_id("requester_id",
                                      label = T("Requester"),
                                      default = s3_logged_in_person()),
                            Field("type", "integer",
                                  requires = IS_IN_SET(req_type_opts),
                                  represent = lambda opt: req_type_opts.get(opt, UNKNOWN_OPT),
                                  label = T("Request Type")),
                            Field("priority",
                                  "integer",
                                  label = T("Priority"),
                                  represent = shn_req_priority_represent,
                                  requires = IS_NULL_OR(
                                                IS_IN_SET(req_priority_opts))
                                  ),
                            req_status("commit_status",
                                       label = T("Commit. Status"),
                                       ),
                            req_status("transit_status",
                                       label = T("Transit Status"),
                                       ),
                            req_status("fulfil_status",
                                       label = T("Fulfil. Status"),
                                       ),
                            Field("cancel",
                                  "boolean",
                                  default = False),
                            comments(label=T("Message"), comment=""),
                            migrate=migrate, *s3_meta_fields())

    # CRUD strings
    ADD_REQUEST = T("Make Request")
    LIST_REQUEST = T("List Requests")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REQUEST,
        title_display = T("Request Details"),
        title_list = LIST_REQUEST,
        title_update = T("Edit Request"),
        title_search = T("Search Requests"),
        subtitle_create = ADD_REQUEST,
        subtitle_list = T("Requests"),
        label_list_button = LIST_REQUEST,
        label_create_button = ADD_REQUEST,
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Request Added"),
        msg_record_modified = T("Request Updated"),
        msg_record_deleted = T("Request Canceled"),
        msg_list_empty = T("No Requests"))

    # Represent
    def shn_req_represent(id, link = True):
        id = int(id) if id else None
        if id:
            query = (db.req_req.id == id)
            req_row = db(query).select(db.req_req.date,
                                       db.req_req.site_id,
                                       limitby=(0, 1)).first()
            req = "%s - %s" % (shn_site_represent(req_row.site_id,
                                                  link = False),
                               req_row.date)

            if link:
                return A(req,
                         _href = URL(r = request,
                                     c = "req",
                                     f = "req",
                                     args = [id]),
                         _title = T("Go to Request"))
            else:
                return req
        else:
            return NONE

    # Reusable Field
    req_id = S3ReusableField("req_id", db.req_req, sortby="request_date",
                             requires = IS_ONE_OF(db,
                                                  "req_req.id",
                                                  lambda id: 
                                                    shn_req_represent(id,
                                                                      False),
                                                  orderby="req_req.date",
                                                  sort=True),
                             represent = shn_req_represent,
                             label = T("Request"),
                             ondelete = "RESTRICT"
                            )

    # Request as a component of Sites
    s3xrc.model.add_component(module,
                              resourcename,
                              multiple = True,
                              joinby = super_key(db.org_site)
                              )

    #----------------------------------------------------------------------
    def shn_req_onaccept(form):
        # Update owned_by_role to the site's owned_by_role
        shn_component_copy_role_func(component_name = "req_req",
                                     resource_name = "org_site",
                                     fk = "site_id",
                                     pk = "site_id"),
    
        # Configure the next page to go to based on the request type
        table = db.req_req
        if form.vars.type == "1" and deployment_settings.has_module("inv"):
            s3xrc.model.configure(table,
                                  create_next = URL(r=request,
                                                    c="req",
                                                    f="req",
                                                    args=["[id]", "req_item"]))
        elif form.vars.type == "2" and deployment_settings.has_module("asset"):
            s3xrc.model.configure(table,
                                  create_next = URL(r=request,
                                                    c="req",
                                                    f="req",
                                                    args=["[id]", "req_asset"]))
        #elif form.vars.type == "3" and deployment_settings.has_module("hrm"):
        #    s3xrc.model.configure(table,
        #                          create_next = URL(r=request,
        #                                            c="req",
        #                                            f="req",
        #                                            args=["[id]", "req_staff"]))
        #elif form.vars.type == "4" and deployment_settings.has_module("cr"):
        #    s3xrc.model.configure(table,
        #                          create_next = URL(r=request,
        #                                            c="req",
        #                                            f="req",
        #                                            args=["[id]", "req_shelter"]))

    s3xrc.model.configure(table,
                          onaccept = shn_req_onaccept,
                          list_fields = ["site_id",
                                         "date",
                                         "date_required",
                                         "priority",
                                         "type",
                                         "commit_status",
                                         "transit_status",
                                         "fulfil_status"]
                        )

    #--------------------------------------------------------------------------
    def shn_req_create_form_mods():
        """
            Function to be called from REST prep functions
             - main module & site components
        """
        # Hide fields which don't make sense in a Create form
        table = db.req_req
        table.commit_status.readable = table.commit_status.writable = False
        table.transit_status.readable = table.transit_status.writable = False
        table.fulfil_status.readable = table.fulfil_status.writable = False
        table.cancel.readable = table.cancel.writable = False
        return

    # Script to inject into Pages which include Request create forms
    req_helptext_script = SCRIPT("""
        $(function() {
            var req_help_msg = '%s\\n\\n%s';
            // Provide some default help text in the Message box if message is empty
            if (!$('#req_req_comments').val()) {
                $('#req_req_comments').addClass('default-text').attr({ value: req_help_msg }).focus(function(){
                    if($(this).val() == req_help_msg){
                        // Clear on click if still default
                        $(this).val('').removeClass('default-text');
                    }
                });
                $('form').submit( function() {
                    // Do the normal form-submission tasks
                    // @ToDo: Look to have this happen automatically
                    // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
                    // http://api.jquery.com/bind/
                    S3ClearNavigateAwayConfirm();

                    if ($('#req_req_comments').val() == req_help_msg) {
                        // Default Message still showing
                        if ($('#req_req_type').val() == 9) {
                            // Requests of type 'Other' need this field to be mandatory
                            $('#req_req_comments').after('<div id="type__error" class="error" style="display: block;">%s</div>');
                            // Reset the Navigation protection
                            S3SetNavigateAwayConfirm();
                            // Move focus to this field
                            $('#req_req_comments').focus();
                            // Prevent the Form's save from continuing
                            return false;
                        } else {
                            // Clear the default message
                            $('#req_req_comments').val('');
                            // Allow the Form's save to continue
                            return true;
                        }
                    } else {
                        // Allow the Form's save to continue
                        return true;
                    }
                });
            }
        });
        """ % (T('If the request is for type "Other", you should enter a summary of the request here.'),
               T("For other types, the next screen will allow you to enter the relevant details..."),
               T("Message field is required!"))
        )
    # ==========================================================================
    def shn_req_rheader(r):
        """ Resource Header for Requests """
    
        if r.representation == "html":
            if r.name == "req":
                req_record = r.record
                if req_record:
    
                    tabs = [(T("Edit Details"), None)]
                    if deployment_settings.has_module("inv"):
                        tabs.append((T("Items"), "req_item"))
    
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                    
                    site_id = request.vars.site_id
                    if site_id:
                        site_name = shn_site_represent(site_id, link = False)
                        commit_btn = TAG[""](
                                    A( T("Commit from %s") % site_name,    
                                        _href = URL( r=request,
                                                     c = "req",
                                                     f = "commit_req",
                                                     args = [r.id],
                                                     vars = dict(site_id = site_id)
                                                    ),
                                        _class = "action-btn"
                                       ),
                                    A( T("Send from %s") % site_name,    
                                        _href = URL( r=request,
                                                     c = "req",
                                                     f = "send_req",
                                                     args = [r.id],
                                                     vars = dict(site_id = site_id)
                                                    ),
                                        _class = "action-btn"
                                       )
                                    )
                    else:
                        commit_btn = A( T("Commit"),     
                                        _href = URL( r=request,
                                                     c = "req",
                                                     f = "commit",
                                                     args = ["create"],
                                                     vars = dict(req_id = r.id)
                                                    ),
                                        _class = "action-btn"
                                       )

    
                    rheader = DIV( TABLE(
                                       TR(
                                        TH( "%s: " % T("Date Required")),
                                        req_record.date_required,
                                        TH( "%s: " % T("Commitment Status")),
                                        req_status_opts.get(req_record.commit_status, ""),
                                        ),
                                       TR(
                                        TH( "%s: " % T("Date Requested")),
                                        req_record.date,
                                        TH( "%s: " % T("Transit Status")),
                                        req_status_opts.get(req_record.transit_status, ""),   
                                        ),
                                       TR(
                                        TH( "%s: " % T("Requested By")),
                                        shn_site_represent(req_record.site_id),
                                        TH( "%s: " % T("Fulfillment Status")),
                                        req_status_opts.get(req_record.fulfil_status, "")
                                        ),
                                       TR(
                                        TH( "%s: " % T("Comments")),
                                        TD(req_record.comments or "", _colspan=3)
                                        ),
                                    ),
                                    commit_btn,
                                    rheader_tabs
                                    )
    
                    return rheader
                else:
                    # No Record means that we are either a Create or List Create
                    # Inject the helptext script
                    return req_helptext_script
        return None

    #--------------------------------------------------------------------------
    def s3_req_match():
        """
            Function to be called from controller functions to display all request as a tab 
            for a site.
            @ToDo: Filter out requests from this site
        """
        tablename, id = request.vars.viewing.split(".")
        site_id = db[tablename][id].site_id
        response.s3.actions = [dict(url = str(URL( r=request,
                                                   c = "req",
                                                   f = "req",
                                                   args = ["[id]","check"],
                                                   vars = {"site_id": site_id}
                                                   )
                                               ),
                                    _class = "action-btn",
                                    label = str(T("Check")),
                                    ),
                               dict(url = str(URL( r=request,
                                                   c = "req",
                                                   f = "commit_req",
                                                   args = ["[id]"],
                                                   vars = {"site_id": site_id}
                                                   )
                                               ),
                                    _class = "action-btn",
                                    label = str(T("Commit")),
                                    ),
                               dict(url = str(URL( r=request,
                                                   c = "req",
                                                   f = "send_req",
                                                   args = ["[id]"],
                                                   vars = {"site_id": site_id}
                                                   )
                                               ),
                                    _class = "action-btn",
                                    label = str(T("Send")),
                                    )
                               
                               ]
        
        rheader_dict = dict(org_office = shn_office_rheader,
                            cr_shelter = shn_shelter_rheader,
                            hms_hospital = shn_hms_hospital_rheader)

        s3xrc.model.configure(db.req_req, insertable=False)
        output = s3_rest_controller("req", "req",
                                    method = "list",
                                    rheader = rheader_dict[tablename])
        if isinstance(output, dict):
            output["title"] = s3.crud_strings[tablename]["title_display"]

        return output
    # -------------------------------------------------------------------------
    def s3_req_check(r, **attr):
        site_id = r.request.vars.site_id
        site_name = shn_site_represent(site_id, link = False)
        output = {}
        output["title"] = s3.crud_strings.req_req.title_display
        output["rheader"] = shn_req_rheader(r)
        output["subtitle"] = T("Request Items") 
        
        #Get req_items & inv_items from this site
        req_items = db( (db.req_req_item.req_id == r.id ) &
                        (db.req_req_item.deleted == False ) #&
                       ).select(db.req_req_item.id,
                                db.req_req_item.item_id,
                                db.req_req_item.quantity,
                                db.req_req_item.item_pack_id,
                                db.req_req_item.quantity_commit,
                                db.req_req_item.quantity_transit,
                                db.req_req_item.quantity_fulfil,
                                )
        inv_items = db( (db.inv_inv_item.site_id == site_id ) &
                        (db.inv_inv_item.deleted == False ) #&
                       ).select(db.inv_inv_item.item_id,
                                db.inv_inv_item.quantity,
                                db.inv_inv_item.item_pack_id,
                                )
        inv_items_dict = inv_items.as_dict(key = "item_id")

        if len(req_items):
            items = TABLE(THEAD(TR(TH(""),
                                   TH(db.req_req_item.item_id.label),
                                   TH(db.req_req_item.quantity.label),
                                   TH(db.req_req_item.item_pack_id.label),
                                   TH(db.req_req_item.quantity_commit.label),
                                   TH(db.req_req_item.quantity_transit.label),
                                   TH(db.req_req_item.quantity_fulfil.label),
                                   TH(T("Quantity in %s's Inventory") % site_name)
                                  )  
                                ),
                          _id = "list",
                          _class = "dataTable display")
    
            for req_item in req_items:
                # Convert inv item quantity to req item quantity
                try:
                    inv_item = Storage(inv_items_dict[req_item.item_id])
                    inv_quantity = inv_item.quantity * \
                                   inv_item.pack_quantity / \
                                   req_item.pack_quantity
                                   
                except:
                    inv_quantity = NONE
                
                items.append(TR( A(req_item.id),
                                 shn_item_represent(req_item.item_id),
                                 req_item.quantity,
                                 shn_item_pack_represent(
                                     req_item.item_pack_id),
                                 req_item.quantity_commit,
                                 req_item.quantity_transit,
                                 req_item.quantity_fulfil,
                                 inv_quantity,
                                )
                            )
                output["items"] = items
                response.s3.actions = [req_item_inv_item_btn]
                response.s3.no_sspag = True # pag won't work 
        else:
            output["items"] = s3.crud_strings.req_req_item.msg_list_empty
                
        
        response.view = "list.html"
        response.s3.no_formats = True
        
                
        return output

    s3xrc.model.set_method(module, resourcename,
                           method = "check", action=s3_req_check )
    #==========================================================================
    if deployment_settings.has_module("inv"):
        #======================================================================
        # Request Items

        resourcename = "req_item"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                req_id(),
                                item_id(),
                                item_pack_id(),
                                Field( "quantity",
                                       "double",
                                       notnull = True),
                                Field( "quantity_commit",
                                       "double",
                                       default = 0,
                                       writable = False),
                                Field( "quantity_transit",
                                       "double",
                                       default = 0,
                                       writable = False),
                                Field( "quantity_fulfil",
                                       "double",
                                       default = 0,
                                       writable = False),
                                comments(),
                                migrate=migrate, *s3_meta_fields())

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

        # ---------------------------------------------------------------------
        def shn_req_quantity_represent(quantity, type):
            if quantity:
                return TAG[""]( quantity,
                                A(DIV(_class = "quantity %s ajax_more collapsed" % type
                                      ),
                                    _href = "#",
                                  )
                                )
            else:
                return quantity

        table.quantity_commit.represent = lambda quantity_commit: \
                        shn_req_quantity_represent(quantity_commit, "commit")
        table.quantity_fulfil.represent = lambda quantity_fulfil: \
                        shn_req_quantity_represent(quantity_fulfil, "fulfil")
        table.quantity_transit.represent = lambda quantity_transit: \
                        shn_req_quantity_represent(quantity_transit, "transit")

        # ---------------------------------------------------------------------
        # CRUD strings
        ADD_REQUEST_ITEM = T("Add Item to Request")
        LIST_REQUEST_ITEM = T("List Request Items")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_REQUEST_ITEM,
            title_display = T("Request Item Details"),
            title_list = LIST_REQUEST_ITEM,
            title_update = T("Edit Request Item"),
            title_search = T("Search Request Items"),
            subtitle_create = T("Add New Request Item"),
            subtitle_list = T("Requested Items"),
            label_list_button = LIST_REQUEST_ITEM,
            label_create_button = ADD_REQUEST_ITEM,
            label_delete_button = T("Delete Request Item"),
            msg_record_created = T("Request Item added"),
            msg_record_modified = T("Request Item updated"),
            msg_record_deleted = T("Request Item deleted"),
            msg_list_empty = T("No Request Items currently registered"))

        # -----------------------------------------------------------------------------
        # Reusable Field
        def shn_req_item_represent (id):
            query = (db.req_req_item.id == id) & \
                    (db.req_req_item.item_id == db.supply_item.id)
            record = db(query).select( db.supply_item.name,
                                       limitby = (0, 1)).first()
            if record:
                return record.name
            else:
                return None

        # Reusable Field
        req_item_id = S3ReusableField( "req_item_id",
                                            db.req_req_item,
                                            requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                            "req_req_item.id",
                                                                            shn_req_item_represent,
                                                                            orderby="req_req_item.id",
                                                                            sort=True),
                                                                  ),
                                            represent = shn_req_item_represent,
                                            label = T("Request Item"),
                                            comment = DIV( _class="tooltip",
                                                           _title="%s|%s" % (T("Request Item"),
                                                                             T("Select Items from the Request"))),
                                            ondelete = "RESTRICT"
                                            )

        #------------------------------------------------------------------------------
        # Request Items as component of Request
        # Request Items as a component of Items
        s3xrc.model.add_component(module, resourcename,
                                  multiple=True,
                                  joinby=dict(req_req = "req_id",
                                              supply_item = "item_id"))

        #------------------------------------------------------------------------------
        # On Accept to update req_req
        def shn_req_item_onaccept(form):
            """
            Update req_req. commit_status, transit_status, fulfil_status
            None = quantity = 0 for ALL items
            Partial = some items have quantity > 0
            Complete = quantity_x = quantity(requested) for ALL items
            """
            try:
                # Update owned_by_role to the req's owned_by_role
                shn_component_copy_role_func(component_name = "req_req_item",
                                             resource_name = "req_req",
                                             fk = "req_id")(form)
            except:
                # Staff Permissions not active
                pass

            req_id = session.rcvars.req_req

            is_none = dict(commit = True,
                           transit = True,
                           fulfil = True,
                           )

            is_complete = dict(commit = True,
                               transit = True,
                               fulfil = True,
                               )

            #Must check all items in the req
            req_items = db( (db.req_req_item.req_id == req_id) & \
                            (db.req_req_item.deleted == False )
                            ).select(db.req_req_item.quantity,
                                     db.req_req_item.quantity_commit,
                                     db.req_req_item.quantity_transit,
                                     db.req_req_item.quantity_fulfil,
                                     )

            for req_item in req_items:
                for status_type in ["commit","transit", "fulfil"]:
                    if req_item["quantity_%s" % status_type] < req_item.quantity:
                        is_complete[status_type] = False
                    if req_item["quantity_%s" % status_type]:
                        is_none[status_type] = False

            status_update = {}
            for status_type in ["commit","transit", "fulfil"]:
                if is_complete[status_type]:
                    status_update["%s_status" % status_type] = REQ_STATUS_COMPLETE
                elif is_none[status_type]:
                    status_update["%s_status" % status_type] = REQ_STATUS_NONE
                else:
                    status_update["%s_status" % status_type] = REQ_STATUS_PARTIAL
            db.req_req[req_id] = status_update

        s3xrc.model.configure(table, onaccept=shn_req_item_onaccept)

        req_item_inv_item_btn = dict(url = str( URL( r=request,
                                                     c = "req",
                                                     f = "req_item_inv_item",
                                                     args = ["[id]"]
                                                    )
                                                ),
                                     _class = "action-btn",
                                     label = str(T("Find All Matches")), # Change to Fulfil? Match?
                                     )
    #==========================================================================
    # Commitments (Pledges)
    # @ToDo: Update the req_item_id in the commit_item if the req_id of the commit is changed  

    resourcename = "commit"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link( db.org_site, 
                                        writable = True,
                                        readable = True,
                                        label = T("From Inventory"),
                                        represent = shn_site_represent
                                        ),
                            req_id(),
                            Field("date",
                                  "date",
                                  default = request.utcnow,
                                  label = T("Date")),
                            Field("date_available",
                                  "date",
                                  label = T("Date Available")),
                            person_id("committer_id",
                                      default = s3_logged_in_person(),
                                      label = T("Committed By") ),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # -------------------------------------------------------------------------
    # CRUD strings
    ADD_COMMIT = T("Make Commitment")
    LIST_COMMIT = T("List Commitments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_COMMIT,
        title_display = T("Commitment Details"),
        title_list = LIST_COMMIT,
        title_update = T("Edit Commitment"),
        title_search = T("Search Commitments"),
        subtitle_create = ADD_COMMIT,
        subtitle_list = T("Commitments"),
        label_list_button = LIST_COMMIT,
        label_create_button = ADD_COMMIT,
        label_delete_button = T("Delete Commitment"),
        msg_record_created = T("Commitment Added"),
        msg_record_modified = T("Commitment Updated"),
        msg_record_deleted = T("Commitment Canceled"),
        msg_list_empty = T("No Commitments"))

    # -----------------------------------------------------------------------------
    def shn_commit_represent(id):
        if id:
            r = db(db.req_commit.id == id).select(db.req_commit.date,
                                                   db.req_commit.site_id,
                                                   limitby=(0, 1)).first()
            return "%s - %s" % \
                    ( shn_site_represent(r.site_id),
                      r.date
                     )
        else:
            return NONE

    # -----------------------------------------------------------------------------
    # Reusable Field
    commit_id = S3ReusableField("commit_id", db.req_commit, sortby="date",
                                  requires = IS_NULL_OR( \
                                                 IS_ONE_OF(db,
                                                           "req_commit.id",
                                                           shn_commit_represent,
                                                           orderby="req_commit.date",
                                                           sort=True)),
                                  represent = shn_commit_represent,
                                  label = T("Commitment"),
                                  ondelete = "RESTRICT"
                                  )

    #------------------------------------------------------------------------------
    # Commitment as a component of Sites
    s3xrc.model.add_component(module,
                              resourcename,
                              multiple = True,
                              joinby = super_key(db.org_site)
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
    
    #==========================================================================
    if deployment_settings.has_module("inv"):
        #======================================================================
        # Commitment Items

        #----------------------------------------------------------------------
        # Redirect to the Items tabs after creation
        # @ToDo: Move this to the controller & make it depend on the type of Request
        s3xrc.model.configure(table,
                              create_next = URL(r=request, c="req", f="commit",
                                                args=["[id]", "commit_item"]))

        #----------------------------------------------------------------------
        resourcename = "commit_item"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                commit_id(),
                                #item_id(),
                                req_item_id(),
                                item_pack_id(),
                                Field("quantity",
                                      "double",
                                      notnull = True),
                                comments(),
                                migrate=migrate, *s3_meta_fields())

        # pack_quantity virtual field
        table.virtualfields.append(item_pack_virtualfields(tablename = tablename))

        # CRUD strings
        ADD_COMMIT_ITEM = T("Commitment Item")
        LIST_COMMIT_ITEM = T("List Commitment Items")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_COMMIT_ITEM,
            title_display = T("Commitment Item Details"),
            title_list = LIST_COMMIT_ITEM,
            title_update = T("Edit Commitment Item"),
            title_search = T("Search Commitment Items"),
            subtitle_create = T("Add New Commitment Item"),
            subtitle_list = T("Commitment Items"),
            label_list_button = LIST_COMMIT_ITEM,
            label_create_button = ADD_COMMIT_ITEM,
            label_delete_button = T("Delete Commitment Item"),
            msg_record_created = T("Commitment Item added"),
            msg_record_modified = T("Commitment Item updated"),
            msg_record_deleted = T("Commitment Item deleted"),
            msg_list_empty = T("No Commitment Items currently registered"))

        #----------------------------------------------------------------------
        # Commitment Items as component of Commitment
        s3xrc.model.add_component(module, resourcename,
                                  multiple=True,
                                  joinby=dict( req_commit = "commit_id" )
                                  )

        #----------------------------------------------------------------------
        def shn_commit_item_onaccept(form):
             # Update owned_by_role to the commit's owned_by_role
            shn_component_copy_role_func(component_name = "req_commit_item",
                                         resource_name = "req_commit",
                                         fk = "commit_id")(form)

            # try to get req_item_id from the form
            req_item_id = 0
            if form:
                req_item_id = form.vars.get("req_item_id")
            if not req_item_id:
                commit_item_id = session.rcvars.req_commit_item
                r_commit_item = db.req_commit_item[commit_item_id]

                req_item_id = r_commit_item.req_item_id

            commit_items =  db( (db.req_commit_item.req_item_id == req_item_id) & \
                                (db.req_commit_item.deleted == False)
                                ).select(db.req_commit_item.quantity ,
                                         db.req_commit_item.item_pack_id
                                         )
            quantity_commit = 0
            for commit_item in commit_items:
                quantity_commit += commit_item.quantity * commit_item.pack_quantity

            r_req_item = db.req_req_item[req_item_id]
            quantity_commit = quantity_commit / r_req_item.pack_quantity
            db.req_req_item[req_item_id] = dict(quantity_commit = quantity_commit)

            #Update status_commit of the req record
            session.rcvars.req_req_item = r_req_item.id
            shn_req_item_onaccept(None)


        s3xrc.model.configure(table, onaccept = shn_commit_item_onaccept )
        
# END =========================================================================
