# -*- coding: utf-8 -*-

"""
    DVI - Management of Dead Bodies and Disaster Victim Identification

    @author: khushbu
    @author: nursix
"""

module = "dvi"
if deployment_settings.has_module(module):

    # Settings
    resource = "setting"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("audit_read", "boolean"),
                            Field("audit_write", "boolean"),
                            migrate=migrate)

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

    opt_dvi_task_status = db.Table(None, "opt_dvi_task_status",
                                   Field("opt_dvi_task_status","integer",
                                   requires = IS_IN_SET(dvi_task_status_opts, zero=None),
                                   default = 1,
                                   label = T("Task Status"),
                                   represent = lambda opt: \
                                               dvi_task_status_opts.get(opt, UNKNOWN_OPT)))

    # -----------------------------------------------------------------------------
    # Recovery Request
    #
    resource = "recreq"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                            Field("date", "datetime"),
                            Field("site_id", length=64),
                            location_id,
                            Field("location_details"),
                            person_id, # Finder
                            Field("description"),
                            Field("bodies_est", "integer"), # Number of bodies found
                            opt_dvi_task_status,
                            Field("bodies_rec", "integer"), # Number of bodies recovered
                            migrate=migrate)

    # Settings and Restrictions
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % table)

    table.date.label = T("Date/Time of Find")
    table.date.comment = SPAN("*", _class="req")
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
        title_list = T("List of Requests"),
        title_update = T("Update Request"),
        title_search = T("Search Request"),
        subtitle_create = T("Add New Request"),
        subtitle_list = T("Body Recovery Requests"),
        label_list_button = T("List of Requests"),
        label_create_button = T("Add Request"),
        label_delete_button = T("Delete Request"),
        msg_record_created = T("Recovery Request added"),
        msg_record_modified = T("Recovery Request updated"),
        msg_record_deleted = T("Recovery Request deleted"),
        msg_list_empty = T("No requests currently registered"))

    dvi_recreq_id = db.Table(None, "dvi_recreq_id",
                             Field("dvi_recreq_id", table,
                                   requires = IS_NULL_OR(IS_ONE_OF(db,
                                                  "dvi_recreq.id",
                                                  "[%(site_id)s] %(date)s: %(bodies_est)s bodies")),
                                   represent = lambda id: id,
                                   ondelete = "RESTRICT"))

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
    table = db.define_table(tablename, timestamp, deletion_status, uuidstamp,
                            pr_pe_fieldset,
                            dvi_recreq_id,
                            Field("date_of_recovery", "datetime"),
                            location_id,
                            Field("recovery_details","text"),
                            Field("has_major_outward_damage","boolean"),
                            Field("is_burned_or_charred","boolean"),
                            Field("is_decayed","boolean"),
                            Field("is_incomplete","boolean"),
                            opt_pr_gender,
                            opt_pr_age_group,
                            migrate = migrate)

    # Settings and Restrictions
    #table.pr_pe_parent.readable = True         # not visible in body registration form
    #table.pr_pe_parent.writable = True         # not visible in body registration form
    #table.pr_pe_parent.requires = IS_NULL_OR(IS_ONE_OF(db,"pr_pentity.id",shn_pentity_represent,filterby="opt_pr_entity_type",filter_opts=(3,)))

    table.pr_pe_label.comment = SPAN("*", _class="req")
    table.pr_pe_label.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db, "dvi_body.pr_pe_label")]
    table.date_of_recovery.comment = SPAN("*", _class="req")
    table.date_of_recovery.requires = IS_DATETIME()

    # Labels
    table.dvi_recreq_id.label = T("Recovery Request")
    table.opt_pr_gender.label=T("Apparent Gender")
    table.opt_pr_age_group.label=T("Apparent Age")
    table.location_id.label=T("Place of Recovery")

    # Representations
    table.has_major_outward_damage.represent = lambda opt: (opt and ["yes"] or [""])[0]
    table.is_burned_or_charred.represent =  lambda opt: (opt and ["yes"] or [""])[0]
    table.is_decayed.represent =  lambda opt: (opt and ["yes"] or [""])[0]
    table.is_incomplete.represent =  lambda opt: (opt and ["yes"] or [""])[0]

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
                          onaccept=lambda form: \
                          shn_pentity_onaccept(form, table=db.dvi_body, entity_type=3),
                          delete_onaccept=lambda form: \
                          shn_pentity_ondelete(form),
                          list_fields=["id",
                                       "pr_pe_label",
                                       "opt_pr_gender",
                                       "opt_pr_age_group",
                                       "date_of_recovery",
                                       "location_id"])

    #
    # Checklist of operations -----------------------------------------------------
    #
    resource = "checklist"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    pr_pe_id,
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
                    migrate = migrate)

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

    # Joined Resource
    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = "pr_pe_id",
                              deletable = True,
                              editable = True)

    s3xrc.model.configure(table, list_fields = ["id"])

    #
    # Personal Effects ------------------------------------------------------------------------
    #
    resource = "effects"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    pr_pe_id,
    #                person_id,
                    Field("clothing", "text"),    #TODO: elaborate
                    Field("jewellery", "text"),   #TODO: elaborate
                    Field("footwear", "text"),    #TODO: elaborate
                    Field("watch", "text"),       #TODO: elaborate
                    Field("other", "text"),
                    migrate = migrate)

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
                              joinby = "pr_pe_id",
                              deletable = True,
                              editable = True)

    s3xrc.model.configure(table, list_fields = ["id"])

    #
    # Identification --------------------------------------------------------------
    #
    dvi_id_status_opts = {
        1:T("Unidentified"),
        2:T("Preliminary"),
        3:T("Confirmed"),
        }

    opt_dvi_id_status = db.Table(None, "opt_dvi_id_status",
                        Field("opt_dvi_id_status","integer",
                        requires = IS_IN_SET(dvi_id_status_opts, zero=None),
                        default = 1,
                        label = T("Identification Status"),
                        represent = lambda opt: dvi_id_status_opts.get(opt, UNKNOWN_OPT)))

    dvi_id_method_opts = {
        1:T("Visual Recognition"),
        2:T("Physical Description"),
        3:T("Fingerprints"),
        4:T("Dental Profile"),
        5:T("DNA Profile"),
        6:T("Combined Method"),
        99:T("Other Evidence")
        }

    opt_dvi_id_method = db.Table(None, "opt_dvi_id_method",
                        Field("opt_dvi_id_method","integer",
                        requires = IS_IN_SET(dvi_id_method_opts, zero=None),
                        default = 99,
                        label = T("Method used"),
                        represent = lambda opt: dvi_id_method_opts.get(opt, UNKNOWN_OPT)))

    resource = "identification"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename, timestamp, uuidstamp, deletion_status,
                    pr_pe_id,
                    Field("identified_by", db.pr_person),  # Person identifying the body
                    Field("reported_by", db.pr_person),    # Person reporting
                    opt_dvi_id_status,                     # Identity status
                    opt_dvi_id_method,                     # Method used
                    Field("identity", db.pr_person),       # Identity of the body
                    Field("comment", "text"),              # Comment (optional)
                    migrate = migrate)

    # Settings and Restrictions
    table.identified_by.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent))
    table.identified_by.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
    table.identified_by.comment = shn_person_comment
    table.identified_by.ondelete = "RESTRICT"

    table.reported_by.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent))
    table.reported_by.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
    table.reported_by.comment = shn_person_comment
    table.reported_by.ondelete = "RESTRICT"

    table.identity.requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id", shn_pr_person_represent))
    table.identity.represent = lambda id: (id and [shn_pr_person_represent(id)] or ["None"])[0]
    table.identity.comment = shn_person_comment
    table.identity.ondelete = "RESTRICT"

    # Labels

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

    # Joined Resource
    s3xrc.model.add_component(module, resource,
                              multiple = False,
                              joinby = "pr_pe_id",
                              deletable = True,
                              editable = True)

    s3xrc.model.configure(table, list_fields = ["id"])

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

                        TR(TH(T("ID Label: ")),
                           "%(pr_pe_label)s" % body,
                           TH(""),
                           ""),

                        TR(TH(T("Gender: ")),
                           "%s" % pr_person_gender_opts[body.opt_pr_gender],
                           TH(""),
                           ""),

                        TR(TH(T("Age Group: ")),
                           "%s" % pr_person_age_group_opts[body.opt_pr_age_group],
                           TH(""),
                           ""),

                        ), rheader_tabs
                    )
                    return rheader

        return None

    # -----------------------------------------------------------------------------
    #
    def shn_dvi_get_body_id(label, fields=None, filterby=None):

        """" find IDs for all body records matching a label """

        if fields and isinstance(fields, (list,tuple)):
            search_fields = []
            for f in fields:
                if db.dvi_body.has_key(f):     # TODO: check for field type?
                    search_fields.append(f)
            if not len(search_fields):
                # Error: none of the specified search fields exists
                return None
        else:
            # No search fields specified at all => fallback
            search_fields = ["pr_pe_label"]

        if label and isinstance(label,str):
            labels = label.split()
            results = []
            query = None
            # TODO: make a more sophisticated search function (levenshtein?)
            for l in labels:

                # append wildcards
                wc = "%"
                _l = "%s%s%s" % (wc, l, wc)

                # build query
                for f in search_fields:
                    if query:
                        query = (db.dvi_body[f].like(_l)) | query
                    else:
                        query = (db.dvi_body[f].like(_l))

                # undeleted records only
                query = (db.dvi_body.deleted==False) & (query)
                # restrict to prior results (AND)
                if len(results):
                    query = (db.dvi_body.id.belongs(results)) & query
                if filterby:
                    query = (filterby) & (query)
                records = db(query).select(db.dvi_body.id)
                # rebuild result list
                results = [r.id for r in records]
                # any results left?
                if not len(results):
                    return None
            return results
        else:
            # no label given or wrong parameter type
            return None

    # -----------------------------------------------------------------------------
    #
    def shn_dvi_body_search_simple(xrequest, **attr):

        """ Simple Search form for body recovery reports """

        if attr is None:
            attr = {}

        if not shn_has_permission("read", db.dvi_body):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c="default", f="user", args="login", vars={"_next":URL(r=request, args="search_simple", vars=request.vars)}))

        if xrequest.representation=="html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = str.lower(URL(r=request, f="body", args="[id]"))

            # Custom view
            response.view = "%s/body_search.html" % xrequest.prefix

            # Title and subtitle
            title = T("Find Recovery Report")
            subtitle = T("Matching Records")

            # Select form
            form = FORM(TABLE(
                    TR(T("ID Label: "),
                    INPUT(_type="text", _name="label", _size="40"),
                    DIV( _class="tooltip", _title=Tstr("ID Label") + "|" + Tstr("To search for a body, enter the ID label of the body. You may use % as wildcard. Press 'Search' without input to list all bodies."))),
                    TR("", INPUT(_type="submit", _value="Search"))
                    ))

            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                if form.vars.label == "":
                    form.vars.label = "%"

                results = shn_dvi_get_body_id(form.vars.label)

                if results and len(results):
                    rows = db(db.dvi_body.id.belongs(results)).select()
                else:
                    rows = None

                # Build table rows from matching records
                if rows:
                    records = []
                    for row in rows:
                        href = next.replace("%5bid%5d", "%s" % row.id)
                        records.append(TR(
                            A(row.pr_pe_label or "[no label]", _href=href),
                            row.opt_pr_gender and pr_person_gender_opts[row.opt_pr_gender] or "unknown",
                            row.opt_pr_age_group and pr_person_age_group_opts[row.opt_pr_age_group] or "unknown",
                            row.date_of_recovery,
                            (row.location_id and [db.gis_location[row.location_id].name] or [""])[0],
    #                        location_id.location_id.represent(row.location_id)
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("ID Label"),
                        TH("Gender"),
                        TH("Age Group"),
                        TH("Recovery Date"),
                        TH("Recovery Site"))),
                        TBODY(records), _id="list", _class="display"))
                else:
                    items = T("None")

            try:
                label_create_button = s3.crud_strings["dvi_body"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button

            add_btn = A(label_create_button, _href=URL(r=request, f="body", args="create"), _class="action-btn")

            output.update(dict(items=items, add_btn=add_btn))
            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, "body", method="search_simple", action=shn_dvi_body_search_simple )

    # -----------------------------------------------------------------------------
