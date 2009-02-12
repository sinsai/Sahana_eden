"""
This file was developed by Fran Boon as a web2py extension.
This file is released under the BSD license (you can include it in bytecode compiled web2py apps as long as you acknowledge the author).
web2py (required to run this file) is released under the GPLv2 license.
"""

from gluon.storage import Storage
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.contrib.markdown import WIKI
try:
    from gluon.contrib.gql import SQLTable
except ImportError:
    from gluon.sql import SQLTable
import traceback

# Copied from Selenium Plone Tool
def getBrowserName(userAgent):
    "Determine which browser is being used."
    if userAgent.find('MSIE') > -1:
        return 'IE'
    elif userAgent.find('Firefox') > -1:
        return 'Firefox'
    elif userAgent.find('Gecko') > -1:
        return 'Mozilla'
    else:
        return 'Unknown'

from gluon.html import *

# Modified versions of URL from gluon/html.py
# we need simplified versions for our jquery functions
def URL2(a=None, c=None, r=None):
    """
    example:

    >>> URL(a='a',c='c')
    '/a/c'

    generates a url "/a/c" corresponding to application a & controller c 
    If r=request is passed, a & c are set, respectively,
    to r.application, r.controller

    The more typical usage is:
    
    URL(r=request) that generates a base url with the present application and controller.
    
    The function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a    
    if c:
        controller = c
    if not (application and controller):
        raise SyntaxError, 'not enough information to build the url'
    #other = ''
    url = '/%s/%s' % (application, controller)
    return url
        
def URL3(a=None, r=None):
    """
    example:

    >>> URL(a='a')
    '/a'

    generates a url "/a" corresponding to application a
    If r=request is passed, a is set
    to r.application

    The more typical usage is:
    
    URL(r=request) that generates a base url with the present application.
    
    The controller & function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a    
    if not (application and controller):
        raise SyntaxError, 'not enough information to build the url'
    #other = ''
    url = '/%s' % application
    return url

import uuid, datetime
from gluon.tools import *

DEFAULT=lambda:None

