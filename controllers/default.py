# -*- coding: utf-8 -*-

"""
    Default Controllers

    @author: Fran Boon
"""

module = "default"

# Options Menu (available in all Functions)
#response.menu_options = [
    #[T("About Sahana"), False, URL(r=request, f="about")],
#]

def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # If webservices don't use sessions, avoid cluttering up the storage
    #session.forget()
    return service()

def download():
    "Download a file"
    return response.download(request, db)

# Add newly-registered users to Person Registry & 'Authenticated' role
auth.settings.register_onaccept = lambda form: auth.s3_register(form)

_table_user = auth.settings.table_user
_table_user.first_name.label = T("First Name")
_table_user.first_name.comment = SPAN("*", _class="req")
_table_user.last_name.label = T("Last Name")
#_table_user.last_name.comment = SPAN("*", _class="req")
_table_user.email.label = T("E-mail")
_table_user.email.comment = SPAN("*", _class="req")
_table_user.password.comment = SPAN("*", _class="req")

#_table_user.password.label = T("Password")
#_table_user.language.label = T("Language")
_table_user.language.comment = DIV(_class="tooltip", _title="%s|%s" % (T("Language"),
                                                                       T("The language you wish the site to be displayed in.")))
_table_user.language.represent = lambda opt: s3_languages.get(opt, UNKNOWN_OPT)

