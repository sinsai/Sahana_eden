# -*- coding: utf-8 -*-

"""
    Admin Controllers
"""

module = "admin"

# Options Menu (available in all Functions' Views)
# - can Insert/Delete items from default menus within a function, if required.
response.menu_options = admin_menu_options

# S3 framework functions
# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def setting():

    """ RESTful CRUD controller """

    resourcename = request.function
    tablename = "s3_" + resourcename
    table = db[tablename]

    table.admin_name.label = T("Admin Name")
    table.admin_email.label = T("Admin Email")
    table.admin_tel.label = T("Admin Tel")
    #table.utc_offset.label = T("UTC Offset")
    table.theme.label = T("Theme")
    table.theme.comment = DIV(A(T("Add Theme"), _class="colorbox", _href=URL(r=request, c="admin", f="theme", args="create", vars=dict(format="popup")), _target="top", _title=T("Add Theme"))),
    #table.archive_not_delete.label = T("Archive not Delete")
    #table.archive_not_delete.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Archive not Delete") + "|" + T("If this setting is enabled then all deleted records are just flagged as deleted instead of being really deleted. They will appear in the raw database access but won't be visible to normal users."))
    #table.debug.label = T("Debug")
    #table.debug.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Debug") + "|" + T("Switch this on to use individual CSS/Javascript files for diagnostics during development."))
    #table.self_registration.label = T("Self Registration")
    #table.self_registration.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Self-registration") + "|" + T("Can users register themselves for authenticated login access?"))
    #table.security_policy.label = T("Security Policy")
    #table.security_policy.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Security Policy") + "|" + T("The simple policy allows anonymous users to Read & registered users to Edit. The full security policy allows the administrator to set permissions on individual tables or records - see models/zzz.py."))
    #table.audit_read.label = T("Audit Read")
    #table.audit_read.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Audit Read") + "|" + T("If enabled then a log is maintained of all records a user accesses. If disabled then it can still be enabled on a per-module basis."))
    #table.audit_write.label = T("Audit Write")
    #table.audit_write.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Audit Write") + "|" + T("If enabled then a log is maintained of all records a user edits. If disabled then it can still be enabled on a per-module basis."))

    s3.crud_strings[tablename] = Storage(
        title_update = T("Edit Settings"),
        msg_record_modified = T("Settings updated"),
        label_list_button = None)

    s3xrc.model.configure(table,
                          deletable=False,
                          listadd=False,
                          #onvalidation=theme_check,
                          #update_next = URL(r=request, args=[1, "update"])
                          onaccept=theme_apply)

    output = s3_rest_controller("s3", resourcename, list_btn=None)
    return output


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def theme():
    """ RESTful CRUD controller """
    resource = "theme"
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    table.name.label = T("Name")
    #table.logo.label = T("Logo")
    #table.logo.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Logo") + "|" + T("Name of the file (& optional sub-path) located in static which should be used for the top-left image."))
    #table.header_background.label = T("Header Background")
    #table.header_background.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Header Background") + "|" + T("Name of the file (& optional sub-path) located in static which should be used for the background of the header."))
    #table.footer.label = T("Footer")
    #table.footer.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Footer") + "|" + T("Name of the file (& optional sub-path) located in views which should be used for footer."))
    table.col_background.label = T("Background Colour")
    table.col_txt.label = T("Text Colour for Text blocks")
    table.col_txt_background.label = T("Background Colour for Text blocks")
    table.col_txt_border.label = T("Border Colour for Text blocks")
    table.col_txt_underline.label = T("Colour for Underline of Subheadings")
    table.col_menu.label = T("Colour of dropdown menus")
    table.col_highlight.label = T("Colour of selected menu items")
    table.col_input.label = T("Colour of selected Input fields")
    table.col_border_btn_out.label = T("Colour of bottom of Buttons when not pressed")
    table.col_border_btn_in.label = T("Colour of bottom of Buttons when pressed")
    table.col_btn_hover.label = T("Colour of Buttons when hovering")

    # CRUD Strings
    ADD_THEME = T("Add Theme")
    LIST_THEMES = T("List Themes")
    s3.crud_strings[resource] = Storage(
        title_create = ADD_THEME,
        title_display = T("Theme Details"),
        title_list = LIST_THEMES,
        title_update = T("Edit Theme"),
        title_search = T("Search Themes"),
        subtitle_create = T("Add New Theme"),
        subtitle_list = T("Themes"),
        label_list_button = LIST_THEMES,
        label_create_button = ADD_THEME,
        msg_record_created = T("Theme added"),
        msg_record_modified = T("Theme updated"),
        msg_record_deleted = T("Theme deleted"),
        msg_list_empty = T("No Themes currently defined"))

    s3xrc.model.configure(table,
                          #onvalidation=theme_check,
                          #list_fields=["id", "name", "logo", "footer", "col_background"],
                          list_fields=["id", "name", "col_background"],
                          )

    return s3_rest_controller(module, resource)
    s3xrc.model.clear_config(table, "onvalidation")


