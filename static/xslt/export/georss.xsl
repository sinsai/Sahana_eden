<xsl:stylesheet version="1.0"
  xmlns="http://www.w3.org/2005/Atom"
  xmlns:georss="http://www.georss.org/georss"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
<xsl:output method="xml" indent="yes"/>
<xsl:template match="/sahanapy">
  <feed xmlns="http://www.w3.org/2005/Atom" xmlns:georss="http://www.georss.org/georss">
	<title>SahanaPy GIS Features</title>
	<link href="{@url}"/>
	<xsl:apply-templates select="resource"/>
  </feed>
</xsl:template>
<xsl:template match="resource">
  <entry>
    <title><xsl:value-of select="data[@field='name']"/></title>
    <link href="{@url}"/>
    <id><xsl:value-of select="@uuid"/></id>
    <georss:point><xsl:value-of select="data[@field='lat']"/> <xsl:value-of select="data[@field='lon']"/></georss:point>
  </entry>
</xsl:template>
</xsl:stylesheet>