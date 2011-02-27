# -*- coding: utf-8 -*-

"""
    OCR Utility Functions

    @author: Shiv Deepak <idlecool@gmail.com>
"""


# Store ocr metadata into the database
#def shn_ocr_store_metadata(source, filename, comment):
#    module = "doc"
#    resourcename = "document"
#    tablename = "%s_%s" % (module, resourcename)
#    stream = StringIO(source)
#    db[tablename].insert(name=filename,\
#                             file=db[tablename].file.store(stream,\
#                                                               filename),\
#                             comments=comment,\
#                             )
#    stream.close()


def shn_ocr_downloadpdf(tablename):
    """ Generate 'Print PDF' button in the view """

    try:
        formelements = []
        pdfenable = 1 # enable downloadpdf button if xform is available
        directprint = 0 # create prompt for multi-language selection

        # Get the list of languages
        # Function currently fails with tablename = project_project or project_activity
        #formelementsls = s3base.s3ocr_get_languages("%s/%s/xforms/create/%s" % (deployment_settings.base.public_url,
        #                                                                        request.application,
        #                                                                        tablename))
        #try:
        #    formelementsls.remove("eng") # avoid duplicating stuff
        #except(ValueError):
        #    pass
        # Hard-code list for now
        #formelementsls = ["en", "es"]
        formelementsls = [response.s3.language]

        if len(formelementsls) == 0:
            pdfenable = 0
        if len(formelementsls) == 1:
            directprint = 1
        if not directprint:
            for eachelement in formelementsls:
                eachelement = str(eachelement)
                l10nlang = s3.l10n_languages[eachelement].read()
                formelements.append(DIV(LABEL(l10nlang,
                                              _class="x-form-item-label"),
                                        DIV(INPUT(_name="pdfLangRadio",
                                                  _value=eachelement,
                                                  _type="radio",
                                                  _class="x-form-text x-form-field"),
                                            _class="x-form-element"),
                                        _class="x-form-item",
                                        _tabindex="-1",
                                        _style="height: 25px;"))
                htmlform = DIV(DIV(T("Select Language"),
                                   _id="formheader",
                                   _class="x-panel-header"),
                               FORM(formelements,
                                    _id="download-pdf-form",
                                    _class="x-panel-body x-form",
                                    _action=URL("ocr",
                                                "getpdf/%s" % tablename),
                                    _method="GET",
                                    _name="pdfLangForm"),
                               _id="download-pdf-form-div",
                               _class="x-panel")

                # download pdf button / ext x-window -----------------------
                downloadpdfbtn = DIV(A(IMG(_src="/%s/static/img/pdficon_small.gif" % request.application,
                                           _alt=T("Download PDF")),
                                           _id="download-pdf-btn",
                                           _title=T("Download PDF")),
                                       _style="height: 10px; text-align: right;")
                xwindowtitle = DIV(T("Download PDF"),
                                   _class="x-hidden",
                                   _id="download-pdf-window-title")
                xwindowscript = SCRIPT(_type="text/javascript",
                                       _src=URL(request.application,
                                                "static",
                                                "scripts/S3/s3.ocr.downloadpdf.js"))

                # multiplexing the output ----------------------------------
                output = DIV(downloadpdfbtn,
                             DIV(xwindowtitle,
                                 htmlform,
                                 _class="x-hidden"),
                             xwindowscript,
                             _id="s3ocr-printpdf")
        if not pdfenable:
            output = ""
        if directprint:
            output = DIV(A(IMG(_src="/%s/static/img/pdficon_small.gif" % request.application,
                               _alt=T("Download PDF")),
                           _id="download-pdf-btn",
                           _title=T("Download PDF"),
                           _href=URL(request.controller, "%s/xforms.pdf" % request.function)),
                         _style="height: 10px; text-align: right;")
    except(AttributeError):
        output = ""
    return output
