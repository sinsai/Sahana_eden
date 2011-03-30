# -*- coding: utf-8 -*-

""" Utilities """

# *****************************************************************************
# Session

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

    roles = []
    if auth.is_logged_in():
        user_id = auth.user.id
        _memberships = db.auth_membership
        # Cache this & invalidate when memberships are changed?
        memberships = db(_memberships.user_id == user_id).select(
                        _memberships.group_id)
        roles = [m.group_id for m in memberships]
    else:
        roles = [3] # Anonymous role
    session.s3.roles = roles
    # not used yet:
    if not auth.permission():
        auth.permission.fail()

    # Are we running in debug mode?
    session.s3.debug = request.vars.get("debug", None) or \
                       deployment_settings.get_base_debug()

    # Should we use Content-Delivery Networks?
    session.s3.cdn = deployment_settings.get_base_cdn()

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

# *****************************************************************************
# Utilities

super_entity = s3xrc.model.super_entity
super_link = s3xrc.model.super_link
super_key = s3xrc.model.super_key

# -----------------------------------------------------------------------------
def s3_get_utc_offset():
    """ Get the current UTC offset for the client """

    offset = None

    if auth.is_logged_in():
        # 1st choice is the personal preference (useful for GETs if user wishes to see times in their local timezone)
        offset = session.auth.user.utc_offset
        if offset:
            offset = offset.strip()

    if not offset:
        # 2nd choice is what the client provides in the hidden field (for form POSTs)
        offset = request.post_vars.get("_utc_offset", None)
        if offset:
            offset = int(offset)
            utcstr = offset < 0 and "UTC +" or "UTC -"
            hours = abs(int(offset/60))
            minutes = abs(int(offset % 60))
            offset = "%s%02d%02d" % (utcstr, hours, minutes)

    if not offset:
        # 3rd choice is the server default (what most clients should see the timezone as)
        offset = deployment_settings.L10n.utc_offset

    return offset

# Store last value in session
session.s3.utc_offset = s3_get_utc_offset()


# -----------------------------------------------------------------------------
def shn_user_utc_offset():
    """ for backward compatibility """
    return session.s3.utc_offset


# -----------------------------------------------------------------------------
def shn_as_local_time(value):
    """
        represents a given UTC datetime.datetime object as string:

        - for the local time of the user, if logged in
        - as it is in UTC, if not logged in, marked by trailing +0000
    """

    format="%Y-%m-%d %H:%M:%S"

    offset = IS_UTC_OFFSET.get_offset_value(session.s3.utc_offset)

    if not value:
        return "-"
    elif offset:
        dt = value + datetime.timedelta(seconds=offset)
        return dt.strftime(str(format))
    else:
        dt = value
        return dt.strftime(str(format))+" +0000"


# -----------------------------------------------------------------------------
# Phone number requires
# Multiple phone numbers can be separated by comma, slash, semi-colon.
# (Semi-colon appears in Brazil OSM data.)
# @ToDo: Need to beware of separators used inside phone numbers
# (e.g. 555-1212, ext 9), so may need fancier validation if we see that.
# @ToDo: Add tooltip giving list syntax, and warning against above.
# (Current use is in importing OSM files, so isn't interactive.)
# @ToDo: Code that should only have a single # should use
# shn_single_phone_requires. Check what messaging assumes.
phone_number_pattern = "\+?\s*[\s\-\.\(\)\d]+(?:(?: x| ext)\s?\d{1,5})?"
single_phone_number_pattern = phone_number_pattern + "$"
multiple_phone_number_pattern = \
    phone_number_pattern + \
    "(\s*(,|/|;)\s*" + phone_number_pattern + ")*$"
shn_single_phone_requires = IS_NULL_OR(IS_MATCH(single_phone_number_pattern))
shn_phone_requires = IS_NULL_OR(IS_MATCH(multiple_phone_number_pattern))


# -----------------------------------------------------------------------------
# Make URLs clickable
shn_url_represent = lambda url: (url and [A(url, _href=url, _target="blank")] or [""])[0]


