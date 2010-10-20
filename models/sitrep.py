# -*- coding: utf-8 -*-

""" Assessments Module - Model

    @author: Fran Boon

    @see: U{<http://eden.sahanafoundation.org/wiki/Pakistan>}

"""

module = "sitrep"
if deployment_settings.has_module(module):

    # *************************************************************************
    # Assessments - WFP (deprecated)
    #
    resource = "assessment"
    tablename = "%s_%s" % (module, resource)
    table = db.define_table(tablename,
                            Field("title"),
                            location_id(),
                            organisation_id(),
                            Field("date", "date"),
                            Field("households", "integer"),
                            Field("population", "integer"),
                            Field("persons_affected", "integer"),
                            Field("persons_injured", "integer"),
                            Field("persons_deceased", "integer"),
                            Field("houses_destroyed", "integer"),
                            Field("houses_damaged", "integer"),
                            Field("crop_losses", "integer"),
                            Field("water_level", "boolean"),
                            Field("crops_affectees", "double"),
                            Field("source"), # Legacy field: will be removed
                            document_id(),
                            comments(),
                            migrate=migrate, *s3_meta_fields())


    table.households.label = T("Total Households")
    table.households.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    #table.households.default = 0

    table.population.label = T("Population")
    table.population.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    #table.population.default = 0

    table.persons_affected.label = T("# of People Affected")
    table.persons_injured.label = T("# of People Injured")
    table.persons_deceased.label = T("# of People Deceased")
    table.houses_destroyed.label = T("# of Houses Destroyed")
    table.houses_damaged.label = T("# of Houses Damaged")

    table.persons_affected.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    table.persons_injured.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    table.persons_deceased.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    table.houses_destroyed.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    table.houses_damaged.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )

    table.persons_affected.comment = T("Numbers Only")
    table.persons_injured.comment = T("Numbers Only")
    table.persons_deceased.comment = T("Numbers Only")
    table.houses_destroyed.comment = T("Numbers Only")
    table.houses_damaged.comment = T("Numbers Only")

    #table.houses_destroyed.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    #table.houses_destroyed.default = 0
    #table.houses_damaged.requires = IS_NULL_OR( IS_INT_IN_RANGE(0,99999999) )
    #table.houses_damaged.default = 0

    table.crop_losses.requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 100))

    table.source.comment = DIV(DIV(_class="tooltip",
                              _title=T("Source") + "|" + T("Ideally a full URL to the source file, otherwise just a note on where data came from.")))

    # CRUD strings
    #ADD_ASSESSMENT = T("Add Assessment")
    #LIST_ASSESSMENTS = T("List Assessments")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ASSESSMENT,
        title_display = T("Assessment Details"),
        title_list = LIST_ASSESSMENTS,
        title_update = T("Edit Assessment"),
        title_search = T("Search Assessments"),
        subtitle_create = T("Add New Assessment"),
        subtitle_list = T("Assessments"),
        label_list_button = LIST_ASSESSMENTS,
        label_create_button = ADD_ASSESSMENT,
        msg_record_created = T("Assessment added"),
        msg_record_modified = T("Assessment updated"),
        msg_record_deleted = T("Assessment deleted"),
        msg_list_empty = T("No Assessments currently registered"))

    # assessment as component of doc_documents
    #s3xrc.model.add_component(module, resource,
    #                          multiple=True,
    #                          joinby=dict(doc_document="document_id"))

    def shn_sitrep_school_report_onvalidation(form):

        """
            School report validation

            Deprecated, but left for now as a good example to be used in RAT
        """

        def validate_total(total, female, male):

            error_msg = T("Contradictory values!")

            _total = form.vars.get(total, None)
            _female = form.vars.get(female, None)
            _male = form.vars.get(male, None)

            if _total is None:
                form.vars[total] = int(_female or 0) + int(_male or 0)
            else:
                _total = int(_total)
                if _male is None:
                    if _female is not None:
                        _female = int(_female)
                        if _female <= _total:
                            form.vars[male] = _total - _female
                        else:
                            form.errors[total] = form.errors[female] = error_msg
                else:
                    _male = int(_male)
                    if _female is not None:
                        _female = int(_female)
                        if _total != _female + _male:
                            form.errors[total] = form.errors[female] = form.errors[male] = error_msg
                    else:
                        if _male <= _total:
                            form.vars[female] = _total - _male
                        else:
                            form.errors[total] = form.errors[male] = error_msg

        validate_total("total_affected_total",
                       "total_affected_female",
                       "total_affected_male")

        validate_total("teachers_affected_total",
                       "teachers_affected_female",
                       "teachers_affected_male")

        validate_total("students_affected_total",
                       "students_affected_female",
                       "students_affected_male")


    # -----------------------------------------------------------------------------
