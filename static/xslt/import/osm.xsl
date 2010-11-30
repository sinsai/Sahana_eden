<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:osm="http://openstreetmap.org/osm/0.6">

    <!-- Sahana Eden XSLT Import Template

        Transformation of
            OpenStreetMap Points of Interest
        into
            Sahana Eden Records (Hospitals, Locations)

        Large files can give memory errors, so best to reduce the file first to just the bounding box &/or tag type of interest:
        e.g. (replace single hyphens with double-hyphens)
        osmosis -read-xml haiti.osm -way-key-value keyValueList="amenity.hospital" -used-node -write-xml haiti_hospital.osm
    -->

    <xsl:output method="xml"/>
    <xsl:param name="name"/>

    <xsl:template match="/">
        <xsl:apply-templates select="./osm"/>
    </xsl:template>

    <xsl:template match="osm">
        <s3xrc>
            <xsl:choose>
                <xsl:when test="$name='hospital'">
                    <xsl:apply-templates select="node[./tag[@k='amenity' and @v='hospital']]|way[./tag[@k='amenity' and @v='hospital']]"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="node|way"/>
                </xsl:otherwise>
            </xsl:choose>
        </s3xrc>
    </xsl:template>

    <xsl:template match="node|way">
        <xsl:choose>
            <xsl:when test="$name='hospital'">
                <xsl:call-template name="hospital"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="location"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="hospital">
        <resource name="hms_hospital">

<!--            <xsl:attribute name="modified_on">
                <xsl:value-of select="@timestamp"/>
            </xsl:attribute>-->

            <data field="gov_uuid">
                <xsl:choose>
                    <xsl:when test="./tag[@k='paho:id']">
                        <xsl:value-of select="concat('urn:paho:id:', ./tag[@k='paho:id']/@v)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat('urn:osm:id:', @id)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <!-- Main Record -->
            <data field="name">
                <xsl:choose>
                    <xsl:when test="./tag[@k='name']">
                        <xsl:value-of select="./tag[@k='name']/@v"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat('Facility #', @id)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <!--
            Can add Hospital-specific tags here
                http://wiki.openstreetmap.org/wiki/Tag:amenity%3Dhospital
                    emergency=yes
                    contact:phone=xxx
                    contact:website=xxx
                    <tag k="health_facility:type" v="hospital"/>
                    <tag k="health_facility:type" v="specialized_hospital"/>
                    <tag k="health_facility:type" v="dispensary"/>
                    <tag k="health_facility:type" v="health_center"/>
                    <tag k="health_facility:bed" v="no"/>
                    <tag k="operator" v="DR GERARD JANVIER"/>
                    <tag k="paho:damage" v="Damaged"/>
                    <tag k="paho:damage" v="Severe"/>
            -->

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>
        </resource>
    </xsl:template>

    <xsl:template name="location">
        <resource name="gis_location">

            <xsl:attribute name="uuid">
                <xsl:value-of select="concat('urn:osm:id:', @id)"/>
            </xsl:attribute>

<!--            <xsl:attribute name="modified_on">
                <xsl:value-of select="@timestamp"/>
            </xsl:attribute>-->

            <xsl:choose>
                <xsl:when test="./tag[@v='town']">
                    <!-- @ToDo: How to handle the variability of levels per-country? -->
                    <data field="level">
                        <xsl:text>L3</xsl:text>
                    </data>
                </xsl:when>

                <xsl:when test="./tag[@v='village']">
                    <!-- @ToDo: How to handle the variability of levels per-country? -->
                    <data field="level">
                        <xsl:text>L4</xsl:text>
                    </data>
                </xsl:when>
            </xsl:choose>

            <xsl:if test="./tag[@k='name']">
                <data field="name">
                    <xsl:value-of select="./tag[@k='name']/@v"/>
                </data>
            </xsl:if>

            <xsl:choose>
                <xsl:when test="local-name()='node'">
                    <data field="gis_feature_type" value="1">Point</data>

                    <data field="lat">
                        <xsl:value-of select="@lat"/>
                    </data>
                    <data field="lon">
                        <xsl:value-of select="@lon"/>
                    </data>
                </xsl:when>
                <xsl:when test="local-name()='way'">
                    <data field="gis_feature_type" value="3">Polygon</data>
                    <data field="wkt">
                        <xsl:text>POLYGON((</xsl:text>
                        <xsl:for-each select="./nd">
                            <xsl:variable name="id" select="@ref"/>
                            <xsl:for-each select="//node[@id=$id][1]">
                                <xsl:value-of select="concat(@lat, ' ', @lon)"/>
                            </xsl:for-each>
                            <xsl:if test="following-sibling::nd">
                                <xsl:text>,</xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                        <xsl:text>))</xsl:text>
                    </data>
                </xsl:when>
            </xsl:choose>

            <!-- @ToDo: Support Is-In
            <data field="parent">
                <xsl:value-of select=""/>
            </data>
            -->

        </resource>
    </xsl:template>

</xsl:stylesheet>
