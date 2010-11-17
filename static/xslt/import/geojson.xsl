<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GeoJSON Import Templates for Sahana-Eden

         Version 0.1 / 2010-11-17 / by nursix

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
    <xsl:template match="/">
        <s3xrc>
            <xsl:apply-templates select="./geojson"/>
        </s3xrc>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template match="geojson">
        <xsl:choose>
            <xsl:when test="./features">
                <xsl:for-each select="./features">
                    <xsl:call-template name="location"/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="location"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <resource name="gis_location">
            <xsl:attribute name="uuid">
                <xsl:value-of select="./id/text()"/>
            </xsl:attribute>
            <data field="lat">
                <xsl:value-of select="./geometry/coordinates[1]/text()"/>
            </data>
            <data field="lon">
                <xsl:value-of select="./geometry/coordinates[2]/text()"/>
            </data>
        </resource>
    </xsl:template>

</xsl:stylesheet>
