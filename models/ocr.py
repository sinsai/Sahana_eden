# -*- coding: utf-8 -*-

""" OCR Utility Functions

    @author: Shiv Deepak <idlecool@gmail.com>

"""

# store ocr metadata into the database
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


def s3ocr_downloadpdf(tablename):
    """ function which generate print pdf button on the view """
    ################# create lang selection form ###########################
    formelements = []
    pdfenable = 1 # enable downloadpdf button if corresponding xform is available
    directprint = 0 # create prompt for language selection if more than one language is present
    formelementsls = s3base.s3ocr_get_languages(deployment_settings.base.public_url+"/eden/xforms/create/"+tablename)
    #formelementsls = ["eng","esp"] #for testing
    if len(formelementsls) == 0:
        pdfenable = 0
    if len(formelementsls) == 1:
        directprint = 1
    if not directprint:
        for eachelement in formelementsls:
            eachelement = str(eachelement)
            formelements.append(DIV(LABEL(eachelement,_class="x-form-item-label"),\
                                        DIV(INPUT(_name="pdfLangRadio",_value=eachelement,_type="radio",_class="x-form-text x-form-field")\
                                                ,_class="x-form-element"),
                                    _class="x-form-item",_tabindex="-1"))
            htmlform = DIV(DIV(T("Select Language"),_id="formheader",_class="x-panel-header"),\
                               FORM(formelements,\
                                        _id="download-pdf-form", _class="x-panel-body x-form", _action=URL("ocr","getpdf/"+tablename), _method="GET", _name="pdfLangForm"),\
                               _id="download-pdf-form-div", _class="x-panel")

            ################ download pdf button / ext x-window ####################
            downloadpdfbtn = A(T("Download PDF"),_class="action-btn",_id="download-pdf-btn") 
            xwindowtitle  = DIV(T("Download PDF"),_class="x-hidden",_id="download-pdf-window-title")
            xwindowscript = SCRIPT(_type="text/javascript",_src=URL(request.application,'static','scripts/S3/s3.ocr.downloadpdf.js'))
    
            ################## multiplexing the output #############################
            output = DIV(downloadpdfbtn, DIV(xwindowtitle, htmlform,_class="x-hidden"), xwindowscript, _id="s3ocr-printpdf")
    if not pdfenable:
        output = ''
    if directprint:
        output = A(T("Download PDF"),_class="action-btn",_id="download-pdf-btn",_href=URL("ocr","getpdf/"+tablename)) 
    return output
