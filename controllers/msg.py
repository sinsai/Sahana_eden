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
	[T("Outbox"), False, URL(r=request, f="outbox")],#TODO
	[T("Distribution groups"), False, URL(r=request, f="group"), [
		[T("List/Add"), False, URL(r=request, f="group")],
		[T("Group Memberships"), False, URL(r=request, f="group_membership")],
	]],
    #["CAP", False, URL(r=request, f="tbc")]
]

# S3 framework functions
def index():
    "Module's Home Page"

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

def tbc():
    """ Coming soon... """
    return dict()

def tropo():
    """ https://www.tropo.com/docs/webapi/newhowitworks.htm """
    exec("from applications.%s.modules.tropo import Tropo, Session" % request.application)
    # Faster for Production (where app-name won't change):
    #from applications.eden.modules.tropo import Tropo, Session
    t = Tropo()
    
    if request.env.request_method == "POST":
        # This is their service contacting us, so parse their request
        s = Session(request.body.read())
        
        # If this is a response to a session request then send back the message again
        if "numberToDial" in s.parameters:
            t.call(to=s.parameters["numberToDial"], network=s.parameters["network"])
            t.say(s.parameters["message"])
            return t.RenderJson()
        else:
            # Otherwise place it in the InBox
            # @ToDo: For now dumping in a separate table
            uuid = s.parameters["id"]
            callerid = s.parameters["from"]
            destination = s.parameters["to"]
            message = s.parameters["initialText"]
            db.msg_tropo.insert(uuid=uuid, callerid=callerid, destination=destination, message=message)
            # Return a '200 OK'
            t.say(["Received!"])
            output = t.RenderJson()
            return output
    else:
        # This is us initiating an outbound request to their service, so parse our request
        try:
            tropo_service = request.args[0]
        except:
            session.error = T("Need to specify a service!")
            redirect(URL(r=request, f="index"))
        try:
            pe = request.args[1]
        except:
            session.error = T("Need to specify a person entity to send to!")
            redirect(URL(r=request, f="index"))
        try:
            # @ToDo We don't really need to redefine this again, as it's the same value...is there a more efficient way to check?
            pe_id = db(db.pr_pentity.pe_id == pe).select(db.pr_pentity.pe_id, limitby=(0, 1)).first().pe_id
        except:
            session.error = T("Person entity not found!")
            redirect(URL(r=request, f="index"))
        from urllib import urlencode
        from urllib2 import urlopen
        base_url = "http://api.tropo.com/1.0/sessions"
        action = "create"
        if tropo_service == "voice":
            token = db(db.msg_setting.id == 1).select(db.msg_setting.tropo_token_voice, limitby=(0, 1)).first().tropo_token_voice
            if not token:
                session.error = T("Need to configure a Voice Token!")
                redirect(URL(r=request, f="setting"))
            # Send the voice call
            pass
        else:
            #token = db(db.msg_setting.id == 1).select(db.msg_setting.tropo_token_messaging, limitby=(0, 1)).first().tropo_token_messaging
            token = db(db.msg_setting.id == 1).select(db.msg_setting.tropo_token_voice, limitby=(0, 1)).first().tropo_token_voice
            if not token:
                session.error = T("Need to configure a Messaging Token!")
                redirect(URL(r=request, f="setting"))
            # @ToDo Pull the message body from the msg_outbox
            message = "hello from the session API!"
            if tropo_service == "sms":
                network = "SMS"
                try:
                    # @ToDo: Handle multiple phone numbers
                    mobile = db((db.pr_pe_contact.pe_id == pe_id) & (db.pr_pe_contact.contact_method == 2)).select(db.pr_pe_contact.value, limitby=(0, 1)).first().value
                    number = msg.sanitise_phone(mobile)
                except:
                    session.error = T("No Mobile Phone set for this person entity!")
                    # @ToDo handle Groups
                    redirect(URL(r=request, c="pr", f="person", args=[pe_id, "pe_contact"]))
            elif tropo_service == "twitter":
                # tbc
                session.error = T("Unsupported Service!")
                redirect(URL(r=request, f="index"))
            elif tropo_service == "jabber":
                network = "JABBER"
                # tbc
                session.error = T("Unsupported Service!")
                redirect(URL(r=request, f="index"))
            else:
                session.error = T("Unknown Service!")
                redirect(URL(r=request, f="index"))
            params = urlencode([("action", action), ("token", token), ("network", network), ("numberToDial", number), ("message", message)])
            # Request Session
            # https://www.tropo.com/docs/webapi/sessionapi.htm
            xml = urlopen("%s?%s" % (base_url, params)).read()
            # Parse Response (actual message is sent as a response to the POST which will happen in parallel)
            root = etree.fromstring(xml)
            elements = root.getchildren()
            if elements[0].text == "false":
                session.error = T("Message sending failed! Reason:") + " " + elements[2].text
                redirect(URL(r=request, f="index"))
            else:
                session.flash = T("Message Sent")
                redirect(URL(r=request, f="index"))