# -----------------------------------------------------------------------------
def theme_apply(form):
    "Apply the Theme specified by Form"
    if form.vars.theme:
        # Valid form
        # Relevant paths
        template = os.path.join(request.folder, "static", "styles", "S3", "template.css")
        tmp_folder = os.path.join(request.folder, "static", "scripts", "tools")
        out_file = os.path.join(request.folder, "static", "styles", "S3", "sahana.css")
        out_file2 = os.path.join(request.folder, "static", "styles", "S3", "sahana.min.css")
        # Check permissions
        if not os.access(template, os.R_OK):
            session.error = T("Template file %s not readable - unable to apply theme!" % template)
            redirect(URL(r=request, args=request.args))
        if not os.access(tmp_folder, os.W_OK):
            session.error = T("Temp folder %s not writable - unable to apply theme!" % tmp_folder)
            redirect(URL(r=request, args=request.args))
        if not os.access(out_file, os.W_OK):
            session.error = T("CSS file %s not writable - unable to apply theme!" % out_file)
            redirect(URL(r=request, args=request.args))
        if not os.access(out_file2, os.W_OK):
            session.error = T("CSS file %s not writable - unable to apply theme!" % out_file2)
            redirect(URL(r=request, args=request.args))
        # Read in Template
        inpfile = open(template, "r")
        lines = inpfile.readlines()
        inpfile.close()
        # Read settings from Database
        theme = db(db.admin_theme.id == form.vars.theme).select(limitby=(0, 1)).first()
        default_theme = db(db.admin_theme.id == 1).select(limitby=(0, 1)).first()
        #if theme.logo:
        #    logo = theme.logo
        #else:
        #    logo = default_theme.logo
        #if theme.header_background:
        #    header_background = theme.header_background
        #else:
        #    header_background = default_theme.header_background
        # Write out CSS
        ofile = open(out_file, "w")
        for line in lines:
            #line = line.replace("YOURLOGOHERE", logo)
            #line = line.replace("HEADERBACKGROUND", header_background )
            # Iterate through Colours
            for key in theme.keys():
                if key[:4] == "col_":
                    if theme[key]:
                        line = line.replace(key, theme[key])
                    else:
                        line = line.replace(key, default_theme[key])
            ofile.write(line)
        ofile.close()

        # Minify
        from subprocess import PIPE, check_call
        currentdir = os.getcwd()
        os.chdir(os.path.join(currentdir, request.folder, "static", "scripts", "tools"))
        import sys
        # If started as a Windows service, os.sys.executable is no longer python
        if ("win" in sys.platform):
            pythonpath = os.path.join(sys.prefix, "python.exe")
        else:
            pythonpath = os.sys.executable
        try:
            proc = check_call([pythonpath, "build.sahana.py", "CSS", "NOGIS"], stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        except:
            session.error = T("Error encountered while applying the theme.")
            redirect(URL(r=request, args=request.args))
        os.chdir(currentdir)

        # Don't do standard redirect to List view as we only want this option available
        redirect(URL(r=request, args=[1, "update"]))
    else:
        session.error = INVALIDREQUEST
        redirect(URL(r=request))


# -----------------------------------------------------------------------------
def theme_check(form):
    "Check the Theme has valid files available. Deprecated"
    # Check which form we're called by
    if form.vars.theme:
        # Called from Settings
        theme = db(db.admin_theme.id == form.vars.theme).select(db.admin_theme.logo, limitby=(0, 1)).first()
        logo = theme.logo
        #header_background = theme.header_background
        #footer = theme.footer
    #elif form.vars.logo and form.vars.footer:
    elif form.vars.logo:
        # Called from Theme
        logo = form.vars.logo
        #header_background = form.vars.header_background
        #footer = form.vars.footer
    else:
        session.error = INVALIDREQUEST
        redirect(URL(r=request))

    _logo = os.path.join(request.folder, "static", logo)
    #_header_background = os.path.join(request.folder, "static", header_background)
    #_footer = os.path.join(request.folder, "views", footer)
    if not os.access(_logo, os.R_OK):
        form.errors["logo"] = T("Logo file %s missing!" % logo)
        return
    #if not os.access(_header_background, os.R_OK):
    #    form.errors["header_background"] = T("Header background file %s missing!" % logo)
    #    return
    #if not os.access(_footer, os.R_OK):
    #    form.errors["footer"] = T("Footer file %s missing!" % footer)
    #    return
    # Validation passed
    return


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def user():
    """ RESTful CRUD controller """
    module = "auth"
    resource = "user"
    tablename = module + "_" + resource
    table = db[tablename]

    # Model options
    role_manager = s3base.S3RoleManager()
    s3xrc.model.set_method(module, resource, method="roles", action=role_manager)

    # CRUD Strings
    ADD_USER = T("Add User")
    LIST_USERS = T("List Users")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_USER,
        title_display = T("User Details"),
        title_list = LIST_USERS,
        title_update = T("Edit User"),
        title_search = T("Search Users"),
        subtitle_create = T("Add New User"),
        subtitle_list = T("Users"),
        label_list_button = LIST_USERS,
        label_create_button = ADD_USER,
        label_delete_button = T("Delete User"),
        msg_record_created = T("User added"),
        msg_record_modified = T("User updated"),
        msg_record_deleted = T("User deleted"),
        msg_list_empty = T("No Users currently registered"))

    # Allow the ability for admin to Disable logins
    db.auth_user.registration_key.writable = True
    db.auth_user.registration_key.readable = True
    db.auth_user.registration_key.label = T("Disabled?")

    # In Controller to allow registration to work with UUIDs - only manual edits need this setting
    db.auth_user.registration_key.requires = IS_NULL_OR(IS_IN_SET(["disabled", "pending"]))

    # Pre-processor
    def user_prep(jr):
        if jr.method == "delete" and jr.http=="GET":
            if jr.id == jr.session.auth.user.id: # we're trying to delete ourself
                request.get_vars.update({"user.id":str(jr.id)})
                jr.id = None
                s3xrc.model.configure(table,
                                      delete_next = URL(r=request, c="default", f="user/logout"))
                s3.crud.confirm_delete = T("You are attempting to delete your own account - are you sure you want to proceed?")

        elif jr.method == "update":
            # Send an email to user if their account is approved
            # (=moved from 'pending' to 'blank'(i.e. enabled))
            s3xrc.model.configure(table,
                                  onvalidation = lambda form: user_approve(form))
        if jr.http == "GET" and not jr.method:
            session.s3.cancel = jr.here()
        return True
    response.s3.prep = user_prep

    s3xrc.model.configure(table,
        main="first_name",
        # Add users to Person Registry & 'Authenticated' role:
        create_onaccept = lambda form: auth.s3_register(form),
        create_onvalidation = lambda form: user_create_onvalidation(form))
    output = s3_rest_controller(module, resource)

    if response.s3.actions:
        response.s3.actions.insert(1,
                    dict(label=str(T("Roles")), _class="action-btn",
                         url=str(URL(r=request, c="admin", f="user", args=["[id]", "roles"]))))
    return output


