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
    [T("Distribution groups"), False, URL(r=request, f="group"), [
        [T("List/Add"), False, URL(r=request, f="group")],
        [T("Group Memberships"), False, URL(r=request, f="group_membership")],
    ]],
    [T("Log"), False, URL(r=request, f="log")],
    [T("Outbox"), False, URL(r=request, f="outbox")],
    [T("Search Tags"), False,URL(r=request, f="twitter_search"),[
        [T("List/Add"), False, URL(r=request, f="twitter_search")],
    ]],
    [T("Tweet Results"), False, URL(r=request, f="search_results")]
    
    #["CAP", False, URL(r=request, f="tbc")]
]

# S3 framework functions
def index():
    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice

    return dict(module_name=module_name)

def tbc():
    """ Coming soon... """
    return dict()

#-------------------------------------------------------------------------------
def compose():

    return shn_msg_compose()

#--------------------------------------
def process_email_via_api():
    """ Controller for Email api processing - to be called via cron """

    msg.process_outbox(contact_method = 1)
    return

def process_sms_via_api():
    """ Controller for SMS api processing - to be called via cron """

    msg.process_outbox(contact_method = 2)
    return

def process_sms_via_tropo():
    """ Controller for SMS tropo processing - to be called via cron """

    msg.process_outbox(contact_method = 2, option = 3)
    return

def process_text_via_twitter():
    """ Controller for twitter message processing - to be called via cron """

    msg.process_outbox(contact_method = 4) # 3 is reserved for XMPP
    return
    
def search_results():
    """ Controller to retrieve real time tweets for user saved search queries - to be called via cron """
    
    result = msg.receive_subscribed_tweets()
    
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

     # Server-side Pagination
    response.s3.pagination = True
    rheader = DIV(B(T("Master Message Log")), ": ", T(str(result)))
    return shn_rest_controller(module, resource, listadd=True, rheader = rheader)    
  
        
#----------------------------------------------------------------------------------------    
def twitter_search():
    """Controller to show/add the user's twitter search queries"""
    
    if not auth.shn_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(r=request, c="default", f="user", args="login"))

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]

     # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource, listadd=True)
       
#-------------------------------------------------------------------------------
def outbox():
    """ View the contents of the Outbox """

    if not auth.shn_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(r=request, c="default", f="user", args="login"))

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

def log():
    """ RESTful CRUD controller """

    if not auth.shn_logged_in():
        session.error = T("Requires Login!")
        redirect(URL(r=request, c="default", f="user", args="login"))

    resource = request.function
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]

    # Model options
    table.message.comment = SPAN("*", _class="req")
    #table.priority.represent = lambda id: (
    #    [id and
    #        DIV(IMG(_src="/%s/static/img/priority/priority_%d.gif" % (request.application,id,), _height=12)) or
    #        DIV(IMG(_src="/%s/static/img/priority/priority_4.gif" % request.application), _height=12)
    #    ][0].xml())

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

    rheader = DIV(B(T("Master Message Log")), ": ", T("All Inbound & Outbound Messages are stored here"))

    # Server-side Pagination
    response.s3.pagination = True

    return shn_rest_controller(module, resource, listadd=False, rheader=rheader)

def tropo():
    """
        Receive a JSON POST from the Tropo WebAPI
        https://www.tropo.com/docs/webapi/newhowitworks.htm
    """
    exec("from applications.%s.modules.tropo import Tropo, Session" % request.application)
    # Faster for Production (where app-name won't change):
    #from applications.eden.modules.tropo import Tropo, Session
    try:
        s = Session(request.body.read())
        t = Tropo()
        # This is their service contacting us, so parse their request
        try:
            row_id = s.parameters["row_id"]
            # This is an Outbound message which we've requested Tropo to send for us
            table = db.msg_tropo_scratch
            query = (table.row_id == row_id)
            row = db(query).select().first() 
            # Send the message
            #t.message(say_obj={"say":{"value":row.message}},to=row.recipient,network=row.network)
            t.call(to=row.recipient, network=row.network)
            t.say(row.message)
            # Update status to sent in Outbox
            db(db.msg_outbox.id == row.row_id).update(status=2)
            # Set message log to actioned
            db(db.msg_log.id == row.message_id).update(actioned=True)
            # Clear the Scratchpad
            db(query).delete()
            return t.RenderJson()
        except:
            # This is an Inbound message
            try:
                message = s.initialText
                # This is an SMS/IM
                # Place it in the InBox
                uuid = s.id
                recipient = s.to["id"]
                try:
                    fromaddress = s.fromaddress["id"]
                except:
                    # SyntaxError: s.from => invalid syntax (why!?)
                    fromaddress = ""
                db.msg_log.insert(uuid=uuid, fromaddress=fromaddress, recipient=recipient, message=message, inbound=True)
                # Send the message to the parser
                reply = parserdooth(message)
                t.say([reply])
                return t.RenderJson()
            except:
                # This is a Voice call
                # - we can't handle these yet
                raise HTTP(501)
    except:
        # GET request or some random POST
        pass

