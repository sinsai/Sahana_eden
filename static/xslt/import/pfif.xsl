<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.1">

    <xsl:output method="xml"/>

    <!-- SahanaPy PFIF Import Template -->
    <!-- Version 0.1 / 2009-10-05 / by nursix -->

    <!-- work in progress: this template is still incomplete (and therefore deactivated) -->

    <xsl:template match="/">
        <xsl:apply-templates select="./pfif:pfif"/>
    </xsl:template>

    <xsl:template match="/pfif:pfif">
            <xsl:apply-templates select="./person"/>
    </xsl:template>

    <!-- pfif:person -->
    <xsl:template match="person">
        <resource name="pr_person">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="./person_record_id/text()"/>
                    </xsl:attribute>
                    <xsl:attribute name="created_on">
                        <xsl:call-template name="pfif2datetime">
			  <xsl:with-param name="datetime" select="./entry_date" />
			</xsl:call-template>
                    </xsl:attribute>
                    <data field="last_name">
                        <xsl:value-of select="./last_name/text()"/>
                    </data>
                    <data field="first_name">
                        <xsl:value-of select="./first_name/text()"/>
                    </data>
                    <!--Put in the author details in one copy of pr_presence here -->
                  <resource name="pr_presence">
                  <data>
                    <xsl:choose>
			<xsl:when test="normalize-space(./found)='false'">
			    <xsl:attribute name="field">opt_pr_presence_condition</xsl:attribute>
			    <xsl:attribute name="value">8</xsl:attribute>
			    <xsl:text>Missing</xsl:text>
			</xsl:when>
			<xsl:otherwise>
<!-- 			change this -->
			  <xsl:text>true</xsl:text>
			</xsl:otherwise>
		    </xsl:choose>
		    </data>
		  </resource>
		  <resource name="pr_address">
		   <data field="city">
                        <xsl:value-of select="./home_city/text()"/>
                    </data>
		   <data field="state">
                        <xsl:value-of select="./home_state/text()"/>
                    </data>            
		   <data field="street1">
                        <xsl:value-of select="./home_street/text()"/>
                    </data>                          
                    <!-- Mapping home_neighborhood as street2 -->
		   <data field="street2">
                        <xsl:value-of select="./home_neighborhood/text()"/>
                    </data>      
		   <data field="postcode">
                        <xsl:value-of select="./home_zip/text()"/>
                    </data>    
		   </resource>
            <xsl:apply-templates select="./note"/>
        </resource>
    </xsl:template>

    <!-- pfif:note -->
    <xsl:template match="note">
        <resource name="pr_presence">
        </resource>
    </xsl:template>

    <!-- Tools -->
    <xsl:template name="pfif2datetime">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, 'T'), ' ', substring-before(substring-after($datetime, 'T'), ':'),':',substring(substring-after(substring-after($datetime, 'T'), ':'),1,2),':',substring(substring-after(substring-after($datetime, 'T'), ':'),3,4)  )"/>
    </xsl:template>

</xsl:stylesheet>

