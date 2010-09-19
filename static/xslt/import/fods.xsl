<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">

    <!-- **********************************************************************

         Simple Import Stylesheet for
         OpenOffice Spreadsheets in flat ODF-XML format (.fods)

         Sheet name = resource name
         First row = attribute/field names
         Other rows = attribute/field values

         Version 0.1 / 2010-09-19 / by nursix

         Copyright (c) 2010 Sahana Software Foundation

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

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xrc>
            <xsl:apply-templates select="//office:spreadsheet"/>
        </s3xrc>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="office:spreadsheet">
        <xsl:apply-templates select="./table:table"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Tables -->
    <xsl:template match="table:table">
        <xsl:apply-templates select="./table:table-row[position()>1]"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Rows -->
    <xsl:template match="table:table-row">
        <xsl:variable name="resource_name" select="../@table:name"/>
        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$resource_name"/>
            </xsl:attribute>
            <xsl:apply-templates select="./table:table-cell" mode="attributes"/>
            <xsl:apply-templates select="./table:table-cell" mode="fields"/>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Attribute cells -->
    <xsl:template match="table:table-cell" mode="attributes">
        <xsl:variable name="fieldindex" select="position()"/>
        <xsl:variable name="fieldname" select="../../table:table-row[1]/table:table-cell[$fieldindex]/text:p/text()"/>
        <xsl:if test="$fieldname='uuid'">
            <xsl:attribute name="uuid">
                <xsl:value-of select="./text:p/text()"/>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Field cells -->
    <xsl:template match="table:table-cell" mode="fields">
        <xsl:variable name="fieldindex" select="position()"/>
        <xsl:variable name="fieldname" select="../../table:table-row[1]/table:table-cell[$fieldindex]/text:p/text()"/>
        <xsl:if test="$fieldname!='uuid'">
            <data>
                <xsl:attribute name="field">
                    <xsl:value-of select="$fieldname"/>
                </xsl:attribute>
                <xsl:value-of select="./text:p/text()"/>
            </data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
