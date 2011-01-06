# -*- coding: utf-8 -*-

""" Authentication, Authorization, Accouting

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: (c) 2010 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__all__ = ["AuthS3", "S3Permission", "S3Audit", "S3RoleManager"]

import sys
import datetime
import re
import urllib
import uuid
import warnings

from gluon.html import *
from gluon.http import HTTP, redirect
from gluon.storage import Storage, Messages
from gluon.validators import *
#try:
#    from gluon.contrib.gql import Field, Row, Query
#except ImportError:
from gluon.sql import Field, Row, Query
from gluon.sqlhtml import SQLFORM, SQLTABLE
from gluon.tools import Auth
from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3rest import S3Method
from s3widgets import S3ACLWidget
from s3validators import IS_ACL

DEFAULT = lambda: None
table_field = re.compile("[\w_]+\.[\w_]+")

# =============================================================================
class AuthS3(Auth):

    """
    S3 extensions of the gluon.tools.Auth class

        - override:
            define_tables()
            login()
            register()
            requires_membership()

        - add:
            shn_has_role()
            shn_has_permission()
            shn_logged_in()
            shn_accessible_query()
            shn_register() callback
            shn_link_to_person()

        - language

    """

    def __init__(self, environment, deployment_settings, db=None):

        """ Initialise parent class & make any necessary modifications """

        Auth.__init__(self, environment, db)

        self.deployment_settings = deployment_settings
        self.session = self.environment.session

        self.settings.lock_keys = False
        self.settings.username_field = False
        self.settings.lock_keys = True
        self.messages.lock_keys = False
        self.messages.registration_pending_approval = "Account registered, however registration is still pending approval - please wait until confirmation received."
        self.messages.email_approver_failed = "Failed to send mail to Approver - see if you can notify them manually!"
        self.messages.email_sent = "Verification Email sent - please check your email to validate. If you do not receive this email please check you junk email or spam filters"
        self.messages.email_verified = "Email verified - you can now login"
        self.messages.registration_disabled = "Registration Disabled!'"
        self.messages.lock_keys = True

        self.permission = S3Permission(self, environment)


    # -------------------------------------------------------------------------
    def __get_migrate(self, tablename, migrate=True):

        if type(migrate).__name__ == "str":
            return (migrate + tablename + ".table")
        elif migrate == False:
            return False
        else:
            return True


    # -------------------------------------------------------------------------
    def define_tables(self, migrate=True):

        """ to be called unless tables are defined manually

            usages::

                # defines all needed tables and table files
                # UUID + "_auth_user.table", ...
                auth.define_tables()

                # defines all needed tables and table files
                # "myprefix_auth_user.table", ...
                auth.define_tables(migrate="myprefix_")

                # defines all needed tables without migration/table files
                auth.define_tables(migrate=False)

        """

        db = self.db
        request = self.environment.request

        # User table
        if not self.settings.table_user:
            passfield = self.settings.password_field
            if self.settings.username_field:
                # with username
                self.settings.table_user = db.define_table(
                    self.settings.table_user_name,
                    Field("first_name", length=128, default="",
                            label=self.messages.label_first_name),
                    Field("last_name", length=128, default="",
                            label=self.messages.label_last_name),
                    Field("person_uuid", length=64, default="",
                             readable=False, writable=False),
                    Field("utc_offset", length=16, readable=False, writable=False),
                    Field("username", length=128, default=""),
                    Field("language", length=16),
                    Field("email", length=512, default="",
                            label=self.messages.label_email),
                    Field(passfield, "password", length=512,
                             readable=False, label=self.messages.label_password),
                    Field("registration_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("reset_password_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("timestmp", "datetime", writable=False,
                            readable=False, default=""),
                    migrate=\
                        self.__get_migrate(self.settings.table_user_name, migrate))
            else:
                # with email-address
                self.settings.table_user = db.define_table(
                    self.settings.table_user_name,
                    Field("first_name", length=128, default="",
                            label=self.messages.label_first_name),
                    Field("last_name", length=128, default="",
                            label=self.messages.label_last_name),
                    Field("person_uuid", length=64, default="",
                             readable=False, writable=False),
                    Field("utc_offset", length=16, readable=False, writable=False),
                    Field("language", length=16),
                    Field("email", length=512, default="",
                            label=self.messages.label_email),
                    Field(passfield, "password", length=512,
                             readable=False, label=self.messages.label_password),
                    Field("registration_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("reset_password_key", length=512,
                            writable=False, readable=False, default="",
                            label=self.messages.label_registration_key),
                    Field("timestmp", "datetime", writable=False,
                            readable=False, default=""),
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
                from s3validators import IS_UTC_OFFSET
                exec("from applications.%s.modules.validators import IS_UTC_OFFSET" % request.application)
                table.utc_offset.requires = IS_EMPTY_OR(IS_UTC_OFFSET())
            except:
                pass
            table[passfield].requires = [CRYPT(key=self.settings.hmac_key, digest_alg="sha512")]
            if self.settings.username_field:
                table.username.requires = IS_NOT_IN_DB(db, "%s.username" % self.settings.table_user._tablename)
            table.email.requires = \
                [IS_EMAIL(error_message=self.messages.invalid_email),
                 IS_NOT_IN_DB(db, "%s.email"
                     % self.settings.table_user._tablename)]
            table.registration_key.default = ""

        # Group table (roles)
        if not self.settings.table_group:
            self.settings.table_group = db.define_table(
                self.settings.table_group_name,
                Field("role", length=512, default="",
                        label=self.messages.label_role),
                Field("description", "text",
                        label=self.messages.label_description),
                migrate=self.__get_migrate(
                    self.settings.table_group_name, migrate))
            table = self.settings.table_group
            table.role.requires = IS_NOT_IN_DB(db, "%s.role"
                 % self.settings.table_group._tablename)

        # Group membership table (user<->role)
        if not self.settings.table_membership:
            self.settings.table_membership = db.define_table(
                self.settings.table_membership_name,
                Field("user_id", self.settings.table_user,
                        label=self.messages.label_user_id),
                Field("group_id", self.settings.table_group,
                        label=self.messages.label_group_id),
                migrate=self.__get_migrate(
                    self.settings.table_membership_name, migrate))
            table = self.settings.table_membership
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_group._tablename,
                    "%(id)s: %(role)s")

        # Permissions table (group<->permission)
        # @todo: deprecate / replace by S3Permission
        if not self.settings.table_permission:
            self.settings.table_permission = db.define_table(
                self.settings.table_permission_name,
                Field("group_id", self.settings.table_group,
                        label=self.messages.label_group_id),
                Field("name", default="default", length=512,
                        label=self.messages.label_name),
                Field("table_name", length=512,
                        label=self.messages.label_table_name),
                Field("record_id", "integer",
                        label=self.messages.label_record_id),
                migrate=self.__get_migrate(
                    self.settings.table_permission_name, migrate))
            table = self.settings.table_permission
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_group._tablename,
                    "%(id)s: %(role)s")
            table.name.requires = IS_NOT_EMPTY()
            table.table_name.requires = IS_IN_SET(self.db.tables)
            table.record_id.requires = IS_INT_IN_RANGE(0, 10 ** 9)

        # Event table (auth log)
        if not self.settings.table_event:
            self.settings.table_event = db.define_table(
                self.settings.table_event_name,
                Field("time_stamp", "datetime",
                        default=self.environment.request.now,
                        label=self.messages.label_time_stamp),
                Field("client_ip",
                        default=self.environment.request.client,
                        label=self.messages.label_client_ip),
                Field("user_id", self.settings.table_user, default=None,
                        label=self.messages.label_user_id),
                Field("origin", default="auth", length=512,
                        label=self.messages.label_origin),
                Field("description", "text", default="",
                        label=self.messages.label_description),
                migrate=self.__get_migrate(
                    self.settings.table_event_name, migrate))
            table = self.settings.table_event
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    self.settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.origin.requires = IS_NOT_EMPTY()
            table.description.requires = IS_NOT_EMPTY()

        # Define permission table
        self.permission.define_table()


    # -------------------------------------------------------------------------
    def login_bare(self, username, password):
        """
        Logins user
            - extended to understand session.s3.roles

        """

        request = self.environment.request
        session = self.environment.session
        db = self.db

        table_user = self.settings.table_user
        table_membership = self.settings.table_membership


        if self.settings.login_userfield:
            userfield = self.settings.login_userfield
        elif 'username' in table_user.fields:
            userfield = 'username'
        else:
            userfield = 'email'
        passfield = self.settings.password_field
        user = db(table_user[userfield] == username).select().first()
        password = table_user[passfield].validate(password)[0]
        if user:
            user_id = user.id
            if not user.registration_key and user[passfield] == password:
                user = Storage(table_user._filter_fields(user, id=True))
                session.auth = Storage(user=user, last_visit=request.now,
                                       expiration=self.settings.expiration)
                self.user = user

                # Add the Roles to session.s3
                roles = []
                set = db(table_membership.user_id == user_id).select(table_membership.group_id)
                session.s3.roles = [s.group_id for s in set]

                return user

        return False


    # -------------------------------------------------------------------------
    def login(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
            log=DEFAULT,
            ):

        """
        Overrides Web2Py's login() to use custom flash styles & utcnow

        @returns: a login form

        """

        table_user = self.settings.table_user
        if "username" in table_user.fields:
            username = "username"
        else:
            username = "email"
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
                            formname="login", dbio=False,
                            onvalidation=onvalidation):
                accepted_form = True
                # check for username in db
                users = self.db(table_user[username] == form.vars[username]).select()
                if users:
                    # user in db, check if registration pending or disabled
                    temp_user = users[0]
                    if temp_user.registration_key == "pending":
                        response.warning = self.messages.registration_pending
                        return form
                    elif temp_user.registration_key == "disabled":
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
                            if temp_user[passfield] == form.vars.get(passfield, ""):
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
            elif hasattr(cas, "login_form"):
                return cas.login_form()
            else:
                # we need to pass through login again before going on
                next = URL(r=request) + "?_next=" + next
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
                if next and not next[0] == "/" and next[:4] != "http":
                    next = self.url(next.replace("[id]", str(form.vars.id)))
                redirect(next)
            table_user[username].requires = old_requires
            return form
        else:
            redirect(next)


    # -------------------------------------------------------------------------
    def register(
        self,
        next=DEFAULT,
        onvalidation=DEFAULT,
        onaccept=DEFAULT,
        log=DEFAULT,
        ):
        """
        Overrides Web2Py's register() to add new functionality:
            - Checks whether registration is permitted
            - Custom Flash styles
            - utcnow
            - Allow form to be embedded in other pages

        @returns: a registration form

        """

        db = self.db
        request = self.environment.request
        response = self.environment.response
        session = self.environment.session
        deployment_settings = self.deployment_settings

        # S3: Don't allow registration if disabled
        self_registration = deployment_settings.get_security_self_registration()
        if not self_registration:
            session.error = self.messages.registration_disabled
            redirect(URL(r=request, args=["login"]))

        #settings = db(db.s3_setting.id > 0).select(db.s3_setting.utc_offset, limitby=(0, 1)).first()
        #if settings:
            #utc_offset = settings.utc_offset
        #else:
            ## db empty and prepopulate is false
            #utc_offset = self.deployment_settings.get_L10n_utc_offset()

        if self.is_logged_in() and request.function != "index":
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

        #user.utc_offset.default = utc_offset

        passfield = self.settings.password_field
        form = SQLFORM(user, hidden=dict(_next=request.vars._next),
                       showid=self.settings.showid,
                       submit_button=self.messages.submit_button,
                       delete_label=self.messages.delete_label)
        for i, row in enumerate(form[0].components):
            item = row[1][0]
            if isinstance(item, INPUT) and item["_name"] == passfield:
                form[0].insert(i + 1, TR(
                        LABEL(self.messages.verify_password + ":"),
                        INPUT(_name="password_two",
                              _type="password",
                              requires=IS_EXPR("value==%s" % \
                               repr(request.vars.get(passfield, None)),
                        error_message=self.messages.mismatched_password)),
                        SPAN("*", _class="req"),
                "", _class="%s_%s__row" % (user, "password_two")))
        if self.settings.captcha != None:
            form[0].insert(-1, TR("", self.settings.captcha, ""))

        user.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars, session, formname="register",
                        onvalidation=onvalidation):
            description = \
                "group uniquely assigned to %(first_name)s %(last_name)s"\
                 % form.vars
            if self.settings.create_user_groups:
                group_id = self.add_group("user_%s" % form.vars.id, description)
                self.add_membership(group_id, form.vars.id)
            if self.settings.registration_requires_verification and self.db(self.settings.table_user.id > 0).count() > 1:
                if not self.settings.mailer or \
                   not self.settings.mailer.send(to=form.vars.email,
                                                 subject=self.messages.verify_email_subject,
                                                 message=self.messages.verify_email % dict(key=key)):
                    self.db.rollback()
                    response.error = self.messages.invalid_email
                    return form
                session.confirmation = self.messages.email_sent
            elif self.settings.registration_requires_approval and self.db(self.settings.table_user.id > 0).count() > 1:
                if not self.settings.mailer or \
                   not self.settings.verify_email_onaccept(form.vars):
                    # We don't wish to prevent registration if the approver mail fails to send
                    #self.db.rollback()
                    session.error = self.messages.email_approver_failed
                    #return form
                user[form.vars.id] = dict(registration_key="pending")
                session.warning = self.messages.registration_pending_approval
            else:
                user[form.vars.id] = dict(registration_key="")
                session.confirmation = self.messages.registration_successful

                table_user = self.settings.table_user
                if "username" in table_user.fields:
                    username = "username"
                else:
                    username = "email"
                user = self.db(table_user[username] == form.vars[username]).select(limitby=(0, 1)).first()
                user = Storage(table_user._filter_fields(user, id=True))

                # Add the first user to admin group
                # Installers should create a default user with random password to make this safe
                if self.db(table_user.id > 0).count() == 1:
                    table_group = self.settings.table_group
                    admin_group = self.db(table_group.role == "Administrator").select(table_group.id, limitby=(0, 1)).first()
                    if admin_group:
                        self.add_membership(admin_group.id, user.id)
                    # Add extra startup roles for system administrator
                    roles = self.settings.admin_startup_roles
                    if roles:
                        for r in roles:
                            group = self.db(table_group.role == r).select(table_group.id, limitby=(0, 1)).first()
                            if group:
                                self.add_membership(group.id, user.id)

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

            elif next and not next[0] == "/" and next[:4] != "http":
                next = self.url(next.replace("[id]", str(form.vars.id)))

            redirect(next)
        return form


    # -------------------------------------------------------------------------
    def shn_logged_in(self):
        """
        Check whether the user is currently logged-in

            - tries Basic if not

        """

        session = self.session
        if not self.is_logged_in():
            if not self.basic():
                return False

        return True


    # -------------------------------------------------------------------------
    def shn_has_role(self, role):
        """
        Check whether the currently logged-in user has a role

        @param role: can be integer or a name

        """

        #deployment_settings = self.deployment_settings
        db = self.db
        session = self.session

        # => trigger basic auth
        if not self.shn_logged_in():
            return False

        # Administrators have all roles
        if 1 in session.s3.roles:
            return True

        try:
            role = int(role)
        except:
            #role = deployment_settings.auth.roles[role]
            try:
                role = db(db.auth_group.role == role).select(db.auth_group.id, limitby=(0, 1)).first().id
            except:
                # Role doesn't exist in the Database
                return False

        if role in session.s3.roles:
            return True
        else:
            return False


    # -------------------------------------------------------------------------
    def shn_has_permission(self, method, table, record_id = 0):

        """
            S3 framework function to define whether a user can access a record in manner "method"
            Designed to be called from the RESTlike controller
            @note: This is planned to be rewritten: http://eden.sahanafoundation.org/wiki/BluePrintAuthorization

            @param table: the table or tablename
        """

        db = self.db
        session = self.session

        if not hasattr(table, "_tablename"):
            table = db[table]

        if session.s3.security_policy == 1:
            # Simple policy
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            else:
                # Authentication required for Create/Update/Delete.
                authorised = self.shn_logged_in()

        elif session.s3.security_policy == 2:
            # Editor policy
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            elif method == "create":
                # Authentication required for Create.
                authorised = self.shn_logged_in()
            elif record_id == 0 and method == "update":
                # Authenticated users can update at least some records
                authorised = self.shn_logged_in()
            else:
                # Editor role required for Update/Delete.
                authorised = self.shn_has_role("Editor")
                if not authorised and self.user and "created_by" in table:
                    # Creator of Record is allowed to Edit
                    record = db(table.id == record_id).select(table.created_by, limitby=(0, 1)).first()
                    if record and self.user.id == record.created_by:
                        authorised = True

        else:
            # Full policy
            if self.shn_logged_in():
                # Administrators are always authorised
                if self.shn_has_role(1):
                    authorised = True
                else:
                    # Require records in auth_permission to specify access (default Web2Py-style)
                    authorised = self.has_permission(method, table, record_id)
            else:
                # No access for anonymous
                authorised = False

        return authorised


    # -------------------------------------------------------------------------
    def shn_accessible_query(self, method, table):

        """
            Returns a query with all accessible records for the current logged in user
            @note: This method does not work on GAE because it uses JOIN and IN
        """

        db = self.db
        session = self.session
        T = self.environment.T

        # If using the "simple" security policy then show all records
        if session.s3.security_policy == 1:
            # simple
            return table.id > 0
        # If using the "editor" security policy then show all records
        elif session.s3.security_policy == 2:
            # editor
            return table.id > 0
        # Administrators can see all data
        if self.shn_has_role(1):
            return table.id > 0
        # If there is access to the entire table then show all records
        try:
            user_id = self.user.id
        except:
            user_id = 0
        if self.has_permission(method, table, 0, user_id):
            return table.id > 0
        # Filter Records to show only those to which the user has access
        session.warning = T("Only showing accessible records!")
        membership = self.settings.table_membership
        permission = self.settings.table_permission
        return table.id.belongs(db(membership.user_id == user_id)\
                           (membership.group_id == permission.group_id)\
                           (permission.name == method)\
                           (permission.table_name == table)\
                           ._select(permission.record_id))


    # -------------------------------------------------------------------------
    def shn_register(self, form):
        """
        S3 framework function

        Designed to be used as an onaccept callback for register()

        Whenever someone registers, it:
            - adds them to the 'Authenticated' role
            - adds their name to the Person Registry

        """

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        self.add_membership(authenticated, form.vars.id)

        # S3: Add to Person Registry as well and Email to pr_pe_contact
        self.shn_link_to_person(user=form.vars)


    # -------------------------------------------------------------------------
    def shn_has_membership(self, group_id=None, user_id=None, role=None):
        """
        Checks if user is member of group_id or role

        Extends Web2Py's requires_membership() to add new functionality:
            - Custom Flash style
            - Uses shn_has_role()

        """

        group_id = group_id or self.id_group(role)
        try:
            group_id = int(group_id)
        except:
            group_id = self.id_group(group_id) # interpret group_id as a role

        if self.shn_has_role(group_id):
            r = True
        else:
            r = False

        log = self.messages.has_membership_log
        if log:
            if not user_id and self.user:
                user_id = self.user.id
            self.log_event(log % dict(user_id=user_id,
                                      group_id=group_id, check=r))
        return r

    # Override original method
    has_membership = shn_has_membership


    # -------------------------------------------------------------------------
    def shn_requires_membership(self, role):
        """
        Decorator that prevents access to action if not logged in or
        if user logged in is not a member of group_id.
        If role is provided instead of group_id then the group_id is calculated.

        Extends Web2Py's requires_membership() to add new functionality:
            - Custom Flash style
            - Uses shn_has_role()
            - Administrators (id=1) are deemed to have all roles

        """

        def decorator(action):

            def f(*a, **b):
                if not self.shn_logged_in():
                    request = self.environment.request
                    next = URL(r=request, args=request.args, vars=request.get_vars)
                    redirect(self.settings.login_url + "?_next=" + urllib.quote(next))

                if not self.shn_has_role(role) and not self.shn_has_role(1):
                    self.environment.session.error = self.messages.access_denied
                    next = self.settings.on_failed_authorization
                    redirect(next)

                return action(*a, **b)

            f.__doc__ = action.__doc__

            return f

        return decorator

    # Override original method
    requires_membership = shn_requires_membership


    # -------------------------------------------------------------------------
    def shn_link_to_person(self, user=None):

        """
        Links user accounts to person registry entries

        Policy for linking to pre-existing person records:

        If and only if:
            - a person record with exactly the same first name and
              last name exists, which has a contact information record
              with exactly the same email address as used in the user
              account, and which is not linked to another user account,
              then this person record will be linked to this user account,

        otherwise:
            - a new person record is created, and a new email contact
              record with the email address from the user record is
              registered for that person

        """

        db = self.db
        utable = self.settings.table_user
        ptable = db.pr_person
        ctable = db.pr_pe_contact
        etable = db.pr_pentity

        if user is None:
            users = db(utable.person_uuid == None).select(utable.ALL)
        else:
            users = [user]

        for user in users:
            if "email" in user:

                first_name = user.first_name
                last_name = user.last_name
                email = user.email.lower()

                query = (ptable.first_name == first_name) & \
                        (ptable.last_name == last_name) & \
                        (ctable.pe_id == ptable.pe_id) & \
                        (ctable.contact_method == 1) & \
                        (ctable.value.lower() == email)
                person = db(query).select(ptable.uuid).first()
                if person:
                    if not db(utable.person_uuid == person.uuid).count():
                        db(utable.id == user.id).update(person_uuid=person.uuid)
                        if self.user and self.user.id == user.id:
                            self.user.person_uuid = person.uuid
                        continue

                pe_id = etable.insert(instance_type="pr_person", deleted=False)
                if pe_id:
                    new_id = ptable.insert(
                        pe_id = pe_id,
                        first_name = user.first_name,
                        last_name = user.last_name)
                    if new_id:
                        person_uuid = ptable[new_id].uuid
                        db(utable.id == user.id).update(person_uuid=person_uuid)
                        db(etable.id == pe_id).update(uuid=person_uuid)
                        # The following adds the email to pr_pe_contact
                        ctable.insert(
                                pe_id = pe_id,
                                contact_method = 1,
                                priority = 1,
                                value = email)
                        # The following adds the mobile to pr_pe_contact
                        mobile = self.environment.request.vars.get("mobile", None)
                        if mobile:
                            ctable.insert(
                                    pe_id = pe_id,
                                    contact_method = 2,
                                    priority = 2,
                                    value = mobile)

                if self.user and self.user.id == user.id:
                    self.user.person_uuid = person_uuid


# =============================================================================
class S3Permission(object):

    """
    S3 Class to handle permissions

    @author: Dominic König <dominic@aidiq.com>
    @status: work in progress

    """

    TABLENAME = "s3_permission"

    CREATE = 0x0001
    READ   = 0x0002
    UPDATE = 0x0004
    DELETE = 0x0008

    ALL = CREATE | READ | UPDATE | DELETE
    NONE = 0x0000 # must be 0!

    PERMISSION_OPTS = OrderedDict([
        #(NONE, "NONE"),
        [CREATE, "CREATE"],
        [READ  , "READ"],
        [UPDATE, "UPDATE"],
        [DELETE, "DELETE"],
        #(READ, "READ"),
        #(CREATE|UPDATE|DELETE, "WRITE")
    ])

    # Method string <-> required permission
    METHODS = Storage(
        create = CREATE,
        read = READ,
        update = UPDATE,
        delete = DELETE
    )

    # Policy helpers
    most_permissive = lambda self, acl: \
                             reduce(lambda x, y: (x[0]|y[0], x[1]|y[1]),
                                    acl, (self.NONE, self.NONE))
    most_restrictive = lambda self, acl: \
                              reduce(lambda x, y: (x[0]&y[0], x[1]&y[1]),
                                     acl, (self.ALL, self.ALL))

    # -------------------------------------------------------------------------
    def __init__(self, auth, environment, tablename=None):
        """
        Constructor, invoked by AuthS3.__init__

        @param auth: the authorization manager
        @param environment: the global environment
        @param tablename: the name for the permissions table

        """

        # Instantiated once per request, but before Auth tables
        # are defined and authentication is checked, thus no use
        # to check permissions in the constructor

        # Auth
        self.auth = auth

        # Configuration
        # @todo: read from deployment settings
        self.skip_table_acls = False

        # Environment
        env = Storage(environment)
        self.session = env.session
        self.db = env.db

        # Permissions table
        self.tablename = tablename or self.TABLENAME
        self.table = self.db.get(self.tablename, None)

        # Error messages
        T = env.T
        self.INSUFFICIENT_PRIVILEGES = T("Insufficient Privileges")
        self.AUTHENTICATION_REQUIRED = T("Authentication Required")

        # Settings
        self.migrate = env.migrate
        self.modules = env.deployment_settings.modules

        # Request information
        request = env.request
        self.controller = request.controller
        self.function = request.function

        # Request format
        self.format = request.extension
        if "format" in request.get_vars:
            ext = request.get_vars.format
            if isinstance(ext, list):
                ext = ext[-1]
            self.format = ext.lower() or self.format
        else:
            ext = [a for a in request.args if "." in a]
            if ext:
                self.format = ext[-1].rsplit(".", 1)[1].lower()

        # Page permission cache
        self.page_acls = Storage()
        self.table_acls = Storage()

        # Pages which never require permission
        self.unrestricted_pages = (
            "default/index",
            "default/user",
            "default/contact",
            "default/about")

        # Default landing pages
        _next = URL(r=request, args=request.args, vars=request.vars)
        self.homepage = URL(r=request, c="default", f="index")
        self.loginpage = URL(r=request, c="default", f="user/login",
                             vars=dict(_next=_next))


    # -------------------------------------------------------------------------
    def define_table(self):
        """
        Define permissions table, invoked by AuthS3.define_tables

        """

        table_group = self.auth.settings.table_group
        if table_group is None:
            table_group = "integer" # fallback

        if not self.table:
            self.table = self.db.define_table(self.tablename,
                            Field("group_id", table_group),
                            Field("controller", length=64),
                            Field("function", length=512),
                            Field("tablename", length=512),
                            Field("oacl", "integer", default=self.ALL),
                            Field("uacl", "integer", default=self.READ),
                            migrate=self.migrate)


    # -------------------------------------------------------------------------
    def __call__(self,
                 c=None,
                 f=None,
                 table=None,
                 record=None):
        """
        Get the ACL for the current user for a path

        @param c: the controller name (falls back request.controller)
        @param f: the function name (falls back to request.function)
        @param table: the table
        @param record: the record ID (or the Row if already loaded)

        @note: if passing a Row, it must contain all available ownership
               fields (id, created_by, owned_by), otherwise the record
               will be re-loaded by this function

        """

        #return self.ALL # not used yet

        ADMIN = 1
        EDITOR = 4

        t = self.table # Permissions table

        # Get user roles
        roles = []
        if self.session.s3 is not None:
            roles = self.session.s3.roles or []
        if ADMIN in roles:
            return self.ALL

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        # Check controller permission in deployment settings
        # @todo: deprecate!
        if c in self.modules:
            module = self.modules[c]
            if module.access:
                # Module is restricted by deployment settings
                groups = re.split("\|", module.access)[1:-1]
                proles = [r for r in groups if int(r) in roles]
                if proles or self.format in ("json", "popup"):
                    return self.ALL
                else:
                    return self.NONE

        page_acl = self.page_acl(c=c, f=f)

        # Done?
        if table is None or self.skip_table_acls:
            acl = page_acl[0] | page_acl[1]
            return acl

        # Get the table ACL
        if EDITOR in roles:
            table_acl = (self.ALL, self.ALL)
        else:
            table_acl = self.table_acl(table=table, c=c)

        # Overall policy
        acl = self.most_restrictive((page_acl, table_acl))

        if acl[0] == self.NONE and acl[1] == self.NONE:
            # No table access
            acl = self.NONE
        elif record is None:
            # No record specified
            acl = acl[1]
        else:
            # Check record ownership
            acl = self.is_owner(table, record) and acl[0] or acl[1]

        return acl


    # -------------------------------------------------------------------------
    def page_acl(self, c=None, f=None):
        """
        Get the ACL for a page

        @param c: the controller (falls back to current request)
        @param f: the function (falls back to current request)

        @returns: tuple of (ACL for owned resources, ACL for all resources)

        """

        t = self.table

        most_permissive = self.most_permissive

        roles = []
        if self.session.s3 is not None:
            roles = self.session.s3.roles or []

        c = c or self.controller
        f = f or self.function

        page = "%s/%s" % (c, f)
        if page in self.unrestricted_pages:
            page_acl = (self.ALL, self.ALL)
        else:
            page_acl = self.page_acls.get(page, None)
        if page_acl is None:
            q = ((t.controller == c) &
                ((t.function == f) | (t.function == None)))
            if roles:
                query = (t.group_id.belongs(roles)) & q
            else:
                query = (t.group_id == None) & q
            rows = self.db(query).select()
            if rows:
                # ACLs found, apply most permissive role
                controller_acl = []
                function_acl = []
                for row in rows:
                    if not row.function:
                        controller_acl += (row.oacl, row.uacl)
                    else:
                        function_acl += (row.oacl, row.uacl)
                controller_acl = most_permissive(controller_acl)
                function_acl = most_permissive(function_acl)
                page_acl = most_permissive((controller_acl, function_acl))
            else:
                # No ACL found for any of the roles
                restricted = self.db(q).select(t.id, limitby=(0, 1)).first()
                if restricted:
                    # Page is restricted, no access
                    page_acl = (self.NONE, self.NONE)
                elif roles:
                    # Authenticated user, full access
                    page_acl = (self.ALL, self.ALL)
                else:
                    # Anonymous user, read-only access
                    page_acl = (self.READ, self.READ)

            # Remember this result
            self.page_acls.update({page:page_acl})

        return page_acl


    # -------------------------------------------------------------------------
    def table_acl(self, table=None, c=None):
        """
        Get the ACL for a table

        @param table: the table
        @param c: the controller (falls back to current request)
        @returns: tuple of (ACL for owned resources, ACL for all resources)

        """

        if table is None:
            return self.page_acl(c=c)

        t = self.table

        roles = []
        if self.session.s3 is not None:
            roles = self.session.s3.roles or []

        c = c or self.controller

        # Already loaded?
        tablename = table._tablename
        table_acl = self.table_acls.get(tablename, None)

        if table_acl is None:
            q = ((t.tablename == tablename) &
                ((t.controller == c) | (t.controller == None)))
            if roles:
                query = (t.group_id.belongs(roles)) & q
            else:
                query = (t.group_id == None) & q
            rows = self.db(query).select()
            table_acl = [(r.oacl, r.uacl) for r in rows]
            if table_acl:
                # ACL found, apply most permissive role
                table_acl = self.most_permissive(table_acl)
            else:
                # No ACL found for any of the roles
                restricted = self.db(q).select(t.id, limitby=(0, 1)).first()
                if restricted:
                    # Table is restricted, no access
                    table_acl = (self.NONE, self.NONE)
                elif roles:
                    # Authenticated user, full access
                    table_acl = (self.ALL, self.ALL)
                else:
                    # Anonymous user, read-only access
                    table_acl = (self.READ, self.READ)

            # Remember this result
            self.table_acls.update({tablename:table_acl})

        return table_acl


    # -------------------------------------------------------------------------
    def is_owner(self, table, record):
        """
        Establish the ownership of a record

        @param table: the table
        @param record: the record ID (or the Row if already loaded)

        @note: if passing a Row, it must contain all available ownership
               fields (id, created_by, owned_by), otherwise the record
               will be re-loaded by this function

        """

        user_id = None
        roles = []

        if self.auth.user is not None:
            user_id = self.auth.user.id
        if self.session.s3 is not None:
            roles = self.session.s3.roles or []

        if not user_id and not roles:
            return False
        elif 1 in roles:
            return True
        else:
            record_id = None
            ownership_fields = ("created_by", "owned_by")
            fields = [f for f in ownership_fields if f in table.fields]
            if not fields:
                return True # Ownership is undefined
            if isinstance(record, Row):
                missing = [f for f in fields if f not in record]
                if missing:
                    if "id" in record:
                        record_id = record.id
                    record = None
            else:
                record_id = record
                record = None
            if not record and fields:
                fs = [table[f] for f in fields] + [table.id]
                record = self.db(table.id == record_id).select(limitby=(0,1), *fs).first()
            if not record:
                return False # Record does not exist

            creator = owner = None
            if "created_by" in table.fields:
                creator = record.created_by
            if "owned_by" in table.fields:
                owner = record.owned_by

            return not creator and not owner or \
                   creator == user_id or owner in roles


    # -------------------------------------------------------------------------
    def accessible_query(self, table, *methods):
        """
        Query for records which the user is permitted to access with method

        @param table: the DB table
        @param methods: list of methods for which permission is required (AND),
                        any combination "create", "read", "update", "delete"

        Example::
            query = auth.permission.accessible_query(table, "read", "update")

        """

        required = self.METHODS

        # Default query
        pkey = table.fields[0]
        query = (table[pkey] != None)

        # Required ACL
        racl = reduce(lambda a, b: a | b,
                     [required[m] for m in methods if m in required], self.NONE)
        if not racl:
            return query

        # User & Roles
        user_id = None
        if self.auth.user is not None:
            user_id = self.auth.user.id
        roles = []
        if self.session.s3 is not None:
            roles = self.session.s3.roles or []

        # Available ACLs
        pacl = self.page_acl()
        tacl = self.table_acl(table)
        acl = (tacl[0] & pacl[0], tacl[1] & pacl[1])

        # Ownership required?
        permitted = (acl[0] | acl[1]) & racl == racl
        if not permitted:
            query = (table[pkey] == None)
            ownership_required = False
        elif "owned_by" in table or "created_by" in table:
            ownership_required = permitted and acl[1] & racl != racl

        # Generate query
        if ownership_required:
            query = None
            if "owned_by" in table:
                query = (table.owned_by.belongs(roles))
            if "created_by" in table:
                q = (table.created_by == user_id)
                if query is not None:
                    query = (query | q)
                else:
                    query = q

        return query


    # -------------------------------------------------------------------------
    def has_permission(self, table, record=None, method=None):
        """
        Check permission to access a record

        @param table: the table
        @param record: the record or record ID (None for any record)
        @param method: the method (or tuple/list of methods),
                       any of "create", "read", "update", "delete"

        @note: when submitting a record, the record ID and the ownership
               fields (="created_by", "owned_by") must be contained if
               available, otherwise the record will be re-loaded

        """

        required = self.METHODS

        if not isinstance(method, (list, tuple)):
            method = [method]

        # Required ACL
        racl = reduce(lambda a, b: a | b,
                     [required[m] for m in method if m in required], self.NONE)

        # Available ACL
        aacl = self(table=table, record=record)

        permitted = racl & aacl == racl
        return permitted


    # -------------------------------------------------------------------------
    def fail(self):
        """
        Action upon insufficient permissions

        """

        if self.format == "html":
            # HTML interactive request => flash message + redirect
            if self.auth.shn_logged_in():
                self.session.error = self.INSUFFICIENT_PRIVILEGES
                redirect(self.homepage)
            else:
                self.session.error = self.AUTHENTICATION_REQUIRED
                redirect(self.loginpage)
        else:
            # non-HTML request => raise proper HTTP error
            if self.auth.shn_logged_in():
                raise HTTP(403)
            else:
                raise HTTP(401)


# =============================================================================
class S3Audit(object):

    """
    S3 Audit Trail Writer Class

    @author: Dominic König <dominic@aidiq.com>

    """

    def __init__(self, db, session,
                 tablename="s3_audit",
                 migrate=True):
        """
        Constructor

        @param db: the database
        @param session: the current session
        @param tablename: the name of the audit table
        @param migrate: migration setting

        @note: this defines the audit table

        """

        self.db = db
        self.table = db.get(tablename, None)
        if not self.table:
            self.table = db.define_table(tablename,
                            Field("timestmp", "datetime"),
                            Field("person", "integer"),
                            Field("operation"),
                            Field("tablename"),
                            Field("record", "integer"),
                            Field("representation"),
                            Field("old_value", "text"),
                            Field("new_value", "text"),
                            migrate=migrate)

        self.session = session
        if session.auth and session.auth.user:
            self.user = session.auth.user.id
        else:
            self.user = None


    # -------------------------------------------------------------------------
    def __call__(self, operation, prefix, name,
                 form=None,
                 record=None,
                 representation="unknown"):
        """
        Audit

        @param operation: Operation to log, one of
            "create", "update", "read", "list" or "delete"
        @param prefix: the module prefix of the resource
        @param name: the name of the resource (without prefix)
        @param form: the form
        @param record: the record ID
        @param representation: the representation format

        """

        settings = self.session.s3

        #print >>sys.stderr, "Audit %s: %s_%s record=%s representation=%s" % (operation, prefix, name, record, representation)

        now = datetime.datetime.utcnow()
        db = self.db
        table = self.table
        tablename = "%s_%s" % (prefix, name)

        if record:
            if isinstance(record, Row):
                record = record.get("id", None)
                if not record:
                    return True
            try:
                record = int(record)
            except ValueError:
                record = None
        else:
            record = None

        if operation in ("list", "read"):
            if settings.audit_read:
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation)

        elif operation in ("create", "update"):
            if settings.audit_write:
                if form:
                    record =  form.vars.id
                    new_value = ["%s:%s" % (var, str(form.vars[var]))
                                 for var in form.vars]
                else:
                    new_value = []
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             new_value = new_value)

        elif operation == "delete":
            if settings.audit_write:

                row = db(db[tablename].id == record).select(limitby=(0, 1)).first()
                old_value = []
                if row:
                    old_value = ["%s:%s" % (field, row[field]) for field in row]
                table.insert(timestmp = now,
                             person = self.user,
                             operation = operation,
                             tablename = tablename,
                             record = record,
                             representation = representation,
                             old_value = old_value)

        return True


# =============================================================================
class S3RoleManager(S3Method):

    """ REST Method to manage ACLs

        @status: work in progress

    """

    # Controllers to hide from the permissions matrix
    HIDE_CONTROLLER = ("admin", "default")

    # Roles to hide from the permissions matrix
    PROTECTED_ROLES = (1, 3, 4)

    controllers = Storage()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
        Apply role manager

        """

        method = self.method

        if method == "list":
            output = self.matrix(r, **attr)
        elif method in ("read", "create", "update"):
            output = self._edit(r, **attr)
        elif method in ("users"):
            output = self._user(r, **attr)
        else:
            r.error(501, self.manager.ERROR.BAD_METHOD)

        return output


    # -------------------------------------------------------------------------
    def matrix(self, r, **attr):
        """
        Role/Permission matrix

        """

        output = dict()

        request = self.request
        resource = self.resource
        auth = self.manager.auth

        T = self.T

        if r.id:
            return self._edit(r, **attr)

        show_matrix = request.get_vars.get("matrix", False) and True

        if r.interactive:

            # Title and subtitle
            output.update(title = T("List of Roles"), subtitle = T("Roles"))

            # Filter out protected roles
            resource.add_filter(~(self.table.id.belongs(self.PROTECTED_ROLES)))
            resource.load()

            # Get active controllers
            controllers = [c for c in self.controllers.keys()
                             if c not in self.HIDE_CONTROLLER]

            # ACLs
            table_acl = auth.permission.table
            query = resource.get_query()
            query = query & (table_acl.group_id == self.table.id) # & (table_acl.function == None)

            rows = self.db(query).select(table_acl.ALL)

            acls = Storage()
            for row in rows:
                if row.controller not in acls.keys():
                    acl = acls[row.controller] = Storage()
                    acl[row.group_id] = Storage(oacl = row.oacl, uacl = row.uacl)

            # Table header
            headers = [TH("ID"), TH(T("Role"))]
            if show_matrix:
                headers += [TH(self.controllers[c].name_nice) for c in controllers]
            else:
                headers += [TH(T("Description"))]
            thead = THEAD(TR(headers))

            # Table body
            trows = []
            i = 1
            for row in resource:

                role_id = row.id
                role_name = row.role
                role_desc = row.description

                action_button = lambda l, i, m: A(l, _href=URL(r=request,
                                                            c="admin",
                                                            f="role",
                                                            args=(m and [i, m] or [i]),
                                                            vars=request.get_vars),
                                                            _class="action-btn")

                role_edit = action_button(T("Edit"), role_id, None)
                role_delete = action_button(T("Delete"), role_id, "delete")
                role_users = action_button(T("Users"), role_id, "users")

                tdata = [TD(role_edit, XML("&nbsp;"),
                            role_delete, XML("&nbsp;"),
                            role_users), TD(role_name)]

                if show_matrix:
                    # Display the permission matrix
                    for c in controllers:
                        if c in acls:
                            if role_id in acls[c]:
                                acl = (acls[c][role_id].oacl, acls[c][role_id].uacl)
                            else:
                                acl = (auth.permission.NONE, auth.permission.NONE)
                        else:
                            acl = (auth.permission.ALL, auth.permission.ALL)

                        oacl = ""
                        uacl = ""
                        options = auth.permission.PERMISSION_OPTS
                        for o in options:
                            if o == 0 and acl[0] == 0:
                                oacl = "%s%s" % (oacl, options[o][0])
                            elif acl[0] and acl[0] & o:
                                oacl = "%s%s" % (oacl, options[o][0])
                            else:
                                oacl = "%s-" % oacl
                            if o == 0 and acl[1] == 0:
                                uacl = "%s%s" % (uacl, options[o][0])
                            elif acl[1] and acl[1] & o:
                                uacl = "%s%s" % (uacl, options[o][0])
                            else:
                                uacl = "%s-" % uacl
                        values = "%s (%s)" % (uacl, oacl)
                        tdata += [TD(values, _nowrap="nowrap")]
                else:
                    # Display role descriptions
                    tdata += [TD(role_desc)]

                c = i % 2 and "even" or "odd"
                trows.append(TR(tdata, _class=c))
            tbody = TBODY(trows)

            items = TABLE(thead, tbody, _id="list", _class="display")
            output.update(items=items, sortby=[[1, 'asc']])

            self.response.view = self._view(r, "list.html")
            self.response.s3.actions = []
            self.response.s3.no_sspag = True

        elif r.representation == "xls":
            # Not implemented yet
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        else:
            r.error(501, self.manager.ERROR.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def _edit(self, r, **attr):
        """
        Create/update roles

        """

        output = dict()

        request = self.request
        session = self.session
        auth = self.manager.auth
        db = self.db
        T = self.T

        settings = self.manager.s3.crud

        if r.interactive:

            # Get the current record (if any)
            if r.record:
                output.update(title=T("Edit Role"))
                role_name = r.record.role
                role_desc = r.record.description
            else:
                output.update(title=T("Create Role"))
                role_name = None
                role_desc = None

            # ACL Widget
            acl_table = db.s3_permission
            acl_table.oacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
            acl_table.uacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
            acl_widget = lambda f, v: S3ACLWidget.widget(acl_table[f], v, _name=f)

            oacl = acl_widget("oacl", auth.permission.NONE)
            uacl = acl_widget("uacl", auth.permission.NONE)

            # Form style from CRUD settings
            formstyle = settings.formstyle

            # Role form
            form_rows = formstyle("role_name", DIV(T("Role Name"), XML("&nbsp;"), SPAN("*", _class="req")),
                                  INPUT(value=role_name,
                                        _name="role_name",
                                        _type="text"), "") + \
                        formstyle("role_desc", T("Description"),
                                  TEXTAREA(value=role_desc,
                                           _name="role_desc",
                                           _rows="4"), "")
            role_form = DIV(TABLE(form_rows), _id="role_form")

            # ACL form
            level = request.get_vars.get("acl", "controller")
            if level == "table":
                acl_form = DIV([], _id="acl_form")
            else:
                form_rows = (TR(TD("Controller"),
                                TD("Function"),
                                TD(uacl),
                                TD(oacl)))

                acl_form = DIV(TABLE(form_rows), _id="acl_form")

            # Action row
            action_row = DIV(INPUT(_type="submit", _value="Save"), _id="action_row")

            # Aggregate form
            form = FORM(role_form, acl_form, action_row)

            # Process the form
            if form.accepts(request.post_vars, session):
                print "title=%s" % form.vars.t1
                print "description=%s" % form.vars.t2
                print "uacl=%s" % form.vars.uacl
                print "oacl=%s" % form.vars.oacl
                redirect(URL(r=request, f="role", vars=request.get_vars))

            output.update(form=form)

            self.response.error = self.T("EDIT Not Implemented Yet")
            self.response.view = "admin/role_update.html"
        else:
            r.error(501, self.manager.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def _user(self, r, **attr):
        """
        See/modify users with a role

        """

        output = dict()

        self.response.error = self.T("USERS Not Implemented Yet")

        self.response.view = self._view(r, "display.html")
        return output

# =============================================================================
