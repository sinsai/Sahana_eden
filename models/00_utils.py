# -*- coding: utf-8 -*-

"""
    Utilities
"""

def s3_sessions():
    """
        Extend session to support:
            Multiple flash classes
            Roles caching
            Settings
                Debug mode
                Security mode
                Audit modes
    """
    response.error = session.error
    response.confirmation = session.confirmation
    response.warning = session.warning
    session.error = []
    session.confirmation = []
    session.warning = []
    # Keep all our configuration options in a single pair of global variables
    # Use session for persistent variables
    if not session.s3:
        session.s3 = Storage()
    # Use response for one-off variables which are visible in views without explicit passing
    response.s3 = Storage()
    response.s3.countries = deployment_settings.get_L10n_countries()
    response.s3.formats = Storage()
    response.s3.gis = Storage()

    roles = []
    if auth.is_logged_in():
        user_id = auth.user.id
        _memberships = db.auth_membership
        memberships = db(_memberships.user_id == user_id).select(_memberships.group_id) # Cache this & invalidate when memberships are changed?
        for membership in memberships:
            roles.append(membership.group_id)
    session.s3.roles = roles

    # Are we running in debug mode?
    session.s3.debug = deployment_settings.get_base_debug()

    # Security Policy
    #session.s3.self_registration = deployment_settings.get_security_self_registration()
    session.s3.security_policy = deployment_settings.get_security_policy()

    # We Audit if either the Global or Module asks us to
    # (ignore gracefully if module author hasn't implemented this)
    try:
        session.s3.audit_read = deployment_settings.get_security_audit_read() \
            or deployment_settings.modules[request.controller].get("audit_read", False)
        session.s3.audit_write = deployment_settings.get_security_audit_write() \
            or deployment_settings.modules[request.controller].get("audit_write", False)
    except:
        # Controller doesn't link to a 'module' (e.g. appadmin)
        session.s3.audit_read = False
        session.s3.audit_write = False

    return

# Extend the session
s3_sessions()

# -----------------------------------------------------------------------------
# Debug Function (same name/parameters as JavaScript one)
def s3_debug(message, value=None):
    """
        Provide an easy, safe, systematic way of handling Debug output
        (print to stdout doesn't work with WSGI deployments)
    """
    import sys
    output = "S3 Debug: " + str(message)
    if value:
        output += ": " + str(value)
    
    print >> sys.stderr, output

# -----------------------------------------------------------------------------
# User Time Zone Operations:
def shn_user_utc_offset():
    """
        returns the UTC offset of the current user or None, if not logged in
    """

    if auth.is_logged_in():
        return db(db.auth_user.id == session.auth.user.id).select(db.auth_user.utc_offset, limitby=(0, 1)).first().utc_offset
    else:
        try:
            offset = db().select(db.s3_setting.utc_offset, limitby=(0, 1)).first().utc_offset
        except:
            offset = None
        return offset


def shn_as_local_time(value):
    """
        represents a given UTC datetime.datetime object as string:

        - for the local time of the user, if logged in
        - as it is in UTC, if not logged in, marked by trailing +0000
    """

    format="%Y-%m-%d %H:%M:%S"

    offset = IS_UTC_OFFSET.get_offset_value(shn_user_utc_offset())

    if offset:
        dt = value + datetime.timedelta(seconds=offset)
        return dt.strftime(str(format))
    else:
        dt = value
        return dt.strftime(str(format))+" +0000"

# -----------------------------------------------------------------------------
# Phone number requires
shn_phone_requires = IS_NULL_OR(IS_MATCH('\+?\s*[\s\-\.\(\)\d]+(?:(?: x| ext)\s?\d{1,5})?$'))

# -----------------------------------------------------------------------------
# Make URLs clickable
shn_url_represent = lambda url: (url and [A(url, _href=url, _target="blank")] or [""])[0]


# -----------------------------------------------------------------------------
def myname(user_id):
    user = db.auth_user[user_id]
    return user.first_name if user else NONE


# -----------------------------------------------------------------------------
def unauthorised():
    session.error = T("Not Authorised!")
    redirect(URL(r=request, c="default", f="user", args="login"))


# -----------------------------------------------------------------------------
def shn_abbreviate(word, size=48):

    """
        Abbreviate a string. For use as a .represent
    """

    if word:
        if (len(word) > size):
            word = "%s..." % word[:size - 4]
        else:
            return word
    else:
        return word


# @ToDo An alternative to having the caller pass in a constructed url
# would be to let then pass in an url or a linkto function, and call
# the function here.

