# -*- coding: utf-8 -*-

""" Sahana Optical Character Recognision Utility (s3ocr)

    @author: Suryajith Chillara <suryajith1987[at]gmail.com>
    @author: Shiv Deepak <idlecool[at]gmail.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
    @license: MIT

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

"""

__all__ = ["S3OCR"]

#========================== import section ====================================

# Generic stuff
import os
import sys
import uuid
import re
from StringIO import StringIO
from htmlentitydefs import name2codepoint

from lxml import etree

# Importing reportlab stuff
try:
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.graphics.barcode import code128
    # for adding more fonts
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab
    reportlab.rl_config.warnOnMissingFontGlyphs = 0
except(ImportError):
    print >> sys.stderr, "S3 Debug: WARNING: S3OCR: reportlab has not been installed."

from s3rest import S3Method
from s3cfg import S3Config

#==========================================================================
#================================= OCR API ================================
#==========================================================================

class S3OCR(S3Method):
    """
    Generate XForms and PDFs the s3 way
    """

    def apply_method(self,
                     r,
                     **attr):
        """
        S3Method's abstract method
        """
        
        xml = self.manager.xml
        self.r = r

        # s3ocr_config - dict which stores ocr configuration
        #                            settings for a resource)
        s3ocr_config = attr.get("s3ocr_config", {})

        # storing localised names of components
        self.rheader_tabs = s3ocr_config.get("tabs", [])

        # store custom pdf title (if any)
        self.pdftitle = s3ocr_config.get("pdftitle", None)

        # store components which have to be excluded
        self.exclude_component_list = s3ocr_config.get("exclude_components", [])

        # store individual field specific properties
        self.custom_field_properties = s3ocr_config.get("field_properties", {})

        # example field_properties
        # field_properties = {
        #     "%s_%s__%s" % (prefix, resourcename, fieldname): { fieldtype="",
        #                                                        .
        #                                                        .
        #                                                        }
        #     }

        # store individual fieldtype specific properties
        s3config = S3Config(self.T)
        self.custom_fieldtype_properties = \
            s3config.get_s3ocr_fieldtype_properties()

        # example field_properties
        # field_properties = {
        #     fieldtype : { fieldtype="",
        #                   .
        #                   .
        #                   }
        #     }

        # field type convention mapping from resource to pdf forms
        self.generic_ocr_field_type = {
            "string": "string", 
            "text": "textbox", 
            "boolean" : "boolean",
            "double": "double",
            "date": "date",
            "datetime": "datetime",
            "integer": "integer",
            "list:integer": "multiselect",
            "list:string": "multiselect",
            "list:double": "multiselect",
            "list:text": "multiselect",
            }

        # text for localisation
        self.l10n = {
            "datetime_hint": {
                "date": self.T("fill in order: day(2) month(2) year(4)"),
                "datetime": self.T("fill in order: hour(2) min(2) day(2) month(2) year(4)"),
                },
            "ocr_inst": {
                "inst1": self.T("1. Fill the necessary fields in BLOCK CAPITAL letters."),
                "inst2": self.T("2. Always use one box per letter and leave one box space to separate words."),
                "inst3": self.T("3. Fill in the circles completely."),
                },
            "boolean": {
                "yes": self.T("Yes"),
                "no": self.T("No"),
                },
            "select": {
                "multiselect": self.T("Select one or more option(s) that apply"),
                "singleselect": self.T("Select any one option that apply"),
                },
            }

        # check if debug mode is enabled
        if r.request.vars.get("_debug", False) == "1":
            self.debug = True
        else:
            self.debug = False

        if self.debug:
            content_disposition = "inline"
        else:
            content_disposition = "attachment"
        
        # serve the request
        format = r.representation
        if r.http == "GET":
            if format == "xml":
                output = self.s3ocr_etree()
                self.response.view = "xml.html"
                self.response.headers["Content-Type"] = "application/xml"
                return xml.tostring(output, pretty_print=True)
            elif format == "pdf":
                output = self.pdf_manager()
                self.response.view = None
                self.response.headers["Content-Type"] = "application/pdf"
                self.response.headers["Content-disposition"] = \
                            "%s; filename=\"%s.pdf\"" % (content_disposition,
                                                         self.tablename)
                return output
            else:
                r.error(501, self.manager.ERROR.BAD_FORMAT)
        elif r.http in ("POST","PUT"):
            if format == "xml":
                r.error(501, self.manager.ERROR.NOT_IMPLEMENTED)
            elif format == "pdf":
                r.error(501, self.manager.ERROR.NOT_IMPLEMENTED)
            else:
                r.error(501, self.manager.ERROR.BAD_FORMAT)
        else:
            r.error(501, self.manager.ERROR.BAD_METHOD)

    def s3ocr_etree(self):
        """
        Optimise & Modifiy s3xml etree to and produce s3ocr etree
        """

        s3xml_etree = self.resource.struct(options=True,
                                   references=True,
                                   stylesheet=None,
                                   as_json=False,
                                   as_tree=True)
        # xml tags
        ITEXT = "label"
        HINT = "comment"
        TYPE = "type"
        HASOPTIONS = "has_options"
        LINES = "lines"
        BOXES = "boxes"

        # Components Localised Text added to the etree
        # Convering s3xml to s3ocr_xml (nicer to traverse)
        s3xml_root = s3xml_etree.getroot()
        resource_element = s3xml_root.getchildren()[0]
        s3ocr_root = etree.Element("s3ocr")

        if self.r.component:     # if it is a component
            component_sequence, components_l10n_dict = \
                self.__rheader_tabs_sequence(self.r.tablename)
            resource_element.set(ITEXT,
                                 components_l10n_dict.get(None,
                                                          self.resource.tablename))
            s3ocr_root.append(resource_element)

        else:                    # if it is main resource
            componentetrees = []
            # mres is main resource etree
            mres = etree.Element("resource")
            for attr in resource_element.attrib.keys():
                mres.set(attr, resource_element.attrib.get(attr))
            for field_element in resource_element:
                if field_element.tag == "field":       # main resource fields
                    mres.append(field_element)
                elif field_element.tag == "resource":  # component resource
                    componentetrees.append(field_element)

            # Serialisation of Component List and l10n
            component_sequence, components_l10n_dict = \
                self.__rheader_tabs_sequence(self.r.tablename)

            mres.set(ITEXT, components_l10n_dict.get(None,
                                                     self.resource.tablename))

            if component_sequence:
                serialised_component_etrees = []
                for eachcomponent in component_sequence:
                    component_table = "%s_%s" % (self.prefix, eachcomponent)

                    for eachtree in componentetrees:
                        if eachtree.attrib.get("name", None) == component_table:
                            # l10n strings are added and sequencing is done here
                            eachtree.set(ITEXT,
                                         components_l10n_dict.get(eachcomponent,
                                                                  component_table))
                            serialised_component_etrees.append(eachtree)
            else:
                serialised_component_etrees = componentetrees

            # create s3ocr tree
            s3ocr_root.append(mres)
            for res in serialised_component_etrees:
                s3ocr_root.append(res)

        # remove fields which are not required
        # loading user defined configuartions
        FIELD_TYPE_LINES = { # mapping types with number of lines
            "string": 2,
            "textbox": 4,
            "integer": 1,
            "double": 1,
            "date": 1,
            "datetime": 1,
            }
        FIELD_TYPE_BOXES = { # mapping type with numboxes
            "integer": 9,
            "double": 16,
            }
        for eachresource in s3ocr_root.iterchildren():
            resourcetablename = eachresource.attrib.get("name")

            if eachresource.attrib.get("name") in self.exclude_component_list:
                # excluded components are removed
                s3ocr_root.remove(eachresource)
                continue
            for eachfield in eachresource.iterchildren():
                fieldname = eachfield.attrib.get("name")
                # fields which have to be displayed
                fieldtype = eachfield.attrib.get(TYPE)
                
                # loading ocr specific fieldtypes
                ocrfieldtype = self.generic_ocr_field_type.get(fieldtype,
                                                               None)
                if ocrfieldtype != None:
                    eachfield.set(TYPE, ocrfieldtype)
                    # refresh fieldtypes after update
                    fieldtype = eachfield.attrib.get(TYPE)

                # set num boxes and lines
                fieldhasoptions = eachfield.attrib.get(HASOPTIONS)
                if fieldhasoptions == "False":
                    eachfield.set(LINES,
                                  str(FIELD_TYPE_LINES.get(fieldtype,
                                                           1)))
                    if fieldtype in FIELD_TYPE_BOXES.keys():
                        eachfield.set(BOXES,
                                      str(FIELD_TYPE_BOXES.get(fieldtype)))

                # if field is readable but not writable set default value
                if eachfield.attrib.get("readable", "False") == "True" and \
                        eachfield.attrib.get("writable", "False") == "False":
                    try:
                        fieldresourcename = \
                            eachresource.attrib.get("name").split("%s_" %\
                                                                      self.prefix)[1]
                    except:
                        fieldresourcename = \
                            eachresource.attrib.get("name").split("_")[1]

                    fieldresource = \
                        self.resource.components.get(fieldresourcename, None)
                    if not fieldresource:
                        fieldresource = self.resource
                    fieldname = eachfield.attrib.get("name")
                    try:
                        fielddefault = self.r.resource.table[fieldname].default
                    except(KeyError):
                        fielddefault = "None"
                    eachfield.set("default",
                                  fielddefault)

                # load custom fieldtype specific settings
                if fieldtype not in self.generic_ocr_field_type.values() \
                        and fieldtype in self.custom_fieldtype_properties.keys():
                    self.__update_custom_fieldtype_settings(eachfield)
                    # refresh fieldtypes after update
                    fieldtype = eachfield.attrib.get(TYPE)
                
                # for unknown field types
                if fieldtype not in self.generic_ocr_field_type.values():
                    eachfield.set(TYPE, "string")
                    eachfield.set(HASOPTIONS, "False")
                    eachfield.set(LINES, "2")
                    # refresh fieldtypes after update
                    fieldtype = eachfield.attrib.get(TYPE)
                
                # loading custom field specific settings
                self.__update_custom_field_settings(eachfield,
                                                    resourcetablename,
                                                    fieldname)

                # in ocr boolean fields should be shown as options
                if fieldtype == "boolean":
                    eachfield.set(HASOPTIONS, "True")

                # fields removed which need not be displayed
                if eachfield.attrib.get("readable", "False") == "False" and \
                        eachfield.attrib.get("writable", "False") == "False":
                    eachresource.remove(eachfield)
                    continue
            
                if eachfield.attrib.get(HASOPTIONS, "False") == "True" and \
                        eachfield.attrib.get(TYPE) != "boolean":
                    s3ocrselect = eachfield.getchildren()[0]
                    for eachoption in s3ocrselect.iterchildren():
                        if eachoption.text == "" or eachoption.text == None:
                            s3ocrselect.remove(eachoption)
                            continue
        return s3ocr_root

    def pdf_manager(self):
        """
        Produces OCR Compatible PDF forms
        """

        s3ocr_root = self.s3ocr_etree() # get element s3xml

        # define font size
        titlefontsize = 18
        sectionfontsize = 15
        regularfontsize = 13
        hintfontsize = 10
        
        # etree labels
        ITEXT = "label"
        HINT = "comment"
        TYPE = "type"
        HASOPTIONS = "has_options"
        LINES = "lines"
        BOXES = "boxes"

        #l10n
        l10n = self.l10n

        # get pdf title
        if self.pdftitle == None or self.pdftitle == "":
            try:
                pdftitle = self.manager.s3.crud_strings[\
                    self.tablename].subtitle_list.decode("utf-8")
            except:
                pdftitle = self.resource.tablename
        else:
            pdftitle = self.pdftitle

        # prepare pdf
        form = Form()
        form.decorate()

        # set header
        form.canvas.setTitle(pdftitle) # set pdf meta title
        form.print_text([pdftitle,],
                        fontsize=titlefontsize,
                        style="center") # set pdf header title

        form.print_text(
            [
                unicode(l10n.get("ocr_inst").get("inst1").decode("utf-8")),
                unicode(l10n.get("ocr_inst").get("inst2").decode("utf-8")),
                unicode(l10n.get("ocr_inst").get("inst3").decode("utf-8"))
                ],
            fontsize=regularfontsize,
            gray=0)
        form.linespace(3)
        # printing the etree
        for eachresource in s3ocr_root:
            form.draw_line()
            form.print_text([
                    eachresource.attrib.get(ITEXT,
                                            eachresource.attrib.get("name"))
                    ],
                            fontsize=sectionfontsize)
            form.draw_line(nextline=1)
            form.linespace(12) # line spacing between each field
            for eachfield in eachresource.iterchildren():
                fieldlabel = eachfield.attrib.get(ITEXT)
                spacing = " " * 5
                fieldhint = self.__trim(eachfield.attrib.get(HINT))
                if fieldhint != "" and fieldhint != None:
                    form.print_text(["%s%s( %s )" % \
                                         (fieldlabel,
                                          spacing,
                                          fieldhint)],
                                     fontsize=regularfontsize)
                else:
                    form.print_text([fieldlabel],
                                     fontsize=regularfontsize)

                if eachfield.attrib.get("readable", "False") == "True" and \
                        eachfield.attrib.get("writable", "False") == "False":
                    # if it is a readonly field
                    form.print_text(
                        [eachfield.attrib.get("default","No default Value")],
                        seek=10,
                        )
                elif eachfield.attrib.get(HASOPTIONS) == "True":
                    fieldtype = eachfield.attrib.get(TYPE)
                    # if the field has to be shown with options
                    if fieldtype == "boolean":
                        form.nextline()
                        form.resetx()
                        bool_text = l10n.get("boolean")
                        form.print_text(
                            [bool_text.get("yes").decode("utf-8")],
                            continuetext=1,
                            seek=3,
                            )
                        # TODO: Store positions
                        form.draw_circle(
                            boxes=1,
                            continuetext=1,
                            gray=0.9,
                            seek=10,
                            fontsize=12,
                            )
                        form.print_text(
                            [bool_text.get("no").decode("utf-8")],
                            continuetext=1,
                            seek=10,
                            )
                        # TODO: Store positions
                        form.draw_circle(
                            boxes=1,
                            continuetext=1,
                            gray=0.9,
                            seek=10,
                            fontsize=12,
                            )
                    else:
                        if fieldtype == "multiselect":
                            option_hint = l10n.get("select").get("multiselect")
                        else:
                            option_hint = l10n.get("select").get("singleselect")
                        form.print_text(
                            [option_hint.decode("utf-8")],
                            fontsize=hintfontsize,
                            gray=0.4,
                            seek=3,
                            )
                        s3ocrselect = eachfield.getchildren()[0]
                        form.nextline(regularfontsize)
                        form.resetx() # move cursor to the front
                        optionseek = 10
                        # resting margin for options
                        formmargin = form.marginsides
                        form.marginsides = optionseek + formmargin
                        for eachoption in s3ocrselect.iterchildren():
                            form.print_text(
                                [eachoption.text],
                                continuetext=1,
                                fontsize = regularfontsize,
                                seek = 10,
                                )
                            # TODO: Store positions
                            form.draw_circle(
                                boxes=1,
                                continuetext=1,
                                gray=0.9,
                                seek=10,
                                fontsize=12,
                                )
                        # restoring orginal margin
                        form.marginsides = formmargin
                            
                else:
                    # if it is a text field
                    fieldtype = eachfield.attrib.get(TYPE)
                    BOXES_TYPES = ["string", "textbox", "integer",
                                   "double", "date", "datetime",]
                    if fieldtype in BOXES_TYPES:
                        if fieldtype in ["string", "textbox"]:
                            form.linespace(3)
                            num_lines = int(eachfield.attrib.get("lines",
                                                                     1))
                            for eachline in xrange(num_lines):
                                # TODO: Store positions
                                form.draw_check_boxes(
                                    completeline=1,
                                    gray=0.9,
                                    seek=3,
                                    )
                        elif fieldtype in ["integer", "double"]:
                            num_boxes = int(eachfield.attrib.get("boxes",
                                                                 9))
                            form.linespace(3)
                            # TODO: Store positions
                            form.draw_check_boxes(
                                boxes = num_boxes,
                                gray=0.9,
                                seek=3,
                                )
                        elif fieldtype in ["date", "datetime"]:
                            # print hint
                            hinttext = \
                                l10n.get("datetime_hint").get(fieldtype).decode("utf-8")
                            form.print_text(
                                [hinttext],
                                fontsize=hintfontsize,
                                gray=0.4,
                                seek=3,
                                )
                            form.linespace(8)
                            datetime_continuetext = 0
                            datetime_seek = 3
                            if fieldtype == "datetime":
                                datetime_continuetext = 1
                                datetime_seek = 6
                                #HH
                                # TODO: Store positions
                                form.draw_check_boxes(
                                    boxes = 2,
                                    gray=0.9,
                                    seek = 3,
                                    )
                                #MM
                                # TODO: Store positions
                                form.draw_check_boxes(
                                    boxes = 2,
                                    gray=0.9,
                                    continuetext=1,
                                    seek = 4,
                                    )
                            # DD
                            # TODO: Store positions
                            form.draw_check_boxes(
                                boxes = 2,
                                gray=0.9,
                                continuetext = datetime_continuetext,
                                seek = datetime_seek,
                                )
                            # MM
                            # TODO: Store positions
                            form.draw_check_boxes(
                                boxes = 2,
                                gray=0.9,
                                continuetext=1,
                                seek = 4,
                                )
                            # YYYY
                            # TODO: Store positions
                            form.draw_check_boxes(
                                boxes = 4,
                                gray=0.9,
                                continuetext=1,
                                seek = 4,
                                )
                    else:
                        self.r.error(501, self.manager.PARSE_ERROR)
                        print sys.stderr("%s :invalid field type: %s" %\
                                             (eachfield.attrib.get("name"),
                                              fieldtype))
        return form.save()

    def __update_custom_fieldtype_settings(self,
                                       eachfield, #field etree
                                       ):
        """
        Update custom fieldtype specific settings into the etree
        """

        # xml attributes
        TYPE = "type"
        READABLE = "readable"
        WRITABLE = "writable"
        LABEL = "label"
        HINT = "comment"
        DEFAULT = "default"
        LINES = "lines"
        BOXES = "boxes"
        HASOPTIONS = "has_options"

        fieldtype = eachfield.attrib.get(TYPE)
        field_property = self.custom_fieldtype_properties.get(fieldtype,  {})

        cust_fieldtype = fieldtype_property.get("fieldtype", None)
        cust_readable = fieldtype_property.get("readable", None)
        cust_writable = fieldtype_property.get("writable", None)
        cust_label = fieldtype_property.get("label", None)
        cust_hint = fieldtype_property.get("hint", None)
        cust_default = fieldtype_property.get("default", None)
        cust_lines = fieldtype_property.get("lines", None)
        cust_boxes = fieldtype_property.get("boxes", None)
        cust_has_options = fieldtype_property.get("has_options", None)
        cust_options = fieldtype_property.get("options", None)
            
        if cust_fieldtype:
            if cust_fieldtype != None:
                eachfield.set(TYPE, cust_fieldtype)
            if cust_readable != None:
                eachfield.set(READABLE, cust_readable)
            if cust_writable != None:
                eachfield.set(WRITABLE, cust_writable)
            if cust_label != None:
                eachfield.set(LABEL, cust_label)
            if cust_hint != None:
                eachfield.set(HINT, cust_hint)
            if cust_default != None:
                eachfield.set(DEFAULT, cust_default)
            if cust_lines != None:
                eachfield.set(LINES, cust_lines)
            if cust_boxes != None:
                eachfield.set(BOXES, cust_boxes)
            if cust_has_options != None:
                eachfield.set(HASOPTIONS, cust_has_options)
            if cust_options != None:
                opt_available = eachfield.getchildren()
                if len(opt_available) == 0:
                    eachfield.append(cust_options)
                elif len(opt_available) == 1:
                    eachfield.remove(opt_available[0])
                    eachfield.append(cust_options)

    def __update_custom_field_settings(self,
                                       eachfield, #field etree
                                       resourcetablename,
                                       fieldname
                                       ):
        """
        Update custom field specific settings into the etree
        """

        # xml attributes
        TYPE = "type"
        READABLE = "readable"
        WRITABLE = "writable"
        LABEL = "label"
        HINT = "comment"
        DEFAULT = "default"
        LINES = "lines"
        BOXES = "boxes"
        HASOPTIONS = "has_options"

        unikey = "%s__%s" % (resourcetablename, fieldname)
        field_property = self.custom_field_properties.get(unikey,  {})

        cust_fieldtype = field_property.get("fieldtype", None)
        cust_readable = field_property.get("readable", None)
        cust_writable = field_property.get("writable", None)
        cust_label = field_property.get("label", None)
        cust_hint = field_property.get("hint", None)
        cust_default = field_property.get("default", None)
        cust_lines = field_property.get("lines", None)
        cust_boxes = field_property.get("boxes", None)
        cust_has_options = field_property.get("has_options", None)
        cust_options = field_property.get("options", None)

        if cust_fieldtype:
            if cust_fieldtype != None:
                eachfield.set(TYPE, cust_fieldtype)
            if cust_readable != None:
                eachfield.set(READABLE, cust_readable)
            if cust_writable != None:
                eachfield.set(WRITABLE, cust_writable)
            if cust_label != None:
                eachfield.set(LABEL, cust_label)
            if cust_hint != None:
                eachfield.set(HINT, cust_hint)
            if cust_default != None:
                eachfield.set(DEFAULT, cust_default)
            if cust_lines != None:
                eachfield.set(LINES, cust_lines)
            if cust_boxes != None:
                eachfield.set(BOXES, cust_boxes)
            if cust_has_options != None:
                eachfield.set(HASOPTIONS, cust_has_options)
            if cust_options != None:
                opt_available = eachfield.getchildren()
                if len(opt_available) == 0:
                    eachfield.append(cust_options)
                elif len(opt_available) == 1:
                    eachfield.remove(opt_available[0])
                    eachfield.append(cust_options)

    def __rheader_tabs_sequence(self, resourcename):
        """
        Sequence of components is returned as a list
        """

        component_seq = []
        component_l10n_dict = {}
        rtabs = self.rheader_tabs
        for eachel in rtabs:
            if eachel[1] != None:
                component_seq.append(eachel[1])
            component_l10n_dict[eachel[1]] = eachel[0].decode("utf-8")
        return component_seq, component_l10n_dict

    def __trim(self, text):
        """
        Helper to trim off any enclosing paranthesis
        """

        if isinstance(text, str) and \
                text[0] == "(" and \
                text[-1] == ")":
            text = text[1:-1]
        return text


