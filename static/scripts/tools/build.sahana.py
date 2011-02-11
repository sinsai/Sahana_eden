#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Built with code/inspiration from MapFish, OpenLayers & Michael Crute
#

import sys
sys.path.append("./")

# For JS
import getopt
import jsmin, mergejs

# For CSS
import re

# For file moves
import shutil
import os

def mergeCSS(inputFilenames, outputFilename):
    output = ""
    for inputFilename in inputFilenames:
        output += file(inputFilename, "r").read()
    file(outputFilename, "w").write(output)
    return outputFilename

def cleanline(theLine):
    """ Kills line breaks, tabs, and double spaces """
    p = re.compile("(\n|\r|\t|\f|\v)+")
    m = p.sub("", theLine)

    # Kills double spaces
    p = re.compile("(  )+")
    m = p.sub(" ", m)

    # Removes last semicolon before }
    p = re.compile("(; }|;})+")
    m = p.sub("}", m)

    # Removes space before {
    p = re.compile("({ )+")
    m = p.sub("{", m)

    # Removes all comments
    p = re.compile("/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/")
    m = p.sub("", m)

    # Strip off the Charset
    p = re.compile("@CHARSET .*;")
    m = p.sub("", m)

    # Strip spaces before the {
    p = re.compile(" {")
    m = p.sub("{", m)

    # Strip space after :
    p = re.compile(": ")
    m = p.sub(":", m)

    # Strip space after ,
    p = re.compile(", ")
    m = p.sub(",", m)

    # Strip space after ;
    p = re.compile("; ")
    m = p.sub(";", m)

    return m

def compressCSS(inputFilename, outputFilename):
    theFile = file(inputFilename, "r").read()
    output = ""
    for line in theFile:
        output = output + cleanline(line)

    # Once more, clean the entire file string
    _output = cleanline(output)

    file(outputFilename, "w").write(_output)
    return

mfbase = "../../mfbase"