# -----------------------------------------------------------------------------
def user_create_onvalidation (form):
    if (form.request_vars.has_key("password_two") and \
        form.request_vars.password != form.request_vars.password_two):
        form.errors.password = T("Password fields don't match")
    return True


# -----------------------------------------------------------------------------
def user_approve(form):
    "Send an email to user if their account is approved (moved from 'pending' to 'blank'(i.e. enabled))"
    if form.vars.registration_key:
        # Now non-blank
        return
    else:
        # Now blank - lookup old value
        status = db(db.auth_user.id == request.vars.id).select(db.auth_user.registration_key, limitby=(0, 1)).first().registration_key
        if status == "pending":
            # Send email to user confirming that they are now able to login
            if not auth.settings.mailer or \
                   not auth.settings.mailer.send(to=form.vars.email,
                        subject=s3.messages.confirmation_email_subject,
                        message=s3.messages.confirmation_email):
                    session.warning = auth.messages.unable_send_email
                    return
        else:
            return


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def usergroup():
    """
        User update form with groups
        - NB This is currently unused & has no custom view
    """
    user = request.vars.user

    # redirect to the user list if user id is not given
    if user is None:
        redirect(URL(r=request, f="user"))
        return

    # gather common variables
    data = {}
    data["user_id"] = user
    data["username"] = db.auth_user[user].first_name + " " + \
                       db.auth_user[user].last_name
    data["role"] = db.auth_group[user].role

    # display the standard user details
    record = db(db.auth_user.id == user).select().first()
    db.auth_user.id.readable = False

    # Let admin view and modify the registration key
    db.auth_user.registration_key.writable = True
    db.auth_user.registration_key.readable = True
    db.auth_user.registration_key.label = T("Disabled?")
    db.auth_user.registration_key.requires = IS_NULL_OR(IS_IN_SET(["disabled", "pending"]))

    form = SQLFORM(db.auth_user, record, deletable=True)

    # find all groups user belongs to
    query = (db.auth_membership.user_id == user)
    allgroups = db().select(db.auth_group.ALL)
    user_membership = db(query).select(db.auth_membership.ALL)

    # db.auth_group[row.group_id].role
    #records = SQLTABLE(db(query).select(db.auth_membership.ALL))

    # handle the M to M of user to group membership for display
    records = []
    for group in allgroups:

        user_group_count = 0

        for row in user_membership:

            if (row.group_id == group.id):
                records.append([group.role, "on", group.id])
                user_group_count += 1

        if (user_group_count == 0):
            # if the group does not exist currently and is enabled
            #if request.has_key(group.id):
            if (group.id == 6):
                db.auth_membership.insert(user_id = user, group_id = group.id)
                records.append([group.role, "on", group.id])
                data["heehe"] = "yes %d" % group.id

            records.append([group.role, "", group.id])

    # Update records for user details
    if form.accepts(request.vars): \
                    response.flash="User " + data["username"] + " Updated"
    elif form.errors: \
                    response.flash="There were errors in the form"

    # Update records for group membership details
    for key in request.vars.keys():
        data["m_" + key] = request.vars[key]

    return dict(data=data, records=records, form=form)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def group():

    """ RESTful CRUD controller """

    prefix = "auth"
    resourcename = "group"
    tablename = "%s_%s" % (prefix, resourcename)
    table = db[tablename]

    # Model options

    # CRUD Strings
    ADD_ROLE = T("Add Role")
    LIST_ROLES = T("List Roles")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_ROLE,
        title_display = T("Role Details"),
        title_list = LIST_ROLES,
        title_update = T("Edit Role"),
        title_search = T("Search Roles"),
        subtitle_create = T("Add New Role"),
        subtitle_list = T("Roles"),
        label_list_button = LIST_ROLES,
        label_create_button = ADD_ROLE,
        msg_record_created = T("Role added"),
        msg_record_modified = T("Role updated"),
        msg_record_deleted = T("Role deleted"),
        msg_list_empty = T("No Roles currently defined"))

    s3xrc.model.configure(table, main="role")
    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def membership():

    """ RESTful CRUD controller """

    prefix = "auth"
    resourcename = "membership"
    tablename = prefix + "_" + resourcename
    table = db[tablename]

    # Model options
    db.auth_membership.group_id.represent = shn_role_represent
    db.auth_membership.user_id.represent = shn_user_represent

    # CRUD Strings
    ADD_MEMBERSHIP = T("Add Membership")
    LIST_MEMBERSHIPS = T("List Memberships")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_MEMBERSHIP,
        title_display = T("Membership Details"),
        title_list = LIST_MEMBERSHIPS,
        title_update = T("Edit Membership"),
        title_search = T("Search Memberships"),
        subtitle_create = T("Add New Membership"),
        subtitle_list = T("Memberships"),
        label_list_button = LIST_MEMBERSHIPS,
        label_create_button = ADD_MEMBERSHIP,
        msg_record_created = T("Membership added"),
        msg_record_modified = T("Membership updated"),
        msg_record_deleted = T("Membership deleted"),
        msg_list_empty = T("No Memberships currently defined"))

    s3xrc.model.configure(table, main="user_id")
    return s3_rest_controller(prefix, resourcename)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def users():
    """
    List/amend which users are in a Group

    @deprecated

    """

    try:
        group = int(request.args(0))
    except TypeError, ValueError:
        session.error = T("Need to specify a role!")
        redirect(URL(r=request, f="group"))

    table = db.auth_membership
    query = table.group_id == group
    title = T("Role") + ": " + db.auth_group[group].role
    description = db.auth_group[group].description
    # Start building the Return
    output = dict(title=title, description=description, group=group)

    if auth.settings.username:
        username = "username"
    else:
        username = "email"

    # Audit
    crud.settings.create_onaccept = lambda form: s3_audit("create", module, "membership",
                                                          form=form,
                                                          representation="html")
    crud.settings.create_onvalidation = lambda form: group_dupes(form, "users", [group])
    # Many<>Many selection (Deletable, no Quantity)
    item_list = []
    sqlrows = db(query).select()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.user_id
        _user = db.auth_user[id]
        item_first = _user.first_name
        item_second = _user.last_name
        item_description = _user[username]
        id_link = A(id, _href=URL(r=request, f="user", args=[id, "read"]))
        checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
        item_list.append(TR(TD(id_link), TD(item_first), TD(item_second), TD(item_description), TD(checkbox), _class=theclass))

    if auth.settings.username:
        username_label = T("Username")
    else:
        username_label = T("Email")
    table_header = THEAD(TR(TH("ID"), TH(T("First Name")), TH(T("Last Name")), TH(username_label), TH(T("Remove"))))
    table_footer = TFOOT(TR(TD(_colspan=4), TD(INPUT(_id="submit_delete_button", _type="submit", _value=T("Remove")))))
    items = DIV(FORM(
        TABLE(table_header,
              TBODY(item_list),
              table_footer, _id="list", _class="display"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(r=request, f="group_remove_users", args=[group])))

    subtitle = T("Users")
    crud.messages.submit_button = T("Add")
    crud.messages.record_created = T("Role Updated")
    form = crud.create(table, next=URL(r=request, args=[group]))
    addtitle = T("Add New User to Role")
    output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form))
    return output


