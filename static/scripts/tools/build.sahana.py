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
    output = ''
    for inputFilename in inputFilenames:
        output += file(inputFilename, "r").read()
    file(outputFilename, "w").write(output)
    return outputFilename

def cleanline(theLine):
	# Kills line breaks, tabs, and double spaces
	p = re.compile('(\n|\r|\t|\f|\v)+')
	m = p.sub('',theLine)

	# Kills double spaces
	p = re.compile('(  )+')
	m = p.sub(' ',m)

	# Removes last semicolon before }
	p = re.compile('(; }|;})+')
	m = p.sub('}',m)

	# Removes space before {
	p = re.compile('({ )+')
	m = p.sub('{',m)

	# Removes all comments
	p = re.compile('/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/')
	m = p.sub('',m)

	# Strip off the Charset
	p = re.compile('@CHARSET .*;')
	m = p.sub('',m)

	# Strip spaces before the {
	p = re.compile(' {')
	m = p.sub('{',m)

	# Strip space after :
	p = re.compile(': ')
	m = p.sub(':',m)

	# Strip space after ,
	p = re.compile(', ')
	m = p.sub(',',m)

	# Strip space after ;
	p = re.compile('; ')
	m = p.sub(';',m)

	return m

def compressCSS(inputFilename, outputFilename):
    theFile = file(inputFilename, "r").read()
    output = ''
    for line in theFile:
        output = output + cleanline(line)

    # Once more, clean the entire file string
    _output = cleanline(output)

    file(outputFilename, "w").write(_output)
    return

mfbase = '../../mfbase'

def dojs(dogis = False):
    """ Minifies the js"""
    # Define which files we want to include
    # also need to amend sahana.js.cfg
    configDictCore = {
        'web2py':                       '..',
        'T2':                           '..',
        'S3':                           '..'
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
        configDictOpenLayers = {
            'OpenLayers.js':                '../gis/openlayers/lib',
            'OpenLayers':                   '../gis/openlayers/lib',
            'Rico':                         '../gis/openlayers/lib',
            'GoogleGears':                  '../gis/openlayers/lib'
        }
        configDictGIS = {
            'gis':                          '..'
        }
        configDictGlobalGIS = {}
        configDictGlobalGIS.update(configDictOpenLayers)
        configDictGlobalGIS.update(configDictGIS)
        configFilenameGIS = "sahana.js.gis.cfg"
        outputFilenameGIS = "OpenLayers.js"
        #Merge GIS JS Files
        print "Merging GIS libraries."
        (files, order) = mergejs.getFiles(configDictGlobalGIS, configFilenameGIS)
        mergedGIS = mergejs.run(files, order)

        # Compress JS files
        print "Compressing - GIS JS"
        minimizedGIS = jsmin.jsmin(mergedGIS)

        # Add license
        minimizedGIS = file("license.gis.txt").read() + minimizedGIS

        # Print to output files
        print "Writing to %s." % outputFilenameGIS
        file(outputFilenameGIS, "w").write(minimizedGIS)

        # Move new JS files
        print "Deleting %s." % outputFilenameGIS
        try:
            os.remove("../gis/%s" % outputFilenameGIS)
        except:
            pass
        print "Moving new GIS JS files"
        shutil.move("OpenLayers.js", "../gis")

def docss(dogis = True):
    """Compresses the  CSS files"""
    listCSS = [
        '../../styles/S3/sahana.css',
        '../../styles/S3/jquery.autocomplete.css',
        '../../styles/S3/jquery.cluetip.css',
        '../../styles/S3/jquery.dataTables.css',
        '../../styles/S3/ui.core.css',
        '../../styles/S3/ui.datepicker.css',
        '../../styles/S3/ui.theme.css',
        '../../styles/S3/ajaxS3.css',
        '../../styles/T2/t2.css',
        '../../styles/web2py/calendar.css'
    ]
    outputFilenameTmpCSS = "sahana.tmp.css"
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

    shutil.move("sahana.min.css", "../../styles/S3")

    if dogis:
        listCSSGIS = [
            '../../styles/gis/gis.css',
            '../../styles/gis/geoext-all.css',
            #mfbase+'/ext/resources/css/ext-all.css', # would need to copy images if included here
            '../../styles/gis/google.css',
            #'../../styles/gis/style.css',
            '../../styles/gis/ie6-style.css'
        ]
        outputFilenameCSSGIS = "gis.tmp.css"
        outputFilenameCSSGIS = "gis.min.css"
    
        # Merge GIS CSS files
        print "Merging GIS styles."
        mergedCSSGIS = mergeCSS(listCSSGIS, outputFilenameCSSGIS)

        # Compress GIS CSS files
        print "Writing to %s." % outputFilenameCSSGIS
        compressCSS(mergedCSSGIS, outputFilenameCSSGIS)


        # Move files to correct locations
        print "Deleting %s." % outputFilenameCSSGIS
        try:
            os.remove("../../styles/gis/%s" % outputFilenameCSSGIS)
        except:
            pass
        shutil.move("gis.min.css", "../../styles/gis")

def main(argv):
    try:
        parameter1 = argv[0]
    except:
        parameter1 = "ALL"

    try:
        if(argv[1]=="DOGIS"):
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
