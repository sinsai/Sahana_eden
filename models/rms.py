# -*- coding: utf-8 -*-

"""
    Request Management System

    @ ToDo:
        Clean this up so that it is clearly different from the Req module
        - that handles Item Requests & this handles other Requests

        Restore Pledges: As a component of Requests

        Remove dependency on CR/HMS by removing FK & 1 of:
            link via site_id (preferred? Although the Inv req has got that component tab already :/)
            using a link table
            linking via Location
"""

module = "rms"
if deployment_settings.has_module(module):
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

    resourcename = "req"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.sit_situation),   # Why is it a Situation?
                            Field("datetime", "datetime"),  # 'timestamp' is a reserved word in Postgres
                            location_id(),
                            person_id(),
                            #hospital_id(),      # @ToDo: Remove FK
                            #shelter_id(),       # @ToDo: Remove FK
                            organisation_id(),  # @ToDo: Remove?
                            Field("type", "integer"),
                            Field("priority", "integer"),
                            Field("message", "text"),
                            Field("verified", "boolean"),
                            Field("verified_details"),
                            Field("actionable", "boolean"),
                            Field("actioned", "boolean"),
                            Field("actioned_details"),
                            Field("pledge_status", "string"),
                            #Field("source_type", "integer"),
                            migrate=migrate, *s3_meta_fields())


    # Make Person Mandatory
    table.person_id.requires = IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name")
    table.person_id.label = T("Requestor")

    table.datetime.requires = IS_DATETIME()
    table.datetime.label = T("Date & Time")

    table.message.requires = IS_NOT_EMPTY()

    # Hide fields from user:
    table.verified.readable = table.verified.writable = False
    table.verified_details.readable = table.verified_details.writable = False
    table.actionable.readable = table.actionable.writable = False
    table.actioned.readable = table.actioned.writable = False
    table.actioned_details.readable = table.actioned_details.writable = False

    # Set default values
    table.actionable.default = 1
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

    def rms_req_onaccept(form):
        # Send a Message to the Inventory Managers when a new Request comes in
        # Q: How to tell whether this is a new request?

        # Hack: Send to all people in the Organisation
        try:
            org_pe_id = db(db.org_organisation.id == form.vars.organisation_id).select(db.org_organisation.pe_id,
                                                                                       limitby=(0, 1)).first().pe_id

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

    rms_req_search = s3base.S3Search(
                            name="rms_req_search_simple",
                            label=T("Text in Message"),
                            comment=T("To search for a request, enter some of the text that you are looking for. You may use % as wildcard. Press 'Search' without input to list all requests."),
                            field=["message"]
                     )

    s3xrc.model.configure(table,
                          mark_required=["type"],
                          super_entity=db.sit_situation,
                          onaccept = lambda form: rms_req_onaccept(form),
                          search_method=rms_req_search
                          )

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
                    represent = lambda id: (id and [db(db.rms_req.id == id).select(db.rms_req.message,
                                                                                   limitby=(0, 1)).first().message] or ["None"])[0],
                    label = T("Request"),
                    ondelete = "RESTRICT"
                    )

    #==========================================================================
    # Create the table for request_detail for requests with arbitrary keys
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
    # Details as component of Requests
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(rms_req="request_id"))

# END =========================================================================