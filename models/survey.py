# -*- coding: utf-8 -*-

"""
   Survey Module

    @author: Robert O'Connor
"""

module = "survey"

if deployment_settings.has_module(module):

#    # Reusable table
#    name_desc = db.Table(db,
#                         Field("name", "string", default="", length=120),
#                         Field("description", "text", default="", length=500),
#                         *s3_meta_fields())

    # Survey Template
    resourcename = "template"
    tablename = module + "_" + resourcename
    template = db.define_table(tablename,
                               Field("name", "string", default="", length=120),
                               Field("description", "text", default="", length=500),
                               Field("table_name", "string", readable=False, writable=False),
                               Field("locked", "boolean", readable=False, writable=False),
                               person_id(),
                               organisation_id(),
                               migrate=migrate,
                               *s3_meta_fields())

    # Survey Series
    resourcename = "series"
    tablename = module + "_" + resourcename
    series = db.define_table(tablename,
                             Field("name", "string", default="", length=120),
                             Field("description", "text", default="", length=500),
                             Field("survey_template_id", db.survey_template),
                             Field("start_date", "date", default=None),
                             Field("end_date", "date", default=None),
                             location_id(),
                             migrate=migrate,
                             *s3_meta_fields())

    def survey_series_onvalidation(form):
        status = form.vars.start_date <= form.vars.end_date
        if status:
            return status
        else:
            error_msg = T("End date should be after start date")
            form.errors["end_date"] = error_msg
            return status

    s3xrc.model.configure(series,
                          onvalidation=survey_series_onvalidation)

    # Survey Section
    resourcename = "questions"
    tablename = module + "_" + resourcename
    section = db.define_table(tablename,
                              migrate=migrate, *s3_meta_fields())


    # Survey Question
    resourcename = "question"
    tablename = module + "_" + resourcename
    question = db.define_table(tablename,
                                Field("name", "string", default="", length=120),
                                Field("question_type", "integer"),
                                Field("description", "text", default="", length=500),
                                migrate=migrate, *s3_meta_fields())

                                #Field("options_id", db.survey_question_options),
                                #Field("tf_ta_columns", "integer"), # number of columns for TF/TA
                                #Field("ta_rows", "integer"), # number of rows for text areas
                                #Field("allow_comments", "boolean"), # whether or not to allow comments
                                #Field("comment_display_label"), # the label for the comment field
                                #Field("required", "boolean"), # marks the question as required
                                #Field("aggregation_type", "string"))

    # Link table
    resourcename = "template_link"
    tablename = module + "_" + resourcename
    link_table = db.define_table(tablename,
                                 Field("survey_question_id", db.survey_question),
                                 Field("survey_template_id", db.survey_template),
                                 Field("survey_questions_id", db.survey_questions),
                                 migrate=migrate, *s3_meta_fields())

    link_table.survey_question_id.requires = IS_NULL_OR(IS_ONE_OF(db, "survey_question.id", "%(name)s"))


    # Unused code below here

#    # Survey Instance
#    resourcename = "instance"
#    tablename = module + "_" + resourcename
#    instance = db.define_table(tablename, timestamp, uuidstamp, deletion_status, authorstamp,
#                               Field("survey_series_id", db.survey_series),
#                               migrate=migrate)

#    # Survey Answer
#    resourcename = "answer"
#    tablename = module + "_" + resourcename
#    answer = db.define_table(tablename, timestamp, uuidstamp, deletion_status, authorstamp,
#                             Field("survey_instance_id", db.survey_instance),
#                             Field("question_id", db.survey_question),
#                             Field("answer_value", "text", length=600),
#                             Field("answer_image", "upload"), # store the image if "Image" is selected.
#                             Field("answer_location", db.gis_location),
#                             Field("answer_person", db.pr_person),
#                             Field("answer_organisation", db.org_organisation),
#                             migrate=migrate)

#    # Question options e.g., Row choices, Column Choices, Layout Configuration data, etc...
#    resourcename = "question_options"
#    tablename = module + "_" + resourcename
#    question_options = db.define_table(tablename, uuidstamp, deletion_status, authorstamp,
##    #                                 Field("display_option", "integer"),
###                                     Field("answer_choices", "text", length=700),
###                                     Field("row_choices", "text"), # row choices
###                                     Field("column_choices", "text"), # column choices
##                                      Field("tf_choices", "text"), # text before the text fields.
#                                       Field("tf_ta_columns", "integer"), # number of columns for TF/TA
#                                       Field("ta_rows", "integer"), # number of rows for text areas
###                                     Field("number_of_options", "integer"),
#                                       Field("allow_comments", "boolean"), # whether or not to allow comments
#                                       Field("comment_display_label"), # the label for the comment field
#                                       Field("required", "boolean"), # marks the question as required
##                                      Field("validate", "boolean"),  # whether or not to enable validation
###                                     Field("validation_options", "integer"), # pre-set validation regexps and such.
#                                       Field("aggregation_type", "string"),
#                                       migrate=migrate)

#    def question_options_onaccept(form):
#        if form.vars.id and session.rcvars.survey_question:
#            table = db.survey_question_options
#            opts = db(table.id == form.vars.id).update(question_id=session.rcvars.survey_question)
#            db.commit()
#
#    s3xrc.model.configure(db.survey_question_options,
#                      onaccept=lambda form: question_options_onaccept(form))

#    def question_onaccept(form):
#        if form.vars.id and session.rcvars.survey_section and session.rcvars.survey_template:
#            db.survey_template_link_table.insert(survey_section_id=session.rcvars.survey_section, survey_template_id=session.rcvars.survey_template)
#            db.commit()
#    s3xrc.model.configure(db.survey_question,
#                      onaccept=lambda form: question_onaccept(form))