# -----------------------------------------------------------------------------
def shn_action_buttons(jr, deletable=True, copyable=False,
                       read_url=None, update_url=None,
                       delete_url=None, copy_url=None):

    """
        Provide the usual Action Buttons for Column views.
        Allow customizing the urls, since this overwrites anything
        that would be inserted by shn_list via linkto.  The resource
        id should be represented by "[id]".
        Designed to be called from a postp
    """

    if jr.component:
        args = [jr.component_name, "[id]"]
    else:
        args = ["[id]"]

    if shn_has_permission("update", jr.table):
        if not update_url:
            update_url = str(URL(r=request, args = args + ["update"]))
        response.s3.actions = [
            dict(label=str(UPDATE), _class="action-btn", url=update_url),
        ]
        # Provide the ability to delete records in bulk
        if deletable and shn_has_permission("delete", jr.table):
            if not delete_url:
                delete_url = str(URL(r=request, args = args + ["delete"]))
            response.s3.actions.append(
                dict(label=str(DELETE), _class="action-btn", url=delete_url)
            )
        if copyable:
            if not copy_url:
                copy_url = str(URL(r=request, args = args + ["copy"]))
            response.s3.actions.append(
                dict(label=str(COPY), _class="action-btn", url=copy_url)
            )
    else:
        if not read_url:
            read_url = str(URL(r=request, args = args))
        response.s3.actions = [
            dict(label=str(READ), _class="action-btn", url=read_url)
        ]

    return


# -----------------------------------------------------------------------------
def shn_compose_message(data, template):

    """
        Compose an SMS Message from an XSLT
    """

    if data:
        root = etree.Element("message")
        for k in data.keys():
            entry = etree.SubElement(root, k)
            entry.text = s3xrc.xml.xml_encode(str(data[k]))

        message = None
        tree = etree.ElementTree(root)

        if template:
            template = os.path.join(request.folder, "static", template)
            if os.path.exists(template):
                message = s3xrc.xml.transform(tree, template)

        if message:
            return str(message)
        else:
            return s3xrc.xml.tostring(tree, pretty_print=True)


# -----------------------------------------------------------------------------
def shn_crud_strings(table_name,
                     table_name_plural = None):
    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            Creates the strings for the title of/in the various CRUD Forms.

            NB Whilst this is useful for RAD purposes, it isn't ideal for maintenance of translations,
               so it's use should be discouraged for the core system

        @arguments:
            table_name - string - The User's name for the resource in the table - eg. "Person"
            table_name_plural - string - The User's name for the plural of the resource in the table - eg. "People"

        @returns:
            class "gluon.storage.Storage" (Web2Py)

        @example
            s3.crud_strings[<table_name>] = shn_crud_strings(<table_name>, <table_name_plural>)
    """

    if not table_name_plural:
        table_name_plural = table_name + "s"

    ADD = T("Add " + table_name)
    LIST = T("List "+ table_name_plural)

    table_strings = Storage(
    title = T(table_name),
    title_plural = T(table_name_plural),
    title_create = ADD,
    title_display = T(table_name + " Details"),
    title_list = LIST,
    title_update = T("Edit "+ table_name),
    title_search = T("Search " + table_name_plural),
    subtitle_create = T("Add New " + table_name),
    subtitle_list = T(table_name_plural),
    label_list_button = LIST,
    label_create_button = ADD,
    label_delete_button = T("Delete " + table_name),
    msg_record_created =  T(table_name +" added"),
    msg_record_modified =  T(table_name + " updated"),
    msg_record_deleted = T( table_name + " deleted"),
    msg_list_empty = T("No " + table_name_plural + " currently registered"))

    return table_strings


# -----------------------------------------------------------------------------
def shn_get_crud_string(tablename, name):
    """
        Get the CRUD strings for a table
    """

    crud_strings = s3.crud_strings.get(tablename, s3.crud_strings)
    not_found = s3.crud_strings.get(name, None)

    return crud_strings.get(name, not_found)


# -----------------------------------------------------------------------------
def shn_import_table(table_name,
                     import_if_not_empty = False):
    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            If a table is empty, it will import values into that table from:
            /private/import/tables/<table>.csv.

        @arguments:
            table_name - string - The name of the table
            import_if_not_empty - bool
    """

    table = db[table_name]
    if not db(table.id).count() or import_if_not_empty:
        import_file = os.path.join(request.folder,
                                   "private", "import", "tables",
                                   table_name + ".csv")
        table.import_from_csv_file(open(import_file,"r"))


# -----------------------------------------------------------------------------
def shn_last_update(table, record_id):

    if table and record_id:
        record = table[record_id]
        if record:
            mod_on_str  = T(" on ")
            mod_by_str  = T(" by ")

            modified_on = ""
            if "modified_on" in table.fields:
                modified_on = "%s%s" % (mod_on_str, shn_as_local_time(record.modified_on))

            modified_by = ""
            if "modified_by" in table.fields:
                user = auth.settings.table_user[record.modified_by]
                if user:
                    person = db(db.pr_person.uuid == user.person_uuid).select(limitby=(0, 1)).first()
                    if person:
                        modified_by = "%s%s" % (mod_by_str, vita.fullname(person))

            if len(modified_on) or len(modified_by):
                last_update = "%s%s%s" % (T("Record last updated"), modified_on, modified_by)
                return last_update
    return None


