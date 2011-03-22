# -*- coding: utf-8 -*-

"""
    Volunteer Management System

    @author: Zubair Assad
    @author: Pat Tressel
    @author: Fran Boon

"""

module = "vol"
if deployment_settings.has_module(module):

    # -------------------------------------------------------------------------
    # vol_volunteer (Component of pr_person)
    #   describes a person's availability as a volunteer

    vol_volunteer_status_opts = {
        1: T("active"),
        2: T("retired")
    }

    resourcename = "volunteer"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            person_id(),
                            # @ToDo: A person may volunteer for more than one org.
                            # Remove this -- the org can be inferred from the project
                            # or team in which the person participates.
                            #organisation_id(),
                            Field("date_avail_start", "date", label=T("Available from")),
                            Field("date_avail_end", "date", label=T("Available until")),
                            Field("hrs_avail_start", "time", label=T("Working hours start")),
                            Field("hrs_avail_end", "time", label=T("Working hours end")),
                            location_id(label=T("Available for Location"),
                                        requires=IS_ONE_OF(db, "gis_location.id",
                                                           shn_gis_location_represent_row,
                                                           filterby="level",
                                                           # This is likely to be customised for the deployment
                                                           filter_opts=["GR", "L0", "L1", "L2", "L3"],
                                                           orderby="gis_location.name"),
                                        widget=None),
                            Field("status", "integer",
                                requires = IS_IN_SET(vol_volunteer_status_opts, zero=None),
                                # default = 1,
                                label = T("Status"),
                                represent = lambda opt: vol_volunteer_status_opts.get(opt, UNKNOWN_OPT)),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    # Field labels
    #table.hrs_avail_end.comment = DIV(T("Minimum shift time is 6 hours"), _class="red")
    table.comments.comment = DIV( _class = "tooltip", 
                                  _title = "%s|%s" % (T("Comments"),
                                                      T("Please use this field to record any additional information, including any Special Needs."))
                                )

    # Representation function
    def shn_vol_volunteer_represent(id):
        person = db((db.vol_volunteer.id == id) & (db.pr_person.id == db.vol_volunteer.person_id)).select(
                    db.pr_person.first_name,
                    db.pr_person.middle_name,
                    db.pr_person.last_name,
                    limitby=(0, 1))
        if person:
            return vita.fullname(person.first())
        else:
            return None

    # CRUD Strings
    ADD_VOLUNTEER = T("Add Volunteer Registration")
    VOLUNTEERS = T("Volunteer Registrations")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_VOLUNTEER,
        title_display = T("Volunteer Registration"),
        title_list = VOLUNTEERS,
        title_update = T("Edit Volunteer Registration"),
        title_search = T("Search Volunteer Registrations"),
        subtitle_create = ADD_VOLUNTEER,
        subtitle_list = VOLUNTEERS,
        label_list_button = T("List Registrations"),
        label_create_button = T("Add Volunteer Registration"),
        msg_record_created = T("Volunteer registration added"),
        msg_record_modified = T("Volunteer registration updated"),
        msg_record_deleted = T("Volunteer registration deleted"),
        msg_list_empty = T("No volunteer information registered"))

    s3xrc.model.add_component(module, resourcename,
                              multiple=False,
                              joinby=dict(pr_person="person_id"))

    def vol_onvalidation(form):
        status = form.vars.date_avail_start <= form.vars.date_avail_end
        if status:
            return status
        else:
            error_msg = T("End date should be after start date")
            #form.errors["date_avail_start"] = error_msg
            form.errors["date_avail_end"] = error_msg
            return status

    s3xrc.model.configure(table,
                          onvalidation=vol_onvalidation,
                          list_fields=["organisation_id",
                                       "status"])

    # -------------------------------------------------------------------------
    # vol_skill
    #   Skills that a Person can have
    #   Certifications, Experience
    #
    vol_skill_category_opts = {
        1:T("Certification"),
        2:T("Experience")
    }
    resourcename = "skill"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("name",  length=128, notnull=True, label=T("Name")),
                            Field("category",
                                  requires=IS_IN_SET(vol_skill_category_opts),
                                  label=T("Category"),
                                  notnull=True,
                                  represent = lambda opt: vol_skill_category_opts(opt,
                                                                                  UNKNOWN_OPT)
                                  ),
                            Field("description"),
                            migrate=migrate, *s3_meta_fields())


    # Field settings
    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    table.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "%s.name" % tablename)]

    # CRUD Strings
    ADD_SKILL = T("Add Skill")
    SKILL = T("Skill")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SKILL,
        title_display = T("Skill Details"),
        title_list = SKILL,
        title_update = T("Edit Skill"),
        title_search = T("Search Skills"),
        subtitle_create = T("Add New Skill"),
        subtitle_list = SKILL,
        label_list_button = T("List Skills"),
        label_create_button = ADD_SKILL,
        label_delete_button = T("Delete Skill"),
        msg_record_created = T("Skill added"),
        msg_record_modified = T("Skill updated"),
        msg_record_deleted = T("Skill deleted"),
        msg_list_empty = T("No skills currently set"))

    # Representation function
    def vol_skill_represent(id):
        if id:
            record = db(db.vol_skill.id == id).select(db.vol_skill.name,
                                                      limitby=(0, 1)).first()
            name = record.name
            #category = record.category
            #if category:
            #    return "%s: %s" % (category, name)
            #else:
            #    return name
            return name
        else:
            return None

    skill_id = S3ReusableField("skill_id", db.vol_skill,
                               sortby = ["category", "name"],
                               requires = IS_ONE_OF(db, "vol_skill.id",
                                                    vol_skill_represent,
                                                    orderby="vol_skill.name"),
                               represent = vol_skill_represent,
                               label = T("Skill"),
                               ondelete = "RESTRICT")

    # -------------------------------------------------------------------------
    # vol_credential
    #   A volunteer's credentials: Confirmed experience & qualifications
    #   Component of pr_person
    #
    vol_credential_status_opts = {
        1:T("Pending"),
        2:T("Approved"),
        3:T("Rejected")
    }
    resourcename = "credential"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            person_id(),
                            skill_id(),
                            Field("status",
                                  requires=IS_IN_SET(vol_credential_status_opts),
                                  label=T("Status"),
                                  notnull=True,
                                  represent = lambda opt: vol_credential_status_opts.get(opt, UNKNOWN_OPT),
                                  default=1),   # pending
                            migrate=migrate, *s3_meta_fields())

    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(pr_person="person_id"))

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "skill_id",
                                       "status"])

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Credential"),
        title_display = T("Credential Details"),
        title_list = T("Credentials"),
        title_update = T("Edit Credential"),
        title_search = T("Search Credentials"),
        subtitle_create = T("Add New Credential"),
        subtitle_list = T("Credentials"),
        label_list_button = T("List Credentials"),
        label_create_button = T("Add Credentials"),
        label_delete_button = T("Delete Credential"),
        msg_record_created = T("Credential added"),
        msg_record_modified = T("Credential updated"),
        msg_record_deleted = T("Credential deleted"),
        msg_list_empty = T("No Credentials currently set"))

    # -------------------------------------------------------------------------
    # shn_pr_group_represent
    #
    def teamname(record):
        """
            Returns the Team Name
        """

        tname = ""
        if record and record.name:
            tname = "%s " % record.name.strip()
        return tname

    def shn_pr_group_represent(id):

        def _represent(id):
            table = db.pr_group
            group = db(table.id == id).select(table.name)
            if group:
                return teamname(group[0])
            else:
                return None

        name = cache.ram("pr_group_%s" % id, lambda: _represent(id))
        return name

    # -------------------------------------------------------------------------
    def shn_vol_project_search_location(xrequest, **attr):
        """ Form function to search projects by location """

        if attr is None:
            attr = {}

        if not s3_has_permission("read", db.project_project):
            session.error = UNAUTHORISED
            redirect(URL(r=request, c="default", f="user", args="login",
                         vars={"_next":URL(r=request, args="search_location",
                                           vars=request.vars)}))

        if xrequest.representation=="html":
            # Check for redirection
            if request.vars._next:
                next = str.lower(request.vars._next)
            else:
                next = str.lower(URL(r=request, c="project", f="project", args="[id]"))

            # Title and subtitle
            title = T("Search for a Project")
            subtitle = T("Matching Records")

            # Select form:
            query = (db.gis_location.deleted == False)
            l_opts = [OPTION(_value="")]
            l_opts += [OPTION(location.name, _value=location.id)
                       for location in db(query).select(db.gis_location.ALL,
                                                        cache=(cache.ram, 3600))]
            form = FORM(TABLE(
                    TR("%s: " % T("Location"),
                       SELECT(_name="location", *l_opts, **dict(name="location",
                                                                requires=IS_NULL_OR(IS_IN_DB(db, "gis_location.id"))))),
                    TR("", INPUT(_type="submit", _value=T("Search")))
                    ))

            output = dict(title=title, subtitle=subtitle, form=form, vars=form.vars)

            # Accept action
            items = None
            if form.accepts(request.vars, session):

                table = db.project_project
                query = (table.deleted == False)

                if form.vars.location is None:
                    results = db(query).select(table.ALL)
                else:
                    query = query & (table.location_id == form.vars.location)
                    results = db(query).select(table.ALL)

                if results and len(results):
                    records = []
                    for result in results:
                        href = next.replace("%5bid%5d", "%s" % result.id)
                        records.append(TR(
                            A(result.name, _href=href),
                            result.start_date or "None",
                            result.end_date or "None",
                            result.description or "None",
                            result.status and project_project_status_opts[result.status] or "unknown",
                            ))
                    items=DIV(TABLE(THEAD(TR(
                        TH("Name"),
                        TH("Start date"),
                        TH("End date"),
                        TH("Description"),
                        TH("Status"))),
                        TBODY(records), _id="list", _class="display"))
                else:
                        items = T("None")

            try:
                label_create_button = s3.crud_strings["project_project"].label_create_button
            except:
                label_create_button = s3.crud_strings.label_create_button

            add_btn = A(label_create_button,
                        _href=URL(r=request, c="project", f="project",
                                  args="create"),
                        _class="action-btn")

            output.update(dict(items=items, add_btn=add_btn))

            return output

        else:
            session.error = BADFORMAT
            redirect(URL(r=request))

    # Plug into REST controller
    s3xrc.model.set_method(module, "project",
                           method="search_location",
                           action=shn_vol_project_search_location)
# -----------------------------------------------------------------------------