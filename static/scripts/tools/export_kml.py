#!/usr/bin/env python

# Needs to be run in the web2py environment
# python web2py.py -S eden -M -R applications/eden/static/scripts/tools/export_kml.py

resource = s3xrc.define_resource("cr","shelter")
stylesheet = os.path.join(request.folder, resource.XSLT_PATH, "kml", "export.xsl")
output = resource.export_xml(stylesheet=stylesheet, pretty_print=True)

outfile = os.path.join(request.folder, 'static', "kml", "shelter.kml")
f=open(outfile, "w")
f.write(output)
f.close()

resource = s3xrc.define_resource("hms","hospital")
output = resource.export_xml(stylesheet=stylesheet, pretty_print=True)

outfile = os.path.join(request.folder, 'static', "kml", "hospital.kml")
f=open(outfile, "w")
f.write(output)
f.close()

