<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.1">

    <xsl:output method="xml"/>

    <!-- SahanaPy PFIF Export Template -->
    <!-- Version 0.1 / 2009-10-04 / by nursix -->

    <!-- work in progress: this template is still incomplete -->

    <xsl:template match="/">
        <xsl:apply-templates select="./sahanapy"/>
    </xsl:template>

    <xsl:template match="/sahanapy">
        <pfif:pfif>
            <xsl:apply-templates select="./resource[@name='pr_person']"/>
        </pfif:pfif>
    </xsl:template>

    <!-- Person -->
    <xsl:template match="resource[@name='pr_person']">
        <pfif:person>
            <pfif:person_record_id>
                <xsl:value-of select="concat(/sahanapy/@domain, '/', ./@uuid)" />
            </pfif:person_record_id>
            <pfif:entry_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./@modified_on" />
                </xsl:call-template>
            </pfif:entry_date>
            <pfif:author_name>
                <xsl:value-of select="./@modified_by" />
            </pfif:author_name>
            <pfif:source_name>
                <xsl:value-of select="/sahanapy/@domain"/>
            </pfif:source_name>
            <pfif:source_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./@created_on" />
                </xsl:call-template>
            </pfif:source_date>
            <pfif:source_url>
                <xsl:value-of select="./@url"/>
            </pfif:source_url>
            <pfif:first_name>
                <xsl:call-template name="name2pfif">
                    <xsl:with-param name="name" select="./data[@field='first_name']/text()" />
                </xsl:call-template>
            </pfif:first_name>
            <pfif:last_name>
                <xsl:call-template name="name2pfif">
                    <xsl:with-param name="name" select="./data[@field='last_name']/text()" />
                </xsl:call-template>
            </pfif:last_name>
            <xsl:apply-templates select="./resource[@name='pr_address' and ./data[@field='opt_pr_address_type']/@value=1][1]" />
            <xsl:apply-templates select="./resource[@name='pr_presence']"/>
        </pfif:person>
    </xsl:template>

    <!-- Presence -->
    <xsl:template match="resource[@name='pr_presence']">
        <pfif:note>
            <pfif:note_record_id>
                <xsl:value-of select="concat(/sahanapy/@domain, '/', ./@uuid)" />
            </pfif:note_record_id>
            <pfif:entry_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./data[@field='time']/@value" />
                </xsl:call-template>
            </pfif:entry_date>
            <pfif:author_name>
                <xsl:value-of select="./reference[@field='reporter']/text()" />
            </pfif:author_name>
            <pfif:source_date>
                <xsl:call-template name="datetime2pfif">
                    <xsl:with-param name="datetime" select="./@created_on" />
                </xsl:call-template>
            </pfif:source_date>
            <pfif:found>
                <xsl:choose>
                    <xsl:when test="./data[@field='opt_pr_presence_condition']/@value=8">
                        <xsl:text>false</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>true</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </pfif:found>
            <pfif:last_known_location>
                <xsl:if test="./data[@field='location']/text()">
                    <xsl:value-of select="./data[@field='location']/text()"/>
                    <xsl:if test="string-length(./data[@field='location_details']/text())&gt;0">
                        <xsl:text> / </xsl:text>
                    </xsl:if>
                </xsl:if>
                <xsl:if test="string-length(./data[@field='location_details']/text())&gt;0">
                    <xsl:value-of select="./data[@field='location_details']/text()"/>
                </xsl:if>
            </pfif:last_known_location>
            <pfif:text>
                <xsl:value-of select="./data[@field='opt_pr_presence_condition']/text()"/>
                <xsl:if test="string-length(./data[@field='procedure']/text())&gt;0">
                    <xsl:text>: </xsl:text>
                    <xsl:value-of select="./data[@field='procedure']/text()"/>
                </xsl:if>
                <xsl:if test="string-length(./data[@field='comment']/text())&gt;0">
                    <xsl:text>- </xsl:text>
                    <xsl:value-of select="./data[@field='comment']/text()"/>
                </xsl:if>
            </pfif:text>
        </pfif:note>
    </xsl:template>

    <!-- Address -->
    <xsl:template match="resource[@prefix='pr' and @name='person']/resource[@prefix='pr' and @name='address']">
        <pfif:home_city>
            <xsl:call-template name="name2pfif">
                <xsl:with-param name="name" select="./data[@field='city']/text()"/>
            </xsl:call-template>
        </pfif:home_city>
        <pfif:home_state>
            <xsl:call-template name="name2pfif">
                <xsl:with-param name="name" select="./data[@field='state']/text()" />
            </xsl:call-template>
        </pfif:home_state>
        <pfif:home_street>
            <xsl:call-template name="name2pfif">
                <xsl:with-param name="name" select="./data[@field='street1']/text()" />
            </xsl:call-template>
        </pfif:home_street>
        <pfif:home_zip>
            <xsl:value-of select="./data[@field='postcode']/text()"/>
        </pfif:home_zip>
    </xsl:template>

    <!-- Helper Templates -->
    <xsl:template name="datetime2pfif">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, ' '), 'T', substring-after($datetime, ' '), 'Z')"/>
    </xsl:template>

    <xsl:template name="name2pfif">
        <xsl:param name="name"/>
        <xsl:value-of select="translate($name,
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ')"/>
    </xsl:template>

</xsl:stylesheet>
