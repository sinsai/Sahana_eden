# -*- coding: utf-8 -*-

"""
    Survey Module -- a tool to create surveys.

    @author: Robert O'Connor
"""
from gluon.html import *

module = "survey"


# Will populate later on.
response.menu_options = None

def index():
    "Module's Home Page"
    module_name = deployment_settings.modules[module].name_nice    
    return dict(module_name=module_name)
def template():
    """ RESTlike CRUD controller """
    resource = "template"
    def _prep(jr):
        crud.settings.create_next = URL(r = request, c="survey", f="layout")
        crud.settings.update_next = URL(r = request, c="survey", f="layout")
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

    return transform_buttons(output,next=True,cancel=True)

def series():
    """ RESTlike CRUD controller """
    resource = "series"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]    
    table.uuid.requires = IS_NOT_IN_DB(db,"%s.uuid" % tablename)
    table.name.requires = IS_NOT_EMPTY()
    table.name.label = T("Survey Series Name")
    table.name.comment = SPAN("*", _class="req")
    table.description.label = T("Description")
    table.survey_template_id.label = T("Survey Template")
    table.survey_template_id.requires = IS_ONE_OF(db, "survey_template.id", "%(name)s")
    table.survey_template_id.represent = lambda id: (id and [db(db.survey_template.id==id).select()[0].name] or [""])[0]
    table.survey_template_id.comment = SPAN("*", _class="req")
    table.from_date.label = T("Start of Period")
    table.from_date.requires = IS_NOT_EMPTY()
    table.from_date.comment = SPAN("*", _class="req")    
    table.to_date.label = T("End of Period")    
    table.to_date.requires = IS_NOT_EMPTY()
    table.to_date.comment = SPAN("*", _class="req")



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

    return transform_buttons(output)
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

    return transform_buttons(output,save=True,cancel=True)


def question():
    # Question data, e.g., name,description, etc.
    resource = "question"
    def _prep(jr):
        if jr.method == "create":
            request.vars._next =  URL(r = request, f="question_options",args=["create"])
        elif jr.method == "update":
            request.vars._next =  URL(r = request, f="question_options",args=["update"])
        crud.settings.create_next = URL(r = request, f="question_options",args=["create"])
        crud.settings.update_next = URL(r = request, f="question_options", args=["update"])
        return True
    response.s3.prep = _prep
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
        7:T("Multiple Text Fields"),
#        8:T("Matrix of Text Fields"),
        9:T("Comment/Essay Box"),
        10:T("Numerical Text Field"),
        11:T("Date and/or Time"),
#        12:T("Image"),         
#        13:T("Descriptive Text (e.g., Prose, etc)"),
        14:T("Location"),
        15:T("Organisation"),
        16:T("Person"),
#        16:T("Custom Database Resource (e.g., anything defined as a resource in Sahana)")
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
    
    return transform_buttons(output,next=True,cancel=True)

def question_options():
    resource = "question_options"
    question_type = None
    question_id = session.rcvars.question_id   
    if session.rcvars and "survey_question" in session.rcvars:
        question = db(db.survey_question.id == session.rcvars.survey_question).select().first()
        question_type = question.question_type
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
    table.column_choices.label = T("Column Choices (One Per Line")
    table.tf_choices.label = T("Text before each Text Field (One per line)")
    id = db(table.id == question_id).select().first()
    output = shn_rest_controller(module, resource,listadd=False)
    output.update(question_type=question_type)
    return transform_buttons(output,prev=True,finish=True,cancel=True)

