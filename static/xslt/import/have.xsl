<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:have="urn:oasis:names:tc:emergency:EDXL:HAVE:1.0"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:xnl="urn:oasis:names:tc:ciq:xnl:3"
            xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
            xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3">

    <!-- **********************************************************************

         EDXL-HAVE Import Templates

         Version 0.3 / 2010-10-26 / by nursix

         Copyright (c) 2010 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./have:HospitalStatus"/>
    </xsl:template>

    <xsl:template match="have:HospitalStatus">
        <s3xrc>
            <xsl:apply-templates select="./have:Hospital"/>
        </s3xrc>
    </xsl:template>


    <!-- ****************************************************************** -->
    <!-- Hospital -->
    <xsl:template match="have:Hospital">
        <resource name="hms_hospital">

            <!-- Modification date -->
            <!-- @todo: pattern check -->
            <xsl:if test="./have:LastUpdateTime/text()">
                <xsl:attribute name="modified_on">
                    <xsl:value-of select="./have:LastUpdateTime/text()"/>
                </xsl:attribute>
            </xsl:if>

            <!-- Organization Info -->
            <xsl:apply-templates select="./have:Organization"/>

            <!-- Operative Status -->
            <xsl:apply-templates select="./have:EmergencyDepartmentStatus"/>
            <xsl:apply-templates select="./have:HospitalBedCapacityStatus"/>

            <!-- Facility and Resources Status -->
            <xsl:apply-templates select="./have:HospitalFacilityStatus"/>
            <xsl:apply-templates select="./have:HospitalResourceStatus"/>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organization -->
    <xsl:template match="have:Organization">
        <xsl:apply-templates match="./have:OrganizationInformation"/>
        <xsl:apply-templates match="./have:OrganizationGeoLocation"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- EmergencyDepartmentStatus -->
    <xsl:template match="have:EmergencyDepartmentStatus">
        <!-- @todo: implement -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalBedCapacityStatus -->
    <xsl:template match="have:HospitalBedCapacityStatus">
        <!-- @todo: implement -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalFacilityStatus -->
    <xsl:template match="have:HospitalFacilityStatus">
        <!-- @todo: implement -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalResourceStatus -->
    <xsl:template match="have:HospitalResourceStatus">
        <!-- @todo: implement -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OrganizationInformation -->
    <xsl:template match="have:OrganizationInformation">
        <xsl:apply-template select="./xnl:OrganisationName"/>
        <data field="facility_type" value="1">Hospital</data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Name and UID -->
    <xsl:template match="xnl:OrganisationName">
        <!-- @todo: import alternative names -->
        <xsl:variable name="name"
                      select="./xnl:NameElement[1]/text()"/>
        <xsl:variable name="uuid_provided"
                      select="./@xnl:ID"/>
        <xsl:if test="$uuid_provided">
            <data field="gov_uuid">
                <xsl:value-of select="$uuid_provided"/>
            </data>
        </xsl:if>
        <data field="name">
            <xsl:value-of select="$name"/>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Contact Numbers -->
    <xsl:template match="xpil:ContactNumbers">
        <!-- @todo: implement -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Addresses -->
    <xsl:template match="xpil:Addresses">
        <!-- @todo: implement -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- GeoLocation -->
    <xsl:template match="have:OrganizationGeoLocation">
        <xsl:variable name="location"
                      select="./gml:Point/gml:coordinates/text()"/>
        <xsl:variable name="location_id"
                      select="./gml:Point/@gml:id"/>
        <xsl:variable name="name"
                      select="../have:OrganizationInformation/xnl:OrganisationName/xnl:NameElement[1]/text()"/>
        <xsl:if test="$location">
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <data field="name">
                        <xsl:value-of select="$name"/>
                    </data>
                    <xsl:if test="$location_id">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$location_id"/>
                        </xsl:attribute>
                    </xsl:if>
                    <data field="gis_feature_type" value="1">Point</data>
                    <data field="lat">
                        <xsl:value-of select="normalize-space(substring-before($location, ','))"/>
                    </data>
                    <data field="lon">
                        <xsl:value-of select="normalize-space(substring-after($location, ','))"/>
                    </data>
                </resource>
            </reference>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
