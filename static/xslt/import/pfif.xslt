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
        <sahanapy-do-not-import> <!-- change this tag to activate -->
            <xsl:apply-templates select="./pfif:person"/>
        </sahanapy-do-not-import>
    </xsl:template>

    <!-- pfif:person -->
    <xsl:template match="pfif:person">
        <resource prefix="pr" name="person">
            <xsl:choose>
                <xsl:when test="contains(./pfif:person_record_id/text(),'/')">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="substring-after(./pfif:person_record_id/text(),'/')"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="./pfif:person_record_id/text()"/>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates select="./pfif:note"/>
        </resource>
    </xsl:template>

    <!-- pfif:note -->
    <xsl:template match="pfif:note">
        <resource prefix="pr" name="presence">
        </resource>
    </xsl:template>

    <!-- Tools -->
    <xsl:template name="pfif2datetime">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, 'T'), ' ', substring-before(substring-after($datetime, 'T'), 'Z'))"/>
    </xsl:template>

</xsl:stylesheet>
