#!/usr/bin/env python

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

# Define which files we want to include
# also need to amend sahana.js.cfg
configDictCore = {
    'web2py':                       '..',
    'T2':                           '..',
    'S3':                           '..'
}

# also need to amend sahana.js.gis.cfg
mfbase = '../../mfbase'
configDictOpenLayers = {
    'OpenLayers.js':                mfbase+'/openlayers/lib',
    'OpenLayers':                   mfbase+'/openlayers/lib',
    'Rico':                         mfbase+'/openlayers/lib',
    'GoogleGears':                  mfbase+'/openlayers/lib'
}
configDictMapFish = {
    'SingleFile.js':                mfbase+'/mapfish',
    'MapFish.js':                   mfbase+'/mapfish',
    'widgets':                      mfbase+'/mapfish',
    'core':                         mfbase+'/mapfish',
    'lang':                         mfbase+'/mapfish'
}
configDictGIS = {
    'gis':                          '..'
}
configDictGlobalGIS = {}
configDictGlobalGIS.update(configDictOpenLayers)
configDictGlobalGIS.update(configDictMapFish)
configDictGlobalGIS.update(configDictGIS)

listCSS = [
    '../../styles/S3/sahana.css',
    '../../styles/S3/jquery.autocomplete.css',
    '../../styles/S3/jquery.cluetip.css',
    '../../styles/S3/jquery.dataTables.css',
    '../../styles/T2/t2.css',
    '../../styles/web2py/calendar.css'
]

listCSSGIS = [
    '../../styles/gis/gis.css',
    '../../styles/gis/mapfish.css',
    #mfbase+'/ext/resources/css/ext-all.css', # would need to copy images if included here
    mfbase+'/openlayers/theme/default/framedCloud.css'
]

configFilename = "sahana.js.cfg"
outputFilename = "S3.min.js"
configFilenameGIS = "sahana.js.gis.cfg"
outputFilenameGIS = "MapFish.min.js"

outputFilenameTmpCSS = "sahana.tmp.css"
outputFilenameCSS = "sahana.min.css"
outputFilenameCSSGIS = "gis.tmp.css"
outputFilenameCSSGIS = "gis.min.css"

# Merge files
print "Merging Core libraries."
(files, order) = mergejs.getFiles(configDictCore, configFilename)
merged = mergejs.run(files, order)
print "Merging GIS libraries."
(files, order) = mergejs.getFiles(configDictGlobalGIS, configFilenameGIS)
mergedGIS = mergejs.run(files, order)

print "Merging Core styles."
mergedCSS = mergeCSS(listCSS, outputFilenameCSS)
print "Merging GIS styles."
mergedCSSGIS = mergeCSS(listCSSGIS, outputFilenameCSSGIS)

# Compress files
print "Compressing."
minimized = jsmin.jsmin(merged)
minimizedGIS = jsmin.jsmin(mergedGIS)
print "Writing to %s." % outputFilenameCSS
compressCSS(mergedCSS,outputFilenameCSS)
print "Writing to %s." % outputFilenameCSSGIS
compressCSS(mergedCSSGIS, outputFilenameCSSGIS)

# Add license
print "Adding license file."
minimized = file("license.txt").read() + minimized
minimizedGIS = file("license.gis.txt").read() + minimizedGIS

# Print to output files
print "Writing to %s." % outputFilename
file(outputFilename, "w").write(minimized)
print "Writing to %s." % outputFilenameGIS
file(outputFilenameGIS, "w").write(minimizedGIS)

# Move files to correct locations
print "Deleting %s." % outputFilename
try:                                            
    os.remove("../S3/%s" % outputFilename)                
except:                                         
    pass
print "Deleting %s." % outputFilenameGIS
try:
    os.remove("../gis/%s" % outputFilenameGIS)
except:
    pass
print "Deleting %s." % outputFilenameCSS
try:
    os.remove("../../styles/S3/%s" % outputFilenameCSS)
except:
    pass
print "Deleting %s." % outputFilenameCSSGIS
try:
    os.remove("../../styles/gis/%s" % outputFilenameCSSGIS)
except:
    pass
print "Moving new files"
shutil.move("S3.min.js","../S3")
shutil.move("MapFish.min.js","../gis")
shutil.move("sahana.min.css","../../styles/S3")
shutil.move("gis.min.css","../../styles/gis")


print "Done."