# -----------------------------------------------------------------------------
def s3_include_debug():
    """
        Generates html to include:
            the js scripts listed in ../static/scripts/tools/sahana.js.cfg
            the css listed in ../static/scripts/tools/sahana.css.cfg
    """

    # Disable printing
    class dummyStream:
        """ dummyStream behaves like a stream but does nothing. """
        def __init__(self): pass
        def write(self,data): pass
        def read(self,data): pass
        def flush(self): pass
        def close(self): pass
    save_stdout = sys.stdout
    # redirect all print deals
    sys.stdout = dummyStream()

    scripts_dir_path = "applications/%s/static/scripts" % request.application

    # Get list of script files
    sys.path.append( "%s/tools" % scripts_dir_path)
    import mergejsmf

    configDictCore = {
        "web2py": scripts_dir_path,
        "T2":     scripts_dir_path,
        "S3":     scripts_dir_path
    }
    configFilename = "%s/tools/sahana.js.cfg"  % scripts_dir_path
    (fs, files) = mergejsmf.getFiles(configDictCore, configFilename)

    # Enable print
    sys.stdout = save_stdout

    include = ""
    for file in files:
        include = '%s\n<script src="/%s/static/scripts/%s" type="text/javascript"></script>' \
            % ( include,
                request.application,
                file)

    include = "%s\n <!-- CSS Syles -->" % include
    f = open("%s/tools/sahana.css.cfg" % scripts_dir_path, "r")
    files = f.readlines()
    for file in files[:-1]:
        include = '%s\n<link href="/%s/static/styles/%s" rel="stylesheet" type="text/css" />' \
            % ( include,
                request.application,
                file[:-1]
               )
    f.close()

    return XML(include)


# -----------------------------------------------------------------------------
def s3_logged_in_person():
    """ Get the person ID of the current user """

    if auth.s3_logged_in():
        person = db.pr_person
        record = db(person.uuid == session.auth.user.person_uuid).select(
                    person.id, limitby=(0,1)).first()
        if record:
            return record.id

    return None


# -----------------------------------------------------------------------------
def unauthorised():
    """ Redirection upon unauthorized request (interactive!) """

    session.error = T("Not Authorised!")
    redirect(URL(r=request, c="default", f="user", args="login"))


# -----------------------------------------------------------------------------
def shn_abbreviate(word, size=48):
    """
        Abbreviate a string. For use as a .represent

        see also: vita.truncate(self, text, length=48, nice=True)
    """

    if word:
        if (len(word) > size):
            word = "%s..." % word[:size - 4]
        else:
            return word
    else:
        return word


# -----------------------------------------------------------------------------
def shn_action_buttons(r,
                       deletable=True,
                       copyable=False,
                       read_url=None,
                       update_url=None,
                       delete_url=None,
                       copy_url=None):
    """
        Provide the usual Action Buttons for Column views.
        Allow customizing the urls, since this overwrites anything
        that would be inserted by shn_list via linkto.  The resource
        id should be represented by "[id]".

        Designed to be called from a postp

        @note: standard action buttons will be inserted automatically unless already overridden
        @note: If custom action buttons are already added,
               they will appear AFTER the standard action buttons
    """

    if r.component:
        args = [r.component_name, "[id]"]
    else:
        args = ["[id]"]

    prefix, name, table, tablename = r.target()

    custom_actions = response.s3.actions

    if s3_has_permission("update", table) and \
       not auth.permission.ownership_required(table, "update"):
        if not update_url:
            update_url = str(URL(r=request, args = args + ["update"]))
        response.s3.actions = [
            dict(label=str(UPDATE), _class="action-btn", url=update_url),
        ]
    else:
        if not read_url:
            read_url = str(URL(r=request, args = args))
        response.s3.actions = [
            dict(label=str(READ), _class="action-btn", url=read_url)
        ]

    if deletable and s3_has_permission("delete", table):
        if not delete_url:
            delete_url = str(URL(r=request, args = args + ["delete"]))
            # Check which records can be deleted
        if auth.permission.ownership_required(table, "delete"):
            q = auth.s3_accessible_query("delete", table)
            rows = db(q).select(table.id)
            restrict = [str(row.id) for row in rows]
            response.s3.actions.append(
                dict(label=str(DELETE), _class="delete-btn", url=delete_url, restrict=restrict)
            )
        else:
            response.s3.actions.append(
                dict(label=str(DELETE), _class="delete-btn", url=delete_url)
            )

    if copyable and s3_has_permission("create", table):
        if not copy_url:
            copy_url = str(URL(r=request, args = args + ["copy"]))
        response.s3.actions.append(
            dict(label=str(COPY), _class="action-btn", url=copy_url)
        )

    if custom_actions:
        response.s3.actions = response.s3.actions + custom_actions

    return


