<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:have="urn:oasis:names:tc:emergency:EDXL:HAVE:1.0"
            xmlns:gml="http://www.opengis.net/gml">

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <xsl:if test="./sahanapy/resource[@name='hms_hospital']">
            <have:HospitalStatus>
                <xsl:apply-templates select="./sahanapy/resource[@name='hms_hospital']"/>
            </have:HospitalStatus>
        </xsl:if>
    </xsl:template>

    <xsl:template match="resource[@name='hms_hospital']">
        <have:Hospital>
            <have:Organization>
                <have:OrganizationInformation>
                    <have:OrganisationName>
                        <xsl:value-of select="./data[@field='name']/text()" />
                    </have:OrganisationName>
                    <have:ContactNumbers>
                        <xsl:text>Phone 1: </xsl:text>
                        <xsl:value-of select="./data[@field='phone1']/text()" />
                        <xsl:text>, Phone 2: </xsl:text>
                        <xsl:value-of select="./data[@field='phone1']/text()" />
                        <xsl:text>, Fax: </xsl:text>
                        <xsl:value-of select="./data[@field='phone1']/text()" />
                    </have:ContactNumbers>
                    <have:Addresses>
                        <xsl:value-of select="./data[@field='address']/text()" />
                    </have:Addresses>
                </have:OrganizationInformation>
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
            <xsl:if test="./data[@field='available_beds']">
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
            </xsl:if>
            <have:HospitalFacilityStatus>
                <have:FacilityStatus>
                    <xsl:choose>
                        <xsl:when test="./data[@field='status']/@value='1'">
                            <xsl:text>Normal</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='status']/@value='5'">
                            <xsl:text>Closed</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Compromised</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </have:FacilityStatus>
            </have:HospitalFacilityStatus>
        </have:Hospital>
    </xsl:template>

</xsl:stylesheet>