class AuthS3(Auth):
    """Extended version of Auth from gluon/tools.py
    - Allow Internationalisation of strings (can't be done in gluon)
    """
    def __init__(self,environment,T,db=None):
        "Initialise parent class & make any necessary modifications"
        Auth.__init__(self,environment,db)
        self.messages.access_denied=T("Insufficient privileges")
        self.messages.logged_in=T("Logged in")
        self.messages.email_sent=T("Email sent")
        self.messages.email_verified=T("Email verified")
        self.messages.logged_out=T("Logged out")
        self.messages.registration_succesful=T("Registration successful")
        self.messages.invalid_email=T("Invalid email")
        self.messages.invalid_login=T("Invalid login")
        self.messages.verify_email_subject=T("Password verify")
        self.messages.username_sent=T("Your username was emailed to you")
        self.messages.new_password_sent=T("A new password was emailed to you")
        self.messages.invalid_email=T("Invalid email")
        self.messages.password_changed=T("Password changed")
        self.messages.retrieve_username=str(T("Your username is"))+": %(username)s"
        self.messages.retrieve_username_subject="Username retrieve"
        self.messages.retrieve_password=str(T("Your password is"))+": %(password)s"
        self.messages.retrieve_password_subject=T("Password retrieve")
        self.messages.profile_updated=T("Profile updated")
                
    def login(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
        Overrides Web2Py's login() to use .error & not .flash for invalid login
        
        returns a login form
        """

        user = self.settings.table_user
        if 'username' in user.fields:
            username = 'username'
        else:
            username = 'email'
        user[username].requires = IS_NOT_EMPTY()
        request = self.environment.request
        session = self.environment.session
        if not request.vars._next:
            request.vars._next = request.env.http_referer or ''
        if next == DEFAULT:
            next = request.vars._next or self.settings.login_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.login_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.login_onaccept
        if log == DEFAULT:
            log = self.settings.login_log
        form = SQLFORM(
            user,
            fields=[username, 'password'],
            hidden=dict(_next=request.vars._next),
            showid=self.settings.showid,
            submit_button=self.settings.submit_button,
            delete_label=self.settings.delete_label,
            )
        if FORM.accepts(form, request.vars, session,
                        onvalidation=onvalidation):

            # ## BEGIN

            TYPES = (
                str,
                int,
                long,
                datetime.time,
                datetime.date,
                datetime.datetime,
                bool,
                )
            users = self.db(user[username]
                             == form.vars[username])(user.password
                     == form.vars.password)(user.registration_key == ''
                    ).select()
            if not users:
                session.error = self.messages.invalid_login
                if not next:
                    next = URL(r=request)
                redirect(next)
            user = Storage(dict([(k, v) for (k, v) in users[0].items()
                           if isinstance(v, TYPES)]))
            session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
            self.user = user
            session.flash = self.messages.logged_in
            log = self.settings.login_log
            if log:
                self.log_event(log % self.user)
            if onaccept:
                onaccept(form)
            if not next:
                next = URL(r=request)
            elif next and not next[0] == '/' and next[:4] != 'http':
                next = URL(r=request, f=next.replace('[id]',
                           str(form.vars.id)))
            redirect(next)
        return form


    def register(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
        Overrides Web2Py's register() to add new functionality:
            * Check that self-registration is allowed: session.s3.self_registration
            * Check whether email verification is required? (Is static config in __db.py sufficient?)
            * Whenever someone registers, it automatically adds their name to the Person Registry
            * Registering automatically logs you in
        
        returns a registration form
        """
        request = self.environment.request
        session = self.environment.session
        if self.is_logged_in():
            redirect(self.settings.logged_url)
        if not request.vars._next:
            request.vars._next = request.env.http_referer or ''
        if next == DEFAULT:
            next = request.vars._next or self.settings.register_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.register_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.register_onaccept
        if log == DEFAULT:
            log = self.settings.register_log
        user = self.settings.table_user
        form = SQLFORM(user, hidden=dict(_next=request.vars._next),
                       showid=self.settings.showid,
                       submit_button=self.settings.submit_button,
                       delete_label=self.settings.delete_label)
        td = form.element(_id="%s_password__row" % user._tablename)[1]
        td.append(BR())
        td.append(INPUT(_name="password2",
                        _type="password",
                  requires=IS_EXPR('value==%s' % repr(request.vars.password))))
        key = str(uuid.uuid4())
        if form.accepts(request.vars, session,
                        onvalidation=onvalidation):
            # S3: Add to Person Registry as well
            # Check to see whether User already exists
            if len(self.db(self.db.pr_person.email==form.vars.email).select()):
                # Update
                #db(db.pr_person.email==form.vars.email).select()[0].update_record(
                #    name = form.vars.name
                #)
                pass
            else:
                # Insert
                self.db.pr_person.insert(
                    first_name = form.vars.first_name,
                    last_name = form.vars.last_name,
                    email = form.vars.email
                )
            description = \
                'group uniquely assigned to %(first_name)s %(last_name)s'\
                 % form.vars
            group_id = self.add_group("user_%s" % form.vars.id, description)
            self.add_membership(group_id, form.vars.id)
            # S3: Control whether verification is required dynamically
            if session.s3.verification:
                user[form.vars.id] = dict(registration_key=key)
                if not self.settings.mailer.send(to=form.vars.email,
                        subject=self.messages.verify_email_subject,
                        message=self.messages.verify_email
                         % dict(key=key)):
                    self.db.rollback()
                    session.error = self.messages.invalid_email
                    return form
                session.flash = self.messages.email_sent
                log = self.settings.register_log
                if log:
                    self.log_event(log % form.vars)
            else:
                # S3: Login automatically upon registration
                if 'username' in user.fields: username='username'
                else: username='email'
                TYPES=(str,int,long,datetime.time,datetime.date,
                   datetime.datetime,bool)
                users=self.db(user[username]==form.vars[username])\
                  (user.password==form.vars.password)\
                  (user.registration_key=='')\
                  .select()
                user=Storage(dict([(k,v) for k,v in users[0].items() \
                         if isinstance(v,TYPES)]))
                session.auth=\
                    Storage(user=user,last_visit=request.now,
                    expiration=self.settings.expiration)
                self.user=user
                session.flash=self.messages.logged_in
                log=self.settings.register_log
                if log:
                    self.log_event(log % form.vars)
                log=self.settings.login_log
                if log:
                    self.log_event(log % self.user)
            if onaccept:
                onaccept(form)
            if not next:
                next = URL(r=request)
            elif next and not next[0] == '/' and next[:4] != 'http':
                next = URL(r=request, f=next.replace('[id]',
                           str(form.vars.id)))
            redirect(next)
        return form

class CrudS3(Crud):
    """Extended version of Crud from gluon/tools.py
    - Allow Internationalisation of strings (can't be done in gluon)
    """
    def __init__(self,environment,T,db=None):
        "Initialise parent class & make any necessary modifications"
        Crud.__init__(self,environment,db)
        self.settings.submit_button=T("Submit")
        self.settings.delete_label=T("Check to delete:")
        self.messages.record_created=T("Record Created")
        self.messages.record_updated=T("Record Updated")

class MailS3(Mail):
    """Extended version of Mail from gluon/tools.py
    - currently a placeholder - nothing actually amended
    """
    def __init__(self):
        "Initialise parent class & make any necessary modifications"
        Mail.__init__(self)
        

#from applications.t3.modules.t2 import T2
from applications.sahana.modules.t2 import T2

class S3(T2):
    "Extended version of T2 from modules/t2.py"

    def __init__(self, request, response, session, cache, T, db, all_in_db=False):
        "Initialise parent class & make any necessary modifications"
        T2.__init__(self, request, response, session, cache, T, db, all_in_db=False)
        # Clear unused info from cluttering every Response
        response.files = []
        # Set email server's port?
        #self.email_server = 'localhost:25'
    
    # Modified version of _stamp
    # we need to support multiple tables
    # NB Needs testing!
    def _stamp_many(self, tables, form, create=False):
        """
        Called by create and update methods. it timestamps the records.
        The following fields are timestamped (if they exist):
        - created_on
        - created_by
        - created_signature
        - modified_on
        - modified_by
        - modified_signature
        """
        
        for table in tables:
            if create:
                if 'created_by_ip' in table.fields: 
                    form.vars.created_by_ip = self.request.client
                if 'created_on' in table.fields: 
                    form.vars.created_on = self.now
                if 'created_by' in table.fields: 
                    form.vars.created_by = self.person_id
                if 'created_signature' in table.fields: 
                    form.vars.created_signature = self.person_name
            if 'modified_by_ip' in table.fields:
                form.vars.modified_by_ip = self.request.client
            if 'modified_on' in table.fields: 
                form.vars.modified_on = self.now
            if 'modified_by' in table.fields:
                form.vars.modified_by = self.person_id
            if 'modified_signature' in table.fields:
                form.vars.modified_signature = self.person_name

    def redirect(self,f=None,args=[],vars={},flash=None,error=None):
        """
        Overrides t2's redirect() to allow error as well as flash
        
        self.redirect('name',[],{},'message') is a shortcut for

            session.flash='message'
            redirect(URL(r=request,f='name',args=[],vars={})
        """
        if flash: self.session.flash=flash
        if error: self.session.error=error
        redirect(self.action(f,args,vars))
