<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:kml="http://www.opengis.net/kml/2.2"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         KML Import Templates for Sahana-Eden

         http://schemas.opengis.net/kml/2.2.0/
         http://code.google.com/apis/kml/documentation/kmlreference.html

         Version 0.2 / 2011-03-28 / by flavour

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

    <!-- Location Hierarchy fieldnames -->
    <xsl:variable name="L1">Prefecture</xsl:variable>
    <xsl:variable name="L2">City</xsl:variable>
    <xsl:variable name="L3">District</xsl:variable>

    <xsl:variable name="prefix_shelter">shelter:</xsl:variable>
    <xsl:variable name="prefix_location">JP-</xsl:variable>
    <xsl:variable name="separator">~</xsl:variable>

    <xsl:key
        name="L1"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L1]/kml:value/text()"/>

    <xsl:key
        name="L2"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L2]/kml:value/text()"/>

    <xsl:key
        name="L3"
        match="//kml:Placemark"
        use="./kml:ExtendedData/kml:Data[@name=$L3]/kml:value/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Shelters -->
            <xsl:call-template name="shelters"/>

            <!-- Do the Locations Hierarchy -->
            <xsl:call-template name="locations"/>

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

        <xsl:attribute name="uuid">
            <xsl:value-of select="$prefix_shelter"/>
            <xsl:for-each select="./kml:Data[@name=$L1]">
                <xsl:call-template name="detail"/>
            </xsl:for-each>
            <xsl:for-each select="./kml:Data[@name=$L2]">
                <xsl:call-template name="detail"/>
            </xsl:for-each>
            <xsl:value-of select="$separator"/>
            <xsl:for-each select="./kml:Data[@name='Name']">
                <xsl:call-template name="detail"/>
            </xsl:for-each>
        </xsl:attribute>

        <!-- Format produced by Google Fusion
        e.g. Japan feed: http://www.google.com/intl/ja/crisisresponse/japanquake2011_shelter.kmz -->
        <xsl:for-each select="./kml:Data[@name='Name']">
            <data field="name">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name='Notes']">
            <data field="comments">
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
        <xsl:for-each select="./kml:Data[@name='Source']">
            <data field="source">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <data field="L0">
            <xsl:text>Japan</xsl:text>
        </data>
        <xsl:for-each select="./kml:Data[@name=$L1]">
            <data field="L1">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name=$L2]">
            <data field="L2">
                <xsl:call-template name="detail"/>
            </data>
        </xsl:for-each>
        <xsl:for-each select="./kml:Data[@name=$L3]">
            <data field="L3">
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
            <xsl:when test="floor($x)=number($x) and $x!='-'">
                <xsl:value-of select="$x"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <!--<xsl:param name="location_name"/>-->
        <resource name="gis_location">

            <xsl:attribute name="uuid">
                <xsl:value-of select="$prefix_location"/>
                <xsl:for-each select="./kml:ExtendedData/kml:Data[@name=$L1]">
                    <xsl:call-template name="detail"/>
                </xsl:for-each>
                <xsl:for-each select="./kml:ExtendedData/kml:Data[@name=$L2]">
                    <xsl:call-template name="detail"/>
                </xsl:for-each>
                <xsl:value-of select="$separator"/>
                <xsl:for-each select="./kml:ExtendedData/kml:Data[@name='Name']">
                    <xsl:call-template name="detail"/>
                </xsl:for-each>
            </xsl:attribute>

            <data field="name">
                <xsl:for-each select="./kml:ExtendedData/kml:Data[@name='Name']">
                    <xsl:call-template name="detail"/>
                </xsl:for-each>
            </data>

            <reference field="parent" resource="gis_location">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$prefix_location"/>
                    <xsl:for-each select="./kml:ExtendedData/kml:Data[@name=$L1]">
                        <xsl:call-template name="detail"/>
                    </xsl:for-each>
                    <xsl:for-each select="./kml:ExtendedData/kml:Data[@name=$L2]">
                        <xsl:variable name="location_L2">
                            <xsl:call-template name="detail"/>
                        </xsl:variable>
                        <xsl:if test="$location_L2">
                            <xsl:value-of select="$location_L2"/>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:attribute>
            </reference>

            <!-- Handle Points -->
            <xsl:for-each select="./kml:Point">
                <xsl:call-template name="point"/>
            </xsl:for-each>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Locations Hierarchy -->
    <xsl:template name="locations">
        <resource name="gis_location" uuid="JP-青森県青森市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県弘前市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県八戸市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県黒石市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県五所川原市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県十和田市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県三沢市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県むつ市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県つがる市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県平川市"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県平内町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県今別町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県蓬田村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県外ヶ浜町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県鰺ヶ沢町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県深浦町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県西目屋村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県藤崎町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県大鰐町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県田舎館村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県板柳町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県鶴田町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県中泊町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県野辺地町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県七戸町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県六戸町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県横浜町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県東北町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県六ケ所村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県おいらせ町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県大間町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県東通村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県風間浦村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県佐井村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県三戸町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県五戸町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県田子町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県南部町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県階上町"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-青森県新郷村"><reference field="parent" resource="gis_location" uuid="JP-青森県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県盛岡市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県宮古市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県大船渡市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県花巻市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県北上市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県久慈市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県遠野市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県一関市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県陸前高田市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県釜石市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県二戸市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県八幡平市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県奥州市"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県雫石町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県葛巻町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県岩手町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県滝沢村"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県紫波町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県矢巾町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県西和賀町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県金ヶ崎町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県平泉町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県藤沢町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県住田町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県大槌町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県山田町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県岩泉町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県田野畑村"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県普代村"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県川井村"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県軽米町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県野田村"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県九戸村"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県洋野町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-岩手県一戸町"><reference field="parent" resource="gis_location" uuid="JP-岩手県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県仙台市青葉区"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県仙台市宮城野区"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県仙台市若林区"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県仙台市太白区"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県仙台市泉区"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県石巻市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県塩竃市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県気仙沼市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県白石市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県名取市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県角田市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県多賀城市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県岩沼市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県登米市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県栗原市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県東松島市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県大崎市"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県蔵王町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県七ケ宿町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県大河原町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県村田町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県柴田町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県川崎町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県丸森町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県亘理町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県山元町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県松島町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県七ケ浜町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県利府町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県大和町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県大郷町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県富谷町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県大衡村"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県色麻町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県加美町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県涌谷町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県美里町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県女川町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県本吉町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-宮城県南三陸町"><reference field="parent" resource="gis_location" uuid="JP-宮城県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県秋田市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県能代市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県横手市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県大館市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県男鹿市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県湯沢市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県鹿角市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県由利本荘市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県潟上市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県大仙市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県北秋田市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県にかほ市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県仙北市"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県小坂町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県上小阿仁村"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県藤里町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県三種町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県八峰町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県五城目町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県八郎潟町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県井川町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県大潟村"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県美郷町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県羽後町"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-秋田県東成瀬村"><reference field="parent" resource="gis_location" uuid="JP-秋田県"/></resource>
        <resource name="gis_location" uuid="JP-山形県山形市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県米沢市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県鶴岡市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県酒田市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県新庄市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県寒河江市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県上山市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県村山市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県長井市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県天童市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県東根市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県尾花沢市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県南陽市"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県山辺町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県中山町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県河北町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県西川町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県朝日町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県大江町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県大石田町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県金山町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県最上町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県舟形町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県真室川町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県大蔵村"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県鮭川村"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県戸沢村"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県高畠町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県川西町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県小国町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県白鷹町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県飯豊町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県三川町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県庄内町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-山形県遊佐町"><reference field="parent" resource="gis_location" uuid="JP-山形県"/></resource>
        <resource name="gis_location" uuid="JP-福島県福島市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県会津若松市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県郡山市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県いわき市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県白河市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県須賀川市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県喜多方市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県相馬市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県二本松市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県田村市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県南相馬市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県伊達市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県本宮市"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県桑折町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県国見町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県川俣町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県大玉村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県鏡石町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県天栄村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県下郷町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県檜枝岐村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県只見町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県南会津町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県北塩原村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県西会津町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県磐梯町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県猪苗代町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県会津坂下町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県湯川村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県柳津町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県三島町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県金山町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県昭和村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県会津美里町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県西郷村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県泉崎村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県中島村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県矢吹町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県棚倉町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県矢祭町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県塙町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県鮫川村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県石川町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県玉川村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県平田村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県浅川町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県古殿町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県三春町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県小野町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県広野町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県楢葉町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県富岡町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県川内村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県大熊町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県双葉町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県浪江町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県葛尾村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県新地町"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-福島県飯舘村"><reference field="parent" resource="gis_location" uuid="JP-福島県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県水戸市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県日立市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県土浦市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県古河市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県石岡市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県結城市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県龍ケ崎市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県下妻市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県常総市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県常陸太田市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県高萩市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県北茨城市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県笠間市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県取手市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県牛久市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県つくば市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県ひたちなか市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県鹿嶋市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県潮来市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県守谷市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県常陸大宮市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県那珂市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県筑西市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県坂東市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県稲敷市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県かすみがうら市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県桜川市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県神栖市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県行方市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県鉾田市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県つくばみらい市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県小美玉市"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県茨城町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県大洗町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県城里町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県東海村"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県大子町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県美浦村"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県阿見町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県河内町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県八千代町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県五霞町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県境町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-茨城県利根町"><reference field="parent" resource="gis_location" uuid="JP-茨城県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県宇都宮市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県足利市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県栃木市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県佐野市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県鹿沼市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県日光市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県小山市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県真岡市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県大田原市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県矢板市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県那須塩原市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県さくら市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県那須烏山市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県下野市"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県上三川町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県西方町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県益子町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県茂木町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県市貝町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県芳賀町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県壬生町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県野木町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県大平町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県藤岡町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県岩舟町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県都賀町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県塩谷町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県高根沢町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県那須町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-栃木県那珂川町"><reference field="parent" resource="gis_location" uuid="JP-栃木県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市北区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市東区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市中央区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市江南区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市秋葉区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市南区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市西区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新潟市西蒲区"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県長岡市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県三条市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県柏崎市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県新発田市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県小千谷市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県加茂市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県十日町市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県見附市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県村上市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県燕市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県糸魚川市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県妙高市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県五泉市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県上越市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県阿賀野市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県佐渡市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県魚沼市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県南魚沼市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県胎内市"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県聖籠町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県弥彦村"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県田上町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県阿賀町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県出雲崎町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県川口町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県湯沢町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県津南町"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県刈羽村"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県関川村"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-新潟県粟島浦村"><reference field="parent" resource="gis_location" uuid="JP-新潟県"/></resource>
        <resource name="gis_location" uuid="JP-長野県長野市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県松本市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県上田市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県岡谷市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県飯田市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県諏訪市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県須坂市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県小諸市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県伊那市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県駒ヶ根市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県中野市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県大町市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県飯山市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県茅野市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県塩尻市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県佐久市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県千曲市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県東御市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県安曇野市"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県小海町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県川上村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県南牧村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県南相木村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県北相木村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県佐久穂町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県軽井沢町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県御代田町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県立科町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県青木村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県長和町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県下諏訪町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県富士見町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県原村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県辰野町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県箕輪町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県飯島町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県南箕輪村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県中川村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県宮田村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県松川町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県高森町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県阿南町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県阿智村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県平谷村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県根羽村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県下條村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県売木村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県天龍村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県泰阜村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県喬木村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県豊丘村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県大鹿村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県上松町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県南木曽町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県木祖村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県王滝村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県大桑村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県木曽町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県麻績村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県生坂村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県波田町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県山形村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県朝日村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県筑北村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県池田町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県松川村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県白馬村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県小谷村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県坂城町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県小布施町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県高山村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県山ノ内町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県木島平村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県野沢温泉村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県信州新町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県信濃町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県小川村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県中条村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県飯綱町"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-長野県栄村"><reference field="parent" resource="gis_location" uuid="JP-長野県"/></resource>
        <resource name="gis_location" uuid="JP-青森県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-岩手県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-宮城県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-秋田県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-山形県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-福島県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-茨城県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-栃木県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-新潟県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="JP-長野県"><reference field="parent" resource="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"/></resource>
        <resource name="gis_location" uuid="www.sahanafoundation.org/COUNTRY-JP"></resource>
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

</xsl:stylesheet>