# -----------------------------------------------------------------------------
def shn_compose_message(data, template):
    """
        Compose an SMS Message from an XSLT

        from FRP
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
        Creates the strings for the title of/in the various CRUD Forms.

        @author: Michael Howden (michael@aidiq.com)

        @note: Whilst this is useful for RAD purposes, it isn't ideal for
               maintenance of translations, so it's use should be discouraged
               for the core system

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

    ADD = T("Add") + " " + T(table_name)
    LIST = T("List") + " " + T(table_name_plural)

    table_strings = Storage(
        title = T(table_name),
        title_plural = T(table_name_plural),
        title_create = ADD,
        title_display = T(table_name) + " " + T("Details"),
        title_list = LIST,
        title_update = T("Edit") + " " + T(table_name),
        title_search = T("Search") + " " + T(table_name_plural),
        subtitle_create = T("Add New") + " " + T(table_name),
        subtitle_list = T(table_name_plural),
        label_list_button = LIST,
        label_create_button = ADD,
        label_delete_button = T("Delete") + " " + T(table_name),
        msg_record_created =  T(table_name) + " " + T("added"),
        msg_record_modified =  T(table_name) + " " + T("updated"),
        msg_record_deleted = T(table_name) + " " + T("deleted"),
        msg_list_empty = T("No") + " " + T(table_name_plural) + " " + T("currently registered")
    )

    return table_strings


# -----------------------------------------------------------------------------
def shn_get_crud_string(tablename, name):
    """ Get the CRUD strings for a table """

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
    if not db(table.id > 0).count() or import_if_not_empty:
        import_file = os.path.join(request.folder,
                                   "private", "import", "tables",
                                   table_name + ".csv")
        table.import_from_csv_file(open(import_file,"r"))


# -----------------------------------------------------------------------------
def shn_last_update(table, record_id):
    """ @todo: docstring?? """

    if table and record_id:
        record = table[record_id]
        if record:
            mod_on_str  = " %s " % T("on")
            mod_by_str  = " %s " % T("by")

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
def s3_represent_multiref(table, opt, represent=None, separator=", "):
    """ Produce a representation for a list:reference field. """

    if represent is None:
        if "name" in table.fields:
            represent = lambda r: r and r.name or UNKNOWN_OPT

    if isinstance(opt, (int, long, str)):
        query = (table.id == opt)
    else:
        query = (table.id.belongs(opt))
    if "deleted" in table.fields:
        query = query & (table.deleted == False)

    records = db(query).select()

    if records:
        try:
            first = represent(records[0])
            rep_function = represent
        except TypeError:
            first = represent % records[0]
            rep_function = lambda r: represent % r

        # NB join only operates on strings, and some callers provide A().
        results = [first]
        for record in records[1:len(records)-1]:
            results.append(separator)
            results.append(rep_function(record))

        # Wrap in XML to allow showing anchors on read-only pages, else
        # Web2py will escape the angle brackets, etc. The single-record
        # location represent produces A() (unless told not to), and we
        # want to show links if we can.
        return XML(DIV(*results))

    else:
        return UNKNOWN_OPT


# -----------------------------------------------------------------------------
def shn_table_links(reference):
    """
        Return a dict of tables & their fields which have references to the
        specified table

        @deprecated: to be replaced by db[tablename]._referenced_by
    """

    tables = {}
    for table in db.tables:
        count = 0
        for field in db[table].fields:
            if str(db[table][field].type) == "reference %s" % reference:
                if count == 0:
                    tables[table] = {}
                tables[table][count] = field
                count += 1

    return tables


# -----------------------------------------------------------------------------
def s3_rheader_tabs(r, tabs=[], paging=False):
    """
        Constructs a DIV of component links for a S3RESTRequest

        @param tabs: the tabs as list of tuples (title, component_name, vars),
            where vars is optional
        @param paging: add paging buttons previous/next to the tabs
    """

    rheader_tabs = []

    tablist = []
    previous = next = None

    for i in xrange(len(tabs)):
        title, component = tabs[i][:2]
        vars_in_request = True
        if len(tabs[i]) > 2:
            _vars = tabs[i][2]
            for k,v in _vars.iteritems():
                if r.request.vars.get(k) != v:
                    vars_in_request = False
                    break
        else:
            _vars = r.request.vars

        here = False
        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
            if not component:
                component = None
        else:
            if "viewing" in _vars:
                tablename, record_id = _vars.viewing.split(".", 1)
                function = tablename.split("_", 1)[1]
            else:
                function = r.request.function
                record_id = r.id
        if function == r.name or\
           (function == r.request.function and "viewing" in request.vars):
            here = True

        if i == len(tabs)-1:
            tab = Storage(title=title, _class = "tab_last")
        else:
            tab = Storage(title=title, _class = "tab_other")
        if i > 0 and tablist[i-1]._class == "tab_here":
            next = tab

        if component:
            if r.component and r.component.name == component and vars_in_request or \
               r.custom_action and r.method == component:
                tab.update(_class = "tab_here")
                previous = i and tablist[i-1] or None
            args = [record_id, component]
            vars = Storage(_vars)
            if "viewing" in vars:
                del vars["viewing"]
            tab.update(_href=URL(r=request, f=function, args=args, vars=vars))
        else:
            if not r.component and len(tabs[i]) <= 2 and here:
                tab.update(_class = "tab_here")
                previous = i and tablist[i-1] or None
            vars = Storage(_vars)
            args = []
            if function != r.name:
                if "viewing" not in vars and r.id:
                    vars.update(viewing="%s.%s" % (r.tablename, r.id))
                #elif "viewing" in vars:
                elif not tabs[i][1]:
                    if "viewing" in vars:
                        del vars["viewing"]
                    args = [record_id]
            else:
                if "viewing" not in vars and record_id:
                    args = [record_id]
            tab.update(_href=URL(r=request, f=function, args=args, vars=vars))

        tablist.append(tab)
        rheader_tabs.append(SPAN(A(tab.title, _href=tab._href), _class=tab._class))

    if rheader_tabs:
        if paging:
            if next:
                rheader_tabs.insert(0, SPAN(A(">", _href=next._href), _class="tab_next_active"))
            else:
                rheader_tabs.insert(0, SPAN(">", _class="tab_next_inactive"))
            if previous:
                rheader_tabs.insert(0, SPAN(A("<", _href=previous._href), _class="tab_prev_active"))
            else:
                rheader_tabs.insert(0, SPAN("<", _class="tab_prev_inactive"))
        rheader_tabs = DIV(rheader_tabs, _class="tabs")
    else:
        rheader_tabs = ""

    return rheader_tabs


# -----------------------------------------------------------------------------
def s3_rheader_resource(r):
    """
        Identify the tablename and record ID for the rheader

        @param r: the current S3Request

    """

    _vars = r.request.vars

    if "viewing" in _vars:
        tablename, record_id = _vars.viewing.rsplit(".", 1)
        record = db[tablename][record_id]
    else:
        tablename = r.tablename
        record = r.record

    return (tablename, record)


# -----------------------------------------------------------------------------
def s3_sortOrderedDict(adict):
    """
        Sort an OrderedDict by Value
        - assumes unique values
    """

    values = adict.values()
    values.sort()
    result = OrderedDict()
    keys = adict.keys()
    for value in values:
        for key in keys:
            if adict[key] == value:
                result[key] = value
                break
    return result


# -----------------------------------------------------------------------------
# CRUD functions
# -----------------------------------------------------------------------------
def shn_import_csv(file, table=None):
    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()

#
# shn_custom_view -------------------------------------------------------------
#
def shn_custom_view(r, default_name, format=None):
    """ Check for custom view """

    prefix = r.request.controller

    if r.component:

        custom_view = "%s_%s_%s" % (r.name, r.component_name, default_name)

        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

        if not os.path.exists(_custom_view):
            custom_view = "%s_%s" % (r.name, default_name)
            _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    else:
        if format:
            custom_view = "%s_%s_%s" % (r.name, default_name, format)
        else:
            custom_view = "%s_%s" % (r.name, default_name)
        _custom_view = os.path.join(request.folder, "views", prefix, custom_view)

    if os.path.exists(_custom_view):
        response.view = "%s/%s" % (prefix, custom_view)
    else:
        if format:
            response.view = default_name.replace(".html", "_%s.html" % format)
        else:
            response.view = default_name


# -----------------------------------------------------------------------------
def shn_copy(r, **attr):
    """
        Copy a record

        used as REST method handler for S3Resources

        @todo: move into S3CRUDHandler
    """

    redirect(URL(r=request, args="create", vars={"from_record":r.id}))


# -----------------------------------------------------------------------------
def shn_list_item(table, resource, action, main="name", extra=None):
    """
        Display nice names with clickable links & optional extra info

        used in shn_search
    """

    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[table.id, action])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)


# -----------------------------------------------------------------------------
def shn_represent_extra(table, module, resource, deletable=True, extra=None):
    """
        Display more than one extra field (separated by spaces)

        used in shn_search
    """

    authorised = s3_has_permission("delete", table._tablename)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % \
                             (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % \
                         (resource, table.id))
    return ",".join( item_list )


# -----------------------------------------------------------------------------
def shn_represent(table, module, resource, deletable=True, main="name", extra=None):
    """
        Designed to be called via table.represent to make t2.search() output useful

        used in shn_search
    """

    db[table].represent = lambda table: \
                          shn_list_item(table, resource,
                                        action="display",
                                        main=main,
                                        extra=shn_represent_extra(table,
                                                                  module,
                                                                  resource,
                                                                  deletable,
                                                                  extra))
    return


# -----------------------------------------------------------------------------
def shn_barchart (r, **attr):
    """
        Provide simple barcharts for resource attributes
        SVG representation uses the SaVaGe library
        Need to request a specific value to graph in request.vars

        used as REST method handler for S3Resources

        @todo: replace by a S3MethodHandler
    """

    # Get all the variables and format them if needed
    valKey = r.request.vars.get("value")

    nameKey = r.request.vars.get("name")
    if not nameKey and r.table.get("name"):
        # Try defaulting to the most-commonly used:
        nameKey = "name"

    # The parameter value is required; it must be provided
    # The parameter name is optional; it is useful, but we don't need it
    # Here we check to make sure we can find value in the table,
    # and name (if it was provided)
    if not r.table.get(valKey):
        raise HTTP (400, s3xrc.xml.json_message(success=False, status_code="400", message="Need a Value for the Y axis"))
    elif nameKey and not r.table.get(nameKey):
        raise HTTP (400, s3xrc.xml.json_message(success=False, status_code="400", message=nameKey + " attribute not found in this resource."))

    start = request.vars.get("start")
    if start:
        start = int(start)

    limit = r.request.vars.get("limit")
    if limit:
        limit = int(limit)

    settings = r.request.vars.get("settings")
    if settings:
        settings = json.loads(settings)
    else:
        settings = {}

    if r.representation.lower() == "svg":
        r.response.headers["Content-Type"] = "image/svg+xml"

        graph = local_import("savage.graph")
        bar = graph.BarGraph(settings=settings)

        title = deployment_settings.modules.get(module).name_nice
        bar.setTitle(title)

        if nameKey:
            xlabel = r.table.get(nameKey).label
            if xlabel:
                bar.setXLabel(str(xlabel))
            else:
                bar.setXLabel(nameKey)

        ylabel = r.table.get(valKey).label
        if ylabel:
            bar.setYLabel(str(ylabel))
        else:
            bar.setYLabel(valKey)

        try:
            records = r.resource.load(start, limit)
            for entry in r.resource:
                val = entry[valKey]

                # Can't graph None type
                if not val is None:
                    if nameKey:
                        name = entry[nameKey]
                    else:
                        name = None
                    bar.addBar(name, val)
            return bar.save()
        # If the field that was provided was not numeric, we have problems
        except ValueError:
            raise HTTP(400, "Bad Request")
    else:
        raise HTTP(501, body=BADFORMAT)


# -----------------------------------------------------------------------------
def s3_rest_controller(prefix, resourcename, **attr):
    """
        Helper function to apply the S3Resource REST interface (new version)

        @param prefix: the application prefix
        @param resourcename: the resource name (without prefix)
        @param attr: additional keyword parameters

        Any keyword parameters will be copied into the output dict (provided
        that the output is a dict). If a keyword parameter is callable, then
        it will be invoked, and its return value will be added to the output
        dict instead. The callable receives the S3Request as its first and
        only parameter.

        CRUD can be configured per table using:

            s3xrc.model.configure(table, **attr)

        *** Redirection:

        create_next             URL to redirect to after a record has been created
        update_next             URL to redirect to after a record has been updated
        delete_next             URL to redirect to after a record has been deleted

        *** Form configuration:

        list_fields             list of names of fields to include into list views
        subheadings             Sub-headings (see separate documentation)
        listadd                 Enable/Disable add-form in list views

        *** CRUD configuration:

        editable                Allow/Deny record updates in this table
        deletable               Allow/Deny record deletions in this table
        insertable              Allow/Deny record insertions into this table
        copyable                Allow/Deny record copying within this table

        *** Callbacks:

        create_onvalidation     Function/Lambda for additional record validation on create
        create_onaccept         Function/Lambda after successful record insertion

        update_onvalidation     Function/Lambda for additional record validation on update
        update_onaccept         Function/Lambda after successful record update

        onvalidation            Fallback for both create_onvalidation and update_onvalidation
        onaccept                Fallback for both create_onaccept and update_onaccept
        ondelete                Function/Lambda after record deletion
    """

    # Parse the request
    resource, r = s3xrc.parse_request(prefix, resourcename)

    resource.set_handler("copy", shn_copy)
    resource.set_handler("barchart", shn_barchart)
    resource.set_handler("merge", s3base.S3RecordMerger())

    resource.set_handler("s3ocr", s3base.S3OCR())

    # Execute the request
    output = resource.execute_request(r, **attr)

    if isinstance(output, dict) and not r.method or r.method=="search":
        if response.s3.actions is None:

            # Add default action buttons
            prefix, name, table, tablename = r.target()
            authorised = s3_has_permission("update", tablename)

            # If the component has components itself, then use the
            # component's native controller for CRU(D) => make sure
            # you have one, or override by native=False
            if r.component and s3xrc.model.has_components(prefix, name):
                native = output.get("native", True)
            else:
                native = False

            # Get table config
            model = s3xrc.model
            listadd = model.get_config(table, "listadd", True)
            editable = model.get_config(table, "editable", True) and \
                       not auth.permission.ownership_required(table, "update")
            deletable = model.get_config(table, "deletable", True)
            copyable = model.get_config(table, "copyable", False)

            # URL to open the resource
            open_url = r.resource.crud._linkto(r,
                                               authorised=authorised,
                                               update=editable,
                                               native=native)("[id]")

            # Add action buttons for Open/Delete/Copy as appropriate
            shn_action_buttons(r,
                               deletable=deletable,
                               copyable=copyable,
                               read_url=open_url,
                               update_url=open_url)

            # Override Add-button, link to native controller and put
            # the primary key into vars for automatic linking
            if native and not listadd and \
               s3_has_permission("create", tablename):
                label = shn_get_crud_string(tablename,
                                            "label_create_button")
                hook = r.resource.components[name]
                fkey = "%s.%s" % (name, hook.fkey)
                vars = request.vars.copy()
                vars.update({fkey: r.id})
                url = str(URL(r=request, c=prefix, f=name,
                              args=["create"], vars=vars))
                add_btn = A(label, _href=url, _class="action-btn")
                output.update(add_btn=add_btn)

    return output

# END
# *****************************************************************************
