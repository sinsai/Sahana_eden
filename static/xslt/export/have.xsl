<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:have="urn:oasis:names:tc:emergency:EDXL:HAVE:1.0"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:xnl="urn:oasis:names:tc:ciq:xnl:3"
            xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
            xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3">

    <!-- SahanaPy EDXL-HAVE Export Template -->
    <!-- Version 0.2 / 2010-01-23 / by nursix -->

    <!-- work in progress - work in progress - work in progress -->

    <xsl:output method="xml"/>
    <xsl:param name="domain"/>


    <xsl:template match="/">
        <xsl:apply-templates select="./sahanapy"/>
    </xsl:template>


    <xsl:template match="sahanapy">
        <xsl:if test="./resource[@name='hms_hospital']">
            <have:HospitalStatus>
                <xsl:apply-templates select="./resource[@name='hms_hospital']"/>
            </have:HospitalStatus>
        </xsl:if>
    </xsl:template>


    <xsl:template match="resource[@name='hms_hospital']">
        <have:Hospital>

            <!-- Reproduce the SahanaPy UUID somewhere - but where?
            <xsl:attribute name="uuid">
                <xsl:choose>
                    <xsl:when test="contains(./@uuid, '/')">
                        <xsl:value-of select="./@uuid" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat(/sahanapy/@domain, '/', ./@uuid)" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            -->

            <!-- Last Update Time -->
            <have:LastUpdateTime>
                <xsl:value-of select="./@modified_on"/>
            </have:LastUpdateTime>

            <!-- Organization -->
            <have:Organization>

                <!-- Organization Information -->
                <have:OrganizationInformation>
                    <xnl:OrganisationName>
                        <xnl:NameElement>
                            <xsl:value-of select="./data[@field='name']/text()" />
                        </xnl:NameElement>
                    </xnl:OrganisationName>
                    <xpil:ContactNumbers>
                        <xpil:ContactNumber xpil:MediaType="Telephone" xpil:ContactNature="Business">
                            <xpil:ContactNumberElement>
                                <xsl:value-of select="./data[@field='phone_business']/text()" />
                            </xpil:ContactNumberElement>
                        </xpil:ContactNumber>
                        <xpil:ContactNumber xpil:MediaType="Telephone" xpil:ContactNature="Emergency">
                            <xpil:ContactNumberElement>
                                <xsl:value-of select="./data[@field='phone_emergency']/text()" />
                            </xpil:ContactNumberElement>
                        </xpil:ContactNumber>
                        <xpil:ContactNumber xpil:MediaType="Fax">
                            <xpil:ContactNumberElement>
                                <xsl:value-of select="./data[@field='fax']/text()" />
                            </xpil:ContactNumberElement>
                        </xpil:ContactNumber>
                    </xpil:ContactNumbers>
                    <xpil:Addresses>
                        <xpil:Address>
                            <xal:FreeTextAddress>
                                <xal:AddressLine>
                                    <xsl:value-of select="./data[@field='address']/text()" />
                                </xal:AddressLine>
                            </xal:FreeTextAddress>
                        </xpil:Address>
                    </xpil:Addresses>
                </have:OrganizationInformation>

                <!-- OrganizationGeoLocation -->
                <xsl:if test="./reference[@field='location_id']">
                    <have:OrganizationGeoLocation>
                        <gml:Point>
                            <gml:coordinates>
                                <xsl:value-of select="./reference[@field='location_id']/@lat"/>
                                <xsl:text>, </xsl:text>
                                <xsl:value-of select="./reference[@field='location_id']/@lon"/>
                            </gml:coordinates>
                        </gml:Point>
                    </have:OrganizationGeoLocation>
                </xsl:if>

            </have:Organization>

            <!-- EMS Traffic Status -->
            <have:EmergencyDepartmentStatus>
                <have:EMSTraffic>
                    <have:EMSTrafficStatus>
                        <xsl:choose>
                            <xsl:when test="./data[@field='ems_status']/@value='1'">
                                <xsl:text>Normal</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='ems_status']/@value='2'">
                                <xsl:text>Advisory</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='ems_status']/@value='3'">
                                <xsl:text>Closed</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>Unknown</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </have:EMSTrafficStatus>
                    <xsl:if test="./data[@field='ems_reason']/text()">
                        <have:EMSTrafficReason>
                            <xsl:value-of select="./data[@field='ems_reason']/text()"/>
                        </have:EMSTrafficReason>
                    </xsl:if>
                </have:EMSTraffic>
            </have:EmergencyDepartmentStatus>

            <!-- Hospital Facility Status -->
            <have:HospitalFacilityStatus>
                <have:FacilityStatus>
                    <xsl:choose>
                        <xsl:when test="./data[@field='facility_status']/@value='1'">
                            <xsl:text>Normal</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='facility_status']/@value='2'">
                            <xsl:text>Compromised</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='facility_status']/@value='3'">
                            <xsl:text>Evacuating</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='facility_status']/@value='4'">
                            <xsl:text>Closed</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Unknown</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </have:FacilityStatus>
                <have:ClinicalStatus>
                    <xsl:choose>
                        <xsl:when test="./data[@field='clinical_status']/@value='1'">
                            <xsl:text>Normal</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='clinical_status']/@value='2'">
                            <xsl:text>Full</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='clinical_status']/@value='3'">
                            <xsl:text>Closed</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>NotApplicable</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </have:ClinicalStatus>
                <have:MorgueCapacity>
                    <have:MorgueCapacityStatus>
                        <xsl:choose>
                            <xsl:when test="./data[@field='morgue_status']/@value='1'">
                                <xsl:text>Open</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='morgue_status']/@value='2'">
                                <xsl:text>Full</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='morgue_status']/@value='3'">
                                <xsl:text>Exceeded</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='morgue_status']/@value='4'">
                                <xsl:text>Closed</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>Unknown</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </have:MorgueCapacityStatus>
                    <have:MorgueCapacityUnits>
                        <xsl:value-of select="./data[@field='morgue_units']/text()"/>
                    </have:MorgueCapacityUnits>
                </have:MorgueCapacity>
                <have:SecurityStatus>
                    <xsl:choose>
                        <xsl:when test="./data[@field='security_status']/@value='1'">
                            <xsl:text>Normal</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='security_status']/@value='2'">
                            <xsl:text>Elevated</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='security_status']/@value='3'">
                            <xsl:text>RestrictedAccess</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='security_status']/@value='4'">
                            <xsl:text>Lockdown</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='security_status']/@value='5'">
                            <xsl:text>Quarantine</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='security_status']/@value='6'">
                            <xsl:text>Closed</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Unknown</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </have:SecurityStatus>
                <have:Activity24Hr>
                    <have:Admissions>
                        <xsl:value-of select="./data[@field='admissions24']"/>
                    </have:Admissions>
                    <have:Discharges>
                        <xsl:value-of select="./data[@field='discharges24']"/>
                    </have:Discharges>
                    <have:Deaths>
                        <xsl:value-of select="./data[@field='deaths24']"/>
                    </have:Deaths>
                </have:Activity24Hr>
            </have:HospitalFacilityStatus>

            <!-- Bed Capacity Status, TODO: adapt to new report structure! -->
            <have:HospitalBedCapacityStatus>
                <have:BedCapacity>
                    <have:BedType>MedicalSurgical</have:BedType>
                    <have:Capacity>
                        <have:CapacityStatus>VacantAvailable</have:CapacityStatus>
                        <have:AvailableCount>
                            <xsl:value-of select="./data[@field='available_beds']/text()" />
                        </have:AvailableCount>
                        <have:BaselineCount>
                            <xsl:value-of select="./data[@field='total_beds']/text()" />
                        </have:BaselineCount>
                    </have:Capacity>
                </have:BedCapacity>
            </have:HospitalBedCapacityStatus>

            <have:HospitalResourceStatus>
                <have:FacilityOperations>
                    <xsl:call-template name="ResourceStatusOptions">
                        <xsl:with-param name="value" select="./data[@field='facility_operations']/@value"/>
                    </xsl:call-template>
                </have:FacilityOperations>
                <have:ClinicalOperations>
                    <xsl:call-template name="ResourceStatusOptions">
                        <xsl:with-param name="value" select="./data[@field='clinical_operations']/@value"/>
                    </xsl:call-template>
                </have:ClinicalOperations>
                <have:Staffing>
                    <xsl:call-template name="ResourceStatusOptions">
                        <xsl:with-param name="value" select="./data[@field='staffing']/@value"/>
                    </xsl:call-template>
                </have:Staffing>

                <xsl:if test="./data[@field='doctors']/text()">
                    <have:ResourceInformationText>
                        <xsl:text>Doctors available: </xsl:text>
                        <xsl:value-of select="./data[@field='doctors']/text()"/>
                    </have:ResourceInformationText>
                </xsl:if>

                <xsl:if test="./data[@field='nurses']/text()">
                    <have:ResourceInformationText>
                        <xsl:text>Nurses available: </xsl:text>
                        <xsl:value-of select="./data[@field='nurses']/text()"/>
                    </have:ResourceInformationText>
                </xsl:if>

                <xsl:if test="./data[@field='non_medical_staff']/text()">
                    <have:ResourceInformationText>
                        <xsl:text>Non-medical staff available: </xsl:text>
                        <xsl:value-of select="./data[@field='non_medical_staff']/text()"/>
                    </have:ResourceInformationText>
                </xsl:if>

                <xsl:apply-templates select="./resource[@name='hms_shortage']"/>
            </have:HospitalResourceStatus>

            <xsl:apply-templates select="./resource[@name='hms_services']"/>

        </have:Hospital>
    </xsl:template>


    <xsl:template match="resource[@name='hms_shortage']">
        <xsl:if test="./data[@field='status']/@value='1' or ./data[@field='status']/@value='2'">
            <have:CommentText>
                <xsl:text>[Priority: </xsl:text>
                <xsl:value-of select="./data[@field='priority']/text()"/>
                <xsl:text>] </xsl:text>
                <xsl:text>Shortage (</xsl:text>
                <xsl:value-of select="./data[@field='type']/text()"/>
                <xsl:text>/</xsl:text>
                <xsl:value-of select="./data[@field='impact']/text()"/>
                <xsl:text>): </xsl:text>
                <xsl:value-of select="./data[@field='description']/text()"/>
            </have:CommentText>
        </xsl:if>
    </xsl:template>


    <xsl:template match="resource[@name='hms_services']">
        <have:ServiceCoverageStatus>
            <xsl:if test="starts-with(./data[@field='tran']/text(), 'T') or
                          starts-with(./data[@field='tair']/text(), 'T')">
                <have:TransportServicesIndicator>
                    <have:TransportServicesSubType>
                        <xsl:if test="starts-with(./data[@field='tran']/text(), 'T')">
                            <have:AmbulanceServices><xsl:text>true</xsl:text></have:AmbulanceServices>
                        </xsl:if>
                        <xsl:if test="starts-with(./data[@field='tair']/text(), 'T')">
                            <have:AirTransportServices><xsl:text>true</xsl:text></have:AirTransportServices>
                        </xsl:if>
                    </have:TransportServicesSubType>
                </have:TransportServicesIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='psya']/text(), 'T') or
                          starts-with(./data[@field='psyp']/text(), 'T')">
                <have:PsychiatricIndicator>
                    <have:PsychiatricSubType>
                        <xsl:if test="starts-with(./data[@field='psya']/text(), 'T')">
                            <have:PsychiatricAdultGeneral>true</have:PsychiatricAdultGeneral>
                        </xsl:if>
                        <xsl:if test="starts-with(./data[@field='psyp']/text(), 'T')">
                            <have:PsychiatricPediatric>true</have:PsychiatricPediatric>
                        </xsl:if>
                    </have:PsychiatricSubType>
                </have:PsychiatricIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='obgy']/text(), 'T')">
                <have:OBGYNIndicator>
                    <have:OBGYN>true</have:OBGYN>
                </have:OBGYNIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='neon']/text(), 'T')">
                <have:Neonatology>true</have:Neonatology>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='pedi']/text(), 'T')">
                <have:Pediatrics>true</have:Pediatrics>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='dial']/text(), 'T')">
                <have:Dialysis>true</have:Dialysis>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='neur']/text(), 'T')">
                <have:NeurologyIndicator>
                    <have:Neurology>true</have:Neurology>
                </have:NeurologyIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='surg']/text(), 'T')">
                <have:SurgeryIndicator>
                    <have:Surgery>true</have:Surgery>
                </have:SurgeryIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='burn']/text(), 'T')">
                <have:Burn>true</have:Burn>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='card']/text(), 'T')">
                <have:CardiologyIndicator>
                    <have:Cardiology>true</have:Cardiology>
                </have:CardiologyIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='trac']/text(), 'T')">
                <have:TraumaCenterIndicator>
                    <have:TraumaCenterServices>true</have:TraumaCenterServices>
                </have:TraumaCenterIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='infd']/text(), 'T')">
                <have:InfectiousDiseases>true</have:InfectiousDiseases>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='emsd']/text(), 'T')">
                <have:EmergencyDepartment>true</have:EmergencyDepartment>
            </xsl:if>
        </have:ServiceCoverageStatus>
    </xsl:template>


    <xsl:template name="ResourceStatusOptions">
        <xsl:param name="value"/>
        <xsl:choose>
            <xsl:when test="$value='1'">
                <xsl:text>Adequate</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Insufficient</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


</xsl:stylesheet>
