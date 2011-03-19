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
import inspect
import os
import sys
import uuid
import re
from StringIO import StringIO

# Importing the xml stuff
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
from xml.dom.minidom import Document

# Importing reportlab stuff
try:
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.graphics.barcode import code128
    # for adding more fonts
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab
except(ImportError):
    print >> sys.stderr, "S3 Debug: WARNING: S3OCR: reportlab has not been installed."

from lxml import etree
from htmlentitydefs import name2codepoint

from s3rest import S3Method

#==========================================================================
#================================= OCR API ================================
#==========================================================================

class S3OCR(S3Method):
    """
    Generate XForms and PDFs the s3 way
    """

    def __init__(self, T):
        """
        Instialisting s3ocr
        """

        self.T = T
        self.rheader_tabs = {}
        self.db2ocr_type_mapping = {
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

        self.custom_field_types = {
            }

        #text for localisation
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
                "yes": T("Yes"),
                "no": T("No"),
                },
            "select": {
                "multiselect": self.T("Select one or more option(s) that apply"),
                "singleselect": self.T("Select any one option that apply"),
                },
            }

    def apply_method(self,
                     r,
                     **attr):
        """
        S3Method's abstract method
        """
        
        xml = self.manager.xml
        self.r = r

        if r.request.vars.get("_debug", False) == "1":
            self.debug = True
        else:
            self.debug = False

        if self.debug:
            content_disposition = "inline"
        else:
            content_disposition = "attachment"
        
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
                raise HTTP(501, body="method not implimented")
            elif format == "pdf":
                raise HTTP(501, body="method not implimented")
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
        s3xml = s3xml_etree.getroot()
        s3resource = s3xml.getchildren()[0]
        s3ocr_etree = etree.Element("s3ocr")

        if self.r.component:     # if it is a component
            component_sequence, components_l10n_dict = \
                self.__rheader_tabs_sequence(self.r.tablename)
            s3resource.set(ITEXT,
                           components_l10n_dict.get(None,
                                                    self.resource.tablename))
            s3ocr_etree.append(s3resource)

        else:                    # if it is main resource
            componentetrees = []
            # mres is main resource etree
            mres = etree.Element("resource")
            for attr in s3resource.attrib.keys():
                mres.set(attr, s3resource.attrib.get(attr))
            for s3field in s3resource:
                if s3field.tag == "field":       # main resource fields
                    mres.append(s3field)
                elif s3field.tag == "resource":  # component resource
                    componentetrees.append(s3field)

            # Serialisation of Component List and l10n
            serialised_component_etrees = []
            component_sequence, components_l10n_dict = \
                self.__rheader_tabs_sequence(self.r.tablename)

            mres.set(ITEXT, components_l10n_dict.get(None,
                                                     self.resource.tablename))

            for eachcomponent in component_sequence:
                component_table = "%s_%s" % (self.prefix, eachcomponent)

                for eachtree in componentetrees:
                    if eachtree.attrib.get("name", None) == component_table:
                        # l10n strings are added and sequencing is done here
                        eachtree.set(ITEXT,
                                     components_l10n_dict.get(eachcomponent,
                                                              component_table))
                        serialised_component_etrees.append(eachtree)

            # create s3ocr tree
            s3ocr_etree.append(mres)
            for res in serialised_component_etrees:
                s3ocr_etree.append(res)

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
        for eachresource in s3ocr_etree.iterchildren():
            resourcetablename = eachresource.attrib.get("name")

            for eachfield in eachresource.iterchildren():
                fieldname = eachfield.attrib.get("name")
                if eachfield.attrib.get("readable", "False") == "False" and \
                        eachfield.attrib.get("writable", "False") == "False":
                    # fields which need not be displayed
                    eachresource.remove(eachfield)
                else:
                    # fields which have to be displayed
                    fieldtype = eachfield.attrib.get(TYPE)

                    # loading custom fieldtype specific settings
                    eachfield.set(TYPE,
                                  self.db2ocr_type_mapping.get(fieldtype,
                                                               "unknown"))
                    # refresh fieldtypes after update
                    fieldtype = eachfield.attrib.get(TYPE)

                    # for unknown field types
                    if fieldtype == "unknown":
                        eachfield.set(TYPE, "string")
                        eachfield.set(HASOPTIONS, "False")

                    # refresh fieldtypes after update
                    fieldtype = eachfield.attrib.get(TYPE)

                    # in ocr boolean fields should be shown as options
                    if fieldtype == "boolean":
                        eachfield.set(HASOPTIONS, "True")

                    # set num boxes and lines
                    fieldhasoptions = eachfield.attrib.get(HASOPTIONS)
                    if fieldhasoptions == "False":
                        eachfield.set(LINES,
                                      str(FIELD_TYPE_LINES.get(fieldtype,
                                                               1)))
                        if fieldtype in FIELD_TYPE_BOXES.keys():
                            eachfield.set(BOXES,
                                          str(FIELD_TYPE_BOXES.get(fieldtype)))

                    # loading custom field specific settings
                    unikey = "%s__%s" % (resourcetablename, fieldname)
                    cust_fieldtype, lines, has_options  = \
                        self.custom_field_types.get(unikey, (None,
                                                             None,
                                                             None))
                    if cust_fieldtype:
                        eachfield.set(TYPE, cust_fieldtype)
                        eachfield.set(LINES, lines)
                        eachfield.set(HASOPTIONS, has_options)

        return s3ocr_etree

    def pdf_manager(self):
        """
        Produces OCR Compatible PDF forms
        """

        s3ocr_etree = self.s3ocr_etree() # get element s3xml

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
        try:
            pdftitle = \
                self.manager.s3.crud_strings[self.tablename].subtitle_list.decode("utf-8")
        except:
            pdftitle = self.resource.tablename

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
        for eachresource in s3ocr_etree:
            form.draw_line()
            form.print_text([eachresource.attrib.get(ITEXT)],
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

                if eachfield.attrib.get(HASOPTIONS) == "True":
                    fieldtype = eachfield.attrib.get(TYPE)
                    
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

    def __trim(self, text):
        """
        Helper to trim off any enclosing paranthesis
        """

        if isinstance(text, str) and \
                text[0] == "(" and \
                text[-1] == ")":
            text = text[1:-1]
        return text

    def set_ocr_fieldtype(self,
                          prefix,
                          suffix,
                          fieldname,
                          fieldtype="string",
                          lines=2,
                          has_options=False
                          ):
        """
        Set custom individual fieldtypes
        """

        key = "%s_%s__%s" % (prefix, suffix, fieldname)
        self.custom_field_types.update({key: (fieldtype,
                                              lines,
                                              has_options)
                                        })

    def set_db2ocr_fieldtype(self, typedict):
        """
        User Defined Custom Field Types
        """

        self.db2ocr_type_mapping.update(typedict)

    def put_rheader_tabs(self, prefix, suffix, tabs):
        """
        Put component names for l10n
        """

        resourcename = "%s_%s" % (prefix, suffix)
        self.rheader_tabs.update({resourcename: tabs,})

    def __rheader_tabs_sequence(self, resourcename):
        """
        Sequence of components is returned as a list
        """

        component_seq = []
        component_l10n_dict = {}
        rtabs = self.rheader_tabs.get(resourcename,[])
        for eachel in rtabs:
            if eachel[1] != None:
                component_seq.append(eachel[1])
            component_l10n_dict[eachel[1]] = eachel[0].decode("utf-8")
        return component_seq, component_l10n_dict


#==============================================================================
#==================== unicode support to reportlab ============================
#==============================================================================

reportlab.rl_config.warnOnMissingFontGlyphs = 0
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
            line = unicode(self.__html_unescape(line))
            
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
                if (self.width - self.marginsides - self.x) < 80:
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


#========== xml.sax.ContentHandler instance for layout parsing ============

class FormHandler(ContentHandler):

    def __init__(self, form, uid, lang="eng"):
        """ Form initialization and preparation """

        self.form = form
        self.input = 0
        self.select = 0
        self.label = 0
        self.value = 0
        self.read = 0
        self.item = 0
        self.model = 0
        self.itext = 0
        self.hint = 0
        self.translation = 0
        self.translang = ""
        self.translist = []
        self.text = 0
        self.textid, self.texttype = ["", ""]
        self.lang = lang
        self.printtext = ""
        self.title = ""
        self.ref = ""
        self.initial = 1
        self.single = 0
        self.multiple = 0
        self.uuid = uid
        #print self.uuid
        self.form.decorate()
        self.page = 1
        self.xmlcreate()
        self.name = ""
        self.dict = {}
        self.pdf = ""
        self.xmls = {}
        self.labelTrans = ""
        self.customfields = {"location_id":4,\
                                 "staff_id":2,\
                                 "staff2_id":2,\
                                 } # fields having custom sizes
        self.readonly = ""
        self.default = ""

    def xmlcreate(self):
        """ Creates the xml """

        self.doc = Document()
        self.xmltitle = "%s_%s_%s.xml" % (str(self.uuid), self.lang,
                                          str(self.page))
        self.root = self.doc.createElement("guide")
        self.doc.appendChild(self.root)
        if self.initial == 0:
            if self.single == 1:
                element = "select1"
            elif self.multiple == 1:
                element = "select"
            elif self.input == 1:
                element = "input"
            self.child1 = self.doc.createElement(element)
            self.child1.setAttribute("ref", self.ref)
            self.root.appendChild(self.child1)
        if self.initial == 1:
            self.initial = 0

    def xmlsave(self):
        """ Save the xml """

        self.xmls[self.xmltitle] = self.doc.toprettyxml(indent = "    ")

    def startElement(self, name, attrs):
        """ Parses the starting element and then check what to read """

        self.element = name
        self.title = ""
        self.value_ch = ""
        if not str(name).find(":") == -1:
            name = name.split(":")[1]
        if name == "input":
            self.input = 1
            self.ref = attrs.get("ref")
            self.readonly = attrs.get("readonly", "")
            self.default = attrs.get("default", "")
            #if not str(self.ref).find("/") == -1:
            #    ref = str(self.ref).split("/")[-1]
            #    if ref in self.hiddenfields:
            #        self.protectedfield = 1
            self.child1 = self.doc.createElement(name)
            self.child1.setAttribute("ref", self.ref)
            if self.ref in self.dict:
                self.child1.setAttribute("type", self.dict[self.ref])
                self.type = self.dict[self.ref]
            else:
                self.child1.setAttribute("type", "string")
                self.type = "string"
            self.root.appendChild(self.child1)
        elif name == "label":
            self.label = 1
            self.labelref = attrs.get("ref")
            if self.select != 1:
                self.child2 = self.doc.createElement("location")
                self.child1.appendChild(self.child2)
            elif self.select == 1 and self.item == 1:
                self.child2 = self.doc.createElement("location")
                self.child1.appendChild(self.child2)
        elif name == "select" or name == "select1":
            self.select = 1
            self.read = 1
            self.ref = attrs.get("ref")
            self.child1 = self.doc.createElement(name)
            self.child1.setAttribute("ref", self.ref)
            self.root.appendChild(self.child1)
            if name == "select":
                self.form.print_text(["", "", unicode(" Multiple select: "), ""],
                                     fontsize=10, gray=0)
                self.multiple = 1
            else:
                self.form.print_text(["", "", unicode("Single select: "), ""],
                                     fontsize=10, gray=0)
                self.single = 1
        elif name == "item":
            self.item = 1
        elif name == "value":
            self.value = 1
        elif name == "bind":
            self.dict[str(attrs.get("nodeset"))] = str(attrs.get("type"))
        elif name == "itext":
            self.itext = 1
        elif name == "translation":
            self.translation = 1
            self.translang = attrs.get("lang")
        elif name == "text":
            self.text = 1
            if attrs.get("id") == "title":
                self.textid = "title"
                self.texttype = "string"
            else:
                self.textid, self.texttype = attrs.get("id").split(":")
        elif name == "model":
            self.model = 1
        elif name == "hint":
            self.hint = 1

    def characters(self, ch):
        """ Deal with the data """

        if self.item == 1 and self.value == 1 and self.select == 1:
            self.value_ch += ch
        elif self.itext == 1 and self.translation == 1 and self.text == 1:
            self.value_ch += ch
        else:
            self.title += ch

    def endElement(self, name):
        """ It specifies the operations to do on closing the element """

        if self.form.lasty < 100:
            self.form.set_new_page()
            self.xmlsave()
            self.page += 1
            self.xmlcreate()
        if not str(name).find(":") == -1:
            name = name.split(":")[1]
        #if name == "title":
        if name == "head":
            if self.model == 0:
                #self.form.barcode(self.uuid) # not needed till ocr is functional
                for trtuple in self.translist:
                    if trtuple[0] == "title":
                        self.printtext = trtuple[2]
                self.form.set_title(unicode(self.printtext))
                #self.form.set_title(str(self.title))
                self.form.print_text([unicode(self.printtext)], fontsize=18,
                                     style="center")
                #self.form.print_text([unicode(self.title)], fontsize=18, style="center")
                self.form.print_text([unicode("1. Fill the necessary fields in BLOCK CAPITAL letters."),
                                      unicode("2. Always use one box per letter and leave one box space to separate words."),
                                      unicode("3. Fill in the circles completely.")],
                                      fontsize=13, gray=0)
                self.form.draw_line()
                # self.form.print_text([unicode(self.uuid)], fontsize=10, gray=0)
        elif name == "input":
            self.input = 0
            #self.protectedfield = 0
            self.type = ""
            self.readonly = ""
            self.default = ""
        elif name == "select" or name == "select1":
            self.select = 0
            self.multiple = 0
            self.single = 0
            self.read = 0
            self.form.print_text([" ",])
        elif name == "label":
            if self.input == 1: #and self.protectedfield != 1:
                for trtuple in self.translist:
                    if trtuple[0] == self.ref and trtuple[1] == "label":
                        self.printtext = trtuple[2]
                self.form.print_text([" ", " %s " % unicode(self.printtext), " "])
                self.child3 = self.doc.createTextNode("%s,%s" % (str(self.form.lastx),
                                                                 str(self.form.lasty)))
                self.child2.appendChild(self.child3)
                self.child2.setAttribute("font", str(16))
                if self.readonly == "true":
                    self.form.print_text(["   %s " % unicode(self.default)])
                elif self.ref == "age":
                    self.form.draw_check_boxes(boxes=2, completeline=0,
                                               continuetext=0, gray=0.9,
                                               fontsize=16, seek=10)
                    self.child2.setAttribute("boxes", str(2))
                elif self.type == "date":
                    self.form.draw_check_boxes(boxes=8, completeline=0,
                                               continuetext=0, gray=0.9,
                                               fontsize=16, seek=10, isdate=1)
                    self.child2.setAttribute("boxes", str(8))
                elif self.type == "datetime":
                    self.form.draw_check_boxes(boxes=12, completeline=0,
                                               continuetext=0, gray=0.9,
                                               fontsize=16, seek=10, isdatetime=1)
                    self.child2.setAttribute("boxes", str(12))
                elif self.type == "int":
                    count = (self.form.width - 2 * self.form.marginsides) / 32
                    self.form.draw_check_boxes(boxes=1, completeline=1,
                                               continuetext=0, gray=0.9,
                                               fontsize=16, seek=10)
                    self.child2.setAttribute("boxes", str(count))
                elif self.type == "text":
                    count = (self.form.width - 2 * self.form.marginsides) / 16
                    self.child2.setAttribute("boxes", str(int(count)))
                    self.child2.setAttribute("lines", "4")
                    for i in xrange(4):
                        self.form.draw_check_boxes(boxes=1, completeline=1,
                                                   continuetext=0, gray=0.9,
                                                   fontsize=16, seek=10)
                        if self.form.lasty < 100:
                            self.form.set_new_page()
                            self.xmlsave()
                            self.page += 1
                            self.xmlcreate()
                else:
                    if not str(self.ref).find("/") == -1:
                        ref = str(self.ref).split("/")[-1]
                        if ref in self.customfields.keys():
                            numlines = self.customfields[ref]
                        else:
                            # Minimum of 2 lines
                            numlines = 2
                    count = (self.form.width - 2 * self.form.marginsides) / 16
                    self.child2.setAttribute("boxes", str(int(count)))
                    self.child2.setAttribute("lines", str(numlines))
                    for i in xrange(numlines):
                        self.form.draw_check_boxes(boxes=1, completeline=1,
                                                   continuetext=0, gray=0.9,
                                                   fontsize=16, seek=10)
                        if self.form.lasty < 100:
                            self.form.set_new_page()
                            self.xmlsave()
                            self.page += 1
                            self.xmlcreate()
            elif self.item == 1 and self.select == 1:
                labelid, labeltype = self.labelref.split("'")[1].split("&")[0].split(":")
                for trtuple in self.translist:
                    if trtuple[0] == labelid and trtuple[1] == labeltype:
                        self.printtext = trtuple[2]
                if self.printtext != "None" and self.printtext != "Unknown":
                    self.form.print_text(["     %s" % unicode(self.printtext)],
                                         continuetext = 1)
                    x = self.form.lastx
                    y = self.form.lasty
                    self.form.draw_circle(boxes=1, continuetext=1, gray=0.9,
                                          fontsize=12, seek=10)
                    self.labelTrans = "Trans"
                else:
                    self.labelTrans = "NoTrans"
            elif self.read == 1 and self.select == 1:
                labelid, labeltype = self.labelref.split("'")[1].split("&")[0].split(":")
                for trtuple in self.translist:
                    if trtuple[0] == labelid and trtuple[1] == labeltype:
                        self.printtext = trtuple[2]
                self.form.print_text([" %s " % unicode(self.printtext), " ", " "])
                self.read = 0
            self.label= 0
            self.labelref = ""
            labelid, labeltype = ["", ""]
            trtuple = ("", "", "")
            self.printtext = ""
        elif name == "value":
            self.value = 0
            if self.select == 1:
                self.child3 = self.doc.createTextNode("%s,%s" % (str(self.form.lastx - 12),
                                                                 str(self.form.lasty)))
                self.child2.appendChild(self.child3)
                self.child2.setAttribute("value", str(self.value_ch))
                self.child2.setAttribute("font", str(12))
                self.child2.setAttribute("boxes", str(1))
                if self.item == 1 and self.labelTrans == "NoTrans":
                    self.printtext = str(self.value_ch)
                    self.form.print_text(["     " + unicode(self.printtext)],
                                         continuetext = 1)
                    x = self.form.lastx
                    y = self.form.lasty
                    self.form.draw_circle(boxes=1, continuetext=1, gray=0.9,
                                          fontsize=12, seek=10)
                    self.labelTrans == ""
            if self.itext == 1 and self.translation == 1 and self.text == 1 and \
                                                    self.translang == self.lang:
                self.translist.append((self.textid, self.texttype,
                                       unicode(self.value_ch)))
            self.value_ch = ""
        elif name == "item":
            self.item = 0
        elif name == "itext":
            self.itext = 0
        elif name == "translation":
            self.translation = 0
            self.translang = ""
        elif name == "text":
            self.name = 0
            self.textid, self.texttype = ["", ""]
        elif name == "model":
            self.model = 0
        elif name == "hint":
            for trtuple in self.translist:
                    if trtuple[0] == self.ref and trtuple[1] == "hint":
                        self.printtext = trtuple[2]
            if self.printtext not in ["None", "Unkown"]:
                self.form.print_text([" %s " % unicode(self.printtext), " ", " "],
                                     fontsize=10)
            self.hint = 0
        elif name == "html":
            self.translist = [] # clearing the translation mapping
            #print "End, saving with the filename %s" % str(self.form.pdfpath)
            self.xmlsave()
            self.pdf = self.form.save()
        self.title = ""

    def get_files(self):
        """ Returns pdf text and layout xml text as dict """
        return self.pdf, self.xmls