# -----------------------------------------------------------------------------
def index():
    """ Main Home Page """

    title = T("Sahana Eden Disaster Management Platform")
    response.title = title

    # Menu Boxes
    #modules = deployment_settings.modules
    def menu_box( title, ci, fi ):
          """ Returns a menu_box linking to URL(ci, fi) """
          return A( DIV(title, _class = "menu-box-r"), _class = "menu-box-l",
                        _href = URL( r=request, c=ci, f=fi) )

    div_arrow_1 = DIV(IMG(_src = "/%s/static/img/arrow_blue_right.png" % \
                                 request.application),
                          _class = "div_arrow")

    div_arrow_2 = DIV(IMG(_src = "/%s/static/img/arrow_blue_right.png" % \
                                 request.application),
                          _class = "div_arrow")

    div_sit = DIV( H3(T("SITUATION")),
                   _class = "menu_div")
    if deployment_settings.has_module("irs"):
        div_sit.append(menu_box(T("Incidents"), "irs", "ireport"))
    if deployment_settings.has_module("assess"):
        div_sit.append(menu_box(T("Assessments"), "assess", "assess"))
    div_sit.append(menu_box(T("Organizations"), "org", "organisation"))

    div_dec = DIV( H3(T("DECISION")),
                   _class = "menu_div")
    div_dec.append(menu_box(T("Map"), "gis", "index"))
    if deployment_settings.has_module("assess"):
        div_dec.append(menu_box(T("Gap Report"), "project", "gap_report"))
        div_dec.append(menu_box(T("Gap Map"), "project", "gap_map"))

    div_res = DIV(H3(T("RESPONSE")),
                  _class = "menu_div",
                  _id = "menu_div_response")
    if deployment_settings.has_module("req"):
        div_res.append(menu_box(T("Requests"), "req", "req"))
    if deployment_settings.has_module("project"):
        div_res.append(menu_box(T("Activities"), "project", "activity"))

    #div_additional = DIV(A(DIV(T("Mobile Assess."),
    #                       _class = "menu_box"
    #                       ),
    #                    _href = URL( r=request, c="assess", f= "mobile_basic_assess")
    #                   ))

    menu_boxes = DIV(div_sit,
                     div_arrow_1,
                     div_dec,
                     div_arrow_2,
                     div_res,
                     #div_additional,
                    )

    # @ToDo: Replace this with an easily-customisable section on the homepage
    #settings = db(db.s3_setting.id == 1).select(limitby=(0, 1)).first()
    #if settings:
    #    admin_name = settings.admin_name
    #    admin_email = settings.admin_email
    #    admin_tel = settings.admin_tel
    #else:
    #    # db empty and prepopulate is false
    #    admin_name = T("Sahana Administrator").xml(),
    #    admin_email = "support@Not Set",
    #    admin_tel = T("Not Set").xml(),

    # Login/Registration forms
    self_registration = deployment_settings.get_security_self_registration()
    registered = False
    login_form = None
    login_div = None
    register_form = None
    register_div = None
    if 2 not in session.s3.roles:
        # This user isn't yet logged-in
        if request.cookies.has_key("registered"):
            # This browser has logged-in before
            registered = True

        # Provide a login box on front page
        request.args = ["login"]
        auth.messages.submit_button = T("Login")
        login_form = auth()
        login_div = DIV(H3(T("Login")),
                        P(XML("%s <b>%s</b> %s" % (T("Registered users can"),
                                                   T("login"),
                                                   T("to access the system")))))

        if self_registration:
            # Provide a Registration box on front page
            request.args = ["register"]
            auth.messages.submit_button = T("Register")
            register_form = auth()
            register_div = DIV(H3(T("Register")),
                               P(XML("%s <b>%s</b>" % (T("If you would like to help, then please"),
                                                       T("sign-up now")))))

            if session.s3.debug:
                validate_script = SCRIPT(_type="text/javascript",
                                         _src=URL(r=request, c="static", f="scripts/S3/jquery.validate.js"))
            else:
                validate_script = SCRIPT(_type="text/javascript",
                                         _src=URL(r=request, c="static", f="scripts/S3/jquery.validate.pack.js"))
            register_div.append(validate_script)
            if request.env.request_method == "POST":
                post_script = """
    // Unhide register form
    $('#register_form').removeClass('hide');
    // Hide login form
    $('#login_form').addClass('hide');
                """
            else:
                post_script = ""
            register_script = SCRIPT("""
$(document).ready(function() {
    // Change register/login links to avoid page reload, make back button work.
    $('#register-btn').attr('href', '#register');
    $('#login-btn').attr('href', '#login');
    %s
    // Redirect Register Button to unhide
    $('#register-btn').click(function() {
        // Unhide register form
        $('#register_form').removeClass('hide');
        // Hide login form
        $('#login_form').addClass('hide');
    });

    // Redirect Login Button to unhide
    $('#login-btn').click(function() {
        // Hide register form
        $('#register_form').addClass('hide');
        // Unhide login form
        $('#login_form').removeClass('hide');
    });
});
            """ % post_script)
            register_div.append(register_script)

    return dict(title = title,
                #modules=modules,
                menu_boxes=menu_boxes,
                #admin_name=admin_name,
                #admin_email=admin_email,
                #admin_tel=admin_tel,
                self_registration=self_registration,
                registered=registered,
                login_form=login_form,
                login_div=login_div,
                register_form=register_form,
                register_div=register_div
                )


# -----------------------------------------------------------------------------
def rapid():
    """ Set/remove rapid data entry flag """

    val = request.vars.get("val", True)
    if val == "0":
        val = False
    else:
        val = True
    session.s3.rapid_data_entry = val

    response.view = "xml.html"
    return dict(item=str(session.s3.rapid_data_entry))

# -----------------------------------------------------------------------------
def user():
    "Auth functions based on arg. See gluon/tools.py"

    auth.settings.on_failed_authorization = URL(r=request, f="error")

    if request.args and request.args(0) == "login_next":
        # Can redirect the user to another page on first login for workflow (set in 00_settings.py)
        # Note the timestamp of last login through the browser
        if auth.is_logged_in():
            db(db.auth_user.id == auth.user.id).update(timestmp = request.utcnow)

    _table_user = auth.settings.table_user
    if request.args and request.args(0) == "profile":
        #_table_user.organisation.writable = False
        _table_user.utc_offset.readable = True
        _table_user.utc_offset.writable = True

    login_form = register_form = None
    if request.args and request.args(0) == "login":
        auth.messages.submit_button = T("Login")
        form = auth()
        login_form = form
    elif request.args and request.args(0) == "register":
        auth.messages.submit_button = T("Register")
        form = auth()
        register_form = form
    else:
        form = auth()

    if request.args and request.args(0) == "profile" and deployment_settings.get_auth_openid():
        form = DIV(form, openid_login_form.list_user_openids())

    self_registration = deployment_settings.get_security_self_registration()

    # Use Custom Ext views
    # Best to not use an Ext form for login: can't save username/password in browser & can't hit 'Enter' to submit!
    #if request.args(0) == "login":
    #    response.title = T("Login")
    #    response.view = "auth/login.html"

    return dict(form=form, login_form=login_form, register_form=register_form, self_registration=self_registration)