# -----------------------------------------------------------------------------
def group_dupes(form, page, arg):
    """
    Onvalidation check for duplicate user roles

    @deprecated

    """

    user = form.latest["user_id"]
    group = form.latest["group_id"]
    query = (form.table.user_id == user) & (form.table.group_id == group)
    items = db(query).select()
    if items:
        session.error = T("User already has this role")
        redirect(URL(r=request, f=page, args=arg))


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def group_remove_users():
    """
        Remove users from a group
    """
    if len(request.args) == 0:
        session.error = T("Need to specify a group!")
        redirect(URL(r=request, f="group"))
    group = request.args(0)
    table = db.auth_membership
    for var in request.vars:
        if str(var).isdigit():
            user = var
            query = (table.group_id == group) & (table.user_id == user)
            db(query).delete()
    # Audit
    #crud.settings.update_onaccept = lambda form: shn_audit_update(form, "membership", "html")
    session.flash = T("Users removed")
    redirect(URL(r=request, f="users", args=[group]))


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def groups():
    """
        List/amend which groups a User is in
    """

    try:
        user = int(request.args(0))
    except TypeError, ValueError:
        session.error = T("Need to specify a user!")
        redirect(URL(r=request, f="user"))

    table = db.auth_membership
    query = table.user_id == user
    title = db.auth_user[user].first_name + " " + db.auth_user[user].last_name
    description = db.auth_user[user].email
    # Start building the Return
    output = dict(title=title, description=description, user=user)

    # Audit
    crud.settings.create_onaccept = lambda form: s3_audit("create", module, "membership",
                                                          form=form,
                                                          representation="html")


    crud.settings.create_onvalidation = lambda form: group_dupes(form, "groups", [user])
    # Many<>Many selection (Deletable, no Quantity)
    item_list = []
    sqlrows = db(query).select()
    even = True
    for row in sqlrows:
        if even:
            theclass = "even"
            even = False
        else:
            theclass = "odd"
            even = True
        id = row.group_id
        _group = db.auth_group[id]
        item_first = _group.role
        item_description = _group.description
        id_link = A(id, _href=URL(r=request, f="group", args=[id, "read"]))
        checkbox = INPUT(_type="checkbox", _value="on", _name=id, _class="remove_item")
        item_list.append(TR(TD(id_link), TD(item_first), TD(item_description), TD(checkbox), _class=theclass))

    table_header = THEAD(TR(TH("ID"), TH(T("Role")), TH(T("Description")), TH(T("Remove"))))
    table_footer = TFOOT(TR(TD(_colspan=3), TD(INPUT(_id="submit_delete_button", _type="submit", _value=T("Remove")))))
    items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name="custom", _method="post", _enctype="multipart/form-data", _action=URL(r=request, f="user_remove_groups", args=[user])))

    subtitle = T("Roles")
    crud.messages.submit_button = T("Add")
    crud.messages.record_created = T("User Updated")
    form = crud.create(table, next=URL(r=request, args=[user]))
    addtitle = T("Add New Role to User")
    output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form=form))
    return output


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def user_remove_groups():
    """ Remove groups from a user """
    if len(request.args) == 0:
        session.error = T("Need to specify a user!")
        redirect(URL(r=request, f="user"))
    user = request.args(0)
    table = db.auth_membership
    for var in request.vars:
        if str(var).isdigit():
            group = var
            query = (table.group_id == group) & (table.user_id == user)
            db(query).delete()
    # Audit
    #crud.settings.update_onaccept = lambda form: shn_audit_update(form, "membership", "html")
    session.flash = T("Groups removed")
    redirect(URL(r=request, f="groups", args=[user]))


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def import_data():
    """
        Export data via CRUD controller. Old - being replaced by Sync.
    """
    title = T("Import Data")
    return dict(title=title)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def import_csv_data():
    """
        Import CSV data via POST upload to Database.
    """
    file = request.vars.multifile.file
    try:
        # Assumes that it is a concatenation of tables
        import_csv(file)
        session.flash = T("Data uploaded")
    except Exception, e:
        session.error = T("Unable to parse CSV file!")
    redirect(URL(r=request, f="import_data"))


