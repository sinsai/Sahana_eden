<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.1">

    <xsl:output method="xml"/>
    <xsl:param name="domain"/>

    <!-- SahanaPy PFIF Import Template -->
    <!-- Version 0.1 / 2009-10-05 / by nursix -->

    <!-- work in progress: this template is still incomplete (and therefore deactivated) -->

    <xsl:template match="/">
        <xsl:apply-templates select="pfif:pfif"/>
    </xsl:template>

    <xsl:template match="pfif:pfif">
        <sahanapy>
            <xsl:attribute name="domain">
                <xsl:value-of select="$domain"/>
            </xsl:attribute>
            <xsl:apply-templates select="./pfif:person"/>
        </sahanapy>
    </xsl:template>

    <xsl:template match="pfif:person">
        <xsl:if test="./pfif:person_record_id/text()">
            <xsl:variable name="uuid">
                <xsl:choose>
                    <xsl:when test="starts-with(./pfif:person_record_id/text(), concat($domain, '/'))">
                        <xsl:value-of select="substring-after(./pfif:person_record_id/text(), '/')"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="./pfif:person_record_id/text()"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <resource name="pr_person">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:attribute>
                <data field="last_name">
                    <xsl:value-of select="./pfif:last_name/text()"/>
                </data>
                <data field="first_name">
                    <xsl:value-of select="./pfif:first_name/text()"/>
                </data>
                <xsl:if test="./pfif:home_city">
                    <resource name="pr_address">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="concat($uuid, '_address')"/>
                        </xsl:attribute>
                        <data field="opt_pr_address_type" value="1">Home Address</data>
                        <data field="street1">
                            <xsl:value-of select="./pfif:home_street/text()"/>
                        </data>
                        <data field="street2">
                            <xsl:value-of select="./pfif:home_neighborhood/text()"/>
                        </data>
                        <data field="postcode">
                            <xsl:value-of select="./pfif:home_zip/text()"/>
                        </data>
                        <data field="city">
                            <xsl:value-of select="./pfif:home_city/text()"/>
                        </data>
                        <data field="state">
                            <xsl:value-of select="./pfif:home_state/text()"/>
                        </data>
                    </resource>
                </xsl:if>
                <xsl:if test="./pfif:photo_url">
                    <resource name="pr_image">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="concat($uuid, '_photo')"/>
                        </xsl:attribute>
                        <data field="opt_pr_image_type" value="1">Photograph</data>
                        <data field="title">Photograph</data>
                        <data field="description">external data source</data>
                        <data field="image"/>
                        <data field="url">
                            <xsl:value-of select="./pfif:photo_url/text()"/>
                        </data>
                    </resource>
                </xsl:if>
                <xsl:apply-templates select="./pfif:note"/>
            </resource>
        </xsl:if>
    </xsl:template>

    <xsl:template match="pfif:note">
        <resource name="pr_presence">
            <xsl:choose>
                <xsl:when test="starts-with(./pfif:note_record_id/text(), concat($domain, '/'))">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="substring-after(./pfif:note_record_id/text(), '/')"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="./pfif:note_record_id/text()"/>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="normalize-space(./pfif:found/text())='false'">
                    <data field="opt_pr_presence_condition">
                        <xsl:attribute name="value">8</xsl:attribute>
                        <xsl:text>Missing</xsl:text>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="opt_pr_presence_condition">
                        <xsl:attribute name="value">4</xsl:attribute>
                        <xsl:text>Found</xsl:text>
                    </data>
                </xsl:otherwise>
            </xsl:choose>
            <data field="time">
                <xsl:call-template name="pfif2datetime">
                    <xsl:with-param name="datetime" select="./pfif:source_date/text()"/>
                </xsl:call-template>
            </data>
            <data field="location_details">
                <xsl:value-of select="./pfif:last_known_location/text()"/>
            </data>
            <data field="proc_desc">
                <xsl:value-of select="./pfif:text/text()"/>
            </data>
            <data field="comment">
                <xsl:value-of select="concat(./pfif:author_name/text(), ' - ', ./pfif:author_email/text(), ' - ', ./pfif:author_phone/text())"/>
            </data>
        </resource>
    </xsl:template>

    <!-- Tools -->
    <xsl:template name="pfif2datetime">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, 'T'),' ',substring-before(substring-after($datetime, 'T'), 'Z'))"/>
    </xsl:template>

</xsl:stylesheet>

