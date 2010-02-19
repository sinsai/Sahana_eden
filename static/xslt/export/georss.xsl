<xsl:stylesheet version="1.0"
  xmlns="http://www.w3.org/2005/Atom"
  xmlns:georss="http://www.georss.org/georss"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/s3xrc">
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:georss="http://www.georss.org/georss">
            <title>SahanaPy GIS Features</title>
            <link href="{@url}"/>
            <xsl:apply-templates select="resource"/>
        </feed>
    </xsl:template>

    <xsl:template match="resource">
        <xsl:choose>
            <xsl:when test="@name='gis_location'">
                <entry>
                    <title><xsl:value-of select="data[@field='name']"/></title>
                    <link href="{@url}"/>
                    <id><xsl:value-of select="@uuid"/></id>
                    <georss:point>
                        <xsl:value-of select="data[@field='lat']"/>
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="data[@field='lon']"/>
                    </georss:point>
                </entry>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="./reference[@field='location_id']">
                    <entry>
                        <title><xsl:value-of select="data[@field='name']"/></title>
                        <link href="{@url}"/>
                        <id><xsl:value-of select="@uuid"/></id>
                        <georss:point>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                            <xsl:text> </xsl:text>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                        </georss:point>
                    </entry>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
