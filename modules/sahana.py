# -*- coding: utf-8 -*-

"""
This file was developed by Fran Boon as a web2py extension.
This file is released under the BSD license 
(you can include it in bytecode compiled web2py apps as long as you acknowledge the author).

web2py (required to run this file) is released under the GPLv2 license.
"""

from gluon.storage import Storage, Messages
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.contrib.markdown import WIKI
try:
    from gluon.contrib.gql import SQLTable, SQLStorage
except ImportError:
    from gluon.sql import SQLTable, SQLStorage
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

# Modified version of SQLTABLE from gluon/sqlhtml.py
# we need a different linkto construction for our CRUD controller
# we need to specify a different ID field to direct to for the M2M controller
class SQLTABLE2(TABLE):
    """
    given a SQLRows object, as returned by a db().select(),
    generates an html table with the rows.

    optional arguments:
    linkto: URL to edit individual records
    upload: URL to download uploaded files
    orderby: Add an orderby link to column headers.
    headers: dictionary of headers to headers redefinions
    truncate: length at which to truncate text in table cells.
              Defaults to 16 characters.
    id: field to direct linkto to
    optional names attributes for passed to the <table> tag
    """

    def __init__(
        self,
        sqlrows,
        linkto=None,
        upload=None,
        orderby=None,
        headers={},
        truncate=16,
        id=None,
        **attributes
        ):
        TABLE.__init__(self, **attributes)
        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not orderby:
            for c in sqlrows.colnames:
                row.append(TH(headers.get(c, c)))
        else:
            for c in sqlrows.colnames:
                row.append(TH(A(headers.get(c, c), _href='?orderby='
                            + c)))
        components.append(THEAD(TR(*row)))
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = 'even'
            else:
                _class = 'odd'
            for colname in sqlrows.colnames:
                if not table_field.match(colname):
                    r = record._extra[colname]
                    row.append(TD(r))
                    continue
                (tablename, fieldname) = colname.split('.')
                field = sqlrows._db[tablename][fieldname]
                if record.has_key(tablename) and isinstance(record,
                        SQLStorage) and isinstance(record[tablename],
                        SQLStorage):
                    r = record[tablename][fieldname]
                elif record.has_key(fieldname):
                    r = record[fieldname]
                else:
                    raise SyntaxError, \
                        'something wrong in SQLRows object'
                if field.represent:
                    r = field.represent(r)
                    row.append(TD(r))
                    continue
                if field.type == 'blob' and r:
                    row.append(TD('DATA'))
                    continue
                r = str(field.formatter(r))
                if upload and field.type == 'upload' and r != None:
                    if r:
                        row.append(TD(A('file', _href='%s/%s'
                                    % (upload, r))))
                    else:
                        row.append(TD())
                    continue
                ur = unicode(r, 'utf8')
                if len(ur) > truncate:
                    r = ur[:truncate - 3].encode('utf8') + '...'
                if id and linkto and field.type == 'id':
                    link_id = sqlrows._db[tablename][r][id]
                    try:
                        href = linkto(link_id)
                    except TypeError:
                        href = '%s/%s' % (linkto, link_id)
                    row.append(TD(A(link_id, _href=href)))
                elif linkto and field.type == 'id':
                    try:
                        href = linkto(r)
                    except TypeError:
                        href = '%s/%s' % (linkto, r)
                    row.append(TD(A(r, _href=href)))
                elif linkto and field.type[:9] == 'reference':
                    row.append(TD(A(r, _href='%s/%s/%s' % (linkto,
                               field.type[10:], r))))
                else:
                    row.append(TD(r))
            tbody.append(TR(_class=_class, *row))
        components.append(TBODY(*tbody))
    
import uuid, datetime
from gluon.tools import *

DEFAULT = lambda:None

