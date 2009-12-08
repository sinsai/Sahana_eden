<xsl:stylesheet version="1.0"
  xmlns="http://www.opengis.net/kml/2.2"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
<xsl:output method="xml" indent="yes"/>
<xsl:template match="/">
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
	<xsl:apply-templates select="sahanapy"/>
  </Document>
  </kml>
</xsl:template>

<xsl:template match="sahanapy">
  <Folder>
	<name>SahanaPy GIS Features</name>
	<xsl:apply-templates select="resource"/>
  </Folder>
</xsl:template>

<xsl:template match="resource">
  <Placemark>
	<name><xsl:value-of select="data[@field='name']"/></name>
	<description><xsl:value-of select="@url"/></description>
	<Point>
	  <coordinates><xsl:value-of select="data[@field='lon']"/>,<xsl:value-of select="data[@field='lat']"/></coordinates>
	</Point>
  </Placemark>
</xsl:template>
</xsl:stylesheet>