# -*- coding: utf-8 -*-

""" Incident Reporting System - Model

    @author: Sahana Taiwan Team

"""

module = "irs"
if deployment_settings.has_module(module):

    # ---------------------------------------------------------------------
    # List of Incident Categories
    # NB It is important that the meaning of these entries is not changed as otherwise this hurts our ability to do synchronisation
    # The keys are based on the Canadian ems.incident hierarchy, with a few extra general versions added
    # The 2nd is meant for end-users
    # Entries can be hidden from user view in the controller.
    # Additional sets of 'translations' can be added to the tuples.
    irs_incident_type_opts = OrderedDict([
        ("animalHealth.animalDieOff", T("Animal Die Off")),
        ("animalHealth.animalFeed", T("Animal Feed")),
        ("aviation.aircraftCrash", T("Aircraft Crash")),
        ("aviation.aircraftHijacking", T("Aircraft Hijacking")),
        ("aviation.airportClosure", T("Airport Closure")),
        ("aviation.airspaceClosure", T("Airspace Closure")),
        ("aviation.noticeToAirmen", T("Notice to Airmen")),
        ("aviation.spaceDebris", T("Space Debris")),
        ("civil.demonstrations", T("Demonstrations")),
        ("civil.dignitaryVisit", T("Dignitary Visit")),
        ("civil.displacedPopulations", T("Displaced Populations")),
        ("civil.emergency", T("Civil Emergency")),
        ("civil.looting", T("Looting")),
        ("civil.publicEvent", T("Public Event")),
        ("civil.riot", T("Riot")),
        ("civil.volunteerRequest", T("Volunteer Request")),
        ("crime", T("Crime")),
        ("crime.bomb", T("Bomb")),
        ("crime.bombExplosion", T("Bomb Explosion")),
        ("crime.bombThreat", T("Bomb Threat")),
        ("crime.dangerousPerson", T("Dangerous Person")),
        ("crime.drugs", T("Drugs")),
        ("crime.homeCrime", T("Home Crime")),
        ("crime.illegalImmigrant", T("Illegal Immigrant")),
        ("crime.industrialCrime", T("Industrial Crime")),
        ("crime.poisoning", T("Poisoning")),
        ("crime.retailCrime", T("Retail Crime")),
        ("crime.shooting", T("Shooting")),
        ("crime.stowaway", T("Stowaway")),
        ("crime.terrorism", T("Terrorism")),
        ("crime.vehicleCrime", T("Vehicle Crime")),
        ("fire", T("Fire")),
        ("fire.forestFire", T("Forest Fire")),
        ("fire.hotSpot", T("Hot Spot")),
        ("fire.industryFire", T("Industry Fire")),
        ("fire.smoke", T("Smoke")),
        ("fire.urbanFire", T("Urban Fire")),
        ("fire.wildFire", T("Wild Fire")),
        ("flood", T("Flood")),
        ("flood.damOverflow", T("Dam Overflow")),
        ("flood.flashFlood", T("Flash Flood")),
        ("flood.highWater", T("High Water")),
        ("flood.overlandFlowFlood", T("Overland Flow Flood")),
        ("flood.tsunami", T("Tsunami")),
        ("geophysical.avalanche", T("Avalanche")),
        ("geophysical.earthquake", T("Earthquake")),
        ("geophysical.lahar", T("Lahar")),
        ("geophysical.landslide", T("Landslide")),
        ("geophysical.magneticStorm", T("Magnetic Storm")),
        ("geophysical.meteorite", T("Meteorite")),
        ("geophysical.pyroclasticFlow", T("Pyroclastic Flow")),
        ("geophysical.pyroclasticSurge", T("Pyroclastic Surge")),
        ("geophysical.volcanicAshCloud", T("Volcanic Ash Cloud")),
        ("geophysical.volcanicEvent", T("Volcanic Event")),
        ("hazardousMaterial", T("Hazardous Material")),
        ("hazardousMaterial.biologicalHazard", T("Biological Hazard")),
        ("hazardousMaterial.chemicalHazard", T("Chemical Hazard")),
        ("hazardousMaterial.explosiveHazard", T("Explosive Hazard")),
        ("hazardousMaterial.fallingObjectHazard", T("Falling Object Hazard")),
        ("hazardousMaterial.infectiousDisease", T("Infectious Disease")),
        ("hazardousMaterial.poisonousGas", T("Poisonous Gas")),
        ("hazardousMaterial.radiologicalHazard", T("Radiological Hazard")),
        ("health.infectiousDisease", T("Infectious Disease")),
        ("health.infestation", T("Infestation")),
        ("ice.iceberg", T("Iceberg")),
        ("ice.icePressure", T("Ice Pressure")),
        ("ice.rapidCloseLead", T("Rapid Close Lead")),
        ("ice.specialIce", T("Special Ice")),
        ("marine.marineSecurity", T("Marine Security")),
        ("marine.nauticalAccident", T("Nautical Accident")),
        ("marine.nauticalHijacking", T("Nautical Hijacking")),
        ("marine.portClosure", T("Port Closure")),
        ("marine.specialMarine", T("Special Marine")),
        ("meteorological.blizzard", T("Blizzard")),
        ("meteorological.blowingSnow", T("Blowing Snow")),
        ("meteorological.drought", T("Drought")),
        ("meteorological.dustStorm", T("Dust Storm")),
        ("meteorological.fog", T("Fog")),
        ("meteorological.freezingDrizzle", T("Freezing Drizzle")),
        ("meteorological.freezingRain", T("Freezing Rain")),
        ("meteorological.freezingSpray", T("Freezing Spray")),
        ("meteorological.hail", T("Hail")),
        ("meteorological.hurricane", T("Hurricane")),
        ("meteorological.rainFall", T("Rain Fall")),
        ("meteorological.snowFall", T("Snow Fall")),
        ("meteorological.snowSquall", T("Snow Squall")),
        ("meteorological.squall", T("Squall")),
        ("meteorological.stormSurge", T("Storm Surge")),
        ("meteorological.thunderstorm", T("Thunderstorm")),
        ("meteorological.tornado", T("Tornado")),
        ("meteorological.tropicalStorm", T("Tropical Storm")),
        ("meteorological.waterspout", T("Waterspout")),
        ("meteorological.winterStorm", T("Winter Storm")),
        ("missingPerson", T("Missing Person")),
        ("missingPerson.amberAlert", T("Child Abduction Emergency")),   # http://en.wikipedia.org/wiki/Amber_Alert
        ("missingPerson.missingVulnerablePerson", T("Missing Vulnerable Person")),
        ("missingPerson.silver", T("Missing Senior Citizen")),          # http://en.wikipedia.org/wiki/Silver_Alert
        ("publicService.emergencySupportFacility", T("Emergency Support Facility")),
        ("publicService.emergencySupportService", T("Emergency Support Service")),
        ("publicService.schoolClosure", T("School Closure")),
        ("publicService.schoolLockdown", T("School Lockdown")),
        ("publicService.serviceOrFacility", T("Service or Facility")),
        ("publicService.transit", T("Transit")),
        ("railway.railwayAccident", T("Railway Accident")),
        ("railway.railwayHijacking", T("Railway Hijacking")),
        ("roadway.bridgeClosure", T("Bridge Closed")),
        ("roadway.hazardousRoadConditions", T("Hazardous Road Conditions")),
        ("roadway.roadwayAccident", T("Road Accident")),
        ("roadway.roadwayClosure", T("Road Closed")),
        ("roadway.roadwayDelay", T("Road Delay")),
        ("roadway.roadwayHijacking", T("Road Hijacking")),
        ("roadway.roadwayUsageCondition", T("Road Usage Condition")),
        ("roadway.trafficReport", T("Traffic Report")),
        ("temperature.arcticOutflow", T("Arctic Outflow")),
        ("temperature.coldWave", T("Cold Wave")),
        ("temperature.flashFreeze", T("Flash Freeze")),
        ("temperature.frost", T("Frost")),
        ("temperature.heatAndHumidity", T("Heat and Humidity")),
        ("temperature.heatWave", T("Heat Wave")),
        ("temperature.windChill", T("Wind Chill")),
        ("wind.galeWind", T("Gale Wind")),
        ("wind.hurricaneForceWind", T("Hurricane Force Wind")),
        ("wind.stormForceWind", T("Storm Force Wind")),
        ("wind.strongWind", T("Strong Wind")),
        ("other.buildingCollapsed", T("Building Collapsed")),
        ("other.peopleTrapped", T("People Trapped")),
        ("other.powerFailure", T("Power Failure")),
    ])
    irs_incident_type_opts = s3_sortOrderedDict(irs_incident_type_opts)

    # This Table defines which Categories are visible to end-users
    resourcename = "icategory"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            Field("code"))
    table.code.label = T("Category")
    table.code.requires = IS_IN_SET(irs_incident_type_opts)
    table.code.represent = lambda opt: irs_incident_type_opts.get(opt, opt)
    
    def irs_icategory_onvalidation(form):
        """
            Incident Category Validation:
                Prevent Duplicates

            Done here rather than in .requires to maintain the dropdown.
        """

        table = db.irs_icategory
        category, error = IS_NOT_ONE_OF(db, "irs_icategory.code")(form.vars.code)
        if error:          
            form.errors.code = error

        return False
    s3xrc.model.configure(table,
                          onvalidation=irs_icategory_onvalidation, 
                          list_fields=[ "code" ])

    # -----------------------------------------------------------------------------
    # Reports
    # This is a report of an Incident
    # @ToDo: A single incident may generate many reports, so we should have a 'lead incident'

    resourcename = "ireport"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            super_link(db.sit_situation),
                            Field("name"),
                            Field("message", "text"),
                            Field("category"),
                            person_id(),
                            Field("contact"),
                            organisation_id(),
                            Field("datetime", "datetime"),
                            location_id(),
                            document_id(),
                            Field("verified", "boolean"),
                            comments(),
                            migrate=migrate, *s3_meta_fields())

    table.category.label = T("Category")
    # The full set available to Admins & Imports/Exports
    # (users use the subset by over-riding this in the Controller)
    table.category.requires = IS_NULL_OR(IS_IN_SET(irs_incident_type_opts))
    table.category.represent = lambda opt: irs_incident_type_opts.get(opt, opt)

    table.name.label = T("Short Description")
    table.name.requires = IS_NOT_EMPTY()

    table.message.label = T("Message")
    table.message.represent = lambda message: shn_abbreviate(message)

    table.person_id.label = T("Reporter Name")
    table.person_id.comment = (T("At/Visited Location (not virtual)"),
                               shn_person_comment(T("Reporter Name"), T("The person at the location who is reporting this incident (optional)")))

    table.contact.label = T("Contact Details")

    table.datetime.label = T("Date/Time")
    table.datetime.requires = [IS_NOT_EMPTY(),
                               IS_UTC_DATETIME(utc_offset=shn_user_utc_offset(), allow_future=False)]

    organisation_id.label = T("Assign to Org.")

    #table.persons_affected.label = T("# of People Affected")
    #table.persons_injured.label = T("# of People Injured")
    #table.persons_deceased.label = T("# of People Deceased")

    table.verified.label = T("Verified?")
    table.verified.represent = lambda verified: (T("No"), T("Yes"))[verified == True]

    # CRUD strings
    ADD_INC_REPORT = T("Add Incident Report")
    LIST_INC_REPORTS = T("List Incident Reports")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_INC_REPORT,
        title_display = T("Incident Report Details"),
        title_list = LIST_INC_REPORTS,
        title_update = T("Edit Incident Report"),
        title_search = T("Search Incident Reports"),
        subtitle_create = T("Add New Incident Report"),
        subtitle_list = T("Incident Reports"),
        label_list_button = LIST_INC_REPORTS,
        label_create_button = ADD_INC_REPORT,
        label_delete_button = T("Delete Incident Report"),
        msg_record_created = T("Incident Report added"),
        msg_record_modified = T("Incident Report updated"),
        msg_record_deleted = T("Incident Report deleted"),
        msg_list_empty = T("No Incident Reports currently registered"))

    # We don't want these visible in Create forms
    # (we override in Update forms in controller)
    table.verified.writable = table.verified.readable = False

    s3xrc.model.configure(table,
                          list_fields = ["id", "category", "location_id", "organisation_id", "verified", "name", "message"]
                          )

    # irs_ireport as component of doc_documents
    s3xrc.model.add_component(module, resourcename,
                              multiple=True,
                              joinby=dict(doc_document="document_id"))

    incident_id = S3ReusableField("incident_id", table,
                                  requires = IS_NULL_OR(IS_ONE_OF(db, "irs_ireport.id", "%(name)s")),
                                  represent = lambda id: id,
                                  label = T("Incident"),
                                  ondelete = "RESTRICT")

    # -----------------------------------------------------------------------------
    irs_image_type_opts = {
        1:T("Photograph"),
        2:T("Map"),
        3:T("Document Scan"),
        99:T("other")
    }

    # Images associated with the Incident Report
    resourcename = "iimage"
    tablename = "%s_%s" % (module, resourcename)
    table = db.define_table(tablename,
                            incident_id(),
                            Field("type", "integer",
                                  requires = IS_IN_SET(irs_image_type_opts, zero=None),
                                  default = 1,
                                  label = T("Image Type"),
                                  represent = lambda opt: irs_image_type_opts.get(opt, UNKNOWN_OPT)),
                            image_id(),
                            Field("description"),
                            migrate=migrate, *s3_meta_fields())

    # CRUD strings
    ADD_IMAGE = T("Add Image")
    LIST_IMAGES = T("List Images")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_IMAGE,
        title_display = T("Image Details"),
        title_list = LIST_IMAGES,
        title_update = T("Edit Image"),
        title_search = T("Search Images"),
        subtitle_create = T("Add New Image"),
        subtitle_list = T("Images"),
        label_list_button = LIST_IMAGES,
        label_create_button = ADD_IMAGE,
        msg_record_created = T("Image added"),
        msg_record_modified = T("Image updated"),
        msg_record_deleted = T("Image deleted"),
        msg_list_empty = T("No Images currently registered"))

    s3xrc.model.add_component(module, resourcename,
                              multiple = True,
                              joinby = dict(irs_ireport="incident_id"))
    # -----------------------------------------------------------------------------
    @auth.shn_requires_membership(1) # must be Administrator
    def shn_irs_ushahidi_import(r, **attr):

        if r.representation == "html" and \
           r.name == "ireport" and not r.component and not r.id:

            url = r.request.get_vars.get("url", "http://")

            title = T("Incident Reports")
            subtitle = T("Import from Ushahidi Instance")

            form = FORM(TABLE(TR(
                        TH("URL: "),
                        INPUT(_type="text", _name="url", _size="100", _value=url,
                              requires=[IS_URL(), IS_NOT_EMPTY()]),
                        TH(DIV(SPAN("*", _class="req", _style="padding-right: 5px;")))),
                        TR(TD("Ignore Errors?: "),
                        TD(INPUT(_type="checkbox", _name="ignore_errors", _id="ignore_errors"))),
                        TR("", INPUT(_type="submit", _value=T("Import")))))

            label_list_btn = shn_get_crud_string(r.tablename, "title_list")
            list_btn = A(label_list_btn,
                         _href=r.other(method="", vars=None),
                         _class="action-btn")

            rheader = DIV(P(T("API is documented here") + ": http://wiki.ushahidi.com/doku.php?id=ushahidi_api"), P(T("Example") + " URL: http://ushahidi.my.domain/api?task=incidents&by=all&resp=xml&limit=1000"))

            output = dict(title=title, form=form, subtitle=subtitle, list_btn=list_btn, rheader=rheader)

            if form.accepts(request.vars, session):

                import_count = [0]
                def sync(job, import_count = import_count):
                    if job.tablename == "irs_ireport":
                        import_count[0] += 1
                s3xrc.resolve = sync

                ireports = r.resource
                ushahidi = form.vars.url

                ignore_errors = form.vars.get("ignore_errors", None)

                template = os.path.join(request.folder, "static", "xslt", "import", "ushahidi.xsl")

                if os.path.exists(template) and ushahidi:
                    try:
                        success = ireports.import_xml(ushahidi, template=template, ignore_errors=ignore_errors)
                    except:
                        import sys
                        e = sys.exc_info()[1]
                        response.error = e
                    else:
                        if success:
                            count = import_count[0]
                            if count:
                                response.flash = "%s %s" % (import_count[0], T("reports successfully imported."))
                            else:
                                response.flash = T("No reports available.")
                        else:
                            response.error = s3xrc.error


            response.view = "create.html"
            return output

        else:
            raise HTTP(501, BADMETHOD)

    s3xrc.model.set_method(module, "ireport",
                           method="ushahidi",
                           action=shn_irs_ushahidi_import)


    # -----------------------------------------------------------------------------