# -----------------------------------------------------------------------------
@auth.requires_login()
def export_data():
    """
        Export data via CRUD controller. Old - being replaced by Sync.
    """
    title = T("Export Data")
    return dict(title=title)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def export_csv():
    """
        Export entire database as CSV. Old - being replaced by Sync.
    """
    import StringIO
    output = StringIO.StringIO()

    db.export_to_csv_file(output)

    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".csv")
    filename = "%s_database.csv" % (request.env.server_name)
    response.headers["Content-disposition"] = "attachment; filename=%s" % filename
    return output.read()


# -----------------------------------------------------------------------------
# Functional Testing
# Deprecated: Use static/selenium/scripts/regressionTests.py with it's Tk UI
def handleResults():
    """
        Process the POST data returned from Selenium TestRunner.
        The data is written out to 2 files.  The overall results are written to
        date-time-browserName-metadata.txt as a list of key: value, one per line.  The
        suiteTable and testTables are written to date-time-browserName-results.html.
    """

    if not request.vars.result:
        # No results
        return

    # Read in results
    result = request.vars.result
    totalTime = request.vars.totalTime
    numberOfSuccesses = request.vars.numTestPasses
    numberOfFailures = request.vars.numTestFailures
    numberOfCommandSuccesses = request.vars.numCommandPasses
    numberOfCommandFailures = request.vars.numCommandFailures
    numberOfCommandErrors = request.vars.numCommandErrors

    suiteTable = ""
    if request.vars.suite:
        suiteTable = request.vars.suite

    testTables = []
    testTableNum = 1
    while request.vars["testTable.%s" % testTableNum]:
        testTable = request.vars["testTable.%s" % testTableNum]
        testTables.append(testTable)
        testTableNum += 1
        try:
            request.vars["testTable.%s" % testTableNum]
            pass
        except:
            break

    # Unescape the HTML tables
    import urllib
    suiteTable = urllib.unquote(suiteTable)
    testTables = map(urllib.unquote, testTables)

    # We want to store results separately for each browser
    browserName = getBrowserName(request.env.http_user_agent)
    date = str(request.utcnow)[:-16]
    time = str(request.utcnow)[11:-10]
    time = time.replace(":", "-")

    # Write out results
    outputDir = os.path.join(request.folder, "static", "selenium", "results")
    metadataFile = "%s-%s-%s-metadata.txt" % (date, time, browserName)
    dataFile = "%s-%s-%s-results.html" % (date, time, browserName)

    #xmlText = '<selenium result="' + result + '" totalTime="' + totalTime + '" successes="' + numberOfCommandSuccesses + '" failures="' + numberOfCommandFailures + '" errors="' + numberOfCommandErrors + '" />'
    f = open(os.path.join(outputDir, metadataFile), "w")
    for key in request.vars.keys():
        if "testTable" in key or key in ["log", "suite"]:
            pass
        else:
            print >> f, "%s: %s" % (key, request.vars[key])
    f.close()

    f = open(os.path.join(outputDir, dataFile), "w")
    print >> f, suiteTable
    for testTable in testTables:
        print >> f, "<br/><br/>"
        print >> f, testTable
    f.close()

    message = DIV(P("Results have been successfully posted to the server here:"),
        P(A(metadataFile, _href=URL(r=request, c="static", f="selenium", args=["results", metadataFile]))),
        P(A(dataFile, _href=URL(r=request, c="static", f="selenium", args=["results", dataFile]))))

    response.view = "display.html"
    title = T("Test Results")
    return dict(title=title, item=message)


