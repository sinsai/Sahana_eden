# -*- coding: utf-8 -*-

"""
    Messaging Module - Controllers
"""

module = request.controller

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
response.menu_options = [
	[T("Compose"), False, URL(r=request, c="msg", f="compose")],
	#[T("Outbox"), False, URL(r=request, f="outbox")],#TODO
	[T("Distribution groups"), False, URL(r=request, f="group"), [
		[T("List/Add"), False, URL(r=request, f="group")],
		[T("Group Memberships"), False, URL(r=request, f="group_membership")],
	]],
    #[T("CAP"), False, URL(r=request, f="tbc")]
]

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

def tbc():
    """ Coming soon... """
    return dict()

def email_settings():
    """ RESTful CRUD controller for email settings - appears in the administration menu """
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.inbound_mail_server.label = T("Server")
    table.inbound_mail_type.label = T("Type")
    table.inbound_mail_ssl.label = "SSL"
    table.inbound_mail_port.label = T("Port")
    table.inbound_mail_username.label = T("Username")
    table.inbound_mail_password.label = T("Password")
    table.inbound_mail_delete.label = T("Delete from Server?")
    table.inbound_mail_port.comment = DIV(DIV(_class="tooltip",
        _title=T("Port|For POP-3 this is usually 110 (995 for SSL), for IMAP \
            this is usually 143 (993 for IMAP).")))
    table.inbound_mail_delete.comment = DIV(DIV(_class="tooltip",
            _title=T("Delete|If this is set to True then mails will be \
            deleted from the server after downloading.")))

    if not auth.has_membership(auth.id_group("Administrator")):
		session.error = UNAUTHORISED
		redirect(URL(r=request, f="index"))
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Email Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Email settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )
    
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, "email_settings", listadd=False, deletable=False)

#--------------------------------------------------------------------------------------------------

# The following 2 functions hook into the pr functions
# -----------------------------------------------------------------------------
def group():
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
        vars={"_next":URL(r=request, c="msg", f="group")}))
    resource = request.function

    db.pr_group.description.readable = False
    db.pr_group.description.writable = False

    response.s3.filter = (db.pr_group.system == False) # do not show system groups
    response.s3.pagination = True
    "RESTful CRUD controller"
    return shn_rest_controller("pr", resource,
                               main="name",
                               extra="description",
                               rheader=shn_pr_rheader,
                               deletable=False)
# -----------------------------------------------------------------------------
def group_membership():
    "RESTful CRUD controller"
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
        vars={"_next":URL(r=request, c="msg", f="group_membership")}))

    db.pr_group_membership.description.readable = False
    db.pr_group_membership.description.writable = False
    
    db.pr_group_membership.comment.readable = False
    db.pr_group_membership.comment.writable = False
    
    db.pr_group_membership.group_head.readable = False
    db.pr_group_membership.group_head.writable = False
    
    
    resource = request.function
    return shn_rest_controller("pr", resource)

#-------------------------------------------------------------------------------

def pe_contact():
    """ Allows the user to add,update and delete his contacts"""
    
    if auth.is_logged_in() or auth.basic():
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        response.s3.filter = (db.pr_pe_contact.pe_id == person)
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, c="msg", f="pe_contact")}))

    db.pr_pe_contact.name.writable = False
    db.pr_pe_contact.name.readable = False
    db.pr_pe_contact.id.writable = False