# -----------------------------------------------------------------------------
def shn_represent_file(file_name,
                       table,
                       field = "file"):
    """
        @author: Michael Howden (michael@aidiq.com)

        @description:
            Represents a file (stored in a table) as the filename with a link to that file
            THIS FUNCTION IS REDUNDANT AND CAN PROBABLY BE REPLACED BY shn_file_represent in models/06_doc.py
    """
    import base64
    url_file = crud.settings.download_url + "/" + file_name

    if db[table][field].uploadfolder:
        path = db[table][field].uploadfolder
    else:
        path = os.path.join(db[table][field]._db._folder, "..", "uploads")
    pathfilename = os.path.join(path, file_name)

    try:
        #f = open(pathfilename,"r")
        #filename = f.filename
        regex_content = re.compile("([\w\-]+\.){3}(?P<name>\w+)\.\w+$")
        regex_cleanup_fn = re.compile('[\'"\s;]+')

        m = regex_content.match(file_name)
        filename = base64.b16decode(m.group("name"), True)
        filename = regex_cleanup_fn.sub("_", filename)
    except:
        filename = file_name

    return A(filename, _href = url_file)


# -----------------------------------------------------------------------------
def shn_reference_field():

    return


# -----------------------------------------------------------------------------
def shn_insert_subheadings(form, tablename, subheadings):

    """
    Insert subheadings into forms

    @param form: the form
    @param tablename: the tablename
    @param subheadings: a dict of {"Headline": Fieldnames}, where Fieldname can
                        be either a single field name or a list/tuple of
                        field names belonging under that headline

    """

    if subheadings:
        if tablename in subheadings:
            subheadings = subheadings.get(tablename)
        form_rows = iter(form[0])
        tr = form_rows.next()
        i = 0
        done = []
        while tr:
            f = tr.attributes.get("_id", None)
            if f.startswith(tablename) and f[-5:] == "__row":
                f = f[len(tablename)+1:-5]
                for k in subheadings.keys():
                    if k in done:
                        continue
                    fields = subheadings[k]
                    if not isinstance(fields, (list, tuple)):
                        fields = [fields]
                    if f in fields:
                        done.append(k)
                        form[0].insert(i, TR(TD(k, _colspan=3, _class="subheading"),
                                             _class = "subheading",
                                             _id = "%s_%s__subheading" % (tablename, f)))
                        tr.attributes.update(_class="after_subheading")
                        tr = form_rows.next()
                        i += 1
            try:
                tr = form_rows.next()
            except StopIteration:
                break
            else:
                i += 1


# -----------------------------------------------------------------------------
def shn_rheader_tabs(r, tabs=[], paging=False):

    """
    Constructs a DIV of component links for a S3RESTRequest

    @param tabs: the tabs as list of tuples (title, component_name, vars), where vars is optional
    @param paging: add paging buttons previous/next to the tabs

    """

    rheader_tabs = []

    tablist = []
    previous = next = None

    for i in xrange(len(tabs)):
        title, component = tabs[i][:2]
        if len(tabs[i]) > 2:
            _vars = tabs[i][2]
        else:
            _vars = r.request.vars

        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
            if not component:
                component = None
        else:
            function = r.request.function

        if i == len(tabs)-1:
            tab = Storage(title=title, _class = "rheader_tab_last")
        else:
            tab = Storage(title=title, _class = "rheader_tab_other")
        if i > 0 and tablist[i-1]._class == "rheader_tab_here":
            next = tab

        if component:
            if r.component and r.component.name == component or \
               r.custom_action and r.method == component:
                tab.update(_class = "rheader_tab_here")
                previous = i and tablist[i-1] or None
            args = [r.id, component]
            tab.update(_href=URL(r=request, f=function, args=args, vars=_vars))
        else:
            if not r.component:
                tab.update(_class = "rheader_tab_here")
                previous = i and tablist[i-1] or None
            args = [r.id]
            vars = Storage(_vars)
            if not vars.get("_next", None):
                vars.update(_next=URL(r=request, f=function, args=args, vars=_vars))
            tab.update(_href=URL(r=request, f=function, args=args, vars=vars))

        tablist.append(tab)
        rheader_tabs.append(SPAN(A(tab.title, _href=tab._href), _class=tab._class))

    if rheader_tabs:
        if paging:
            if next:
                rheader_tabs.insert(0, SPAN(A(">", _href=next._href), _class="rheader_next_active"))
            else:
                rheader_tabs.insert(0, SPAN(">", _class="rheader_next_inactive"))
            if previous:
                rheader_tabs.insert(0, SPAN(A("<", _href=previous._href), _class="rheader_prev_active"))
            else:
                rheader_tabs.insert(0, SPAN("<", _class="rheader_prev_inactive"))
        rheader_tabs = DIV(rheader_tabs, _id="rheader_tabs")
    else:
        rheader_tabs = ""

    return rheader_tabs
