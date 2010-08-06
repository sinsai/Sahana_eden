<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

  <xsl:variable name="outermostElementName" select="name(/*)" />
  
  <xsl:template match="/*">
  <s3xrc>
   <resource                                                                       
      name="{$outermostElementName}" />                                    
      <xsl:for-each select="child::*">
      
      <data field="{name(.)}"><xsl:value-of select="."/></data>
      </xsl:for-each>
   
      
  </s3xrc>
  </xsl:template>
</xsl:stylesheet>