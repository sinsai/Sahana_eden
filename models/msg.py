# -*- coding: utf-8 -*-

"""
    Messaging module
"""

module = "msg"
if deployment_settings.has_module(module):
    # Settings
    resourcename = "setting"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("outgoing_sms_handler"),
                            # Moved to deployment_settings
                            #Field("default_country_code", "integer", default=44),
                            migrate=migrate)

    table.outgoing_sms_handler.requires = IS_IN_SET(["Modem", "Gateway", "Tropo"], zero=None)

    #------------------------------------------------------------------------
    resourcename = "email_settings"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                    Field("inbound_mail_server"),
                    Field("inbound_mail_type"),
                    Field("inbound_mail_ssl", "boolean"),
                    Field("inbound_mail_port", "integer"),
                    Field("inbound_mail_username"),
                    Field("inbound_mail_password"),
                    Field("inbound_mail_delete", "boolean"),
                    # Also needs to be used by Auth (order issues), DB calls are overheads
                    # - as easy for admin to edit source in 000_config.py as to edit DB (although an admin panel can be nice)
                    #Field("outbound_mail_server"),
                    #Field("outbound_mail_from"),
                    migrate=migrate)
    table.inbound_mail_type.requires = IS_IN_SET(["imap", "pop3"], zero=None)

    #------------------------------------------------------------------------
    resourcename = "modem_settings"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            #Field("account_name"), # Nametag to remember account - To be used later
                            Field("modem_port"),
                            Field("modem_baud", "integer", default = 115200),
                            Field("enabled", "boolean", default = False),
                            #Field("preference", "integer", default = 5), To be used later
                            migrate=migrate)

    #------------------------------------------------------------------------
    resourcename = "gateway_settings"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("url",
                                  default = "https://api.clickatell.com/http/sendmsg"),
                            Field("parameters",
                                  default="user=yourusername&password=yourpassword&api_id=yourapiid"),
                            Field("message_variable", "string", default = "text"),
                            Field("to_variable", "string", default = "to"),
                            Field("enabled", "boolean", default = False),
                            #Field("preference", "integer", default = 5), To be used later
                            migrate=migrate)

    #------------------------------------------------------------------------
    resourcename = "tropo_settings"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("token_messaging"),
                            #Field("token_voice"),
                            migrate=migrate)


    #------------------------------------------------------------------------
    resourcename = "twitter_settings"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("pin"),
                            Field("oauth_key"),
                            Field("oauth_secret"),
                            Field("twitter_account"),
                            migrate=migrate)
    table.oauth_key.writable = False
    table.oauth_secret.writable = False

    ### comment these 2 when debugging
    table.oauth_key.readable = False
    table.oauth_secret.readable = False

    table.twitter_account.writable = False

    def twitter_settings_onvalidation(form):
        """ Complete oauth: take tokens from session + pin from form, and do the 2nd API call to Twitter """
        if form.vars.pin and session.s3.twitter_request_key and session.s3.twitter_request_secret:
            try:
                import tweepy
            except:
                raise HTTP(501, body=T("Can't import tweepy"))

            oauth = tweepy.OAuthHandler(deployment_settings.twitter.oauth_consumer_key,
                                        deployment_settings.twitter.oauth_consumer_secret)
            oauth.set_request_token(session.s3.twitter_request_key, session.s3.twitter_request_secret)
            try:
                oauth.get_access_token(form.vars.pin)
                form.vars.oauth_key = oauth.access_token.key
                form.vars.oauth_secret = oauth.access_token.secret
                twitter = tweepy.API(oauth)
                form.vars.twitter_account = twitter.me().screen_name
                form.vars.pin = "" # we won't need it anymore
                return
            except tweepy.TweepError:
                session.error = T("Settings were reset because authenticating with Twitter failed")
        # Either user asked to reset, or error - clear everything
        for k in ["oauth_key", "oauth_secret", "twitter_account"]:
            form.vars[k] = None
        for k in ["twitter_request_key", "twitter_request_secret"]:
            session.s3[k] = ""

    s3xrc.model.configure(table, onvalidation=twitter_settings_onvalidation)

    #------------------------------------------------------------------------
    # Message priority
    msg_priority_opts = {
        3:T("High"),
        2:T("Medium"),
        1:T("Low")
    }
    #------------------------------------------------------------------------
    # Message Log - This is where all the messages / logs go into
    resourcename = "log"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.pr_pentity), # pe_id, Sender
                            Field("sender"),        # The name to go out incase of the email, if set used
                            Field("fromaddress"),   # From address if set changes sender to this
                            Field("recipient"),
                            Field("subject", length=78),
                            Field("message", "text"),
                            #Field("attachment", "upload", autodelete = True), #TODO
                            Field("verified", "boolean", default = False),
                            Field("verified_comments", "text"),
                            Field("actionable", "boolean", default = True),
                            Field("actioned", "boolean", default = False),
                            Field("actioned_comments", "text"),
                            # Hide until actually wired-up for something
                            #Field("priority", "integer", default = 1),
                            Field("inbound", "boolean", default = False),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    #table.priority.requires = IS_NULL_OR(IS_IN_SET(msg_priority_opts))
    #table.priority.label = T("Priority")
    table.inbound.label = T("Direction")
    table.inbound.represent = lambda direction: (direction and ["In"] or ["Out"])[0]
    #@ToDo More Labels for i18n

    s3xrc.model.configure(table,
                          list_fields=["id",
                                       "inbound",
                                       "pe_id",
                                       "fromaddress",
                                       "recipient",
                                       "subject",
                                       "message",
                                       "verified",
                                       #"verified_comments",
                                       "actionable",
                                       "actioned",
                                       #"actioned_comments",
                                       #"priority"
                                       ])

    # Reusable Message ID
    message_id = S3ReusableField("message_id", db.msg_log,
                                 requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                                 # FIXME: Subject works for Email but not SMS
                                 represent = lambda id: db(db.msg_log.id == id).select(db.msg_log.subject,
                                                                                       limitby=(0, 1)).first().subject,
                                 ondelete = "RESTRICT"
                                )

    
    #------------------------------------------------------------------------
    # Message Tag - Used to tag a message to a resource
    resourcename = "tag"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            message_id(),
                            Field("resource"),
                            Field("record_uuid", # null in this field implies subscription to the entire resource
                                  type=s3uuid,
                                  length=128),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "record_uuid",
                                        "resource",
                                       ])
    #------------------------------------------------------------------------
    # Twitter Search Queries
    resourcename = "twitter_search"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("search_query", length = 140),
                            migrate = migrate           
                            )
    #------------------------------------------------------------------------
    # Twitter Search Results
    resourcename = "twitter_search_results"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("tweet", length=140),
                            Field("posted_by"),
                            Field("posted_at"),
                            Field("twitter_search", db.msg_twitter_search),
                            migrate = migrate
                            )  
    #table.twitter_search.requires = IS_ONE_OF(db, "twitter_search.search_query")                    
    #table.twitter_search.represent = lambda id: db(db.msg_twitter_search.id == id).select(db.msg_twitter_search.search_query, limitby = (0,1)).first().search_query
                            
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(msg_twitter_search="twitter_search"))
   
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "tweet",
                                        "posted_by",
                                        "posted_at",
                                        "twitter_search",
                                       ])                       
               
   
    #------------------------------------------------------------------------
    # The following was added to show only the supported messaging methods
    msg_contact_method_opts = { # pr_contact_method dependency
        1:T("Email"),
        2:T("Mobile Phone"),
        #3:T("XMPP"),
        4:T("Twitter"),
    }

    # Channel - For inbound messages this tells which channel the message came in from.
    resourcename = "channel"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            message_id(),
                            Field("pr_message_method", "integer",
                                  requires = IS_IN_SET(msg_contact_method_opts, zero=None),
                                  default = 1),
                            Field("log"),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))


    #------------------------------------------------------------------------
    # Status
    resourcename = "email_inbound_status"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("status"),
                            migrate=migrate)


    # Valid message outbox statuses
    msg_status_type_opts = {
        1:T("Unsent"),
        2:T("Sent"),
        3:T("Draft"),
        4:T("Invalid")
        }

    opt_msg_status = db.Table(None, "opt_msg_status",
                              Field("status", "integer", notnull=True,
                              requires = IS_IN_SET(msg_status_type_opts, zero=None),
                              default = 1,
                              label = T("Status"),
                              represent = lambda opt: msg_status_type_opts.get(opt, UNKNOWN_OPT)))

    # Outbox - needs to be separate to Log since a single message sent needs different outbox entries for each recipient
    resourcename = "outbox"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            message_id(),
                            super_link(db.pr_pentity), # pe_id, Person/Group to send the message out to
                            Field("address"),   # If set used instead of picking up from pe_id
                            Field("pr_message_method", "integer",
                                  requires = IS_IN_SET(msg_contact_method_opts, zero=None),
                                  default = 1,
                                  label = T("Contact Method"),
                                  represent = lambda opt: msg_contact_method_opts.get(opt, UNKNOWN_OPT)),
                            opt_msg_status,
                            Field("system_generated", "boolean", default = False),
                            Field("log"),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))

    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(msg_log="message_id"))

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "pe_id",
                                        "status",
                                        "log",
                                       ])

    # Message Read Status - To replace Message Outbox #TODO
    resourcename = "read_status"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            message_id(),
                            person_id(),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)
    s3xrc.model.configure(table,
                          list_fields=[ "id",
                                        "message_id",
                                        "person_id",
                                       ])

    #------------------------------------------------------------------------
    # Tropo Scratch pad for outbound messaging
    resourcename = "tropo_scratch"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("row_id","integer"),
                            Field("message_id","integer"),
                            Field("recipient"),
                            Field("message"),
                            Field("network"),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))

    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)

    # SMS store for persistence and scratch pad for combining incoming xform chunks
    resourcename = "xforms_store"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("sender", "string", length = 20),
                            Field("fileno", "integer"),
                            Field("totalno", "integer"),
                            Field("partno", "integer"),
                            Field("message", "string", length = 160),
                            migrate=migrate)

    #------------------------------------------------------------------------
    # CAP: Common Alerting Protocol
    # http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html
    # CAP alert Status Code (status)
    cap_alert_status_code_opts = {
        "Actual":T("Actionable by all targeted recipients"),
        "Exercise":T("Actionable only by designated exercise participants; exercise identifier SHOULD appear in <note>"),
        "System":T("For messages that support alert network internal functions"),
        "Test":T("Technical testing only, all recipients disregard"),
        "Draft":T("preliminary template or draft, not actionable in its current form"),
    }
    # CAP info Event Category (category)
    cap_info_category_opts = {
        "Geo":T("Geophysical (inc. landslide)"),
        "Met":T("Meteorological (inc. flood)"),
        "Safety":T("General emergency and public safety"),
        "Security":T("Law enforcement, military, homeland and local/private security"),
        "Rescue":T("Rescue and recovery"),
        "Fire":T("Fire suppression and rescue"),
        "Health":T("Medical and public health"),
        "Env":T("Pollution and other environmental"),
        "Transport":T("Public and private transportation"),
        "Infra":T("Utility, telecommunication, other non-transport infrastructure"),
        "CBRNE":T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
        "Other":T("Other events"),
    }
    # CAP info Response Type (responseType)
    cap_info_responseType_opts = {
        "Shelter":T("Take shelter in place or per <instruction>"),
        "Evacuate":T("Relocate as instructed in the <instruction>"),
        "Prepare":T("Make preparations per the <instruction>"),
        "Execute":T("Execute a pre-planned activity identified in <instruction>"),
        "Avoid":T("Avoid the subject event as per the <instruction>"),
        "Monitor":T("Attend to information sources as described in <instruction>"),
        "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
        "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
        "None":T("No action recommended"),
    }

    # Reports
    # Verified reports ready to be sent out as alerts or displayed on a map
    msg_report_type_opts = {
        "Shelter":T("Take shelter in place or per <instruction>"),
        "Evacuate":T("Relocate as instructed in the <instruction>"),
        "Prepare":T("Make preparations per the <instruction>"),
        "Execute":T("Execute a pre-planned activity identified in <instruction>"),
        "Avoid":T("Avoid the subject event as per the <instruction>"),
        "Monitor":T("Attend to information sources as described in <instruction>"),
        "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
        "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
        "None":T("No action recommended"),
    }
    resourcename = "report"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            message_id(),
                            location_id(),
                            Field("image", "upload", autodelete = True),
                            Field("url", requires=IS_NULL_OR(IS_URL())),
                            migrate=migrate,
                            *(s3_timestamp() + s3_uid() + s3_deletion_status()))
    table.uuid.requires = IS_NOT_ONE_OF(db, "%s.uuid" % tablename)

