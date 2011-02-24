<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:output method="xml"/>
    <xsl:include href="../xml/commons.xsl"/>

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table[1]"/>
        </s3xml>
    </xsl:template>

    <xsl:template match="table">
        <xsl:apply-templates select="./row"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospital -->
    <xsl:template match="row">
        <xsl:variable name="hospital_name">
            <xsl:choose>
                <xsl:when test="./col[@field='HospitalName']/text()!=''">
                    <xsl:value-of select="./col[@field='HospitalName']"/>
                </xsl:when>
                <xsl:when test="./col[@field='ID']/text()!=''">
                    <xsl:value-of select="./col[@field='ID']"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="./col[@field='OBJECTID']"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:if test="$hospital_name">
            <resource name="hms_hospital">
                <data field="gov_uuid">
                    <xsl:value-of select="./col[@field='OBJECTID']"/>
                </data>
                <data field="name">
                    <xsl:value-of select="$hospital_name"/>
                </data>
                <data field="phone_exchange">
                    <xsl:value-of select="./col[@field='Phone']"/>
                </data>
                <data field="website">
                    <xsl:value-of select="./col[@field='URL']"/>
                </data>
                <data field="comment">
                    <xsl:value-of select="concat('Source: ', ./col[@field='Source'])"/>
                </data>
                <xsl:variable name="facility_type">1</xsl:variable>
                <xsl:call-template name="HospitalLocation">
                    <xsl:with-param name="hospital_name">
                        <xsl:value-of select="$hospital_name"/>
                    </xsl:with-param>
                </xsl:call-template>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalLocation -->
    <xsl:template name="HospitalLocation">
        <xsl:param name="hospital_name"/>
        <reference field="location_id" resource="gis_location">
            <resource name="gis_location">
                <data field="name">
                    <xsl:value-of select="$hospital_name"/>
                </data>
                <data field="lat">
                    <xsl:value-of select="./col[@field='Latitude']"/>
                </data>
                <data field="lon">
                    <xsl:value-of select="./col[@field='Longitude']"/>
                </data>
            </resource>
        </reference>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
