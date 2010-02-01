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

SHAPELY = False
try:
    import shapely
    SHAPELY = True
except ImportError:
    print >> sys.stderr, "WARNING: %s: shapely gis library not instsalled" % __name__

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

# Map WKT types to db types (multi- geometry types are mapped to single types)
GEOM_TYPES = {
    "point": 1,
    "multipoint": 1,
    "linestring": 2,
    "multilinestring": 2,
    "polygon": 3,
    "multipolygon": 3,
}

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

    def bbox_intersects(self, lon_min, lat_min, lon_max, lat_max):
        return db((db.gis_location.lat_min < lat_max) & 
            (db.gis_location.lat_max > lat_min) &
            (db.gis_location.lon_min < lon_max) & 
            (db.gis_location.lon_max > lon_min))

    def _intersects(self, shape):
        "Returns a generator of locations whose shape intersects the given shape"
        for loc in self.bbox_intersects(*shape.bounds).select():
            location_shape = shapely.wkt.loads(loc.wkt)
            if location_shape.intersects(shape):
                yield loc
    
    def _intersects_latlon(self, lat, lon):
        "Returns a generator of locations whose shape intersects the given lat,lon"    
        point = shapely.geometry.point.Point(lon, lat)
        return self.intersects(point)
    
    if SHAPELY:
        intersects = _intersects
        intersects_latlon = _intersects_latlon 
    
    def parse_location(self, wkt, lon=None, lat=None):
        """Parses a location from wkt, returning wkt, lat, lon, bounding box and type.
            For points, wkt may be None if lat and lon are provided; wkt will be generated.
            For lines and polygons, the lat, lon returned represent the shape's centroid.
            Centroid and bounding box will be None if shapely is not available.
        """
        if not wkt:
            assert lon is not None and lat is not None, "Need wkt or lon+lat to parse a location"
            wkt = 'POINT(%f %f)' % (lon, lat)
            geom_type = GEOM_TYPES['point']
            bbox = (lon, lat, lon, lat)
        else:
            if SHAPELY:
                shape = shapely.wkt.loads(wkt)
                centroid = shape.centroid
                lat = centroid.y
                lon = centroid.x
                geom_type = GEOM_TYPES[shape.type.lower()]
                bbox = shape.bounds
            else:
                lat = None
                lon = None
                geom_type = GEOM_TYPES[wkt.split('(')[0].lower()]
                bbox = None
                
        res = {'wkt': wkt, 'lat': lat, 'lon': lon, 'gis_feature_type': geom_type}
        if bbox:
            res['lon_min'], res['lat_min'], res['lon_max'], res['lat_max'] = bbox
        return res

