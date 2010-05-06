<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- Sahana Eden XSLT Export Template

        Transformation of
            Sahana Eden GIS Location
        into
            GeoJSON: http://geojson.org
            
        v0.1 POINT support
    -->
    
    <xsl:output method="xml"/>
    
    <xsl:template match="/">
        <type>FeatureCollection</type>
        <features>
            <xsl:apply-templates select="s3xrc"/>
        </features>
    </xsl:template>
    
    <xsl:template match="s3xrc">
        <xsl:apply-templates select="./resource"/>
    </xsl:template>
    
    <xsl:template match="resource">
        <xsl:choose>
            <xsl:when test="@name='gis_location'">
                <type>Feature</type>
                <id>
                    <xsl:value-of select="@uuid"/>
                </id>
                <geometry>
                    <type>
                        <xsl:value-of select="data[@field='gis_feature_type']"/>
                    </type>
                    <coordinates>
                        <xsl:choose>
                            <xsl:when test="data[@field='gis_feature_type']='Point'">
                                <xsl:text>[</xsl:text>
                                <xsl:value-of select="data[@field='lat']"/>
                                <xsl:text>, </xsl:text>
                                <xsl:value-of select="data[@field='lon']"/>
                                <xsl:text>]</xsl:text>
                            </xsl:when>
                        </xsl:choose>
                    </coordinates>
                </geometry>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
</xsl:stylesheet>