@auth.shn_requires_membership(1)
def setting():
    """ Overall settings for the messaging framework """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    table.outgoing_sms_handler.label = T("Outgoing SMS handler")
    table.tropo_token_voice.label = T("Tropo Voice Token")
    table.tropo_token_messaging.label = T("Tropo Messaging Token")
    table.outgoing_sms_handler.comment = DIV(DIV(_class="tooltip",
        _title=T("Outgoing SMS Handler") + "|" + T("Selects whether to use the gateway or the Modem for sending out SMS")))
    table.tropo_token_voice.comment = DIV(DIV(_class="stickytip",
        _title=T("Tropo Voice Token") + "|" + T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>"))
    table.tropo_token_messaging.comment = DIV(DIV(_class="stickytip",
        _title=T("Tropo Messaging Token") + "|" + T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>"))
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
        label_delete_button = T("Delete Setting"),
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Messaging settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

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
        _title=T("Port") + "|" + T("For POP-3 this is usually 110 (995 for SSL), for IMAP this is usually 143 (993 for IMAP).")))
    table.inbound_mail_delete.comment = DIV(DIV(_class="tooltip",
            _title=T("Delete") + "|" + T("If this is set to True then mails will be deleted from the server after downloading.")))

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
    "RESTful CRUD controller"
    
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
        vars={"_next":URL(r=request, c="msg", f="group")}))

    module = "pr"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False

    # Do not show system groups
    response.s3.filter = (table.system == False)

    response.s3.pagination = True

    return shn_rest_controller(module, resource,
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

    module = "pr"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # Hide unnecessary fields
    table.description.readable = table.description.writable = False
    table.comments.readable = table.comments.writable = False
    table.group_head.readable = table.group_head.writable = False
    
    return shn_rest_controller(module, resource)

#-------------------------------------------------------------------------------

def pe_contact():
    """ Allows the user to add, update and delete their contacts"""
    
    if auth.is_logged_in() or auth.basic():
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        response.s3.filter = (db.pr_pe_contact.pe_id == person)
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, c="msg", f="pe_contact")}))

    module = "pr"
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    # These fields will be populated automatically
    table.name.writable = table.name.readable = False
    table.pe_id.writable = table.pe_id.readable = False
    table.person_name.writable = table.person_name.readable = False
    table.id.writable = False
#   table.id.readable = False

    def msg_pe_contact_onvalidation(form):
        """ This onvalidation method adds the person id to the record """
        person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
        form.vars.pe_id = person

    def msg_pe_contact_restrict_access(jr):
        """ The following restricts update and delete access to contacts not owned by the user """
        if jr.id :
            person = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
            if person == db(db.pr_pe_contact.id == jr.id).select(db.pr_pe_contact.pe_id, limitby=(0, 1)).first().pe_id :
                return True
            else:
                session.error = T("Access denied")
                return dict(bypass = True, output = redirect(URL(r=request)))
        else:
            return True
    s3xrc.model.configure(table,
            onvalidation=lambda form: msg_pe_contact_onvalidation(form))
    response.s3.prep = msg_pe_contact_restrict_access
    response.menu_options = []
    return shn_rest_controller(module, resource, listadd=True)

#-------------------------------------------------------------------------------

