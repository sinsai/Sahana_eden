# -*- coding: utf-8 -*-

"""
   Survey Module

    @author: Robert O'Connor
"""

module = "survey"

from gluon.sqlhtml import *


ADD_LOCATION = T("Add Location")
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name
location_id = db.Table(None, "location_id",
                       FieldS3("location_id", db.gis_location, sortby="name",
                       requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id", repr_select, sort=True)),
                       represent = lambda id: shn_gis_location_represent(id),
                       label = T("Location"),
                       comment = DIV(SPAN("* ", _class="req"),A(ADD_LOCATION,
                                       _class="colorbox",
                                       _href=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup")),
                                       _target="top",
                                       _title=ADD_LOCATION),
                                     DIV( _class="tooltip",
                                       _title=Tstr("Location") + "|" + Tstr("The Location of this Site, which can be general (for Reporting) or precise (for displaying on a Map)."))),
                       ondelete = "RESTRICT"))

s3xrc.model.configure(db.gis_location,
                      onvalidation=lambda form: gis.wkt_centroid(form),
                      onaccept=gis.update_location_tree())


if deployment_settings.has_module(module):

    #Reusable table
    name_desc = db.Table(db,timestamp, uuidstamp, deletion_status, authorstamp,
                         Field("name", "string", default="", length=120),
                         Field("description", "text", default="",length=500))

    #Survey Template
    resource = "template"
    tablename = module + "_" + resource
    template = db.define_table(tablename,name_desc,
                               Field("table_name","string",readable=False,writable=False),
                               Field("locked","boolean",readable=False,writable=False),
                               person_id,
                               organisation_id)

    # Survey Series
    resource = "series"
    tablename = module + "_" + resource
    series = db.define_table(tablename,name_desc,
                             Field("survey_template_id", db.survey_template),
                             Field("from_date", "datetime", default=None),
                             Field("to_date","datetime",default=None),
                             location_id)

    # Survey Section
    resource = "questions"
    tablename = module +"_" + resource
    section = db.define_table(tablename,name_desc)

    # Question options e.g., Row choices, Column Choices, Layout Configuration data, etc...
    resource = "question_options"
    tablename = module +"_" + resource
    question_options = db.define_table(tablename,uuidstamp,deletion_status,authorstamp,
#    #                                        Field("display_option","integer"),
##                                            Field("answer_choices","text",length=700),
##                                            Field("row_choices","text"), # row choices
##                                            Field("column_choices","text"), # column choices
#                                            Field("tf_choices","text"), # text before the text fields.
                                            Field("tf_ta_columns","integer"), # number of columns for TF/TA
                                            Field("ta_rows","integer"), # number of rows for text areas
##                                            Field("number_of_options","integer"),
                                            Field("allow_comments","boolean"), # whether or not to allow comments
                                            Field("comment_display_label"), # the label for the comment field
                                            Field("required","boolean"), # marks the question as required
#                                            Field("validate","boolean"),  # whether or not to enable validation
##                                            Field("validation_options","integer"), # pre-set validation regexps and such.
                                            Field("aggregation_type","string"))

    # Survey Question
    resource = "question"
    tablename = module +"_" + resource
    question = db.define_table(tablename,name_desc,
                               Field("question_type","integer"),
#                               Field("options_id",db.survey_question_options),
                               Field("tf_ta_columns","integer"), # number of columns for TF/TA
                               Field("ta_rows","integer"), # number of rows for text areas
                               Field("allow_comments","boolean"), # whether or not to allow comments
                               Field("comment_display_label"), # the label for the comment field
                               Field("required","boolean"), # marks the question as required
                               Field("aggregation_type","string"))


    #Survey Instance
    resource = "instance"
    tablename = module +"_" + resource
    instance = db.define_table(tablename,timestamp, uuidstamp, deletion_status, authorstamp,
                               Field("survey_series_id",db.survey_series))

    # Survey Answer
    resource = "answer"
    tablename = module +"_" + resource
    answer = db.define_table(tablename,timestamp, uuidstamp, deletion_status, authorstamp,
                             Field("survey_instance_id",db.survey_instance),
                             Field("question_id",db.survey_question),
                             Field("answer_value","text",length=600),
                             Field("answer_image","upload"), # store the image if "Image" is selected.
                             Field("answer_location",db.gis_location),
                             Field("answer_person",db.pr_person),
                             Field("answer_organisation",db.org_organisation))

    # Link table
    resource = "template_link"
    tablename = module +"_" + resource
    link_table = db.define_table(tablename,timestamp, uuidstamp, deletion_status, authorstamp,
                                 Field("survey_question_id",db.survey_question),
                                 Field("survey_template_id", db.survey_template),
                                 Field("survey_questions_id", db.survey_questions))
    link_table.survey_question_id.requires =IS_NULL_OR(IS_ONE_OF(db, "survey_question.id", "%(name)s"))


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