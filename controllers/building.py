# -*- coding: utf-8 -*-

"""
    Buildings Assessments module

    @author Fran Boon <fran@aidiq.com>

    Data model from:
    http://www.atcouncil.org/products/downloadable-products/placards

    Postearthquake Safety Evaluation of Buildings: ATC-20
    http://www.atcouncil.org/pdfs/rapid.pdf
    This is actually based on the New Zealand variant:
    http://eden.sahanafoundation.org/wiki/BluePrintBuildingAssessments

    @ToDo: add other forms
    Urgent: Level 2 of the ~ATC-20
    - make this a 1-1 component of the rapid form?
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    session.error = T("Module disabled!")
    redirect(URL(r=request, c="default", f="index"))

# Options Menu (available in all Functions' Views)
def shn_menu():
    menu = [
        [T("NZSEE Level 1"), False, aURL(r=request, f="nzseel1"), [
            [T("Submit New (triage)"), False, aURL(p="create", r=request, f="nzseel1", args="create", vars={"triage":1})],
            [T("Submit New (full form)"), False, aURL(p="create", r=request, f="nzseel1", args="create")],
            [T("Search"), False, aURL(r=request, f="nzseel1", args="search")],
            [T("List"), False, aURL(r=request, f="nzseel1")],
        ]],
        [T("Report"), False, aURL(r=request, f="report"),
         [
          [T("Snapshot"), False, aURL(r=request, f="report")],
          [T("Assessment timeline"), False, aURL(r=request, f="timeline", args="assessment")],
         ]
        ]
    ]
    response.menu_options = menu

shn_menu()

# S3 framework functions
# -----------------------------------------------------------------------------
def index():

    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# NZSEE Level 1 (~ATC-20 Rapid Evaluation) Safety Assessment Form -------------
def nzseel1():

    """
        RESTful CRUD controller
    """

    tablename = "%s_%s" % (module, resourcename)
    table = db[tablename]

    # Pre-populate Inspector ID
    table.person_id.default = s3_logged_in_person()

    # Subheadings in forms:
    s3xrc.model.configure(table,
        deletable=False,
        create_next = URL(r=request, c=module, f=resourcename, args="[id]"),
        subheadings = {
            ".": "name", # Description in ATC-20
            "%s / %s" % (T("Overall Hazards"), T("Damage")): "collapse",
            ".": "posting",
            "%s:" % T("Further Action Recommended"): "barricades",
            ".": "estimated_damage",
            })

    rheader = lambda r: nzseel1_rheader(r)

    output = s3_rest_controller(module, resourcename,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def nzseel1_rheader(r, tabs=[]):
    """ Resource Headers """

    if r.representation == "html":
        if r.name == "nzseel1":
            assess = r.record
            if assess:
                rheader_tabs = shn_rheader_tabs(r, tabs)
                location = assess.location_id
                if location:
                    location = shn_gis_location_represent(location)
                person = assess.person_id
                if person:
                    pe_id = db(db.pr_person.id == person).select(db.pr_person.pe_id, limitby=(0, 1)).first().pe_id
                    query = (db.pr_pe_contact.pe_id == pe_id) & (db.pr_pe_contact.contact_method == 2)
                    mobile = db(query).select(db.pr_pe_contact.value, limitby=(0, 1)).first()
                    if mobile:
                        mobile = mobile.value
                    person = vita.fullname(person)
                rheader = DIV(TABLE(
                                TR(
                                    TH("%s: " % T("Person")), person,
                                    TH("%s: " % T("Mobile")), mobile,
                                  ),
                                TR(
                                    TH("%s: " % T("Location")), location,
                                    TH("%s: " % T("Date")), assess.date
                                  ),
                                TR(
                                    TH(""), "",
                                    TH("%s: " % T("Ticket ID")),
                                        r.table.ticket_id.represent(assess.ticket_id),
                                  ),
                                ),
                              rheader_tabs)

                return rheader
    return None

# -----------------------------------------------------------------------------
def report():
    """
        A report providing assessment totals, and breakdown by assessment type and status.
        e.g. Level 1 (red, yellow, green) Level 2 (R1-R3, Y1-Y2, G1-G2)

        @ToDo: Make into a Custom Method to be able to support Table ACLs
        (currently protected by Controller ACL)
    """

    table = db.building_nzseel1
    level1 = Storage()
    # Which is more efficient?
    # A) 4 separate .count() in DB
    # B) Pulling all records into Python & doing counts in Python
    query = (table.deleted == False)
    level1.total = db(query).count()
    filter = (table.posting == 1)
    level1.green = db(query & filter).count()
    filter = (table.posting == 2)
    level1.yellow = db(query & filter).count()
    filter = (table.posting == 3)
    level1.red = db(query & filter).count()

    level2 = Storage()

    return dict(level1=level1,
                level2=level2)

# -----------------------------------------------------------------------------
def timeline():
    """
        A report providing assessments received broken down by time
    """
    from datetime import datetime
    
    result = Storage()
    inspection = []
    creation = {}
    sql = "select `date`, daytime, count(*) FROM building_nzseel1 WHERE deleted = \"F\" GROUP BY `date`, daytime ORDER BY `date` DESC"
    result = db.executesql(sql)
    # Format the results
    for report in result:
        date = datetime.strptime(report[0],"%Y-%m-%d").strftime('%d %b %Y')
        daytime = report[1]
        count = report[2]
        print date 
        inspection.append((date,daytime, count))
    
    sql = "select created_on, estimated_damage FROM building_nzseel1 WHERE deleted = \"F\" ORDER BY created_on DESC"
    result = db.executesql(sql)
    # Format the results
    for report in result:
        print report[0]
        trueDate = datetime.strptime(report[0],"%Y-%m-%d %H:%M:%S") 
        date = trueDate.strftime('%d %b %Y')
        hour = trueDate.strftime("%H")
        if creation.has_key((date,hour)):
            creation[(date,hour)][0] += 1
        else:
            creation[(date,hour)] = [1,0,0,0,0,0,0,0]
        creation[(date,hour)][report[1]] += 1
    for (key,value) in creation.keys():
        print key
        print value
        print creation[(key,value)]
    return dict(inspection=inspection,
                creation=creation
                )

