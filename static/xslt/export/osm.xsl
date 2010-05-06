<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns="http://openstreetmap.org/osm/0.6">

    <!-- Sahana Eden XSLT Export Template

        Transformation of
            Sahana Eden GIS Locations
        into
            OpenStreetMap Points of Interest
    -->

    <xsl:output method="xml"/>

    <xsl:template match="/">
        <osm>
            <xsl:attribute name="version">0.6</xsl:attribute>
            <xsl:attribute name="generator">Sahana Eden</xsl:attribute>
            
            <xsl:apply-templates select="./s3xrc"/>
    
        </osm>
    </xsl:template>

    <xsl:template match="s3xrc">
    
        <xsl:variable name="domain" select="@domain" />
    
        <bounds>
            <xsl:attribute name="minlat"><xsl:value-of select="@latmin"/></xsl:attribute>
            <xsl:attribute name="minlon"><xsl:value-of select="@lonmin"/></xsl:attribute>
            <xsl:attribute name="maxlat"><xsl:value-of select="@latmax"/></xsl:attribute>
            <xsl:attribute name="maxlon"><xsl:value-of select="@lonmax"/></xsl:attribute>
        </bounds>
            
        <xsl:for-each select="//resource" >
        
            <xsl:choose>
                <xsl:when test="@name='gis_location'">

                    <xsl:if test="./data[@field='lat'] and ./data[@field='lon']">
                        <node>
                            <xsl:variable name="id" select='position()' />
                            <xsl:attribute name="id">
                                <xsl:text>-</xsl:text>
                                <xsl:value-of select="$id" />
                            </xsl:attribute>
                            
                            <xsl:attribute name="lat"><xsl:value-of select="./data[@field='lat']"/></xsl:attribute>
                            <xsl:attribute name="lon"><xsl:value-of select="./data[@field='lon']"/></xsl:attribute>
                            
                            <tag>
                                <xsl:attribute name="k">uuid</xsl:attribute>
                                <xsl:attribute name="v">
                                    <xsl:value-of select="$domain"/>
                                    <xsl:text>/</xsl:text>
                                    <xsl:value-of select="@uuid"/>
                                </xsl:attribute>
                            </tag>
                            
                            <tag>
                                <xsl:attribute name="k">name</xsl:attribute>
                                <xsl:attribute name="v"><xsl:value-of select="./data[@field='name']"/></xsl:attribute>
                            </tag>
                            
                            <tag>
                                <xsl:choose>
                                    <xsl:when test="reference[@field='feature_class_id']='Town'">
                                        <xsl:attribute name="k">place</xsl:attribute>
                                        <xsl:attribute name="v">town</xsl:attribute>
                                    </xsl:when>
                                    <xsl:when test="reference[@field='feature_class_id']='Airport'">
                                        <xsl:attribute name="k">aeroway</xsl:attribute>
                                        <xsl:attribute name="v">aerodrome</xsl:attribute>
                                    </xsl:when>
                                    <xsl:when test="reference[@field='feature_class_id']='Bridge'">
                                        <xsl:attribute name="k">highway</xsl:attribute>
                                        <xsl:attribute name="v">road</xsl:attribute>
                                        <xsl:attribute name="k">bridge</xsl:attribute>
                                        <xsl:attribute name="v">yes</xsl:attribute>
                                    </xsl:when>
                                    <xsl:when test="reference[@field='feature_class_id']='Hospital'">
                                        <xsl:attribute name="k">amenity</xsl:attribute>
                                        <xsl:attribute name="v">hospital</xsl:attribute>
                                    </xsl:when>
                                    <xsl:when test="reference[@field='feature_class_id']='Church'">
                                        <xsl:attribute name="k">amenity</xsl:attribute>
                                        <xsl:attribute name="v">place_of_worship</xsl:attribute>
                                    </xsl:when>
                                    <xsl:when test="reference[@field='feature_class_id']='School'">
                                        <xsl:attribute name="k">amenity</xsl:attribute>
                                        <xsl:attribute name="v">school</xsl:attribute>
                                    </xsl:when>
                                </xsl:choose>
                            </tag>

                        </node>
                    </xsl:if>
                    
                </xsl:when>
                
                <xsl:otherwise>

                    <xsl:if test="./reference[@resource='gis_location']">
                        <node>
                            <xsl:variable name="id" select='position()' />
                            <xsl:attribute name="id">
                                <xsl:text>-</xsl:text>
                                <xsl:value-of select="$id" />
                            </xsl:attribute>
                            
                            <xsl:attribute name="lat"><xsl:value-of select="reference[@field='location_id']/@lat"/></xsl:attribute>
                            <xsl:attribute name="lon"><xsl:value-of select="reference[@field='location_id']/@lon"/></xsl:attribute>
                            
                            <tag>
                                <xsl:attribute name="k">uuid</xsl:attribute>
                                <xsl:attribute name="v">
                                    <xsl:value-of select="$domain"/>
                                    <xsl:text>/</xsl:text>
                                    <xsl:value-of select="@uuid"/>
                                </xsl:attribute>
                            </tag>
                            
                            <tag>
                                <xsl:attribute name="k">name</xsl:attribute>
                                <xsl:attribute name="v"><xsl:value-of select="./data[@field='name']"/></xsl:attribute>
                            </tag>
                            
                            <tag>
                                <xsl:choose>
                                    <xsl:when test="@name='hms_hospital'">
                                        <xsl:attribute name="k">amenity</xsl:attribute>
                                        <xsl:attribute name="v">hospital</xsl:attribute>
                                    </xsl:when>
                                </xsl:choose>
                            </tag>
                            
                        </node>
                    </xsl:if>

                </xsl:otherwise>
                
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>
