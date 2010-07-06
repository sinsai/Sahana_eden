# -*- coding: utf-8 -*-

"""
    Survey Module -- a tool to create survey.

    @author: Robert O'Connor
"""
from gluon.html import *

module = "survey"

# Will populate later on.
response.menu_options = None


def template():
    """ RESTlike CRUD controller """
    resource = "template"
    def _prep(jr):        
        crud.settings.create_next = URL(r=request, f="series", args=["create"])
        crud.settings.update_next = URL(r=request, f="series", args=["create"]) #TODO: NB this needs to be re-worked! 
        return True        
    response.s3.prep = _prep

    tablename = "%s_%s" % (module, resource)
    table = db[tablename]    
    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Name")
    table.name.comment = SPAN("*", _class="req")
    table.description.label = T("Description")
    
    
    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Survey Template"),
        title_display = T('Survey Template Details'),
        title_list = T("List Survey Templates"),
        title_update = T('Edit Survey Template'),
        subtitle_create = T('Add New Survey Template'),
        subtitle_list = T('Survey Templates'),
        label_list_button = T("List Survey Templates"),
        label_create_button = T("Add Survey Template"),
        msg_record_created = T('Survey Template added'),
        msg_record_modified = T('Survey Template updated'),
        msg_record_deleted = T('Survey Template deleted'),
        msg_list_empty = T('No Survey Template currently registered'))

    output = shn_rest_controller(module,resource,listadd=False)
    def _postp(jr):
        reponse.s3.template_id = jr.id
        return True
    response.s3.postp = _postp        

    if output:
        form = output.get("form", None)
        if form:
            addButtons(form,next=True)
    return output

def series():
    """ RESTlike CRUD controller """
    resource = "series"
    def _prep(jr):
        if "prev" in request.post_vars:
            if response.s3.template_id:
                crud.settings.create_next = jr.other(method="template",record_id=response.s3.template_id,representation=html)           
        return True
    response.s3.prep = _prep
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]    
    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Series Name")
    table.description.label = T("Description")
    table.survey_template_id.label = T("Survey Template")
    table.survey_template_id.requires = IS_NULL_OR(IS_ONE_OF(db, "survey_template.id", "%(name)s"))
    table.survey_template_id.represent = lambda id: (id and [db(db.survey_template.id==id).select()[0].name] or [""])[0]
    table.from_date.label = T("Start of Period")
    table.to_date.label = T("End of Period")    
    table.to_date.label = T("End of Period")    

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
        msg_record_created = T("Survey Series added"),
        msg_record_modified = T("Survey Series updated"),
        msg_record_deleted = T("Survey Series deleted"),
        msg_list_empty = T("No Survey Series currently registered"))


    output = shn_rest_controller(module, resource,listadd=False)    
    if output:
        form = output.get("form", None)
        if form:
            addButtons(form,next=True,prev=True)
    return output

def section():
    """ RESTlike CRUD controller """
    resource = "section"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.comment = SPAN("*", _class="req")
    table.name.label = T("Survey Section Display Name")
    table.description.label = T("Description")


    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Survey Section"),
        title_display = T("Survey Section Details"),
        title_list = T("List Survey Sections"),
        title_update = T("Edit Survey Section"),
        subtitle_create = T("Add New Survey Section"),
        subtitle_list = T("Survey Section"),
        label_list_button = T("List Survey Sections"),
        label_create_button = T("Add Survey Section"),
        msg_record_created = T("Survey Section added"),
        msg_record_modified = T("Survey Section updated"),
        msg_record_deleted = T("Survey Section deleted"),
        msg_list_empty = T("No Survey Sections currently registered"))
    output = shn_rest_controller(module, resource,listadd=False)
    if output:
        form = output.get("form", None)
        if form:
            addButtons(form,next=True,prev=True)
    return output


def question():
    # Question data, e.g., name,description, etc.
    resource = "question"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Question Display Name")
    table.name.comment = SPAN("*", _class="req")

    table.description.label = T("Description")

    question_types = {
        1:T("Multiple Choice (Only One Answer)"),
        2:T("Multiple Choice (Multiple Answers)"),
        3:T("Matrix of Choices (Only one answer)"),
        4:T("Matrix of Choices (Multiple Answers)"),
        5:T("Rating Scale"),
        6:T("Single Text Field"),
        7:T("Multiple Textboxes"),
        8:T("Comment/Essay Box"),
        9:T("Numerical Text Field"),
        10:T("Date and/or Time"),
        11:T("Image"),
        12:T("Descriptive Text (e.g., Prose, etc)"),
        13:T("Location"),
        14:T("Organisation"),
        15:T("Person"),
        16:T("Custom Database Resource (e.g., anything defined as a resource in Sahana)")
    }

    table.question_type.requires = IS_IN_SET(question_types)
    table.question_type.comment = SPAN("*", _class="req")

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Survey Question"),
        title_display = T("Survey Question Details"),
        title_list = T("List Survey Questions"),
        title_update = T("Edit Survey Question"),
        subtitle_create = T("Add New Survey Question"),
        subtitle_list = T("Survey Question'"),
        label_list_button = T("List Survey Questions"),
        label_create_button = T("Add Survey Question"),
        msg_record_created = T("Survey Question added"),
        msg_record_modified = T("Survey Question updated"),
        msg_record_deleted = T("Survey Question deleted"),
        msg_list_empty = T("No Survey Questions currently registered"))

    output = shn_rest_controller(module, resource,listadd=False)
    if output:
        form = output.get("form", None)
        if form:
            addButtons(form,next=True,prev=True)
    return output

def question_options():        
    if response.s3.question_id:
        question = db(db.survey_question.id == response.s3.question_id)
    resource = "question_options"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.question_id.readable = False
    table.question_id.writable = False
    table.tf_ta_columns.label = T("Number of Columns")
    table.ta_rows.label = T("Number of Rows")
    table.answer_choices.label = T("Answer Choices (One Per Line)")
    table.aggregation_type.writable = False
    table.aggregation_type.readable = False
    table.row_choices.label = T("Row Choices (One Per Line)")
    table.column_choices.label = T("Column Choices (One Per Line)")
    output = shn_rest_controller(module, resource,listadd=False)
    if output:
        form = output.get("form", None)
        if form:
            addButtons(form,finish=True,prev=True)
    return output

def addButtons(form, prev = None, next = None, finish = None,cancel=None):
    """
        Utility Function to reduce code duplication as this deals with:

        1) removing the save button
        2) adding the following: Cancel, Next, Previous and Finish(shown on the last step *ONLY*)
    """
    form[0][-1][1][0] = "" # remove the original Save Button
    if prev:
        form[0][-1][1].append(INPUT(_type="submit",_name = "prev",_value=T("Previous"), _id="prev"))
    if next:
        form[0][-1][1].append(INPUT(_type="submit", _value=T("Next"),_name="next",_id="next"))
    if finish:
        form[0][-1][1].append(INPUT(_type="submit", _value=T("Finish"),_name="finish",_id="finish"))
    return form