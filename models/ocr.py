# -*- coding: utf-8 -*-

"""
    OCR Utility Functions

    @author: Shiv Deepak <idlecool@gmail.com>
"""

def shn_ocr_downloadpdf(tablename):
    """ Generate 'Print PDF' button in the view """
    output = DIV(A(IMG(_src="/%s/static/img/pdficon_small.gif" % \
                           request.application,
                       _alt=T("Download PDF")),
                   _id="download-pdf-btn",
                   _title=T("Download PDF"),
                   _href=URL(request.controller,
                             "%s/s3ocr.pdf" % request.function)),
                 _style="height: 10px; text-align: right;")
    return output
