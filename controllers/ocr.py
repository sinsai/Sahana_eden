# -*- coding: utf-8 -*-

"""
    OCR - Controllers
"""


import StringIO


def getpdf():
    """
    Function to create OCRforms from the tables

    """
    if len(request.args) == 0:
        session.error = T("Need to specify a table!")
        redirect(URL(r=request))
    tablename = request.args(0)
    lang = request.vars.get("pdfLangRadio", "eng")
    try:
        langlist = s3base.s3ocr_get_languages(deployment_settings.base.public_url+\
                                                  "/eden/xforms/create/"+\
                                                  tablename)
    except:
        raise HTTP(404, body="S3 installaton error, reportlab has not been installed")
    if len(langlist)==0:
        raise HTTP(404, body="%s xform is not yet available" % (tablename))
    if lang not in langlist:
        if lang=="":
            raise HTTP(404, body="You have to specify a language")
        else:
            raise HTTP(404, body="Sorry, %s language is not supported till now" % (lang))
    output = StringIO.StringIO()
    try:
        pdfs, xmls = s3base.s3ocr_generate_pdf(deployment_settings.base.public_url+\
                                                   "/eden/xforms/create/"+\
                                                   tablename,\
                                                   "eng")
    except:
        raise HTTP(404, body="S3 installaton error, reportlab has not been installed")
    for i in pdfs.keys():
        pdfname = i
        pdfcontent = pdfs[i]
    output.write(pdfcontent)
    output.seek(0)
    import gluon.contenttype
    response.headers["Content-Type"] = gluon.contenttype.contenttype(".pdf")
    #filename = str(pdfname)
    filename = str(tablename+"_"+lang+".pdf")
    response.headers["Content-disposition"] = "attachment; filename=\"%s\"" % filename
    return output.read()
