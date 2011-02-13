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

#========================== import section ================================

__all__ = ["s3ocr_generate_pdf", "s3ocr_get_languages"]

#Generic stuff
import os
import sys
import uuid
from StringIO import StringIO


#Importing the xml stuff
from xml.sax.handler import ContentHandler
from xml.sax import make_parser
from xml.dom.minidom import Document


#Importing reportlab stuff
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128


# Fonts
Courier = "Courier"
Helvetica = "Helvetica"
Helvetica_Bold = "Helvetica-Bold"
Helvetica_Bold_Oblique = "Helvetica-BoldOblique"
Helvetica_Oblique = "Helvetica-Oblique"

#==========================================================================
#=============== internal Class Definitions and functions =================
#==========================================================================

#======================== pdf layout from xform ===========================

class Form:
    """ Form class to use reportlab to generate pdf """

    def __init__(self, pdfname="ocrform.pdf", margintop=50, marginsides=50, **kw):
	""" Form initialization """
        self.pdfpath = kw.get("pdfpath", pdfname)
        self.verbose = kw.get("verbose", 0)
        self.font = kw.get("typeface", Courier)
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

    def barcode(self, uuid):
        """ Generate barcode of uuid """
        barcode = code128.Code128(str(uuid), barWidth=1, barHeight=20)
        barcode.drawOn(self.canvas, self.lastx, self.lasty)
        self.lasty = self.lasty - 20
        self.y = self.lasty

    def decorate(self):
        """ Decorates the the form with the markers needed to align the form later """
        c = self.canvas
        c.rect(20, 20, 20, 20, fill=1)
        c.rect(self.width - 40, 20, 20, 20, fill=1)
        c.rect(20, self.height - 40, 20, 20, fill=1)
        c.rect(self.width/2 - 10, 20, 20, 20, fill=1)
        c.rect(20, self.height/2 - 10, 20, 20, fill=1)
        c.rect(self.width - 40, self.height - 40, 20, 20, fill=1)
        c.rect(self.width - 40, self.height/2 - 10, 20, 20, fill=1)

    def print_text(self, lines, fontsize=12, gray=0, seek=0, continuetext=0, style="default"):
	""" Give the lines to be printed as a list, set the font and grey level """
        c = self.canvas
        self.fontsize = fontsize
        if style == "center":
            self.x = self.width / 2
        if seek > (self.width-(self.marginsides + self.fontsize)):
            seek = 0
        if seek != 0:
            self.x = self.x + seek
        if continuetext == 1:
            self.x = self.lastx + seek
            if seek == 0:
                self.y = self.y + fontsize
        for line in lines:
            if style == "center":
                self.x = self.x - (len(line)) * self.fontsize / 2
            if style == "right":
                self.x = self.width - (self.marginsides + len(line) * self.fontsize)
            if (self.width - self.marginsides - self.lastx) < 200:
                self.x = self.marginsides
                if continuetext == 1:
                    self.y = self.y - 2 * fontsize
            if (self.y - self.fontsize) < 50:
                self.set_new_page()
            t = c.beginText(self.x, self.y)
            t.setFont(Helvetica, fontsize)
            t.setFillGray(gray)
            t.textOut(line)
            c.drawText(t)
	    self.y = self.y - fontsize
	    self.lastx = t.getX()
            self.lasty = self.y
        self.x = self.marginsides

    def draw_check_boxes(self, boxes=1, completeline=0, lines=0, seek=0, continuetext=0, fontsize=0, gray=0, style="", isdate=0):
	""" Function to draw check boxes default no of boxes = 1 """
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
        if continuetext == 1:
            self.y = self.y + self.fontsize
            self.x = self.lastx
        else:
            self.x = self.marginsides
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
        self.x = self.marginsides
        self.y = self.y - self.fontsize
        if isdate:
            t = c.beginText(self.x, self.y)
            t.setFont(Helvetica, 13)
            t.setFillGray(0)
            t.textOut("   D  D  M  M  Y  Y  Y  Y")
            c.drawText(t)
            self.y = self.y - fontsize
            self.lastx = t.getX()
            self.lasty = self.y
        self.lastx = self.x
        self.x = self.marginsides
        self.y = self.y - 13

    def draw_circle(self, boxes=1, completeline=0, lines=0, seek=0, continuetext=0, fontsize=0, gray=0, style=""):
        """ Draw circles on the form """
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
        if continuetext == 1:
            self.y = self.y + self.fontsize
            self.x = self.lastx
        else:
            self.x = self.marginsides
        if seek != 0:
            self.x = self.x + seek
        if fontsize == 0:
            fontsize = self.fontsize
        else:
            self.fontsize = fontsize
        if completeline == 1:
            boxes = int(self.width / self.fontsize)
        for i in range(boxes):
            c.circle(self.x + self.fontsize/2, self.y+self.fontsize/2, self.fontsize/2, fill = 0)
            self.x = self.x + self.fontsize
            if self.x > (self.width - (self.marginsides + self.fontsize)):
                break
        self.lastx = self.x
        self.x = self.marginsides
        self.y = self.y - self.fontsize

    def draw_line(self, gray=0):
	""" Function to draw a straight line """
        c = self.canvas
        c.setStrokeGray(gray)
        c.setLineWidth(0.40)
        self.y = self.y - (self.fontsize)
        c.line(self.x, self.y, self.width - self.x, self.y)
        self.y = self.y - (self.fontsize)

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
        self.print_text([str("Page "+ str(self.num))], fontsize=8, style="right")
        self.x = self.marginsides
        self.lastx = self.x
        self.y = self.y - 32

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

    def xmlcreate(self):
        """ Creates the xml """
        self.doc = Document()
        self.xmltitle = str(self.uuid) + "_" + self.lang + "_" + str(self.page) + ".xml"
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
                self.form.print_text(["", "", str(" Multiple select: "), ""], fontsize=10, gray=0)
                self.multiple = 1
            else:
                self.form.print_text(["", "", str("Single select: "), ""], fontsize=10, gray=0)
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
                self.form.print_text([unicode(self.printtext)], fontsize=18, style="center")
                #self.form.print_text([str(self.title)], fontsize=18, style="center")
                self.form.print_text([str("1. Fill the necessary fields in BLOCK CAPITAL letters."), str("2. Always use one box per letter and leave one box space to separate words."), str("3. Fill in the circles completely.")], fontsize=13, gray=0)
                self.form.draw_line()
                # self.form.print_text([str(self.uuid)], fontsize=10, gray=0)
        elif name == "input":
            self.input = 0
            #self.protectedfield = 0
            self.type = ""
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
                self.form.print_text([" ", " " + unicode(self.printtext) + " ", " "])
                self.child3 = self.doc.createTextNode(str(self.form.lastx) + "," + str(self.form.lasty))
                self.child2.appendChild(self.child3)
                self.child2.setAttribute("font", str(16))
                if self.ref == "age":
                    self.form.draw_check_boxes(boxes=2, completeline=0, continuetext=0, gray=0.9, fontsize=16, seek=10)
                    self.child2.setAttribute("boxes", str(2))
                elif self.type == "date":
                    self.form.draw_check_boxes(boxes=8, completeline=0, continuetext=0, gray=0.9, fontsize=16, seek=10, isdate=1)
                    self.child2.setAttribute("boxes", str(8))
                elif self.type == "int":
                    count = (self.form.width - 2 * self.form.marginsides) / 32
                    self.form.draw_check_boxes(boxes=1, completeline=1, continuetext=0, gray=0.9, fontsize=16, seek=10)
                    self.child2.setAttribute("boxes", str(count))
                elif self.type == "text":
                    count = (self.form.width - 2 * self.form.marginsides) / 16
                    self.child2.setAttribute("boxes", str(int(count)))
                    self.child2.setAttribute("lines", "4")
                    for i in xrange(4):
                        self.form.draw_check_boxes(boxes=1, completeline=1, continuetext=0, gray=0.9, fontsize=16, seek=10)
                else:
                    if not str(self.ref).find("/") == -1:
                        ref = str(self.ref).split("/")[-1]
                        if ref in self.customfields.keys():
                            numlines = self.customfields[ref]
                        else:
                            numlines = 1
                    count = (self.form.width - 2 * self.form.marginsides) / 16
                    self.child2.setAttribute("boxes", str(int(count)))
                    self.child2.setAttribute("lines", str(numlines))
                    for i in xrange(numlines):
                        self.form.draw_check_boxes(boxes=1, completeline=1, continuetext=0, gray=0.9, fontsize=16, seek=10)
            elif self.item == 1 and self.select == 1:
                labelid, labeltype = self.labelref.split("'")[1].split("&")[0].split(":")
                for trtuple in self.translist:
                    if trtuple[0] == labelid and trtuple[1] == labeltype:
                        self.printtext = trtuple[2]
                if self.printtext != "None" and self.printtext != "Unknown":
                    self.form.print_text(["     " + self.printtext], continuetext = 1)
                    x = self.form.lastx
                    y = self.form.lasty
                    self.form.draw_circle(boxes=1, continuetext=1, gray=0.9, fontsize=12, seek=10)
                    self.labelTrans = "Trans"
                else:
                    self.labelTrans = "NoTrans"
            elif self.read == 1 and self.select == 1:
                labelid, labeltype = self.labelref.split("'")[1].split("&")[0].split(":")
                for trtuple in self.translist:
                    if trtuple[0] == labelid and trtuple[1] == labeltype:
                        self.printtext = trtuple[2]
                self.form.print_text([" " + str(self.printtext) + " ", " ", " "])
                self.read = 0
            self.label= 0
            self.labelref = ""
            labelid, labeltype = ["", ""]
            trtuple = ("", "", "")
            self.printtext = ""
        elif name == "value":
            self.value = 0
            if self.select == 1:
                self.child3 = self.doc.createTextNode(str(self.form.lastx - 12) + "," + str(self.form.lasty))
                self.child2.appendChild(self.child3)
                self.child2.setAttribute("value", str(self.value_ch))
                self.child2.setAttribute("font", str(12))
                self.child2.setAttribute("boxes", str(1))
                if self.item == 1 and self.labelTrans == "NoTrans":
                    self.printtext = str(self.value_ch)
                    self.form.print_text(["     " + self.printtext], continuetext = 1)
                    x = self.form.lastx
                    y = self.form.lasty
                    self.form.draw_circle(boxes=1, continuetext=1, gray=0.9, fontsize=12, seek=10)
                    self.labelTrans == ""
            if self.itext == 1 and self.translation == 1 and self.text == 1 and self.translang == self.lang:
                self.translist.append((self.textid, self.texttype, unicode(self.value_ch)))
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
                self.form.print_text([" " + str(self.printtext) + " ", " ", " "], fontsize=10)
            self.hint = 0
        elif name == "html":
            self.translist = [] # clearing the translation mapping
            #print "End, saving with the filename "+str(self.form.pdfpath)
            self.xmlsave()
            self.pdf = self.form.save()
        self.title = ""

    def get_files(self):
        """ Returns pdf text and layout xml text as dict """
        return self.pdf, self.xmls


