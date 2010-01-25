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
                <Style id="hospital">
                    <IconStyle>
                        <Icon>
                            <href>http://haiti.sahanafoundation.org/prod/default/download/gis_marker.image.E_Med_Hospital_S1.png</href>
                        </Icon>
                    </IconStyle>
                </Style>
                <Placemark>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <styleUrl>#hospital</styleUrl>
                    <!-- <description><xsl:value-of select="@url"/></description> -->
                    <description>
                        &lt;table&gt;
                            &lt;tr&gt;
                                &lt;td&gt;EMS Status: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='ems_status']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Facility Status: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='facility_status']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Clinical Status: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='clinical_status']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Beds total: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='total_beds']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Beds available: &lt;/td&gt;
                                &lt;td&gt;<xsl:value-of select="./data[@field='available_beds']/text()"/>&lt;/td&gt;
                            &lt;/tr&gt;
                            &lt;tr&gt;
                                &lt;td&gt;Details: &lt;/td&gt;
                                &lt;td&gt;&lt;a href=<xsl:value-of select="@url"/>&gt;<xsl:value-of select="@url"/>&lt;/a&gt;&lt;/td&gt;
                            &lt;/tr&gt;
                        &lt;/table&gt;
                        <xsl:if test="./resource[@name='hms_shortage']/data[@field='status']/@value='1' or ./resource[@name='hms_shortage']/data[@field='status']/@value='2'">
                            &lt;ul&gt;
                            <xsl:apply-templates select="./resource[@name='hms_shortage']"/>
                            &lt;/ul&gt;
                        </xsl:if>
                    </description>
                    <Point>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                            <xsl:text>,</xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </Point>
                </Placemark>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="./reference[@field='location_id']">
                    <Style><xsl:attribute name="id"><xsl:value-of select="reference[@field='location_id']/@uuid"/></xsl:attribute>
                        <IconStyle>
                            <Icon>
                                <href><xsl:value-of select="reference[@field='location_id']/@marker"/></href>
                            </Icon>
                        </IconStyle>
                    </Style>
                    <Placemark>
                        <name><xsl:value-of select="data[@field='name']"/></name>
                        <styleUrl>#<xsl:value-of select="reference[@field='location_id']/@uuid"/></styleUrl>
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

    <xsl:template match="resource[@name='hms_shortage']">
        <xsl:if test="./data[@field='status']/@value='1' or ./data[@field='status']/@value='2'">
            &lt;li&gt;Shortage [<xsl:value-of select="./data[@field='priority']/text()"/>/<xsl:value-of select="./data[@field='impact']/text()"/>/<xsl:value-of select="./data[@field='type']/text()"/>]: <xsl:value-of select="./data[@field='description']/text()"/>&lt;/li&gt;
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
