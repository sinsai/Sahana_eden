<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Sahana Eden XSLT Import Template

        Transformation of
            Ushahidi Incidents
        into
            Sahana Eden Tickets
    -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <xsl:apply-templates select="./response/payload"/>
    </xsl:template>

    <xsl:template match="response/payload">
        <xsl:apply-templates select="./incidents"/>
    </xsl:template>

    <xsl:template match="incidents">
        <s3xrc>
            <xsl:for-each select="//incident" >

                <!-- create location 1st so that it can be linked to ticket -->
                <xsl:apply-templates select="./location"/>

                <resource name="ticket_log">

                    <xsl:attribute name="uuid">
                        <!-- Should be replaced by domain when Ushahidi API supports this -->
                        <xsl:text>ushahidi/</xsl:text>
                        <xsl:value-of select="id"/>
                    </xsl:attribute>
            
                    <data field="subject">
                        <xsl:value-of select="title"/>
                    </data>

                    <data field="message">
                        <xsl:value-of select="description"/>
                    </data>

                    <data field="source_id">
                        <xsl:value-of select="id"/>
                    </data>

                    <data field="source_time">
                        <xsl:value-of select="date"/>
                    </data>
                    <!--
                    <data field="">
                        <xsl:value-of select="mode"/>
                    </data>

                    <data field="">
                        <xsl:value-of select="active"/>
                    </data>
                    -->
                    <data field="verified">
                        <xsl:value-of select="verified"/>
                    </data>

                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:text>ushahidi/</xsl:text>
                            <xsl:value-of select="location/id"/>
                        </xsl:attribute>
                    </reference>

                    <data field="categories">
                        <xsl:choose>

                            <xsl:when test="./id=4"> <!-- 4. Menaces | Security Threats -->
                                <xsl:text>2</xsl:text> <!-- Report Security Incident -->
                            </xsl:when>

                        </xsl:choose>
                    </data>
                </resource>

                <!--
                <xsl:apply-templates select="./categories"/>
                -->

            </xsl:for-each>
        </s3xrc>
    </xsl:template>

    <xsl:template match="location">
        <resource name="gis_location">

            <xsl:attribute name="uuid">
                <!-- Should be replaced by domain when Ushahidi API supports this -->
                <xsl:text>ushahidi/</xsl:text>
                <xsl:value-of select="id"/>
            </xsl:attribute>

            <data field="gis_feature_type" value="1">Point</data>

            <data field="name">
                <xsl:value-of select="name"/>
            </data>

            <data field="lat">
                <xsl:value-of select="latitude"/>
            </data>

            <data field="lon">
                <xsl:value-of select="longitude"/>
            </data>

        </resource>
    </xsl:template>

    <xsl:template match="categories">
        <xsl:for-each select="//category">
            <resource name="ticket_log">
                <!-- id -->
                <data field="name">
                    <xsl:value-of select="title"/>
                </data>
            </resource>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
