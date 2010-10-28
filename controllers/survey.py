# -*- coding: utf-8 -*-

""" Survey Module -- a tool to create surveys.

    @author: Robert O'Connor

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

from gluon.html import *
from gluon.sqlhtml import SQLFORM

response.menu_options = [
    [T("Templates"), False, URL(r=request, f="template"),[
        [T("List"), False, URL(r=request, f="template")],
        [T("Add"), False, URL(r=request, f="template", args="create")]
    ]],
    [T("Series"), False, URL(r=request, f="series"),[
        [T("List"), False, URL(r=request, f="series")],
        [T("Add"), False, URL(r=request, f="series", args="create")]
    ]]]

def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[prefix].name_nice
    return dict(module_name=module_name)


def template():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    def prep(r):
        s3xrc.model.configure(r.table,
            create_next = URL(r=request, c="survey", f="questions"),
            update_next = URL(r=request, c="survey", f="questions"))
        return True
    response.s3.prep = prep

    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Name")
    table.description.label = T("Description")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Survey Template"),
        title_display = T("Survey Template Details"),
        title_list = T("List Survey Templates"),
        title_update = T("Edit Survey Template"),
        subtitle_create = T("Add New Survey Template"),
        subtitle_list = T("Survey Templates"),
        label_list_button = T("List Survey Templates"),
        label_create_button = T("Add Survey Template"),
        label_delete_button = T("Delete Survey Template"),
        msg_record_created = T("Survey Template added"),
        msg_record_modified = T("Survey Template updated"),
        msg_record_deleted = T("Survey Template deleted"),
        msg_list_empty = T("No Survey Template currently registered"))

    s3xrc.model.configure(table, listadd=False)
    output = s3_rest_controller(prefix, resourcename)

    #return transform_buttons(output, next=True, cancel=True)
    return output


def template_link():

    """ @todo: fix docstring, PEP8 """

    response.s3.prep = lambda r: r.representation in ("xml", "json") and True or False
    return s3_rest_controller("survey", "template_link")


def questions():

    """ At this stage, the user the following workflow will be implemented:
            -  User adds questions via the drop down or clicks "Add Question" to add a new one.

    """

    table = db["survey_questions"]
    record = request.args(0)
    template = db(db.survey_template.id == session.rcvars.survey_template).select(limitby=(0, 1)).first()
    if not template:
        session.error = T("No template found!")
        redirect(URL(r=request, f="template"))
    if not record:
        questions_query = (db.survey_template_link.survey_questions_id == db.survey_questions.id) & (template.id == db.survey_template_link.survey_template_id)
        record = db(questions_query).select(db.survey_questions.id, limitby=(0, 1)).first()
        if record:
           redirect(URL(r=request, f="questions", args=[record.id]))
    questions_form = SQLFORM(table, record, deletable=True, keepvalues=True)
    all_questions = db().select(db.survey_question.ALL)
    output = dict(all_questions=all_questions)
    # Let's avoid blowing up -- this loads questions
    try:
        query = (template.id == db.survey_template_link.survey_template_id)
        contained_questions = db(query).select(db.survey_question.id)
        if len(contained_questions) > 0:
            output.update(contained_questions=contained_questions)
        else:
            output.update(contained_questions=contained_questions)
    except:
        output.update(contained_questions=[])
        pass # this means we didn't pass an id, e.g., making a new section!
    if questions_form.accepts(request.vars, session, keepvalues=True):
        questions = request.post_vars.questions
        if questions:
            for question in questions:
               if not has_dupe_questions(template.id, question):
                   db.survey_template_link.insert(survey_template_id=session.rcvars.survey_template,
                                                  survey_questions_id=questions_form.vars.id,
                                                  survey_question_id=question)
    elif questions_form.errors:
        response.error = T("Please correct all errors.")
    output.update(form=questions_form)

    return output

def table():

    """ @todo: fix docstring, PEP8 """

    if not "series_id" in request.vars:
        response.error = T("You must provide a series id to proceed.")
        return dict() # empty dict!

    # store the necessary information -- we're safe at this point.
    series_id = request.vars.series_id

    # first check the series exists.
    series = db(db.survey_series.id == series_id).select(limitby=(0, 1)).first()
    if not series:
        response.error = T("A survey series with id %s does not exist. Please go back and create one.") % (series_id)
        return dict()
    # query for the template to get the table name
    template = db(db.survey_template.id == series.survey_template_id).select(limitby=(0, 1)).first()

    # everything is good at this point!
    table = get_table_for_template(template.id)
    resourcename = "template_%s" % (template.id)
    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % template.table_name)
    table.id.represent =  lambda id: A(id, _href=URL(r=request, f="table", args=[id, "update"], vars={"series_id":request.vars.series_id}))
     # CRUD Strings
    s3.crud_strings[template.table_name] = Storage(
        title_create = T("Add Survey Answer"),
        title_display = T("Survey Answer Details"),
        title_list = T("List Survey Answers"),
        title_update = T("Edit Survey Answer"),
        subtitle_create = T("Add New Survey Answer"),
        subtitle_list = T("Survey Answer"),
        label_list_button = T("List Survey Answers"),
        label_create_button = T("Add Survey Answer"),
        label_delete_button = T("Delete Survey Answer"),
        msg_record_created = T("Survey Answer added"),
        msg_record_modified = T("Survey Answer updated"),
        msg_record_deleted = T("Survey Answer deleted"),
        msg_list_empty = T("No Survey Answers currently registered"))
    response.s3.filter = (table.series_id == series_id)

    s3xrc.model.configure(table, listadd=False)
    output = s3_rest_controller("survey", resourcename)

    authorised = shn_has_permission("create", table)
    if authorised:
        output.update(add_btn=A(T("Add Survey Answer"),
                                _href=URL(r=request, f="table", args=["create"], vars={"series_id":request.vars.series_id}),
                                _class="action-btn"))
    else:
        output.update(add_btn="")
    return output


def series():

    """ RESTful CRUD controller """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Series Name")
    table.description.label = T("Description")
    table.survey_template_id.label = T("Survey Template")
    table.survey_template_id.requires = IS_ONE_OF(db, "survey_template.id", "%(name)s")
    table.survey_template_id.represent = lambda id: (id and [db(db.survey_template.id == id).select(db.survey_template.name, limitby=(0, 1)).first().name] or [""])[0]
    table.from_date.label = T("Start of Period")
    table.from_date.requires = IS_NOT_EMPTY()
    table.to_date.label = T("End of Period")
    table.to_date.requires = IS_NOT_EMPTY()

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Survey Series"),
        title_display = T("Survey Series Details"),
        title_list = T("List Survey Series"),
        title_update = T("Edit Survey Series"),
        subtitle_create = T("Add New Survey Series"),
        subtitle_list = T("Survey Series"),
        label_list_button = T("List Survey Series"),
        label_create_button = T("Add Survey Series"),
        label_delete_button = T("Delete Survey Series"),
        msg_record_created = T("Survey Series added"),
        msg_record_modified = T("Survey Series updated"),
        msg_record_deleted = T("Survey Series deleted"),
        msg_list_empty = T("No Survey Series currently registered"))

    # Post-processor
    def postp(r, output):
        shn_survey_action_buttons(r, deletable=False)
        return output
    response.s3.postp = postp

    s3xrc.model.configure(table, listadd=False)
    output = s3_rest_controller(prefix, resourcename)

    return output


def question():

    """ Question data, e.g., name, description, etc. """

    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Question Display Name")
    table.description.label = T("Description")
#    table.tf_ta_columns.label = T("Number of Columns")
#    table.ta_rows.label = T("Number of Rows")
#    table.aggregation_type.writable = False
#    table.aggregation_type.readable = False

    question_types = {
#        1:T("Multiple Choice (Only One Answer)"),
#        2:T("Multiple Choice (Multiple Answers)"),
#        3:T("Matrix of Choices (Only one answer)"),
#        4:T("Matrix of Choices (Multiple Answers)"),
#        5:T("Rating Scale"),
        6:T("Text"),
#        7:T("Multiple Text Fields"),
#        8:T("Matrix of Text Fields"),
        9:T("Long Text"),
        10:T("Number"),
        11:T("Date"),
#        12:T("Image"),
#        13:T("Descriptive Text (e.g., Prose, etc)"),
#        14:T("Location"),
#        15:T("Organization"),
#        16:T("Person"),
##        16:T("Custom Database Resource (e.g., anything defined as a resource in Sahana)")
    }

    table.question_type.requires = IS_IN_SET(question_types)

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Survey Question"),
        title_display = T("Survey Question Details"),
        title_list = T("List Survey Questions"),
        title_update = T("Edit Survey Question"),
        subtitle_create = T("Add New Survey Question"),
        subtitle_list = T("Survey Question"),
        label_list_button = T("List Survey Questions"),
        label_create_button = T("Add Survey Question"),
        label_delete_button = T("Delete Survey Question"),
        msg_record_created = T("Survey Question added"),
        msg_record_modified = T("Survey Question updated"),
        msg_record_deleted = T("Survey Question deleted"),
        msg_list_empty = T("No Survey Questions currently registered"))

    s3xrc.model.configure(table, listadd=False)
    output = s3_rest_controller(prefix, resourcename)

    #return transform_buttons(output, cancel=True, save=True)
    return output


def add_buttons(form, save = None, prev = None, next = None, finish = None, cancel=None):

    """ Utility Function to reduce code duplication as this deals with:

        1) removing the save button
        2) adding the following: Cancel, Next, Previous and Finish (shown on the last step *ONLY*)

    """

    form[0][-1][1][0] = "" # remove the original Save Button
    if save:
        form[-1][-1][1].append(INPUT(_type="submit", _name = "save", _value=T("Save"), _id="save"))

    if cancel:
        form[-1][-1][1].append(INPUT(_type="button", _name = "cancel", _value=T("Cancel"), _id="cancel"))

    if prev:
        form[-1][-1][1].append(INPUT(_type="submit",_name = "prev", _value=T("Previous"), _id="prev"))

    if next:
        form[-1][-1][1].append(INPUT(_type="submit", _value=T("Next"), _name="next", _id="next"))

    if finish:
        form[-1][-1][1].append(INPUT(_type="submit", _value=T("Finish"), _name="finish", _id="finish"))
    return form


def transform_buttons(output,save = None, prev = None, next = None, finish = None, cancel=None):

    """ @todo: fix docstring, PEP8 """

    # fails when output is not HTML (e.g., JSON)
    if isinstance(output, dict):
        form = output.get("form", None)
        if form:
            add_buttons(form, save, prev, next, finish, cancel)
    return output


def has_dupe_questions(template_id, question_id):

    """ @todo: fix docstring, PEP8 """

    question_query = (db.survey_template_link.survey_template_id == template_id) \
    & (question_id == db.survey_template_link.survey_question_id)
    questions = db(question_query).select(db.survey_question.ALL)
    if len(questions) > 1:
        return True
    else:
        return False


def prune_questions(questions_id, questions, all_questions):

    """ @todo: fix docstring, PEP8 """

    if not questions_id:
        return # do nothing
    if not questions:
        return # nothing to act on.
    for question in all_questions:
        if not question in questions:
            question_query = (db.survey_template_link.survey_questions_id == questions_id) \
            & (question.id == db.survey_template_link.survey_question_id)
            db(question_query).delete()
            db.commit()
    return questions

def get_contained_questions(questions_id):

    """ @todo: fix docstring, PEP8 """

    question_query = (db.survey_template_link.survey_questions_id == questions_id) & \
        (db.survey_question.id == db.survey_template_link.survey_question_id) & \
        (db.survey_template.id == db.survey_template_link.survey_template_id)
    contained_questions = db(question_query).select(db.survey_question.ALL)
    return contained_questions

def get_table_for_template(template_id):
    """
        Returns the table for the given template and if it doesn't exist
        -- creates and returns that
    """

    # get the template first -- we need to get the table name
    template = db(db.survey_template.id == template_id).select().first()

    tbl = None

    if template: # avoid blow ups!
        fields = [Field("series_id", db.survey_series, writable=False, readable=False)
                  ] # A list of Fields representing the questions

        questions = db((db.survey_template_link.survey_template_id == template_id) & \
       (db.survey_question.id == db.survey_template_link.survey_question_id)).select(db.survey_question.ALL)
        # for each question, depending on its type create a Field
        for question in questions:
            question_type = question.question_type

            if question_type == 6: # Single TF -- simple for now -- will introduce more types later.
                fields.append(Field("question_%s" % (question.id), label=question.name))


            elif question_type  == 9:
                fields.append(Field("question_%s" % (question.id), "text", label=question.name))

            elif question_type == 10:
                fields.append(Field("question_%s" % (question.id), "integer", label=question.name))

            elif question_type == 11:
                fields.append(Field("question_%s" % (question.id), "date", label=question.name))

        tbl = db.define_table("survey_template_%s" % (template_id), uuidstamp, deletion_status, authorstamp, migrate=True, *fields)
        # now add the table name to the template record so we can reference it later.
        db(db.survey_template.id == template_id).update(table_name="survey_template_%s" % (template.id))
        db.commit()

        # set up onaccept for this table.
        def _onaccept(form):
            db(tbl.id == form.vars.id).update(series_id=request.vars.series_id)
            db.commit()

        s3xrc.model.configure(tbl,
                              onaccept=lambda form: _onaccept(form))
        # finally we return the newly created or existing table.
        return tbl

def shn_survey_action_buttons(r, deletable=True):

    """
        Over-ride the usual Action Buttons for Column views.
        Designed to be called from a postp
    """

    if r.component:
        args = [r.component_name, "[id]"]
    else:
        args = ["[id]"]
    if auth.is_logged_in():
        # Provide the ability to delete records in bulk
        if deletable:
            response.s3.actions = [
                dict(label=str(UPDATE), _class="action-btn", url=str(URL(r=request, args = args + ["update"]))),
                dict(label=str(DELETE), _class="action-btn", url=str(URL(r=request, args = args + ["delete"])))
            ]
        else:
            url = URL(r=request, f="table", vars={"series_id":args})
            response.s3.actions = [
                dict(label=str(UPDATE), _class="action-btn", url=str(URL(r=request, args = args + ["update"]))),
                dict(label="Answer", _class="action-btn", url=str(URL(r=request, f="table",args="create", vars={"series_id":"[id]"}))),
                dict(label="Results", _class="action-btn", url=str(URL(r=request, f="table", vars={"series_id":"[id]"}))) ]
    else:
        response.s3.actions = [
            dict(label=str(READ), _class="action-btn", url=str(URL(r=request, args = args)))
        ]

    return

# Unused code

#def section():
#    """ RESTful CRUD controller """
#    tablename = "%s_%s" % (prefix, resourcename)
#    table = db[tablename]
#    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#    table.name.requires = IS_NOT_EMPTY()
#    table.name.label = T("Survey Section Display Name")
#    table.description.label = T("Description")
#
#    # CRUD Strings
#    s3.crud_strings[tablename] = Storage(
#        title_create = T("Add Survey Section"),
#        title_display = T("Survey Section Details"),
#        title_list = T("List Survey Sections"),
#        title_update = T("Edit Survey Section"),
#        subtitle_create = T("Add New Survey Section"),
#        subtitle_list = T("Survey Section"),
#        label_list_button = T("List Survey Sections"),
#        label_create_button = T("Add Survey Section"),
#        label_delete_button = T("Delete Survey Section"),
#        msg_record_created = T("Survey Section added"),
#        msg_record_modified = T("Survey Section updated"),
#        msg_record_deleted = T("Survey Section deleted"),
#        msg_list_empty = T("No Survey Sections currently registered"))
#    output = s3_rest_controller(prefix, resourcename)
#
#    return transform_buttons(output, save=True, cancel=True)

#def question_options():
#    resourcename = "question"
#    tablename = "%s_%s" % (prefix, resourcename)
#    table = db[tablename]
#    table.uuid.requires = IS_NOT_IN_DB(db, "%s.uuid" % tablename)
#    table.tf_ta_columns.label = T("Number of Columns")
#    table.ta_rows.label = T("Number of Rows")
##    table.answer_choices.label = T("Answer Choices (One Per Line)")
#    table.aggregation_type.writable = False
#    table.aggregation_type.readable = False
##    table.row_choices.label = T("Row Choices (One Per Line)")
##    table.column_choices.label = T("Column Choices (One Per Line")
##    table.tf_choices.label = T("Text before each Text Field (One per line)")
#    output = s3_rest_controller(prefix, resourcename)
#    output.update(question_type=question_type)
#    return transform_buttons(output, prev=True, finish=True, cancel=True)

#def get_options_for_questions(template_id):
#        questions = db((db.survey_template_link.survey_template_id == template_id) & \
#        (db.survey_question.id == db.survey_template_link.survey_question_id)).select(db.survey_question.ALL)
#        opt_map = {}
#        for question in questions:
#            question_type = question.question_type
#            if question_type == 6: # Single TF -- simple for now -- will introduce more types later.
#                opt_map[question.id] = {"allow_comments":question.allow_comments,\
#                                         "comment_display_label":question.comment_display_label,\
#                                         "required":question.required}
#
#            elif question_type  == 9:
#                opt_map[question.id] = { "allow_comments":question.allow_comments,\
#                                         "comment_display_label":question.comment_display_label,\
#                                         "required":question.required}
#            elif question_type == 10:
#                opt_map[question.id] = {"allow_comments":question.allow_comments,\
#                                        "comment_display_label":question.comment_display_label,\
#                                        "required":question.required}
#
#            elif question_type == 11:
#                opt_map[question.id] = {"allow_comments":question.allow_comments,\
#                                        "comment_display_label":question.comment_display_label,\
#                                        "required":question.required}
#        return opt_map