#--------------------------------------
# Parser
def parserdooth(message):
    """ 
        This function hopes to grow into a full fledged page that offers customizable routing with keywords
        Dooth = Messenger 
    """
    import difflib
    import string

    primary_keywords = ["get", "give", "show"] # Equivalent keywords in one list
    contact_keywords = ["email", "mobile", "facility", "clinical", "security", "phone", "status", "hospital", "person", "organisation"]
    keywords = string.split(message)
    query = []
    name = ""
    reply = ""
    for word in keywords:
        match = difflib.get_close_matches(word, primary_keywords + contact_keywords)
        if match:
            query.append(match[0])
        else:
            name = word

#   ------------ Person Search [get name person phone email]------------
    if "person" in query:
        result = person_search(name)
    
        if len(result) > 1:
            return "Multiple Matches"
        if len(result) == 1:
            if "Person" in result[0]["name"]:
                reply = result[0]["name"]
                table3 = db.pr_pe_contact
                if "email" in query:
                    query = (table3.pe_id == result[0]["id"]) & (table3.contact_method == 1)
                    recipient = db(query).select(table3.value, orderby = table3.priority, limitby=(0, 1)).first()
                    reply = reply + " Email->" + recipient.value
                if "mobile" in query:
                    query = (table3.pe_id == result[0]["id"]) & (table3.contact_method == 2)
                    recipient = db(query).select(table3.value, orderby = table3.priority, limitby=(0, 1)).first()
                    reply = reply + " Mobile->" + str(recipient.value)
        if len(reply) == 0:
            return "No Match"

        return reply

#   -------------Hospital Search [example: get name hospital facility status ] --------------
    if "hospital" in query:
        table = db.hms_hospital
        result = s3xrc.search_simple(table,fields=["name"],label = str(name))
        if len(result) > 1:
            return "Multiple Matches"
    
        if len(result) == 1:
            hospital = db(table.id == result[0]).select().first()
            reply = reply + " " + hospital.name + "(Hospital) "
            if "phone" in query:
                reply = reply + "Phone->" + str(hospital.phone_emergency)
            if "facility" in query:
                reply = reply + "Facility status " + str(table.facility_status.represent(hospital.facility_status))
            if "clinical" in query:
                reply = reply + "Clinical status " + str(table.facility_status.represent(hospital.clinical_status))
            if "security" in query:
                reply = reply + "Security status " + str(table.facility_status.represent(hospital.security_status))
        if len(reply) == 0:
            return "No Match"

        return reply

#   -----------------Organisation search [example: get name organisation phone]------------------------------
    if "organisation" in query:
        table = db.org_organisation
        result = s3xrc.search_simple(table, fields=["name"], label = str(name))
        if len(result) > 1:
            return "Multiple Matches"

        if len(result) == 1:
            organisation = db(table.id == result[0]).select().first()
            reply = reply + " " + organisation.name + "(Organisation) "
            if "phone" in query:
                reply = reply + "Phone->" + str(organisation.donation_phone)
        if len(reply) == 0:
            return "No Match"

        return reply

    return "Please provide one of the keywords - person, hospital, organisation"

#--------------------------------------
@auth.shn_requires_membership(1)
def setting():
    """ Overall settings for the messaging framework """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    table.outgoing_sms_handler.label = T("Outgoing SMS handler")
    table.outgoing_sms_handler.comment = DIV(DIV(_class="tooltip",
        _title=T("Outgoing SMS Handler") + "|" + T("Selects whether to use a Modem, Tropo or other Gateway for sending out SMS")))
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

#--------------------------------------
@auth.shn_requires_membership(1)
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

#-------------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def modem_settings():
    """ RESTful CRUD controller for modem settings - appears in the administration menu """
    
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

#-------------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def gateway_settings():
    """ RESTful CRUD controller for gateway settings - appears in the administration menu """

    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    
    table.url.label = T("URL")
    table.to_variable.label = T("To variable")
    table.message_variable.label = T("Message variable")
    table.url.comment = DIV(DIV(_class="tooltip",
        _title=T("URL") + "|" + T("The URL of your web gateway without the post parameters")))
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

