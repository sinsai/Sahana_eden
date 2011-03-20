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

def dojs(dogis = False):
    """ Minifies the JavaScript """

    # Do we have local version of the Closure Compiler available?
    use_compressor = "jsmin" # Fallback
    try:
        import closure
        use_compressor = "closure"
        print "using local Closure Compiler"
    except Exception, E:
        print "No closure (%s)" % E
        print "Download from http://closure-compiler.googlecode.com/files/compiler-latest.zip"
        try:
            import closure_ws
            use_compressor = "closure_ws"
            print "Using Closure via Web Service - limited to files < 1Mb!"
        except ImportError:
            print "No closure_ws"
    
    if use_compressor == "closure":
        minimize = closure.minimize
    elif use_compressor == "closure_ws":
        minimize = closure_ws.minimize
    elif use_compressor == "jsmin":
        minimize = jsmin.jsmin

    sourceDirectory = ".."
    configFilename = "sahana.js.cfg"
    outputFilename = "S3.min.js"

    # Merge JS files
    print "Merging Core libraries."
    merged = mergejs.run(sourceDirectory, None, configFilename)

    # Compress JS files
    print "Compressing - JS"
    minimized = minimize(merged)

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
        sourceDirectoryGIS = "../gis"
        sourceDirectoryOpenLayers = "../gis/openlayers/lib"
        sourceDirectoryOpenLayersExten = "../gis"
        sourceDirectoryMGRS = "../gis"
        sourceDirectoryGeoExt = "../gis/GeoExt/lib"
        sourceDirectoryGeoExtux = "../gis/GeoExt/ux"
        sourceDirectoryGxp = "../gis/gxp"
        sourceDirectoryGeoExplorer = "../gis/GeoExplorer"
        configFilenameOpenLayers = "sahana.js.ol.cfg"
        configFilenameGIS = "sahana.js.gis.cfg"
        configFilenameMGRS = "sahana.js.mgrs.cfg"
        configFilenameGeoExt = "sahana.js.geoext.cfg"
        configFilenameGeoExtux = "sahana.js.geoextux.cfg"
        configFilenameGxp = "sahana.js.gxp.cfg"
        configFilenameGeoExplorer = "sahana.js.geoexplorer.cfg"
        outputFilenameGIS = "OpenLayers.js"
        outputFilenameMGRS = "MGRS.min.js"
        outputFilenameGeoExt = "GeoExt.js"
        outputFilenameGxp = "gxp.js"
        outputFilenameGeoExplorer = "GeoExplorer.js"

        # Merge GIS JS Files
        print "Merging OpenLayers libraries."
        mergedOpenLayers = mergejs.run(sourceDirectoryOpenLayers, None, configFilenameOpenLayers)
        mergedGIS = mergejs.run(sourceDirectoryGIS, None, configFilenameGIS)

        print "Merging MGRS libraries."
        mergedMGRS = mergejs.run(sourceDirectoryMGRS, None, configFilenameMGRS)

        print "Merging GeoExt libraries."
        mergedGeoExt = mergejs.run(sourceDirectoryGeoExt, None, configFilenameGeoExt)
        mergedGeoExtux = mergejs.run(sourceDirectoryGeoExtux, None, configFilenameGeoExtux)

        print "Merging gxp libraries."
        mergedGxp = mergejs.run(sourceDirectoryGxp, None, configFilenameGxp)

        print "Merging GeoExplorer libraries."
        mergedGeoExplorer = mergejs.run(sourceDirectoryGeoExplorer, None, configFilenameGeoExplorer)

        
        # Compress JS files
        print "Compressing - GIS JS"
        if use_compressor == "closure_ws":
            # Limited to files < 1Mb!
            minimizedGIS = jsmin.jsmin("%s\n%s" % (mergedOpenLayers, mergedGIS))
        else:
            minimizedGIS = minimize("%s\n%s" % (mergedOpenLayers, mergedGIS))

        print "Compressing - MGRS JS"
        minimizedMGRS = minimize(mergedMGRS)

        print "Compressing - GeoExt JS"
        minimizedGeoExt = minimize("%s\n%s" % (mergedGeoExt, mergedGeoExtux))

        print "Compressing - gxp JS"
        minimizedGxp = minimize(mergedGxp)

        print "Compressing - GeoExplorer JS"
        minimizedGeoExplorer = minimize(mergedGeoExplorer)
            
        # Add license
        minimizedGIS = file("license.gis.txt").read() + minimizedGIS

        # Print to output files
        print "Writing to %s." % outputFilenameGIS
        file(outputFilenameGIS, "w").write(minimizedGIS)

        print "Writing to %s." % outputFilenameMGRS
        file(outputFilenameMGRS, "w").write(minimizedMGRS)

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
        shutil.move(outputFilenameGIS, "../gis")

        print "Deleting %s." % outputFilenameMGRS
        try:
            os.remove("../gis/%s" % outputFilenameMGRS)
        except:
            pass
        print "Moving new MGRS JS files"
        shutil.move(outputFilenameMGRS, "../gis")

        print "Deleting %s." % outputFilenameGeoExt
        try:
            os.remove("../gis/%s" % outputFilenameGeoExt)
        except:
            pass
        print "Moving new GeoExt JS files"
        shutil.move(outputFilenameGeoExt, "../gis")

        print "Deleting %s." % outputFilenameGxp
        try:
            os.remove("../gis/%s" % outputFilenameGxp)
        except:
            pass
        print "Moving new gxp JS files"
        shutil.move(outputFilenameGxp, "../gis")

        print "Deleting %s." % outputFilenameGeoExplorer
        try:
            os.remove("../gis/%s" % outputFilenameGeoExplorer)
        except:
            pass
        print "Moving new GeoExplorer JS files"
        shutil.move(outputFilenameGeoExplorer, "../gis")

def docss():
    """ Compresses the  CSS files """
    listCSS = []

    f = open("sahana.css.cfg", "r")
    files = f.readlines()
    f.close()
    for file in files[:-1]:
        p = re.compile("(\n|\r|\t|\f|\v)+")
        file = p.sub("", file)
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
            docss()
        else:
            dojs(parameter2)
    print "Done."

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
