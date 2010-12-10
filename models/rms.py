# -*- coding: utf-8 -*-

"""
    Request Management System
"""

module = "rms"
if deployment_settings.has_module(module):
    # NB Current this module depends on HMS, CR & Project

    # -------------------------------
    # Load lists/dictionaries for drop down menus

    rms_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }

    rms_status_opts = {
        1:T("Pledged"),
        2:T("In Transit"),
        3:T("Delivered"),
        4:T("Received"),
        5:T("Cancelled")
        }

    rms_type_opts = {
        1:T("Items"),
        2:T("Find"),
        3:T("Shelter"),
        4:T("Report")
        }

    # -----------------
    # Requests table

    #def shn_req_aid_represent(id):
        #return  A(T("Make Pledge"), _href=URL(r=request, f="req", args=[id, "pledge"]))

    # 2010-10-31 Michael Howden: The request resource is undergoing a significant re-design.
    # A large number of fields are being commented out. Eventually they should be removed
    # (Once the re-design is accepted)

    resourcename = "req"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.sit_situation),
                            Field("datetime", "datetime"),  # 'timestamp' is a reserved word in Postgres
                            location_id(),
                            person_id("requestor_person_id"),
                            hospital_id(),    # @ToDo: Check if the HMS module is enabled for adding FK: check CR for an example
                            shelter_id(),     # @ToDo: Check if the CR module is enabled for adding FK: check CR for an example
                            organisation_id(),
                            inventory_store_id("from_inventory_store_id"),
                            Field("type", "integer"),
                            Field("priority", "integer"),
                            Field("message", "text"),
                            activity_id(),     # @ToDo: Check if the Project module is enabled for adding FK: check CR for an example
                            #Field("verified", "boolean"),
                            #Field("verified_details"),
                            #Field("actionable", "boolean"),
                            #Field("actioned", "boolean"),
                            #Field("actioned_details"),
                            #Field("pledge_status", "string"),
                            document_id(),
                            migrate=migrate, *s3_meta_fields())


    # Make Person Mandatory
    table.requestor_person_id.requires = IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name")
    table.requestor_person_id.label = T("Requestor")

    table.datetime.requires = IS_DATETIME()
    table.datetime.label = T("Date & Time")

    table.from_inventory_store_id.label = T("From Warehouse")

    #This is only set by rms/store_for_req
    #table.from_inventory_store_id.readable = table.from_inventory_store_id.writable = False

    table.message.requires = IS_NOT_EMPTY()

    # Hide fields from user:
    #table.source_id.readable = table.source_id.writable = False
    #table.verified.readable = table.verified.writable = False
    #table.verified_details.readable = table.verified_details.writable = False
    #table.actionable.readable = table.actionable.writable = False
    #table.actioned.readable = table.actioned.writable = False
    #table.actioned_details.readable = table.actioned_details.writable = False

    # Set default values
    #table.actionable.default = 1
    #table.source_type.default = 1

    table.priority.requires = IS_NULL_OR(IS_IN_SET(rms_priority_opts))
    table.priority.represent = lambda id: (
        [id and
            DIV(IMG(_src="/%s/static/img/priority/priority_%d.gif" % (request.application,id,), _height=12)) or
            DIV(IMG(_src="/%s/static/img/priority/priority_4.gif" % request.application), _height=12)
        ][0])
    table.priority.label = T("Priority Level")

    table.type.requires = IS_IN_SET(rms_type_opts)
    table.type.represent = lambda type: type and rms_type_opts[type]
    table.type.label = T("Request Type")

    #rms_req_source_type = { 1 : "Manual",
    #                        2 : "SMS",
    #                        3 : "Tweet" }

    #table.source_type.readable = table.source_type.writable = False
    #table.source_type.requires = IS_NULL_OR(IS_IN_SET(rms_req_source_type))
    #table.source_type.represent = lambda stype: stype and rms_req_source_type[stype]
    #table.source_type.label = T("Source Type")

    # CRUD strings
    ADD_REQUEST = T("Add Request")
    LIST_REQUESTS = T("List Requests")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REQUEST,
        title_display = T("Request Details"),
        title_list = LIST_REQUESTS,
        title_update = T("Edit Request"),
        title_search = T("Search Requests"),
        subtitle_create = T("Add New Request"),
        subtitle_list = T("Requests"),
        label_list_button = LIST_REQUESTS,
        label_create_button = ADD_REQUEST,
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Request added"),
        msg_record_modified = T("Request updated"),
        msg_record_deleted = T("Request deleted"),
        msg_list_empty = T("No Requests have been made yet"),
        msg_no_match = T("No Requests match this criteria"))

    # Reusable Field
    request_id = S3ReusableField("request_id", db.rms_req, sortby="message",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "rms_req.id", "%(message)s")),
                    represent = lambda id: (id and [db(db.rms_req.id == id).select(limitby=(0, 1)).first().message] or ["None"])[0],
                    label = T("Request"),
                    comment = DIV(A(ADD_REQUEST,
                                    _class="colorbox",
                                    _href=URL(r=request, c="rms", f="req", args="create", vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_REQUEST
                                    ),
                                  DIV( _class="tooltip",
                                       _title=T("Add Request") + "|" + T("The Request this record is associated with.")
                                       )
                                  ),
                    ondelete = "RESTRICT"
                    )

    def rms_req_onaccept(form):
        # Send a Message to the Inventory Managers when a new Request comes in
        # Q: How to tell whether this is a new request?

        # Hack: Send to all people in the Organisation
        try:
            org_pe_id = db(db.org_organisation.id == form.vars.organisation_id).select(db.org_organisation.pe_id, limitby=(0, 1)).first().pe_id

            message = T("Sahana: new request has been made. Please login to see if you can fulfil the request.")

            msg.send_sms_by_pe_id(self,
                                  org_pe_id,
                                  message=message,
                                  sender_pe_id="",
                                  sender="",
                                  fromaddress="",
                                  system_generated=True)
        except:
            pass

    s3xrc.model.configure(table,
                          mark_required=["type"],
                          super_entity=db.sit_situation,
                          onaccept = lambda form: rms_req_onaccept(form),
                          )

    # rms_req as component of doc_documents, shelters, hospitals, activities and inventory store
    s3xrc.model.add_component(module,
                              resourcename,
                              multiple=True,
                              joinby=dict(doc_document="document_id",
                                          cr_shelter="shelter_id",
                                          hms_hospital="hospital_id",
                                          project_activity = "activity_id",
                                          inventory_store = "from_inventory_store_id",
                                          )
                              )

    # --------------------------------------------------------------------
    def shn_rms_get_req(label, fields=None, filterby=None):
        """
            Finds a request by Message string
        """

        if fields and isinstance(fields, (list,tuple)):
            search_fields = []
            for f in fields:
                if db.rms_req.has_key(f):     # TODO: check for field type?
                    search_fields.append(f)
            if not len(search_fields):
                # Error: none of the specified search fields exists
                return None
        else:
            # No search fields specified at all => fallback
            search_fields = ["message"]

        if label and isinstance(label, str):
            labels = label.split()
            results = []
            query = None
            # TODO: make a more sophisticated search function (Levenshtein?)
            for l in labels:

                # append wildcards
                wc = "%"
                _l = "%s%s%s" % (wc, l, wc)

                # We want to do case-insensitive searches
                # (default anyway on MySQL/SQLite, but not PostgreSQL)
                _l = _l.lower()

                # build query
                for f in search_fields:
                    if query:
                        query = (db.rms_req[f].lower().like(_l)) | query
                    else:
                        query = (db.rms_req[f].lower().like(_l))

                # undeleted records only
                query = (db.rms_req.deleted == False) & (query)
                # restrict to prior results (AND)
                if len(results):
                    query = (db.rms_req.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)
                records = db(query).select(db.rms_req.id)
                # rebuild result list
                results = [r.id for r in records]
                # any results left?
                if not len(results):
                    return None
            return results
        else:
            # no label given or wrong parameter type
            return None

    # ---------------------------------------------------------------------
    def shn_rms_req_search_simple(xrequest, **attr):
        """
            Simple search form for requests
        """

        if attr is None:
            attr = {}

        if not shn_has_permission("read", db.rms_req):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_simple", vars=request.vars)}))

        if xrequest.representation=="html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = str.lower(URL(r=request, f="req", args="[id]"))

            # Custom view
            response.view = "%s/req_search.html" % xrequest.prefix

            # Title and subtitle
            title = T("Search for a Request")
            subtitle = T("Matching Records")

            # Select form
            form = FORM(TABLE(
                    TR(T("Text in Message: "),
                    INPUT(_type="text", _name="label", _size="40"),
                    DIV( _class="tooltip", _title=T("Text in Message") + "|" + T("To search for a request, enter some of the text that you are looking for. You may use % as wildcard. Press 'Search' without input to list all requests."))),
                    TR("", INPUT(_type="submit", _value=T("Search")))
                    ))

            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                if form.vars.label == "":
                    form.vars.label = "%"

                results = shn_rms_get_req(form.vars.label)

                if results and len(results):
                    rows = db(db.rms_req.id.belongs(results)).select()
                else:
                    rows = None

                # Build table rows from matching records
                if rows:
                    records = []
                    for row in rows:
                        href = next.replace("%5bid%5d", "%s" % row.id)
                        records.append(TR(
                            row.completion_status,
                            row.message,
                            row.datetime,
                            row.location_id and shn_gis_location_represent(row.location_id) or "unknown",
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("Completion Status"),
                        TH("Message"),
                        TH("Time"),
                        TH("Location"),
                        )),
                        TBODY(records), _id="list", _class="display"))
                else:
                    items = T("None")

            try:
                label_create_button = s3.crud_strings["rms_req"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button

            add_btn = A(label_create_button, _href=URL(r=request, f="req", args="create"), _class="action-btn")

            output.update(dict(items=items, add_btn=add_btn))
            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, resourcename, method="search_simple", action=shn_rms_req_search_simple )

    #==============================================================================
    # Request Item
    #
    resourcename = "ritem"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            request_id(),
                            item_id(empty=False),
                            Field("quantity", "double"),
                            comments(),
                            migrate=migrate, *s3_meta_fields())
    # CRUD strings
    ADD_REQUEST_ITEM = T("Add Request Item")
    LIST_REQUEST_ITEMS = T("List Request Items")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REQUEST_ITEM,
        title_display = T("Request Item Details"),
        title_list = LIST_REQUEST_ITEMS,
        title_update = T("Edit Request Item"),
        title_search = T("Search Request Items"),
        subtitle_create = T("Add New Request Item"),
        subtitle_list = T("Request Items"),
        label_list_button = LIST_REQUEST_ITEMS,
        label_create_button = ADD_REQUEST_ITEM,
        label_delete_button = T("Delete Request Item"),
        msg_record_created = T("Request Item added"),
        msg_record_modified = T("Request Item updated"),
        msg_record_deleted = T("Request Item deleted"),
        msg_list_empty = T("No Items currently requested"))

    table.item_id.requires = IS_ONE_OF(db, "supply_item.id", "%(name)s") 
    #table.quantity.requires = IS_NOT_EMPTY() 

    # Items as component of Locations
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(rms_req="request_id",
                                          supply_item="item_id"))

    #==============================================================================
    # Create the table for request_detail for requests with arbitrary keys
    # (This is probably redundant)
    resourcename = "req_detail"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            request_id(),
                            Field("request_key", "string"),
                            Field("value", "string"),
                            migrate=migrate, *s3_meta_fields())


    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(rms_req="request_id"))

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "request_id",
                                       "request_key",
                                       "value"],
                          main="request_key", extra="value")

    # Make some fields invisible:
    table.request_id.readable = table.request_id.writable = False

    # make all fields read only
    #table.tweet_req_id.readable = table.tweet_req_id.writable = False
    #table.request_key.writable = False
    #table.value.writable = False

    ADD_REQUEST_DETAIL = T("Add Request Detail")
    s3.crud_strings[tablename] = Storage(
                                         title_create        = ADD_REQUEST_DETAIL,
                                         title_display       = "Request Detail",
                                         title_list          = "List Request Details",
                                         title_update        = "Edit Request Details",
                                         title_search        = "Search Request Details",
                                         subtitle_create     = "Add New Request Detail",
                                         subtitle_list       = "Request Details",
                                         label_list_button   = "List Request Details",
                                         label_create_button = ADD_REQUEST_DETAIL,
                                         msg_record_created  = "Request detail added",
                                         msg_record_modified = "Request detail updated",
                                         msg_record_deleted  = "Request detail deleted",
                                         msg_list_empty      = "No request details currently available"
                                        )
