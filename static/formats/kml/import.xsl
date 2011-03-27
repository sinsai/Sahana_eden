<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:kml="http://www.opengis.net/kml/2.2"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         KML Import Templates for Sahana-Eden

         http://schemas.opengis.net/kml/2.2.0/
         http://code.google.com/apis/kml/documentation/kmlreference.html

         Version 0.1 / 2011-03-27 / by flavour

         Copyright (c) 2011 Sahana Software Foundation

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
    <xsl:output method="xml" indent="yes"/>
    <!--<xsl:include href="../xml/commons.xsl"/>-->
    
    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:for-each select="//kml:Placemark">
                <xsl:call-template name="location"/>
           </xsl:for-each>
        </s3xml>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <resource name="gis_location">

            <data field="name">
                <xsl:value-of select="./kml:name/text()"/>
            </data>

            <!-- Handle Points -->
            <xsl:for-each select="./kml:Point">
                <xsl:call-template name="point"/>
            </xsl:for-each>

            <!-- Handle Linestrings -->
            <!--
            <xsl:for-each select="./kml:LineString">
                <xsl:call-template name="linestring"/>
            </xsl:for-each>
            -->

            <!-- Handle Polygons -->
            <!--
            <xsl:for-each select="./kml:Polygon">
                <xsl:call-template name="polygon"/>
            </xsl:for-each>
            -->

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="point">
        <data field="gis_feature_type">1</data>
        <data field="lon">
            <xsl:call-template name="lon">
                <xsl:with-param name="lonlatalt" select="./kml:coordinates/text()"/>
            </xsl:call-template>
        </data>
        <data field="lat">
            <xsl:call-template name="lat">
                <xsl:with-param name="lonlatalt" select="./kml:coordinates/text()"/>
            </xsl:call-template>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="linestring">
        <data field="gis_feature_type">2</data>
        <data field="wkt">
            <xsl:text>LINESTRING(</xsl:text>
            <!-- @ToDo Convert Coordinates to build WKT string -->
            <!-- http://code.google.com/apis/kml/documentation/kml_tut.html#paths -->
            <!-- http://en.wikipedia.org/wiki/Well-known_text -->
            <xsl:value-of select="./kml:coordinates/text()"/>
            <xsl:text>)</xsl:text>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="polygon">
        <data field="gis_feature_type">3</data>
        <data field="wkt">
            <xsl:text>POLYGON((</xsl:text>
            <!-- @ToDo Convert Coordinates to build WKT string -->
            <!-- http://code.google.com/apis/kml/documentation/kml_tut.html#polygons -->
            <!-- http://en.wikipedia.org/wiki/Well-known_text -->
            <xsl:value-of select="./kml:coordinates/text()"/>
            <xsl:text>))</xsl:text>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="lon">
        <xsl:param name="lonlatalt"/>
        <!-- @ToDO: Trim leading whitespace: http://stackoverflow.com/questions/1498778/left-trim-white-space-xslt-1-0 -->
        <xsl:value-of select="substring-before($lonlatalt, ',')"/>
    </xsl:template>
    
    <xsl:template name="lat">
        <xsl:param name="lonlatalt"/>
        <xsl:value-of select="substring-before(substring-after($lonlatalt, ','), ',')"/>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>