#   db.pr_pe_contact.id.readable = False
    db.pr_pe_contact.pe_id.writable = False
    db.pr_pe_contact.pe_id.readable = False
    db.pr_pe_contact.person_name.writable = False
    db.pr_pe_contact.person_name.readable = False
    def msg_pe_contact_onvalidation(form):
        """This onvalidation method adds the person id to the record"""
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        form.vars.pe_id = person
    def msg_pe_contact_restrict_access(jr):
        """The following restricts update and delete access to contacts not
        owned by the user"""
        if jr.id :
            person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
            if person == db(db.pr_pe_contact.id == jr.id).select(db.pr_pe_contact.pe_id, limitby=(0, 1)).first().pe_id :
                return True
            else:
                session.error = T("Access denied")
                return dict(bypass = True, output = redirect(URL(r=request)))
        else:
            return True
    s3xrc.model.configure(db.pr_pe_contact,
            onvalidation=lambda form: msg_pe_contact_onvalidation(form))
    response.s3.prep = msg_pe_contact_restrict_access
    response.menu_options = []
    return shn_rest_controller("pr", "pe_contact", listadd=True)

#-------------------------------------------------------------------------------

def search():
    """Do a search of groups which match a type
    Used for auto-completion
    """
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        return

    import gluon.contrib.simplejson as sj
    table1 = db.pr_group
    field1 = "name"
    table2 = db.pr_person
    field21 = "first_name"
    field22 = "middle_name"
    field23 = "last_name"
    # JQuery Autocomplete uses 'q' instead of 'value'
    value = request.vars.q
    if value:
		item = []
		query = db((table1[field1].like("%" + value + "%"))).select(db.pr_group.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field21].like("%" + value + "%"))).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field22].like("%" + value + "%"))).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field23].like("%" + value + "%"))).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		item = sj.dumps(item)
		response.view = "xml.html"
		return dict(item=item)
    return


def process_sms_via_api():
	"Controller for SMS api processing - to be called via cron"
	msg.process_outbox(contact_method = 2)
	return

def process_email_via_api():
	"Controller for Email api processing - to be called via cron"
	msg.process_outbox(contact_method = 1)
	return

#-------------------------------------------------------------------------------

@auth.shn_requires_membership(1)
def modem_settings():
    "Modem settings"
    try:
        import serial
    except ImportError:
        session.error = T("Python Serial module not available within the\
        Python - this needs installing to activate the Modem")
        redirect(URL(r=request, c="admin", f="index"))
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.modem_port.label = T("Port")
    table.modem_baud.label = T("Baud")
    table.modem_port.comment = DIV(DIV(_class="tooltip",
        _title=T("Port|The serial port at which the modem is connected -\
            /dev/ttyUSB0, etc on linux and com1, com2, etc on Windows")))
    table.modem_baud.comment = DIV(DIV(_class="tooltip",
        _title=T("Baud|Baud rate to use for your modem - The default is safe\
            for most cases")))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title=T("Enabled|Unselect to disable the modem")))
    
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Modem Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Modem settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False,
    listadd=False)

@auth.shn_requires_membership(1)
def gateway_settings():
    """ Gateway settings """
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.url.label = "URL"
    table.to_variable.label = T("To variable")
    table.message_variable.label = T("Message variable")
    table.url.comment = DIV(DIV(_class="tooltip",
        _title=T("URL|The URL of your web gateway without the post parameters")))
    table.parameters.comment = DIV(DIV(_class="tooltip",
        _title=T("Parameters|The post variables other than the ones containing\
            the message and the phone number")))
    table.message_variable.comment = DIV(DIV(_class="tooltip",
        _title=T("Message Variable|The post variable on the URL used for\
        sending messages")))
    table.to_variable.comment = DIV(DIV(_class="tooltip",
        _title=T("To variable|The post variable containing the phone number")))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title=T("Enabled|Unselect to disable the modem")))

    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Gateway Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Gateway settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False,
    listadd=False)

@auth.shn_requires_membership(1)
def setting():
    "Overall settings for the messaging framework"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    table.outgoing_sms_handler.label = T("Outgoing SMS handler")
    table.outgoing_sms_handler.comment = DIV(DIV(_class="tooltip",
    _title=T("Outgoing SMS handler|Selects whether to use the gateway or the Modem for sending out SMS")))
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
    title_create = ADD_SETTING,
    title_display = T("Setting Details"),
    title_list = VIEW_SETTINGS,
    title_update = T("Edit Messaging Settings"),
    title_search = T("Search Settings"),
    subtitle_list = T("Settings"),
    label_list_button = VIEW_SETTINGS,
    label_create_button = ADD_SETTING,
    msg_record_created = T("Setting added"),
    msg_record_modified = T("Messaging settings updated"),
    msg_record_deleted = T("Setting deleted"),
    msg_list_empty = T("No Settings currently defined")
    )
    
    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False,
    listadd=False)