def layout():     
    """Deals with Rendering the survey editor"""    

    template_id = None
    section_rendered = []
    question_rendered = []
    if session.rcvars and "survey_template" in session.rcvars:
        template_id = session.rcvars["survey_template"]
    output = {}
    if template_id:
        output.update(template_id=template_id)
    question_list = {}
    # Get sections for this template.
    section_query = (db.survey_template_link_table.survey_template_id == template_id) & (db.survey_section.id == db.survey_template_link_table.survey_section_id)
    sections = db(section_query).select(db.survey_section.ALL)
    
    ui = DIV(_class="sections")    
    # build the UI
    for section in sections:
        section_rendered.append(section.id)
        link = A(section.name,_class="colorbox",_id="survey_section_%s" % (section.uuid),_href=URL(r=request, c="survey", f="section", args=[section.id, "update"], vars=dict(format="popup",caller="survey_section_%s" % (section.uuid))),
                                       _target="top",
                                       _title="Edit Section")

        ui.append(BR())

        if not section_rendered.count(section.id) > 1:
            ui.append(DIV(link,_class="section_title"))
        question_query = (db.survey_template_link_table.survey_section_id == section.id) & (db.survey_question.id == db.survey_template_link_table.survey_question_id)
        questions = db(question_query).select(db.survey_question.ALL)
        if not questions:
            ui.append(DIV(A (T("Add Question"),_href=URL(r=request,f="question")),_class="question_title"))
        for question in questions:
            question_rendered.append(question.id)
            if question_rendered.count(question.id) > 1:
                continue
            #TODO: take order into account.
            # MC (Only One Answer allowed)
            options = db(db.survey_question_options.question_id == question.id).select().first()
            ui.append(BR())           
            if question.question_type is 1:
                table = TABLE(_class="question")
                table_row = TR()
                if options:
                   answer_choices = options.answer_choices
                   if answer_choices:
                        choices = answer_choices.split("\r\n")
                        table_row.append(DIV(question.name))
                        for choice in choices:
                            table_row.append(TD((DIV(choice,INPUT(_type="radio",_name="%s" % (question.uuid)),_class="question_answer"))))
                        if options.allow_comments:
                            comment_text = options.comment_display_label
                            if comment_text:
                                table_row.append(TD(DIV(comment_text,TD(INPUT(_type="text",name="%s_comment" % (question.uuid))))))
                            else:
                                table_row.append(TD(DIV("Comments",TD(INPUT(_type="text",name="%s_comment" % (question.uuid))))))
                table.append(table_row)
                ui.append(table)
            elif question.question_type is 2: # MC (more than one answer)
                table,table_row = TABLE(_class="question"),TR()
                if options:
                   answer_choices = options.answer_choices
                   if answer_choices:
                        choices = answer_choices.split("\r\n")
                        table_row.append(TD(DIV(question.name)))
                        for choice in choices:
                            table_row.append(TD((DIV(choice,INPUT(_type="checkbox",_name="%s" % (question.uuid)),_class="question_answer"))))
                        if options.allow_comments:
                            comment_text = options.comment_display_label                            
                            table_row.append(TD(DIV((INPUT(_type="checkbox"),comment_text,TD(INPUT(_type="text",name="%s_comment" % (question.uuid)))))))
                table.append(table_row)
                ui.append(table)
            elif question.question_type is 3:
                table,table_row = TABLE(_class="question"),TR()
                thead = THEAD()
                tbody = TBODY()
                column_choices = options.column_choices
                c_choices = column_choices.split("\r\n")
                if c_choices:
                    table_row.append(DIV(question.name,_class="question"))
                    table.append(table_row)                    
                    thead.append(table_row.append(TH(XML("&nbsp;"),_style="width:20%;")))
                    for choice in c_choices: 
                        table_row.append(TH(choice,_scope="col",_style="width:16%;"))
                    thead.append(table_row)
                    num_columns = len(c_choices)
                    row_choices = options.row_choices
                    r_choices = row_choices.split("\r\n")                    
                    for row in r_choices:
                        table_row = TR()
                        table_row.append(TH(row,_scope="row",_align="left"))
                        for i in range(num_columns):
                            table_row.append(TD(INPUT(_type="radio"),_align="center"))
                    tbody.append(table_row)
                    table.append(tbody)
            elif question.question_type == 4:
                table,table_row = TABLE(_class="question"),TR()
                thead = THEAD()
                tbody = TBODY()
                column_choices = options.column_choices
                c_choices = column_choices.split("\r\n")
                if c_choices:
                    table_row.append(DIV(question.name))
                    table.append(table_row)
                    thead.append(table_row.append(TH(XML("&nbsp;"),_style="width:20%;")))
                    for choice in c_choices:
                        table_row.append(TH(choice,_scope="col",_style="width:16%;"))
                    thead.append(table_row)
                    num_columns = len(c_choices)
                    row_choices = options.row_choices
                    r_choices = row_choices.split("\r\n")
                    for row in r_choices:
                        table_row = TR()
                        table_row.append(TH(row,_scope="row",_align="left"))
                        for i in range(num_columns):
                            table_row.append(TD(INPUT(_type="checkbox"),_align="center"))                    
                    tbody.append(table_row)
                    table.append(tbody)
            elif question.question_type == 5: #TODO: rating question -- take weights into account.
                table = TABLE(_class="question")
                thead = THEAD()
                tbody = TBODY()
                column_choices = options.column_choices
                c_choices = column_choices.split("\r\n")
                if c_choices:
                    table_row = TR()
                    table_row.append(DIV(question.name,_class="question"))
                    table.append(table_row)
                    thead.append(table_row.append(TH(XML("&nbsp;"),_style="width:20%;")))
                    for choice in c_choices:
                        table_row.append(TH(choice,_scope="col",_style="width:16%;"))
                    thead.append(table_row)
                    num_columns = len(c_choices)
                    row_choices = options.row_choices
                    r_choices = row_choices.split("\r\n")
                    for row in r_choices:
                        table_row = TR()
                        table_row.append(TH(row,_scope="row",_align="left"))
                        for i in range(num_columns):
                            table_row.append(TD(INPUT(_type="radio",_align="center")))
                    tbody.append(table_row)
                    table.append(tbody)
            elif question.question_type == 6:
                table,table_row = TABLE(_class="question"), TR()
                table_row.append(DIV(question.name))
                table_row.append(TD(DIV(DIV("%s " % (question.name),TD(INPUT()),_class="question_answer"))))
                if options.allow_comments:
                     comment_text = options.comment_display_label
                     if comment_text:
                         table_row.append(TD(DIV(DIV("%s: " % (comment_text),TD(INPUT())))))
                     else:
                         table_row.append(TD(DIV(DIV("Comments: ",TD(INPUT())))))
                table.append(table_row)

                ui.append(table)

            elif question.question_type == 7:
                table = TABLE(_class="question")
                tf_choices = options.tf_choices
                choices = tf_choices.split("\r\n")
                columns = options.tf_ta_columns # for now this isn't customizable on a TF by TF basis -- I have some ideas as to how to accomplish this.
                table.append(TR(TD(DIV(question.name))))
                for choice in choices:
                    table_row = TR()
                    table_row.append(TD(DIV(choice),TD(INPUT(_size="%s" % (columns)))))
                    table.append(table_row)
                ui.append(table)
            elif question.question_type == 8:
                pass # Deferred "Matrix of Text Fields" -- handy data type but not necessary for the first pass.
            elif question.question_type == 9:
                table = TABLE()
                columns = options.tf_ta_columns
                rows = options.ta_rows
                table_row = TR()
                table_row.append(DIV(question.name))
                table_row.append(TEXTAREA(_rows="%s", _columns="%s" % (rows,columns)))
            elif question.question_type == 10:
               table,table_row = TABLE(_class="question"), TR()
               table_row.append(DIV(question.name))
               table_row.append((INPUT())) 
               if options.allow_comments:
                    comment_text = options.comment_display_label
                    if comment_text:
                        table_row.append(TD(DIV(DIV("%s: " % (comment_text),TD(INPUT())))))
                    else:
                        table_row.append(TD(DIV(DIV("Comments: ",TD(INPUT())))))
               table.append(table_row)

               ui.append(table)
            elif question.question_type == 11:     
               table,table_row = TABLE(_class="question"), TR()
               table_row.append(DIV(question.name))
               table_row.append((INPUT(_class="date"))) # Date/Time
               if options.allow_comments:
                    comment_text = options.comment_display_label
                    if comment_text:
                        table_row.append(TD(DIV(DIV("%s: " % (comment_text),TD(INPUT())))))
                    else:
                        table_row.append(TD(DIV(DIV("Comments: ",TD(INPUT())))))
               table.append(table_row)

               ui.append(table)

            elif question.question_type == 12:
                pass # deferred -- "Image"
            elif question.question_type == 13:
                pass # deferred "Descriptive read-only text"
            elif question.question_type == 14:
                pass # Location
            elif question.question_type == 15:
                pass # Organisation
            elif question.question_type == 16:
                pass # Person
            else:
                pass # Uh-oh -- something went wrong

    ui.append(BR())
    if sections:
        ui.append(DIV(DIV(A (T("Add Question"), _class="colorbox",_href=URL(r=request,f="question",args=["create"],vars=dict(format="popup")), ),_class="question_title")))
    ui.append(BR())

    ui.append(DIV(A(T("Add Section"),_class="colorbox",
                                       _href=URL(r=request, f="section", args=["create"], vars=dict(format="popup")),
                                       _target="top",
                                       _title=T("Add Section")),_class="section_title"))
    output.update(ui=ui)
    return output
    

