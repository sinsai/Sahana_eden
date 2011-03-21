# -*- coding: utf-8 -*-

"""
    Human Resource Management

    @author: Dominic König <dominic AT aidiq DOT com>

"""

prefix = request.controller
resourcename = request.function

if prefix not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# =============================================================================
def shn_menu():
    """ Application Menu """
    menu = [
        [T("Human Resource"), False, None,[
            [T("New"), False, aURL(p="create", r=request, f="human_resource", args="create")],
            [T("Search"), False, aURL(r=request, f="human_resource", args="search")],
            [T("List All"), False, aURL(r=request, f="human_resource")],
        ]],
        [T("Dashboard"), False, aURL(r=request, f="index")],
    ]
    response.menu_options = menu

shn_menu()


# =============================================================================
def index():
    """ Dashboard """

    # Module's nice name
    try:
        module_name = deployment_settings.modules[prefix].name_nice
    except:
        module_name = T("Volunteer Management")

    return dict()

# =============================================================================
def human_resource():
    """ Human Resource Controller """

    output = s3_rest_controller(prefix, resourcename)
    return output


# =============================================================================
def person():
    """ Person Controller """

    return dict()


# =============================================================================
def organization():
    """ Organization Controller """

    return dict()


# =============================================================================
def site():
    """ Site Controller """

    return dict()


# =============================================================================
def skill():
    """ Skills Controller """

    output = s3_rest_controller(prefix, resourcename)
    return output


# =============================================================================
def help_pages():
    """ Help Pages """

    return dict()


# END =========================================================================
