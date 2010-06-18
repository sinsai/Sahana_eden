# -*- coding: utf-8 -*-

"""
    Sahana Eden GIS Module

    @version: 0.0.7
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @author: Fran Boon <francisboon@gmail.com>
    @author: Timothy Caro-Bruce <tcarobruce@gmail.com>
    @author: Zubin Mithra <zubin.mithra@gmail.com>
    @copyright: (c) 2010 Sahana Software Foundation
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

__all__ = ["GIS", "GoogleGeocoder", "YahooGeocoder"]

#import logging
import os
import re
import sys
import urllib           # Needed for urlencoding
import urllib2          # Needed for error handling on fetch
#import uuid
import Cookie           # Needed for Sessions on Internal KML feeds
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
import zipfile          # Needed to unzip KMZ files
from lxml import etree  # Needed to follow NetworkLinks
KML_NAMESPACE = "http://earth.google.com/kml/2.2"

from gluon.storage import Storage, Messages
from gluon.html import *
#from gluon.http import HTTP
from gluon.tools import fetch

SHAPELY = False
try:
    import shapely
    import shapely.geometry
    from shapely.wkt import loads as wkt_loads
    SHAPELY = True
except ImportError:
    print >> sys.stderr, "WARNING: %s: Shapely GIS library not installed" % __name__

# Map WKT types to db types (multi-geometry types are mapped to single types)
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

    def __init__(self, environment, db, auth=None, cache=None):
        self.environment = Storage(environment)
        self.request = self.environment.request
        self.response = self.environment.response
        self.session = self.environment.session
        self.T = self.environment.T
        assert db is not None, "Database must not be None."
        self.db = db
        self.cache = cache and (cache.ram, 60) or None
        assert auth is not None, "Undefined authentication controller"
        self.auth = auth
        self.messages = Messages(None)
        #self.messages.centroid_error = str(A("Shapely", _href="http://pypi.python.org/pypi/Shapely/", _target="_blank")) + " library not found, so can't find centroid!"
        self.messages.centroid_error = "Shapely library not functional, so can't find centroid! Install Geos & Shapely for Line/Polygon support"
        self.messages.unknown_type = "Unknown Type!"
        self.messages.invalid_wkt_linestring = "Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!"
        self.messages.invalid_wkt_polygon = "Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!"
        self.messages.lon_empty = "Invalid: Longitude can't be empty if Latitude specified!"
        self.messages.lat_empty = "Invalid: Latitude can't be empty if Longitude specified!"
        self.messages.unknown_parent = "Invalid: %(parent_id)s is not a known Location"
        self.messages["T"] = self.T
        self.messages.lock_keys = True

    def abbreviate_wkt(self, wkt, max_length=30):
        if not wkt:
            # Blank WKT field
            return None
        elif len(wkt) > max_length:
            return "%s(...)" % wkt[0:wkt.index("(")]
        else:
            return wkt

    def download_kml(self, url, public_url):
        """
        Download a KML file:
            unzip it if-required
            follow NetworkLinks recursively if-required

        Returns a file object
        """

        response = self.response
        session = self.session

        file = ""
        warning = ""

        if len(url) > len(public_url) and url[:len(public_url)] == public_url:
            # Keep Session for local URLs
            cookie = Cookie.SimpleCookie()
            cookie[response.session_id_name] = response.session_id
            session._unlock(response)
            try:
                file = fetch(url, cookie=cookie)
            except urllib2.URLError:
                warning = "URLError"
                return file, warning
            except urllib2.HTTPError:
                warning = "HTTPError"
                return file, warning

        else:
            try:
                file = fetch(url)
            except urllib2.URLError:
                warning = "URLError"
                return file, warning
            except urllib2.HTTPError:
                warning = "HTTPError"
                return file, warning

            if file[:2] == "PK":
                # Unzip
                fp = StringIO(file)
                myfile = zipfile.ZipFile(fp)
                try:
                    file = myfile.read("doc.kml")
                except:
                    file = myfile.read(myfile.infolist()[0].filename)
                myfile.close()

            # Check for NetworkLink
            if "<NetworkLink>" in file:
                # Remove extraneous whitespace
                #file = " ".join(file.split())
                try:
                    parser = etree.XMLParser(recover=True, remove_blank_text=True)
                    tree = etree.XML(file, parser)
                    # Find contents of href tag (must be a better way?)
                    url = ""
                    for element in tree.iter():
                        if element.tag == "{%s}href" % KML_NAMESPACE:
                            url = element.text
                    if url:
                        file, warning2 = self.download_kml(url, public_url)
                        warning += warning2
                except (etree.XMLSyntaxError,):
                    e = sys.exc_info()[1]
                    warning += "<ParseError>%s %s</ParseError>" % (e.line, e.errormsg)

            # Check for Overlays
            if "<GroundOverlay>" in file:
                warning += "GroundOverlay"
            if "<ScreenOverlay>" in file:
                warning += "ScreenOverlay"

        return file, warning

    def get_api_key(self, layer="google"):
        " Acquire API key from the database "

        query = self.db.gis_apikey.name == layer
        return self.db(query).select(db.gis_apikey.name, limitby=(0, 1)).first().apikey

    def get_bearing(lat_start, lon_start, lat_end, lon_end):
        """
            Given a Start & End set of Coordinates, return a Bearing
            Formula from: http://www.movable-type.co.uk/scripts/latlong.html
        """

        import math

        delta_lon = lon_start - lon_end
        bearing = math.atan2( math.sin(delta_lon)*math.cos(lat_end) , (math.cos(lat_start)*math.sin(lat_end)) - (math.sin(lat_start)*math.cos(lat_end)*math.cos(delta_lon)) )
        # Convert to a compass bearing
        bearing = (bearing + 360) % 360

        return bearing

    def get_bounds(self, features=[]):
        """
            Calculate the Bounds of a list of Features
            e.g. to use in GPX export for correct zooming
        """
        # If we have a list of features, then use this to build the bounds
        if features:
            min_lon = 180
            min_lat = 90
            max_lon = -180
            max_lat = -90
            for feature in features:
                if feature.lon > max_lon:
                    max_lon = feature.lon
                if feature.lon < min_lon:
                    min_lon = feature.lon
                if feature.lat > max_lat:
                    max_lat = feature.lat
                if feature.lat < min_lat:
                    min_lat = feature.lat
            # Check that we're still within overall bounds
            config = self.get_config()
            if min_lon < config.min_lon:
                min_lon = config.min_lon
            if min_lat < config.min_lat:
                min_lat = config.min_lat
            if max_lon > config.max_lon:
                max_lon = config.max_lon
            if max_lat > config.max_lat:
                max_lat = config.max_lat

        else:
            # Read from config
            config = self.get_config()
            min_lon = config.min_lon
            min_lat = config.min_lat
            max_lon = config.max_lon
            max_lat = config.max_lat

        return dict(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    def get_children(self, parent_id):
        "Return a list of all GIS Features which are children of the requested parent"

        db = self.db

        # Switch to modified preorder tree traversal:
        # http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        children = db(db.gis_location.parent == parent_id).select()
        for child in children:
            children = children & self.get_children(child.id)

        return children

    def get_config(self):
        " Reads the current GIS Config from the DB "

        db = self.db
        _config = db.gis_config
        _projection = db.gis_projection
        
        query = (_config.id == 1) & (_projection.id == _config.projection_id)
        config = db(query).select(limitby=(0, 1)).first()
        
        output = Storage()
        for item in config["gis_config"]:
            output[item] = config["gis_config"][item]
        
        for item in config["gis_projection"]:
            if item in ["epsg", "units", "maxResolution", "maxExtent"]:
                output[item] = config["gis_projection"][item]
        
        return output

    def get_feature_class_id_from_name(self, name):
        """
            Returns the Feature Class ID from it's name
        """

        db = self.db

        feature = db(db.gis_feature_class.name == name).select()
        if feature:
            return feature[0].id
        else:
            return None

    def get_features_in_radius(lat, lon, radius):
        """
            Returns Features within a Radius (in km) of a LatLon Location
            Calling function has the job of filtering features by the type they are interested in
            Formula from: http://blog.peoplesdns.com/archives/24
            Spherical Law of Cosines (accurate down to around 1m & computationally quick): http://www.movable-type.co.uk/scripts/latlong.html

            IF PROJECTION CHANGES THIS WILL NOT WORK
        """

        import math

        # km
        radius_earth = 6378.137
        pi = math.pi

        # ToDo: Do a Square query 1st & then run the complex query over subset (to improve performance)
        lat_max = 90
        lat_min = -90
        lon_max = 180
        lon_min = -180
        table = db.gis_location
        query = (table.lat > lat_min) & (table.lat < lat_max) & (table.lon < lon_max) & (table.lon > lon_min)
        deleted = ((table.deleted==False) | (table.deleted==None))
        query = deleted & query

        # ToDo: complete port from PHP to Eden
        pilat180 = pi * lat /180
        #calc = "radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180)) + (math.cos(pilat180) * math.cos(pi*table.lat/180) * math.cos(pi * table.lon/180-pi* lon /180)))"
        #query2 = "SELECT DISTINCT table.lon, table.lat, calc AS distance FROM table WHERE calc <= radius ORDER BY distance"
        #query2 = (radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180)) + (math.cos(pilat180) * math.cos(pi*table.lat/180) * math.cos(pi * table.lon/180-pi* lon /180))) < radius)
        # TypeError: unsupported operand type(s) for *: 'float' and 'Field'
        query2 = (radius_earth * math.acos((math.sin(pilat180) * math.sin(pi * table.lat /180))) < radius)
        #query = query & query2
        features = db(query).select()
        #features = db(query).select(orderby=distance)

        return features

    def get_marker(self, feature_id):

        """ Returns the Marker URL for a Feature

            @param feature_id: the feature ID (int) or UUID (str)

        """

        db = self.db
        table_feature = db.gis_location
        table_marker = db.gis_marker
        table_fclass = db.gis_feature_class
        table_symbology = db.gis_symbology_to_feature_class

        config = self.get_config()
        symbology = config.symbology_id

        query = None

        if isinstance(feature_id, int):
            query = (table_feature.id == feature_id)
        elif isinstance(feature_id, str):
            query = (table_feature.uuid == feature_id)

        feature = db(query).select(table_feature.marker_id,
                                   table_feature.feature_class_id,
                                   limitby=(0, 1))
        if feature:
            _feature = feature.first()
            feature_class =  _feature.feature_class_id
            marker_id =  _feature.first().marker_id

            # 1st choice for a Marker is the Feature's
            if marker_id:
                query = (table_marker.id == marker_id)
                marker = db(query).select(table_marker.image, limitby=(0, 1),
                                          cache=self.cache)
                if marker:
                    return marker.first().image

            # 2nd choice for a Marker is the Symbology for the Feature Class
            query = (table_symbology.feature_class_id == feature_class) & \
                    (table_symbology.symbology_id == symbology) & \
                    (table_marker.id == table_symbology.marker_id)
            marker = db(query).select(table_marker.image, limitby=(0, 1),
                                      cache=self.cache)
            if marker:
                return marker.first().image

            # 3rd choice for a Marker is the Feature Class's
            query = (table_fclass.id == feature_class) & \
                    (table_marker.id == table_fclass.marker_id)
            marker = db(query).select(table_marker.image, limitby=(0, 1),
                                      cache=self.cache)
            if marker:
                return marker.first().image

        # 4th choice for a Marker is the default
        query = (table_marker.id == config.marker_id)
        marker = db(query).select(table_marker.image, limitby=(0, 1),
                                  cache=self.cache)
        if marker:
            return marker.first().image
        else:
            return ""

    def latlon_to_wkt(self, lat, lon):
        """
            Convert a LatLon to a WKT string

            >>> s3gis.latlon_to_wkt(6, 80)
            'POINT(80 6)'
        """
        WKT = "POINT(%f %f)" % (lon, lat)
        return WKT

    def layer_subtypes(self, layer="openstreetmap"):
        """ Return a lit of the subtypes available for a Layer """

        if layer == "openstreetmap":
            #return ["Mapnik", "Osmarender", "Aerial"]
            return ["Mapnik", "Osmarender"]
        elif layer == "google":
            return ["Satellite", "Maps", "Hybrid", "Terrain"]
        elif layer == "yahoo":
            return ["Satellite", "Maps", "Hybrid"]
        elif layer == "bing":
            return ["Satellite", "Maps", "Hybrid", "Terrain"]
        else:
            return None

    def show_map( self,
                  height = None,
                  width = None,
                  lat = None,
                  lon = None,
                  zoom = None,
                  projection = None,
                  feature_overlays = [],
                  wms_browser = {},
                  catalogue_overlays = False,
                  catalogue_toolbar = False,
                  toolbar = False,
                  search = False,
                  print_tool = {},
                  mgrs = {},
                  window = False,
                  public_url = "http://127.0.0.1:8000"
                ):
        """
            Returns the HTML to display a map

            @param height: Height of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param width: Width of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param lat: default Latitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param lon: default Longitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param zoom: default Zoom level of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param projection: EPSG code for the Projection to use (if not provided then the default setting from the Map Service Catalogue is used)
            @param feature_overlays: Which Feature Groups to overlay onto the map & their options (List of Dicts):
                [{
                 feature_group : db.gis_feature_group.name,
                 parent : None,         # Only display features with this parent set. ToDo: search recursively to allow all descendants
                 filter : None,         # A query to further limit which features from the feature group are loaded
                 active : False,        # Is the feed displayed upon load or needs ticking to load afterwards?
                 popup_url : None,      # The URL which will be used to fill the pop-up. it will be appended by the Location ID.
                 marker : None          # The icon used to display the feature (over-riding the normal process). Can be a lambda to vary icon (size/colour) based on attribute levels.
                }]
            @param wms_browser: WMS Server's GetCapabilities & options (dict)
                {
                name: string,           # Name for the Folder in LayerTree
                url: string             # URL of GetCapabilities
                }
            @param catalogue_overlays: Show the Overlays from the GIS Catalogue (@ToDo: make this a dict of which external overlays to allow)
            @param catalogue_toolbar: Show the Catalogue Toolbar
            @param toolbar: Show the Icon Toolbar of Controls
            @param search: Show the Geonames search box
            @param print_tool: Show a print utility (NB This requires server-side support: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting)
                {
                url: string             # URL of print service (e.g. http://localhost:8080/geoserver/pdf/)
                }
            @param mgrs: Use the MGRS Control to select PDFs
                {
                name: string,           # Name for the Control
                url: string             # URL of PDF server
                }
            @param window: Have viewport pop out of page into a resizable window
            @param public_url: pass from model (not yet defined when Module instantiated

            @ToDo: Rewrite these to use the API:
                map_viewing_client()
                display_feature()
                display_features()
        """

        request = self.request
        response = self.response
        if not response.warning:
            response.warning = ""
        session = self.session
        T = self.T
        db = self.db
        auth = self.auth

        # Read configuration
        config = self.get_config()
        if not height:
            height = config.map_height
        if not width:
            width = config.map_width
        # Support bookmarks (such as from the control)
        # - these over-ride the arguments
        if "lat" in request.vars:
            lat = request.vars.lat
        elif not lat:
            lat = config.lat
        if "lon" in request.vars:
            lon = request.vars.lon
        elif not lon:
            lon = config.lon
        if "zoom" in request.vars:
            zoom = request.vars.zoom
        elif not zoom:
            zoom = config.zoom
        if not projection:
            projection = config.epsg
        units = config.units
        maxResolution = config.maxResolution
        maxExtent = config.maxExtent
        numZoomLevels = config.zoom_levels
        marker_default = config.marker_id
        cluster_distance = config.cluster_distance
        cluster_threshold = config.cluster_threshold

        html = DIV(_id="map_wrapper")

        #####
        # CSS
        #####
        if session.s3.debug:
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="scripts/ext/resources/css/ext-all.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="scripts/gis/ie6-style.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="scripts/gis/google.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/geoext-all-debug.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/gis.css"), _media="screen", _charset="utf-8") )
        else:
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="scripts/ext/resources/css/ext-all.min.css"), _media="screen", _charset="utf-8") )
            html.append(LINK( _rel="stylesheet", _type="text/css", _href=URL(r=request, c="static", f="styles/gis/gis.min.css"), _media="screen", _charset="utf-8") )

        ######
        # HTML
        ######
        # Catalogue Toolbar
        if catalogue_toolbar:
            if auth.has_membership(1):
                config_button = SPAN( A(T("Defaults"), _href=URL(r=request, c="gis", f="config", args=["1", "update"])), _class="rheader_tab_other" )
            else:
                config_button = SPAN( A(T("Defaults"), _href=URL(r=request, c="gis", f="config", args=["1", "display"])), _class="rheader_tab_other" )
            catalogue_toolbar = DIV(
                config_button,
                SPAN( A(T("Locations"), _href=URL(r=request, c="gis", f="location")), _class="rheader_tab_other" ),
                SPAN( A(T("Feature Classes"), _href=URL(r=request, c="gis", f="feature_class")), _class="rheader_tab_other" ),
                SPAN( A(T("Feature Groups"), _href=URL(r=request, c="gis", f="feature_group")), _class="rheader_tab_other" ),
                SPAN( A(T("Keys"), _href=URL(r=request, c="gis", f="apikey")), _class="rheader_tab_other" ),
                SPAN( A(T("Layers"), _href=URL(r=request, c="gis", f="map_service_catalogue")), _class="rheader_tab_other" ),
                SPAN( A(T("Markers"), _href=URL(r=request, c="gis", f="marker")), _class="rheader_tab_other" ),
                SPAN( A(T("Projections"), _href=URL(r=request, c="gis", f="projection")), _class="rheader_tab_other" ),
                _id="rheader_tabs")
            html.append(catalogue_toolbar)

        # Map (Embedded not Window)
        html.append(DIV(_id="map_panel"))

        # Status Reports
        html.append(TABLE(TR(
            TD(
                # Somewhere to report details of OSM File Features via on_feature_hover()
                DIV(_id="status_osm"),
                _style="border: 0px none ;", _valign="top",
            ),
            TD(
                # Somewhere to report whether GeoRSS feed is using cached copy or completely inaccessible
                DIV(_id="status_georss"),
                # Somewhere to report whether KML feed is using cached copy or completely inaccessible
                DIV(_id="status_kml"),
                # Somewhere to report if Files are not found
                DIV(_id="status_files"),
                _style="border: 0px none ;", _valign="top",
            )
        )))

        #########
        # Scripts
        #########
        if session.s3.debug:
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/ext/adapter/jquery/ext-jquery-adapter-debug.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/ext/ext-all-debug.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/openlayers/lib/OpenLayers.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/MP.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/usng2.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/RemoveFeature.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/osm_styles.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/geoext/lib/GeoExt.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/geoext/ux/GeoNamesSearchCombo.js")))
        else:
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/ext/adapter/jquery/ext-jquery-adapter.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/ext/ext-all.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/OpenLayers.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/RemoveFeature.js")))
            html.append(SCRIPT(_type="text/javascript", _src=URL(r=request, c="static", f="scripts/gis/GeoExt.js")))

        if print_tool:
            url = print_tool["url"] + "info.json?var=printCapabilities"
            html.append(SCRIPT(_type="text/javascript", _src=url))

        #######
        # Tools
        #######

        # MGRS
        if mgrs:
            mgrs_html = """
var selectPdfControl = new OpenLayers.Control();
OpenLayers.Util.extend( selectPdfControl, {
    draw: function () {
        this.box = new OpenLayers.Handler.Box( this, {
                'done': this.getPdf
            });
        this.box.activate();
        },
    response: function(req) {
        this.w.destroy();
        var gml = new OpenLayers.Format.GML();
        var features = gml.read(req.responseText);
        var html = features.length + ' pdfs. <br /><ul>';
        if (features.length) {
            for (var i = 0; i < features.length; i++) {
                var f = features[i];
                var text = f.attributes.utm_zone + f.attributes.grid_zone + f.attributes.grid_square + f.attributes.easting + f.attributes.northing;
                html += "<li><a href='" + features[i].attributes.url + "'>" + text + '</a></li>';
            }
        }
        html += '</ul>';
        //console.log(html);
        this.w = new Ext.Window({
            'html': html,
            width: 300,
            'title': 'Results',
            height: 200
        });
        this.w.show();
    },
    getPdf: function (bounds) {
        var ll = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.left, bounds.bottom)).transform(projection_current, proj4326);
        //console.log(ll);
        var ur = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top)).transform(projection_current, proj4326);
        var boundsgeog = new OpenLayers.Bounds(ll.lon, ll.lat, ur.lon, ur.lat);
        bbox = boundsgeog.toBBOX();
        //console.log(bbox);
        OpenLayers.Request.GET({
            url: '""" + str(XML(mgrs["url"])) + """&bbox=' + bbox,
            callback: OpenLayers.Function.bind(this.response, this)
        });
        this.w = new Ext.Window({
            'html':'Searching """ + mgrs["name"] + """, please wait.',
            width: 200,
            'title': "Please Wait."
            });
        this.w.show();
    }
});
"""
            mgrs2 = """
    // MGRS Control
    var mgrsButton = new GeoExt.Action({
        text: 'Select """ + mgrs["name"] + """',
        control: selectPdfControl,
        map: map,
        toggleGroup: toggleGroup,
        allowDepress: false,
        tooltip: 'Select """ + mgrs["name"] + """',
        // check item options group: 'draw'
    });
    """
            mgrs3 = """
    toolbar.add(mgrsButton);
    toolbar.addSeparator();
    """
        else:
            mgrs_html = ""
            mgrs2 = ""
            mgrs3 = ""

        # Toolbar
        if toolbar:
            toolbar = """
        toolbar = mapPanel.getTopToolbar();
        var toggleGroup = "controls";

        // OpenLayers controls
        var length = new OpenLayers.Control.Measure(OpenLayers.Handler.Path, {
            eventListeners: {
                measure: function(evt) {
                    alert('""" + str(T("The length was ")) + """' + evt.measure + evt.units);
                }
            }
        });

        var area = new OpenLayers.Control.Measure(OpenLayers.Handler.Polygon, {
            eventListeners: {
                measure: function(evt) {
                    alert('""" + str(T("The area was ")) + """' + evt.measure + evt.units);
                }
            }
        });

        // Controls for Draft Features
        // - interferes with Feature Layers!
        //var selectControl = new OpenLayers.Control.SelectFeature(featuresLayer, {
        //    onSelect: onFeatureSelect,
        //    onUnselect: onFeatureUnselect,
        //    multiple: false,
        //    clickout: true,
        //    isDefault: true
        //});

        //var removeControl = new OpenLayers.Control.RemoveFeature(featuresLayer,
        //    {onDone: function(feature) {console.log(feature)}
        //});

        var nav = new OpenLayers.Control.NavigationHistory();

        // GeoExt Buttons
        var zoomfull = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomToMaxExtent(),
            map: map,
            iconCls: 'zoomfull',
            tooltip: '""" + str(T("Zoom to maximum map extent")) + """'
        });

        var zoomout = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox({ out: true }),
            map: map,
            iconCls: 'zoomout',
            tooltip: '""" + str(T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle")) + """',
            toggleGroup: toggleGroup
        });

        var zoomin = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox(),
            map: map,
            iconCls: 'zoomin',
            tooltip: '""" + str(T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle")) + """',
            toggleGroup: toggleGroup
        });

        var pan = new GeoExt.Action({
            control: new OpenLayers.Control.Navigation(),
            map: map,
            iconCls: 'pan-off',
            tooltip: '""" + str(T("Pan Map: keep the left mouse button pressed and drag the map")) + """',
            toggleGroup: toggleGroup,
            //allowDepress: false,
            pressed: true
        });

        var lengthButton = new GeoExt.Action({
            control: length,
            map: map,
            iconCls: 'measure-off',
            tooltip: '""" + str(T("Measure Length: Click the points along the path & end with a double-click")) + """',
            toggleGroup: toggleGroup
        });

        var areaButton = new GeoExt.Action({
            control: area,
            map: map,
            iconCls: 'measure-area',
            tooltip: '""" + str(T("Measure Area: Click the points around the polygon & end with a double-click")) + """',
            toggleGroup: toggleGroup
        });

        """ + mgrs2 + """

        var selectButton = new GeoExt.Action({
            //control: selectControl,
            map: map,
            iconCls: 'searchclick',
            tooltip: '""" + str(T("Query Feature")) + """',
            toggleGroup: toggleGroup
        });

        //var pointButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point),
        //    map: map,
        //    iconCls: 'drawpoint-off',
        //    tooltip: '""" + str(T("Add Point")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var lineButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path),
        //    map: map,
        //    iconCls: 'drawline-off',
        //    tooltip: '""" + str(T("Add Line")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var polygonButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon),
        //    map: map,
        //    iconCls: 'drawpolygon-off',
        //    tooltip: '""" + str(T("Add Polygon")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var dragButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DragFeature(featuresLayer),
        //    map: map,
        //    iconCls: 'movefeature',
        //    tooltip: '""" + str(T("Move Feature: Drag feature to desired location")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var resizeButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(featuresLayer, { mode: OpenLayers.Control.ModifyFeature.RESIZE }),
        //    map: map,
        //    iconCls: 'resizefeature',
        //    tooltip: '""" + str(T("Resize Feature: Select the feature you wish to resize & then Drag the associated dot to your desired size")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var rotateButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(featuresLayer, { mode: OpenLayers.Control.ModifyFeature.ROTATE }),
        //    map: map,
        //    iconCls: 'rotatefeature',
        //    tooltip: '""" + str(T("Rotate Feature: Select the feature you wish to rotate & then Drag the associated dot to rotate to your desired location")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var modifyButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(featuresLayer),
        //    map: map,
        //    iconCls: 'modifyfeature',
        //    tooltip: '""" + str(T("Modify Feature: Select the feature you wish to deform & then Drag one of the dots to deform the feature in your chosen manner")) + """',
        //    toggleGroup: toggleGroup
        //});

        //var removeButton = new GeoExt.Action({
        //    control: removeControl,
        //    map: map,
        //    iconCls: 'removefeature',
        //    tooltip: '""" + str(T("Remove Feature: Select the feature you wish to remove & press the delete key")) + """',
        //    toggleGroup: toggleGroup
        //});

        var navPreviousButton = new Ext.Toolbar.Button({
            iconCls: 'back',
            tooltip: '""" + str(T("Previous View")) + """',
            handler: nav.previous.trigger
        });

        var navNextButton = new Ext.Toolbar.Button({
            iconCls: 'next',
            tooltip: '""" + str(T("Next View")) + """',
            handler: nav.next.trigger
        });

        var saveButton = new Ext.Toolbar.Button({
            // ToDo: Make work!
            iconCls: 'save',
            tooltip: '""" + str(T("Save: Default Lat, Lon & Zoom for the Viewport")) + """',
            handler: function saveViewport(map) {
                // Read current settings from map
                var lonlat = map.getCenter();
                var zoom_current = map.getZoom();
                // Convert back to LonLat for saving
                //var proj4326 = new OpenLayers.Projection('EPSG:4326');
                lonlat.transform(map.getProjectionObject(), proj4326);
                //alert('""" + str(T("Latitude")) + """': ' + lat);
                // Use AJAX to send back
                var url = '""" + URL(r=request, c="gis", f="config", args=["1.json", "update"]) + """';
            }
        });

        // Add to Map & Toolbar
        toolbar.add(zoomfull);
        toolbar.add(zoomout);
        toolbar.add(zoomin);
        toolbar.add(pan);
        toolbar.addSeparator();
        // Measure Tools
        toolbar.add(lengthButton);
        toolbar.add(areaButton);
        toolbar.addSeparator();
        """ + mgrs3 + """
        // Draw Controls
        //toolbar.add(selectButton);
        //toolbar.add(pointButton);
        //toolbar.add(lineButton);
        //toolbar.add(polygonButton);
        //toolbar.add(dragButton);
        //toolbar.add(resizeButton);
        //toolbar.add(rotateButton);
        //toolbar.add(modifyButton);
        //toolbar.add(removeButton);
        //toolbar.addSeparator();
        // Navigation
        map.addControl(nav);
        nav.activate();
        toolbar.addButton(navPreviousButton);
        toolbar.addButton(navNextButton);
        toolbar.addSeparator();
        // Save Viewport
        toolbar.addButton(saveButton);
        """
            toolbar2 = "Ext.QuickTips.init();"
        else:
            toolbar = ""
            toolbar2 = ""

        # Search
        if search:
            search = """
        var mapSearch = new GeoExt.ux.geonames.GeoNamesSearchCombo({
            map: map,
            zoom: 8
         });

        var searchCombo = new Ext.Panel({
            title: '""" + str(T("Search Geonames")) + """',
            layout: 'border',
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            html: '""" + str(T("Geonames.org search requires Internet connectivity!")) + """',
            items: [{
                    region: 'center',
                    items: [ mapSearch ]
                }]
        });
        """
            search2 = """,
                            searchCombo"""
        else:
            search = ""
            search2 = ""

        # WMS Browser
        if wms_browser:
            name = wms_browser["name"]
            # urlencode the URL
            url = urllib.quote(wms_browser["url"])
            layers_wms_browser = """
        var root = new Ext.tree.AsyncTreeNode({
            expanded: true,
            loader: new GeoExt.tree.WMSCapabilitiesLoader({
                url: OpenLayers.ProxyHost + '""" + url + """',
                layerOptions: {buffer: 1, singleTile: false, ratio: 1, wrapDateLine: true},
                layerParams: {'TRANSPARENT': 'TRUE'},
                // customize the createNode method to add a checkbox to nodes
                createNode: function(attr) {
                    attr.checked = attr.leaf ? false : undefined;
                    return GeoExt.tree.WMSCapabilitiesLoader.prototype.createNode.apply(this, [attr]);
                }
            })
        });
        wmsBrowser = new Ext.tree.TreePanel({
            id: 'wmsbrowser',
            title: '""" + name + """',
            root: root,
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            listeners: {
                // Add layers to the map when checked, remove when unchecked.
                // Note that this does not take care of maintaining the layer
                // order on the map.
                'checkchange': function(node, checked) {
                    if (checked === true) {
                        mapPanel.map.addLayer(node.attributes.layer);
                    } else {
                        mapPanel.map.removeLayer(node.attributes.layer);
                    }
                }
            }
        });
        """
            layers_wms_browser2 = """,
                            wmsBrowser"""
        else:
            layers_wms_browser = ""
            layers_wms_browser2 = ""

        # Print
        if print_tool:
            url = print_tool["url"]
            print_tool1 = """
        printProvider = new GeoExt.data.PrintProvider({
            //method: 'POST',
            //url: '""" + url + """'
            method: 'GET', // 'POST' recommended for production use
            capabilities: printCapabilities // from the info.json script in the html
        });
        // Our print page. Stores scale, center and rotation and gives us a page
        // extent feature that we can add to a layer.
        printPage = new GeoExt.data.PrintPage({
            printProvider: printProvider,
            customParams: {
                mapTitle: 'Printing Demo'
            }
        });
        // A layer to display the print page extent
        var pageLayer = new OpenLayers.Layer.Vector();
        pageLayer.addFeatures(printPage.feature);
        map.addLayer(pageLayer);
        map.setOptions(options, {
            eventListeners: {
                // recenter/resize page extent after pan/zoom
                'moveend': function(){ printPage.fit(this); }
            }
        });
        // The form with fields controlling the print output
        var formPanel = new Ext.form.FormPanel({
            title: 'Print Map',
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            bodyStyle: 'padding:5px',
            labelAlign: 'top',
            defaults: {anchor: '100%'},
            items: [{
                xtype: 'textarea',
                name: 'comment',
                value: '',
                fieldLabel: 'Comment',
                plugins: new GeoExt.plugins.PrintPageField({
                    printPage: printPage
                })
            }, {
                xtype: 'combo',
                store: printProvider.layouts,
                displayField: 'name',
                fieldLabel: 'Layout',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                plugins: new GeoExt.plugins.PrintProviderField({
                    printProvider: printProvider
                })
            }, {
                xtype: 'combo',
                store: printProvider.dpis,
                displayField: 'name',
                fieldLabel: 'Resolution',
                tpl: '<tpl for="."><div class="x-combo-list-item">{name} dpi</div></tpl>',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                plugins: new GeoExt.plugins.PrintProviderField({
                    printProvider: printProvider
                }),
                // the plugin will work even if we modify a combo value
                setValue: function(v) {
                    v = parseInt(v) + ' dpi';
                    Ext.form.ComboBox.prototype.setValue.apply(this, arguments);
                }
            }, {
                xtype: 'combo',
                store: printProvider.scales,
                displayField: 'name',
                fieldLabel: 'Scale',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                plugins: new GeoExt.plugins.PrintPageField({
                    printPage: printPage
                })
            }, {
                xtype: 'textfield',
                name: 'rotation',
                fieldLabel: 'Rotation',
                plugins: new GeoExt.plugins.PrintPageField({
                    printPage: printPage
                })
            }],
            buttons: [{
                text: 'Create PDF',
                handler: function() {
                    printProvider.print(mapPanel, printPage);
                }
            }]
        });
        """
            print_tool2 = """,
                    formPanel"""
        else:
            print_tool1 = ""
            print_tool2 = ""

        # Strategy
        # Need to be uniquely instantiated
        strategy_fixed = """new OpenLayers.Strategy.Fixed()"""
        strategy_cluster = """new OpenLayers.Strategy.Cluster({distance: """ + str(cluster_distance) + """, threshold: """ + str(cluster_threshold) + """})"""

        # Layout
        if window:
            layout = """
        var win = new Ext.Window({
            collapsible: true,
            """
            layout2 = "win.show();"
        else:
            # Embedded
            layout = """
    var panel = new Ext.Panel({
        renderTo: "map_panel",
            """
            layout2 = ""

        ########
        # Layers
        ########

        #
        # Base Layers
        #

        layers_openstreetmap = ""
        layers_google = ""
        layers_yahoo = ""
        layers_bing = ""

        # Only enable commercial base layers if using a sphericalMercator projection
        if projection == 900913:

            # OpenStreetMap
            gis_layer_openstreetmap_subtypes = self.layer_subtypes("openstreetmap")
            openstreetmap = Storage()
            openstreetmap_enabled = db(db.gis_layer_openstreetmap.enabled == True).select()
            for layer in openstreetmap_enabled:
                for subtype in gis_layer_openstreetmap_subtypes:
                    if layer.subtype == subtype:
                        openstreetmap["%s" % subtype] = layer.name

            if openstreetmap:
                functions_openstreetmap = """
        function osm_getTileURL(bounds) {
            var res = this.map.getResolution();
            var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
            var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
            var z = this.map.getZoom();
            var limit = Math.pow(2, z);
            if (y < 0 || y >= limit) {
                return OpenLayers.Util.getImagesLocation() + '404.png';
            } else {
                x = ((x % limit) + limit) % limit;
                return this.url + z + '/' + x + '/' + y + '.' + this.type;
            }
        }
        """
                if openstreetmap.Mapnik:
                    layers_openstreetmap += """
        var mapnik = new OpenLayers.Layer.TMS( '""" + openstreetmap.Mapnik + """', 'http://tile.openstreetmap.org/', {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
        map.addLayer(mapnik);
                    """
                if openstreetmap.Osmarender:
                    layers_openstreetmap += """
        var osmarender = new OpenLayers.Layer.TMS( '""" + openstreetmap.Osmarender + """', 'http://tah.openstreetmap.org/Tiles/tile/', {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
        map.addLayer(osmarender);
                    """
                if openstreetmap.Aerial:
                    layers_openstreetmap += """
        var oam = new OpenLayers.Layer.TMS( '""" + openstreetmap.Aerial + """', 'http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/', {type: 'png', getURL: osm_getTileURL } );
        map.addLayer(oam);
                    """
            else:
                functions_openstreetmap = ""

            # Google
            gis_layer_google_subtypes = self.layer_subtypes("google")
            google = Storage()
            google_enabled = db(db.gis_layer_google.enabled == True).select()
            if google_enabled:
                google.key = self.get_api_key("google")
                for layer in google_enabled:
                    for subtype in gis_layer_google_subtypes:
                        if layer.subtype == subtype:
                            google["%s" % subtype] = layer.name
            if google:
                html.append(SCRIPT(_type="text/javascript", _src="http://maps.google.com/maps?file=api&v=2&key=" + google.key))
                if google.Satellite:
                    layers_google += """
        var googlesat = new OpenLayers.Layer.Google( '""" + google.Satellite + """' , {type: G_SATELLITE_MAP, 'sphericalMercator': true } );
        map.addLayer(googlesat);
                    """
                if google.Maps:
                    layers_google += """
        var googlemaps = new OpenLayers.Layer.Google( '""" + google.Maps + """' , {type: G_NORMAL_MAP, 'sphericalMercator': true } );
        map.addLayer(googlemaps);
                    """
                if google.Hybrid:
                    layers_google += """
        var googlehybrid = new OpenLayers.Layer.Google( '""" + google.Hybrid + """' , {type: G_HYBRID_MAP, 'sphericalMercator': true } );
        map.addLayer(googlehybrid);
                    """
                if google.Terrain:
                    layers_google += """
        var googleterrain = new OpenLayers.Layer.Google( '""" + google.Terrain + """' , {type: G_PHYSICAL_MAP, 'sphericalMercator': true } )
        map.addLayer(googleterrain);
                    """

            # Yahoo
            gis_layer_yahoo_subtypes = self.layer_subtypes("yahoo")
            yahoo = Storage()
            yahoo_enabled = db(db.gis_layer_yahoo.enabled == True).select()
            if yahoo_enabled:
                yahoo.key = self.get_api_key("yahoo")
                for layer in yahoo_enabled:
                    for subtype in gis_layer_yahoo_subtypes:
                        if layer.subtype == subtype:
                            yahoo["%s" % subtype] = layer.name
            if yahoo:
                html.append(SCRIPT(_type="text/javascript", _src="http://api.maps.yahoo.com/ajaxymap?v=3.8&appid=" + yahoo.key))
                if yahoo.Satellite:
                    layers_yahoo += """
        var yahoosat = new OpenLayers.Layer.Yahoo( '""" + yahoo.Satellite + """' , {type: YAHOO_MAP_SAT, 'sphericalMercator': true } );
        map.addLayer(yahoosat);
                    """
                if yahoo.Maps:
                    layers_yahoo += """
        var yahoomaps = new OpenLayers.Layer.Yahoo( '""" + yahoo.Maps + """' , {'sphericalMercator': true } );
        map.addLayer(yahoomaps);
                    """
                if yahoo.Hybrid:
                    layers_yahoo += """
        var yahoohybrid = new OpenLayers.Layer.Yahoo( '""" + yahoo.Hybrid + """' , {type: YAHOO_MAP_HYB, 'sphericalMercator': true } );
        map.addLayer(yahoohybrid);
                    """

            # Bing - Broken in GeoExt currently: http://www.geoext.org/pipermail/users/2009-December/000417.html
            bing = False
            #gis_layer_bing_subtypes = self.layer_subtypes("bing")
            #bing = Storage()
            #bing_enabled = db(db.gis_layer_bing.enabled == True).select()
            #for layer in bing_enabled:
            #    for subtype in gis_layer_bing_subtypes:
            #        if layer.subtype == subtype:
            #            bing["%s" % subtype] = layer.name
            if bing:
                html.append(SCRIPT(_type="text/javascript", _src="http://ecn.dev.virtualearth.net/mapcontrol/mapcontrol.ashx?v=6.2&mkt=en-us"))
                if bing.Satellite:
                    layers_bing += """
        var bingsat = new OpenLayers.Layer.VirtualEarth( '""" + bing.Satellite + """' , {type: VEMapStyle.Aerial, 'sphericalMercator': true } );
        map.addLayer(bingsat);
                    """
                if bing.Maps:
                    layers_bing += """
        var bingmaps = new OpenLayers.Layer.VirtualEarth( '""" + bing.Maps + """' , {type: VEMapStyle.Road, 'sphericalMercator': true } );
        map.addLayer(bingmaps);
                    """
                if bing.Hybrid:
                    layers_bing += """
        var binghybrid = new OpenLayers.Layer.VirtualEarth( '""" + bing.Hybrid + """' , {type: VEMapStyle.Hybrid, 'sphericalMercator': true } );
        map.addLayer(binghybrid);
                    """
                if bing.Terrain:
                    layers_bing += """
        var bingterrain = new OpenLayers.Layer.VirtualEarth( '""" + bing.Terrain + """' , {type: VEMapStyle.Shaded, 'sphericalMercator': true } );
        map.addLayer(bingterrain);
                    """

        # WMS
        layers_wms = ""
        wms_enabled = db(db.gis_layer_wms.enabled == True).select()
        for layer in wms_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            try:
                wms_map = "map: '" + layer.map + "',"
            except:
                wms_map = ""
            wms_layers = layer.layers
            try:
                format = "type: '" + layer.format + "'"
            except:
                format = ""
            wms_projection = db(db.gis_projection.id == layer.projection_id).select(limitby=(0, 1)).first().epsg
            if wms_projection == 4326:
                wms_projection = "projection: proj4326"
            else:
                wms_projection = "projection: new OpenLayers.Projection('EPSG:" + wms_projection + "')"
            if layer.transparent:
                transparent = "transparent: true,"
            else:
                transparent = ""
            options = "wrapDateLine: 'true'"
            if not layer.base:
                options += """,
                   isBaseLayer: false"""
                if not layer.visible:
                   options += """,
                   visibility: false"""

            layers_wms  += """
        var wmsLayer""" + name_safe + """ = new OpenLayers.Layer.WMS(
            '""" + name + """', '""" + url + """', {
               """ + wms_map + """
               layers: '""" + wms_layers + """',
               """ + format + """
               """ + transparent + """
               """ + wms_projection + """
               },
               {
               """ + options + """
               }
            );
        map.addLayer(wmsLayer""" + name_safe + """);
        """

        # TMS
        layers_tms = ""
        tms_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in tms_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            tms_layers = layer.layers
            try:
                format = "type: '" + layer.format + "'"
            except:
                format = ""

            layers_tms  += """
        var tmsLayer""" + name_safe + """ = new OpenLayers.Layer.TMS( '""" + name + """', '""" + url + """', {
                layername: '""" + tms_layers + """',
                """ + format + """
            });
        map.addLayer(tmsLayer""" + name_safe + """);
        """

        # XYZ
        layers_xyz = ""
        xyz_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in xyz_enabled:
            name = layer.name
            name_safe = re.sub('\W', '_', name)
            url = layer.url
            if layer.sphericalMercator:
                sphericalMercator = "sphericalMercator: 'true',"
            else:
                sphericalMercator = ""
            if layer.transitionEffect:
                transitionEffect = "transitionEffect: '{{=xyz_layers[layer].transitionEffect}}',"
            else:
                transitionEffect = ""
            if layer.numZoomLevels:
                xyz_numZoomLevels = "numZoomLevels: '" + layer.numZoomLevels + "'"
            else:
                xyz_numZoomLevels = ""
            if layer.base:
                base = "isBaseLayer: 'true'"
            else:
                base = ""
                if layer.transparent:
                    base += "transparent: 'true',"
                if layer.visible:
                    base += "visibility: 'true',"
                if layer.opacity:
                    base += "opacity: '" + layer.opacity + "',"
                base += "isBaseLayer: 'false'"

            layers_xyz  += """
        var xyzLayer""" + name_safe + """ = new OpenLayers.Layer.XYZ( '""" + name + """', '""" + url + """', {
                """ + sphericalMercator + """
                """ + transitionEffect + """
                """ + xyz_numZoomLevels + """
                """ + base + """
            });
        map.addLayer(xyzLayer""" + name_safe + """);
        """

        # JS
        layers_js = ""
        js_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in js_enabled:
            layers_js  += layer.code

        #
        # Overlays
        #

        # Can we cache downloaded feeds?
        # Needed for unzipping & filtering as well
        cachepath = os.path.join(request.folder, "uploads", "gis_cache")
        if os.access(cachepath, os.W_OK):
            cache = True
        else:
            cache = False

        #
        # Features
        #
        layers_features = ""
        if feature_overlays:

            layers_features += """
        var featureLayers = new Array();
        var features = [];
        var parser = new OpenLayers.Format.WKT();
        var geom, featureVec;

        function addFeature(feature_id, name, feature_class, geom, iconURL) {
            geom = geom.transform(proj4326, projection_current);
            // Set icon dims
            icon_img.src = iconURL;
            width = icon_img.width;
            height = icon_img.height;
            if(width > max_w){
                height = ((max_w / width) * height);
                width = max_w;
            }
            if(height > max_h){
                width = ((max_h / height) * width);
                height = max_h;
            }
            // Needs to be uniquely instantiated
            var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
            style_marker.graphicOpacity = 1;
            style_marker.graphicWidth = width;
            style_marker.graphicHeight = height;
            style_marker.graphicXOffset = -(width / 2);
            style_marker.graphicYOffset = -height;
            style_marker.externalGraphic = iconURL;
            // Create Feature Vector
            var featureVec = new OpenLayers.Feature.Vector(geom, null, style_marker);
            featureVec.fid = feature_id;
            featureVec.attributes.name = name;
            featureVec.attributes.feature_class = feature_class;
            return featureVec;
        }

        function loadDetails(url, id, popup) {
            //$.getS3(
            $.get(
                    url,
                    function(data) {
                        $('#' + id + '_contentDiv').html(data);
                        popup.updateSize();
                    },
                    'html'
                );
        }
        """
            for layer in feature_overlays:
                name = layer["feature_group"]
                if "popup_url" in layer:
                    popup_url = layer["popup_url"]
                # We'd like to do something like this:
                #elif feature_class is office:
                #    popup_url = str(URL(r=request, c="or", f="office"))
                else:
                    popup_url = str(URL(r=request, c="gis", f="location", args=["read.popup"]))

                # Generate HTML snippet
                name_safe = re.sub("\W", "_", name)
                if "active" in layer and layer["active"]:
                    visibility = "featureLayer" + name_safe +".setVisibility(true);"
                else:
                    visibility = "featureLayer" + name_safe +".setVisibility(false);"
                layers_features += """
        features = [];
        // Style Rule For Clusters
        var style_cluster = new OpenLayers.Style({
            pointRadius: "${radius}",
            fillColor: "#8087ff",
            fillOpacity: 1,
            strokeColor: "#2b2f76",
            strokeWidth: 2,
            strokeOpacity: 1
        }, {
            context: {
                radius: function(feature) {
                    // Size For Unclustered Point
                    var pix = 6;
                    // Size For Clustered Point
                    if(feature.cluster) {
                        pix = Math.min(feature.attributes.count, 7) + 4;
                    }
                    return pix;
                }
            }
        });
        // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
        var featureClusterStyleMap = new OpenLayers.StyleMap({
                                          "default": style_cluster,
                                          "select": {
                                              fillColor: "#ffdc33",
                                              strokeColor: "#ff9933"
                                          }
        });

        var featureLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name + """',
            {
                strategies: [ """ + strategy_cluster + """ ],
                styleMap: featureClusterStyleMap
            }
        );
        """ + visibility + """
        map.addLayer(featureLayer""" + name_safe + """);
        featureLayer""" + name_safe + """.events.on({
            "featureselected": onFeatureSelect""" + name_safe + """,
            "featureunselected": onFeatureUnselect
        });
        featureLayers.push(featureLayer""" + name_safe + """);

        function onFeatureSelect""" + name_safe + """(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            if(feature.cluster) {
                // Cluster
                // Create Empty Array to Contain Feature Names
                var clusterFeaturesArray = [];
                // Add Each Feature To Array
                for (var i = 0; i < feature.cluster.length; i++)
                {
                    var clusterFeaturesArrayName = feature.cluster[i].attributes.name;
                    var clusterFeaturesArrayType = feature.cluster[i].attributes.feature_class;
                    var clusterFeaturesArrayX = feature.cluster[i].geometry.x;
                    var clusterFeaturesArrayY = feature.cluster[i].geometry.y;
                    var clusterFeaturesArrayID = feature.cluster[i].fid;

                    // ToDo: Refine
                    var clusterFeaturesArrayEntry = "<li>" + clusterFeaturesArrayName + "</li>";

                    clusterFeaturesArray.push(clusterFeaturesArrayEntry);
                };
            } else {
                // Single Feature
                var selectedFeature = feature;
                var id = 'featureLayer""" + name_safe + """Popup';
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    feature.geometry.getBounds().getCenterLonLat(),
                    new OpenLayers.Size(200, 200),
                    "Loading...<img src='""" + str(URL(r=request, c="static", f="img")) + """/ajax-loader.gif' border=0>",
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                map.addPopup(popup);
                // call AJAX to get the contentHTML
                var uuid = feature.fid;
                loadDetails('""" + popup_url + """' + '?location.uid=' + uuid, id, popup);
            }
        }
        """
                if "parent" in feature_overlays:
                    parent_id = db(db.gis_location.name == parent).select(limitby=(0, 1)).first().id
                    query = (db.gis_location.deleted == False) & (db.gis_feature_group.name == name) & (db.gis_feature_class_to_feature_group.feature_group_id == db.gis_feature_group.id) & (db.gis_location.feature_class_id == db.gis_feature_class_to_feature_group.feature_class_id) & (db.gis_location.parent == parent_id)
                else:
                    query = (db.gis_location.deleted == False) & (db.gis_feature_group.name == name) & (db.gis_feature_class_to_feature_group.feature_group_id == db.gis_feature_group.id) & (db.gis_location.feature_class_id == db.gis_feature_class_to_feature_group.feature_class_id)
                features = db(query).select()
                for feature in features:
                    marker = self.get_marker(feature.gis_location.id)
                    marker_url = URL(r=request, c='default', f='download', args=[marker])
                    # Deal with null Feature Classes
                    if feature.gis_location.feature_class_id:
                        fc = "'" + str(feature.gis_location.feature_class_id) + "'"
                    else:
                        fc = "null"
                    # Deal with manually-imported Features which are missing WKT
                    if feature.gis_location.wkt:
                        wkt = feature.gis_location.wkt
                    else:
                        wkt = self.latlon_to_wkt(feature.gis_location.lat, feature.gis_location.lon)
                    # Deal with apostrophes in Feature Names
                    fname = re.sub("'", "\\'", feature.gis_location.name)
                    
                    layers_features += """
        geom = parser.read('""" + wkt + """').geometry;
        iconURL = '""" + marker_url + """';
        featureVec = addFeature('""" + feature.gis_location.uuid + """', '""" + fname + """', """ + fc + """, geom, iconURL)
        features.push(featureVec);
        """
                # Append to Features layer
                layers_features += """
        featureLayer""" + name_safe + """.addFeatures(features);
        """
            # Append to Features section
            layers_features += """
        allLayers = allLayers.concat(featureLayers);
        """

        else:
            # No Feature Layers requested
            pass

        layers_georss = ""
        layers_gpx = ""
        layers_kml = ""
        if catalogue_overlays:
            # GeoRSS
            georss_enabled = db(db.gis_layer_georss.enabled == True).select()
            if georss_enabled:
                layers_georss += """
        var georssLayers = new Array();
        var format_georss = new OpenLayers.Format.GeoRSS();
        function onGeorssFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var selectedFeature = feature;
            if (undefined == feature.attributes.description) {
                var popup = new OpenLayers.Popup.FramedCloud('georsspopup',
                feature.geometry.getBounds().getCenterLonLat(),
                new OpenLayers.Size(200,200),
                '<h2>' + feature.attributes.title + '</h2>',
                null, true, onPopupClose);
            } else {
                var popup = new OpenLayers.Popup.FramedCloud('georsspopup',
                feature.geometry.getBounds().getCenterLonLat(),
                new OpenLayers.Size(200,200),
                '<h2>' + feature.attributes.title + '</h2>' + feature.attributes.description,
                null, true, onPopupClose);
            };
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in georss_enabled:
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    georss_projection = db(db.gis_projection.id == layer["projection_id"]).select(db.gis_projection.epsg, limitby=(0, 1)).first().epsg
                    if georss_projection == 4326:
                        projection_str = "projection: proj4326,"
                    else:
                        projection_str = "projection: new OpenLayers.Projection('EPSG:" + georss_projection + "'),"
                    marker_id = layer["marker_id"]
                    if marker_id:
                        marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    else:
                        marker = db(db.gis_marker.id == marker_default).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    marker_url = URL(r=request, c="default", f="download", args=marker)

                    if cache:
                        # Download file
                        try:
                            file = fetch(url)
                            warning = ""
                        except urllib2.URLError:
                            warning = "URLError"
                        except urllib2.HTTPError:
                            warning = "HTTPError"
                        filename = "gis_cache.file." + name.replace(" ", "_") + ".rss"
                        filepath = os.path.join(cachepath, filename)
                        f = open(filepath, "w")
                        # Handle errors
                        if "URLError" in warning or "HTTPError" in warning:
                            # URL inaccessible
                            if os.access(filepath, os.R_OK):
                                # Use cached version
                                date = db(db.gis_cache.name == name).select(db.gis_cache.modified_on, limitby=(0, 1)).first().modified_on
                                response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                                url = URL(r=request, c="default", f="download", args=[filename])
                            else:
                                # No cached version available
                                response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                                # skip layer
                                continue
                        else:
                            # Download was succesful
                            # Write file to cache
                            f.write(file)
                            f.close()
                            records = db(db.gis_cache.name == name).select()
                            if records:
                                records[0].update(modified_on=response.utcnow)
                            else:
                                db.gis_cache.insert(name=name, file=filename)
                            url = URL(r=request, c="default", f="download", args=[filename])
                    else:
                        # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                        pass

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "georssLayer" + name_safe + ".setVisibility(true);"
                    else:
                        visibility = "georssLayer" + name_safe + ".setVisibility(false);"
                    layers_georss += """
            iconURL = '""" + marker_url + """';
            icon_img.src = iconURL;
            width = icon_img.width;
            height = icon_img.height;
            if(width > max_w){
                height = ((max_w / width) * height);
                width = max_w;
            }
            if(height > max_h){
                width = ((max_h / height) * width);
                height = max_h;
            }
            // Needs to be uniquely instantiated
            var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
            style_marker.graphicOpacity = 1;
            style_marker.graphicWidth = width;
            style_marker.graphicHeight = height;
            style_marker.graphicXOffset = -(width / 2);
            style_marker.graphicYOffset = -height;
            style_marker.externalGraphic = iconURL;
            var georssLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
                '""" + name_safe + """',
                {
                    """ + projection_str + """
                    strategies: [ """ + strategy_fixed + ", " + strategy_cluster + """ ],
                    style: style_marker,
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: '""" + url + """',
                        format: format_georss
                    })
                }
            );
            """ + visibility + """
            map.addLayer(georssLayer""" + name_safe + """);
            georssLayers.push(georssLayer""" + name_safe + """);
            georssLayer""" + name_safe + """.events.on({ "featureselected": onGeorssFeatureSelect, "featureunselected": onFeatureUnselect });
            """
                layers_georss += """
        allLayers = allLayers.concat(georssLayers);
        """

            # GPX
            gpx_enabled = db(db.gis_layer_gpx.enabled == True).select()
            if gpx_enabled:
                layers_gpx += """
        var georssLayers = new Array();
        var format_gpx = new OpenLayers.Format.GPX();
        function onGpxFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            // Anything we want to do here?
        }
        """
                for layer in gpx_enabled:
                    name = layer["name"]
                    track = db(db.gis_track.id == layer.track_id).select(limitby=(0, 1)).first()
                    url = track.track
                    visible = layer["visible"]
                    marker_id = layer["marker_id"]
                    if marker_id:
                        marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    else:
                        marker = db(db.gis_marker.id == marker_default).select(db.gis_marker.image, limitby=(0, 1)).first().image
                    marker_url = URL(r=request, c="default", f="download", args=marker)

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "gpxLayer" + name_safe + ".setVisibility(true);"
                    else:
                        visibility = "gpxLayer" + name_safe + ".setVisibility(false);"
                    layers_gpx += """
            iconURL = '""" + marker_url + """';
            icon_img.src = iconURL;
            width = icon_img.width;
            height = icon_img.height;
            if(width > max_w){
                height = ((max_w / width) * height);
                width = max_w;
            }
            if(height > max_h){
                width = ((max_h / height) * width);
                height = max_h;
            }
            // Needs to be uniquely instantiated
            var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
            style_marker.graphicOpacity = 1;
            style_marker.graphicWidth = width;
            style_marker.graphicHeight = height;
            style_marker.graphicXOffset = -(width / 2);
            style_marker.graphicYOffset = -height;
            style_marker.externalGraphic = iconURL;
            var gpxLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
                '""" + name_safe + """',
                {
                    projection: proj4326,
                    strategies: [ """ + strategy_fixed + ", " + strategy_cluster + """ ],
                    style: style_marker,
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: '""" + url + """',
                        format: format_gpx
                    })
                }
            );
            """ + visibility + """
            map.addLayer(gpxLayer""" + name_safe + """);
            gpxLayers.push(gpxLayer""" + name_safe + """);
            gpxLayer""" + name_safe + """.events.on({ "featureselected": onGpxFeatureSelect, "featureunselected": onFeatureUnselect });
            """
                layers_gpx += """
        allLayers = allLayers.concat(gpxLayers);
        """

            # KML
            kml_enabled = db(db.gis_layer_kml.enabled == True).select()
            if kml_enabled:
                layers_kml += """
        var kmlLayers = new Array();
        var format_kml = new OpenLayers.Format.KML({
            extractStyles: true,
            extractAttributes: true,
            maxDepth: 2
        })
        function onKmlFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var selectedFeature = feature;
            var type = typeof feature.attributes.name;
            if ('object' == type) {
                var popup = new OpenLayers.Popup.FramedCloud("kmlpopup",
                    feature.geometry.getBounds().getCenterLonLat(),
                    new OpenLayers.Size(200,200),
                    "<h2>" + "</h2>",
                    null, true, onPopupClose
                );
            } else if (undefined == feature.attributes.description) {
                var popup = new OpenLayers.Popup.FramedCloud("kmlpopup",
                    feature.geometry.getBounds().getCenterLonLat(),
                    new OpenLayers.Size(200,200),
                    "<h2>" + feature.attributes.name + "</h2>",
                    null, true, onPopupClose
                );
            } else {
                var content = "<h2>" + feature.attributes.name + "</h2>" + feature.attributes.description;
                // Protect the description against JavaScript attacks
                if (content.search("<script") != -1) {
                    content = "Content contained Javascript! Escaped content below.<br />" + content.replace(/</g, "<");
                }
                var popup = new OpenLayers.Popup.FramedCloud("kmlpopup",
                    feature.geometry.getBounds().getCenterLonLat(),
                    new OpenLayers.Size(200,200),
                    content,
                    null, true, onPopupClose
                );
            };
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in kml_enabled:
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    projection_str = "projection: proj4326,"
                    if cache:
                        # Download file
                        file, warning = self.download_kml(url, public_url)
                        filename = "gis_cache.file." + name.replace(" ", "_") + ".kml"
                        filepath = os.path.join(cachepath, filename)
                        f = open(filepath, "w")
                        # Handle errors
                        if "URLError" in warning or "HTTPError" in warning:
                            # URL inaccessible
                            if os.access(filepath, os.R_OK):
                                statinfo = os.stat(filepath)
                                if statinfo.st_size:
                                    # Use cached version
                                    date = db(db.gis_cache.name == name).select(db.gis_cache.modified_on, limitby=(0, 1)).first().modified_on
                                    response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                                    url = URL(r=request, c="default", f="download", args=[filename])
                                else:
                                    # 0k file is all that is available
                                    response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                                    # skip layer
                                    continue
                            else:
                                # No cached version available
                                response.warning += url + " " + str(T("not accessible - no cached version available!")) + "\n"
                                # skip layer
                                continue
                        else:
                            # Download was succesful
                            if "ParseError" in warning:
                                # @ToDo Parse detail
                                response.warning += str(T("Layer")) + ": " + name + " " + str(T("couldn't be parsed so NetworkLinks not followed.")) + "\n"
                            if "GroundOverlay" in warning or "ScreenOverlay" in warning:
                                response.warning += str(T("Layer")) + ": " + name + " " + str(T("includes a GroundOverlay or ScreenOverlay which aren't supported in OpenLayers yet, so it may not work properly.")) + "\n"
                            # Write file to cache
                            f.write(file)
                            f.close()
                            records = db(db.gis_cache.name == name).select()
                            if records:
                                records[0].update(modified_on=response.utcnow)
                            else:
                                db.gis_cache.insert(name=name, file=filename)
                            url = URL(r=request, c="default", f="download", args=[filename])
                    else:
                        # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                        pass

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "kmlLayer" + name_safe + ".setVisibility(true);"
                    else:
                        visibility = "kmlLayer" + name_safe + ".setVisibility(false);"
                    layers_kml += """
            iconURL = '""" + marker_url + """';
            icon_img.src = iconURL;
            width = icon_img.width;
            height = icon_img.height;
            if(width > max_w){
                height = ((max_w / width) * height);
                width = max_w;
            }
            if(height > max_h){
                width = ((max_h / height) * width);
                height = max_h;
            }
            // Needs to be uniquely instantiated
            var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
            style_marker.graphicOpacity = 1;
            style_marker.graphicWidth = width;
            style_marker.graphicHeight = height;
            style_marker.graphicXOffset = -(width / 2);
            style_marker.graphicYOffset = -height;
            style_marker.externalGraphic = iconURL;
            var kmlLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
                '""" + name_safe + """',
                {
                    """ + projection_str + """
                    strategies: [ """ + strategy_fixed + ", " + strategy_cluster + """ ],
                    style: style_marker,
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: '""" + url + """',
                        format: format_kml
                    })
                }
            );
            """ + visibility + """
            map.addLayer(kmlLayer""" + name_safe + """);
            kmlLayers.push(kmlLayer""" + name_safe + """);
            kmlLayer""" + name_safe + """.events.on({ "featureselected": onKmlFeatureSelect, "featureunselected": onFeatureUnselect });
            """
                layers_kml += """
        allLayers = allLayers.concat(kmlLayers);
        """

        #############
        # Main script
        #############

        html.append(SCRIPT("""
    var map, mapPanel, legendPanel, toolbar;
    var currentFeature, popupControl, highlightControl;
    var wmsBrowser;
    var printProvider, printForm;
    var allLayers = new Array();
    OpenLayers.ImgPath = '/""" + request.application + """/static/img/gis/openlayers/';
    // avoid pink tiles
    OpenLayers.IMAGE_RELOAD_ATTEMPTS = 3;
    OpenLayers.Util.onImageLoadErrorColor = "transparent";
    OpenLayers.ProxyHost = '""" + str(URL(r=request, c="gis", f="proxy")) + """?url=';
    // See http://crschmidt.net/~crschmidt/spherical_mercator.html#reprojecting-points
    var proj4326 = new OpenLayers.Projection('EPSG:4326');
    var projection_current = new OpenLayers.Projection('EPSG:""" + str(projection) + """');
    var lat = """ + str(lat) + """;
    var lon = """ + str(lon) + """;
    var center = new OpenLayers.LonLat(lon, lat);
    center.transform(proj4326, projection_current);
    var options = {
        displayProjection: proj4326,
        projection: projection_current,
        units: '""" + units + """',
        maxResolution: """ + str(maxResolution) + """,
        maxExtent: new OpenLayers.Bounds(""" + maxExtent + """),
        numZoomLevels: """ + str(numZoomLevels) + """
    };

    function addLayers(map) {
        // Base Layers
        // OSM
        """ + layers_openstreetmap + """
        // Google
        """ + layers_google + """
        // Yahoo
        """ + layers_yahoo + """
        // Bing
        """ + layers_bing + """
        // TMS
        """ + layers_tms + """
        // WMS
        """ + layers_wms + """
        // XYZ
        """ + layers_xyz + """
        // JS
        """ + layers_js + """

        // Overlays
        var max_w = 25;
        var max_h = 35;
        var width, height;
        var icon_img = new Image();
        var iconURL;

        // Features
        """ + layers_features + """

        // GeoRSS
        """ + layers_georss + """

        // GPX
        """ + layers_gpx + """

        // KML
        """ + layers_kml + """
    }

    """ + functions_openstreetmap + """

    // Supports popupControl for All Vector Layers
    function onFeatureUnselect(event) {
        var feature = event.feature;
        if (feature.popup) {
            map.removePopup(feature.popup);
            feature.popup.destroy();
            delete feature.popup;
        }
    }
    function onPopupClose(evt) {
        //currentFeature.popup.hide();
        popupControl.unselectAll();
    }

    // Supports highlightControl for All Vector Layers
    var lastFeature = null;
    var tooltipPopup = null;
    function tooltipSelect(event){
        var feature = event.feature;
        if(feature.cluster) {
            // Cluster
            // no tooltip
        } else {
            // Single Feature
            var selectedFeature = feature;
            // if there is already an opened details window, don\'t draw the tooltip
            if(feature.popup != null){
                return;
            }
            // if there are other tooltips active, destroy them
            if(tooltipPopup != null){
                map.removePopup(tooltipPopup);
                tooltipPopup.destroy();
                if(lastFeature != null){
                    delete lastFeature.popup;
                    tooltipPopup = null;
                }
            }
            lastFeature = feature;
            if (undefined == feature.attributes.name) {
                // GeoRSS
                tooltipPopup = new OpenLayers.Popup("activetooltip",
                        feature.geometry.getBounds().getCenterLonLat(),
                        new OpenLayers.Size(80, 12),
                        feature.attributes.title,
                        true
                );
            } else {
                // KML
                tooltipPopup = new OpenLayers.Popup("activetooltip",
                        feature.geometry.getBounds().getCenterLonLat(),
                        new OpenLayers.Size(80, 12),
                        feature.attributes.name,
                        true
                );
            }
            // should be moved to CSS
            tooltipPopup.contentDiv.style.backgroundColor='ffffcb';
            tooltipPopup.closeDiv.style.backgroundColor='ffffcb';
            tooltipPopup.contentDiv.style.overflow='hidden';
            tooltipPopup.contentDiv.style.padding='3px';
            tooltipPopup.contentDiv.style.margin='0';
            tooltipPopup.closeOnMove = true;
            tooltipPopup.autoSize = true;
            feature.popup = tooltipPopup;
            map.addPopup(tooltipPopup);
        }
    }
    function tooltipUnselect(event){
        var feature = event.feature;
        if(feature != null && feature.popup != null){
            map.removePopup(feature.popup);
            feature.popup.destroy();
            delete feature.popup;
            tooltipPopup = null;
            lastFeature = null;
        }
    }

    Ext.onReady(function() {
        map = new OpenLayers.Map('center', options);
        addLayers(map);

        map.addControl(new OpenLayers.Control.ScaleLine());
        map.addControl(new OpenLayers.Control.MGRSMousePosition());
        map.addControl(new OpenLayers.Control.Permalink());
        map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: options}));

        // Popups
        // onClick Popup
        popupControl = new OpenLayers.Control.SelectFeature(
            allLayers, {
                toggle: true,
                clickout: true,
                multiple: false
            }
        );
        // onHover Tooltip
        highlightControl = new OpenLayers.Control.SelectFeature(
            allLayers, {
                hover: true,
                highlightOnly: true,
                renderIntent: "temporary",
                eventListeners: {
                    featurehighlighted: tooltipSelect,
                    featureunhighlighted: tooltipUnselect
                }
            }
        );
        map.addControl(highlightControl);
        map.addControl(popupControl);
        highlightControl.activate();
        popupControl.activate();

        """ + mgrs_html + """

        mapPanel = new GeoExt.MapPanel({
            region: 'center',
            height: """ + str(height) + """,
            width: """ + str(width) + """,
            id: 'mappanel',
            xtype: 'gx_mappanel',
            map: map,
            center: center,
            zoom: """ + str(zoom) + """,
            tbar: new Ext.Toolbar()
        });

        """ + toolbar + """

        """ + search + """

        var layerTreeBase = new GeoExt.tree.BaseLayerContainer({
            text: '""" + str(T("Base Layers")) + """',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        });

        var layerTreeFeaturesExternal = new GeoExt.tree.OverlayLayerContainer({
            text: '""" + str(T("External Features")) + """',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        });

        var layerTreeFeaturesInternal = new GeoExt.tree.OverlayLayerContainer({
            //text: '""" + str(T("Internal Features")) + """',
            text: '""" + str(T("Overlays")) + """',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        });

        """ + layers_wms_browser + """

        var layerTree = new Ext.tree.TreePanel({
            id: 'treepanel',
            title: '""" + str(T("Layers")) + """',
            root: new Ext.tree.AsyncTreeNode({
                expanded: true,
                children: [
                    layerTreeBase,
                    //layerTreeFeaturesExternal,
                    layerTreeFeaturesInternal
                ]
            }),
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            enableDD: true
        });

        legendPanel = new GeoExt.LegendPanel({
            id: 'legendpanel',
            title: '""" + str(T("Legend")) + """',
            defaults: {
                labelCls: 'mylabel',
                style: 'padding:5px'
            },
            bodyStyle: 'padding:5px',
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false
        });
        
        """ + print_tool1 + """

        """ + layout + """
            autoScroll: true,
            maximizable: true,
            titleCollapse: true,
            height: """ + str(height) + """,
            width: """ + str(width) + """,
            layout: 'border',
            items:  [{
                        region: 'west',
                        id: 'tools',
                        title: '""" + str(T("Tools")) + """',
                        border: true,
                        width: 250,
                        collapsible: true,
                        split: true,
                        items: [
                            layerTree""" + layers_wms_browser2 + search2 + print_tool2 + """, legendPanel
                            ]
                    },
                    mapPanel
                    ]
        });
        """ + layout2 + """
        """ + toolbar2 + """
    });
    """))

        return html.xml()

    def parse_location(self, wkt, lon=None, lat=None):
        """
            Parses a location from wkt, returning wkt, lat, lon, bounding box and type.
            For points, wkt may be None if lat and lon are provided; wkt will be generated.
            For lines and polygons, the lat, lon returned represent the shape's centroid.
            Centroid and bounding box will be None if shapely is not available.
        """

        if not wkt:
            assert lon is not None and lat is not None, "Need wkt or lon+lat to parse a location"
            wkt = "POINT(%f %f)" % (lon, lat)
            geom_type = GEOM_TYPES["point"]
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
                geom_type = GEOM_TYPES[wkt.split("(")[0].lower()]
                bbox = None

        res = {"wkt": wkt, "lat": lat, "lon": lon, "gis_feature_type": geom_type}
        if bbox:
            res["lon_min"], res["lat_min"], res["lon_max"], res["lat_max"] = bbox

        return res

    def update_location_tree(self):
        """
            Update the Tree for GIS Locations:
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
        """

        db = self.db

        # tbc

        return

    def wkt_centroid(self, form):
        """
            OnValidation callback:
            If a Point has LonLat defined: calculate the WKT.
            If a Line/Polygon has WKT defined: validate the format & calculate the LonLat of the Centroid
            Centroid calculation is done using Shapely, which wraps Geos.
            A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm
        """

        if form.vars.gis_feature_type == "1":
            # Point
            if form.vars.lon == None and form.vars.lat == None:
                # No geo to create WKT from, so skip
                return
            elif form.vars.lat == None:
                form.errors["lat"] = self.messages.lat_empty
                return
            elif form.vars.lon == None:
                form.errors["lon"] = self.messages.lon_empty
                return
            else:
                form.vars.wkt = "POINT(%(lon)f %(lat)f)" % form.vars
                return

        elif form.vars.gis_feature_type == "2":
            # Line
            try:
                try:
                    line = wkt_loads(form.vars.wkt)
                except:
                    form.errors["wkt"] = self.messages.invalid_wkt_linestring
                    return
                centroid_point = line.centroid
                form.vars.lon = centroid_point.wkt.split("(")[1].split(" ")[0]
                form.vars.lat = centroid_point.wkt.split("(")[1].split(" ")[1][:1]
            except:
                form.errors.gis_feature_type = self.messages.centroid_error
        elif form.vars.gis_feature_type == "3":
            # Polygon
            try:
                try:
                    polygon = wkt_loads(form.vars.wkt)
                except:
                    form.errors["wkt"] = self.messages.invalid_wkt_polygon
                    return
                centroid_point = polygon.centroid
                form.vars.lon = centroid_point.wkt.split("(")[1].split(" ")[0]
                form.vars.lat = centroid_point.wkt.split("(")[1].split(" ")[1][:1]
            except:
                form.errors.gis_feature_type = self.messages.centroid_error

        else:
            form.errors.gis_feature_type = self.messages.unknown_type

        return

    def bbox_intersects(self, lon_min, lat_min, lon_max, lat_max):
        db = self.db
        return db((db.gis_location.lat_min <= lat_max) &
            (db.gis_location.lat_max >= lat_min) &
            (db.gis_location.lon_min <= lon_max) &
            (db.gis_location.lon_max >= lon_min))

    def _intersects(self, shape):
        """
            Returns Rows of locations whose shape intersects the given shape
        """

        db = self.db
        for loc in self.bbox_intersects(*shape.bounds).select():
            location_shape = wkt_loads(loc.wkt)
            if location_shape.intersects(shape):
                yield loc

    def _intersects_latlon(self, lat, lon):
        """
            Returns a generator of locations whose shape intersects the given LatLon
        """

        point = shapely.geometry.point.Point(lon, lat)
        return self.intersects(point)

    if SHAPELY:
        intersects = _intersects
        intersects_latlon = _intersects_latlon


class Geocoder(object):
    " Base class for all geocoders "

    def __init__(self):
        " Initializes the page content object "
        self.page = ""

    def read_details(self, url):
        self.page = fetch(url)

class GoogleGeocoder(Geocoder):
    " Google Geocoder module "

    def __init__(self, location, db, domain="maps.google.com", resource="maps/geo", output_format="kml"):
        " Initialize the values based on arguments or default settings "
        self.api_key = self.get_api_key()
        self.domain = domain
        self.resource = resource
        self.params = {"q": location, "key": self.api_key}
        self.url = "http://%(domain)s/%(resource)?%%s" % locals()
        self.db = db

    def get_api_key(self):
        " Acquire API key from the database "
        query = self.db.gis_apikey.name == "google"
        return self.db(query).select(db.gis_apikey.apikey, limitby=(0, 1)).first().apikey

    def construct_url(self):
        " Construct the URL based on the arguments passed "
        self.url = self.url % urllib.urlencode(params)

    def get_kml(self):
        " Returns the output in KML format "
        return self.page.read()

class YahooGeocoder(Geocoder):
    " Yahoo Geocoder module "

    def __init__(self, location, db):
        " Initialize the values based on arguments or default settings "
        self.api_key = self.get_api_key()
        self.location = location
        self.params = {"location": self.location, "appid": self.app_key}
        self.db = db

    def get_api_key(self):
        " Acquire API key from the database "
        query = self.db.gis_apikey.name == "yahoo"
        return self.db(query).select(db.gis_apikey.apikey, limitby=(0, 1)).first().apikey

    def construct_url(self):
        " Construct the URL based on the arguments passed "
        self.url = self.url % urllib.urlencode(params)

    def get_xml(self):
        " Return the output in XML format "
        return self.page.read()