class AuthS3(Auth):
    """
    Extended version of Auth from gluon/tools.py
    - override login() & register()
    - add shn_register() callback
    """
    def __init__(self, environment, db=None):
        "Initialise parent class & make any necessary modifications"
        Auth.__init__(self, environment, db)
        self.messages.lock_keys = False
        self.messages.registration_disabled = 'Registration Disabled!'
        self.messages.lock_keys = True
                
    def __get_migrate(self, tablename, migrate=True):

        if type(migrate).__name__=='str':
            return (migrate+tablename+'.table')
        elif migrate==False:
            return False
        else:
            return True

    def define_tables(self, migrate=True):
        """
        to be called unless tables are defined manually

        usages::

            # defines all needed tables and table files
            # UUID+'_auth_user.table', ...
            auth.define_tables()

            # defines all needed tables and table files
            # 'myprefix_auth_user.table', ...
            auth.define_tables(migrate='myprefix_')

            # defines all needed tables without migration/table files
            auth.define_tables(migrate=False)

        """

        db = self.db
        if not self.settings.table_user:
            passfield = self.settings.password_field
            self.settings.table_user = db.define_table(
                self.settings.table_user_name,
                db.Field('first_name', length=128, default='',
                        label=self.messages.label_first_name),
                db.Field('last_name', length=128, default='',
                        label=self.messages.label_last_name),

                # add UTC Offset (+/-HHMM) to specify the user's timezone
                # TODO:
                #   - this could need a nice label and context help
                #   - entering timezone from a drop-down would be more comfortable
                #   - automatic DST adjustment could be nice
                db.Field('utc_offset'),

                # db.Field('username', length=128, default=''),
                db.Field('email', length=512, default='',
                        label=self.messages.label_email),
                db.Field(passfield, 'password', length=512,
                         readable=False, label=self.messages.label_password),
                db.Field('registration_key', length=512,
                        writable=False, readable=False, default='',
                        label=self.messages.label_registration_key),
                migrate=\
                    self.__get_migrate(self.settings.table_user_name, migrate))
            table = self.settings.table_user
            table.first_name.requires = \
                IS_NOT_EMPTY(error_message=self.messages.is_empty)
            table.last_name.requires = \
                IS_NOT_EMPTY(error_message=self.messages.is_empty)
            table.utc_offset.label = "UTC Offset"
            table.utc_offset.comment = A(SPAN("[Help]"), _class="tooltip", _title="UTC Offset|The time difference between UTC and your timezone, specify as +HHMM for eastern or -HHMM for western timezones.")
            try:
                from applications.sahana.modules.validators import IS_UTC_OFFSET
                table.utc_offset.requires = IS_UTC_OFFSET()
            except:
                pass
            table[passfield].requires = [CRYPT(key=self.settings.hmac_key)]
            table.email.requires = \
                [IS_EMAIL(error_message=self.messages.invalid_email),
                 IS_NOT_IN_DB(db, '%s.email'
                     % self.settings.table_user._tablename)]
            table.registration_key.default = ''
        if not self.settings.table_group:
            self.settings.table_group = db.define_table(
                self.settings.table_group_name,
                db.Field('role', length=512, default='',
                        label=self.messages.label_role),
                db.Field('description', 'text',
                        label=self.messages.label_description),
                migrate=self.__get_migrate(
                    self.settings.table_group_name, migrate))
            table = self.settings.table_group
            table.role.requires = IS_NOT_IN_DB(db, '%s.role'
                 % self.settings.table_group._tablename)
        if not self.settings.table_membership:
            self.settings.table_membership = db.define_table(
                self.settings.table_membership_name,
                db.Field('user_id', self.settings.table_user,
                        label=self.messages.label_user_id),
                db.Field('group_id', self.settings.table_group,
                        label=self.messages.label_group_id),
                migrate=self.__get_migrate(
                    self.settings.table_membership_name, migrate))
            table = self.settings.table_membership
            table.user_id.requires = IS_IN_DB(db, '%s.id' %
                    self.settings.table_user._tablename,
                    '%(id)s: %(first_name)s %(last_name)s')
            table.group_id.requires = IS_IN_DB(db, '%s.id' %
                    self.settings.table_group._tablename,
                    '%(id)s: %(role)s')
        if not self.settings.table_permission:
            self.settings.table_permission = db.define_table(
                self.settings.table_permission_name,
                db.Field('group_id', self.settings.table_group,
                        label=self.messages.label_group_id),
                db.Field('name', default='default', length=512,
                        label=self.messages.label_name),
                db.Field('table_name', length=512,
                        label=self.messages.label_table_name),
                db.Field('record_id', 'integer',
                        label=self.messages.label_record_id),
                migrate=self.__get_migrate(
                    self.settings.table_permission_name, migrate))
            table = self.settings.table_permission
            table.group_id.requires = IS_IN_DB(db, '%s.id' %
                    self.settings.table_group._tablename,
                    '%(id)s: %(role)s')
            table.name.requires = IS_NOT_EMPTY()
            table.table_name.requires = IS_IN_SET(self.db.tables)
            table.record_id.requires = IS_INT_IN_RANGE(0, 10 ** 9)
        if not self.settings.table_event:
            self.settings.table_event = db.define_table(
                self.settings.table_event_name,
                db.Field('time_stamp', 'datetime',
                        default=self.environment.request.now,
                        label=self.messages.label_time_stamp),
                db.Field('client_ip',
                        default=self.environment.request.client,
                        label=self.messages.label_client_ip),
                db.Field('user_id', self.settings.table_user, default=None,
                        label=self.messages.label_user_id),
                db.Field('origin', default='auth', length=512,
                        label=self.messages.label_origin),
                db.Field('description', 'text', default='',
                        label=self.messages.label_description),
                migrate=self.__get_migrate(
                    self.settings.table_event_name, migrate))
            table = self.settings.table_event
            table.user_id.requires = IS_IN_DB(db, '%s.id' %
                    self.settings.table_user._tablename,
                    '%(id)s: %(first_name)s %(last_name)s')
            table.origin.requires = IS_NOT_EMPTY()
            table.description.requires = IS_NOT_EMPTY()

    def login(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
        Overrides Web2Py's login() to use custom flash styles &  utcnow
        
        returns a login form

        .. method:: Auth.login([next=DEFAULT [, onvalidation=DEFAULT
            [, onaccept=DEFAULT [, log=DEFAULT]]]])

        """

        table_user = self.settings.table_user
        if 'username' in table_user.fields:
            username = 'username'
        else:
            username = 'email'
        old_requires = table_user[username].requires
        table_user[username].requires = IS_NOT_EMPTY()
        request = self.environment.request
        response = self.environment.response
        session = self.environment.session
        passfield = self.settings.password_field
        if next == DEFAULT:
            next = request.vars._next or self.settings.login_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.login_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.login_onaccept
        if log == DEFAULT:
            log = self.messages.login_log

        user = None # default

        # do we use our own login form, or from a central source?
        if self.settings.login_form == self:
            form = SQLFORM(
                table_user,
                fields=[username, passfield],
                hidden=dict(_next=request.vars._next),
                showid=self.settings.showid,
                submit_button=self.messages.submit_button,
                delete_label=self.messages.delete_label,
                )
            accepted_form = False
            if form.accepts(request.vars, session,
                            formname='login', dbio=False,
                            onvalidation=onvalidation):
                accepted_form = True
                # check for username in db
                users = self.db(table_user[username] == form.vars[username]).select()
                if users:
                    # user in db, check if registration pending or disabled
                    temp_user = users[0]
                    if temp_user.registration_key == 'pending':
                        response.warning = self.messages.registration_pending
                        return form
                    elif temp_user.registration_key == 'disabled':
                        response.error = self.messages.login_disabled
                        return form
                    elif temp_user.registration_key:
                        response.warning = \
                            self.messages.registration_verifying
                        return form
                    # try alternate logins 1st as these have the current version of the password
                    for login_method in self.settings.login_methods:
                        if login_method != self and \
                                login_method(request.vars[username],
                                             request.vars[passfield]):
                            if not self in self.settings.login_methods:
                                # do not store password in db
                                form.vars[passfield] = None
                            user = self.get_or_create_user(form.vars)
                            break
                    if not user:
                        # alternates have failed, maybe because service inaccessible
                        if self.settings.login_methods[0] == self:
                            # try logging in locally using cached credentials
                            if temp_user[passfield] == form.vars.get(passfield, ''):
                                # success
                                user = temp_user
                else:
                    # user not in db
                    if not self.settings.alternate_requires_registration:
                        # we're allowed to auto-register users from external systems
                        for login_method in self.settings.login_methods:
                            if login_method != self and \
                                    login_method(request.vars[username],
                                                 request.vars[passfield]):
                                if not self in self.settings.login_methods:
                                    # do not store password in db
                                    form.vars[passfield] = None
                                user = self.get_or_create_user(form.vars)
                                break
                if not user:
                    # invalid login
                    session.error = self.messages.invalid_login
                    redirect(self.url(args=request.args))
        else:
            # use a central authentication server
            cas = self.settings.login_form
            cas_user = cas.get_user()
            if cas_user:
                cas_user[passfield] = None
                user = self.get_or_create_user(cas_user)
            else:
                # we need to pass through login again before going on
                next = URL(r=request) + '?_next=' + next
                redirect(cas.login_url(next))

        # process authenticated users
        if user:
            user = Storage(table_user._filter_fields(user, id=True))
            session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
            self.user = user
            session.confirmation = self.messages.logged_in
        if log and self.user:
            self.log_event(log % self.user)

        # how to continue
        if self.settings.login_form == self:
            if accepted_form:
                if onaccept:
                    onaccept(form)
                if isinstance(next, (list, tuple)):
                    # fix issue with 2.6
                    next = next[0]
                if next and not next[0] == '/' and next[:4] != 'http':
                    next = self.url(next.replace('[id]', str(form.vars.id)))
                redirect(next)
            table_user[username].requires = old_requires
            return form
        else:
            redirect(next)

    def register(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
        Overrides Web2Py's register() to add new functionality:
            * Checks whether registration is permitted
            * Custom Flash styles
            * utcnow
            
        returns a registration form

        .. method:: Auth.register([next=DEFAULT [, onvalidation=DEFAULT
            [, onaccept=DEFAULT [, log=DEFAULT]]]])


        """

        request = self.environment.request
        response = self.environment.response
        session = self.environment.session
        
        # S3: Don't allow registration if disabled
        db = self.db
        self_registration = db().select(db.s3_setting.self_registration)[0].self_registration
        if not self_registration:
            session.error = self.messages.registration_disabled
            redirect(URL(r=request, args=['login']))


        if self.is_logged_in():
            redirect(self.settings.logged_url)


        if next == DEFAULT:
            next = request.vars._next or self.settings.register_next
        if onvalidation == DEFAULT:
            onvalidation = self.settings.register_onvalidation
        if onaccept == DEFAULT:
            onaccept = self.settings.register_onaccept
        if log == DEFAULT:
            log = self.messages.register_log
        user = self.settings.table_user
        passfield = self.settings.password_field
        form = SQLFORM(user, hidden=dict(_next=request.vars._next),
                       showid=self.settings.showid,
                       submit_button=self.messages.submit_button,
                       delete_label=self.messages.delete_label)
        for i, row in enumerate(form[0].components):
            item = row[1][0]
            if isinstance(item, INPUT) and item['_name'] == passfield:
                form[0].insert(i+1, TR(
                        LABEL(self.messages.verify_password + ':'),
                        INPUT(_name="password_two",



                              _type="password",
                              requires=IS_EXPR('value==%s' % \
                               repr(request.vars.get(passfield, None)),
                        error_message=self.messages.mismatched_password)),
                '', _class='%s_%s__row' % (user, 'password_two')))
        if self.settings.captcha != None:
            form[0].insert(-1, TR('', self.settings.captcha, ''))

        user.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars, session, formname='register',
                        onvalidation=onvalidation):
            description = \
                'group uniquely assigned to %(first_name)s %(last_name)s'\
                 % form.vars
            if self.settings.create_user_groups:
                group_id = self.add_group("user_%s" % form.vars.id, description)
                self.add_membership(group_id, form.vars.id)
            if self.settings.registration_requires_verification:
                if not self.settings.mailer or \
                   not self.settings.mailer.send(to=form.vars.email,
                        subject=self.messages.verify_email_subject,
                        message=self.messages.verify_email
                         % dict(key=key)):
                    self.db.rollback()
                    response.error = self.messages.invalid_email
                    return form
                session.confirmation = self.messages.email_sent
            elif self.settings.registration_requires_approval:
                user[form.vars.id] = dict(registration_key='pending')
                session.warning = self.messages.registration_pending
            else:
                user[form.vars.id] = dict(registration_key='')
                session.confirmation = self.messages.registration_successful

                table_user = self.settings.table_user
                if 'username' in table_user.fields:
                    username = 'username'
                else:
                    username = 'email'
                users = self.db(table_user[username] == form.vars[username])\
                    .select()
                user = users[0]
                user = Storage(table_user._filter_fields(user, id=True))
                session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
                self.user = user
                session.flash = self.messages.logged_in

            if log:
                self.log_event(log % form.vars)
            if onaccept:
                onaccept(form)
            if not next:
                next = self.url(args = request.args)
            elif isinstance(next, (list, tuple)):
                # fix issue with 2.6
                next = next[0]

            elif next and not next[0] == '/' and next[:4] != 'http':
                next = self.url(next.replace('[id]', str(form.vars.id)))

            redirect(next)
        return form

    def shn_register(self, form):
        """
        S3 framework function
        Designed to be used as an onaccept callback for register()
        Whenever someone registers, it:
            * adds them to the 'Authenticated' role
            * adds their name to the Person Registry
        """
        db = self.db
        # Add to 'Authenticated' role
        authenticated = self.id_group('Authenticated')
        self.add_membership(authenticated, form.vars.id)
        # S3: Add to Person Registry as well
        # Check to see whether User already exists
        if len(db(db.pr_person.email==form.vars.email).select()):
            # Update
            #db(db.pr_person.email==form.vars.email).select()[0].update_record(
            #    name = form.vars.name
            #)
            pass
        else:
            # Insert Person Entity
            pr_pe_id = db.pr_pentity.insert(opt_pr_entity_type=1,label=None)
            # Link to Person Entity
            if pr_pe_id:
                db.pr_person.insert(
                    pr_pe_id = pr_pe_id,
                    pr_pe_label=None,
                    first_name = form.vars.first_name,
                    last_name = form.vars.last_name,
                    email = form.vars.email
                )
                
    def requires_membership(self, role):
        """
        decorator that prevents access to action if not logged in or
        if user logged in is not a member of group_id.
        If role is provided instead of group_id then the group_id is calculated.
        
        Overrides Web2Py's requires_membership() to add new functionality:
            * Custom Flash style
        """

        def decorator(action):
            group_id = self.id_group(role)

            def f(*a, **b):
                if not self.basic() and not self.is_logged_in():
                    args = self.environment.request.args
                    redirect(self.settings.login_url + \
                                 '?_next='+urllib.quote(self.url(args=args)))
                if not self.has_membership(group_id):
                    self.environment.session.error = \
                        self.messages.access_denied
                    next = self.settings.on_failed_authorization
                    redirect(next)
                return action(*a, **b)

            return f

        return decorator

