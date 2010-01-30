# -*- coding: utf-8 -*-

"""
    SahanaPy GIS Module

    @version: 0.0.1
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @author: flavour
    @copyright: (c) 2010 Fran Boon
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

"""

__name__ = "S3GIS"

__all__ = ['GIS']


#import sys, uuid
#import gluon.contrib.simplejson as json

#from gluon.storage import Storage
#from gluon.html import URL
#from gluon.http import HTTP
#from gluon.validators import IS_NULL_OR

#from xml.etree.cElementTree import ElementTree

NO_SHAPELY = True
#try:
#    from lxml import etree
#    NO_LXML = False
#except ImportError:
#    try:
#        import xml.etree.cElementTree as etree
#        print >> sys.stderr, "WARNING: %s: lxml not installed - using cElementTree" % __name__
#    except ImportError:
#        try:
#            import xml.etree.ElementTree as etree
#            print >> sys.stderr, "WARNING: %s: lxml not installed - using ElementTree" % __name__
#        except ImportError:
#            try:
#                import cElementTree as etree
#                print >> sys.stderr, "WARNING: %s: lxml not installed - using cElementTree" % __name__
#            except ImportError:
#                # normal ElementTree install
#                import elementtree.ElementTree as etree
#                print >> sys.stderr, "WARNING: %s: lxml not installed - using ElementTree" % __name__


# Error messages
S3GIS_BAD_RESOURCE = "Invalid Resource"
S3GIS_DATA_IMPORT_ERROR = "Data Import Error"
S3GIS_NOT_PERMITTED = "Operation Not Permitted"
S3GIS_NOT_IMPLEMENTED = "Not Implemented"

class GIS(object):
    """ GIS functions """

    def __init__(self, db):
        assert db is not None, "Database must not be None."
        self.db = db
        
    def read_config(self):
        """ Reads the current GIS Config from the DB """
        
        db = self.db
                
        config = db(db.gis_config.id == 1).select().first()
        
        return config
        
    def get_marker(self, feature_id):
        """ Returns the Marker URL for a Feature"""

        db = self.db
        
        config = self.read_config()
        symbology = config.symbology_id
        
        feature = db(db.gis_location.id == feature_id).select().first()
        feature_class = db(db.gis_feature_class.id == feature.feature_class_id).select().first().id
        
        # 1st choice for a Marker is the Feature's
        marker = feature.marker_id
        if not marker:
            # 2nd choice for a Marker is the Symbology for the Feature Class
            query = (db.gis_symbology_to_feature_class.feature_class_id == feature_class) & (db.gis_symbology_to_feature_class.symbology_id == symbology)
            try:
                marker = db(query).select().first().marker_id
            except:
                if not marker:
                    # 3rd choice for a Marker is the Feature Class's
                    marker = db(db.gis_feature_class.id == feature_class).select().first().marker_id
                if not marker:
                    # 4th choice for a Marker is the default
                    marker = config.marker_id
        
        marker = db(db.gis_marker.id == marker).select().first().image
        
        return marker
    
    def get_bounds(self):
        """
        Calculate the bounds of a set of features
        e.g. to use in KML export for correct zooming
        """
        # Quick fix is to read from config
        config = self.read_config()
        min_lon = config.min_lon
        min_lat = config.min_lat
        max_lon = config.max_lon
        max_lat = config.max_lat
        
        return dict(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)