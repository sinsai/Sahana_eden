#!/usr/bin/python

from xml.sax import saxutils, make_parser
from xml.sax.handler import feature_namespaces
import sys
import shutil
import os

try:
    from fontTools import ttx
except(ImportError):
    print >>sys.stderr, "fontTools need to be installed"
    print >>sys.stderr, "you can grab the latest version from http://fonttools.sourceforge.net"
    print >>sys.stderr, "the script is exiting due to unavailable modules"
    exit()

class GetMappings(saxutils.DefaultHandler):
    def __init__(self):
        self.cmap_format_4 = 0
        self.cmap = 0
        self.charmap = []
        self.charrange = []

    def startElement(self, name, attrs):
        if name == "cmap_format_4" \
                and attrs.get("platformID") == "3":
            self.cmap_format_4 = 1
        elif name == "cmap":
            self.cmap = 1
        elif name == "map":
            if self.cmap == 1 \
                    and self.cmap_format_4 == 1:
                self.charmap.append(int(attrs.get("code"), 0))

    def endElement(self, name):
        if name == "cmap_format_4":
            self.cmap_format_4 = 0
        elif name == "cmap":
            self.cmap = 0

    def maprange(self):
        lowindex = 0
        for index in xrange(len(self.charmap)):
            if index != 0:
                if (self.charmap[index]-1) == self.charmap[index-1]:
                    pass
                else:
                    highindex = index - 1
                    self.charrange.append((self.charmap[lowindex], self.charmap[highindex]+1))
                    lowindex = index
            if index == (len(self.charmap)-1):
                highindex = index
                self.charrange.append((self.charmap[lowindex], self.charmap[highindex]))

    def printme(self, filename):
        #print self.charmap
        #fileobj = open("mappings.txt", "w")
        #for eca in self.charmap:
        #    fileobj.write(str(eca))
        #    fileobj.write("\n")
        #fileobj.close()

        fileobj = open("maprange-%s.txt" % filename, "w")
        for eca in self.charrange:
            fileobj.write("(%s, %s)," % (str(eca[0]), str(eca[1])))
            fileobj.write("\n")
        fileobj.close()
        print >>sys.stderr, "The Mapping has been saved to maprange-%s.txt" % filename
            

if __name__ == '__main__':
    filepath = sys.argv[1]
    print filepath
    filedir, filename = os.path.split(filepath)
    fileext = filename.split(".")[-1]
    filename  = filename.split(".")
    filename.pop(-1)
    filename  = ".".join(filename)
    try:
        if fileext != "ttf":
            print >>sys.stderr, "Given file is not a ttf file"
            exit()
    except(IndexError):
        print >>sys.stderr, "You should provide a ttf file as first argument"
        exit()
    ttx.main([filepath, ])
    ttxfilepath = os.path.join(filedir, "%s.ttx" % filename)
    parser = make_parser()
    parser.setFeature(feature_namespaces, 0)
    dh = GetMappings()
    parser.setContentHandler(dh)
    fontttx = open(ttxfilepath)
    parser.parse(fontttx)
    fontttx.close()
    os.remove(ttxfilepath)
    dh.maprange()
    dh.printme(filename)