#------------------------------------------------------------------------
def shn_msg_compose( redirect_module = "msg",
                     redirect_function = "compose",
                     redirect_vars = None,
                     title_name = "Send Message" ):
    """
        Form to Compose a Message

        @param redirect_module: Redirect to the specified module's url after login.
        @param redirect_function: Redirect to the specified function
        @param redirect_vars:  Dict with vars to include in redirects
        @param title_name: Title of the page
    """

    resourcename1 = "log"
    tablename1 = "msg" + "_" + resourcename1
    table1 = db[tablename1]
    resourcename2 = "outbox"
    tablename2 = "msg" + "_" + resourcename2
    table2 = db[tablename2]

    if auth.is_logged_in() or auth.basic():
        pass
    else:
        redirect(URL(r=request, c="default", f="user", args="login",
            vars={"_next":URL(r=request, c=redirect_module, f=redirect_function, vars=redirect_vars)}))

    # Model options
    table1.sender.writable = table1.sender.readable = False
    table1.fromaddress.writable = table1.fromaddress.readable = False
    table1.pe_id.writable = table1.pe_id.readable = False
    table1.verified.writable = table1.verified.readable = False
    table1.verified_comments.writable = table1.verified_comments.readable = False
    table1.actioned.writable = table1.actioned.readable = False
    table1.actionable.writable = table1.actionable.readable = False
    table1.actioned_comments.writable = table1.actioned_comments.readable = False

    table1.subject.label = T("Subject")
    table1.message.label = T("Message")
    #table1.priority.label = T("Priority")

    table2.pe_id.writable = table2.pe_id.readable = True
    table2.pe_id.label = T("Recipients")
    table2.pe_id.comment = DIV(_class="tooltip",
                               _title="%s|%s" % (T("Recipients"),
                                                 T("Please enter the first few letters of the Person/Group for the autocomplete.")))

    def compose_onvalidation(form):
        """ Set the sender and use msg.send_by_pe_id to route the message """
        if not request.vars.pe_id:
            session.error = T("Please enter the recipient")
            redirect(URL(r=request,c=redirect_module, f=redirect_function, vars=redirect_vars))
        sender_pe_id = db(db.pr_person.uuid == auth.user.person_uuid).select(db.pr_person.pe_id,
                                                                             limitby=(0, 1)).first().pe_id
        if msg.send_by_pe_id(request.vars.pe_id,
                             request.vars.subject,
                             request.vars.message,
                             sender_pe_id,
                             request.vars.pr_message_method):
            session.flash = T("Check outbox for the message status")
            redirect(URL(r=request, c=redirect_module, f=redirect_function, vars=redirect_vars))
        else:
            session.error = T("Error in message")
            redirect(URL(r=request,c=redirect_module, f=redirect_function, vars=redirect_vars))

    logform = crud.create(table1,
                          onvalidation = compose_onvalidation)
    outboxform = crud.create(table2)

    return dict(logform = logform, outboxform = outboxform, title = T(title_name))
