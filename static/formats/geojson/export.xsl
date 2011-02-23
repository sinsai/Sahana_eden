<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GeoJSON Export Templates for Sahana-Eden

         Version 0.2 / 2010-11-17 / by nursix

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

    <xsl:param name="prefix"/>
    <xsl:param name="name"/>

    <xsl:template match="/">
        <GeoJSON>
            <xsl:apply-templates select="s3xml"/>
        </GeoJSON>
    </xsl:template>

    <xsl:template match="s3xml">
        <xsl:variable name="resource">
            <xsl:value-of select="concat($prefix,'_',$name)"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="count(./resource[@name=$resource])=1">
                <xsl:apply-templates select="./resource[@name=$resource]"/>
            </xsl:when>
            <xsl:otherwise>
                <type>FeatureCollection</type>
                <xsl:for-each select="./resource[@name=$resource]">
                    <features>
                        <xsl:apply-templates select="."/>
                    </features>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uid" select="./@uuid"/>
        <xsl:choose>
            <xsl:when test="//reference[@resource='gis_location' and @uuid=$uid]">
                <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uid]">
                    <xsl:if test="not(../@name='gis_location')">
                        <xsl:apply-templates select=".."/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <type>Feature</type>
                <geometry>
                    <type>
                        <xsl:text>Point</xsl:text>
                    </type>
                    <coordinates>
                        <xsl:value-of select="data[@field='lon']"/>
                    </coordinates>
                    <coordinates>
                        <xsl:value-of select="data[@field='lat']"/>
                    </coordinates>
                </geometry>
                <properties>
                    <id>
                        <xsl:value-of select="$uid"/>
                    </id>
                    <name>
                        <xsl:value-of select="data[@field='name']"/>
                    </name>
                    <marker>
                        <xsl:value-of select="@marker"/>
                    </marker>
                </properties>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="./reference[@field='location_id']">
            <type>Feature</type>
            <geometry>
                <type>
                    <xsl:text>Point</xsl:text>
                </type>
                <coordinates>
                    <xsl:value-of select="reference[@field='location_id']/@lon"/>
                </coordinates>
                <coordinates>
                    <xsl:value-of select="reference[@field='location_id']/@lat"/>
                </coordinates>
            </geometry>
            <properties>
                <id>
                    <xsl:value-of select="reference[@field='location_id']/@uuid"/>
                </id>
                <name>
                    <xsl:value-of select="data[@field='name']"/>
                </name>
                <marker>
                    <xsl:value-of select="reference[@field='location_id']/@marker"/>
                </marker>
            </properties>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