# -------------------------------------------------------------------------
def source():
    """ RESTful CRUD controller """
    return s3_rest_controller("s3", "source")

# -------------------------------------------------------------------------
# About Sahana
def apath(path=""):
    "Application path"
    import os
    from gluon.fileutils import up
    opath = up(request.folder)
    #TODO: This path manipulation is very OS specific.
    while path[:3] == "../": opath, path=up(opath), path[3:]
    return os.path.join(opath,path).replace("\\", "/")

def about():
    """
    The About page provides details on the software
    depedencies and versions available to this instance
    of Sahana Eden.
    """
    import sys
    import subprocess
    import string
    python_version = sys.version
    web2py_version = open(apath("../VERSION"), "r").read()[8:]
    sahana_version = open(os.path.join(request.folder, "VERSION"), "r").read()
    try:
        sqlite_version = (subprocess.Popen(["sqlite3", "-version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()
    except:
        sqlite_version = T("Not installed or incorrectly configured.")
    try:
        mysql_version = (subprocess.Popen(["mysql", "--version"], stdout=subprocess.PIPE).communicate()[0]).rstrip()[10:]
    except:
        mysql_version = T("Not installed or incorrectly configured.")
    try:
        pgsql_reply = (subprocess.Popen(["psql", "--version"], stdout=subprocess.PIPE).communicate()[0])
        pgsql_version = string.split(pgsql_reply)[2]
    except:
        pgsql_version = T("Not installed or incorrectly configured.")
    try:
        import MySQLdb
        pymysql_version = MySQLdb.__revision__
    except:
        pymysql_version = T("Not installed or incorrectly configured.")
    try:
        import reportlab
        reportlab_version = reportlab.Version
    except:
        reportlab_version = T("Not installed or incorrectly configured.")
    try:
        import xlwt
        xlwt_version = xlwt.__VERSION__
    except:
        xlwt_version = T("Not installed or incorrectly configured.")
    return dict(
                python_version=python_version,
                sahana_version=sahana_version,
                web2py_version=web2py_version,
                sqlite_version=sqlite_version,
                mysql_version=mysql_version,
                pgsql_version=pgsql_version,
                pymysql_version=pymysql_version,
                reportlab_version=reportlab_version,
                xlwt_version=xlwt_version
                )

# -----------------------------------------------------------------------------
def help():
    "Custom View"
    response.title = T("Help")
    return dict()

# -----------------------------------------------------------------------------
def contact():
    """
        Give the user options to contact the site admins.
        Either:
            An internal Support Requests database
        or:
            Custom View
    """
    if auth.is_logged_in() and deployment_settings.get_options_support_requests():
        # Provide an internal Support Requests ticketing system.
        prefix = "support"
        resourcename = "req"
        tablename = "%s_%s" % (prefix, resourcename)
        table = db[tablename]

        # Pre-processor
        def prep(r):
            # Only Admins should be able to update ticket status
            if not auth.s3_has_role(1):
                table.status.writable = False
                table.actions.writable = False
            if r.interactive and r.method == "create":
                table.status.readable = False
                table.actions.readable = False
            return True
        response.s3.prep = prep

        output = s3_rest_controller(prefix, resourcename)
        return output
    else:
        # Default: Simple Custom View
        response.title = T("Contact us")
        return dict()

# END -------------------------------------------------------------------------