# -*- coding: utf-8 -*-

""" Authentication, Authorization, Accouting

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: (c) 2010-2011 Sahana Software Foundation
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
from gluon.dal import Field, Row, Query, Set, Table, Expression
from gluon.sqlhtml import SQLFORM, SQLTABLE, CheckboxesWidget
from gluon.tools import Auth, callback
from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3rest import S3Method
from s3widgets import S3ACLWidget
from s3validators import IS_ACL, IS_ONE_OF

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
                verify_email()
                requires_membership()

            - add:
                s3_has_role()
                s3_has_permission()
                s3_logged_in()
                s3_accessible_query()
                s3_register() callback
                s3_link_to_person()
                s3_group_members()
                s3_user_to_person()
                s3_person_to_user()
                person_id()

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
        self.messages.duplicate_email = "This email address is already in use"
        self.messages.registration_disabled = "Registration Disabled!'"
        self.messages.registration_verifying = "You haven't yet Verified your account - please check your email"
        self.messages.label_utc_offset = "UTC Offset"
        self.messages.help_utc_offset = "The time difference between UTC and your timezone, specify as +HHMM for eastern or -HHMM for western timezones."
        self.messages.label_mobile_phone = "Mobile Phone"
        self.messages.help_mobile_phone = "Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages."
        self.messages.label_organisation = "Organisation"
        self.messages.help_organisation = "Entering an Organisation is optional, but doing so directs you to the appropriate approver & means you automatically get the appropriate permissions."
        self.messages.lock_keys = True

        self.permission = S3Permission(self, environment)

        T = self.environment.T
        self.org_site_types = Storage(
                                cr_shelter = T("Shelter"),
                                org_office = T("Office"),
                                hms_hospital = T("Hospital"),
                            )



    # -------------------------------------------------------------------------
    def __get_migrate(self, tablename, migrate=True):

        if type(migrate).__name__ == "str":
            return ("%s%s.table" % (migrate, tablename))
        elif migrate == False:
            return False
        else:
            return True


    # -------------------------------------------------------------------------
    def define_tables(self, migrate=True):

        """
            to be called unless tables are defined manually

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
        settings = self.settings
        messages = self.messages

        # User table
        if not settings.table_user:
            passfield = settings.password_field
            if settings.username_field:
                # with username (not used by default in Sahana)
                settings.table_user = db.define_table(
                    settings.table_user_name,
                    Field("first_name", length=128, default="",
                          label=messages.label_first_name),
                    Field("last_name", length=128, default="",
                          label=messages.label_last_name),
                    Field("person_uuid", length=64, default="",
                          readable=False, writable=False),
                    Field("utc_offset", length=16,
                          readable=False, writable=False),
                    Field("username", length=128, default=""),
                    Field("language", length=16),
                    Field("email", length=512, default="",
                          label=messages.label_email),
                    Field(passfield, "password", length=512,
                          readable=False, label=messages.label_password),
                    Field("registration_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("reset_password_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("deleted", "boolean", writable=False,
                          readable=False, default=False),
                    Field("timestmp", "datetime", writable=False,
                          readable=False, default=""),
                    migrate = self.__get_migrate(settings.table_user_name,
                                                 migrate))
            else:
                # with email-address (Sahana default)
                settings.table_user = db.define_table(
                    settings.table_user_name,
                    Field("first_name", length=128, default="",
                          label=messages.label_first_name),
                    Field("last_name", length=128, default="",
                          label=messages.label_last_name),
                    Field("person_uuid", length=64, default="",
                          readable=False, writable=False),
                    Field("utc_offset", length=16,
                          readable=False, writable=False, label=messages.label_utc_offset),
                    Field("language", length=16),
                    Field("email", length=512, default="",
                          label=messages.label_email),
                    Field(passfield, "password", length=512,
                          readable=False, label=messages.label_password),
                    Field("registration_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("reset_password_key", length=512,
                          writable=False, readable=False, default="",
                          label=messages.label_registration_key),
                    Field("deleted", "boolean", writable=False,
                          readable=False, default=False),
                    Field("timestmp", "datetime", writable=False,
                          readable=False, default=""),
                    migrate = self.__get_migrate(settings.table_user_name,
                                                 migrate))
            table = settings.table_user
            table.first_name.requires = \
                IS_NOT_EMPTY(error_message=messages.is_empty)
            #table.last_name.requires = \
                #IS_NOT_EMPTY(error_message=messages.is_empty)
            table.utc_offset.comment = A(SPAN("[Help]"),
                                         _class="tooltip",
                                         _title="%s|%s" % (messages.label_utc_offset,
                                                           messages.help_utc_offset))
            try:
                from s3validators import IS_UTC_OFFSET
                table.utc_offset.requires = IS_EMPTY_OR(IS_UTC_OFFSET())
            except:
                pass
            table[passfield].requires = [CRYPT(key=settings.hmac_key,
                                               digest_alg="sha512")]
            if settings.username_field:
                table.username.requires = IS_NOT_IN_DB(db,
                                                       "%s.username" % settings.table_user._tablename)
            table.email.requires = \
                [IS_EMAIL(error_message=messages.invalid_email),
                 IS_NOT_IN_DB(db,
                              "%s.email" % settings.table_user._tablename,
                              error_message=messages.duplicate_email)]
            table.registration_key.default = ""

        # Group table (roles)
        if not settings.table_group:
            settings.table_group = db.define_table(
                settings.table_group_name,
                Field("role", length=512, default="",
                      label=messages.label_role),
                Field("description", "text",
                      label=messages.label_description),
                migrate = self.__get_migrate(settings.table_group_name,
                                             migrate))
            table = settings.table_group
            table.role.requires = IS_NOT_IN_DB(db, "%s.role"
                 % settings.table_group._tablename)

        # Group membership table (user<->role)
        if not settings.table_membership:
            settings.table_membership = db.define_table(
                settings.table_membership_name,
                Field("user_id", settings.table_user,
                      label=messages.label_user_id),
                Field("group_id", settings.table_group,
                      label=messages.label_group_id),
                migrate = self.__get_migrate(settings.table_membership_name,
                                             migrate))
            table = settings.table_membership
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_group._tablename,
                    "%(id)s: %(role)s")

        # Permissions table (group<->permission)
        # NB This Web2Py table is deprecated / replaced in Eden by S3Permission
        if not settings.table_permission:
            settings.table_permission = db.define_table(
                settings.table_permission_name,
                Field("group_id", settings.table_group,
                      label=messages.label_group_id),
                Field("name", default="default", length=512,
                      label=messages.label_name),
                Field("table_name", length=512,
                      label=messages.label_table_name),
                Field("record_id", "integer",
                      label=messages.label_record_id),
                migrate = self.__get_migrate(
                    settings.table_permission_name, migrate))
            table = settings.table_permission
            table.group_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_group._tablename,
                    "%(id)s: %(role)s")
            table.name.requires = IS_NOT_EMPTY()
            table.table_name.requires = IS_IN_SET(self.db.tables)
            table.record_id.requires = IS_INT_IN_RANGE(0, 10 ** 9)

        # Event table (auth log)
        if not settings.table_event:
            settings.table_event = db.define_table(
                settings.table_event_name,
                Field("time_stamp", "datetime",
                      default=self.environment.request.now,
                      label=messages.label_time_stamp),
                Field("client_ip",
                      default=self.environment.request.client,
                      label=messages.label_client_ip),
                Field("user_id", settings.table_user, default=None,
                      label=messages.label_user_id),
                Field("origin", default="auth", length=512,
                      label=messages.label_origin),
                Field("description", "text", default="",
                      label=messages.label_description),
                migrate = self.__get_migrate(settings.table_event_name,
                                             migrate))
            table = settings.table_event
            table.user_id.requires = IS_IN_DB(db, "%s.id" %
                    settings.table_user._tablename,
                    "%(id)s: %(first_name)s %(last_name)s")
            table.origin.requires = IS_NOT_EMPTY()
            table.description.requires = IS_NOT_EMPTY()

        # Define permission table
        self.permission.define_table()


    # -------------------------------------------------------------------------
    def login_bare(self, username, password):
        """
            Logs user in
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
    def set_cookie(self):
        """
            Set a Cookie to the client browser so that we know this user has
            registered & so we should present them with a login form instead
            of a register form
        """

        response = self.environment.response

        response.cookies["registered"] = "yes"
        response.cookies["registered"]["expires"] = 365 * 24 * 3600    # 1 year
        response.cookies["registered"]["path"] = "/"

    # -------------------------------------------------------------------------
    def login(self,
              next=DEFAULT,
              onvalidation=DEFAULT,
              onaccept=DEFAULT,
              log=DEFAULT):
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
                query = (table_user[username] == form.vars[username])
                users = self.db(query).select()
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
                    redirect(self.url(args=request.args,
                                      vars=request.get_vars))
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
                next = "%s?_next=%s" % (URL(r=request), next)
                redirect(cas.login_url(next))

        # process authenticated users
        if user:
            user = Storage(table_user._filter_fields(user, id=True))
            session.auth = Storage(user=user, last_visit=request.now,
                                   expiration=self.settings.expiration)
            self.user = user
            session.confirmation = self.messages.logged_in
            # Set a Cookie to present user with login box by default
            self.set_cookie()
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
    def register(self,
                 next=DEFAULT,
                 onvalidation=DEFAULT,
                 onaccept=DEFAULT,
                 log=DEFAULT):
        """
            Overrides Web2Py's register() to add new functionality:
                - Checks whether registration is permitted
                - Custom Flash styles
                - Allow form to be embedded in other pages
                - Optional addition of Mobile Phone field to the Register form
                - Optional addition of Organisation field to the Register form
                - Lookup Domains/Organisations to check for Whitelists
                  &/or custom Approver

            @returns: a registration form
        """

        db = self.db
        settings = self.settings
        messages = self.messages
        request = self.environment.request
        response = self.environment.response
        session = self.environment.session
        deployment_settings = self.deployment_settings

        # S3: Don't allow registration if disabled
        self_registration = deployment_settings.get_security_self_registration()
        if not self_registration:
            session.error = messages.registration_disabled
            redirect(URL(r=request, args=["login"]))

        if self.is_logged_in() and request.function != "index":
            redirect(settings.logged_url)

        if next == DEFAULT:
            next = request.vars._next or settings.register_next
        if onvalidation == DEFAULT:
            onvalidation = settings.register_onvalidation
        if onaccept == DEFAULT:
            onaccept = settings.register_onaccept
        if log == DEFAULT:
            log = messages.register_log

        user = settings.table_user

        passfield = settings.password_field
        form = SQLFORM(user, hidden=dict(_next=request.vars._next),
                       showid=settings.showid,
                       submit_button=messages.submit_button,
                       delete_label=messages.delete_label)
        for i, row in enumerate(form[0].components):
            item = row[1][0]
            if isinstance(item, INPUT) and item["_name"] == passfield:
                form[0].insert(i + 1, TR(
                        TD(LABEL("%s:" % messages.verify_password),
                                 _class="w2p_fl"),
                        INPUT(_name="password_two",
                              _type="password",
                              requires=IS_EXPR("value==%s" % \
                               repr(request.vars.get(passfield, None)),
                        error_message=messages.mismatched_password)),
                        SPAN("*", _class="req"),
                "", _class="%s_%s__row" % (user, "password_two")))

        # S3: Insert Mobile phone field into form
        if deployment_settings.get_auth_registration_requests_mobile_phone():
            form[0].insert(-4,
                           TR(TD(LABEL("%s:" % messages.label_mobile_phone),
                                       _class="w2p_fl"),
                                 INPUT(_name="mobile", _id="mobile"),
                              TD(DIV(_class="tooltip",
                                     _title="%s|%s" % (messages.label_mobile_phone,
                                                       messages.help_mobile_phone)))))

        # S3: Insert Organisation field into form
        # @ToDo: Widget (ideally Combobox for < 50 entries)
        if deployment_settings.get_auth_registration_requests_organisation():
            organisations = db(db.org_organisation.deleted != True).select(db.org_organisation.id, db.org_organisation.name)
            options = [OPTION(r.name, _value=r.id) for r in organisations]
            form[0].insert(-4,
                           TR(TD(LABEL("%s:" % messages.label_organisation),
                                       _class="w2p_fl"),
                              TD(SELECT(OPTION(""), *options,
                                        _name="organisation",
                                        _id="organisation",
                                        requires = IS_NULL_OR(IS_ONE_OF(db, "org_organisation.id"))
                                        ),
                                 _class="w2p_fw"),
                              TD(DIV(_class="tooltip",
                                     _title="%s|%s" % (messages.label_organisation,
                                                       messages.help_organisation)))))

        if settings.captcha != None:
            form[0].insert(-1, TR("", settings.captcha, ""))

        user.registration_key.default = key = str(uuid.uuid4())

        if form.accepts(request.vars, session, formname="register",
                        onvalidation=onvalidation):

            if settings.create_user_groups:
                # Not used in S3
                description = \
                    "group uniquely assigned to %(first_name)s %(last_name)s"\
                     % form.vars
                group_id = self.add_group("user_%s" % form.vars.id,
                                          description)
                self.add_membership(group_id, form.vars.id)

            approved = False
            users = db(settings.table_user.id > 0).count()
            if users == 1:
                # 1st user to register shouldn't need verification/approval
                approved = True

            elif settings.registration_requires_verification:
                # Ensure that we add to the correct Organisation
                approver, organisation_id = self.s3_approver(form.vars)
                form.vars.organisation = organisation_id

                # Send the Verification email
                if not settings.mailer or \
                   not settings.mailer.send(to=form.vars.email,
                                            subject=messages.verify_email_subject,
                                            message=messages.verify_email % dict(key=key)):
                    db.rollback()
                    response.error = messages.invalid_email
                    return form
                session.confirmation = messages.email_sent

            elif settings.registration_requires_approval:
                # Identify the Approver &
                # ensure that we add to the correct Organisation
                approver, organisation_id = self.s3_approver(form.vars)
                form.vars.organisation = organisation_id

                if approver:
                    # Send the Authorisation email
                    form.vars.approver = approver
                    if not settings.mailer or \
                        not settings.verify_email_onaccept(form.vars):
                        # We don't wish to prevent registration if the approver mail fails to send
                        #db.rollback()
                        session.error = messages.email_approver_failed
                        #return form
                    user[form.vars.id] = dict(registration_key="pending")
                    session.warning = messages.registration_pending_approval
                else:
                    # The domain is Whitelisted
                    approved = True
            else:
                # No verification or approval needed
                approved = True

            # Set a Cookie to present user with login box by default
            self.set_cookie()

            if approved:
                user[form.vars.id] = dict(registration_key="")
                session.confirmation = messages.registration_successful

                table_user = settings.table_user
                if "username" in table_user.fields:
                    username = "username"
                else:
                    username = "email"
                query = (table_user[username] == form.vars[username])
                user = db(query).select(limitby=(0, 1)).first()
                user = Storage(table_user._filter_fields(user, id=True))

                if users == 1:
                    # Add the first user to admin group
                    admin_group_id = 1
                    self.add_membership(admin_group_id, user.id)

                session.auth = Storage(user=user, last_visit=request.now,
                                       expiration=settings.expiration)
                self.user = user
                session.flash = messages.logged_in

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
    def s3_register(self, form):
        """
            S3 framework function

            Designed to be used as an onaccept callback for register()

            Whenever someone registers, it:
                - adds them to the 'Authenticated' role
                - adds their name to the Person Registry
                - creates an entry in the Org_Staff table
        """

        db = self.db
        deployment_settings = self.deployment_settings

        # Add to 'Authenticated' role
        authenticated = self.id_group("Authenticated")
        self.add_membership(authenticated, form.vars.id)

        # Add to Person Registry and Email/Mobile to pr_contact
        person_id = self.s3_link_to_person(user=form.vars)

        organisation_id = form.vars.get("organisation",
                                        None)
        if organisation_id:
            # Create an Org_Staff entry
            table = db.pr_person
            staff_id = db.org_staff.insert(person_id=person_id,
                                           organisation_id=organisation_id)
            if deployment_settings.get_aaa_has_staff_permissions():
                # Add to the Staff Roles
                self.s3_update_staff_membership(record=Storage(id=staff_id))

    # -------------------------------------------------------------------------
    def s3_link_to_person(self, user=None):
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
        ctable = db.pr_contact
        etable = db.pr_pentity
        ttable = db.sit_trackable

        if user is None:
            users = db(utable.person_uuid == None).select(utable.ALL)
        else:
            users = [user]

        person_ids = []
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
                person = db(query).select(ptable.id, ptable.uuid).first()
                if person:
                    person_ids.append(person.id)
                    if not db(utable.person_uuid == person.uuid).count():
                        db(utable.id == user.id).update(person_uuid=person.uuid,
                                                        owned_by_user=user.id)
                        if self.user and self.user.id == user.id:
                            self.user.person_uuid = person.uuid
                        continue

                pe_id = etable.insert(instance_type="pr_person", deleted=False)
                track_id = ttable.insert(instance_type="pr_person", deleted=False)
                if pe_id:
                    new_id = ptable.insert(
                        pe_id = pe_id,
                        track_id = track_id,
                        first_name = user.first_name,
                        last_name = user.last_name,
                        owned_by_user = user.id
                        )
                    if new_id:
                        person_ids.append(new_id)
                        person_uuid = ptable[new_id].uuid
                        db(utable.id == user.id).update(person_uuid=person_uuid)
                        db(etable.id == pe_id).update(uuid=person_uuid)
                        db(ttable.id == track_id).update(uuid=person_uuid)
                        # Add the email to pr_contact
                        ctable.insert(
                                pe_id = pe_id,
                                contact_method = 1,
                                priority = 1,
                                value = email)
                        # Add the mobile to pr_contact
                        mobile = self.environment.request.vars.get("mobile",
                                                                   None)
                        if mobile:
                            ctable.insert(
                                    pe_id = pe_id,
                                    contact_method = 2,
                                    priority = 2,
                                    value = mobile)

                if self.user and self.user.id == user.id:
                    self.user.person_uuid = person_uuid

        if len(person_ids) == 1:
            return person_ids[0]
        else:
            return person_ids


    # -------------------------------------------------------------------------
    def s3_approver(self,
                    user):
        """
            Returns the Approver for a new Registration &
            the organisation_id field

            @param: user - the user record (form.vars when done direct)
        """

        db = self.db
        deployment_settings = self.deployment_settings

        # Default Approver
        approver = deployment_settings.get_mail_approver()
        organisation_id = None
        # Check for Domain: Whitelist or specific Approver
        table = db.auth_organisation
        address, domain = user.email.split("@", 1)
        query = (table.domain == domain)
        record = db(query).select(table.organisation_id,
                                  table.approver,
                                  limitby=(0, 1)).first()
        if record:
            organisation_id = record.organisation_id
            approver = record.approver

        elif deployment_settings.get_auth_registration_requests_organisation():
            # Check for an Organisation-specific Approver
            organisation_id = user.get("organisation",
                                       None)
            if organisation_id:
                query = (table.organisation_id == organisation_id)
                record = db(query).select(table.approver,
                                          limitby=(0, 1)).first()
                if record and record.approver:
                    approver = record.approver

        return approver, organisation_id


    # -------------------------------------------------------------------------
    def verify_email(self,
                     next=DEFAULT,
                     onaccept=DEFAULT,
                     log=DEFAULT):
        """
            action user to verify the registration email, XXXXXXXXXXXXXXXX

            .. method:: Auth.verify_email([next=DEFAULT [, onvalidation=DEFAULT
                [, onaccept=DEFAULT [, log=DEFAULT]]]])
        """

        db = self.db
        environment = self.environment
        settings = self.settings
        messages = self.messages
        deployment_settings = self.deployment_settings

        key = environment.request.args[-1]
        table_user = settings.table_user
        user = db(table_user.registration_key == key).select().first()
        if not user:
            raise HTTP(404)
        # S3: Lookup the Approver
        approver, organisation_id = self.s3_approver(user)
        if settings.registration_requires_approval and approver:
            user.update_record(registration_key = "pending")
            environment.session.flash = messages.registration_pending
        else:
            user.update_record(registration_key = "")
            environment.session.flash = messages.email_verified
        if log == DEFAULT:
            log = messages.verify_email_log
        if next == DEFAULT:
            next = settings.verify_email_next
        if onaccept == DEFAULT:
            onaccept = settings.verify_email_onaccept
        if log:
            self.log_event(log % user)

        if approver:
            user.approver = approver
            callback(onaccept, user)

        redirect(next)


    # -------------------------------------------------------------------------
    def s3_update_staff_membership(self,
                                   record,
                                   delete = False):
        """
            Updates the staff's memberships of the roles associated with the
            organisation and/or site instance record which the staff is a component of
            Called from onaccept & ondelete
        """

        db = self.db
        session = self.session

        if delete:
            org_staff_id     = record.id
            org_staff_record = db.org_staff[org_staff_id]
            deleted_fks      = Storage()
            for fk in eval(org_staff_record.deleted_fk):
                deleted_fks[fk["f"]] = fk["k"]
            organisation_id  = deleted_fks.organisation_id
            person_id        = deleted_fks.person_id
            site_id          = deleted_fks.site_id
        else:
            try:
                # Coming from org_staff form
                org_staff_id = session.rcvars.org_staff
            except:
                # Coming from register()
                org_staff_id = record.id
            org_staff_record = db.org_staff[org_staff_id]
            organisation_id  = org_staff_record.organisation_id
            person_id        = org_staff_record.person_id
            site_id          = org_staff_record.site_id

        supervisor = org_staff_record.supervisor
        no_access = org_staff_record.no_access

        user_id = self.s3_person_to_user(person_id)

        if organisation_id:
            # This staff is a component of an organisation
            # This should always be true
            try:
                organisation_staff_role_id = \
                    db.org_organisation[organisation_id].owned_by_role
            except:
                # An Invalid organisation_id (e.g. from tampering)
                return

            tablename = "org_organisation"
            table = db[tablename]
            try:
                id = organisation_id
                record = db(table.id == id).select(table.name,
                                                   limitby=(0, 1)).first()
                recordname = record.name
            except:
                recordname = ""
            organisation_supervisor_role = \
                            "%s_%s Supervisors of %s" % (tablename,
                                                         organisation_id,
                                                         recordname)
            table = db[self.settings.table_group]
            query = (table.role == organisation_supervisor_role)
            org_supervisor_role_id = db(query).select(table.id,
                                                      limitby=(0, 1)).first().id
            if no_access or delete:
                self.del_membership(organisation_staff_role_id, user_id)
                self.del_membership(org_supervisor_role_id, user_id)
            elif not supervisor:
                self.add_membership(organisation_staff_role_id, user_id)
                self.del_membership(org_supervisor_role_id, user_id)
            else:
                self.add_membership(organisation_staff_role_id, user_id)
                self.add_membership(org_supervisor_role_id, user_id)

            # The organisation staff role owns the org_staff
            # (This is more inclusive that site staff role)
            staff_ownership = dict(owned_by_role = organisation_staff_role_id)
            if no_access or delete:
                # Current user has no permissions
                staff_ownership["owned_by_user"] = None
            db.org_staff[org_staff_id] = staff_ownership

        if site_id:
            prefix, resourcename, id = self.s3_site_resource(site_id)
            tablename = "%s_%s" % (prefix, resourcename)
            if tablename in self.org_site_types:
                # This staff is a component of a site instance
                table = db[tablename]
                query = (table.site_id == site_id)
                record = db(query).select(table.owned_by_role,
                                          table.id,
                                          table.name,
                                          limitby=(0, 1)).first()
                id = record.id
                recordname = record.name or ""
                site_staff_role_id = record.owned_by_role

                site_supervisor_role = "%s_%s Supervisors of %s" % (tablename,
                                                                    id,
                                                                    recordname)
                table = db[self.settings.table_group]
                query = (table.role == site_supervisor_role)
                site_super_role_id = db(query).select(table.id,
                                                      limitby=(0, 1)).first().id
                if no_access or delete:
                    self.del_membership(site_staff_role_id, user_id)
                    self.del_membership(site_super_role_id, user_id)

                elif not supervisor:
                    self.add_membership(site_staff_role_id, user_id)
                    self.del_membership(site_super_role_id, user_id)

                else:
                    self.add_membership(site_staff_role_id, user_id)
                    self.add_membership(site_super_role_id, user_id)

    # -------------------------------------------------------------------------
    def s3_site_resource(self, site_id):
        """
            Returns the prefix, resource and id which a site refers to
            @ToDo: Should this functionality be shifted to
                   the super entity code? (But then can't be visible from Auth)
        """

        db = self.db

        r_site = db.org_site[site_id]
        site_type = r_site.instance_type
        site_type_split = site_type.split("_")
        prefix = site_type_split[0]
        resourcename = site_type_split[1]
        id = r_site[site_type].select(db[site_type].id,
                                      limitby=(0, 1)).first().id
        return (prefix, resourcename, id)


    # -------------------------------------------------------------------------
    def s3_logged_in(self):
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
    def s3_has_role(self, role):
        """
            Check whether the currently logged-in user has a role

            @param role: can be integer or a name
        """

        #deployment_settings = self.deployment_settings
        db = self.db
        session = self.session

        # => trigger basic auth
        if not self.s3_logged_in():
            return False

        # Administrators have all roles
        if 1 in session.s3.roles:
            return True

        try:
            role = int(role)
        except:
            #role = deployment_settings.auth.roles[role]
            try:
                query = (db.auth_group.role == role)
                role = db(query).select(db.auth_group.id,
                                        limitby=(0, 1)).first().id
            except:
                # Role doesn't exist in the Database
                return False

        if role in session.s3.roles:
            return True
        else:
            return False


    # -------------------------------------------------------------------------
    def s3_group_members(self, group_id):
        """
            Get a list of members of a group

            @param group_id: the group record ID
            @returns: a list of the user_ids for members of a group
        """

        membership = self.settings.table_membership
        query = (membership.group_id == group_id)
        members = self.db(query).select(membership.user_id)
        return [member.user_id for member in members]


    # -------------------------------------------------------------------------
    def s3_user_to_person(self, user_id):
        """
            Get the person_id for a given user_id

            @param user_id: the user record ID
            @returns: the person record ID for this user ID

            @note: unsafe method - do not expose to users
        """

        table_user = self.settings.table_user
        query = (table_user.id == user_id) & \
                (table_user.person_uuid == db.pr_person.uuid)
        record = db(query).select(db.pr_person.id,
                                  limitby=(0,1)).first()

        if record:
            return record.id
        else:
            return None


    # -------------------------------------------------------------------------
    def s3_person_to_user(self, person_id):
        """
            Get the user_id for a given person_id

            @param person_id: the person record ID
            @returns: the user record ID associated with this person record

            @note: unsafe method - do not expose to users
        """

        table_user = self.settings.table_user
        record = self.db( (self.db.pr_person.id == person_id) &
                          (self.db.pr_person.uuid == table_user.person_uuid)
                    ).select(table_user.id, limitby=(0,1)).first()
        if record:
            return record.id
        else:
            return None


    # -------------------------------------------------------------------------
    def person_id(self):
        """
            Get the person record ID for the current logged-in user
        """

        if self.s3_logged_in():
            record = self.db(self.db.pr_person.uuid == self.user.person_uuid
                             ).select(self.db.pr_person.id,
                                      limitby=(0,1)
                                      ).first()
            if record:
                return record.id
        return None


    # -------------------------------------------------------------------------
    def s3_has_permission(self, method, table, record_id = 0):
        """
            S3 framework function to define whether a user can access a record in manner "method"
            Designed to be called from the RESTlike controller
            @note: This is planned to be rewritten:
                   http://eden.sahanafoundation.org/wiki/BluePrintAuthorization

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
                authorised = self.s3_logged_in()

        elif session.s3.security_policy == 2:
            # Editor policy
            # Anonymous users can Read.
            if method == "read":
                authorised = True
            elif method == "create":
                # Authentication required for Create.
                authorised = self.s3_logged_in()
            elif record_id == 0 and method == "update":
                # Authenticated users can update at least some records
                authorised = self.s3_logged_in()
            else:
                # Editor role required for Update/Delete.
                authorised = self.s3_has_role("Editor")
                if not authorised and self.user and "owned_by_user" in table:
                    # Creator of Record is allowed to Edit
                    query = (table.id == record_id)
                    record = db(query).select(table.owned_by_user,
                                              limitby=(0, 1)).first()
                    if record and self.user.id == record.owned_by_user:
                        authorised = True

        elif session.s3.security_policy == 3:
            # Controller ACLs
            self.permission.use_cacls = True
            self.permission.use_facls = False
            self.permission.use_tacls = False
            authorised = self.permission.has_permission(table,
                                                        record=record_id,
                                                        method=method)

        elif session.s3.security_policy == 4:
            # Controller+Function ACLs
            self.permission.use_cacls = True
            self.permission.use_facls = True
            self.permission.use_tacls = False
            authorised = self.permission.has_permission(table,
                                                        record=record_id,
                                                        method=method)

        elif session.s3.security_policy == 5:
            # Controller+Function+Table ACLs
            self.permission.use_cacls = True
            self.permission.use_facls = True
            self.permission.use_tacls = True
            authorised = self.permission.has_permission(table,
                                                        record=record_id,
                                                        method=method)

        else:
            # Full policy
            if self.s3_logged_in():
                # Administrators are always authorised
                if self.s3_has_role(1):
                    authorised = True
                else:
                    # Require records in auth_permission to specify access (default Web2Py-style)
                    authorised = self.has_permission(method, table, record_id)
            else:
                # No access for anonymous
                authorised = False


        return authorised


    # -------------------------------------------------------------------------
    def s3_accessible_query(self, method, table):
        """
            Returns a query with all accessible records for the current logged in user

            @note: This method does not work on GAE because it uses JOIN and IN
        """

        db = self.db
        session = self.session
        T = self.environment.T

        policy = session.s3.security_policy

        if policy == 1:
            # "simple" security policy: show all records
            return table.id > 0
        elif policy == 2:
            # "editor" security policy: show all records
            return table.id > 0
        elif policy in (3, 4, 5):
            # ACLs: use S3Permission method
            query = self.permission.accessible_query(table, method)
            return query

        # "Full" security policy
        if self.s3_has_role(1):
            # Administrators can see all data
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
    def s3_has_membership(self, group_id=None, user_id=None, role=None):
        """
            Checks if user is member of group_id or role

            Extends Web2Py's requires_membership() to add new functionality:
                - Custom Flash style
                - Uses s3_has_role()
        """

        group_id = group_id or self.id_group(role)
        try:
            group_id = int(group_id)
        except:
            group_id = self.id_group(group_id) # interpret group_id as a role

        if self.s3_has_role(group_id):
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
    has_membership = s3_has_membership


    # -------------------------------------------------------------------------
    def s3_requires_membership(self, role):
        """
            Decorator that prevents access to action if not logged in or
            if user logged in is not a member of group_id.
            If role is provided instead of group_id then the group_id is calculated.

            Extends Web2Py's requires_membership() to add new functionality:
                - Custom Flash style
                - Uses s3_has_role()
                - Administrators (id=1) are deemed to have all roles
        """

        def decorator(action):

            def f(*a, **b):
                if not self.s3_logged_in():
                    request = self.environment.request
                    next = URL(r=request, args=request.args, vars=request.get_vars)
                    redirect("%s?_next=%s" % (self.settings.login_url, urllib.quote(next)))

                if not self.s3_has_role(role) and not self.s3_has_role(1):
                    self.environment.session.error = self.messages.access_denied
                    next = self.settings.on_failed_authorization
                    redirect(next)

                return action(*a, **b)

            f.__doc__ = action.__doc__

            return f

        return decorator

    # Override original method
    requires_membership = s3_requires_membership


    # -------------------------------------------------------------------------
    def s3_create_role(self, role, description, *acls):
        """
            Back-end method to create roles with ACLs
        """

        table = self.settings.table_group

        query = (table.role == role)
        record = self.db(query).select(limitby=(0, 1)).first()
        if record:
            role_id = record.id
            record.update_record(role=role, description=description)
        else:
            role_id = table.insert(role=role, description=description)

        if role_id:
            for acl in acls:
                self.s3_update_acl(role_id, **acl)

        return role_id


    # -------------------------------------------------------------------------
    def s3_update_acl(self, role, c=None, f=None, t=None, oacl=None, uacl=None):
        """
            Back-end method to update an ACL
        """

        table = self.permission.table

        if c is None and f is None and t is None:
            return None

        if t is not None:
            c = f = None

        if oacl is None:
            oacl = self.permission.NONE
        if uacl is None:
            uacl = self.permission.NONE

        if role:
            query = ((table.group_id == role) &
                     (table.controller == c) &
                     (table.function == f) &
                     (table.tablename == f))
            record = self.db(query).select(table.id, limitby=(0,1)).first()
            acl = dict(group_id=role,
                       controller=c,
                       function=f,
                       tablename=t,
                       oacl=oacl,
                       uacl=uacl)
            if record:
                success = record.update_record(**acl)
            else:
                success = table.insert(**acl)

        return success


    # -------------------------------------------------------------------------
    def s3_make_session_owner(self, table, record_id):
        """
            Makes the current session owner of this record
        """

        if hasattr(table, "_tablename"):
            table = table._tablename

        if not self.user:
            session = self.session
            if "owned_records" not in session:
                session.owned_records = Storage()
            records = session.owned_records.get(table, [])
            record_id = str(record_id)
            if record_id not in records:
                records.append(record_id)
            session.owned_records[table] = records


    # -------------------------------------------------------------------------
    def s3_session_owns(self, table, record_id):
        """
            Checks whether the current session owns a record
        """

        if hasattr(table, "_tablename"):
            table = table._tablename
        if not self.user:
            try:
                records = self.session.owned_records.get(table, [])
            except:
                records = []
            if str(record_id) in records:
                return True
        return False





# =============================================================================
class S3Permission(object):
    """
        S3 Class to handle permissions

        @author: Dominic König <dominic@aidiq.com>
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

    # see models/zzz_1st_run.py
    ADMIN = 1
    AUTHENTICATED = 2
    ANONYMOUS = 3
    EDITOR = 4

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

        # Environment
        env = Storage(environment)
        self.session = env.session
        self.db = env.db
        self.migrate = env.migrate

        # Deployment settings
        deployment_settings = env.deployment_settings
        self.policy = deployment_settings.get_security_policy()
        # Which level of granularity do we want?
        self.use_cacls = self.policy in (3, 4, 5) # Controller ACLs
        self.use_facls = self.policy in (4, 5) # Function ACLs
        self.use_tacls = self.policy in (5,) # Table ACLs
        self.modules = deployment_settings.modules

        # Permissions table
        self.tablename = tablename or self.TABLENAME
        self.table = self.db.get(self.tablename, None)

        # Error messages
        T = env.T
        self.INSUFFICIENT_PRIVILEGES = T("Insufficient Privileges")
        self.AUTHENTICATION_REQUIRED = T("Authentication Required")

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
                   fields (id, owned_by_user, owned_by_role), otherwise the record
                   will be re-loaded by this function
        """

        t = self.table # Permissions table

        if record == 0:
            record = None

        # Get user roles
        roles = []
        if self.session.s3 is not None:
            roles = self.session.s3.roles or []
            if self.policy not in (3, 4, 5):
                # Fall back to simple authorization
                if self.auth.s3_logged_in():
                    return self.ALL
                else:
                    return self.READ
        if self.ADMIN in roles:
            return self.ALL

        # Fall back to current request
        c = c or self.controller
        f = f or self.function

        page_acl = self.page_acl(c=c, f=f)

        if table is None or not self.use_tacls:
            acl = page_acl
        else:
            if self.EDITOR in roles:
                table_acl = (self.ALL, self.ALL)
            else:
                table_acl = self.table_acl(table=table, c=c)
            acl = self.most_restrictive((page_acl, table_acl))

        if acl[0] == self.NONE and acl[1] == self.NONE:
            # No table access
            acl = self.NONE
        elif record is None:
            # No record specified
            acl = acl[0] | acl[1]
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
        if self.ADMIN in roles:
            return (self.ALL, self.ALL)

        c = c or self.controller
        f = f or self.function

        page = "%s/%s" % (c, f)
        if page in self.unrestricted_pages:
            page_acl = (self.ALL, self.ALL)
        elif c not in self.modules or \
             c in self.modules and not self.modules[c].restricted:
            # Controller is not restricted => simple authorization
            if self.auth.s3_logged_in():
                page_acl = (self.ALL, self.ALL)
            else:
                page_acl = (self.READ, self.READ)
        else:
            page_acl = self.page_acls.get(page, None)

        if page_acl is None:
            page_acl = (self.NONE, self.NONE) # default
            q = ((t.controller == c) &
                ((t.function == f) | (t.function == None)))
            if roles:
                query = (t.group_id.belongs(roles)) & q
            else:
                query = (t.group_id == None) & q
            rows = self.db(query).select()
            if rows:
                # ACLs found, check for function-specific
                controller_acl = []
                function_acl = []
                for row in rows:
                    if not row.function:
                        controller_acl += [(row.oacl, row.uacl)]
                    else:
                        function_acl += [(row.oacl, row.uacl)]
                # Function-specific ACL overrides Controller ACL
                if function_acl and self.use_facls:
                    page_acl = most_permissive(function_acl)
                elif controller_acl:
                    page_acl = most_permissive(controller_acl)

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

        if table is None or not self.use_tacls:
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
                elif self.auth.s3_logged_in():
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
                   fields (id, owned_by_user, owned_by_role), otherwise the record
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
        elif self.ADMIN in roles:
            return True
        else:
            record_id = None
            ownership_fields = ("owned_by_user", "owned_by_role")
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
                record = self.db(table.id == record_id).select(limitby=(0,1),
                                                               *fs).first()
            if not record:
                return False # Record does not exist

            creator = owner = None
            if "owned_by_user" in table.fields:
                creator = record.owned_by_user
            if "owned_by_role" in table.fields:
                owner = record.owned_by_role

            if not user_id:
                if not creator and self.auth.s3_session_owns(table, record_id):
                    return True
                else:
                    return False

            return not creator and not owner or \
                   creator == user_id or owner in roles


    # -------------------------------------------------------------------------
    def hidden_modules(self):
        """
            List of modules to hide from the main menu
        """

        hidden_modules = []
        if self.policy in (3, 4, 5):
            restricted_modules = [m for m in self.modules
                                    if self.modules[m].restricted]
            roles = []
            if self.session.s3 is not None:
                roles = self.session.s3.roles or []
            if self.ADMIN in roles or self.EDITOR in roles:
                return []
            if not roles:
                hidden_modules = restricted_modules
            else:
                t = self.table
                query = (t.controller.belongs(restricted_modules)) & \
                        (t.tablename == None)
                if roles:
                    query = query & (t.group_id.belongs(roles))
                else:
                    query = query & (t.group_id == None)
                rows = self.db(query).select()
                acls = dict()
                for acl in rows:
                    if acl.controller not in acls:
                        acls[acl.controller] = self.NONE
                    acls[acl.controller] |= acl.oacl | acl.uacl
                hidden_modules = [m for m in restricted_modules if m not in acls or not acls[m]]

        return hidden_modules


    # -------------------------------------------------------------------------
    def accessible_url(self,
                       p=None,
                       a=None,
                       c=None,
                       f=None,
                       r=None,
                       args=[],
                       vars={},
                       anchor='',
                       extension=None,
                       env=None,
                       #not supported by web2py < r2806, and not needed in Eden:
                       #hmac_key=None
                      ):
        """
            Return a URL only if accessible by the user, otherwise False
        """

        required = self.METHODS
        if p in required:
            permission = required[p]
        else:
            permission = self.READ

        if not c:
            c = self.controller
        if not f:
            f = self.function

        # Hide disabled modules
        if self.modules and c not in self.modules:
            return False

        acl = self.page_acl(c=c, f=f)
        acl = (acl[0] | acl[1]) & permission
        if acl == permission or self.policy not in (3, 4, 5):
            return URL(a=a,
                       c=c,
                       f=f,
                       r=r,
                       args=args,
                       vars=vars,
                       anchor=anchor,
                       extension=extension,
                       env=env,
                       #not supported by web2py < r2806, and not needed in Eden:
                       #hmac_key=hmac_key
                       )
        else:
            return False


    # -------------------------------------------------------------------------
    def accessible_query(self, table, *methods):
        """
            Query for records which the user is permitted to access with method

            Example::
                query = auth.permission.accessible_query(table, "read", "update")

            @param table: the DB table
            @param methods: list of methods for which permission is required (AND),
                            any combination "create", "read", "update", "delete"
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
        if self.ADMIN in roles or self.EDITOR in roles:
            return query

        # Available ACLs
        pacl = self.page_acl()
        if not self.use_tacls:
            acl = pacl
        else:
            tacl = self.table_acl(table)
            acl = (tacl[0] & pacl[0], tacl[1] & pacl[1])

        # Ownership required?
        permitted = (acl[0] | acl[1]) & racl == racl
        ownership_required = False
        if not permitted:
            query = (table[pkey] == None)
        elif "owned_by_role" in table or "owned_by_user" in table:
            ownership_required = permitted and acl[1] & racl != racl

        # Generate query
        if ownership_required:
            if not user_id:
                query = (table[pkey] == None)
                if "owned_by_user" in table and pkey == "id":
                    try:
                        records = self.session.owned_records.get(table._tablename,
                                                                 None)
                    except:
                        pass
                    else:
                        if records:
                            query = (table.id.belongs(records))
            else:
                query = None
                if "owned_by_role" in table:
                    query = (table.owned_by_role.belongs(roles))
                if "owned_by_user" in table:
                    q = (table.owned_by_user == user_id)
                    if query is not None:
                        query = (query | q)
                    else:
                        query = q

        return query


    # -------------------------------------------------------------------------
    def ownership_required(self, table, *methods):
        """
            Check if record ownership is required for a method

            @param table: the table
            @param methods: methods to check (OR)
        """

        roles = []
        if self.session.s3 is not None:
            # No ownership required in policies without ACLs
            if self.policy not in (3, 4, 5):
                return False
            roles = self.session.s3.roles or []

        if self.ADMIN in roles or self.EDITOR in roles:
            return False # Admins and Editors do not need to own a record

        required = self.METHODS
        racl = reduce(lambda a, b: a | b,
                     [required[m] for m in methods if m in required], self.NONE)
        if not racl:
            return False

        # Available ACLs
        pacl = self.page_acl()
        if not self.use_tacls:
            acl = pacl
        else:
            tacl = self.table_acl(table)
            acl = (tacl[0] & pacl[0], tacl[1] & pacl[1])

        # Ownership required?
        permitted = (acl[0] | acl[1]) & racl == racl
        ownership_required = False
        if not permitted:
            pkey = table.fields[0]
            query = (table[pkey] == None)
        elif "owned_by_role" in table or "owned_by_user" in table:
            ownership_required = permitted and acl[1] & racl != racl

        return ownership_required


    # -------------------------------------------------------------------------
    def has_permission(self, table, record=None, method=None):
        """
            Check permission to access a record

            @param table: the table
            @param record: the record or record ID (None for any record)
            @param method: the method (or tuple/list of methods),
                           any of "create", "read", "update", "delete"

            @note: when submitting a record, the record ID and the ownership
                   fields (="owned_by_user", "owned_by_role") must be contained
                   if available, otherwise the record will be re-loaded
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
            if self.auth.s3_logged_in():
                self.session.error = self.INSUFFICIENT_PRIVILEGES
                redirect(self.homepage)
            else:
                self.session.error = self.AUTHENTICATION_REQUIRED
                redirect(self.loginpage)
        else:
            # non-HTML request => raise proper HTTP error
            if self.auth.s3_logged_in():
                raise HTTP(403)
            else:
                raise HTTP(401)


# =============================================================================
class S3Safe(object):
    """
        Wrapper for AAA-safe DAL access
    """

    def __init__(self, auth, audit, obj=None):

        self.db = audit.db

        self.auth = auth
        self.audit = audit

        self.__obj = obj

    # Table operations:
    def insert(self, **fields):
        return self.__obj.insert(**fields)

    def bulk_insert(self, items):
        return self.__obj.bulk_insert(items)

    def __getitem__(self, key):
        return self.__obj.__getitem__(key)

    def __setitem__(self, key, value):
        self.__obj.__setitem__(key, value)

    def __delitem__(self, key):
        self.__obj.__delitem__(key)

    # Set operations:
    def select(self, *fields, **attributes):
        if isinstance(self.__obj, Set):
            return self.__obj.select(*fields, **attributes)
        else:
            return self.db(self.__obj).select(*fields, **attributes)

    def count(self, distinct=None):
        if isinstance(self.__obj, Set):
            return self.__obj.count(distinct=distinct)
        else:
            return self.db(self.__obj).count(distinct=distinct)

    def update(self, **update_fields):
        if isinstance(self.__obj, Set):
            return self.__obj.update(**update_fields)
        else:
            return self.db(self.__obj).update(**update_fields)

    def delete(self):
        if isinstance(self.__obj, Set):
            return self.__obj.delete()
        else:
            return self.db(self.__obj).delete()

    # Row operations:
    def update_record(self, **fields):
        return self.__obj.update_record(**fields)

    def delete_record(self):
        return self.__obj.delete_record()


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
        self.auth = session.auth
        if session.auth and session.auth.user:
            self.user = session.auth.user.id
        else:
            self.user = None

        self.diff = None

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
        elif form:
            try:
                record = form.vars["id"]
            except:
                try:
                    record = form["id"]
                except:
                    record = None
            if record:
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
                self.diff = None

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
                self.diff = None

        return True


    # -------------------------------------------------------------------------
    def utcnow(self, row):

        self.diff = dict(row)

        now = datetime.datetime.utcnow()
        return now

    # -------------------------------------------------------------------------
    def safe(self, obj):

        return S3Safe(self.auth, self, obj)


# =============================================================================
class S3RoleManager(S3Method):

    """
        REST Method to manage ACLs
    """

    # Controllers to hide from the permissions matrix
    HIDE_CONTROLLER = ("admin", "default")

    # Roles to hide from the permissions matrix
    HIDE_ROLES = (1, 4)

    # Undeletable roles
    PROTECTED_ROLES = (1, 2, 3, 4, 5)

    controllers = Storage()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply role manager
        """

        method = self.method

        if method == "list":
            output = self._list(r, **attr)
        elif method in ("read", "create", "update"):
            output = self._edit(r, **attr)
        elif method == "delete":
            output = self._delete(r, **attr)
        elif method == "roles" and r.name == "user":
            output = self._roles(r, **attr)
        elif method == "users":
            output = self._users(r, **attr)
        else:
            r.error(501, self.manager.ERROR.BAD_METHOD)

        if r.http == "GET" and method not in ("create", "update", "delete"):
            self.session.s3.cancel = r.here()
        return output


    # -------------------------------------------------------------------------
    def _list(self, r, **attr):
        """
            List roles/permissions
        """

        output = dict()

        request = self.request
        resource = self.resource
        auth = self.manager.auth

        T = self.T

        if r.id:
            return self._edit(r, **attr)

        # Show permission matrix?
        show_matrix = request.get_vars.get("matrix", False) and True

        if r.interactive:

            # Title and subtitle
            output.update(title = T("List of Roles"))

            # Filter out hidden roles
            resource.add_filter(~(self.table.id.belongs(self.HIDE_ROLES)))
            resource.load()

            # Get active controllers
            controllers = [c for c in self.controllers.keys()
                             if c not in self.HIDE_CONTROLLER]

            # ACLs
            acl_table = auth.permission.table
            query = resource.get_query()
            query = query & (acl_table.group_id == self.table.id)
            records = self.db(query).select(acl_table.ALL)

            any = "ANY"
            acls = Storage({any:Storage()})
            for acl in records:
                c = acl.controller
                f = acl.function
                if not f:
                    f = any
                role_id = acl.group_id
                if f not in acls:
                    acls[f] = Storage()
                if c not in acls[f]:
                    acls[f][c] = Storage()
                acls[f][c][str(role_id)] = Storage(oacl = acl.oacl,
                                                   uacl = acl.uacl)
            for c in controllers:
                if c not in acls[any]:
                    acls[any][c] = Storage()
                if any not in acls[any][c]:
                    acls[any][c][any] = Storage(oacl = auth.permission.NONE,
                                                uacl = auth.permission.NONE)

            # Table header
            columns = []
            headers = [TH("ID"), TH(T("Role"))]
            if show_matrix:
                for c in controllers:
                    if c in acls[any]:
                        headers.append(TH(self.controllers[c].name_nice))
                        columns.append((c, any))
                    for f in acls:
                        if f != any and c in acls[f]:
                            headers.append(TH(self.controllers[c].name_nice, BR(), f))
                            columns.append((c, f))
            else:
                headers += [TH(T("Description"))]
            thead = THEAD(TR(headers))

            # Table body
            trows = []
            i = 1
            for role in resource:

                role_id = role.id
                role_name = role.role
                role_desc = role.description

                edit_btn = A(T("Edit"),
                             _href=URL(r=request, c="admin", f="role",
                                       args=[role_id], vars=request.get_vars),
                             _class="action-btn")

                users_btn = A(T("Users"),
                              _href=URL(r=request, c="admin", f="role",
                                        args=[role_id, "users"]),
                              _class="action-btn")

                if role_id in self.PROTECTED_ROLES:
                    tdata = [TD(edit_btn,
                                XML("&nbsp;"),
                                users_btn),
                                TD(role_name)]
                else:
                    delete_btn = A(T("Delete"),
                                _href=URL(r=request, c="admin", f="role",
                                          args=[role_id, "delete"],
                                          vars=request.get_vars),
                                _class="delete-btn")
                    tdata = [TD(edit_btn,
                                XML("&nbsp;"),
                                users_btn,
                                XML("&nbsp;"),
                                delete_btn),
                             TD(role_name)]

                if show_matrix:
                    # Display the permission matrix
                    for c, f in columns:
                        if f in acls and c in acls[f] and str(role_id) in acls[f][c]:
                            oacl = acls[f][c][str(role_id)].oacl
                            uacl = acls[f][c][str(role_id)].uacl
                        else:
                            oacl = acls[any][c][any].oacl
                            uacl = acls[any][c][any].oacl

                        oaclstr = ""
                        uaclstr = ""
                        options = auth.permission.PERMISSION_OPTS
                        NONE = auth.permission.NONE
                        for o in options:
                            if o == NONE and oacl == NONE:
                                oaclstr = "%s%s" % (oaclstr, options[o][0])
                            elif oacl and oacl & o:
                                oaclstr = "%s%s" % (oaclstr, options[o][0])
                            else:
                                oaclstr = "%s-" % oaclstr
                            if o == NONE and uacl == NONE:
                                uaclstr = "%s%s" % (uaclstr, options[o][0])
                            elif uacl and uacl & o:
                                uaclstr = "%s%s" % (uaclstr, options[o][0])
                            else:
                                uaclstr = "%s-" % uaclstr

                        values = "%s (%s)" % (uaclstr, oaclstr)
                        tdata += [TD(values, _nowrap="nowrap")]
                else:
                    # Display role descriptions
                    tdata += [TD(role_desc)]

                _class = i % 2 and "even" or "odd"
                trows.append(TR(tdata, _class=_class))
            tbody = TBODY(trows)

            # Aggregate list
            items = TABLE(thead, tbody, _id="list", _class="dataTable display")
            output.update(items=items, sortby=[[1, 'asc']])

            # Add-button
            add_btn = A(T("Add Role"), _href=URL(r=request, c="admin", f="role",
                                                 args=["create"]),
                                                 _class="action-btn")
            output.update(add_btn=add_btn)

            self.response.view = "admin/role_list.html"
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
            Create/update role
        """

        output = dict()

        request = self.request
        session = self.session
        db = self.db
        T = self.T

        crud_settings = self.manager.s3.crud

        CACL = T("Application Permissions")
        FACL = T("Function Permissions")
        TACL = T("Table Permissions")

        CANCEL = T("Cancel")

        auth = self.manager.auth
        model = self.manager.model
        acl_table = auth.permission.table

        if r.interactive:

            # Get the current record (if any)
            if r.record:
                output.update(title=T("Edit Role"))
                role_id = r.record.id
                role_name = r.record.role
                role_desc = r.record.description
            else:
                output.update(title=T("New Role"))
                role_id = None
                role_name = None
                role_desc = None

            # Form helpers ----------------------------------------------------
            mandatory = lambda l: DIV(l, XML("&nbsp;"),
                                      SPAN("*", _class="req"))
            acl_table.oacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
            acl_table.uacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
            acl_widget = lambda f, n, v: S3ACLWidget.widget(acl_table[f], v,
                                                            _id=n,
                                                            _name=n,
                                                            _class="acl-widget")
            formstyle = crud_settings.formstyle


            using_default = SPAN(T("using default"), _class="using-default")
            delete_acl = lambda _id: _id is not None and \
                                     A(T("Delete"),
                                       _href = URL(r=request,
                                                   c="admin", f="acl",
                                                   args=[_id, "delete"],
                                                   vars=dict(_next=r.here())),
                                       _class = "delete-btn") or using_default
            new_acl =  SPAN(T("new ACL"), _class="new-acl")

            # Role form -------------------------------------------------------
            form_rows = formstyle("role_name", mandatory("%s:" % T("Role Name")),
                                  INPUT(value=role_name,
                                        _name="role_name",
                                        _type="text",
                                        requires=IS_NOT_IN_DB(db,
                                            "auth_group.role",
                                            allowed_override=[role_name])), "") + \
                        formstyle("role_desc", "%s:" % T("Description"),
                                  TEXTAREA(value=role_desc,
                                           _name="role_desc",
                                           _rows="4"), "")
            key_row = P(T("* Required Fields"), _class="red")
            role_form = DIV(TABLE(form_rows), key_row, _id="role-form")

            # Prepare ACL forms -----------------------------------------------
            any = "ANY"
            controllers = [c for c in self.controllers.keys()
                             if c not in self.HIDE_CONTROLLER]
            ptables = []
            records = db(acl_table.group_id == role_id).select()

            acl_forms = []

            # Relevant ACLs
            acls = Storage()
            for acl in records:
                if acl.controller in controllers:
                    if acl.controller not in acls:
                        acls[acl.controller] = Storage()
                    if not acl.function:
                        f = any
                    else:
                        if auth.permission.use_facls:
                            f = acl.function
                        else:
                            continue
                    acls[acl.controller][f] = acl

            # Controller ACL table --------------------------------------------

            # Table header
            thead = THEAD(TR(TH(T("Application")),
                             TH(T("All Records")),
                             TH(T("Owned Records")),
                             TH()))

            # Rows for existing ACLs
            form_rows = []
            i = 0
            for c in controllers:
                default = Storage(id = None,
                                  controller = c,
                                  function = any,
                                  tablename = None,
                                  uacl = auth.permission.NONE,
                                  oacl = auth.permission.NONE)
                if c in acls:
                    acl_list = acls[c]
                    if any not in acl_list:
                        acl_list[any] = default
                else:
                    acl_list = Storage(ANY=default)
                acl = acl_list[any]
                _class = i % 2 and "even" or "odd"
                i += 1
                uacl = auth.permission.NONE
                oacl = auth.permission.NONE
                if acl.oacl is not None:
                    oacl = acl.oacl
                if acl.uacl is not None:
                    uacl = acl.uacl
                _id = acl.id
                delete_btn = delete_acl(_id)
                n = "%s_%s_ANY_ANY" % (_id, c)
                uacl = acl_widget("uacl", "acl_u_%s" % n, uacl)
                oacl = acl_widget("oacl", "acl_o_%s" % n, oacl)
                cn = self.controllers[c].name_nice
                form_rows.append(TR(TD(cn),
                                    TD(uacl),
                                    TD(oacl),
                                    TD(delete_btn),
                                    _class=_class))

            # Tabs
            tabs = [SPAN(A(CACL), _class="tab_here")]
            if auth.permission.use_facls:
                _class = auth.permission.use_tacls and \
                         "tab_other" or "tab_last"
                tabs.append(SPAN(A(FACL, _class="facl-tab"), _class=_class))
            if auth.permission.use_tacls:
                tabs.append(SPAN(A(TACL, _class="tacl-tab"),
                                 _class="tab_last"))

            acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                     TABLE(thead, TBODY(form_rows)),
                                     _id="controller-acls"))

            # Function ACL table ----------------------------------------------
            if auth.permission.use_facls:

                # Table header
                thead = THEAD(TR(TH(T("Application")),
                                 TH(T("Function")),
                                 TH(T("All Records")),
                                 TH(T("Owned Records")),
                                 TH()))

                # Rows for existing ACLs
                form_rows = []
                i = 0
                for c in controllers:
                    if c in acls:
                        acl_list = acls[c]
                    else:
                        continue
                    keys = acl_list.keys()
                    keys.sort()
                    for f in keys:
                        if f == any:
                            continue
                        acl = acl_list[f]
                        _class = i % 2 and "even" or "odd"
                        i += 1
                        uacl = auth.permission.NONE
                        oacl = auth.permission.NONE
                        if acl.oacl is not None:
                            oacl = acl.oacl
                        if acl.uacl is not None:
                            uacl = acl.uacl
                        _id = acl.id
                        delete_btn = delete_acl(_id)
                        n = "%s_%s_%s_ANY" % (_id, c, f)
                        uacl = acl_widget("uacl", "acl_u_%s" % n, uacl)
                        oacl = acl_widget("oacl", "acl_o_%s" % n, oacl)
                        cn = self.controllers[c].name_nice
                        form_rows.append(TR(TD(cn),
                                            TD(f),
                                            TD(uacl),
                                            TD(oacl),
                                            TD(delete_btn),
                                            _class=_class))

                # Row to enter a new controller ACL
                _class = i % 2 and "even" or "odd"
                c_opts = [OPTION("", _value=None, _selected="selected")] + \
                         [OPTION(self.controllers[c].name_nice,
                                 _value=c) for c in controllers]
                c_select = SELECT(_name="new_controller", *c_opts)

                form_rows.append(TR(
                    TD(c_select),
                    TD(INPUT(_type="text", _name="new_function")),
                    TD(acl_widget("uacl", "new_c_uacl", auth.permission.NONE)),
                    TD(acl_widget("oacl", "new_c_oacl", auth.permission.NONE)),
                    TD(new_acl), _class=_class))

                # Tabs to change to the other view
                tabs = [SPAN(A(CACL, _class="cacl-tab"),
                             _class="tab_other"),
                        SPAN(A(FACL), _class="tab_here")]
                if auth.permission.use_tacls:
                    tabs.append(SPAN(A(TACL, _class="tacl-tab"),
                                     _class="tab_last"))

                acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                         TABLE(thead, TBODY(form_rows)),
                                         _id="function-acls"))


            # Table ACL table -------------------------------------------------

            if auth.permission.use_tacls:
                tacls = db(acl_table.tablename != None).select(acl_table.tablename,
                                                               distinct=True)
                if tacls:
                    ptables = [acl.tablename for acl in tacls]
                # Relevant ACLs
                acls = dict([(acl.tablename, acl) for acl in records
                                                if acl.tablename in ptables])

                # Table header
                thead = THEAD(TR(TH(T("Tablename")),
                                 TH(T("All Records")),
                                 TH(T("Owned Records")),
                                 TH()))

                # Rows for existing table ACLs
                form_rows = []
                i = 0
                for t in ptables:
                    _class = i % 2 and "even" or "odd"
                    i += 1
                    uacl = auth.permission.NONE
                    oacl = auth.permission.NONE
                    _id = None
                    if t in acls:
                        acl = acls[t]
                        if acl.uacl is not None:
                            uacl = acl.uacl
                        if acl.oacl is not None:
                            oacl = acl.oacl
                        _id = acl.id
                    delete_btn = delete_acl(_id)
                    n = "%s_ANY_ANY_%s" % (_id, t)
                    uacl = acl_widget("uacl", "acl_u_%s" % n, uacl)
                    oacl = acl_widget("oacl", "acl_o_%s" % n, oacl)
                    form_rows.append(TR(TD(t),
                                        TD(uacl),
                                        TD(oacl),
                                        TD(delete_btn),
                                        _class=_class))

                # Row to enter a new table ACL
                _class = i % 2 and "even" or "odd"
                all_tables = [t._tablename for t in self.db]
                form_rows.append(TR(
                    TD(INPUT(_type="text", _name="new_table",
                            requires=IS_EMPTY_OR(IS_IN_SET(all_tables,
                                                           zero=None,
                                        error_message=T("Undefined Table"))))),
                    TD(acl_widget("uacl", "new_t_uacl", auth.permission.NONE)),
                    TD(acl_widget("oacl", "new_t_oacl", auth.permission.NONE)),
                    TD(new_acl), _class=_class))

                # Tabs
                tabs = [SPAN(A(CACL, _class="cacl-tab"),
                             _class="tab_other")]
                if auth.permission.use_facls:
                    tabs.append(SPAN(A(FACL, _class="facl-tab"),
                                     _class="tab_other"))
                tabs.append(SPAN(A(TACL), _class="tab_here"))
                acl_forms.append(DIV(DIV(tabs, _class="tabs"),
                                     TABLE(thead, TBODY(form_rows)),
                                     _id="table-acls"))

            # Aggregate ACL Form ----------------------------------------------
            acl_form = DIV(acl_forms, _id="table-container")

            # Action row
            if session.s3.cancel:
                cancel = session.s3.cancel
            else:
                cancel = URL(r=request, c="admin", f="role", vars=request.get_vars)
            action_row = DIV(INPUT(_type="submit", _value=T("Save")),
                             A(CANCEL, _href=cancel, _class="action-lnk"),
                             _id="action-row")

            # Complete form
            form = FORM(role_form, acl_form, action_row)

            # Append role_id
            if role_id:
                form.append(INPUT(_type="hidden", _name="role_id", value=role_id))

            # Process the form ------------------------------------------------
            if form.accepts(request.post_vars, session):
                vars = form.vars

                # Update the role
                role = Storage(role=vars.role_name, description=vars.role_desc)
                if r.record:
                    r.record.update_record(**role)
                    role_id = form.vars.role_id
                    self.session.confirmation = '%s "%s" %s' % (T("Role"),
                                                                role.role,
                                                                T("updated"))
                else:
                    role_id = self.table.insert(**role)
                    self.session.confirmation = '%s "%s" %s' % (T("Role"),
                                                                role.role,
                                                                T("created"))

                if role_id:

                    # Collect the ACLs
                    acls = Storage()
                    for v in vars:
                        if v[:4] == "acl_":
                            acl_type, name = v[4:].split("_", 1)
                            n = name.split("_", 3)
                            i, c, f, t = map(lambda item: \
                                             item != any and item or None, n)
                            if i.isdigit():
                                i = int(i)
                            else:
                                i = None
                            name = "%s_%s_%s" % (c, f, t)
                            if name not in acls:
                                acls[name] = Storage()
                            acls[name].update({"id": i,
                                               "group_id": role_id,
                                               "controller": c,
                                               "function": f,
                                               "tablename": t,
                                               "%sacl" % acl_type: vars[v]})
                    for v in ("new_controller", "new_table"):
                        if v in vars and vars[v]:
                            c = v == "new_controller" and vars.new_controller or None
                            f = v == "new_controller" and vars.new_function or None
                            t = v == "new_table" and vars.new_table or None
                            name = "%s_%s_%s" % (c, f, t)
                            x = v == "new_table" and "t" or "c"
                            uacl = vars["new_%s_uacl" % x]
                            oacl = vars["new_%s_oacl" % x]
                            if name not in acls:
                                acls[name] = Storage()
                            acls[name].update(group_id=role_id,
                                              controller=c,
                                              function=f,
                                              tablename=t,
                                              oacl=oacl,
                                              uacl=uacl)

                    # Save the ACLs
                    for acl in acls.values():
                        _id = acl.pop("id", None)
                        if _id:
                            db(acl_table.id == _id).update(**acl)
                        elif acl.oacl or acl.uacl:
                            _id = acl_table.insert(**acl)

                redirect(URL(r=request, f="role", vars=request.get_vars))

            output.update(form=form)
            if form.errors:
                if "new_table" in form.errors:
                    output.update(acl="table")
                elif "new_controller" in form.errors:
                    output.update(acl="function")
            self.response.view = "admin/role_edit.html"

        else:
            r.error(501, self.manager.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def _delete(self, r, **attr):
        """
            Delete role
        """

        session = self.session
        request = self.request
        T = self.T

        auth = self.manager.auth

        if r.interactive:

            if r.record:
                role_id = r.record.id
                role_name = r.record.role

                if role_id in self.PROTECTED_ROLES:
                    session.error = '%s "%s" %s' % (T("Role"),
                                                    role_name,
                                                    T("cannot be deleted."))
                    redirect(URL(r=request, c="admin", f="role",
                                 vars=request.get_vars))
                else:
                    # Delete all ACLs for this role:
                    acl_table = auth.permission.table
                    self.db(acl_table.group_id == role_id).delete()
                    # Remove all memberships:
                    membership_table = self.db.auth_membership
                    self.db(membership_table.group_id == role_id).delete()
                    # Update roles in session:
                    session.s3.roles = [role for role in session.s3.roles if role != role_id]
                    # Remove role:
                    self.db(self.table.id == role_id).delete()
                    # Confirmation:
                    session.confirmation = '%s "%s" %s' % (T("Role"),
                                                           role_name,
                                                           T("deleted"))
            else:
                session.error = T("No role to delete")
        else:
            r.error(501, self.manager.BAD_FORMAT)

        redirect(URL(r=request, c="admin", f="role", vars=request.get_vars))


    # -------------------------------------------------------------------------
    def _roles(self, r, **attr):
        """
            View/Update roles of a user
        """

        output = dict()

        db = self.db
        T = self.T

        CANCEL = T("Cancel")

        session = self.session
        request = self.request
        crud_settings = self.manager.s3.crud
        formstyle = crud_settings.formstyle

        auth = self.manager.auth
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership

        if r.interactive:
            if r.record:
                user = r.record
                user_id = user.id
                username = user.email
                query = (mtable.user_id == user_id)
                memberships = db(query).select()
                memberships = Storage([(str(m.group_id),
                                        m.id) for m in memberships])
                roles = db().select(gtable.id, gtable.role)
                roles = Storage([(str(g.id),
                                  " %s" % g.role) for g in roles if g.id not in (2, 3)])
                field = Storage(name="roles",
                                requires = IS_IN_SET(roles, multiple=True))
                widget = CheckboxesWidget.widget(field, memberships.keys())

                if session.s3.cancel:
                    cancel = session.s3.cancel
                else:
                    cancel = r.there()
                form = FORM(TABLE(
                            TR(TD(widget)),
                            TR(TD(INPUT(_type="submit", _value=T("Save")),
                                  A(CANCEL, _href=cancel, _class="action-lnk")))))

                if form.accepts(request.post_vars, session):
                    assign = form.vars.roles
                    for role in roles:
                        query = (mtable.user_id == user_id) & \
                                (mtable.group_id == role)
                        if str(role) not in assign:
                            db(query).delete()
                        else:
                            membership = db(query).select(limitby=(0, 1)).first()
                            if not membership:
                                mtable.insert(user_id=user_id, group_id=role)
                    session.confirmation = T("User Updated")
                    redirect(r.there())

                output.update(title="%s - %s" % (T("Assigned Roles"), username),
                              form=form)

                self.response.view = "admin/user_roles.html"

            else:
                session.error = T("No user to update")
                redirect(r.there())
        else:
            r.error(501, self.manager.BAD_FORMAT)

        return output


    # -------------------------------------------------------------------------
    def _users(self, r, **attr):
        """
            View/Update users of a role
        """

        output = dict()

        session = self.session
        request = self.request

        db = self.db
        T = self.T
        auth = self.manager.auth

        utable = auth.settings.table_user
        gtable = auth.settings.table_group
        mtable = auth.settings.table_membership

        if r.interactive:
            if r.record:

                role_id = r.record.id
                role_name = r.record.role
                role_desc = r.record.description

                title = "%s: %s" % (T("Role"), role_name)
                output.update(title=title,
                              description=role_desc,
                              group=role_id)

                if auth.settings.username:
                    username = "username"
                else:
                    username = "email"

                # @todo: Audit
                users = db().select(utable.ALL)
                assigned = db(mtable.group_id == role_id).select(mtable.ALL)

                assigned_users = [row.user_id for row in assigned]
                unassigned_users = [(row.id,
                                     row) for row in users if row.id not in assigned_users]

                # Delete form
                if assigned_users:
                    thead = THEAD(TR(TH(),
                                     TH(T("Name")),
                                     TH(T("Username")),
                                     TH(T("Remove?"))))
                    trows = []
                    i = 0
                    for user in users:
                        if user.id not in assigned_users:
                            continue
                        _class = i % 2 and "even" or "odd"
                        i += 1
                        trow = TR(TD(A(), _name="Id"),
                                  TD("%s %s" % (user.first_name,
                                                user.last_name)),
                                  TD(user[username]),
                                  TD(INPUT(_type="checkbox",
                                           _name="d_%s" % user.id,
                                           _class="remove_item")),
                                _class=_class)
                        trows.append(trow)
                    trows.append(TR(TD(), TD(), TD(),
                                TD(INPUT(_id="submit_delete_button",
                                         _type="submit",
                                         _value=T("Remove")))))
                    tbody = TBODY(trows)
                    del_form = TABLE(thead, tbody, _id="list",
                                     _class="dataTable display")
                else:
                    del_form = T("No users with this role")

                del_form = FORM(DIV(del_form, _id="table-container"),
                                    _name="del_form")

                # Add form
                uname = lambda u: "%s: %s %s" % (u.id, u.first_name, u.last_name)
                u_opts = [OPTION(uname(u[1]),
                          _value=u[0]) for u in unassigned_users]
                if u_opts:
                    u_opts = [OPTION("",
                              _value=None, _selected="selected")] + u_opts
                    u_select = DIV(TABLE(TR(
                                    TD(SELECT(_name="new_user", *u_opts)),
                                    TD(INPUT(_type="submit",
                                             _id="submit_add_button",
                                             _value=T("Add"))))))
                else:
                    u_select = T("No further users can be added")
                add_form = FORM(DIV(u_select), _name="add_form")

                # Process delete form
                if del_form.accepts(request.post_vars,
                                    session, formname="del_form"):
                    del_ids = [v[2:] for v in del_form.vars
                                     if v[:2] == "d_" and del_form.vars[v] == "on"]
                    db((mtable.group_id == role_id) &
                       (mtable.user_id.belongs(del_ids))).delete()
                    redirect(r.here())

                # Process add form
                if add_form.accepts(request.post_vars,
                                    session, formname="add_form"):
                    if add_form.vars.new_user:
                        mtable.insert(group_id=role_id,
                                      user_id=add_form.vars.new_user)
                    redirect(r.here())

                form = DIV(H4(T("Users with this role")), del_form,
                           H4(T("Add new users")), add_form)
                list_btn = A(T("Back to Roles List"),
                             _href=URL(r=request, c="admin", f="role"),
                             _class="action-btn")
                edit_btn = A(T("Edit Role"),
                             _href=URL(r=request, c="admin", f="role",
                                       args=[role_id]),
                             _class="action-btn")
                output.update(form=form, list_btn=list_btn, edit_btn=edit_btn)

                self.response.view = "admin/role_users.html"

            else:
                session.error = T("No role to update")
                redirect(r.there())
        else:
            r.error(501, self.manager.BAD_FORMAT)

        return output

# =============================================================================