# -----------------------------------------------------------------------------
# Web2Py Ticket Viewer functions Borrowed from admin application of web2py
@auth.s3_requires_membership(1)
def errors():
    """ Error handler """

    from gluon.admin import apath
    from gluon.fileutils import listdir

    app = request.application

    for item in request.vars:
        if item[:7] == "delete_":
            os.unlink(apath("%s/errors/%s" % (app, item[7:]), r=request))

    func = lambda p: os.stat(apath("%s/errors/%s" % (app, p), r=request)).st_mtime
    tickets = sorted(listdir(apath("%s/errors/" % app, r=request), "^\w.*"),
                     key=func,
                     reverse=True)

    return dict(app=app, tickets=tickets)


# -----------------------------------------------------------------------------
def make_link(path):
    """ Create a link from a path """
    tryFile = path.replace("\\", "/")

    if os.path.isabs(tryFile) and os.path.isfile(tryFile):
        (folder, filename) = os.path.split(tryFile)
        (base, ext) = os.path.splitext(filename)
        app = request.args[0]

        editable = {"controllers": ".py", "models": ".py", "views": ".html"}
        for key in editable.keys():
            check_extension = folder.endswith("%s/%s" % (app, key))
            if ext.lower() == editable[key] and check_extension:
                return A('"' + tryFile + '"',
                         _href=URL(r=request,
                         f="edit/%s/%s/%s" % (app, key, filename))).xml()
    return ""