@auth.shn_requires_membership(1) #Enabled only for testing
def log():
    " RESTful CRUD controller "
    resource = 'log'
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    table.message.comment = SPAN("*", _class="req")
    table.priority.represent = lambda id: (
        [id and
            DIV(IMG(_src='/%s/static/img/priority/priority_%d.gif' % (request.application,id,), _height=12)) or
            DIV(IMG(_src='/%s/static/img/priority/priority_4.gif' % request.application), _height=12)
        ][0].xml())
    table.priority.label = T('Priority')
    # Add Auth Restrictions

    # CRUD Strings
    ADD_MESSAGE = T('Add Message')
    LIST_MESSAGES = T('List Messages')
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MESSAGE,
        title_display = T('Message Ddetails'),
        title_list = LIST_MESSAGES,
        title_update = T('Edit message'),
        title_search = T('Search messages'),
        subtitle_create = T('Send new message'),
        subtitle_list = T('Messages'),
        label_list_button = LIST_MESSAGES,
        label_create_button = ADD_MESSAGE,
        msg_record_created = T('Message added'),
        msg_record_modified = T('Message updated'),
        msg_record_deleted = T('Message deleted'),
        msg_list_empty = T('No messages in the system '))

    # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource,
        listadd=False,
        )

@auth.shn_requires_membership(1) #Enabled only for testing
def tag():
    " RESTful CRUD controller "
    resource = 'tag'
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    # Server-side Pagination
    response.s3.pagination = True
    
    return shn_rest_controller(module, resource,
    listadd=False,
    )

def compose():
    " Message Compose page"
    resource1 = 'log'
    tablename1 = module + "_" + resource1
    table1 = db[tablename1]
    resource2 = 'outbox'
    tablename2 = module + "_" + resource2
    table2 = db[tablename2]

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, c="msg", f="compose")}))

    # Model options
    table1.sender.writable = False
    table1.sender.readable = False
    table1.fromaddress.writable = False
    table1.fromaddress.readable = False
    table1.pe_id.writable = False
    table1.pe_id.readable = False
    table1.verified.writable = False
    table1.verified.readable = False
    table1.verified_comments.writable = False
    table1.verified_comments.readable = False
    table1.actioned.writable = False
    table1.actioned.readable = False
    table1.actionable.writable = False
    table1.actionable.readable = False
    table1.actioned_comments.writable = False
    table1.actioned_comments.readable = False
    table1.subject.label = T('Subject')
    table1.message.label = T('Message')
    table1.priority.label = T('Priority')
    table2.pe_id.label = T('Recipients')


    def compose_onvalidation(form):
        """This onvalidation sets the sender and uses msg.send_by_pe_id to route the message"""
        if not request.vars.pe_id:
            session.error = T('Please enter the recipient')
            redirect(URL(r=request,c="msg", f="compose"))
        sender_pe_id = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        if msg.send_by_pe_id(request.vars.pe_id,
                                request.vars.subject,
                                request.vars.message,
                                sender_pe_id,
                                request.vars.pr_message_method):
                                    session.flash = T('Message sent to outbox')
                                    redirect(URL(r=request, c="msg", f="compose"))
        else:
            session.error = T('Error in message')
            redirect(URL(r=request,c="msg", f="compose"))


    logform = crud.create(table1, 
                            onvalidation = compose_onvalidation)
    outboxform = crud.create(table2)
    
    return dict(logform = logform, outboxform = outboxform, title = T('Send Message'))