class CrudS3(Crud):
    """
    Extended version of Crud from gluon/tools.py
    - select() uses SQLTABLE2 (to allow different linkto construction)
    """
    def __init__(self, environment, db=None):
        "Initialise parent class & make any necessary modifications"
        Crud.__init__(self, environment, db)
        
    def select(
        self,
        table,
        query=None,
        fields=None,
        orderby=None,
        limitby=None,
        headers={},
        **attr
        ):
        request = self.environment.request
        if isinstance(table, str):
            if not table in self.db.tables:
                raise HTTP(404)
            table = self.db[table]
        if not query:
            query = table.id > 0
        if not fields:
            fields = [table.ALL]
        rows = self.db(query).select(*fields,
            **dict(orderby=orderby, limitby=limitby))
        if not rows:
            return None # Nicer than an empty table.
        if not 'linkto' in attr:
            attr['linkto'] = URL(r=request, args='read')
        if not 'upload' in attr:
            attr['upload'] = URL(r=request, f='download')
        return SQLTABLE2(rows, headers=headers, **attr)

#from applications.t3.modules.t2 import T2
#class S3(T2):
class S3:
    "The T2 functions we still use extracted from t2.py"

    IMAGE_EXT = ['.jpg', '.gif', '.png']
    def __init__(self, request, response, session, cache, T, db,
            all_in_db = False):
        self.messages = Storage()
        self.messages.record_deleted = T("Record Deleted")
        self.error_action = 'error'
        self.request = request
        self.response = response
        self.session = session
        self.cache = cache
        self.T = T
        self.db = db
        self.all_in_db = all_in_db
        if self.db._dbname == 'gql':
            self.is_gae = True
            self.all_in_db = True
        else:
            self.is_gae = False
        if all_in_db:
            session.connect(request, response, db=db)
        if not session.t2:
            session.t2 = Storage()
        try:
            self.id = int(request.args[-1])
        except:
            self.id = 0
        
    def _globals(self):
        """
        Returns (request, response, session, cache, T, db)
        """
        return self.request, self.response, self.session, \
               self.cache, self.T, self.db

    def _error(self):
        """
        Redirects to the self.error_action (='error'?) page.
        """
        self.redirect(self.error_action)

    def action(self, f=None, args=[], vars={}):
        """
        self.action('name', [], {}) is a shortcut for 
     
            URL(r=request, f='name', args=[], vars={})
        """
        if not f:
            f = self.request.function
        if not isinstance(args, (list, tuple)):
            args = [args]
        return URL(r=self.request, f=f, args=args, vars=vars)

    def redirect(self, f=None, args=[], vars={}, flash=None):
        """
        self.redirect('name', [], {}, 'message') is a shortcut for

            session.flash = 'message'
            redirect(URL(r=request, f='name', args=[], vars={})
        """
        if flash:
            self.session.flash = flash
        redirect(self.action(f, args, vars))

    # Deprecated
    def itemize(self, *tables, **opts):
        """
        Lists all records from tables.
        opts include: query, orderby, nitems, header where nitems is items per page;
        """
        ### FIX - ADD PAGINATION BUTTONS
        import re
        request, response, session, cache, T, db = self._globals()
        if not len(tables):
            raise SyntaxError
        query = opts.get('query', None)
        orderby = opts.get('orderby', None)
        nitems = opts.get('nitems', 25)
        g = re.compile('^(?P<min>\d+)$').match(request.vars.get('_page', ''))
        page = int(g.group('min')) if g else 0
        limitby = opts.get('limitby', (page*nitems, page*nitems + nitems))
        if not query:
            query = tables[0].id > 0
        rows_count = tables[0]._db(query).count()
        rows = tables[0]._db(query).select(orderby=orderby, limitby=limitby,
                                         *[t.ALL for t in tables])
        if not rows:
            return None # rather than 'No data'. Give caller a chance to do his i18n issue
        def represent(t, r):
            try:
                rep = t.represent(r) # Note: custom represent() should generate a string or a list, but NOT a TR(...) instance
            except KeyError:
                rep = ([r[f] for f in t.displays] # Default depends on t.displays, if any
                if 'displays' in t else ['#%i'%r.id, str(r[t.fields[1]])]) # Fall back to TR(id,FirstField)
            return rep if isinstance(rep, list) else [rep] # Ensure to return a list
        header = opts.get('header',# Input can be something like TR(TH('ID'),TH('STAMP'))
          TR(*[TH(tables[0][f].label) for f in tables[0].displays])
            if 'displays' in tables[0] else '') # Default depends on tables[0].displays, if any
        headerList = [header] if header else []
        nav = DIV( # Iceberg at 21cn dot com prefers this style of page navigation :-)
          INPUT(_type='button', _value='|<', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':0})) if page else '',
          INPUT(_type='button', _value='<', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':page-1})) if page else '',
          SELECT(value=page,
            _onchange = 'javascript:location="%s?_page="+this.value' % self.action(args=request.args), 
            # Intentionally "hide" it here for professional users. Cuz I doubt it is not intuitive enough for non-english common users.
            _title=query, 
            # I hope the marks here are universal therefore no need for i18n
            *[OPTION('P%d (#%d~#%d)' % 
              (i+1, i*nitems+1, min(rows_count, (i+1)*nitems)),
              _value=i) for i in xrange(rows_count/nitems+1)]
            ) if nitems < rows_count else '',
          INPUT(_type='button', _value='>', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':page+1})
            ) if page*nitems+len(rows) < rows_count else '',
          INPUT(_type='button', _value='>|', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':rows_count/nitems})
            ) if page*nitems+len(rows) < rows_count else '',
          ) if nitems < rows_count else None
        if len(tables) == 1:
            return DIV(
                # It shouldn't be inside the table otherwise it is tricky to set the correct _colspan for IE7
                nav if nav else '', 
                # sorry, I don't know how to setup css to make _class='t2-itemize' looks cool, so I stick to "sortable"
                TABLE(_class='sortable', 
                    *headerList+[TR(*represent(tables[0], row)) for row in rows]),
                nav if nav else '') # See above
        else:
            import itertools
            return DIV(
                # And don't try to make it "align=right", because the table might be too wide to show in the screen.
                nav if nav else '', 
                TABLE(_class='sortable', # see above
                    *headerList+[TR(*list(itertools.chain(
                        *[represent(table,row[table._tablename]) for table in tables])))
                        for row in rows]),
                    nav if nav else '') # See above

    SEARCH_OP_PREFIX = '_op_'
    SEARCH_LOW_PREFIX, SEARCH_HIGH_PREFIX = '_low_', '_high_' # For date and datetime
    def field_search_widget(self, field):
        "Build a search widget for a db field"
        if isinstance(field.requires, IS_NULL_OR):
            requires = field.requires.other
        else:
            requires = field.requires
        if isinstance(requires, IS_IN_SET):
            return DIV(
                SELECT(OPTION('=', _value='is'),OPTION('!=', _value='isnot'),
                        _name = '%s%s' % (self.SEARCH_OP_PREFIX,field.name)
                      ),
                SELECT(_name=field.name, requires=IS_NULL_OR(requires),
                        *[OPTION('', _value='')]
                            +[OPTION(l, _value=v) for v, l in requires.options()]
                      ),
                      )
        if isinstance(requires, (IS_DATE, IS_DATETIME)):
            lowName = '%s%s' % (self.SEARCH_LOW_PREFIX, field.name)
            highName = '%s%s' % (self.SEARCH_HIGH_PREFIX, field.name)
            return DIV(
                        INPUT(
                            _class='date' if isinstance(requires, IS_DATE) else 'datetime',
                            _type='text', 
                            _name=lowName, 
                            _id=lowName, 
                            requires=IS_NULL_OR(requires)
                        ),
                    '<= X <=',
                    INPUT(_class='date' if isinstance(requires,IS_DATE) else 'datetime',
                        _type='text', 
                        _name=highName, 
                        _id=highName, 
                        requires=IS_NULL_OR(requires)),
                     )
        if field.name == 'id':
            return DIV('=', 
                    # we still need this to trigger the search anyway
                    INPUT(_type='hidden', 
                            _value='is', 
                            _name='%s%s' % (self.SEARCH_OP_PREFIX, field.name)),
                    INPUT(_class='integer', _name='id'))
        if field.type in ('text', 'string'): # the last exit
            return DIV(
                SELECT(
                    OPTION(self.T('contains'), _value='contain'),
                    OPTION(self.T('does not contain'), _value='notcontain'),
                    _name = '%s%s'%(self.SEARCH_OP_PREFIX, field.name)),
                #Use naive INPUT(...) to waive all validators, such as IS_URL()
                INPUT(_type='text', _name=field.name, _id=field.name))
        import logging
        logging.warn('Oops, this field is not yet supported. Please report it.')

    def search(self, *tables, **opts):    
        """
        Makes a search widgets to search records in tables.
        opts can be query, orderby, limitby
        """
        request, response, session, cache, T, db = self._globals()
        if self.is_gae and len(tables) != 1:
            self._error()
        def is_integer(x):
            try:
                int(x)
            except:
                return False
            else:
                return True
        def is_double(x):
            try:
                float(x)
            except:
                return False
            else:
                return True
        from gluon.sqlhtml import form_factory
        options = []
        orders = []
        query = opts.get('query', None)
        def option(s):
            return OPTION(s if s[:3] != 't2_' else s[3:], _value=s)
        for table in tables:
            for field in table.get('displays', table.fields):
                tf = str(table[field])
                t = table[field].type
                if not self.is_gae and (t=='string' or t=='text'): 
                    options.append(option('%s contains' % tf))
                    options.append(option('%s starts with' % tf))
                if t != 'upload':
                    options.append(option('%s greater than' % tf))
                options.append(option('%s equal to' % tf))
                options.append(option('%s not equal to' % tf))
                if t != 'upload':
                    options.append(option('%s less than' % tf))
                orders.append(option('%s ascending' % tf))
                orders.append(option('%s descending' % tf))
        form = FORM(SELECT(_name='cond', *options),
                  INPUT(_name='value', value=request.vars.value or '0'),
                  ' ordered by ',
                  SELECT(_name='order', *orders),' refine? ',
                  INPUT(_type='checkbox', _name='refine'),
                  INPUT(_type='submit'))
        if form.accepts(request.vars, formname='search'):
            db = tables[0]._db
            p = (request.vars.cond, request.vars.value, request.vars.order)
            if not request.vars.refine:
                session.t2.query = []
            session.t2.query.append(p)
            orderby, message1, message2 = None, '', ''
            prev = [None, None, None]        
            for item in session.t2.query:
                c, value, order = item
                if c != prev[0] or value != prev[1]:
                    tf, cond = c.split(' ', 1)                
                    table, field = tf.split('.')
                    f = db[table][field]
                    if (f.type=='integer' or f.type=='id') and \
                       not is_integer(value):
                        session.flash = self.messages.invalid_value
                        self.redirect(args=request.args)
                    elif f.type=='double' and not is_double(value):
                        session.flash = self.messages.invalid_value
                        self.redirect(args=request.args)
                    elif cond=='contains':
                        q = f.lower().like('%%%s%%' %value.lower())
                    elif cond=='starts with':
                        q = f.lower().like('%s%%' % value.lower())
                    elif cond=='less than': 
                        q = f < value
                    elif cond=='equal to':
                        q = f == value
                    elif cond=='not equal to':
                        q = f != value
                    elif cond=='greater than': 
                        q = f > value
                    query = query&q if query else q
                    message1 += '%s "%s" AND ' % (c, value)
                if order != prev[2]:
                    p = None
                    c, d = request.vars.order.split(' ')
                    table, field = c.split('.')
                    if d == 'ascending':
                        p = f
                    elif d == 'descending':
                        p = ~f
                    orderby = orderby|p if orderby else p
                    message2 += '%s ' % order
                prev = item
            message = 'QUERY %s ORDER %s' % (message1, message2)
            return DIV(TABLE(TR(form), TR(message), 
                TR(self.itemize(query=query, orderby=orderby, *tables))), 
                _class='t2-search')
        else:
            session.t2.query = []
        return DIV(TABLE(TR(form)), _class='t2-search')

# *****************************************************************************
# Joined Resources
#
# added by nursix
#

# *****************************************************************************
# Joined Resource
#
class JoinedResource(object):

    def __init__(self, prefix, name, joinby=None, multiple=True, fields=None, rss=None, attr=None):

        self.prefix = prefix
        self.name = name
        self.joinby = joinby
        self.multiple = multiple
        self.fields = fields
        self.rss = rss
        if attr:
            self.attr = attr
        else:
            self.attr = {}

        if not 'deletable' in self.attr:
            self.set_attr('deletable', True)

        if not 'editable' in self.attr:
            self.set_attr('editable', True)

    # get_prefix --------------------------------------------------------------
    def get_prefix(self):
        return self.prefix

    # is_multiple -------------------------------------------------------------
    def is_multiple(self):
        return self.multiple

    # list_fields -------------------------------------------------------------
    def list_fields(self):
        return self.fields

    # rss ---------------------------------------------------------------------
    def _rss(self):
        return self.rss

    # head_fields -------------------------------------------------------------
    def head_fields(self):
        if 'main' in self.attr:
            main = self.attr['main']
        else:
            main = 'id'

        if 'extra' in self.attr:
            extra = self.attr['extra']
        else:
            extra = main

        return (main, extra)

    # set_attr ----------------------------------------------------------------
    def set_attr(self, name, value):
        self.attr.update(name, value)

    # get_attr ----------------------------------------------------------------
    def get_attr(self, name):
        if name in self.attr:
            return self.attr[name]
        else:
            return None

    # get_join_key ------------------------------------------------------------
    def get_join_key(self, module, resource):

        tablename = "%s_%s" % (module, resource)

        if self.joinby:

            if isinstance(self.joinby, str):
                # natural join
                return (self.joinby, self.joinby)

            elif isinstance(self.joinby, dict):
                # primary/foreign key join
                if tablename in self.joinby:
                    return ('id', self.joinby[tablename])
                else:
                    # Not joined with this table
                    return None
            else:
                # Invalid definition
                return None
        else:
            # No join_key defined
            return None

# *****************************************************************************
# JRLayer
#
class JRLayer(object):

    jresources = {}
    settings = {}
    methods = {}
    jmethods = {}

    def __init__(self, db):

        self.db = db
        self.jresources = {}
        self.settings = {}

    # add_jresource -----------------------------------------------------------
    def add_jresource(self, prefix, name, joinby=None, multiple=True, rss=None, fields=None, **attr):

        _table = "%s_%s" % (prefix, name)

        if fields:
            list_fields = [self.db[_table][f] for f in fields]

        jr = JoinedResource(prefix, name, joinby=joinby, multiple=multiple, rss=rss, fields=list_fields, attr=attr)
        self.jresources[name] = jr

    # get_prefix --------------------------------------------------------------
    def get_prefix(self, name):

        if name in self.jresources:
            return self.jresources[name].get_prefix()
        else:
            return None

    # is_multiple -------------------------------------------------------------
    def is_multiple(self, name):

        if name in self.jresources:
            return self.jresources[name].is_multiple()
        else:
            return True

    # get_join_key ------------------------------------------------------------
    def get_join_key(self, name, module, resource):

        if name in self.jresources:
            return self.jresources[name].get_join_key(module, resource)
        else:
            return None

    # list_fields -------------------------------------------------------------
    def list_fields(self, name):

        if name in self.jresources:
            return self.jresources[name].list_fields()
        else:
            return None

    # rss ---------------------------------------------------------------------
    def rss(self, name):

        if name in self.jresources:
            return self.jresources[name]._rss()
        else:
            return None

    # head_fields -------------------------------------------------------------
    def head_fields(self, resource):

        if resource in self.jresources:
            return self.jresources[resource].head_fields()
        else:
            return (None, None)

    # set_attr ----------------------------------------------------------------
    def set_attr(self, resource, name, value):

        if resource in self.jresources:
            self.jresources[resource].set_attr(name, value)

    # get_attr ----------------------------------------------------------------
    def get_attr(self, resource, name):

        if resource in self.jresources:
            return self.jresources[resource].get_attr(name)
        else:
            return None

    # set_method --------------------------------------------------------------
    def set_method(self, prefix, resource, jprefix, jresource, method, action):

        if not method:
            return None

        if prefix and resource:
            tablename = "%s_%s" % (prefix, resource)

            if jprefix and jresource:
                jtablename = "%s_%s" % (jprefix, jresource)
                if not (method in self.jmethods):
                    self.jmethods[method] = {}
                if not (jtablename in self.jmethods[method]):
                    self.jmethods[method][jtablename] = {}
                self.jmethods[method][jtablename][tablename] = action
                return action
            else:
                if not (method in self.methods):
                    self.methods[method] = {}
                self.methods[method][tablename] = action
                return action

        else:
            return None

    # get_method --------------------------------------------------------------
    def get_method(self, prefix, resource, jprefix, jresource, method):

        if not method:
            return None

        if prefix and resource:
            tablename = "%s_%s" % (prefix, resource)

            if jprefix and jresource:
                jtablename = "%s_%s" % (jprefix, jresource)
                if method in self.jmethods and \
                    jtablename in self.jmethods[method] and \
                    tablename in self.jmethods[method][jtablename]:
                    return self.jmethods[method][jtablename][tablename]
                else:
                    return None
            else:
                if method in self.methods and tablename in self.methods[method]:
                    return self.methods[method][tablename]
                else:
                    return None
        else:
            return None

    # store_session -----------------------------------------------------------
    def store_session(self, session, module, resource, record_id):

        if session and not ('jrvars' in session):
            session.jrvars = Storage()

        if session and 'jrvars' in session:
            tablename = "%s_%s" % (module, resource)
            session.jrvars[tablename] = record_id

    # clear_session -----------------------------------------------------------
    def clear_session(self, session, module=None, resource=None):

        if session:

            if module and resource:
                tablename = "%s_%s" % (module, resource)
                if ('jrvars' in session) and (tablename in session.jrvars):
                    del session.jrvars[tablename]

            else:
                if 'jrvars' in session:
                    del session['jrvars']

# *****************************************************************************
# JRequest
#
class JRequest(object):
    """
        Class handling requests to joined resources REST controller.
    """

    def __init__(self, jrlayer, module, resource, request, session=None):

        self.default_representation = 'html'
        self.request = request
        self.jrlayer = jrlayer
        self.session = session

        self.invalid = False
        self.badmethod = False
        self.badrecord = False
        self.badrequest = False

        self.representation = request.extension
        self.http = request.env.request_method
        self.extension = False

        self.module = module or request.controller
        self.resource = resource or request.function
        self.method = None
        self.record_id = None
        self.jresource = None

        # Parse original request
        if not self.__parse():
            return None

        self.tablename = None
        self.table = None
        self.record = None

        # Check for primary record
        if not self.__record():
            return None

        self.jmodule = None
        self.jtablename = None
        self.jtable = None
        self.jrecord_id = None
        self.pkey = None
        self.fkey = None
        self.multiple = True

        #  Get Joined Resource parameters (if any)
        if self.jresource:
            self.jmodule = self.jrlayer.get_prefix(self.jresource)
            self.multiple = self.jrlayer.is_multiple(self.jresource)
            if not self.jrecord_id:
                if self.args[len(self.args)-1].isdigit():
                    self.jrecord_id = self.args[len(self.args)-1]
            self.jtablename = "%s_%s" % (self.jmodule, self.jresource)
            self.jtable = self.jrlayer.db[self.jtablename]

            # Get join key
            join_keys = self.jrlayer.get_join_key(self.jresource, self.module, self.resource)
            if not join_keys:
                self.badmethod = True
                self.invalid = True
                return self
            else:
                self.pkey, self.fkey = join_keys

        # Get custom action (if any)
        self.custom_action = self.jrlayer.get_method(
            self.module,
            self.resource,
            self.jmodule,
            self.jresource,
            self.method)

        # Append record ID to request as necessary
        if self.record_id:
            if len(self.args)>0 or len(self.args)==0 and ('id_label' in self.request.vars):
                if self.jresource and not self.args[0].isdigit():
                    self.args.insert(0, str(self.record_id))
                    if self.representation==self.default_representation or self.extension:
                        self.request.args.insert(0, str(self.record_id))
                    else:
                        self.request.args.insert(0, '%s.%s' % (self.record_id, self.representation))
                elif not self.jresource and not (str(self.record_id) in self.args):
                    self.args.append(self.record_id)
                    if self.representation==self.default_representation or self.extension:
                        self.request.args.append(self.record_id)
                    else:
                        self.request.args.append('%s.%s' % (self.record_id, self.representation))
    # -------------------------------------------------------------------------
    def __parse(self):
        """
            Parse the original request
        """

        self.args = []

        if len(self.request.args)>0:

            # Check for extensions
            for arg in self.request.args:
                if '.' in arg:
                    arg, ext = arg.rsplit('.',1)
                    if ext and len(ext)>0:
                        self.representation = str.lower(ext)
                        self.extension = True
                self.args.append(str.lower(arg))

            # Parse arguments
            if self.args[0].isdigit():
                self.record_id = self.args[0]
                if len(self.args)>1:
                    self.jresource = self.args[1]
                    if self.jresource in self.jrlayer.jresources:
                        if len(self.args)>2:
                            if self.args[2].isdigit():
                                self.jrecord_id = self.args[2]
                            else:
                                self.method = self.args[2]
                        else:
                            self.method = None
                    else:
                        # Error: BAD REQUEST
                        self.badrequest = True
                        self.invalid = True
                        return False
                else:
                    self.jresource = None
                    self.method = None
            else:
                if self.args[0] in self.jrlayer.jresources:
                    self.jresource = self.args[0]
                    self.record_id = None
                    if len(self.args)>1:
                        if self.args[1].isdigit():
                            self.jrecord_id = self.args[1]
                        else:
                            self.method = self.args[1]
                    else:
                        self.method = None
                else:
                    self.method = self.args[0]
                    self.jresource = None
                    if len(self.args)>1 and self.args[1].isdigit():
                        self.record_id = self.args[1]
                    else:
                        self.record_id = None

        # Check format option
        if 'format' in self.request.vars:
            self.representation = str.lower(self.request.vars.format)

        # Representation fallback
        if not self.representation:
            self.representation = self.default_representation

        return True

    # -------------------------------------------------------------------------
    def __record(self):
        """
            Check primary record ID
        """

        # Get primary table
        self.tablename = "%s_%s" % (self.module, self.resource)
        self.table = self.jrlayer.db[self.tablename]

        # Check record ID passed in the request
        if self.record_id:
            query = (self.table.id==self.record_id)
            if 'deleted' in self.table:
                query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
            records = self.jrlayer.db(query).select(self.table.ALL)
            if records:
                self.record = records[0]
                self.record_id = self.record.id
            else:
                # Error: NO SUCH RECORD
                self.record_id = 0
                self.badrecord = True
                self.invalid = True
                return False

        # Check for ?id_label=
        if not self.record_id and 'id_label' in self.request.vars:
            id_label = str.strip(self.request.vars.id_label)
            if 'pr_pe_label' in self.table:
                query = (self.table.pr_pe_label==id_label)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.jrlayer.db(query).select(self.table.ALL)
                if records:
                    self.record = records[0]
                    self.record_id = self.record.id
                else:
                    # Error: NO SUCH RECORD
                    self.record_id = 0
                    self.badrecord = True
                    self.invalid = True
                    return False

        # Retrieve prior selected ID, if any
        if not self.record_id and len(self.request.args)>0:
            if self.session and self.session.jrvars and self.tablename in self.session.jrvars:
                self.record_id = self.session.jrvars[self.tablename]
                query = (self.table.id==self.record_id)
                if 'deleted' in self.table:
                    query = ((self.table.deleted==False) | (self.table.deleted==None)) & query
                records = self.jrlayer.db(query).select(self.table.ALL)
                if records:
                    self.record = records[0]
                    self.record_id = self.record.id
                else:
                    self.record_id = None
                    self.session.jrvars[self.tablename] = None

        # Remember primary record ID for further requests
        if self.record_id and self.session:
            self.jrlayer.store_session(self.session, self.module, self.resource, self.record_id)

        return True

    # -------------------------------------------------------------------------
    def here(self, representation=None):
        """
            Backlink producing the same request
        """

        args = []

        if not representation:
            representation = self.representation

        f = self.resource

        if self.jresource:
            args = [self.record_id]
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
            if self.method:
                args.append(self.method)
                if self.jrecord_id:
                    args.append(self.jrecord_id)
        else:
            if self.method:
                args.append(self.method)
            if self.record_id:
                if not representation==self.default_representation:
                    args.append('%s.%s' % (self.record_id, representation))
                else:
                    args.append(self.record_id)
            else:
                if not representation==self.default_representation:
                    f='%s.%s' % (self.resource, representation)
                else:
                    f=self.resource

        return(URL(r=self.request, c=self.request.controller, f=f, args=args))

    # -------------------------------------------------------------------------
    def there(self, representation=None):
        """
            Backlink producing a HTTP/list request to the same resource
        """
        args = []

        if not representation:
            representation = self.representation

        f = self.resource

        if self.jresource:
            args = [self.record_id]
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
        else:
            if not representation==self.default_representation:
                f='%s.%s' % (self.resource, representation)
            else:
                f=self.resource

        return(URL(r=self.request, c=self.request.controller, f=f, args=args))

    # -------------------------------------------------------------------------
    def same(self, representation=None):
        """
            Backlink producing the same request with neutralized primary record ID
        """

        args = []

        if not representation:
            representation = self.representation

        f = self.resource

        if self.jresource:
            args = ['[id]']
            if not representation==self.default_representation:
                args.append('%s.%s' % (self.jresource, representation))
            else:
                args.append(self.jresource)
            if self.method:
                args.append(self.method)
                #if self.jrecord_id:
                #    args.append(self.jrecord_id)
        else:
            if self.method:
                args.append(self.method)
            if self.record_id:
                if not representation==self.default_representation:
                    args.append('[id].%s' % representation)
                else:
                    args.append('[id]')
            else:
                if not representation==self.default_representation:
                    f='%s.%s' % (self.resource, representation)
                else:
                    f=self.resource

        return(URL(r=self.request, c=self.request.controller, f=f, args=args))