# -----------------------------------------------------------------------------
def make_links(traceback):
    """ Make links using the given traceback """

    lwords = traceback.split('"')

    # Make the short circuit compatible with <= python2.4
    result = (len(lwords) != 0) and lwords[0] or ""

    i = 1

    while i < len(lwords):
        link = make_link(lwords[i])

        if link == "":
            result += '"' + lwords[i]
        else:
            result += link

            if i + 1 < len(lwords):
                result += lwords[i + 1]
                i = i + 1

        i = i + 1

    return result


# -----------------------------------------------------------------------------
class TRACEBACK(object):
    """ Generate the traceback """

    def __init__(self, text):
        """ TRACEBACK constructor """

        self.s = make_links(CODE(text).xml())

    def xml(self):
        """ Returns the xml """

        return self.s


# -----------------------------------------------------------------------------
# Ticket viewing
@auth.s3_requires_membership(1)
def ticket():
    """ Ticket handler """

    if len(request.args) != 2:
        session.error = T("Invalid ticket")
        redirect(URL(r=request))

    app = request.args[0]
    ticket = request.args[1]
    e = RestrictedError()
    e.load(request, app, ticket)

    return dict(app=app,
                ticket=ticket,
                traceback=TRACEBACK(e.traceback),
                code=e.code,
                layer=e.layer)


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def role():
    """
    Role Manager

    @author: Dominic König <dominic@aidiq.com>

    """

    prefix = "auth"
    name = "group"

    # ACLs as component of roles
    s3xrc.model.add_component("s3", "permission",
        joinby = dict(auth_group="group_id"),
        multiple=True)

    def prep(r):
        if r.representation not in ("html",):
            return False

        handler = s3base.S3RoleManager()
        modules = deployment_settings.modules
        handler.controllers = Storage([(m, modules[m]) for m in modules
                                                       if modules[m].restricted])

        # Configure REST methods
        resource = r.resource
        resource.add_method("users", handler)
        resource.set_handler("read", handler)
        resource.set_handler("list", handler)
        resource.set_handler("copy", handler)
        resource.set_handler("create", handler)
        resource.set_handler("update", handler)
        resource.set_handler("delete", handler)
        return True
    response.s3.prep = prep

    response.s3.no_sspag = True
    response.extra_styles = ["S3/role.css"]

    output = s3_rest_controller(prefix, name)
    return output


# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def acl():
    """
    Preliminary controller for ACLs
    for testing purposes, not for production use!

    """

    prefix = "s3"
    name = "permission"

    table = auth.permission.table
    table.group_id.requires = IS_ONE_OF(db, "auth_group.id", "%(role)s")
    table.group_id.represent = lambda opt: opt and db.auth_group[opt].role or opt

    table.controller.requires = IS_EMPTY_OR(IS_IN_SET(auth.permission.modules.keys(), zero="ANY"))
    table.controller.represent = lambda opt: opt and "%s (%s)" % (opt, auth.permission.modules.get(opt, {}).get("name_nice", opt)) or "ANY"

    table.function.represent = lambda val: val and val or T("ANY")

    table.tablename.requires = IS_EMPTY_OR(IS_IN_SET([t._tablename for t in db], zero=T("ANY")))
    table.tablename.represent = lambda val: val and val or T("ANY")

    table.uacl.label = T("All Resources")
    table.uacl.widget = S3ACLWidget.widget
    table.uacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
    table.uacl.represent = lambda val: acl_represent(val, auth.permission.PERMISSION_OPTS)

    table.oacl.label = T("Owned Resources")
    table.oacl.widget = S3ACLWidget.widget
    table.oacl.requires = IS_ACL(auth.permission.PERMISSION_OPTS)
    table.oacl.represent = lambda val: acl_represent(val, auth.permission.PERMISSION_OPTS)

    s3xrc.model.configure(table,
        create_next = URL(r=request),
        update_next = URL(r=request))

    if "_next" in request.vars:
        next = request.vars._next
        s3xrc.model.configure(table, delete_next=next)

    output = s3_rest_controller(prefix, name)
    return output


# -----------------------------------------------------------------------------
def acl_represent(acl, options):
    """
    Represent ACLs in tables
    for testing purposes, not for production use!

    """

    values = []

    for o in options.keys():
        if o == 0 and acl == 0:
            values.append("%s" % options[o][0])
        elif acl and acl & o == o:
            values.append("%s" % options[o][0])
        else:
            values.append("_")

    return " ".join(values)

# -----------------------------------------------------------------------------
