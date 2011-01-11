# -*- coding: utf-8 -*-

""" VITA Person Finder, Models

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

module = "pf"

if deployment_settings.has_module(module):

    # *************************************************************************
    # Missing report
    #
    shn_pf_reporter_comment = \
        DIV(A(ADD_PERSON,
            _class="colorbox",
            _href=URL(r=request, c="pr", f="person", args="create", vars=dict(format="popup")),
            _target="top",
            _title=ADD_PERSON),
        DIV(DIV(_class="tooltip",
            _title=T("Reporter") + "|" + T("The person reporting about the missing person."))))

    reporter = S3ReusableField("reporter",
                               db.pr_person,
                               sortby=["first_name", "middle_name", "last_name"],
                               requires = IS_NULL_OR(IS_ONE_OF(db,
                                                               "pr_person.id",
                                                               shn_pr_person_represent,
                                                               orderby="pr_person.first_name")),
                               represent = lambda id: (id and
                                                       [shn_pr_person_represent(id)] or
                                                       ["None"])[0],
                               comment = shn_pf_reporter_comment,
                               ondelete = "RESTRICT")

    # -------------------------------------------------------------------------
    resourcename = "missing_report"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            person_id(),
                            reporter(),
                            Field("since", "datetime"),
                            Field("details", "text"),
                            location_id(label=T("Last known location")),
                            #Field("location_details"),
                            Field("contact", "text"),
                            migrate=migrate, *s3_meta_fields())


    table.person_id.label = T("Person missing")
    table.reporter.label = T("Person reporting")

    table.since.label = T("Date/Time of disappearance")
    table.since.requires = IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)
    table.since.represent = lambda value: shn_as_local_time(value)
    table.since.default = request.utcnow

    table.location_id.label = T("Last known location")
    #table.location_id.comment = DIV(A(ADD_LOCATION,
            #_class="colorbox",
            #_href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
            #_target="top",
            #_title=ADD_LOCATION),
        #DIV( _class="tooltip",
            #_title=T("Last known location") + "|" + T("The last known location of the missing person before disappearance."))),
    #table.location_details.label = T("Location details")

    #table.details.label = T("Details")
    #table.details.comment = DIV(DIV(_class="tooltip",
        #_title=T("Details") + "|" + T("Circumstances of disappearance, other victims/witnesses who last saw the missing person alive.")))

    table.contact.label = T("Contact")
    table.contact.comment =  DIV(DIV(_class="tooltip",
        _title=T("Contact") + "|" + T("Contact person(s) in case of news or further questions (if different from reporting person). Include telephone number, address and email as available.")))

    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=dict(pr_person="person_id"))


    def shn_pf_report_onaccept(form):
        """
        @todo: docstring

        """

        table = db.pr_person
        person_id = request.post_vars.person_id

        if person_id:
            person = db(table.id == person_id).select(table.pe_id, limitby=(0,1)).first()
            if person:
                pe_id = person.pe_id
            else:
                return
        else:
            return

        user = db(table.uuid == session.auth.user.person_uuid).select(table.id, limitby=(0,1)).first()
        if user:
            user_id = user.id
        else:
            return # no anonymous reports!

        table = db.pr_presence
        query = (table.pe_id == pe_id) & (table.deleted == False) & \
                (table.presence_condition == vita.MISSING) & \
                (table.closed == False) & \
                (table.reporter == user_id)
        presence = db(query).select(table.id, orderby=~table.datetime, limitby=(0,1)).first()

        record = dict(pe_id = pe_id,
                      datetime = request.utcnow,
                      reporter = user_id,
                      location_id = form.vars.location_id,
                      closed = False,
                      presence_condition = vita.MISSING)

        if presence:
            record_id = presence.id
            db(table.id == presence.id).update(**record)
        else:
            record_id = table.insert(**record)

        if record_id:
            vita.presence_accept(record_id)


    s3xrc.model.configure(table,
        deletable=False,
        onaccept = lambda form: shn_pf_report_onaccept(form),
        list_fields = [
            "id",
            "reporter"
        ])

# -----------------------------------------------------------------------------
ADD_REPORT = T("Add Report")
LIST_REPORTS = T("List Reports")
s3.crud_strings[tablename] = Storage(
title_create = ADD_REPORT,
title_display = T("Missing Persons Report"),
title_list = LIST_REPORTS,
title_update = T("Edit Report"),
title_search = T("Search Reports"),
subtitle_create = ADD_PERSON,
subtitle_list = T("Missing Person Reports"),
label_list_button = LIST_REPORTS,
label_create_button = ADD_REPORT,
label_delete_button = T("Delete Report"),
msg_record_created = T("Report added"),
msg_record_modified = T("Report updated"),
msg_record_deleted = T("Report deleted"),
msg_list_empty = T("No report available."))