#==============================================================================
#==================== unicode support to reportlab ============================
#==============================================================================

fonts_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "../../static/fonts")

#------------------------------------------------------------------------------
# unifont - considered to be an allrounder
#------------------------------------------------------------------------------

try:
    pdfmetrics.registerFont(TTFont("unifont",
                                   os.path.join(fonts_directory,
                                                "unifont/unifont.ttf")))
    unifont_map = [
        (0, 65536),
        ]
except:
    unifont_map = []
    print >> sys.stderr, "S3 Debug: s3ocr: unifont not found, run static/fonts/setfonts.py"

#------------------------------------------------------------------------------
# Arabic fonts
#------------------------------------------------------------------------------

try:
    pdfmetrics.registerFont(TTFont("AlMateen-Bold",
                                   os.path.join(fonts_directory,
                                                "arabic/ae_AlMateen-Bold.ttf")))
    from fontmap.AlMateenBold import AlMateenBold_map

    pdfmetrics.registerFont(TTFont("AlMohanad",
                                   os.path.join(fonts_directory,
                                                "arabic/ae_AlMohanad.ttf")))
    from fontmap.AlMohanad import AlMohanad_map

except:
    AlMateenBold_map = []
    AlMohanad_map = []
    print >> sys.stderr, "S3 Debug: s3ocr: arabic fonts not found, run static/fonts/setfonts.py"    

