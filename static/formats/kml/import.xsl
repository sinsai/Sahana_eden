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

    <!-- Which Resource? -->
    <xsl:param name="name"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:choose>
                <!-- Shelters -->
                <xsl:when test="$name='shelter'">
                    <xsl:call-template name="shelters"/>
                </xsl:when>

                <!-- Default to Locations -->
                <xsl:otherwise>
                    <xsl:call-template name="locations"/>
                </xsl:otherwise>
            </xsl:choose>
        </s3xml>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="shelters">
        <xsl:for-each select="//kml:Placemark">
            <xsl:call-template name="shelter"/>
       </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="shelter">
        <resource name="cr_shelter">

            <!-- The name field is populated with the Prefecture in the Japan export! -->
            <!--
            <data field="name">
                <xsl:value-of select="./kml:name/text()"/>
            </data>
            -->

            <!-- HTML isn't really appropriate for the Comments field -->
            <!--
            <data field="comments">
                <xsl:value-of select="./kml:description/text()"/>
            </data>
            -->

            <xsl:for-each select="./kml:ExtendedData">
                <xsl:call-template name="extended"/>
            </xsl:for-each>
            
            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>    
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="extended">
        <!-- Format produced by Google Fusion
        e.g. Japan feed: http://www.google.com/intl/ja/crisisresponse/japanquake2011_shelter.kmz -->
        <xsl:for-each select="./kml:Data[@name='Name']">
            <data field="name">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Population']">
            <data field="population">
                <xsl:call-template name="integer"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Capacity']">
            <data field="capacity">
                <xsl:call-template name="integer"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Notes']">
            <data field="comments">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Source']">
            <data field="source">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Prefecture']">
            <data field="L1">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='City']">
            <data field="L2">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <!-- Date needs converting -->
        <!--
        <xsl:for-each select="./kml:Data[@name='UpdateDate']">
            <xsl:attribute name="modified_on">
                <xsl:call-template name="detail"/>
             </xsl:attribute>
        </xsl:for-each>
        -->

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="detail">
        <xsl:value-of select="./kml:value/text()"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="integer">
        <xsl:variable name="x">
            <xsl:value-of select="./kml:value/text()"/>
        </xsl:variable>
        <xsl:choose>
            <!-- This test isn't working with lxml, works with Xalan -->
            <xsl:when test="floor($x) = $x">
                <xsl:value-of select="$x"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="locations">
        <xsl:for-each select="//kml:Placemark">
            <xsl:call-template name="location"/>
       </xsl:for-each>
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
                <xsl:with-param name="coordinate" select="./kml:coordinates/text()"/>
            </xsl:call-template>
        </data>
        <data field="lat">
            <xsl:call-template name="lat">
                <xsl:with-param name="coordinate" select="./kml:coordinates/text()"/>
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
        <xsl:param name="coordinate"/>
        <xsl:call-template name="left-trim">
            <xsl:with-param name="s" select="substring-before($coordinate, ',')"/>
        </xsl:call-template>
    </xsl:template>
    
    <xsl:template name="lat">
        <xsl:param name="coordinate"/>
        <xsl:choose>
            <xsl:when test="contains (substring-after($coordinate, ','), ',')">
                <!-- Altitude field present -->
                <xsl:value-of select="substring-before(substring-after($coordinate, ','), ',')"/>
            </xsl:when>
            <xsl:otherwise>
                <!-- Altitude field not present -->
                <xsl:call-template name="right-trim">
                    <xsl:with-param name="s" select="substring-after($coordinate, ',')"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    
    <xsl:template name="left-trim">
      <xsl:param name="s" />
      <xsl:choose>
        <xsl:when test="substring($s, 1, 1) = ''">
          <xsl:value-of select="$s"/>
        </xsl:when>
        <xsl:when test="normalize-space(substring($s, 1, 1)) = ''">
          <xsl:call-template name="left-trim">
            <xsl:with-param name="s" select="substring($s, 2)" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$s" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <xsl:template name="right-trim">
      <xsl:param name="s" />
      <xsl:choose>
        <xsl:when test="substring($s, 1, 1) = ''">
          <xsl:value-of select="$s"/>
        </xsl:when>
        <xsl:when test="normalize-space(substring($s, string-length($s))) = ''">
          <xsl:call-template name="right-trim">
            <xsl:with-param name="s" select="substring($s, 1, string-length($s) - 1)" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$s" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>