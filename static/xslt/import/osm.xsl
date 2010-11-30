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

    <xsl:template match="/">
        <xsl:apply-templates select="./osm"/>
    </xsl:template>

    <xsl:template match="osm">
        <s3xrc>
            <!--
                Handle simple Nodes (minority case)
            -->
            <xsl:for-each select="//node" >
                <xsl:choose>

                    <!-- Hospitals -->
                    <!--
                        @ToDo: Catch:
                            Clinics (http://wiki.openstreetmap.org/wiki/Proposed_features/Clinic_%28Medical%29)
                            & Pharmacies (http://wiki.openstreetmap.org/wiki/Tag:amenity%3Dpharmacy)
                    -->
                    <xsl:when test="./tag[@k='amenity'] and ./tag[@v='hospital']">
                        <resource name="hms_hospital">

                            <xsl:attribute name="uuid">
                                <xsl:text>openstreetmap.org/</xsl:text>
                                <xsl:value-of select="@id"/>
                            </xsl:attribute>

                            <xsl:attribute name="modified_on">
                                <xsl:value-of select="@timestamp"/>
                            </xsl:attribute>

                            <!-- Main Record -->
                            <xsl:if test="./tag[@k='name']">
                                <data field="name">
                                    <xsl:value-of select="./tag[@k='name']/@v"/>
                                </data>
                            </xsl:if>

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
                                <resource name="gis_location">

                                    <xsl:if test="./tag[@k='name']">
                                        <data field="name">
                                            <xsl:value-of select="./tag[@k='name']/@v"/>
                                        </data>
                                    </xsl:if>

                                    <data field="gis_feature_type" value="1">Point</data>

                                    <data field="lat">
                                        <xsl:value-of select="@lat"/>
                                    </data>
                                    <data field="lon">
                                        <xsl:value-of select="@lon"/>
                                    </data>
                                    
                                    <data field="osm_id">
                                        <xsl:value-of select="@id"/>
                                    </data>

                                </resource>
                            </reference>

                        </resource>
                    </xsl:when>
                    
                    <!-- Places -->
                    <xsl:when test="./tag[@k='place']">
                        <resource name="gis_location">
                            
                            <xsl:attribute name="uuid">
                                <xsl:text>openstreetmap.org/</xsl:text>
                                <xsl:value-of select="@id"/>
                            </xsl:attribute>

                            <xsl:attribute name="modified_on">
                                <xsl:value-of select="@timestamp"/>
                            </xsl:attribute>

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

                            <data field="gis_feature_type" value="1">Point</data>

                            <data field="lat">
                                <xsl:value-of select="@lat"/>
                            </data>
                            <data field="lon">
                                <xsl:value-of select="@lon"/>
                            </data>

                            <!-- @ToDo: Support Is-In
                            <data field="parent">
                                <xsl:value-of select=""/>
                            </data>
                            -->

                        </resource>
                    </xsl:when>

                    <!-- @ToDo: Landmarks -->
                    <!--
                    <xsl:when test="./tag[@k='aeroway'] and ./tag[@v='aerodrome']">
                        <reference field="feature_class_id" resource="gis_feature_class">Airport</reference>
                    </xsl:when>
                    <xsl:when test="./tag[@k='amenity'] and ./tag[@v='place_of_worship']">
                        <reference field="feature_class_id" resource="gis_feature_class">Church</reference>
                    </xsl:when>
                    <xsl:when test="./tag[@k='amenity'] and ./tag[@v='school']">
                        <reference field="feature_class_id" resource="gis_feature_class">School</reference>
                    </xsl:when>
                    <xsl:when test="./tag[@k='bridge'] and ./tag[@v='yes']">
                        <reference field="feature_class_id" resource="gis_feature_class">Bridge</reference>
                    </xsl:when>
                    -->

                </xsl:choose>
            </xsl:for-each>
            
            <!--
                @ToDo: Handle Ways (majority case)
                    lookup all linked nodes, create WKT & pull in as polygon
                    (centroid calculated onvalidation)
            -->
            <xsl:for-each select="//way" >
                <xsl:choose>

                    <!-- Hospitals -->
                    <!--
                        @ToDo: Catch:
                            Clinics (http://wiki.openstreetmap.org/wiki/Proposed_features/Clinic_%28Medical%29)
                            & Pharmacies (http://wiki.openstreetmap.org/wiki/Tag:amenity%3Dpharmacy)
                    -->
                    <xsl:when test="./tag[@k='amenity'] and ./tag[@v='hospital']">
                        <resource name="hms_hospital">

                            <xsl:attribute name="uuid">
                                <xsl:text>openstreetmap.org/</xsl:text>
                                <xsl:value-of select="@id"/>
                            </xsl:attribute>

                            <xsl:attribute name="modified_on">
                                <xsl:value-of select="@timestamp"/>
                            </xsl:attribute>

                            <!-- Main Record -->
                            <xsl:if test="./tag[@k='name']">
                                <data field="name">
                                    <xsl:value-of select="./tag[@k='name']/@v"/>
                                </data>
                            </xsl:if>

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
                                <resource name="gis_location">

                                    <xsl:if test="./tag[@k='name']">
                                        <data field="name">
                                            <xsl:value-of select="./tag[@k='name']/@v"/>
                                        </data>
                                    </xsl:if>

                                    <data field="osm_id">
                                        <xsl:value-of select="@id"/>
                                    </data>

                                    <!-- Save as Polygon -->
                                    <data field="gis_feature_type" value="3">Polygon</data>

                                    <data field="wkt">
                                        <!-- Initialise the WKT -->
                                        <xsl:text>POLYGON((</xsl:text>
                                        
                                        <!-- Walk through the Nodes -->
                                        <xsl:for-each select="./nd" >

                                            <xsl:variable name="id" select="@ref"/>
                                            <xsl:for-each select="//node[@id=$id][1]">
                                                
                                                <!-- Append the Node's Lat/Lon to WKT -->
                                                <xsl:value-of select="@lon"/><xsl:text> </xsl:text><xsl:value-of select="@lat"/><xsl:text>,</xsl:text>
                                                
                                            </xsl:for-each>

                                        </xsl:for-each>
                                        
                                        <!-- complete the WKT -->
                                        <xsl:text>))</xsl:text>
                                    </data>

                                </resource>
                            </reference>
                        </resource>
                    </xsl:when>

                    <!--
                        @ToDo: Admin Boundaries
                            <tag k="admin_level" v="8"/>
                            <tag k="source" v="US Census Bureau"/>
                    <xsl:when test="./tag[@k='boundary'] and ./tag[@v='administrative']">
                    
                    </xsl:when>
                    -->

                </xsl:choose>
            </xsl:for-each>

            <!--
                @ToDo: Handle Relations (minority case)
                    lookup all linked ways, & hence nodes, create WKT & pull in as polygon or multipolygon
                    (centroid calculated onvalidation)
            <xsl:for-each select="//relation" >
            </xsl:for-each>
            -->

        </s3xrc>
    </xsl:template>
</xsl:stylesheet>