def search():
    """
        Do a search of groups which match a type
        Used for auto-completion
    """
    if auth.is_logged_in() or auth.basic():
        pass
    else:
        return

    import gluon.contrib.simplejson as json
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
		query = db((table1[field1].like("%" + value + "%")) & (table1.deleted == False)).select(db.pr_group.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field21].like("%" + value + "%")) & (table2.deleted == False)).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field22].like("%" + value + "%")) & (table2.deleted == False)).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		query = db((table2[field23].like("%" + value + "%")) & (table2.deleted == False)).select(db.pr_person.pe_id)
		for row in query:
			item.append({"id":row.pe_id, "name":shn_pentity_represent(row.pe_id, default_label = "")})
		item = json.dumps(item)
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
    """ Modem settings """
    
    try:
        import serial
    except ImportError:
        session.error = T("Python Serial module not available within the running Python - this needs installing to activate the Modem")
        redirect(URL(r=request, c="admin", f="index"))

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.modem_port.label = T("Port")
    table.modem_baud.label = T("Baud")
    table.modem_port.comment = DIV(DIV(_class="tooltip",
        _title=T("Port") + "|" + T("The serial port at which the modem is connected - /dev/ttyUSB0, etc on linux and com1, com2, etc on Windows")))
    table.modem_baud.comment = DIV(DIV(_class="tooltip",
        _title=T("Baud") + "|" + T("Baud rate to use for your modem - The default is safe for most cases")))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title=T("Enabled") + "|" + T("Unselect to disable the modem")))
    
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
        _title="URL|" + T("The URL of your web gateway without the post parameters")))
    table.parameters.comment = DIV(DIV(_class="tooltip",
        _title=T("Parameters") + "|" + T("The post variables other than the ones containing the message and the phone number")))
    table.message_variable.comment = DIV(DIV(_class="tooltip",
        _title=T("Message Variable") + "|" + T("The post variable on the URL used for sending messages")))
    table.to_variable.comment = DIV(DIV(_class="tooltip",
        _title=T("To variable") + "|" + T("The post variable containing the phone number")))
    table.enabled.comment = DIV(DIV(_class="tooltip",
        _title=T("Enabled") + "|" + T("Unselect to disable the modem")))

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
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def compose():

    return shn_msg_compose()

def outbox():
    "View the contents of the Outbox"

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

    table.message_id.label = T("Message")
    table.message_id.writable = False
    table.pe_id.readable = True
    table.pe_id.label = T("Recipient")
    
    # Subject works for Email but not SMS
    table.message_id.represent = lambda id: db(db.msg_log.id == id).select(db.msg_log.message, limitby=(0, 1)).first().message

    # CRUD Strings
    s3.crud_strings[tablename] = Storage(
        title_list = T("View Outbox"),
        title_update = T("Edit Message"),
        subtitle_list = T("Available Messages"),
        label_list_button = T("View Outbox"),
        label_delete_button = T("Delete Message"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No Messages currently in Outbox")
    )

    # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource, listadd=False)

# Enabled only for testing - the ticketing module should be the normal interface
# - although we should provide a menu item to that here...
@auth.shn_requires_membership(1)
def log():
    " RESTful CRUD controller "
    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    table.message.comment = SPAN("*", _class="req")
    table.priority.represent = lambda id: (
        [id and
            DIV(IMG(_src="/%s/static/img/priority/priority_%d.gif" % (request.application,id,), _height=12)) or
            DIV(IMG(_src="/%s/static/img/priority/priority_4.gif" % request.application), _height=12)
        ][0].xml())
    table.priority.label = T("Priority")
    # Add Auth Restrictions

    # CRUD Strings
    ADD_MESSAGE = T("Add Message")
    LIST_MESSAGES = T("List Messages")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MESSAGE,
        title_display = T("Message Details"),
        title_list = LIST_MESSAGES,
        title_update = T("Edit message"),
        title_search = T("Search messages"),
        subtitle_create = T("Send new message"),
        subtitle_list = T("Messages"),
        label_list_button = LIST_MESSAGES,
        label_create_button = ADD_MESSAGE,
        msg_record_created = T("Message added"),
        msg_record_modified = T("Message updated"),
        msg_record_deleted = T("Message deleted"),
        msg_list_empty = T("No messages in the system"))

    # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource, listadd=False)

# Enabled only for testing
@auth.shn_requires_membership(1)
def tag():
    " RESTful CRUD controller "
    resource = "tag"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    # Server-side Pagination
    response.s3.pagination = True
    
    return shn_rest_controller(module, resource, listadd=False)

