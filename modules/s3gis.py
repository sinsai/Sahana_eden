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

    def __init__(self, environment, db, auth=None):
        self.environment = Storage(environment)
        self.request = self.environment.request
        self.response = self.environment.response
        self.session = self.environment.session
        self.T = self.environment.T
        assert db is not None, "Database must not be None."
        self.db = db
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

    def config_read(self):
        """
            Reads the current GIS Config from the DB 
        """

        db = self.db

        config = db(db.gis_config.id == 1).select().first()

        return config

    def download_kml(self, url, S3_PUBLIC_URL):
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

        if len(url) > len(S3_PUBLIC_URL) and url[:len(S3_PUBLIC_URL)] == S3_PUBLIC_URL:
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
                        file, warning2 = self.download_kml(url, S3_PUBLIC_URL)
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
            config = self.config_read()
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
            config = self.config_read()
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
        """
            Returns the Marker URL for a Feature
        """

        db = self.db

        config = self.config_read()
        symbology = config.symbology_id

        marker = False
        if type(feature_id) == int:
            # ID passed
            feature = db(db.gis_location.id == feature_id).select().first()
        elif type(feature_id) == str:
            # UUID passed
            feature = db(db.gis_location.uuid == feature_id).select().first()
        else:
            # Unknown type - something wrong, so fallback to default!
            marker = config.marker_id
        try:
            feature_class = feature.feature_class_id
        except:
            # Feature not found, so fallback to default!
            marker = config.marker_id

        if not marker:
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
                        marker = db(db.gis_feature_class.id == feature_class).select().first()
                        if marker:
                            marker = marker.marker_id
                    if not marker:
                        # 4th choice for a Marker is the default
                        marker = config.marker_id

        marker = db(db.gis_marker.id == marker).select().first().image

        return marker
    
    def latlon_to_wkt(self, lat, lon):
        """
            Convert a LatLon to a WKT string

            >>> s3gis.latlon_to_wkt(6, 80)
            'POINT(80 6)'
        """
        WKT = "POINT(%f %f)" % (lon, lat)
        return WKT

    def show_map( self,
                  height = None,
                  width = None,
                  lat = None,
                  lon = None,
                  zoom = None,
                  feature_overlays = [],
                  catalogue_overlays = False,
                  catalogue_toolbar = False,
                  toolbar = False,
                  mgrs = False,
                  window = False,
                  S3_PUBLIC_URL = "http://127.0.0.1:8000"):
        """
            Returns the HTML to display a map

            @param height: Height of viewport
            @param width: Width of viewport
            @param lat: default Latitude of viewport
            @param lon: default Longitude of viewport
            @param zoom: default Zoom level of viewport
            @param feature_overlays: Which Feature Groups to overlay onto the map & their options (List of Dicts):
                [{
                 feature_group : db.gis_feature_group.name,
                 filter : None,         # A query to limit which features from the feature group are loaded
                 active : False,        # Is the feed displayed upon load or needs ticking to load afterwards?
                 popup_url : None,      # The URL which will be used to fill the pop-up. it will be appended by the Location ID.
                 marker : None          # The icon used to display the feature (over-riding the normal process). Can be a lambda to vary icon (size/colour) based on attribute levels.
                }]
            @param catalogue_overlays: Show the Overlays from the GIS Catalogue (@ToDo: make this a dict of which external overlays to allow)
            @param catalogue_toolbar: Show the Catalogue Toolbar
            @param toolbar: Show the Icon Toolbar of Controls
            @param mgrs: Use the MGRS Control to select PDFs
            @param window: Have viewport pop out of page into a resizable window
            @param S3_PUBLIC_URL: pass from model (not yet defined when Module instantiated

            @ToDo: Rewrite these to use the API:
                map_viewing_client()
                display_feature()
                display_features()
        """

        request = self.request
        response = self.response
        session = self.session
        T = self.T
        db = self.db
        auth = self.auth

        # Read configuration
        config = self.config_read()
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
        _projection = config.projection_id
        projection = db(db.gis_projection.id==_projection).select().first().epsg
        epsg = db(db.gis_projection.epsg==projection).select().first()
        units = epsg.units
        maxResolution = epsg.maxResolution
        maxExtent = epsg.maxExtent
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
                config_button = TD( A(T("Defaults"), _id="configs-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="config", args=["1", "update"])), _class="btn-panel" )
            else:
                config_button = TD( A(T("Defaults"), _id="configs-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="config", args=["1", "display"])), _class="btn-panel" )
            catalogue_toolbar = TABLE(TR(
                config_button,
                TD( A(T("Locations"), _id="features-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="location")), _class="btn-panel" ),
                TD( A(T("Feature Classes"), _id="feature_classes-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="feature_class")), _class="btn-panel" ),
                TD( A(T("Feature Groups"), _id="feature_groups-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="feature_group")), _class="btn-panel" ),
                TD( A(T("Keys"), _id="keys-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="apikey")), _class="btn-panel" ),
                TD( A(T("Layers"), _id="layers-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="map_service_catalogue")), _class="btn-panel" ),
                TD( A(T("Markers"), _id="markers-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="marker")), _class="btn-panel" ),
                TD( A(T("Projections"), _id="projections-btn", _class="toolbar-link", _href=URL(r=request, c="gis", f="projection")), _class="btn-panel" ),
            ))
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
            
        # Toolbar
        if toolbar:
            toolbar = """
    toolbar = mapPanel.getTopToolbar();
    """
            toolbar2 = "Ext.QuickTips.init();"
        else:
            toolbar = ""
            toolbar2 = ""

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
            #    [{
            #    feature_group : db.gis_feature_group.name,
            #    filter : None,         # A query to limit which features from the feature group are loaded
            #    active : True,         # Is the feed displayed upon load or needs ticking to load afterwards?
            #    popup_url : <default>, # The URL which will be used to fill the pop-up. it will be appended by the Location ID.
            #    marker : <default>     # The icon used to display the feature. Can be a lambda to vary icon (size/colour) based on attribute levels.
            #   }]

            for layer in feature_overlays:
                name = layer["feature_group"]
                url = S3_PUBLIC_URL + "/" + request.application + "/gis/location.kml?feature_group=" + urllib.quote(name)
                if "popup_url" in layer:
                    popup_url = layer["popup_url"]
                # We'd like to do something like this:
                #elif feature_class is office:
                #    popup_url = str(URL(r=request, c="or", f="office"))
                else:
                    popup_url = str(URL(r=request, c="gis", f="location"))
                if cache:
                    # Download file
                    file, warning = self.download_kml(url, S3_PUBLIC_URL)
                    filename = "gis_cache.file." + name.replace(" ", "_") + ".kml"
                    filepath = os.path.join(cachepath, filename)
                    f = open(filepath, "w")
                    # Handle errors
                    if "URLError" in warning or "HTTPError" in warning:
                        # URL inaccessible
                        if os.access(filepath, os.R_OK):
                            # Use cached version
                            date = db(db.gis_cache.name == name).select().first().modified_on
                            response.warning += url + " " + str(T("not accessible - using cached version from")) + " " + str(date) + "\n"
                            url = URL(r=request, c="default", f="download", args=[filename])
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
                if "active" in layer and layer["active"]:
                    visibility = "featureLayer" + name_safe +".setVisibility(true);"
                else:
                    visibility = "featureLayer" + name_safe +".setVisibility(false);"
                layers_features += """
        var featureLayer""" + name_safe + """ = new OpenLayers.Layer.GML( '""" + name + """', '""" + url + """', {
            strategies: [ strategy ],
            format: OpenLayers.Format.KML,
            formatOptions: { extractStyles: true, extractAttributes: true, maxDepth: 2 },
            projection: proj4326});
        """ + visibility + """
        map.addLayer(featureLayer""" + name_safe + """);
        featureLayer""" + name_safe + """.events.on({ "featureselected": onKmlFeatureSelect""" + name_safe + """, "featureunselected": onFeatureUnselect });
        allLayers.push(featureLayer""" + name_safe + """);
        
        function loadDetails(url, id) {
            $.getS3(
                    url,
                    function(data) {
                        $('#' + id).html(data);
                    },
                    'html',
                    'popup'
                );
        }

        function onKmlFeatureSelect""" + name_safe + """(event) {
            // unselect any previous selections
            //tooltipUnselect(event);
            var feature = event.feature;
            var selectedFeature = feature;
            var id = 'featureLayer""" + name_safe + """' + '_' + Math.floor(Math.random()*1001)
            var popup = new OpenLayers.Popup.FramedCloud(
                id,
                feature.geometry.getBounds().getCenterLonLat(),
                new OpenLayers.Size(400, 400),
                "<div style='height: 400px; width: 400px;'>Loading...<img src='""" + str(URL(r=request, c="static", f="img")) + """/ajax-loader.gif' border=0></div>",
                null,
                true,
                onPopupClose
            );
            feature.popup = popup;
            map.addPopup(popup);
            // call AJAX to get the data
            loadDetails('""" + popup_url + """' + '?location.uid=' + feature.attributes.styleUrl.replace(new RegExp('^[#"]+', 'g'), ''), id);
        }
                """

        else:
            # No Feature Layers requested
            pass

        #
        # Base Layers
        #

        # OpenStreetMap
        gis_layer_openstreetmap_subtypes = ["Mapnik", "Osmarender"] # Copied from Model - Need to DRY!
        openstreetmap = Storage()
        openstreetmap_enabled = db(db.gis_layer_openstreetmap.enabled==True).select()
        for layer in openstreetmap_enabled:
            for subtype in gis_layer_openstreetmap_subtypes:
                if layer.subtype == subtype:
                    openstreetmap["%s" % subtype] = layer.name

        functions_openstreetmap = ""
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

        layers_openstreetmap = ""
        if projection==900913:
            # Only enable commercial base layers if using a sphericalMercator projection
            if openstreetmap:
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

            google = db(db.gis_layer_google.enabled==True).select()
            if google:
                # @ToDo
                layers_google = ""
            else:
                layers_google = ""
            yahoo = db(db.gis_layer_yahoo.enabled==True).select()
            if yahoo:
                # @ToDo
                layers_yahoo = ""
            else:
                layers_yahoo = ""
            #bing = db(db.gis_layer_bing.enabled==True).select()
            bing = False
            if bing:
                # @ToDo
                layers_bing = ""
            else:
                layers_bing = ""
        layers_tms = ""
        layers_wms = ""
        layers_xyz = ""
        layers_js = ""
        if catalogue_overlays:
            # @ToDo
            layers_wms += ""
            layers_georss = ""
            layers_gpx = ""
            layers_kml = ""
        else:
            layers_georss = ""
            layers_gpx = ""
            layers_kml = ""

        #############
        # Main script
        #############

        html.append(SCRIPT("""
    var map, mapPanel, toolbar;
    var currentFeature, popupControl;
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
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        var icon_img = new Image();
        var max_w = 25;
        var max_h = 35;
        var width, height;
        var iconURL;
        var strategy = new OpenLayers.Strategy.Cluster({distance: """ + str(cluster_distance) + """, threshold: """ + str(cluster_threshold) + """});
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

    // ol_vector_registerEvents.js

    // ol_controls_features.js

    // Supports selectControl for All Feature Layers
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

    // ol_functions.js

    Ext.onReady(function() {
        map = new OpenLayers.Map('center', options);
        addLayers(map);
        
        // ol_layers_features_all.js
        map.addControl(new OpenLayers.Control.ScaleLine());
        map.addControl(new OpenLayers.Control.MGRSMousePosition());
        map.addControl(new OpenLayers.Control.Permalink());
        map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: options}));
        popupControl = new OpenLayers.Control.SelectFeature(allLayers);
        map.addControl(popupControl);
        popupControl.activate();
        
        // MGRS from ol_controls.js
    
        var mapPanel = new GeoExt.MapPanel({
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

        var layerTree = new Ext.tree.TreePanel({
            id: 'treepanel',
            title: '""" + str(T("Layers")) + """',
            root: new Ext.tree.AsyncTreeNode({
                expanded: true,
                children: [layerTreeBase, layerTreeFeaturesInternal]
                //children: [layerTreeBase, layerTreeFeaturesExternal, layerTreeFeaturesInternal]
            }),
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            enableDD: true
        });

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

        """ + layout + """
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
                            layerTree,
                            searchCombo
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
        return self.db(query).select().first().apikey

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
        return self.db(query).select().first().apikey

    def construct_url(self):
        " Construct the URL based on the arguments passed "
        self.url = self.url % urllib.urlencode(params)

    def get_xml(self):
        " Return the output in XML format "
        return self.page.read()