def add_buttons(form, save = None, prev = None, next = None, finish = None,cancel=None):
    """
        Utility Function to reduce code duplication as this deals with:

        1) removing the save button
        2) adding the following: Cancel, Next, Previous and Finish(shown on the last step *ONLY*)
    """
    form[0][-1][1][0] = "" # remove the original Save Button
    if save:
        form[-1][-1][1].append(INPUT(_type="submit",_name = "save",_value=T("Save"), _id="save"))

    if cancel:
        form[-1][-1][1].append(INPUT(_type="button",_name = "cancel",_value=T("Cancel"), _id="cancel"))

    if prev:
        form[-1][-1][1].append(INPUT(_type="submit",_name = "prev",_value=T("Previous"), _id="prev"))

    if next:
        form[-1][-1][1].append(INPUT(_type="submit", _value=T("Next"),_name="next",_id="next"))

    if finish:
        form[-1][-1][1].append(INPUT(_type="submit", _value=T("Finish"),_name="finish",_id="finish"))
    return form

def transform_buttons(output,save = None, prev = None, next = None, finish = None,cancel=None,extra=None):
    # fails when output is not HTML (e.g., JSON)
    if isinstance(output, dict):
        form = output.get("form",None)
        if form:
            add_buttons(form,save,prev,next,finish,cancel)
    return output

def check_comments(allow_comments,text):
    ret = None
    if allow_comments:
        ret = DIV(text,INPUT())
    return ret    