#-------------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def tropo_settings():
    """ RESTful CRUD controller for Tropo settings - appears in the administration menu """
    resource = request.function
    tablename = module + "_" + resource
    table = db[tablename]
    table.token_messaging.label = T("Tropo Messaging Token")
    table.token_messaging.comment = DIV(DIV(_class="stickytip",_title=T("Tropo Messaging Token") + "|" + T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>"))
    #table.token_voice.label = T("Tropo Voice Token")
    #table.token_voice.comment = DIV(DIV(_class="stickytip",_title=T("Tropo Voice Token") + "|" + T("The token associated with this application on") + " <a href='https://www.tropo.com/docs/scripting/troposessionapi.htm' target=_blank>Tropo.com</a>"))
    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Edit Tropo Settings"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("Tropo settings updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )

    crud.settings.update_next = URL(r=request, args=[1, "update"])
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

#-------------------------------------------------------------------------------
@auth.shn_requires_membership(1)
def twitter_settings():
    """ RESTful CRUD controller for Twitter settings - appears in the administration menu """

    # CRUD Strings
    ADD_SETTING = T("Add Setting")
    VIEW_SETTINGS = T("View Settings")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_SETTING,
        title_display = T("Setting Details"),
        title_list = VIEW_SETTINGS,
        title_update = T("Authenticate system's Twitter account"),
        title_search = T("Search Settings"),
        subtitle_list = T("Settings"),
        label_list_button = VIEW_SETTINGS,
        label_create_button = ADD_SETTING,
        msg_record_created = T("Setting added"),
        msg_record_modified = T("System's Twitter account updated"),
        msg_record_deleted = T("Setting deleted"),
        msg_list_empty = T("No Settings currently defined")
    )
    
    def prep(jr):
        try:
            import tweepy
        except:
            session.error = T("Couldn't import tweepy library")
            return True
        if not (deployment_settings.twitter.oauth_consumer_key and deployment_settings.twitter.oauth_consumer_secret):
            session.error = T("You should edit Twitter settings in models/000_config.py")
            return True
        oauth = tweepy.OAuthHandler(deployment_settings.twitter.oauth_consumer_key,
                                    deployment_settings.twitter.oauth_consumer_secret)

        resource = request.function
        tablename = module + "_" + resource
        table = db[tablename]

        if jr.http == "GET" and jr.method in ["create", "update"]:
            # We're showing the form
            try:
                session.s3.twitter_oauth_url = oauth.get_authorization_url()
                session.s3.twitter_request_key = oauth.request_token.key
                session.s3.twitter_request_secret = oauth.request_token.secret
            except tweepy.TweepError:
                session.error = T("problem connecting to twitter.com - please refresh")
                return True
            table.pin.readable = True
            table.pin.label = SPAN(T("PIN number "),
                A(T("from Twitter"), _href=T(session.s3.twitter_oauth_url), _target="_blank"),
                T(" (leave empty to detach account)"))
            table.pin.value = ""
            table.twitter_account.label = T("Current Twitter account")
            return True
        else:
            # Not showing form, no need for pin
            table.pin.readable = False
            table.pin.label = T("PIN") # won't be seen
            table.pin.value = ""       # but let's be on the safe side
        return True
    response.s3.prep = prep
    
    response.menu_options = admin_menu_options
    return shn_rest_controller(module, "twitter_settings", listadd=False, deletable=False)


#--------------------------------------------------------------------------------------------------
# The following 2 functions hook into the pr functions
# -----------------------------------------------------------------------------
def group():
    """ RESTful CRUD controller """
    
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
    """ RESTful CRUD controller """

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
    """ Allows the user to add, update and delete their contacts """
    
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
    # JQuery Autocomplete uses 'q' instead of 'value'
    value = request.vars.q
    if value:
        item = person_search(value)
        item = json.dumps(item)
        response.view = "xml.html"
        return dict(item=item)
    return

def person_search(value):
    """ Generic function to do the search of groups which match a type """
    table1 = db.pr_group
    field1 = "name"
    table2 = db.pr_person
    field21 = "first_name"
    field22 = "middle_name"
    field23 = "last_name"
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
    return item

#--------------------------------------
# Enabled only for testing
@auth.shn_requires_membership(1)
def tag():
    """ RESTful CRUD controller """
    resource = "tag"
    tablename = "%s_%s" % (module, resource)
    table = db[tablename]
    # Server-side Pagination
    response.s3.pagination = True
    
    return shn_rest_controller(module, resource, listadd=False)