#== xml.sax.ContentHandler instance to find available languages in xform ==

class LangHandler(ContentHandler):
    """ To retrieve list of available languages """

    def __init__(self):
        """ Form initialization and preparation"""
        self.itext = 0
        self.translation = 0
        self.lang = []

    def startElement(self, name, attrs):
        """ Parses the starting element and then check what to read """
        if not str(name).find(":") == -1:
            name = name.split(":")[1]
        if name == "translation":
            if self.translation == 0 and self.itext == 1:
                self.translation= 1
                self.lang.append(str(attrs.get("lang")))
        elif name == "itext":
            self.itext = 1

    def endElement(self, name):
        """ It specifies the operations to do on closing the element """
        if not str(name).find(":") == -1:
            name = name.split(":")[1]
        if name == "translation":
            self.translation = 0
        elif name == "itext":
            self.itext = 0

    def get_lang(self):
        """ Return list of available languages in the xform """
        return self.lang


def _open_anything(source):
    """ Read anything link/file/string """
    import urllib
    try:
        return urllib.urlopen(source)
    except (IOError, OSError):
        pass
    try:
        return open(source, "r")
    except (IOError, OSError):
        pass
    return StringIO.StringIO(str(source))


#==========================================================================
#================================= OCR API ================================
#==========================================================================