def dojs(dogis = False):
    """ Minifies the js """
    # Define which files we want to include
    # also need to amend sahana.js.cfg
    configDictCore = {
        "web2py":                       "..",
        "T2":                           "..",
        "S3":                           ".."
    }

    configFilename = "sahana.js.cfg"
    outputFilename = "S3.min.js"

    # Merge JS files
    print "Merging Core libraries."
    (files, order) = mergejs.getFiles(configDictCore, configFilename)
    merged = mergejs.run(files, order)

    # Compress JS files
    print "Compressing - JS"
    minimized = jsmin.jsmin(merged)

    # Add license
    print "Adding license file."
    minimized = file("license.txt").read() + minimized

    # Print to output files
    print "Writing to %s." % outputFilename
    file(outputFilename, "w").write(minimized)

    # Remove old JS files
    print "Deleting %s." % outputFilename
    try:
        os.remove("../S3/%s" % outputFilename)
    except:
        pass

    # Move new JS files
    print "Moving new JS files"
    shutil.move("S3.min.js", "../S3")

    if dogis:

        # also need to amend sahana.js.gis.cfg
        configDictGIS = {
            "gis":                          ".."
        }
        configDictOpenLayers = {
            "OpenLayers.js":            "../gis/openlayers/lib",
            "OpenLayers":               "../gis/openlayers/lib",
            "Rico":                     "../gis/openlayers/lib",
            "Gears":                    "../gis/openlayers/lib"
        }
        configDictGeoExt = {
            "GeoExt.js":                "../gis/GeoExt/lib",
            "GeoExt":                   "../gis/GeoExt/lib",
            "ux":                       "../gis/GeoExt"
        }
        configDictGxp = {
            "gxp":                      "../gis",
            "data":                     "../gis/gxp",
            "menu":                     "../gis/gxp",
            "plugins":                  "../gis/gxp",
            "widgets":                  "../gis/gxp"
        }
        configDictGeoExplorer = {
            "GeoExplorer.js":           "../gis/GeoExplorer",
            "GeoExplorer":              "../gis/GeoExplorer"
        }
        configDictGlobalGIS = {}
        configDictGlobalGIS.update(configDictOpenLayers)
        configDictGlobalGIS.update(configDictGIS)
        configFilenameGIS = "sahana.js.gis.cfg"
        configFilenameGeoExt = "sahana.js.geoext.cfg"
        configFilenameGxp = "sahana.js.gxp.cfg"
        configFilenameGeoExplorer = "sahana.js.geoexplorer.cfg"
        outputFilenameGIS = "OpenLayers.js"
        outputFilenameGeoExt = "GeoExt.js"
        outputFilenameGxp = "gxp.js"
        outputFilenameGeoExplorer = "GeoExplorer.js"
        
        # Merge GIS JS Files
        print "Merging GIS libraries."
        (files, order) = mergejs.getFiles(configDictGlobalGIS, configFilenameGIS)
        mergedGIS = mergejs.run(files, order)

        print "Merging GeoExt libraries."
        (files, order) = mergejs.getFiles(configDictGeoExt, configFilenameGeoExt)
        mergedGeoExt = mergejs.run(files, order)

        print "Merging gxp libraries."
        (files, order) = mergejs.getFiles(configDictGxp, configFilenameGxp)
        mergedGxp = mergejs.run(files, order)

        print "Merging GeoExplorer libraries."
        (files, order) = mergejs.getFiles(configDictGeoExplorer, configFilenameGeoExplorer)
        mergedGeoExplorer = mergejs.run(files, order)

        # Compress JS files
        print "Compressing - GIS JS"
        minimizedGIS = jsmin.jsmin(mergedGIS)

        print "Compressing - GeoExt JS"
        minimizedGeoExt = jsmin.jsmin(mergedGeoExt)

        print "Compressing - gxp JS"
        minimizedGxp = jsmin.jsmin(mergedGxp)

        print "Compressing - GeoExplorer JS"
        minimizedGeoExplorer = jsmin.jsmin(mergedGeoExplorer)

        # Add license
        minimizedGIS = file("license.gis.txt").read() + minimizedGIS

        # Print to output files
        print "Writing to %s." % outputFilenameGIS
        file(outputFilenameGIS, "w").write(minimizedGIS)

        print "Writing to %s." % outputFilenameGeoExt
        file(outputFilenameGeoExt, "w").write(minimizedGeoExt)

        print "Writing to %s." % outputFilenameGxp
        file(outputFilenameGxp, "w").write(minimizedGxp)

        print "Writing to %s." % outputFilenameGeoExplorer
        file(outputFilenameGeoExplorer, "w").write(minimizedGeoExplorer)

        # Move new JS files
        print "Deleting %s." % outputFilenameGIS
        try:
            os.remove("../gis/%s" % outputFilenameGIS)
        except:
            pass
        print "Moving new GIS JS files"
        shutil.move("OpenLayers.js", "../gis")
        
        print "Deleting %s." % outputFilenameGeoExt
        try:
            os.remove("../gis/%s" % outputFilenameGeoExt)
        except:
            pass
        print "Moving new GeoExt JS files"
        shutil.move("GeoExt.js", "../gis")

        print "Deleting %s." % outputFilenameGxp
        try:
            os.remove("../gis/%s" % outputFilenameGxp)
        except:
            pass
        print "Moving new gxp JS files"
        shutil.move("gxp.js", "../gis")
        
        print "Deleting %s." % outputFilenameGeoExplorer
        try:
            os.remove("../gis/%s" % outputFilenameGeoExplorer)
        except:
            pass
        print "Moving new GeoExplorer JS files"
        shutil.move("GeoExplorer.js", "../gis")

def docss():
    """ Compresses the  CSS files """
    listCSS = []
    
    f = open("sahana.css.cfg" % scripts_dir_path, 'r')
    files = f.readlines()
    f.close()    
    for file in files:
        listCSS.append("../../styles/%s" % file)

    outputFilenameCSS = "sahana.min.css"

    # Merge CSS files
    print "Merging Core styles."
    mergedCSS = mergeCSS(listCSS, outputFilenameCSS)

    # Compress CSS files
    print "Writing to %s." % outputFilenameCSS
    compressCSS(mergedCSS, outputFilenameCSS)

    # Move files to correct locations
    print "Deleting %s." % outputFilenameCSS
    try:
        os.remove("../../styles/S3/%s" % outputFilenameCSS)
    except:
        pass
    print "Deleting %s." % outputFilenameCSS
    shutil.move(outputFilenameCSS, "../../styles/S3")

def main(argv):
    try:
        parameter1 = argv[0]
    except:
        parameter1 = "ALL"

    try:
        if(argv[1] == "DOGIS"):
            parameter2 = True
        else:
            parameter2 = False

    except:
        parameter2 = True

    if parameter1 == "ALL":
        dojs()
        docss()
    else:
        if parameter1 == "CSS":
            docss(parameter2)
        else:
            dojs(parameter2)
    print "Done."

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