#------------------------------------------------------------------------------
# japanese fonts
#------------------------------------------------------------------------------

try:
    pdfmetrics.registerFont(TTFont("SazanamiGothic",
                                   os.path.join(fonts_directory,
                                                "japanese/sazanami-gothic.ttf")))
    from fontmap.SazanamiGothic import SazanamiGothic_map

    pdfmetrics.registerFont(TTFont("SazanamiMincho",
                                   os.path.join(fonts_directory,
                                                "japanese/sazanami-mincho.ttf")))
    from fontmap.SazanamiMincho import SazanamiMincho_map

except:
    SazanamiGothic_map = []
    SazanamiMincho_map = []
    print >> sys.stderr, "S3 Debug: s3ocr: japanese fonts not found, run static/fonts/setfonts.py"

#--------------------------------------------------------------------------
# Standard fonts
#--------------------------------------------------------------------------

Helvetica = "Helvetica"
Helvetica_map = [
    (32, 127),
    (160, 161),
    (173, 173),
    ]

# Fonts
#Courier = "Courier"
#Helvetica_Bold = "Helvetica-Bold"
#Helvetica_Bold_Oblique = "Helvetica-BoldOblique"
#Helvetica_Oblique = "Helvetica-Oblique"

#--------------------------------------------------------------------------
# some global variables
#--------------------------------------------------------------------------

