# -*- coding: utf-8 -*-

""" VITA Disaster Victim Identification, Models

    @author: nursix
    @author: khushbu
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "dvi"
if deployment_settings.has_module(module):

    # -----------------------------------------------------------------------------
    # Recovery Request
    #
    task_status = {
        1:T("New"),
        2:T("Assigned"),
        3:T("In Progress"),
        4:T("Completed"),
        5:T("Not Applicable"),
        6:T("Not Possible")
    }

    resourcename = "recreq"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("date", "datetime"),
                            Field("marker", length=64),
                            location_id(),
                            Field("location_details"),
                            person_id(), # Finder
                            Field("description"),
                            Field("bodies_est", "integer"), # Number of bodies found
                            Field("status", "integer",
                                  requires = IS_IN_SET(task_status, zero=None),
                                  default = 1,
                                  label = T("Task Status"),
                                  represent = lambda opt: \
                                              task_status.get(opt, UNKNOWN_OPT)),
                            Field("bodies_rec", "integer"), # Number of bodies recovered
                            migrate=migrate, *s3_meta_fields())

    # Settings and Restrictions
    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % table)

    table.date.label = T("Date/Time of Find")
    table.date.default = request.utcnow
    table.date.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(),
                                          allow_future=False)
    table.date.represent = shn_as_local_time

    table.marker.label = T("Marker")
    table.marker.comment = DIV(_class="tooltip",
                                _title="%s|%s" % (
                                       T("Marker"),
                                       T("Number or code used to mark the place of find, e.g. flag code, grid coordinates, site reference number or similar (if available)")))

    table.location_id.label = T("Location")
    table.person_id.label = T("Finder")

    table.bodies_est.label = T("Bodies found")
    table.bodies_est.requires = IS_INT_IN_RANGE(1, 99999)
    table.bodies_est.default = 0

    table.bodies_rec.label = T("Bodies recovered")
    table.bodies_rec.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 99999))
    table.bodies_rec.default = 0

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
                                               "[%(marker)s] %(date)s: %(bodies_est)s bodies")),
                                    represent = lambda id: id,
                                    ondelete = "RESTRICT")


    s3xrc.model.configure(table,
        list_fields = ["id",
                       "date",
                       "marker",
                       "location_id",
                       "location_details",
                       #"description",
                       "bodies_est",
                       "bodies_rec",
                       "status"])

    # Body ====================================================================
    resourcename = "body"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id
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

    table.pe_label.requires = [IS_NOT_EMPTY(
                                error_message=T("Enter a unique label!")),
                               IS_NOT_ONE_OF(db, "dvi_body.pe_label")]

    table.date_of_recovery.default = request.utcnow
    table.date_of_recovery.requires = IS_UTC_DATETIME(
                                        utc_offset=shn_user_utc_offset(),
                                        allow_future=False)
    table.date_of_recovery.represent = shn_as_local_time

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
        title_create = T("Add Dead Body Report"),
        title_display = T("Dead Body Details"),
        title_list = T("Dead Body Reports"),
        title_update = T("Edit Dead Body Details"),
        title_search = T("Find Dead Body Report"),
        subtitle_create = T("Add New Report"),
        subtitle_list = T("List of Reports"),
        label_list_button = T("List Reports"),
        label_create_button = T("Add Report"),
        label_delete_button = T("Delete Report"),
        msg_record_created = T("Dead body report added"),
        msg_record_modified = T("Dead body report updated"),
        msg_record_deleted = T("Dead body report deleted"),
        msg_list_empty = T("No dead body reports available"))

    s3xrc.model.configure(table,
                          super_entity=db.pr_pentity,
                          list_fields=["id",
                                       "pe_label",
                                       "gender",
                                       "age_group",
                                       "incomplete",
                                       "date_of_recovery",
                                       "location_id"])

    dvi_body_search = s3base.S3Search(
            name = "body_search_simple",
            label = T("ID Tag"),
            comment = T("To search for a body, enter the ID tag number of the body. You may use % as wildcard. Press 'Search' without input to list all bodies."),
            field = ["pe_label"])

    # Set as standard search method
    s3xrc.model.configure(db.dvi_body, search_method=dvi_body_search)

    #
    # Checklist of operations -----------------------------------------------------
    #
    resourcename = "checklist"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                super_link(db.pr_pentity), # pe_id
                Field("personal_effects","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Inventory of Effects"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("body_radiology","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Radiology"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("fingerprints","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Fingerprinting"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("anthropology","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Anthropolgy"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("pathology","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Pathology"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("embalming","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Embalming"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("dna","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("DNA Profiling"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                Field("dental","integer",
                        requires = IS_IN_SET(task_status, zero=None),
                        default = 1,
                        label = T("Dental Examination"),
                        represent = lambda opt: \
                                    task_status.get(opt, UNKNOWN_OPT)),
                migrate=migrate, *s3_meta_fields())

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

    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = super_key(db.pr_pentity))

    s3xrc.model.configure(table, list_fields = ["id"])

    # -------------------------------------------------------------------------
    # Personal Effects
    #
    resourcename = "effects"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                super_link(db.pr_pentity),  # pe_id
                Field("clothing", "text"),  #TODO: elaborate
                Field("jewellery", "text"), #TODO: elaborate
                Field("footwear", "text"),  #TODO: elaborate
                Field("watch", "text"),     #TODO: elaborate
                Field("other", "text"),
                migrate=migrate, *s3_meta_fields())

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

    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = super_key(db.pr_pentity))

    s3xrc.model.configure(table, list_fields = ["id"])

    # -------------------------------------------------------------------------
    # Identification
    #
    dvi_id_status = {
        1:T("Unidentified"),
        2:T("Preliminary"),
        3:T("Confirmed"),
    }

    dvi_id_methods = {
        1:T("Visual Recognition"),
        2:T("Physical Description"),
        3:T("Fingerprints"),
        4:T("Dental Profile"),
        5:T("DNA Profile"),
        6:T("Combined Method"),
        9:T("Other Evidence")
    }

    resourcename = "identification"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                super_link(db.pr_pentity), # pe_id
                Field("status", "integer",
                      requires = IS_IN_SET(dvi_id_status, zero=None),
                      default = 1,
                      label = T("Identification Status"),
                      represent = lambda opt: \
                                  dvi_id_status.get(opt, UNKNOWN_OPT)),
                person_id("identity",
                            label=T("Identified as"),
                            empty=False),
                person_id("identified_by",
                            label=T("Identified by"),
                            empty=False),
                Field("method", "integer",
                      requires = IS_IN_SET(dvi_id_methods, zero=None),
                      default = 1,
                      label = T("Method used"),
                      represent = lambda opt: \
                                  dvi_id_methods.get(opt, UNKNOWN_OPT)),
                Field("presence", db.pr_presence),
                Field("comment", "text"),
                migrate=migrate, *s3_meta_fields())

    table.presence.readable = False
    table.presence.writable = False

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
    s3xrc.model.add_component(module, resourcename,
                              multiple = False,
                              joinby = super_key(db.pr_pentity))


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
                                                      table.status,
                                                      limitby=(0, 1)).first()

            if not record:
                return

            if record.presence and \
               (record.deleted or record.opt_dvi_id_status != 3):

                # Remove prior attached presence records
                db(db.pr_presence.id == record.presence).update(deleted=True)
                vita.presence_accept(record.presence)
                db(table.id == record_id).update(presence=None)

            elif not record.presence and record.status == 3:

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
                observer = None
                query = db.pr_person.uuid == session.auth.user.person_uuid
                user = db(query).select(db.pr_person.id, limitby=(0,1)).first()
                if user:
                    observer = user.id

                # Insert new presence record
                presence_id = db.pr_presence.insert(
                    pe_id = person.pe_id,
                    observer = observer,
                    datetime = request.utcnow,
                    location_id = location_id,
                    presence_condition = vita.DECEASED,
                )
                if presence_id:
                    db(table.id == record_id).update(presence=presence_id)
                    vita.presence_accept(presence_id)

    # -----------------------------------------------------------------------------
    s3xrc.model.configure(table,
        mark_required = ["identity", "identified_by"],
        onvalidation = lambda form: dvi_identification_onvalidation(form),
        onaccept = lambda form: dvi_identification_onaccept(form),
        delete_onaccept = lambda row: dvi_identification_onaccept(row),
        list_fields = ["id"])


    # -----------------------------------------------------------------------------
    #
    def shn_dvi_rheader(r, tabs=[]):

        """ Page header for component pages """

        if r.name == "body":
            if r.representation == "html":
                _next = r.here()
                _same = r.same()

                rheader_tabs = s3_rheader_tabs(r, tabs)

                body = r.record
                if body:
                    rheader = DIV(TABLE(

                        TR(TH("%s: " % T("ID Tag Number")),
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
