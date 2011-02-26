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
        [T("NZSEE Level 2"), False, aURL(r=request, f="nzseel2"), [
            [T("Submit New"), False, aURL(p="create", r=request, f="nzseel2", args="create")],
            [T("Search"), False, aURL(r=request, f="nzseel2", args="search")],
            [T("List"), False, aURL(r=request, f="nzseel2")],
        ]],
        [T("Report"), False, aURL(r=request, f="index"),
         [
          [T("Snapshot"), False, aURL(r=request, f="report")],
          [T("Assessment timeline"), False, aURL(r=request, f="timeline")],
          [T("Assessment admin level"), False, aURL(r=request, f="adminLevel")],
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
        @ToDo: Action Button to create a new L2 Assessment from an L1
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
# NZSEE Level 2 (~ATC-20 Rapid Evaluation) Safety Assessment Form
def nzseel2():

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
            ".": "posting_existing",
            "%s:" % T("Further Action Recommended"): "barricades",
            ".": "estimated_damage",
            "%s / %s" % (T("Structural Hazards"), T("Damage")): "structural_foundations",
            "%s / %s" % (T("Non-structural Hazards"), T("Damage")): "non_parapets",
            "%s / %s" % (T("Geotechnical Hazards"), T("Damage")): "geotechnical_slope",
            })

    rheader = lambda r: nzseel2_rheader(r)

    output = s3_rest_controller(module, resourcename,
                                rheader=rheader)
    return output

# -----------------------------------------------------------------------------
def nzseel2_rheader(r, tabs=[]):
    """ Resource Headers """

    if r.representation == "html":
        if r.name == "nzseel2":
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

    level1 = Storage()
    table = db.building_nzseel1
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
    table = db.building_nzseel2
    query = (table.deleted == False)
    level2.total = db(query).count()
    filter = (table.posting.belongs((1, 2)))
    level2.green = db(query & filter).count()
    filter = (table.posting.belongs((3, 4)))
    level2.yellow = db(query & filter).count()
    filter = (table.posting.belongs((5, 6, 7)))
    level2.red = db(query & filter).count()

    return dict(level1=level1,
                level2=level2)
# -----------------------------------------------------------------------------
def getformatedData(dbresult):
    result = []
    cnt = -1;
    # Format the results
    for row in dbresult:
        print row
        damage = row.building_nzseel1.estimated_damage
        try:
            trueDate = row.building_nzseel1.date #datetime.datetime.strptime(row.date, "%Y-%m-%d %H:%M:%S")
        except:
            trueDate = row.building_nzseel1.created_on
        date = trueDate.strftime('%d %b %Y')
        hour = trueDate.strftime("%H")
        key = (date, hour)
        if (cnt == -1) or (result[cnt][0] != key):
            result.append([key , 0, 0, 0, 0, 0, 0, 0, 1])
            cnt += 1
        else:
            result[cnt][8] += 1
        result[cnt][damage] += 1

    return result

def timeline():
    """
        A report providing assessments received broken down by time
    """
    result = Storage()
    inspection = []
    creation = []
    # Here is the raw SQL command
    # select `date`, estimated_damage FROM building_nzseel1 WHERE deleted = "F" ORDER BY `date` DESC
    
    table = db.building_nzseel1
    dbresult = db().select(table.date ,
                           table.estimated_damage,
                           table.deleted == False,
                           orderby=~table.date,
                           )
    inspection = getformatedData(dbresult)

    # Here is the raw SQL command
    # select created_on, estimated_damage FROM building_nzseel1 WHERE deleted = "F" ORDER BY created_on DESC
    dbresult = db().select(table.created_on ,
                           table.estimated_damage,
                           table.deleted == False,
                           orderby=~table.created_on,
                           )
    creation = getformatedData(dbresult)
    
    totals = [0,0,0,0,0,0,0,0]
    for line in inspection:
        for i in range(8):
            totals[i] += line[i+1]
    return dict(inspection=inspection,
                creation=creation,
                totals= totals
                ) 

    
# -----------------------------------------------------------------------------

def adminLevel():
    """
        A report providing assessments received broken down by administration level
        @ToDo: Use DAL for database portability
    """
    # Here is the raw SQL command
    # select parent, `path`, estimated_damage FROM building_nzseel1, gis_location WHERE building_nzseel1.deleted = "F" and (gis_location.id = building_nzseel1.location_id)
    tableNZ1 = db.building_nzseel1
    tableGIS = db.gis_location
    dbresult = db(tableNZ1.location_id == tableGIS.id).select(tableGIS.path,
                                                              tableGIS.parent,
                                                              tableNZ1.estimated_damage,
                                                              tableNZ1.deleted == False,
                                                              )

    result = []
    temp = {}

    # Format the results
    for row in dbresult:
        parent = row.gis_location.parent ##report[0]
        path   = row.gis_location.path #report[1]
        damage = row.building_nzseel1.estimated_damage #report[2]
        
        if temp.has_key(parent):
            temp[parent][7] += 1
        else:
            temp[parent]=[0, 0, 0, 0, 0, 0, 0, 1]
        temp[parent][damage - 1] += 1
    gis = {}
    for (key) in temp.keys():
        # Here is the raw SQL command
        # "select name, parent FROM gis_location WHERE gis_location.id = '%s'" % key
        row = tableGIS(key)
        if row == None:
            gis[key] = T("Unknown")
        else:
            gis[key] = row.name

    for (key,item) in temp.items():
        if gis.has_key(key):
            name = gis[key]
        else:
            name = T("Unknown")
        result.append((name,item))
    return dict(report=result,
                ) 
    
    
# -----------------------------------------------------------------------------