fontlist = [
    "Helvetica",         # english and latin english fonts
    "AlMateen-Bold",     # arabic fonts
    "AlMohanad",         # arabic fonts
    "SazanamiGothic",    # japanese fonts
    "SazanamiMincho",    # japanese fonts
    "unifont",           # unifont should be always at the last
    ]

fontmapping = {
    "Helvetica": Helvetica_map,
    "AlMateen-Bold": AlMateenBold_map,
    "AlMohanad": AlMohanad_map,
    "SazanamiGothic": SazanamiGothic_map,
    "SazanamiMincho": SazanamiMincho_map,
    "unifont": unifont_map,
}

fontchecksequence = []

for eachfont in fontlist:
    if len(fontmapping[eachfont]) != 0:
        fontchecksequence.append(eachfont)


#==========================================================================
#=============== internal Class Definitions and functions =================
#==========================================================================

#======================== pdf layout from xform ===========================

class Form(object):
    """ Form class to use reportlab to generate pdf """

    def __init__(self, pdfname="ocrform.pdf", margintop=65, marginsides=50,
                 **kw):
        """ Form initialization """

        self.pdfpath = kw.get("pdfpath", pdfname)
        self.verbose = kw.get("verbose", 0)
        self.linespacing = kw.get("linespacing", 4)
        self.font = kw.get("typeface", "Helvetica")
        self.fontsize = kw.get("fontsize", 13)
        self.IObuffer = StringIO()
        self.canvas = Canvas(self.IObuffer, pagesize = A4)
        self.width, self.height = A4
        self.x = marginsides
        self.lastx = marginsides
        self.marginsides = marginsides
        self.margintop = margintop
        self.y = self.height - margintop
        self.lasty = self.height - margintop
        self.num = 1
        self.gray = 0
        self.pagebegin = 1
        self.put_page_num()

    def barcode(self, uuid):
        """ Generate barcode of uuid """

        barcode = code128.Code128(str(uuid), barWidth=1, barHeight=20)
        barcode.drawOn(self.canvas, self.lastx, self.lasty)
        self.lasty = self.lasty - 20
        self.y = self.lasty

    def decorate(self):
        """ Decorates the the form with the markers needed to align the form later """

        c = self.canvas
        c.rect(20, 20, 20, 20, fill=1)                              # bt lf
        c.rect(self.width - 40, 20, 20, 20, fill=1)                 # bt rt
        c.rect(20, self.height - 40, 20, 20, fill=1)                # tp lf
        c.rect(self.width/2 - 10, 20, 20, 20, fill=1)               # bt md
        c.rect(20, self.height/2 - 10, 20, 20, fill=1)              # md lf
        c.rect(self.width - 40, self.height - 40, 20, 20, fill=1)   # tp rt
        c.rect(self.width - 40, self.height/2 - 10, 20, 20, fill=1) # md rt

    def print_text(self,
                   lines,
                   fontsize=13,
                   gray=0,
                   seek=0,
                   continuetext=0,
                   style="default"):
        """
        Give the lines to be printed as a list,
        set the font and grey level 
        """

        self.fontsize = fontsize
        self.gray = gray

        if not continuetext and not self.pagebegin:
                self.resetx()
                self.nextline()

        self.pagebegin = 0

        if seek:
            self.resetx(seek=seek)

        numlines = len(lines)
        loopcounter = 0
        for line in lines:
            loopcounter += 1
            line = self.__html_unescape(unicode(line))
            
            # alignment
            if not continuetext:
                if style == "center":
                    self.x = \
                        (self.width - (len(line) * (self.fontsize / 2)))/2
                elif style == "right":
                    self.x = \
                        ((self.width - self.marginsides) -\
                             ((len(line)+3) * (self.fontsize / 2)))
            if continuetext:
                # wrapping multiline options
                if (self.width - self.marginsides - self.x) < 100:
                    self.resetx()
                    self.nextline()
            if (self.y - self.fontsize) < 50:
                self.set_new_page()
            for char in line:
                t = self.writechar(char)
                self.x = t.getX()
                self.y = t.getY()
                # text wrapping -> TODO: word wrapping
                if self.x > (self.width - self.marginsides - self.fontsize):
                    self.writechar("-")
                    self.nextline()
                    self.resetx(self.fontsize)
            if not continuetext and loopcounter != numlines:
                self.nextline()
                self.resetx()

    def writechar(self, char=" "):
        """
        Writes one character on canvas
        """

        font=self.selectfont(char)
        t = self.canvas.beginText(self.x, self.y)
        t.setFont(font, self.fontsize)
        t.setFillGray(self.gray)
        t.textOut(char)
        self.canvas.drawText(t)
        return t

    def nextline(self, fontsize=0):
        """
        Moves the y cursor down one line
        """

        if fontsize != 0:
            self.fontsize = fontsize

        if self.pagebegin == 0:
            self.y = self.y - (self.fontsize + self.linespacing)
            if self.y < self.margintop:
                self.set_new_page()

        self.pagebegin = 0

    def resetx(self, offset=0, seek=None):
        """
        Moves the x cursor with offset
        """

        if seek == None:
            self.x = self.marginsides + offset
        else:
            self.x += seek
        lastvalidx = self.width - (self.marginsides + (self.fontsize / 2))
        writablex = self.width - (2 * self.marginsides)
        if self.x > lastvalidx:
            currentx = self.x - self.marginsides
            remx = currentx % writablex
            self.x = remx + self.marginsides
            numlines = int(currentx / writablex)
            for line in xrange(numlines):
                self.nextline()

    def __html_unescape(self, text):
        """
        Helper function, unscape any html special characters
        """

        return re.sub("&(%s);" % "|".join(name2codepoint),
                      lambda m: unichr(name2codepoint[m.group(1)]),
                      text)

    def linespace(self, spacing=2):
        """
        Moves the y cursor down by given units
        """
        if self.pagebegin == 0:
            self.y -= spacing
        self.pagebegin = 0

    def selectfont(self, char):
        """ Select font according to the input character """

        charcode = ord(char)
        for font in fontchecksequence:
            for fontrange in fontmapping[font]:
                if charcode in xrange(fontrange[0], fontrange[1]):
                    return font
        return "Helvetica"  # fallback, if no thirdparty font is installed

    def draw_check_boxes(self,
                         boxes=1,
                         completeline=0,
                         lines=0,
                         seek=0,
                         continuetext=0,
                         fontsize=15,
                         gray=0,
                         style="",
                         ):
        """ Function to draw check boxes default no of boxes = 1 """

        if not continuetext and not self.pagebegin:
            self.resetx()
            self.nextline()
        self.pagebegin = 0
        self.fontsize = fontsize
        c = self.canvas
        c.setLineWidth(0.90)
        c.setStrokeGray(gray)
        if style == "center":
            self.x = self.width / 2
        elif style == "right":
            self.x = self.width - self.marginsides - self.fontsize
        if seek > (self.width - (self.marginsides + self.fontsize)):
            seek = 0
        if (self.y - self.fontsize) < 40:
            self.set_new_page()
        #if continuetext == 1:
        #    self.y = self.y + self.fontsize
        #    self.x = self.lastx
        #else:
        #    self.x = self.marginsides
        if seek != 0:
            self.x = self.x + seek
        if fontsize == 0:
            fontsize = self.fontsize
        else:
            self.fontsize = fontsize
        if completeline == 1:
            boxes = int(self.width / self.fontsize)
        for i in range(boxes):
            c.rect(self.x, self.y, self.fontsize, self.fontsize)
            self.x = self.x + self.fontsize
            if self.x > (self.width - (self.marginsides + self.fontsize)):
                break
        self.lastx = self.x
        #self.x = self.marginsides
        #self.y = self.y - self.fontsize
        #if isdate:
        #    t = c.beginText(self.x, self.y)
        #    t.setFont(Helvetica, 13)
        #    t.setFillGray(0)
        #    t.textOut("   D  D  M  M  Y  Y  Y  Y")
        #    c.drawText(t)
        #    self.y = self.y - fontsize
        #    self.lastx = t.getX()
        #    self.lasty = self.y
        #if isdatetime:
        #    t = c.beginText(self.x, self.y)
        #    t.setFont(Helvetica, 12.5)
        #    t.setFillGray(0.4)
        #    t.textOut("   D  D  M  M  Y  Y  Y  Y -H  H :M  M")
        #    c.drawText(t)
        #    self.y = self.y - fontsize
        #    self.lastx = t.getX()
        #    self.lasty = self.y
        self.lastx = self.x

    def draw_circle(self,
                    boxes=1,
                    completeline=0,
                    lines=0,
                    seek=0,
                    continuetext=0,
                    fontsize=0,
                    gray=0,
                    style=""):
        """ Draw circles on the form """

        c = self.canvas
        c.setLineWidth(0.90)
        c.setStrokeGray(gray)
        self.resetx(seek=seek)
        #if style == "center":
        #    self.x = self.width / 2
        #elif style == "right":
        #    self.x = self.width - self.marginsides - self.fontsize
        #if seek > (self.width - (self.marginsides + self.fontsize)):
        #    seek = 0
        #if (self.y - self.fontsize) < 40:
        #    self.set_new_page()
        #if continuetext == 1:
        #    self.y = self.y + self.fontsize
        #    self.x = self.lastx
        #else:
        #    self.x = self.marginsides
        #if seek != 0:
        #    self.x = self.x + seek
        #if fontsize == 0:
        #    fontsize = self.fontsize
        #else:
        #    self.fontsize = fontsize
        #if completeline == 1:
        #    boxes = int(self.width / self.fontsize)
        for eachcircle in xrange(boxes):
            c.circle(self.x + self.fontsize/2, self.y + self.fontsize/2,
                     self.fontsize/2, fill = 0)
            self.resetx(seek=self.fontsize)
            self.resetx(seek=seek)
        #    if self.x > (self.width - (self.marginsides + self.fontsize)):
        #        break
        #self.lastx = self.x
        #self.x = self.marginsides
        #self.y = self.y - self.fontsize

    def draw_line(self, gray=0, nextline=0):
        """ Function to draw a straight line """

        self.fontsize = 4
        if nextline:
            self.nextline()
        else:
            self.linespace(8)
        self.resetx()
        c = self.canvas
        c.setStrokeGray(gray)
        c.setLineWidth(1)
        #self.y = self.y + self.linespacing + (self.fontsize/2)
        c.line(self.x, self.y, self.width - self.x, self.y)
        self.y = self.y + (self.linespacing)

    def set_new_page(self):
        """
            All changes are forgotten when a showPage() has been executed.
            They have to be set again.
        """
        self.num += 1
        c = self.canvas
        c.showPage()
        self.decorate()
        self.x = self.marginsides
        self.lastx = self.marginsides
        self.y = self.height - self.margintop
        #self.print_text(["Page %s" % unicode(self.num)], fontsize=8,
        #                style="right")
        self.put_page_num()
        #self.x = self.marginsides
        #self.lastx = self.x
        #self.y = self.y - 32
        self.pagebegin = 1

    def put_page_num(self):
        x, y = self.x, self.y
        fontsize = self.fontsize

        self.fontsize = 10
        text = "page%s" % self.num
        self.x = self.width - \
            (((len(text)+2)*(self.fontsize/2)) + self.marginsides)
        self.y = 25
        for char in text:
            t = self.writechar(char)
            self.x = t.getX()
            self.y = t.getY()

        self.fontsize = fontsize
        self.x, self.y = x, y

    def set_title(self, title = "FORM"):
        """ Sets the title of the pdf. """

        c = self.canvas.setTitle(title)

    def save(self):
        """ Saves the form """

        self.canvas.save()
        pdf = self.IObuffer.getvalue()
        self.IObuffer.close()
        return pdf
