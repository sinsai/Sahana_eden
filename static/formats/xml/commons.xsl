<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Common templates

         include into other stylesheets with:
             <xsl:include href="../xml/commons.xsl"/>

         Copyright (c) 2010-11 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    -->

    <!-- ****************************************************************** -->
    <!-- Convert ISO8601 datetime YYYY-MM-DDTHH:mm:ssZ into internal format -->

    <xsl:template name="iso2datetime">
        <xsl:param name="datetime"/>
        <xsl:variable name="date" select="substring-before($datetime, 'T')"/>
        <xsl:variable name="time" select="substring-before(substring-after($datetime, 'T'), 'Z')"/>
        <xsl:choose>
            <xsl:when test="contains($time, '.')">
                <xsl:value-of select="concat($date, ' ', substring-before($time, '.'))"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat($date, ' ', $time)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Convert internal format datetime into ISO8601 YYYY-MM-DDTHH:mm:ssZ -->

    <xsl:template name="datetime2iso">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, ' '), 'T', substring-after($datetime, ' '), 'Z')"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Convert a string to uppercase -->
    <xsl:template name="uppercase">
        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ')"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Convert a string to lowercase -->
    <xsl:template name="lowercase">
        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ',
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø')"/>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
