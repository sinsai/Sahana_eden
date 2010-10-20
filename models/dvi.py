# -*- coding: utf-8 -*-

""" DVI - Management of Dead Bodies and Disaster Victim Identification

    @author: khushbu
    @author: nursix

"""

module = "dvi"
if deployment_settings.has_module(module):

    # -----------------------------------------------------------------------------
    # Option fields
    #
    dvi_task_status_opts = {
        1:T("New"),
        2:T("Assigned"),
        3:T("In Progress"),
        4:T("Completed"),
        5:T("Not Applicable"),
        6:T("Not Possible")
    }

    dvi_task_status = S3ReusableField("opt_dvi_task_status","integer",
                            requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                            default = 1,
                            label = T("Task Status"),
                            represent = lambda opt: \
                                        dvi_task_status_opts.get(opt, UNKNOWN_OPT))


    # -----------------------------------------------------------------------------
    # Recovery Request
    #
    resource = "recreq"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("date", "datetime"),
                            Field("site_id", length=64),
                            location_id(),
                            Field("location_details"),
                            person_id(), # Finder
                            Field("description"),
                            Field("bodies_est", "integer"), # Number of bodies found
                            dvi_task_status(),
                            Field("bodies_rec", "integer"), # Number of bodies recovered
                            migrate=migrate, *s3_meta_fields())


    # Settings and Restrictions
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)

    table.date.label = T("Date/Time of Find")
    table.date.comment = SPAN("*", _class="req")
    table.date.default = request.utcnow
    table.date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                          allow_future=False)
    table.date.represent = lambda value: shn_as_local_time(value)

    table.site_id.label = T("Site ID")
    #table.site_id.requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, table.site_id))

    table.location_id.label = T("Location")
    table.person_id.label = T("Finder")

    table.bodies_est.label = T("Bodies found")
    table.bodies_est.comment = SPAN("*", _class="req")
    table.bodies_est.requires = IS_INT_IN_RANGE(1, 99999)
    table.bodies_est.default = 0

    table.bodies_rec.label = T("Bodies recovered")
    table.bodies_rec.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.bodies_rec.default = 0

    table.opt_dvi_task_status.label = T("Task status")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Body Recovery Request"),
        title_display = T("Request Details"),
        title_list = T("Body Recovery Requests"),
        title_update = T("Update Request"),
        title_search = T("Search Request"),
        subtitle_create = T("Add New Request"),
        subtitle_list = T("List of Requests"),
        label_list_button = T("List of Requests"),
        label_create_button = T("Add Request"),
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Recovery Request added"),
        msg_record_modified = T("Recovery Request updated"),
        msg_record_deleted = T("Recovery Request deleted"),
        msg_list_empty = T("No requests found"))


    dvi_recreq_id = S3ReusableField("dvi_recreq_id", table,
                                    requires = IS_NULL_OR(IS_ONE_OF(db,
                                               "dvi_recreq.id",
                                               "[%(site_id)s] %(date)s: %(bodies_est)s bodies")),
                                    represent = lambda id: id,
                                    ondelete = "RESTRICT")


    s3xrc.model.configure(table,
                          list_fields = ["id",
                                         "date",
                                         "site_id",
                                         "location_id",
                                         "location_details",
                                         #"description",
                                         "bodies_est",
                                         "bodies_rec",
                                         "opt_dvi_task_status"])

    #
    # Body ------------------------------------------------------------------------
    #
    resource = "body"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            pe_id(),
                            pe_label(),
                            dvi_recreq_id(),
                            Field("date_of_recovery", "datetime"),
                            location_id(),
                            Field("recovery_details","text"),
                            Field("incomplete","boolean"),
                            Field("major_outward_damage","boolean"),
                            Field("burned_or_charred","boolean"),
                            Field("decomposed","boolean"),
                            pr_gender(),
                            pr_age_group(),
                            migrate=migrate, *s3_meta_fields())

    table.pe_label.comment = SPAN("*", _class="req")
    table.pe_label.requires = [IS_NOT_EMPTY(error_message=T("Enter a unique label!")),
                               IS_NOT_IN_DB(db, "dvi_body.pe_label")]

    table.date_of_recovery.default = request.utcnow
    table.date_of_recovery.comment = SPAN("*", _class="req")
    table.date_of_recovery.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                                      allow_future=False)
    table.date_of_recovery.represent = lambda value: shn_as_local_time(value)

    # Labels
    table.dvi_recreq_id.label = T("Recovery Request")
    table.gender.label=T("Apparent Gender")
    table.age_group.label=T("Apparent Age")
    table.location_id.label=T("Place of Recovery")

    table.incomplete.label = T("Incomplete")
    table.major_outward_damage.label = T("Major outward damage")
    table.burned_or_charred.label = T("Burned/charred")
    table.decomposed.label = T("Decomposed")

    # Representations
    table.major_outward_damage.represent = lambda opt: (opt and ["yes"] or [""])[0]
    table.burned_or_charred.represent =  lambda opt: (opt and ["yes"] or [""])[0]
    table.decomposed.represent =  lambda opt: (opt and ["yes"] or [""])[0]
    table.incomplete.represent =  lambda opt: (opt and ["yes"] or [""])[0]

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Recovery Report"),
        title_display = T("Dead Body Details"),
        title_list = T("Body Recovery Reports"),
        title_update = T("Edit Recovery Details"),
        title_search = T("Find Recovery Report"),
        subtitle_create = T("Add New Report"),
        subtitle_list = T("List of Reports"),
        label_list_button = T("List Reports"),
        label_create_button = T("Add Recovery Report"),
        label_delete_button = T("Delete Recovery Report"),
        msg_record_created = T("Recovery report added"),
        msg_record_modified = T("Recovery report updated"),
        msg_record_deleted = T("Recovery report deleted"),
        msg_list_empty = T("No recovery reports available"))

    s3xrc.model.configure(table,
                          onaccept=lambda form: shn_pentity_onaccept(form, table=db.dvi_body),
                          delete_onaccept=lambda form: shn_pentity_ondelete(form),
                          list_fields=["id",
                                       "pe_label",
                                       "gender",
                                       "age_group",
                                       "incomplete",
                                       "date_of_recovery",
                                       "location_id"])

    #
    # Checklist of operations -----------------------------------------------------
    #
    resource = "checklist"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    pe_id(),
                    Field("personal_effects","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Inventory of Effects"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("body_radiology","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Radiology"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("fingerprints","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Fingerprinting"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("anthropology","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Anthropolgy"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("pathology","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Pathology"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("embalming","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Embalming"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("dna","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("DNA Profiling"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    Field("dental","integer",
                        requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                        default = 1,
                        label = T("Dental Examination"),
                        represent = lambda opt: dvi_task_status_opts.get(opt, T("not specified"))),
                    migrate=migrate, *s3_meta_fields())

    # Setting and restrictions

    # CRUD Strings
    CREATE_CHECKLIST = T("Create Checklist")
    s3.crud_strings[tablename] = Storage(
        title_create = CREATE_CHECKLIST,
        title_display = T("Checklist of Operations"),
        title_list = T("List Checklists"),
        title_update = T("Update Task Status"),
        title_search = T("Search Checklists"),
        subtitle_create = T("New Checklist"),
        subtitle_list = T("Checklist of Operations"),
        label_list_button = T("Show Checklist"),
        label_create_button = CREATE_CHECKLIST,
        msg_record_created = T("Checklist created"),
        msg_record_modified = T("Checklist updated"),
        msg_record_deleted = T("Checklist deleted"),
        msg_list_empty = T("No Checklist available"))

    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = "pe_id")

    s3xrc.model.configure(table, list_fields = ["id"])

    #
    # Personal Effects ------------------------------------------------------------------------
    #
    resource = "effects"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                    pe_id(),
    #                person_id(),
                    Field("clothing", "text"),    #TODO: elaborate
                    Field("jewellery", "text"),   #TODO: elaborate
                    Field("footwear", "text"),    #TODO: elaborate
                    Field("watch", "text"),       #TODO: elaborate
                    Field("other", "text"),
                    migrate=migrate, *s3_meta_fields())

    # Settings and Restrictions

    # Labels
    #table.person_id.label = T("Reporter")

    # CRUD Strings
    ADD_PERSONAL_EFFECTS = T("Add Personal Effects")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_PERSONAL_EFFECTS,
        title_display = T("Personal Effects Details"),
        title_list = T("List Personal Effects"),
        title_update = T("Edit Personal Effects Details"),
        title_search = T("Search Personal Effects"),
        subtitle_create = T("Add New Entry"),
        subtitle_list = T("Personal Effects"),
        label_list_button = T("List Records"),
        label_create_button = ADD_PERSONAL_EFFECTS,
        msg_record_created = T("Record added"),
        msg_record_modified = T("Record updated"),
        msg_record_deleted = T("Record deleted"),
        msg_list_empty = T("No Details currently registered"))

    # Joined Resource
    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = "pe_id")

    s3xrc.model.configure(table, list_fields = ["id"])

    #
    # Identification --------------------------------------------------------------
    #
    dvi_id_status_opts = {
        1:T("Unidentified"),
        2:T("Preliminary"),
        3:T("Confirmed"),
    }

    dvi_id_status = S3ReusableField("opt_dvi_id_status","integer",
                        requires = IS_IN_SET(dvi_id_status_opts, zero=None),
                        default = 1,
                        label = T("Identification Status"),
                        represent = lambda opt: dvi_id_status_opts.get(opt, UNKNOWN_OPT))


    dvi_id_method_opts = {
        1:T("Visual Recognition"),
        2:T("Physical Description"),
        3:T("Fingerprints"),
        4:T("Dental Profile"),
        5:T("DNA Profile"),
        6:T("Combined Method"),
        99:T("Other Evidence")
    }

    dvi_id_method = S3ReusableField("opt_dvi_id_method","integer",
                        requires = IS_IN_SET(dvi_id_method_opts, zero=None),
                        default = 99,
                        label = T("Method used"),
                        represent = lambda opt: dvi_id_method_opts.get(opt, UNKNOWN_OPT))


    resource = "identification"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            pe_id(),
                            Field("identified_by", db.pr_person),  # Person identifying the body
                            Field("reported_by", db.pr_person),    # Person reporting
                            dvi_id_status(),                       # Identity status
                            dvi_id_method(),                       # Method used
                            Field("identity", db.pr_person),       # Identity of the body
                            Field("presence", db.pr_presence),     # Related presence record of the identified person
                            Field("comment", "text"),              # Comment (optional)
                            migrate=migrate, *s3_meta_fields())


    # Settings and Restrictions
    table.identified_by.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name"))
    table.identified_by.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
    table.identified_by.comment = shn_person_id_comment
    table.identified_by.ondelete = "RESTRICT"

    table.reported_by.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name"))
    table.reported_by.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
    table.reported_by.comment = shn_person_id_comment
    table.reported_by.ondelete = "RESTRICT"

    table.identity.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent, orderby="pr_person.first_name"))
    table.identity.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
    table.identity.comment = shn_person_id_comment
    table.identity.ondelete = "RESTRICT"

    table.presence.readable = None
    table.presence.writable = None


    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Identification Report"),
        title_display = T("Identification Report"),
        title_list = T("List Reports"),
        title_update = T("Edit Identification Report"),
        title_search = T("Search Report"),
        subtitle_create = T("Add New Report"),
        subtitle_list = T("Identification Reports"),
        label_list_button = T("List Reports"),
        label_create_button = T("Add Identification Report"),
        msg_record_created = T("Report added"),
        msg_record_modified = T("Report updated"),
        msg_record_deleted = T("Report deleted"),
        msg_list_empty = T("No Identification Report Available"))


    # Identification reports as component of person entities
    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = "pe_id")


    # -----------------------------------------------------------------------------
    def dvi_identification_onvalidation(form):

        """ Remove attached presence records upon identity change """

        table = db.dvi_identification

        record_id = form.vars.id
        identity = form.vars.identity
        if record_id:
            record = db(table.id == record_id).select(table.identity,
                                                      table.presence,
                                                      limitby=(0,1)).first()
            if record:
                if str(identity) != str(record.identity):
                    db(db.pr_presence.id == record.presence).update(deleted=True)
                    vita.presence_accept(record.presence)
        return


    # -----------------------------------------------------------------------------
    def dvi_identification_onaccept(form):

        """ Attach presence record for the identified person """

        table = db.dvi_identification

        if isinstance(form, Row):
            record_id = form.id
        else:
            record_id = form.vars.id

        if record_id:
            record = db(table.id == record_id).select(table.pe_id,
                                                      table.deleted,
                                                      table.identity,
                                                      table.presence,
                                                      table.opt_dvi_id_status,
                                                      limitby=(0,1)).first()

            if not record:
                return

            if record.presence and \
               (record.deleted or record.opt_dvi_id_status != 3):

                # Remove prior attached presence records
                db(db.pr_presence.id == record.presence).update(deleted=True)
                vita.presence_accept(record.presence)
                db(table.id == record_id).update(presence=None)

            elif not record.presence and record.opt_dvi_id_status == 3:

                # Get the identified person:
                person = db(db.pr_person.id == record.identity).select(db.pr_person.pe_id,
                                                                       limitby=(0,1)).first()
                if not person:
                    return

                # Get the recovery location and time of the body
                location_id = None
                body = db(db.dvi_body.pe_id == record.pe_id).select(db.dvi_body.location_id,
                                                                    db.dvi_body.date_of_recovery,
                                                                    limitby=(0,1)).first()
                if body:
                    location_id = body.location_id

                # Get the current user
                reporter = None
                query = db.pr_person.uuid == session.auth.user.person_uuid
                user = db(query).select(db.pr_person.id, limitby=(0,1)).first()
                if user:
                    report_id = user.id

                # Insert new presence record
                presence_id = db.pr_presence.insert(
                    pe_id = person.pe_id,
                    reporter = reporter,
                    datetime = request.utcnow,
                    location_id = location_id,
                    presence_condition = vita.DECEASED,
                )
                if presence_id:
                    db(table.id == record_id).update(presence=presence_id)
                    vita.presence_accept(presence_id)

    # -----------------------------------------------------------------------------
    s3xrc.model.configure(table,
        onvalidation = lambda form: dvi_identification_onvalidation(form),
        onaccept = lambda form: dvi_identification_onaccept(form),
        delete_onaccept = lambda row: dvi_identification_onaccept(row),
        list_fields = ["id"])


    # -----------------------------------------------------------------------------
    #
    def shn_dvi_rheader(jr, tabs=[]):

        """ Page header for component pages """

        if jr.name == "body":
            if jr.representation == "html":
                _next = jr.here()
                _same = jr.same()

                rheader_tabs = shn_rheader_tabs(jr, tabs)

                body = jr.record
                if body:
                    rheader = DIV(TABLE(

                        TR(TH("%s: " % T("ID Label")),
                           "%(pe_label)s" % body,
                           TH(""),
                           ""),

                        TR(TH("%s: " % T("Gender")),
                           "%s" % pr_gender_opts[body.gender],
                           TH(""),
                           ""),

                        TR(TH("%s: " % T("Age Group")),
                           "%s" % pr_age_group_opts[body.age_group],
                           TH(""),
                           ""),

                        ), rheader_tabs
                    )
                    return rheader

        return None


    # -----------------------------------------------------------------------------
    #
    def shn_dvi_body_search_simple(r, **attr):

        """ Simple search form for bodies (recovery reports) """

        resource = r.resource
        table = resource.table

        r.id = None

        # Check permission
        if not shn_has_permission("read", table):
            r.unauthorised()

        if r.representation == "html":

            # Check for redirection
            next = r.request.vars.get("_next", None)
            if not next:
                next = URL(r=request, f="body", args="[id]")

            # Select form
            form = FORM(TABLE(
                    TR("%s: " % T("ID Tag"),
                    INPUT(_type="text", _name="label", _size="40"),
                    DIV(DIV(_class="tooltip",
                            _title=T("ID Tag") + "|" + T("To search for a body, enter the ID label of the body. You may use % as wildcard. Press 'Search' without input to list all bodies.")))),
                    TR("", INPUT(_type="submit", _value=T("Search")))))

            output = dict(form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                if form.vars.label == "":
                    form.vars.label = "%"

                # Search
                results = s3xrc.search_simple(table,
                            fields = ["pe_label",],
                            label = form.vars.label)

                # Get the results
                if results:
                    resource.build_query(id=results)
                    report = resource.crud(r, method="list", **attr)["items"]
                    r.next = None
                else:
                    report = T("No matching records found.")

                output.update(items=report)

            # Title and subtitle
            title = T("Search Recovery Reports")
            subtitle = T("Matching Records")

            # Add-button
            label_create_button = shn_get_crud_string("dvi_body", "label_create_button")
            add_btn = A(label_create_button, _class="action-btn",
                        _href=URL(r=request, f="body", args="create"))

            output.update(title=title, subtitle=subtitle, add_btn=add_btn)
            response.view = "search_simple.html"
            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, "body", method="search_simple", action=shn_dvi_body_search_simple )

    # -----------------------------------------------------------------------------