def s3ocr_generate_pdf(xform, pdflang):
    """ Generates pdf/xml files out of xform with language support """
    uid = uuid.uuid1()
    pdfs = {}
    xmls = {}
    form = Form(pdfname = str(uid) + ".pdf")
    formhandler = FormHandler(form, uid, pdflang)
    saxparser = make_parser()
    saxparser.setContentHandler(formhandler)
    datasource = _open_anything(xform)
    saxparser.parse(datasource)
    pdf, xmls = formhandler.get_files()
    pdfs[str(uid) + "_" + str(pdflang) + ".pdf"] = pdf
    return pdfs, xmls


def s3ocr_get_languages(xform):
    """ Shows the languages supported by given xform """
    formhandler = LangHandler()
    saxparser = make_parser()
    saxparser.setContentHandler(formhandler)
    datasource = _open_anything(xform)
    saxparser.parse(datasource)
    langlist = formhandler.get_lang()
    return langlist


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit("Usage: python xforms2pdf.py filename.xml language")
    xform = sys.argv[1]
    if len(sys.argv) < 3:
        lang = "eng"
    else:
        lang = str(sys.argv[2])
        avail_langs = s3ocr_get_languages(xform)
        if lang not in avail_langs:
            sys.exit("Required Language '"+\
                         lang+\
                         "' is not available, available languages are:\n" + str(avail_langs))
    pdfs, xmls = s3ocr_generate_pdf(xform, "eng")
    for i in pdfs.keys():
            f = open(i, "w")
            f.write(pdfs[i])
            f.close()
    for i in xmls.keys():
            f = open(i, "w")
            f.write(xmls[i])
            f.close()
