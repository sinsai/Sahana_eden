<xsl:stylesheet version="1.0"
  xmlns="http://www.opengis.net/kml/2.2"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/">
        <kml xmlns="http://www.opengis.net/kml/2.2">
            <Document>
                <xsl:apply-templates select="sahanapy"/>
            </Document>
        </kml>
    </xsl:template>

    <xsl:template match="sahanapy">
        <Folder>
            <name>SahanaPy GIS Features</name>
            <xsl:apply-templates select="resource"/>
        </Folder>
    </xsl:template>

    <xsl:template match="resource">
        <xsl:choose>
            <xsl:when test="@name='gis_location'">
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <description><xsl:value-of select="@url"/></description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="data[@field='lon']"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="data[@field='lat']"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:when>
            <xsl:when test="@name='hms_hospital'">
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <description>
                        <table border="0" padding="3">
                            <tr>
                                <td>EMS Status:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='ems_status']/text()"/>
                                </td>
                            </tr>
                            <tr>
                                <td>Facility Status:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='facility_status']/text()"/>
                                </td>
                            </tr>
                            <tr>
                                <td>Clinical Status:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='clinical_status']/text()"/>
                                </td>
                            </tr>
                            <tr>
                                <td>Morgue Status:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='morgue_status']/text()"/>
                                </td>
                            </tr>
                            <tr>
                                <td>Staffing:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='staffing']/text()"/>
                                </td>
                            </tr>
                            <tr>
                                <td>Beds total:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='total_beds']/text()"/>
                                </td>
                            </tr>
                            <tr>
                                <td>Beds available:</td>
                                <td>
                                    <xsl:value-of select="./data[@field='available_beds']/text()"/>
                                </td>
                            </tr>
                        </table>
                        <p><xsl:value-of select="@url"/></p>
                    </description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="data[@field='lon']"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="data[@field='lat']"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="./reference[@field='location_id']">
                    <Placemark>
                        <name><xsl:value-of select="data[@field='name']"/></name>
                        <description><xsl:value-of select="@url"/></description>
                        <Point>
                            <coordinates>
                                <xsl:value-of select="reference[@field='location_id']/@lon"/>
                                <xsl:text>,</xsl:text>
                                <xsl:value-of select="reference[@field='location_id']/@lat"/>
                            </coordinates>
                        </Point>
                    </Placemark>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
