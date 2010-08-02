# -*- coding: utf-8 -*-

"""
    Incident Reporting System - Model
"""

module = "ir"

# Reports
# We may wish later to add Incidents, each of which may generate several Reports
ir_incident_types = {
    1:T("animalHealth.animalDieOff"),
    2:T("animalHealth.animalFeed"),
    3:T("aviation.aircraftCrash"),
    4:T("aviation.aircraftHijacking"),
    5:T("aviation.airportClosure"),
    6:T("aviation.airspaceClosure"),
    7:T("aviation.noticeToAirmen"),
    8:T("aviation.spaceDebris"),
    9:T("civil.demonstrations"),
    10:T("civil.dignitaryVisit"),
    11:T("civil.displacedPopulations"),
    12:T("civil.emergency"),
    13:T("civil.looting"),
    14:T("civil.publicEvent"),
    15:T("civil.riot"),
    16:T("civil.volunteerRequest"),
    17:T("crime.bomb"),
    18:T("crime.bombExplosion"),
    19:T("crime.bombThreat"),
    20:T("crime.dangerousPerson"),
    21:T("crime.drugs"),
    22:T("crime.homeCrime"),
    23:T("crime.illegalImmigrant"),
    24:T("crime.industrialCrime"),
    25:T("crime.poisoning"),
    26:T("crime.retailCrime"),
    27:T("crime.shooting"),
    28:T("crime.stowaway"),
    29:T("crime.terrorism"),
    30:T("crime.vehicleCrime"),
    31:T("fire.forestFire"),
    32:T("fire.hotSpot"),
    33:T("fire.industryFire"),
    34:T("fire.smoke"),
    35:T("fire.urbanFire"),
    36:T("fire.wildFire"),
    37:T("flood.damOverflow"),
    38:T("flood.flashFlood"),
    39:T("flood.highWater"),
    40:T("flood.overlandFlowFlood"),
    41:T("flood.tsunami"),
    42:T("geophysical.avalanche"),
    43:T("geophysical.earthquake"),
    44:T("geophysical.lahar"),
    45:T("geophysical.landslide"),
    46:T("geophysical.magneticStorm"),
    47:T("geophysical.meteorite"),
    48:T("geophysical.pyroclasticFlow"),
    49:T("geophysical.pyroclasticSurge"),
    50:T("geophysical.volcanicAshCloud"),
    51:T("geophysical.volcanicEvent"),
    52:T("hazardousMaterial.biologicalHazard"),
    53:T("hazardousMaterial.chemicalHazard"),
    54:T("hazardousMaterial.explosiveHazard"),
    55:T("hazardousMaterial.fallingObjectHazard"),
    56:T("hazardousMaterial.infectiousDisease"),
    57:T("hazardousMaterial.poisonousGas"),
    58:T("hazardousMaterial.radiologicalHazard"),
    59:T("health.infectiousDisease"),
    60:T("health.infestation"),
    61:T("ice.iceberg"),
    62:T("ice.icePressure"),
    63:T("ice.rapidCloseLead"),
    64:T("ice.specialIce"),
    65:T("marine.marineSecurity"),
    66:T("marine.nauticalAccident"),
    67:T("marine.nauticalHijacking"),
    68:T("marine.portClosure"),
    69:T("marine.specialMarine"),
    70:T("meteorological.blizzard"),
    71:T("meteorological.blowingSnow"),
    72:T("meteorological.drought"),
    73:T("meteorological.dustStorm"),
    74:T("meteorological.fog"),
    75:T("meteorological.freezingDrizzle"),
    76:T("meteorological.freezingRain"),
    77:T("meteorological.freezingSpray"),
    78:T("meteorological.hail"),
    79:T("meteorological.hurricane"),
    80:T("meteorological.rainFall"),
    81:T("meteorological.snowFall"),
    82:T("meteorological.snowSquall"),
    83:T("meteorological.squall"),
    84:T("meteorological.stormSurge"),
    85:T("meteorological.thunderstorm"),
    86:T("meteorological.tornado"),
    87:T("meteorological.tropicalStorm"),
    88:T("meteorological.waterspout"),
    89:T("meteorological.winterStorm"),
    90:T("missingPerson.amberAlert"),
    91:T("missingPerson.missingVulnerablePerson"),
    92:T("missingPerson.silver"),
    93:T("publicService.emergencySupportFacility"),
    94:T("publicService.emergencySupportService"),
    95:T("publicService.schoolClosure"),
    96:T("publicService.schoolLockdown"),
    97:T("publicService.serviceOrFacility"),
    98:T("publicService.transit"),
    99:T("railway.railwayAccident"),
    100:T("railway.railwayHijacking"),
    101:T("roadway.bridgeClosure"),
    102:T("roadway.hazardousRoadConditions"),
    103:T("roadway.roadwayAccident"),
    104:T("roadway.roadwayClosure"),
    105:T("roadway.roadwayDelay"),
    106:T("roadway.roadwayHijacking"),
    107:T("roadway.roadwayUsageCondition"),
    108:T("roadway.trafficReport"),
    109:T("temperature.arcticOutflow"),
    110:T("temperature.coldWave"),
    111:T("temperature.flashFreeze"),
    112:T("temperature.frost"),
    113:T("temperature.heatAndHumidity"),
    114:T("temperature.heatWave"),
    115:T("temperature.windChill"),
    116:T("wind.galeWind"),
    117:T("wind.hurricaneForceWind"),
    118:T("wind.stormForceWind"),
    119:T("wind.strongWind")
}

resource = "report"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename, timestamp, uuidstamp, authorstamp, deletion_status,
        Field("name"),
        Field("category", "integer"),
        person_id,
        Field("contact"),
        location_id,
        Field("time", "datetime"),
        Field("photo", "upload"), 
        Field("affected", "integer"), 
        comments, 
        )
table.name.requires = IS_NOT_EMPTY()
table.category.requires = IS_NULL_OR(IS_IN_SET(ir_incident_types))
table.category.represent = lambda opt: ir_incident_types.get(opt, opt)
table.person_id.default = session.auth.user.id if auth.is_logged_in() else None

# Status of a Report
# This is designed 
resource = "status"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
        Field("report_id", db.ir_report),
        Field("status", "text"), 
        Field("time", "datetime"), 
   )

table.report_id.represent = lambda id: db(db.ir_report.id == id).select(db.ir_report.name, limitby=(0, 1)).first().name
table.report_id.label = T("Report")
table.status.label = T("Status Update")

# Status as a component of Report
s3xrc.model.add_component(module,
                          resource,
                          mutiple=True,
                          joinby=dict(ir_report="report_id"),
                          deletable=True,
                          editable=True
                          )
