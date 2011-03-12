# -*- coding: utf-8 -*-

""" GIS Module

    @version: 0.0.9

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{shapely}} <http://trac.gispython.org/lab/wiki/Shapely>}

    @author: Fran Boon <francisboon[at]gmail.com>
    @author: Timothy Caro-Bruce <tcarobruce[at]gmail.com>

    @copyright: (c) 2010-2011 Sahana Software Foundation
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
import math             # Needed for greatCircleDistance
import os
import re
import sys
import random           # Needed when feature_queries are passed in without a name
import urllib           # Needed for urlencoding
import urllib2          # Needed for error handling on fetch
import uuid
import Cookie           # Needed for Sessions on Internal KML feeds
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO
import zipfile          # Needed to unzip KMZ files
from lxml import etree  # Needed to follow NetworkLinks
KML_NAMESPACE = "http://earth.google.com/kml/2.2"
# Which resources have a different icon per-category
gis_categorised_resources = ["irs_ireport"]

from gluon.dal import Rows
from gluon.storage import Storage, Messages
from gluon.html import *
#from gluon.http import HTTP
from gluon.tools import fetch

def s3_debug(message, value=None):
    """
        Provide an easy, safe, systematic way of handling Debug output
        (print to stdout doesn't work with WSGI deployments)
    """
    try:
        output = "S3 Debug: " + str(message)
        if value:
            output += ": " + str(value)
    except:
        output = "S3 Debug: " + unicode(message)
        if value:
            output += ": " + unicode(value)

    print >> sys.stderr, output

SHAPELY = False
try:
    import shapely
    import shapely.geometry
    from shapely.wkt import loads as wkt_loads
    SHAPELY = True
except ImportError:
    s3_debug("WARNING: %s: Shapely GIS library not installed" % __name__)

# Map WKT types to db types (multi-geometry types are mapped to single types)
GEOM_TYPES = {
    "point": 1,
    "multipoint": 1,
    "linestring": 2,
    "multilinestring": 2,
    "polygon": 3,
    "multipolygon": 3,
}

# km
RADIUS_EARTH = 6371.01

# Garmin GPS Symbols
GPS_SYMBOLS = [
    "Airport",
    "Amusement Park"
    "Ball Park",
    "Bank",
    "Bar",
    "Beach",
    "Bell",
    "Boat Ramp",
    "Bowling",
    "Bridge",
    "Building",
    "Campground",
    "Car",
    "Car Rental",
    "Car Repair",
    "Cemetery",
    "Church",
    "Circle with X",
    "City (Capitol)",
    "City (Large)",
    "City (Medium)",
    "City (Small)",
    "Civil",
    "Controlled Area",
    "Convenience Store",
    "Crossing",
    "Dam",
    "Danger Area",
    "Department Store",
    "Diver Down Flag 1",
    "Diver Down Flag 2",
    "Drinking Water",
    "Exit",
    "Fast Food",
    "Fishing Area",
    "Fitness Center",
    "Flag",
    "Forest",
    "Gas Station",
    "Geocache",
    "Geocache Found",
    "Ghost Town",
    "Glider Area",
    "Golf Course",
    "Green Diamond",
    "Green Square",
    "Heliport",
    "Horn",
    "Hunting Area",
    "Information",
    "Levee",
    "Light",
    "Live Theater",
    "Lodging",
    "Man Overboard",
    "Marina",
    "Medical Facility",
    "Mile Marker",
    "Military",
    "Mine",
    "Movie Theater",
    "Museum",
    "Navaid, Amber",
    "Navaid, Black",
    "Navaid, Blue",
    "Navaid, Green",
    "Navaid, Green/Red",
    "Navaid, Green/White",
    "Navaid, Orange",
    "Navaid, Red",
    "Navaid, Red/Green",
    "Navaid, Red/White",
    "Navaid, Violet",
    "Navaid, White",
    "Navaid, White/Green",
    "Navaid, White/Red",
    "Oil Field",
    "Parachute Area",
    "Park",
    "Parking Area",
    "Pharmacy",
    "Picnic Area",
    "Pizza",
    "Post Office",
    "Private Field",
    "Radio Beacon",
    "Red Diamond",
    "Red Square",
    "Residence",
    "Restaurant",
    "Restricted Area",
    "Restroom",
    "RV Park",
    "Scales",
    "Scenic Area",
    "School",
    "Seaplane Base",
    "Shipwreck",
    "Shopping Center",
    "Short Tower",
    "Shower",
    "Skiing Area",
    "Skull and Crossbones",
    "Soft Field",
    "Stadium",
    "Summit",
    "Swimming Area",
    "Tall Tower",
    "Telephone",
    "Toll Booth",
    "TracBack Point",
    "Trail Head",
    "Truck Stop",
    "Tunnel",
    "Ultralight Area",
    "Water Hydrant",
    "Waypoint",
    "White Buoy",
    "White Dot",
    "Zoo"
    ]

# -----------------------------------------------------------------------------
class GIS(object):
    """ GIS functions """

    def __init__(self, environment, deployment_settings, db, auth=None, cache=None):
        self.environment = Storage(environment)
        self.request = self.environment.request
        self.response = self.environment.response
        self.session = self.environment.session
        self.T = self.environment.T
        self.deployment_settings = deployment_settings
        assert db is not None, "Database must not be None."
        self.db = db
        self.cache = cache and (cache.ram, 60) or None
        assert auth is not None, "Undefined authentication controller"
        self.auth = auth
        self.messages = Messages(None)
        #self.messages.centroid_error = str(A("Shapely", _href="http://pypi.python.org/pypi/Shapely/", _target="_blank")) + " library not found, so can't find centroid!"
        self.messages.centroid_error = "Shapely library not functional, so can't find centroid! Install Geos & Shapely for Line/Polygon support"
        self.messages.unknown_type = "Unknown Type!"
        self.messages.invalid_wkt_point = "Invalid WKT: Must be like POINT(3 4)!"
        self.messages.invalid_wkt_linestring = "Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!"
        self.messages.invalid_wkt_polygon = "Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!"
        self.messages.lon_empty = "Invalid: Longitude can't be empty if Latitude specified!"
        self.messages.lat_empty = "Invalid: Latitude can't be empty if Longitude specified!"
        self.messages.unknown_parent = "Invalid: %(parent_id)s is not a known Location"
        self.messages["T"] = self.T
        self.messages.lock_keys = True
        self.gps_symbols = GPS_SYMBOLS

    # -----------------------------------------------------------------------------
    def abbreviate_wkt(self, wkt, max_length=30):
        if not wkt:
            # Blank WKT field
            return None
        elif len(wkt) > max_length:
            return "%s(...)" % wkt[0:wkt.index("(")]
        else:
            return wkt

    # -----------------------------------------------------------------------------
    def download_kml(self, url, public_url):
        """
        Download a KML file:
            - unzip it if-required
            - follow NetworkLinks recursively if-required

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

    # -----------------------------------------------------------------------------
    def get_api_key(self, layer="google"):
        " Acquire API key from the database "

        db = self.db
        query = db.gis_apikey.name == layer
        result = db(query).select(db.gis_apikey.apikey, limitby=(0, 1)).first()
        if result:
            return result.apikey
        else:
            return None

    # -----------------------------------------------------------------------------
    def get_bearing(self, lat_start, lon_start, lat_end, lon_end):
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

    # -----------------------------------------------------------------------------
    def get_bounds(self, features=[]):
        """
            Calculate the Bounds of a list of Features
            e.g. to use in GPX export for correct zooming
            Ensure a minimum size of bounding box, and that the points
            are inset from the border.
            @ToDo: Optimised Geospatial routines rather than this crude hack
        """

        config = self.get_config()
        if not config.bbox_min_size:
            # DB not a fresh one, so new values not prepopulated
            # @ToDo: clean up when we don't have legacy systems to upgrade
            config.bbox_min_size = 0.01
        if not config.bbox_inset:
            config.bbox_inset = 0.007

        if len(features) > 0:

            min_lon = 180
            min_lat = 90
            max_lon = -180
            max_lat = -90

            for feature in features:

                # Skip features without lon, lat.
                try:
                    # A simple feature set?
                    lon = feature.lon
                    lat = feature.lat

                except:
                    try:
                        # A Join
                        lon = feature.gis_location.lon
                        lat = feature.gis_location.lat

                    except:
                        continue

                # Also skip those set to None. Note must use explicit test,
                # as zero is a legal value.
                if lon is None or lat is None:
                    continue

                min_lon = min(lon, min_lon)
                min_lat = min(lat, min_lat)
                max_lon = max(lon, max_lon)
                max_lat = max(lat, max_lat)

        else: # no features
            min_lon = max_lon = config.lon
            min_lat = max_lat = config.lat

        # Assure a reasonable-sized box.
        delta_lon = (config.bbox_min_size - (max_lon - min_lon)) / 2.0
        if delta_lon > 0:
            min_lon -= delta_lon
            max_lon += delta_lon
        delta_lat = (config.bbox_min_size - (max_lat - min_lat)) / 2.0
        if delta_lat > 0:
            min_lat -= delta_lat
            max_lat += delta_lat

        # Move bounds outward by specified inset.
        min_lon -= config.bbox_inset
        max_lon += config.bbox_inset
        min_lat -= config.bbox_inset
        max_lat += config.bbox_inset

        # Check that we're still within overall bounds
        min_lon = max(config.min_lon, min_lon)
        min_lat = max(config.min_lat, min_lat)
        max_lon = min(config.max_lon, max_lon)
        max_lat = min(config.max_lat, max_lat)

        return dict(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)

    # -------------------------------------------------------------------------
    def _lookup_parent_path(self, feature_id):
        """
        Helper that gets parent and path for a location.
        """

        db = self.db
        _locations = db.gis_location

        deleted = (_locations.deleted == False)
        query = deleted & (_locations.id == feature_id)
        feature = db(query).select(
                  _locations.path, _locations.parent,
                  limitby=(0, 1)).first()

        return feature

    # -------------------------------------------------------------------------
    def get_children(self, parent_id):
        """
        Return a list of all GIS Features which are children of
        the requested feature, using Materialized path for retrieving
        the children

        @author: Aravind Venkatesan and Ajay Kumar Sreenivasan from NCSU

        This has been chosen over Modified Preorder Tree Traversal for greater efficiency:
        http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees

        Assists lazy update of a database without location paths by calling
        update_location_tree to get the path.
        """

        parent_row = self._lookup_parent_path(parent_id)
        path = parent_row.path
        if parent_row.parent and not path:
            path = self.update_location_tree(parent_id, feature.parent)

        for row in db(table.path.like(path + "/%")).select():
            list.append(row.id)

        return list

    # -------------------------------------------------------------------------
    def get_parents(self, feature_id, feature=None, ids_only=False):
        """
        Returns a list containing ancestors of the requested feature.

        If the caller already has the location row, including path and parent
        fields, they can supply it via feature to avoid a db lookup.

        If ids_only is false, each element in the list is a gluon.sql.Row
        containing the gis_location record of an ancestor of the specified
        location.

        If ids_only is true, just returns a list of ids of the parents.
        This avoids a db lookup for the parents if the specified feature has
        a path.

        List elements are in the opposite order as the location path and
        exclude the specified location itself, i.e. element 0 is the parent
        and the last element is the most distant ancestor.

        Assists lazy update of a database without location paths by calling
        update_location_tree to get the path.
        """

        db = self.db
        _locations = db.gis_location

        if not feature or "path" not in feature or "parent" not in feature:
            feature = self._lookup_parent_path(feature_id)

        if feature and (feature.path or feature.parent):
            if feature.path:
                path = feature.path
            else:
                path = self.update_location_tree(feature_id, feature.parent)

            path_list = map(int, path.split("/"))
            if len(path_list) == 1:
                # No parents -- path contains only this feature.
                return None

            # Get path in the desired order, without current feature.
            reverse_path = path_list[0:len(path_list)-1]
            reverse_path.reverse()

            # If only ids are wanted, stop here.
            if ids_only:
                return reverse_path

            # Retrieve parents -- order in which they're returned is arbitrary.
            unordered_parents = db(_locations.id.belongs(reverse_path)).select()

            # Reorder parents in order of reversed path.
            unordered_ids = [row.id for row in unordered_parents]
            parents = [unordered_parents[unordered_ids.index(path_id)]
                       for path_id in reverse_path if path_id in unordered_ids]

            return parents

        else:
            return None

    # -------------------------------------------------------------------------
    def get_parent_per_level(self, results, feature_id, feature=None, names=False):
        """
        Adds ancestor of requested feature for each level to supplied dict.

        If the caller already has the location row, including path and parent
        fields, they can supply it via feature to avoid a db lookup.

        If a dict is not supplied in results, one is created. The results
        dict is returned in either case.

        If names=True (used by address_onvalidation) then:
        For each ancestor, an entry ancestor.level : ancestor.name is added to
        results.

        If names=False (used by S3LocationSelectorWidget) then:
        For each ancestor, an entry ancestor.level : ancestor.id is added to
        results.
        """

        if not results:
            results = {}

        if not feature or "path" not in feature or "parent" not in feature:
            feature = self._lookup_parent_path(feature_id)

        if feature and (feature.path or feature.parent):
            if feature.path:
                path = feature.path
            else:
                path = self.update_location_tree(feature_id, feature.parent)

            # Get ids of ancestors at each level.
            strict = self.deployment_settings.get_gis_strict_hierarchy()
            if path and strict and not names:
                # No need to do a db lookup for parents in this case -- we
                # know the levels of the parents from their position in path.
                # Note ids returned from db are ints, not strings, so be
                # consistent with that.
                path_ids = map(int, path.split("/"))
                # This skips the last path element, which is the supplied
                # location.
                for (i, id) in enumerate(path_ids[0:len(path_ids)-1]):
                    results["L%i" % i] = id
            elif path or parent:
                ancestors = self.get_parents(feature_id, feature=feature)
                if ancestors:
                    for ancestor in ancestors:
                        if names:
                            results[ancestor.level] = ancestor.name
                        else:
                            results[ancestor.level] = ancestor.id

        return results

    # -----------------------------------------------------------------------------
    def get_config(self):
        " Reads the current GIS Config from the DB "

        auth = self.auth
        db = self.db

        _config = db.gis_config
        _projection = db.gis_projection

        # Default config is the 1st
        config = 1
        if auth.is_logged_in():
            # Read personalised config, if available
            personalised = db((db.pr_person.uuid == auth.user.person_uuid) & (_config.pe_id == db.pr_person.pe_id)).select(_config.id, limitby=(0, 1)).first()
            if personalised:
                config = personalised.id

        query = (_config.id == config)

        query = query & (_projection.id == _config.projection_id)
        config = db(query).select(limitby=(0, 1)).first()

        output = Storage()
        for item in config["gis_config"]:
            output[item] = config["gis_config"][item]

        for item in config["gis_projection"]:
            if item in ["epsg", "units", "maxResolution", "maxExtent"]:
                output[item] = config["gis_projection"][item]

        return output

    # -----------------------------------------------------------------------------
    def get_feature_class_id_from_name(self, name):
        """
            Returns the Feature Class ID from it's name
        """

        db = self.db

        feature = db(db.gis_feature_class.name == name).select(db.gis_feature_class.id, limitby=(0, 1)).first()
        if feature:
            return feature.id
        else:
            return None

    # -----------------------------------------------------------------------------
    def get_feature_layer(self, prefix, resourcename, layername, popup_label, config=None, marker_id=None, filter=None, active=True, polygons=False, opacity=1):
        """
        Return a Feature Layer suitable to display on a map
        @param layername: used as the label in the LayerSwitcher
        @param popup_label: used in Cluster Popups to differentiate between types
        """
        db = self.db
        cache = self.cache
        auth = self.auth
        deployment_settings = self.deployment_settings
        request = self.request

        _locations = db.gis_location
        _markers = db.gis_marker

        tablename = "%s_%s" % (prefix, resourcename)

        try:
            table = db[tablename]
            if "deleted" in table.fields:
                # Hide deleted Resources
                query = (table.deleted == False)
            else:
                query = (table.id > 0)

            if filter:
                query = query & (db[filter.tablename].id == filter.id)

            # Hide Resources recorded to Country Locations on the map?
            if not deployment_settings.get_gis_display_l0():
                query = query & ((_locations.level != "L0") | (_locations.level == None))

            query = query & (_locations.id == db["%s_%s" % (prefix, resourcename)].location_id)
            if not polygons and not resourcename in gis_categorised_resources:
                # Only retrieve the bulky polygons if-required
                locations = db(query).select(_locations.id, _locations.uuid, _locations.parent, _locations.name, _locations.lat, _locations.lon)
            elif not polygons and resourcename in gis_categorised_resources:
                locations = db(query).select(_locations.id, _locations.uuid, _locations.parent, _locations.name, _locations.lat, _locations.lon, table.category)
            elif polygons and not resourcename in gis_categorised_resources:
                locations = db(query).select(_locations.id, _locations.uuid, _locations.parent, _locations.name, _locations.wkt, _locations.lat, _locations.lon)
            else:
                # Polygons & Categorised resources
                locations = db(query).select(_locations.id, _locations.uuid, _locations.parent, _locations.name, _locations.wkt, _locations.lat, _locations.lon, table.category)

            if resourcename in gis_categorised_resources:
                for i in range(0, len(locations)):
                    locations[i].popup_label = "%s-%s" % (locations[i].name, popup_label)
                    locations[i].marker = self.get_marker(tablename, locations[i][tablename].category)
            else:
                for i in range(0, len(locations)):
                    locations[i].popup_label = "%s-%s" % (locations[i].name, popup_label)

            popup_url = URL(r=request, c=prefix, f=resourcename, args="read.plain?%s.location_id=" % resourcename)

            if not marker_id and not resourcename in gis_categorised_resources:
                # Add the marker here so that we calculate once/layer not once/feature
                table_fclass = db.gis_feature_class
                if not config:
                    config = self.get_config()
                query = (table_fclass.deleted == False) & (table_fclass.symbology_id == config.symbology_id) & (table_fclass.resource == resourcename)
                marker = db(query).select(db.gis_feature_class.id, limitby=(0, 1), cache=cache).first()
                if marker:
                    marker_id = marker.id

            try:
                marker = db(_markers.id == marker_id).select(_markers.image, _markers.height, _markers.width, _markers.id, limitby=(0, 1), cache=cache).first()
                layer = {"name":layername, "query":locations, "active":active, "marker":marker, "opacity": opacity, "popup_url": popup_url, "polygons": polygons}
            except:
                layer = {"name":layername, "query":locations, "active":active, "opacity": opacity, "popup_url": popup_url, "polygons": polygons}

            return layer

        except:
            # Application disabled, skip layer
            return None

    # -----------------------------------------------------------------------------
    def get_features_in_polygon(self, location_id, tablename=None, category=None):
        """
            Returns a gluon.sql.Rows of Features within a Polygonal Location
        """

        db = self.db
        session = self.session
        T = self.T
        locations = db.gis_location

        # Check that the location is a polygon
        location = db(locations.id == location_id).select(locations.wkt, locations.lon_min, locations.lon_max, locations.lat_min, locations.lat_max, limitby=(0, 1)).first()
        if location and location.wkt and (location.wkt.startswith("POLYGON") or location.wkt.startswith("MULTIPOLYGON")):
            # ok
            pass
        else:
            s3_debug("Location searched within isn't a Polygon!")
            session.error = T("Location searched within isn't a Polygon!")
            return None

        try:
            polygon = wkt_loads(location.wkt)
        except:
            s3_debug("Invalid Polygon!")
            session.error = T("Invalid Polygon!")
            return None

        lon_min = locations.lon_min
        lon_max = locations.lon_max
        lat_min = locations.lat_min
        lat_max = locations.lat_max

        table = db[tablename]
        deployment_settings = self.deployment_settings

        query = (table.location_id == locations.id)
        if "deleted" in table.fields:
            query = query & (table.deleted == False)
        # @ToDo: Check AAA

        features = db(query).select(locations.wkt, locations.lat, locations.lon, table.ALL)
        output = Rows()
        # @ToDo: provide option to use PostGIS/Spatialite
        # if deployment_settings.gis.spatialdb and deployment_settings.database.db_type == "postgres":
        # 1st check for Features included within the bbox (faster)
        def in_bbox(row):
            _location = row.gis_location
            return (_location.lon > lon_min) & (_location.lon < lon_max) & (_location.lat > lat_min) & (_location.lat < lat_max)
        for row in features.find(lambda row: in_bbox(row)):
            # Search within this subset with a full geometry check
            # Uses Shapely.
            try:
                shape = wkt_loads(row.gis_location.wkt)
                if shape.intersects(polygon):
                    # Save Record
                    output.records.append(row)
            except shapely.geos.ReadingError:
                s3_debug("Error reading wkt of location with id", row.id)

        return output

    # -----------------------------------------------------------------------------
    def get_features_in_radius(self, lat, lon, radius, tablename=None, category=None):
        """
            Returns Features within a Radius (in km) of a LatLon Location
        """

        db = self.db
        deployment_settings = self.deployment_settings

        if deployment_settings.gis.spatialdb and deployment_settings.database.db_type == "postgres":
            # Use PostGIS routine
            # The ST_DWithin function call will automatically include a bounding box comparison that will make use of any indexes that are available on the geometries.
            # @ToDo: Support optional Category (make this a generic filter?)

            import psycopg2
            import psycopg2.extras

            dbname = deployment_settings.database.database
            username = deployment_settings.database.username
            password = deployment_settings.database.password
            host = deployment_settings.database.host
            port = deployment_settings.database.port or "5432"

            # Convert km to degrees (since we're using the_geom not the_geog)
            radius = math.degrees(float(radius) / RADIUS_EARTH)

            connection = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s" % (dbname, username, password, host, port))
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            info_string = "SELECT column_name, udt_name FROM information_schema.columns WHERE table_name = 'gis_location' or table_name = '%s';" % tablename
            cursor.execute(info_string)
            # @ToDo: Look at more optimal queries for just those fields we need
            if tablename:
                # Lookup the resource
                query_string = cursor.mogrify("SELECT * FROM gis_location, %s WHERE %s.location_id = gis_location.id and ST_DWithin (ST_GeomFromText ('POINT (%s %s)', 4326), the_geom, %s);" % (tablename, tablename, lat, lon, radius))
            else:
                # Lookup the raw Locations
                query_string = cursor.mogrify("SELECT * FROM gis_location WHERE ST_DWithin (ST_GeomFromText ('POINT (%s %s)', 4326), the_geom, %s);" % (lat, lon, radius))

            cursor.execute(query_string)
            # @ToDo: Export Rows?
            features = []
            for record in cursor:
                d = dict(record.items())
                row = Storage()
                # @ToDo: Optional support for Polygons
                if tablename:
                    row.gis_location = Storage()
                    row.gis_location.id = d["id"]
                    row.gis_location.lat = d["lat"]
                    row.gis_location.lon = d["lon"]
                    row.gis_location.lat_min = d["lat_min"]
                    row.gis_location.lon_min = d["lon_min"]
                    row.gis_location.lat_max = d["lat_max"]
                    row.gis_location.lon_max = d["lon_max"]
                    row[tablename] = Storage()
                    row[tablename].id = d["id"]
                    row[tablename].name = d["name"]
                else:
                    row.name = d["name"]
                    row.id = d["id"]
                    row.lat = d["lat"]
                    row.lon = d["lon"]
                    row.lat_min = d["lat_min"]
                    row.lon_min = d["lon_min"]
                    row.lat_max = d["lat_max"]
                    row.lon_max = d["lon_max"]
                features.append(row)

            return features

        #elif deployment_settings.database.db_type == "mysql":
            # Do the calculation in MySQL to pull back only the relevant rows
            # Raw MySQL Formula from: http://blog.peoplesdns.com/archives/24
            # PI = 3.141592653589793, mysqls pi() function returns 3.141593
            #pi = math.pi
            #query = """SELECT name, lat, lon, acos(SIN( PI()* 40.7383040 /180 )*SIN( PI()*lat/180 ))+(cos(PI()* 40.7383040 /180)*COS( PI()*lat/180) *COS(PI()*lon/180-PI()* -73.99319 /180))* 3963.191
            #AS distance
            #FROM gis_location
            #WHERE 1=1
            #AND 3963.191 * ACOS( (SIN(PI()* 40.7383040 /180)*SIN(PI() * lat/180)) + (COS(PI()* 40.7383040 /180)*cos(PI()*lat/180)*COS(PI() * lon/180-PI()* -73.99319 /180))) < = 1.5
            #ORDER BY 3963.191 * ACOS((SIN(PI()* 40.7383040 /180)*SIN(PI()*lat/180)) + (COS(PI()* 40.7383040 /180)*cos(PI()*lat/180)*COS(PI() * lon/180-PI()* -73.99319 /180)))"""
            # db.executesql(query)

        else:
            # Calculate in Python
            # Pull back all the rows within a square bounding box (faster than checking all features manually)
            # Then check each feature within this subset
            # http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates

            # @ToDo: Support optional Category (make this a generic filter?)

            # shortcuts
            radians = math.radians
            degrees = math.degrees

            MIN_LAT = radians(-90)     # -PI/2
            MAX_LAT = radians(90)      # PI/2
            MIN_LON = radians(-180)    # -PI
            MAX_LON = radians(180)     #  PI

            # Convert to radians for the calculation
            r = float(radius) / RADIUS_EARTH
            radLat = radians(lat)
            radLon = radians(lon)

            # Calculate the bounding box
            minLat = radLat - r
            maxLat = radLat + r

            if (minLat > MIN_LAT) and (maxLat < MAX_LAT):
                deltaLon = math.asin(math.sin(r) / math.cos(radLat))
                minLon = radLon - deltaLon
                if (minLon < MIN_LON):
                    minLon += 2 * math.pi
                maxLon = radLon + deltaLon
                if (maxLon > MAX_LON):
                    maxLon -= 2 * math.pi
            else:
                # Special care for Poles & 180 Meridian:
                # http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates#PolesAnd180thMeridian
                minLat = max(minLat, MIN_LAT)
                maxLat = min(maxLat, MAX_LAT)
                minLon = MIN_LON
                maxLon = MAX_LON

            # Convert back to degrees
            minLat = degrees(minLat)
            minLon = degrees(minLon)
            maxLat = degrees(maxLat)
            maxLon = degrees(maxLon)

            # shortcut
            locations = db.gis_location

            query = (locations.lat > minLat) & (locations.lat < maxLat) & (locations.lon > minLon) & (locations.lon < maxLon)
            deleted = (locations.deleted == False)
            empty = (locations.lat != None) & (locations.lon != None)
            query = deleted & empty & query

            if tablename:
                # Lookup the resource
                table = db[tablename]
                query = query & (table.location_id == locations.id)
                records = db(query).select(table.ALL,
                                           locations.id,
                                           locations.name,
                                           locations.level,
                                           locations.lat,
                                           locations.lon,
                                           locations.lat_min,
                                           locations.lon_min,
                                           locations.lat_max,
                                           locations.lon_max)
            else:
                # Lookup the raw Locations
                records = db(query).select(locations.id,
                                           locations.name,
                                           locations.level,
                                           locations.lat,
                                           locations.lon,
                                           locations.lat_min,
                                           locations.lon_min,
                                           locations.lat_max,
                                           locations.lon_max)
            features = Rows()
            for record in records:
                # Calculate the Great Circle distance
                if tablename:
                    distance = self.greatCircleDistance(lat,
                                                        lon,
                                                        record.gis_location.lat,
                                                        record.gis_location.lon)
                else:
                    distance = self.greatCircleDistance(lat,
                                                        lon,
                                                        record.lat,
                                                        record.lon)
                if distance < radius:
                    features.records.append(record)
                else:
                    # skip
                    continue

            return features

    # -----------------------------------------------------------------------------
    def get_latlon(self, feature_id, filter=False):

        """ Returns the Lat/Lon for a Feature

            @param feature_id: the feature ID (int) or UUID (str)
            @param filter: Filter out results based on deployment_settings
        """

        db = self.db
        deployment_settings = self.deployment_settings
        _locations = db.gis_location

        if isinstance(feature_id, int):
            query = (_locations.id == feature_id)
        elif isinstance(feature_id, str):
            query = (_locations.uuid == feature_id)
        else:
            # Bail out
            return None

        feature = db(query).select(
                      _locations.id, _locations.lat, _locations.lon,
                      limitby=(0, 1)).first()

        #query = (_locations.deleted == False)
        #if filter and not deployment_settings.get_gis_display_l0():
            # @ToDo: This query looks wrong. Does it intend to exclude both
            # L0 and no level? Because it's actually a no-op. If location is
            # L0 then first term is false, but there is a level so the 2nd
            # term is also false, so the combination is false, same as the
            # 1st term alone. If the level isn't L0, the first term is true,
            # so the 2nd is irrelevant and probably isn't even evaluated, so
            # the combination is same as the 1st term alone.
            # @ToDo And besides, it the L0 lon, lat is all we have, isn't it
            # better to use that than nothing?
            #query = query & ((_locations.level != "L0") | (_locations.level == None))

        # Zero is an allowed value, hence explicit test for None.
        if "lon" in feature and "lat" in feature and \
           (feature.lat is not None) and (feature.lon is not None):
            return dict(lon=feature.lon, lat=feature.lat)

        else:
            # Step through ancestors to first with lon, lat.
            parents = self.get_parents(feature.id)
            if parents:
                lon = lat = None
                for row in parents:
                    if "lon" in row and "lat" in row and \
                       (row.lon is not None) and (row.lat is not None):
                        return dict(lon=row.lon, lat=row.lat)

        # Invalid feature_id
        return None

    # -----------------------------------------------------------------------------
    def get_marker(self, tablename, category=None):

        """
            Returns the Marker for a Feature
                marker.image = filename
                marker.height
                marker.width

            Used by s3xrc for Feeds export and by get_feature_layer for Categorised Resources

            @param tablename
            @param category
        """

        cache = self.cache
        db = self.db
        table_marker = db.gis_marker
        table_fclass = db.gis_feature_class

        config = self.get_config()
        symbology = config.symbology_id

        query = None

        # 1st choice for a Marker is the Feature Class's
        query = (table_fclass.resource == tablename) & (table_fclass.symbology_id == symbology)
        if category:
            query = query & (table_fclass.category == category)
        marker_id = db(query).select(table_fclass.marker_id, limitby=(0, 1), cache=cache).first()
        if marker_id:
            marker = db(table_marker.id == marker_id.marker_id).select(table_marker.image,
                                                                       table_marker.height,
                                                                       table_marker.width,
                                                                       limitby=(0, 1),
                                                                       cache=cache).first()
            return marker

        # 2nd choice for a Marker is the default
        query = (table_marker.id == config.marker_id)
        marker = db(query).select(table_marker.image,
                                  table_marker.height,
                                  table_marker.width,
                                  limitby=(0, 1),
                                  cache=cache).first()
        if marker:
            return marker
        else:
            return ""

    # -----------------------------------------------------------------------------
    def get_gps_marker(self, tablename, category=None):

        """
            Returns the GPS Marker (Symbol) for a Feature

            Used by s3xrc for Feeds export

            @param tablename
            @param category
        """

        cache = self.cache
        db = self.db
        table_fclass = db.gis_feature_class

        config = self.get_config()

        query = None

        # 1st choice for a Marker is the Feature Class's
        query = (table_fclass.resource == tablename)
        if category:
            query = query & (table_fclass.category == category)
        marker = db(query).select(table_fclass.gps_marker, limitby=(0, 1), cache=cache).first()
        if marker and marker.gps_marker:
            return marker.gps_marker

        # 2nd choice for a Marker is the default
        marker = "White Dot"
        return marker

    # -----------------------------------------------------------------------------
    def greatCircleDistance(self, lat1, lon1, lat2, lon2, quick=True):

        """
            Calculate the shortest distance (in km) over the earth's sphere between 2 points
            Formulae from: http://www.movable-type.co.uk/scripts/latlong.html
            (NB We should normally use PostGIS functions, where possible, instead of this query)
        """

        # shortcuts
        cos = math.cos
        sin = math.sin
        radians = math.radians

        if quick:
            # Spherical Law of Cosines (accurate down to around 1m & computationally quick)
            acos = math.acos
            lat1 = radians(lat1)
            lat2 = radians(lat2)
            lon1 = radians(lon1)
            lon2 = radians(lon2)
            distance = acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon2-lon1)) * RADIUS_EARTH
            return distance

        else:
            # Haversine
            #asin = math.asin
            atan2 = math.atan2
            sqrt = math.sqrt
            pow = math.pow
            dLat = radians(lat2-lat1)
            dLon = radians(lon2-lon1)
            a = pow(sin(dLat / 2), 2) + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(dLon / 2), 2)
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            #c = 2 * asin(sqrt(a))              # Alternate version
            # Convert radians to kilometers
            distance = RADIUS_EARTH * c
            return distance

    # -----------------------------------------------------------------------------
    def import_csv(self, filename, domain=None, check_duplicates=True):
        """
            Import a CSV file of Admin Boundaries into the Locations table

            The Location names should be ADM0_NAME to ADM5_NAME
            - the highest-numbered name will be taken as the name of the current location
            - the previous will be taken as the parent(s)
            - any other name is ignored

            It is possible to use the tool purely for Hierarchy, however:
            If there is a column named 'WKT' then it will be used to provide polygon &/or centroid information.
            If there is no column named 'WKT' but there are columns named 'Lat' & Lon' then these will be used for Point information.

            WKT columns can be generated from a Shapefile using:
            ogr2ogr -f CSV CSV myshapefile.shp -lco GEOMETRY=AS_WKT

            Currently this function expects to be run from the CLI, with the CSV file in the web2py folder
            Currently it expects L0 data to be pre-imported into the database.
            - L1 should be imported 1st, then L2, then L3
            - parents are found though the use of the name columns, so the previous level of hierarchy shouldn't have duplicate names in

            @ToDo: Extend to support being run from the webpage
            @ToDo: Write additional function(s) to do the OGR2OGR transformation from an uploaded Shapefile
        """

        import csv

        cache = self.cache
        db = self.db
        _locations = db.gis_location

        csv.field_size_limit(2**20 * 10)  # 10 megs

        def utf8_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
            for row in csv.reader(unicode_csv_data):
                yield [unicode(cell, "utf-8") for cell in row]

        def utf8_dict_reader(data, dialect=csv.excel, **kwargs):
            reader = utf8_csv_reader(data, dialect=dialect, **kwargs)
            headers = reader.next()
            for r in reader:
                yield dict(zip(headers, r))

        # For each row
        current_row = 0
        for row in utf8_dict_reader(open(filename)):
            current_row += 1
            try:
                name0 = row.pop("ADM0_NAME")
            except:
                name0 = ""
            try:
                name1 = row.pop("ADM1_NAME")
            except:
                name1 = ""
            try:
                name2 = row.pop("ADM2_NAME")
            except:
                name2 = ""
            try:
                name3 = row.pop("ADM3_NAME")
            except:
                name3 = ""
            try:
                name4 = row.pop("ADM4_NAME")
            except:
                name4 = ""
            try:
                name5 = row.pop("ADM5_NAME")
            except:
                name5 = ""

            if not name5 and not name4 and not name3 and not name2 and not name1:
                # We need a name! (L0's are already in DB)
                s3_debug("No name provided", current_row)
                continue

            try:
                wkt = row.pop("WKT")
            except:
                wkt = None
                try:
                    lat = row.pop("LAT")
                    lon = row.pop("LON")
                except:
                    lat = None
                    lon = None

            if domain:
                try:
                    uuid = domain + "/" + row.pop("UUID")
                except:
                    uuid = ""
            else:
                uuid = ""

            # What level are we?
            if name5:
                level = "L5"
                name = name5
                parent = name4
                grandparent = name3
            elif name4:
                level = "L4"
                name = name4
                parent = name3
                grandparent = name2
            elif name3:
                level = "L3"
                name = name3
                parent = name2
                grandparent = name1
            elif name2:
                level = "L2"
                name = name2
                parent = name1
                grandparent = name0
            else:
                level = "L1"
                name = name1
                parent = name0
                grandparent = ""

            if name == "Name Unknown" or parent == "Name Unknown":
                # Skip these locations
                continue

            # Calculate Centroid & Bounds
            if wkt:
                try:
                    # Valid WKT
                    shape = wkt_loads(wkt)
                    centroid_point = shape.centroid
                    lon = centroid_point.x
                    lat = centroid_point.y
                    bounds = shape.bounds
                    lon_min = bounds[0]
                    lat_min = bounds[1]
                    lon_max = bounds[2]
                    lat_max = bounds[3]
                    if lon_min == lon:
                        feature_type = 1 # Point
                    else:
                        feature_type = 3 # Polygon
                except:
                    s3_debug("Invalid WKT", name)
                    continue
            else:
                lon_min = lon_max = lon
                lat_min = lat_max = lat
                feature_type = 1 # Point

            # Locate Parent
            # @ToDo: Extend to search alternate names
            if parent:
                # Hack for Pakistan
                if parent == "Jammu Kashmir":
                    parent = "Pakistan"

                if grandparent:
                    _grandparent = db(_locations.name == grandparent).select(_locations.id, limitby=(0, 1), cache=cache).first()
                    if _grandparent:
                        _parent = db((_locations.name == parent) & (_locations.parent == _grandparent.id)).select(_locations.id, limitby=(0, 1), cache=cache).first()
                    else:
                        _parent = db(_locations.name == parent).select(_locations.id, limitby=(0, 1), cache=cache).first()
                else:
                    _parent = db(_locations.name == parent).select(_locations.id, limitby=(0, 1), cache=cache).first()
                if _parent:
                    parent_id = _parent.id
                else:
                    s3_debug("Location", name)
                    s3_debug("Parent cannot be found", parent)
                    parent = ""

            # Check for duplicates
            query = (_locations.name == name) & (_locations.level == level) & (_locations.parent == parent_id)
            duplicate = db(query).select()

            if duplicate:
                s3_debug("Location", name)
                s3_debug("Duplicate - updating...")
                # Update with any new information
                if uuid:
                    db(query).update(lat=lat, lon=lon, wkt=wkt, lon_min=lon_min, lon_max=lon_max, lat_min=lat_min, lat_max=lat_max, gis_feature_type=feature_type, uuid=uuid)
                else:
                    db(query).update(lat=lat, lon=lon, wkt=wkt, lon_min=lon_min, lon_max=lon_max, lat_min=lat_min, lat_max=lat_max, gis_feature_type=feature_type)
            else:
                # Create new entry in database
                if uuid:
                    _locations.insert(name=name, level=level, parent=parent_id, lat=lat, lon=lon, wkt=wkt, lon_min=lon_min, lon_max=lon_max, lat_min=lat_min, lat_max=lat_max, gis_feature_type=feature_type, uuid=uuid)
                else:
                    _locations.insert(name=name, level=level, parent=parent_id, lat=lat, lon=lon, wkt=wkt, lon_min=lon_min, lon_max=lon_max, lat_min=lat_min, lat_max=lat_max, gis_feature_type=feature_type)

        # Better to give user control, can then dry-run
        #db.commit()
        return

    # -----------------------------------------------------------------------------
    def import_geonames(self, country, level=None):
        """
            Import Locations from the Geonames database

            @param country: the 2-letter country code
            @param level: the ADM level to import

            Designed to be run from the CLI
            Levels should be imported sequentially.
            It is assumed that L0 exists in the DB already
            L1-L3 may have been imported from Shapefiles with Polygon info
            Geonames can then be used to populate the lower levels of hierarchy
        """

        import codecs

        cache = self.cache
        db = self.db
        request = self.request
        deployment_settings = self.deployment_settings
        _locations = db.gis_location

        url = "http://download.geonames.org/export/dump/" + country + ".zip"

        cachepath = os.path.join(request.folder, "cache")
        filename = country + ".txt"
        filepath = os.path.join(cachepath, filename)
        if os.access(filepath, os.R_OK):
            cached = True
        else:
            cached = False
            if not os.access(cachepath, os.W_OK):
                s3_debug("Folder not writable", cachepath)
                return

        if not cached:
            # Download File
            try:
                f = fetch(url)
            except (urllib2.URLError,):
                e = sys.exc_info()[1]
                s3_debug("URL Error", e)
                return
            except (urllib2.HTTPError,):
                e = sys.exc_info()[1]
                s3_debug("HTTP Error", e)
                return

            # Unzip File
            if f[:2] == "PK":
                # Unzip
                fp = StringIO(f)
                myfile = zipfile.ZipFile(fp)
                try:
                    # Python 2.6+ only :/
                    # For now, 2.5 users need to download/unzip manually to cache folder
                    myfile.extract(filename, cachepath)
                    myfile.close()
                except:
                    s3_debug("Zipfile contents don't seem correct!")
                    myfile.close()
                    return

        f = codecs.open(filepath, encoding="utf-8")
        # Downloaded file is worth keeping
        #os.remove(filepath)

        if level == "L1":
            fc = "ADM1"
            parent_level = "L0"
        elif level == "L2":
            fc = "ADM2"
            parent_level = "L1"
        elif level == "L3":
            fc = "ADM3"
            parent_level = "L2"
        elif level == "L4":
            fc = "ADM4"
            parent_level = "L3"
        else:
            # 5 levels of hierarchy or 4?
            # @ToDo make more extensible still
            gis_location_hierarchy = deployment_settings.get_gis_locations_hierarchy()
            try:
                label = gis_location_hierarchy["L5"]
                level = "L5"
                parent_level = "L4"
            except:
                # ADM4 data in Geonames isn't always good (e.g. PK bad)
                level = "L4"
                parent_level = "L3"
            finally:
                fc = "PPL"

        deleted = (_locations.deleted == False)
        query = deleted & (_locations.level == parent_level)
        # Do the DB query once (outside loop)
        all_parents = db(query).select(_locations.wkt, _locations.lon_min, _locations.lon_max, _locations.lat_min, _locations.lat_max, _locations.id)
        if not all_parents:
            # No locations in the parent level found
            # - use the one higher instead
            parent_level = "L" + str(int(parent_level[1:]) + 1)
            query = deleted & (_locations.level == parent_level)
            all_parents = db(query).select(_locations.wkt, _locations.lon_min, _locations.lon_max, _locations.lat_min, _locations.lat_max, _locations.id)

        # Parse File
        current_row = 0
        for line in f:
            current_row += 1
            # Format of file: http://download.geonames.org/export/dump/readme.txt
            geonameid, name, asciiname, alternatenames, lat, lon, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, gtopo30, timezone, modification_date = line.split("\t")

            if feature_code == fc:
                # @ToDo: Agree on a global repository for UUIDs:
                # http://eden.sahanafoundation.org/wiki/UserGuidelinesGISData#UUIDs
                uuid = "geo.sahanafoundation.org/" + uuid.uuid4()

                # Add WKT
                lat = float(lat)
                lon = float(lon)
                wkt = self.latlon_to_wkt(lat, lon)

                shape = shapely.geometry.point.Point(lon, lat)

                # Add Bounds
                lon_min = lon_max = lon
                lat_min = lat_max = lat

                # Locate Parent
                parent = ""
                # 1st check for Parents whose bounds include this location (faster)
                def in_bbox(row):
                    return (row.lon_min < lon_min) & (row.lon_max > lon_max) & (row.lat_min < lat_min) & (row.lat_max > lat_max)
                for row in all_parents.find(lambda row: in_bbox(row)):
                    # Search within this subset with a full geometry check
                    # Uses Shapely.
                    # @ToDo provide option to use PostGIS/Spatialite
                    try:
                        parent_shape = wkt_loads(row.wkt)
                        if parent_shape.intersects(shape):
                            parent = row.id
                            # Should be just a single parent
                            break
                    except shapely.geos.ReadingError:
                        s3_debug("Error reading wkt of location with id", row.id)

                # Add entry to database
                _locations.insert(uuid=uuid, geonames_id=geonames_id, source="geonames",
                                  name=name, level=level, parent=parent,
                                  lat=lat, lon=lon, wkt=wkt,
                                  lon_min=lon_min, lon_max=lon_max, lat_min=lat_min, lat_max=lat_max)

            else:
                continue

        s3_debug("All done!")
        return

    # -----------------------------------------------------------------------------
    def latlon_to_wkt(self, lat, lon):
        """
            Convert a LatLon to a WKT string

            >>> s3gis.latlon_to_wkt(6, 80)
            'POINT(80 6)'
        """
        WKT = "POINT(%f %f)" % (lon, lat)
        return WKT

    # -----------------------------------------------------------------------------
    def layer_subtypes(self, layer="google"):
        """ Return a lit of the subtypes available for a Layer """

        if layer == "google":
            return ["Satellite", "Maps", "Hybrid", "Terrain", "MapMaker", "MapMakerHybrid"]
        elif layer == "yahoo":
            return ["Satellite", "Maps", "Hybrid"]
        elif layer == "bing":
            return ["Satellite", "Maps", "Hybrid"]
        else:
            return None


    # -----------------------------------------------------------------------------
    def parse_location(self, wkt, lon=None, lat=None):
        """
            Parses a location from wkt, returning wkt, lat, lon, bounding box and type.
            For points, wkt may be None if lat and lon are provided; wkt will be generated.
            For lines and polygons, the lat, lon returned represent the shape's centroid.
            Centroid and bounding box will be None if Shapely is not available.
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

    # -----------------------------------------------------------------------------
    def update_location_tree(self, location_id, parent_id=None):
        """
            Update the Tree for GIS Locations:
            @author: Aravind Venkatesan and Ajay Kumar Sreenivasan from NCSU
            @summary: Using Materialized path for each node in the tree
            http://eden.sahanafoundation.org/wiki/HaitiGISToDo#HierarchicalTrees
            Do a lazy update of a database that does not have location paths.
            For convenience of get_parents, return the path.
        """

        db = self.db
        table = db.gis_location

        if parent_id:
            parent = db(table.id == parent_id).select(table.parent, table.path).first()
        # It is Somebody Else's Problem (see Douglas Adams) to assure that
        # parent_id points to an actual location.  We just protect ourselves
        # in case they didn't.
        if parent_id and parent:
            if parent.path:
                # Parent has a path.
                path = "%s/%s" % (str(parent.path), str(location_id))
            elif parent.parent:
                parent_path = self.update_location_tree(parent_id, parent.parent)
                # Ok, *now* the parent has a path.
                path = "%s/%s" % (str(parent_path), str(location_id))
            else:
                # Parent has no parent.
                path = "%s/%s" % (str(parent_id), str(location_id))
        else:
            path = str(location_id)

        db(table.id == location_id).update(path=path)

        return path

    # -----------------------------------------------------------------------------
    def wkt_centroid(self, form):
        """
            OnValidation callback:
            If a Point has LonLat defined: calculate the WKT.
            If a Line/Polygon has WKT defined: validate the format,
                calculate the LonLat of the Centroid, and set bounds
            Centroid and bounds calculation is done using Shapely, which wraps Geos.
            A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm

            Relies on Shapely.
            @ToDo: provide an option to use PostGIS/Spatialite
        """

        if not "gis_feature_type" in form.vars:
            # Default to point
            form.vars.gis_feature_type = "1"

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
                form.vars.lon_min = form.vars.lon_max = form.vars.lon
                form.vars.lat_min = form.vars.lat_max = form.vars.lat
                return

        elif form.vars.gis_feature_type in ("2", "3"):
            # Parse WKT for LineString, Polygon
            try:
                try:
                    shape = wkt_loads(form.vars.wkt)
                except:
                    if form.vars.gis_feature_type  == "3":
                        # POLYGON
                        try:
                            # Perhaps this is really a LINESTRING (e.g. OSM import of an unclosed Way)
                            linestring = "LINESTRING%s" % form.vars.wkt[8:-1]
                            shape = wkt_loads(linestring)
                            form.vars.gis_feature_type = 2
                            form.vars.wkt = linestring
                        except:
                            form.errors["wkt"] = self.messages.invalid_wkt_polygon
                    else:
                        # "2"
                        form.errors["wkt"] = self.messages.invalid_wkt_linestring
                    return
                centroid_point = shape.centroid
                form.vars.lon = centroid_point.x
                form.vars.lat = centroid_point.y
                bounds = shape.bounds
                form.vars.lon_min = bounds[0]
                form.vars.lat_min = bounds[1]
                form.vars.lon_max = bounds[2]
                form.vars.lat_max = bounds[3]
            except:
                form.errors.gis_feature_type = self.messages.centroid_error
        else:
            form.errors.gis_feature_type = self.messages.unknown_type

        return

    # -----------------------------------------------------------------------------
    def query_features_by_bbox(self, lon_min, lat_min, lon_max, lat_max):
        """
            Returns a query of all Locations inside the given bounding box
        """
        db = self.db
        _locations = db.gis_location
        query = (_locations.lat_min <= lat_max) & (_locations.lat_max >= lat_min) & (_locations.lon_min <= lon_max) & (_locations.lon_max >= lon_min)
        return query

    # -----------------------------------------------------------------------------
    def get_features_by_bbox(self, lon_min, lat_min, lon_max, lat_max):
        """
            Returns Rows of Locations whose shape intersects the given bbox.
        """
        db = self.db
        return db(self.query_features_by_bbox(lon_min, lat_min, lon_max, lat_max)).select()

    # -----------------------------------------------------------------------------
    def _get_features_by_shape(self, shape):
        """
            Returns Rows of locations which intersect the given shape.

            Relies on Shapely for wkt parsing and intersection.
            @ToDo: provide an option to use PostGIS/Spatialite
        """

        db = self.db
        in_bbox = self.query_features_by_bbox(*shape.bounds)
        has_wkt = (db.gis_location.wkt != None) & (db.gis_location.wkt != '')

        for loc in db(in_bbox & has_wkt).select():
            try:
                location_shape = wkt_loads(loc.wkt)
                if location_shape.intersects(shape):
                    yield loc
            except shapely.geos.ReadingError:
                s3_debug("Error reading wkt of location with id", loc.id)

    # -----------------------------------------------------------------------------
    def _get_features_by_latlon(self, lat, lon):
        """
        Returns a generator of locations whose shape intersects the given LatLon.

        Relies on Shapely.
        @todo: provide an option to use PostGIS/Spatialite
        """

        point = shapely.geometry.point.Point(lon, lat)
        return self._get_features_by_shape(point)

    # -----------------------------------------------------------------------------
    def _get_features_by_feature(self, feature):
        """
        Returns all Locations whose geometry intersects the given feature.

        Relies on Shapely.
        @ToDo: provide an option to use PostGIS/Spatialite
        """
        shape = wkt_loads(feature.wkt)
        return self.get_features_by_shape(shape)

    # -----------------------------------------------------------------------------
    if SHAPELY:
        get_features_by_shape = _get_features_by_shape
        get_features_by_latlon = _get_features_by_latlon
        get_features_by_feature = _get_features_by_feature

    # -----------------------------------------------------------------------------
    def set_all_bounds(self):
        """
        Sets bounds for all locations without them.

        If shapely is present, and a location has wkt, bounds of the geometry
        are used.  Otherwise, the (lat, lon) are used as bounds.
        """
        db = self.db
        _location = db.gis_location
        no_bounds = (_location.lon_min == None) & (_location.lat_min == None) & (_location.lon_max == None) & (_location.lat_max == None) & (_location.lat != None) & (_location.lon != None)
        if SHAPELY:
            wkt_no_bounds = no_bounds & (_location.wkt != None) & (_location.wkt != '')
            for loc in db(wkt_no_bounds).select():
                try :
                    shape = wkt_loads(loc.wkt)
                except:
                    s3_debug("Error reading wkt", loc.wkt)
                    continue
                bounds = shape.bounds
                _location[loc.id] = dict(
                    lon_min = bounds[0],
                    lat_min = bounds[1],
                    lon_max = bounds[2],
                    lat_max = bounds[3],
                )

        db(no_bounds).update(lon_min=_location.lon, lat_min=_location.lat, lon_max=_location.lon, lat_max=_location.lat)

    # -----------------------------------------------------------------------------
    def show_map( self,
                  height = None,
                  width = None,
                  bbox = {},
                  lat = None,
                  lon = None,
                  zoom = None,
                  projection = None,
                  add_feature = False,
                  add_feature_active = False,
                  feature_queries = [],
                  wms_browser = {},
                  catalogue_overlays = False,
                  catalogue_toolbar = False,
                  legend = False,
                  toolbar = False,
                  search = False,
                  mouse_position = "normal",
                  print_tool = {},
                  mgrs = {},
                  window = False,
                  window_hide = False,
                  closable = True,
                  collapsed = False,
                  public_url = "http://127.0.0.1:8000"
                ):
        """
            Returns the HTML to display a map

            Normally called in the controller as: map = gis.show_map()
            In the view, put: {{=XML(map)}}

            @param height: Height of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param width: Width of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param bbox: default Bounding Box of viewport (if not provided then the Lat/Lon/Zoom are used) (Dict):
                {
                "max_lat" : float,
                "max_lon" : float,
                "min_lat" : float,
                "min_lon" : float
                }
            @param lat: default Latitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param lon: default Longitude of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param zoom: default Zoom level of viewport (if not provided then the default setting from the Map Service Catalogue is used)
            @param projection: EPSG code for the Projection to use (if not provided then the default setting from the Map Service Catalogue is used)
            @param add_feature: Whether to include a DrawFeature control to allow adding a marker to the map
            @param add_feature_active: Whether the DrawFeature control should be active by default
            @param feature_queries: Feature Queries to overlay onto the map & their options (List of Dicts):
                [{
                 name   : "MyLabel",    # A string: the label for the layer
                 query  : query,        # A gluon.sql.Rows of gis_locations, which can be from a simple query or a Join. Extra fields can be added for 'marker' or 'shape' (with optional 'color' & 'size') & 'popup_label'
                 active : False,        # Is the feed displayed upon load or needs ticking to load afterwards?
                 popup_url : None,      # The URL which will be used to fill the pop-up. If the string contains <id> then the Location ID will be replaced here, otherwise it will be appended by the Location ID.
                 marker : None,         # The marker query or marker_id for the icon used to display the feature (over-riding the normal process).
                 polygons : False       # Use Polygon data, if-available (defaults to just using Point)
                }]
            @param wms_browser: WMS Server's GetCapabilities & options (dict)
                {
                name: string,           # Name for the Folder in LayerTree
                url: string             # URL of GetCapabilities
                }
            @param catalogue_overlays: Show the Overlays from the GIS Catalogue (@ToDo: make this a dict of which external overlays to allow)
            @param catalogue_toolbar: Show the Catalogue Toolbar
            @param legend: Show the Legend panel
            @param toolbar: Show the Icon Toolbar of Controls
            @param search: Show the Geonames search box
            @param mouse_position: Show the current coordinates in the bottom-right of the map. 3 Options: 'normal' (default), 'mgrs' (MGRS), False (off)
            @param print_tool: Show a print utility (NB This requires server-side support: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting)
                {
                url: string,            # URL of print service (e.g. http://localhost:8080/geoserver/pdf/)
                mapTitle: string        # Title for the Printed Map (optional)
                subTitle: string        # subTitle for the Printed Map (optional)
                }
            @param mgrs: Use the MGRS Control to select PDFs
                {
                name: string,           # Name for the Control
                url: string             # URL of PDF server
                }
            @param window: Have viewport pop out of page into a resizable window
            @param window_hide: Have the window hidden by default, ready to appear (e.g. on clicking a button)
            @param closable: In Window mode, whether the window is closable or not
            @param collapsed: Start the Tools panel (West region) collapsed
            @param public_url: pass from model (not yet defined when Module instantiated
        """

        request = self.request
        response = self.response
        if not response.warning:
            response.warning = ""
        session = self.session
        T = self.T
        db = self.db
        auth = self.auth
        cache = self.cache
        deployment_settings = self.deployment_settings

        # Read configuration
        config = self.get_config()
        if height:
            map_height = height
        else:
            map_height = config.map_height
        if width:
            map_width = width
        else:
            map_width = config.map_width
        if bbox and (-90 < bbox["max_lat"] < 90) and (-90 < bbox["min_lat"] < 90) and (-180 < bbox["max_lon"] < 180) and (-180 < bbox["min_lon"] < 180):
            # We have sane Bounds provided, so we should use them
            pass
        else:
            # No bounds or we've been passed bounds which aren't sane
            bbox = None
        # Support bookmarks (such as from the control)
        # - these over-ride the arguments
        if "lat" in request.vars:
            lat = request.vars.lat
        if lat is None or lat == "":
            lat = config.lat
        if "lon" in request.vars:
            lon = request.vars.lon
        if lon is None or lon == "":
            lon = config.lon
        if "zoom" in request.vars:
            zoom = request.vars.zoom
        if not zoom:
            zoom = config.zoom
        if not projection:
            projection = config.epsg
        units = config.units
        maxResolution = config.maxResolution
        maxExtent = config.maxExtent
        numZoomLevels = config.zoom_levels
        marker_id_default = config.marker_id
        query = (db.gis_marker.id == marker_id_default)
        marker_default = db(query).select(db.gis_marker.image,
                                          db.gis_marker.height,
                                          db.gis_marker.width,
                                          limitby=(0, 1),
                                          cache=cache).first()
        symbology = config.symbology_id
        cluster_distance = config.cluster_distance
        cluster_threshold = config.cluster_threshold

        markers = {}

        html = DIV(_id="map_wrapper")

        #####
        # CSS
        #####
        # All Loaded as-standard to avoid delays in page loading

        ######
        # HTML
        ######
        # Catalogue Toolbar
        if catalogue_toolbar:
            if auth.has_membership(1):
                config_button = SPAN( A(T("Defaults"),
                                      _href=URL(r=request, c="gis", f="config",
                                                args=["1", "update"])),
                                      _class="rheader_tab_other" )
            else:
                config_button = SPAN( A(T("Defaults"),
                                      _href=URL(r=request, c="gis", f="config",
                                                args=["1", "display"])),
                                      _class="rheader_tab_other" )
            catalogue_toolbar = DIV(
                config_button,
                SPAN( A(T("Layers"),
                      _href=URL(r=request, c="gis", f="map_service_catalogue")),
                      _class="rheader_tab_other" ),
                SPAN( A(T("Markers"),
                      _href=URL(r=request, c="gis", f="marker")),
                      _class="rheader_tab_other" ),
                SPAN( A(T("Keys"),
                      _href=URL(r=request, c="gis", f="apikey")),
                      _class="rheader_tab_other" ),
                SPAN( A(T("Projections"),
                      _href=URL(r=request, c="gis", f="projection")),
                      _class="rheader_tab_other" ),
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
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/openlayers/lib/OpenLayers.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/MP.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/cdauth.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/usng2.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/osm_styles.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/GeoExt/lib/GeoExt.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/GeoExt/ux/GeoNamesSearchCombo.js")))
        else:
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/OpenLayers.js")))
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/gis/GeoExt.js")))

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
        var ur = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top)).transform(projection_current, proj4326);
        var boundsgeog = new OpenLayers.Bounds(ll.lon, ll.lat, ur.lon, ur.lat);
        bbox = boundsgeog.toBBOX();
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
        text: 'Select %s',
        control: selectPdfControl,
        map: map,
        toggleGroup: toggleGroup,
        allowDepress: false,
        tooltip: 'Select %s',
        // check item options group: 'draw'
    });
    """ % (mgrs["name"], mgrs["name"])
            mgrs3 = """
    toolbar.add(mgrsButton);
    toolbar.addSeparator();
    """
        else:
            mgrs_html = ""
            mgrs2 = ""
            mgrs3 = ""

        # Legend panel
        if legend:
            legend1= """
        legendPanel = new GeoExt.LegendPanel({
            id: 'legendpanel',
            title: '%s',
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
        """ % (T("Legend"))
            legend2 = ", legendPanel"
        else:
            legend1= ""
            legend2 = ""

        # Draw Feature Control
        crosshair_on = "$('.olMapViewport').addClass('crosshair');"
        crosshair_off = "$('.olMapViewport').removeClass('crosshair');"
        crosshair = ""
        if add_feature:
            if add_feature_active:
                draw_depress = "true"
                crosshair = crosshair_on
            else:
                draw_depress = "false"
            draw_feature = """
        pointButton = new GeoExt.Action({
            control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Point, {
                // custom Callback
                'featureAdded': function(feature){
                    // Remove previous point
                    if (lastDraftFeature){
                        lastDraftFeature.destroy();
                    }
                    // updateFormFields
                    centerPoint = feature.geometry.getBounds().getCenterLonLat();
                    centerPoint.transform(projection_current, proj4326);
                    $('#gis_location_lon').val(centerPoint.lon);
                    $('#gis_location_lat').val(centerPoint.lat);
                    // Prepare in case user selects a new point
                    lastDraftFeature = feature;
                }
            }),
            handler: function(){
                if (pointButton.items[0].pressed) {
                    """ + crosshair_on + """
                } else {
                    """ + crosshair_off + """
                }
            },
            map: map,
            iconCls: 'drawpoint-off',
            tooltip: '%s',
            toggleGroup: 'controls',
            allowDepress: true,
            enableToggle: true,
            pressed: """ + draw_depress + """
        });
        """ % T("Add Point")

        
            if None:
                draw_feature += """
        // Controls for Draft Features
        // - interferes with popupControl which is active on allLayers
        //var selectControl = new OpenLayers.Control.SelectFeature(draftLayer, {
        //    onSelect: onFeatureSelect,
        //    onUnselect: onFeatureUnselect,
        //    multiple: false,
        //    clickout: true,
        //    isDefault: true
        //});

        //var removeControl = new OpenLayers.Control.RemoveFeature(draftLayer, {
        //    onDone: function(feature) {
        //        console.log(feature)
        //    }
        //});

        //var selectButton = new GeoExt.Action({
            //control: selectControl,
        //    map: map,
        //    iconCls: 'searchclick',
            // button options
        //    tooltip: '""" + T("Query Feature") + """',
        //    toggleGroup: 'controls',
        //    enableToggle: true
        //});

        //var lineButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Path),
        //    map: map,
        //    iconCls: 'drawline-off',
        //    tooltip: '""" + T("Add Line") + """',
        //    toggleGroup: 'controls'
        //});

        //var polygonButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DrawFeature(draftLayer, OpenLayers.Handler.Polygon),
        //    map: map,
        //    iconCls: 'drawpolygon-off',
        //    tooltip: '""" + T("Add Polygon") + """',
        //    toggleGroup: 'controls'
        //});

        //var dragButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.DragFeature(draftLayer),
        //    map: map,
        //    iconCls: 'movefeature',
        //    tooltip: '""" + T("Move Feature: Drag feature to desired location") + """',
        //    toggleGroup: 'controls'
        //});

        //var resizeButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer, { mode: OpenLayers.Control.ModifyFeature.RESIZE }),
        //    map: map,
        //    iconCls: 'resizefeature',
        //    tooltip: '""" + T("Resize Feature: Select the feature you wish to resize & then Drag the associated dot to your desired size") + """',
        //    toggleGroup: 'controls'
        //});

        //var rotateButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer, { mode: OpenLayers.Control.ModifyFeature.ROTATE }),
        //    map: map,
        //    iconCls: 'rotatefeature',
        //    tooltip: '""" + T("Rotate Feature: Select the feature you wish to rotate & then Drag the associated dot to rotate to your desired location") + """',
        //    toggleGroup: 'controls'
        //});

        //var modifyButton = new GeoExt.Action({
        //    control: new OpenLayers.Control.ModifyFeature(draftLayer),
        //    map: map,
        //    iconCls: 'modifyfeature',
        //    tooltip: '""" + T("Modify Feature: Select the feature you wish to deform & then Drag one of the dots to deform the feature in your chosen manner") + """',
        //    toggleGroup: 'controls'
        //});

        //var removeButton = new GeoExt.Action({
        //    control: removeControl,
        //    map: map,
        //    iconCls: 'removefeature',
        //    tooltip: '""" + T("Remove Feature: Select the feature you wish to remove & press the delete key") + """',
        //    toggleGroup: 'controls'
        //});
        """
            
            draw_feature2 = """
        // Draw Controls
        //toolbar.add(selectButton);
        toolbar.add(pointButton);
        //toolbar.add(lineButton);
        //toolbar.add(polygonButton);
        //toolbar.add(dragButton);
        //toolbar.add(resizeButton);
        //toolbar.add(rotateButton);
        //toolbar.add(modifyButton);
        //toolbar.add(removeButton);
        toolbar.addSeparator();
        """
        else:
            draw_feature = ""
            draw_feature2 = ""

        # Toolbar
        if toolbar or add_feature:
            if 1 in session.s3.roles or auth.s3_has_role("MapAdmin"):
            #if auth.is_logged_in():
                # Provide a way to save the viewport
                # @ToDo Extend to personalised Map Views
                # @ToDo Extend to choice of Base Layer & Enabled status of Overlays
                save_button = """
        var saveButton = new Ext.Toolbar.Button({
            iconCls: 'save',
            tooltip: '%s',
            handler: function() {
                // Read current settings from map
                var lonlat = map.getCenter();
                var zoom_current = map.getZoom();
                // Convert back to LonLat for saving
                lonlat.transform(map.getProjectionObject(), proj4326);
                // Use AJAX to send back
                var url = '%s';
                Ext.Ajax.request({
                    url: url,
                    method: 'GET',
                    params: {
                        uuid: '%s',
                        lat: lonlat.lat,
                        lon: lonlat.lon,
                        zoom: zoom_current
                    }
                });
            }
        });
        """ % (T("Save: Default Lat, Lon & Zoom for the Viewport"),
               URL(r=request, c="gis", f="config", args=["1.url", "update"]),
               config.uuid)
                save_button2 = """
        toolbar.addSeparator();
        // Save Viewport
        toolbar.addButton(saveButton);
        """
            else:
                save_button = ""
                save_button2 = ""

            osm_oauth_consumer_key = deployment_settings.get_osm_oauth_consumer_key()
            osm_oauth_consumer_secret = deployment_settings.get_osm_oauth_consumer_secret()
            if osm_oauth_consumer_key and osm_oauth_consumer_secret:
                potlatch_button = """
        var potlatchButton = new Ext.Toolbar.Button({
            iconCls: 'potlatch',
            tooltip: '%s',
            handler: function() {
                // Read current settings from map
                var lonlat = map.getCenter();
                var zoom_current = map.getZoom();
                if ( zoom_current < 14 ) {
                    zoom_current = 14;
                }
                // Convert back to LonLat for saving
                lonlat.transform(map.getProjectionObject(), proj4326);
                var url = '%s?lat=' + lonlat.lat + '&lon=' + lonlat.lon + '&zoom=' + zoom_current;
                window.open(url);
            }
        });
        """ % (T("Edit the OpenStreetMap data for this area"),
               URL(r=request, f="potlatch2", args="potlatch2.html"))
                potlatch_button2 = """
        toolbar.addSeparator();
        // Edit in OpenStreetMap
        toolbar.addButton(potlatchButton);
        """
            else:
                potlatch_button = ""
                potlatch_button2 = ""

            if add_feature:
                pan_depress = "false"
            else:
                pan_depress = "true"

            toolbar = """
        toolbar = mapPanel.getTopToolbar();

        // OpenLayers controls

        // Measure Controls
        var measureSymbolizers = {
            'Point': {
                pointRadius: 5,
                graphicName: 'circle',
                fillColor: 'white',
                fillOpacity: 1,
                strokeWidth: 1,
                strokeOpacity: 1,
                strokeColor: '#f5902e'
            },
            'Line': {
                strokeWidth: 3,
                strokeOpacity: 1,
                strokeColor: '#f5902e',
                strokeDashstyle: 'dash'
            },
            'Polygon': {
                strokeWidth: 2,
                strokeOpacity: 1,
                strokeColor: '#f5902e',
                fillColor: 'white',
                fillOpacity: 0.5
            }
        };
        var styleMeasure = new OpenLayers.Style();
        styleMeasure.addRules([
            new OpenLayers.Rule({symbolizer: measureSymbolizers})
        ]);
        var styleMapMeasure = new OpenLayers.StyleMap({'default': styleMeasure});

        var length = new OpenLayers.Control.Measure(
            OpenLayers.Handler.Path, {
                geodesic: true,
                persist: true,
                handlerOptions: {
                    layerOptions: {styleMap: styleMapMeasure}
                }
            }
        );
        length.events.on({
            'measure': function(evt) {
                alert('""" + T("The length is ") + """' + evt.measure.toFixed(2) + ' ' + evt.units);
            }
        });
        var area = new OpenLayers.Control.Measure(
            OpenLayers.Handler.Polygon, {
                geodesic: true,
                persist: true,
                handlerOptions: {
                    layerOptions: {styleMap: styleMapMeasure}
                }
            }
        );
        area.events.on({
            'measure': function(evt) {
                alert('""" + T("The area is ") + """' + evt.measure.toFixed(2) + ' ' + evt.units + '2');
            }
        });

        var nav = new OpenLayers.Control.NavigationHistory();

        // GeoExt Buttons
        var zoomfull = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomToMaxExtent(),
            map: map,
            iconCls: 'zoomfull',
            // button options
            tooltip: '""" + T("Zoom to maximum map extent") + """'
        });

        var zoomout = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox({ out: true }),
            map: map,
            iconCls: 'zoomout',
            // button options
            tooltip: '""" + T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle") + """',
            toggleGroup: 'controls'
        });

        var zoomin = new GeoExt.Action({
            control: new OpenLayers.Control.ZoomBox(),
            map: map,
            iconCls: 'zoomin',
            // button options
            tooltip: '""" + T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle") + """',
            toggleGroup: 'controls'
        });

        var pan = new GeoExt.Action({
            control: new OpenLayers.Control.Navigation(),
            map: map,
            iconCls: 'pan-off',
            // button options
            tooltip: '""" + T("Pan Map: keep the left mouse button pressed and drag the map") + """',
            toggleGroup: 'controls',
            allowDepress: true,
            pressed: """ + pan_depress + """
        });

        // 1st of these 2 to get activated cannot be deselected!
        var lengthButton = new GeoExt.Action({
            control: length,
            map: map,
            iconCls: 'measure-off',
            // button options
            tooltip: '""" + T("Measure Length: Click the points along the path & end with a double-click") + """',
            toggleGroup: 'controls',
            allowDepress: true,
            enableToggle: true
        });

        var areaButton = new GeoExt.Action({
            control: area,
            map: map,
            iconCls: 'measure-area',
            // button options
            tooltip: '""" + T("Measure Area: Click the points around the polygon & end with a double-click") + """',
            toggleGroup: 'controls',
            allowDepress: true,
            enableToggle: true
        });

        var navPreviousButton = new Ext.Toolbar.Button({
            iconCls: 'back',
            tooltip: '""" + T("Previous View") + """',
            handler: nav.previous.trigger
        });

        var navNextButton = new Ext.Toolbar.Button({
            iconCls: 'next',
            tooltip: '""" + T("Next View") + """',
            handler: nav.next.trigger
        });

        var geoLocateButton = new Ext.Toolbar.Button({
            iconCls: 'geolocation',
            tooltip: '""" + T("Zoom to Current Location") + """',
            handler: function(){
                navigator.geolocation.getCurrentPosition(getCurrentPosition);
            }
        });

        """ + mgrs2 + """

        """ + draw_feature + """

        """ + save_button + """

        """ + potlatch_button + """

        // Add to Map & Toolbar
        toolbar.add(zoomfull);
        if (navigator.geolocation) {
            // HTML5 geolocation is available :)
            toolbar.addButton(geoLocateButton);
        } else {
            // geolocation is not available...IE sucks! ;)
        }
        toolbar.add(zoomout);
        toolbar.add(zoomin);
        toolbar.add(pan);
        toolbar.addSeparator();
        // Navigation
        map.addControl(nav);
        nav.activate();
        toolbar.addButton(navPreviousButton);
        toolbar.addButton(navNextButton);
        """ + save_button2 + """
        toolbar.addSeparator();
        // Measure Tools
        toolbar.add(lengthButton);
        toolbar.add(areaButton);
        """ + mgrs3 + """
        """ + draw_feature2 + """
        """ + potlatch_button2

            toolbar2 = "Ext.QuickTips.init();"
        else:
            toolbar = ""
            toolbar2 = ""

        # Search
        if search:
            search = """
        var mapSearch = new GeoExt.ux.GeoNamesSearchCombo({
            map: map,
            zoom: 12
         });

        var searchCombo = new Ext.Panel({
            id: 'searchCombo',
            title: '%s',
            layout: 'border',
            rootVisible: false,
            split: true,
            autoScroll: true,
            collapsible: true,
            collapseMode: 'mini',
            lines: false,
            html: '%s',
            items: [{
                    region: 'center',
                    items: [ mapSearch ]
                }]
        });
        """ % (T("Search Geonames"),
               T("Geonames.org search requires Internet connectivity!"))
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
                url: OpenLayers.ProxyHost + '%s',
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
            title: '%s',
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
        """ % (url, name)
            layers_wms_browser2 = """,
                            wmsBrowser"""
        else:
            layers_wms_browser = ""
            layers_wms_browser2 = ""

        # Mouse Position
        if mouse_position and mouse_position is not "mgrs":
            mouse_position = "map.addControl(new OpenLayers.Control.MousePosition());"
        elif mouse_position == "mgrs":
            mouse_position = "map.addControl(new OpenLayers.Control.MGRSMousePosition());"
        else:
            mouse_position = ""

        # Print
        # NB This isn't too-flexible a method. We're now focussing on print.css
        if print_tool:
            url = print_tool["url"]
            if "title" in print_tool:
                mapTitle = str(print_tool["mapTitle"])
            else:
                mapTitle = T("Map from Sahana Eden")
            if "subtitle" in print_tool:
                subTitle = str(print_tool["subTitle"])
            else:
                subTitle = T("Printed from Sahana Eden")
            if session.auth:
                creator = session.auth.user.email
            else:
                creator = ""
            print_tool1 = """
        if (typeof(printCapabilities) != 'undefined') {
            // info.json from script headers OK
            printProvider = new GeoExt.data.PrintProvider({
                //method: 'POST',
                //url: '""" + url + """',
                method: 'GET', // 'POST' recommended for production use
                capabilities: printCapabilities, // from the info.json returned from the script headers
                customParams: {
                    mapTitle: '""" + mapTitle + """',
                    subTitle: '""" + subTitle + """',
                    creator: '""" + creator + """'
                }
            });
            // Our print page. Stores scale, center and rotation and gives us a page
            // extent feature that we can add to a layer.
            printPage = new GeoExt.data.PrintPage({
                printProvider: printProvider
            });

            //var printExtent = new GeoExt.plugins.PrintExtent({
            //    printProvider: printProvider
            //});
            // A layer to display the print page extent
            //var pageLayer = new OpenLayers.Layer.Vector('""" + T("Print Extent") + """');
            //pageLayer.addFeatures(printPage.feature);
            //pageLayer.setVisibility(false);
            //map.addLayer(pageLayer);
            //var pageControl = new OpenLayers.Control.TransformFeature();
            //map.addControl(pageControl);
            //map.setOptions({
            //    eventListeners: {
                    // recenter/resize page extent after pan/zoom
            //        'moveend': function() {
            //            printPage.fit(mapPanel, true);
            //        }
            //    }
            //});
            // The form with fields controlling the print output
            var formPanel = new Ext.form.FormPanel({
                title: '""" + T("Print Map") + """',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%'},
                listeners: {
                    'expand': function() {
                        //if (null == mapPanel.map.getLayersByName('""" + T("Print Extent") + """')[0]) {
                        //    mapPanel.map.addLayer(pageLayer);
                        //}
                        if (null == mapPanel.plugins[0]) {
                            //map.addLayer(pageLayer);
                            //pageControl.activate();
                            //mapPanel.plugins = [ new GeoExt.plugins.PrintExtent({
                            //    printProvider: printProvider,
                            //    map: map,
                            //    layer: pageLayer,
                            //    control: pageControl
                            //}) ];
                            //mapPanel.plugins[0].addPage();
                        }
                    },
                    'collapse':  function() {
                        //mapPanel.map.removeLayer(pageLayer);
                        //if (null != mapPanel.plugins[0]) {
                        //    map.removeLayer(pageLayer);
                        //    mapPanel.plugins[0].removePage(mapPanel.plugins[0].pages[0]);
                        //    mapPanel.plugins = [];
                        //}
                    }
                },
                items: [{
                    xtype: 'textarea',
                    name: 'comment',
                    value: '',
                    fieldLabel: '""" + T("Comment") + """',
                    plugins: new GeoExt.plugins.PrintPageField({
                        printPage: printPage
                    })
                }, {
                    xtype: 'combo',
                    store: printProvider.layouts,
                    displayField: 'name',
                    fieldLabel: '""" + T("Layout") + """',
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
                    fieldLabel: '""" + T("Resolution") + """',
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
                //}, {
                //    xtype: 'combo',
                //    store: printProvider.scales,
                //    displayField: 'name',
                //    fieldLabel: '""" + T("Scale") + """',
                //    typeAhead: true,
                //    mode: 'local',
                //    triggerAction: 'all',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                //}, {
                //    xtype: 'textfield',
                //    name: 'rotation',
                //    fieldLabel: '""" + T("Rotation") + """',
                //    plugins: new GeoExt.plugins.PrintPageField({
                //        printPage: printPage
                //    })
                }],
                buttons: [{
                    text: '""" + T("Create PDF") + """',
                    handler: function() {
                        // the PrintExtent plugin is the mapPanel's 1st plugin
                        //mapPanel.plugins[0].print();
                        // convenient way to fit the print page to the visible map area
                        printPage.fit(mapPanel, true);
                        // print the page, including the legend, where available
                        if (null == legendPanel) {
                            printProvider.print(mapPanel, printPage);
                        } else {
                            printProvider.print(mapPanel, printPage, {legend: legendPanel});
                        }
                    }
                }]
            });
        } else {
            // Display error diagnostic
            var formPanel = new Ext.Panel ({
                title: '%s',
                rootVisible: false,
                split: true,
                autoScroll: true,
                collapsible: true,
                collapsed: true,
                collapseMode: 'mini',
                lines: false,
                bodyStyle: 'padding:5px',
                labelAlign: 'top',
                defaults: {anchor: '100%'},
                html: '%s: <BR />%s'
            });
        }
        """ % (T("Print Map"),
               T("Printing disabled since server not accessible"), url)
            print_tool2 = """,
                    formPanel"""
        else:
            print_tool1 = ""
            print_tool2 = ""

        ##########
        # Settings
        ##########

        # Strategy
        # Need to be uniquely instantiated
        strategy_cluster = "new OpenLayers.Strategy.Cluster({distance: %i, threshold: %i})" % (cluster_distance,
                                                                                               cluster_threshold)

        # Layout
        if window:
            if window_hide:
                layout = """
            closeAction: 'hide',
            """
                layout2 = """
            """
            else:
                if closable:
                    layout = """
                """
                else:
                    layout = """
            closable: false,
                """
                layout2 = """
        mapWin.show();
        mapWin.maximize();
            """
            layout = """
        mapWin = new Ext.Window({
            id: 'gis-map-window',
            collapsible: true,
            constrain: true,
        """ + layout
        else:
            # Embedded
            layout = """
        var panel = new Ext.Panel({
            id: 'gis-map-panel',
            renderTo: 'map_panel',
            """
            layout2 = ""

        # Collapsed
        if collapsed:
            collapsed = "true"
        else:
            collapsed = "false"

        # Bounding Box
        if bbox:
            # Calculate from Bounds
            center = """
    var bottom_left = new OpenLayers.LonLat(%f, %f);
    bottom_left.transform(proj4326, projection_current);
    var left = bottom_left.lon;
    var bottom = bottom_left.lat;
    top_right = new OpenLayers.LonLat(%f, %f);
    top_right.transform(proj4326, projection_current);
    var right = top_right.lon;
    var top = top_right.lat;
    var bounds = OpenLayers.Bounds.fromArray([left, bottom, right, top]);
    var center = bounds.getCenterLonLat();
    """ % (bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])
            zoomToExtent = """
        map.zoomToExtent(bounds);
        """
        else:
            center = """
    var lat = %s;
    var lon = %s;
    var center = new OpenLayers.LonLat(lon, lat);
    center.transform(proj4326, projection_current);
    """ % (lat, lon)
            zoomToExtent = ""

        cluster_style_options = """
        // Style Rule For Clusters
        var style_cluster_style = {
            label: '${label}',
            pointRadius: '${radius}',
            fillColor: '${fill}',
            fillOpacity: 0.5,
            strokeColor: '${stroke}',
            strokeWidth: 2,
            strokeOpacity: 1
        };
        var style_cluster_options = {
            context: {
                radius: function(feature) {
                    // Size for Unclustered Point
                    var pix = 12;
                    // Size for Clustered Point
                    if (feature.cluster) {
                        pix = Math.min(feature.attributes.count/2, 8) + 12;
                    }
                    return pix;
                },
                fill: function(feature) {
                    // fillColor for Unclustered Point
                    var color = '#f5902e';
                    // fillColor for Clustered Point
                    if (feature.cluster) {
                        color = '#8087ff';
                    }
                    return color;
                },
                stroke: function(feature) {
                    // strokeColor for Unclustered Point
                    var color = '#f5902e';
                    // strokeColor for Clustered Point
                    if (feature.cluster) {
                        color = '#2b2f76';
                    }
                    return color;
                },
                label: function(feature) {
                    // Label For Unclustered Point or Cluster of just 2
                    var label = '';
                    // Label For Clustered Point
                    if (feature.cluster && feature.attributes.count > 2) {
                        label = feature.attributes.count;
                    }
                    return label;
                }
            }
        };
        """

        cluster_style = """
        // Needs to be uniquely instantiated
        var style_cluster = new OpenLayers.Style(style_cluster_style, style_cluster_options);
        // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
        var featureClusterStyleMap = new OpenLayers.StyleMap({
                                          'default': style_cluster,
                                          'select': {
                                              fillColor: '#ffdc33',
                                              strokeColor: '#ff9933'
                                          }
        });
        """

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

        # OpenStreetMap
        query = (db.gis_layer_openstreetmap.enabled == True)
        openstreetmap_enabled = db(query).select()
        if openstreetmap_enabled:
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
                var path = z + "/" + x + "/" + y + "." + this.type;
                var url = this.url;
                if (url instanceof Array) {
                    url = this.selectUrl(path, url);
                }
                return url + path;
            }
        }
        """
            for layer in openstreetmap_enabled:
                if layer.role_required and not auth.s3_has_role(layer.role_required):
                    continue
                name = layer.name
                name_safe = re.sub("\W", "_", name)
                url1 = layer.url1
                url2 = layer.url2
                url3 = layer.url3
                if url3:
                    url = "['%s', '%s', '%s']" % (url1, url2, url3)
                elif url2:
                    url = "['%s', '%s']" % (url1, url2)
                else:
                    url = "['%s']" % url1
                if layer.base:
                    base = ""
                else:
                    base = ", isBaseLayer: false"
                if layer.visible:
                    visibility = ""
                else:
                    visibility = "osmLayer%s.setVisibility(false);" % name_safe
                if layer.attribution:
                    attribution = ",attribution: '%s'" % layer.attribution
                else:
                    attribution = ""
                if layer.base or catalogue_overlays:
                    layers_openstreetmap += """
        var osmLayer""" + name_safe + """ = new OpenLayers.Layer.TMS( '""" + name + """', """ + url + """, {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true """ + attribution + base + """ } );
        map.addLayer(osmLayer""" + name_safe + """);
        """ + visibility
        else:
            functions_openstreetmap = ""

        # Only enable commercial base layers if using a sphericalMercator projection
        if projection == 900913:

            # Google
            gis_layer_google_subtypes = self.layer_subtypes("google")
            google = Storage()
            google_enabled = db(db.gis_layer_google.enabled == True).select()
            if google_enabled:
                google.key = self.get_api_key("google")
                for layer in google_enabled:
                    if layer.role_required and not auth.s3_has_role(layer.role_required):
                        continue
                    for subtype in gis_layer_google_subtypes:
                        if layer.subtype == subtype:
                            google["%s" % subtype] = layer.name
            if google:
                if google.MapMaker or google.MapMakerHybrid:
                    # Need to use v2 API
                    # http://code.google.com/p/gmaps-api-issues/issues/detail?id=2349
                    googleMapmaker = True
                    html.append(SCRIPT(_type="text/javascript",
                                       _src="http://maps.google.com/maps?file=api&v=2&key=%s" % google.key))
                else:
                    googleMapmaker = False
                    html.append(SCRIPT(_type="text/javascript",
                                       _src="http://maps.google.com/maps/api/js?sensor=false"))
                # Google Earth (coming soon)
                #html.append(SCRIPT(_type="text/javascript",
                #                   _src="http://www.google.com/jsapi?key=%s" % google.key))
                #html.append(SCRIPT("google && google.load('earth', '1');", _type="text/javascript"))
                if google.Satellite:
                    if googleMapmaker:
                        layers_google += """
        var googlesat = new OpenLayers.Layer.Google( '%s' , {type: G_SATELLITE_MAP, 'sphericalMercator': true} );
        map.addLayer(googlesat);
                    """ % google.Satellite
                    else:
                        layers_google += """
        var googlesat = new OpenLayers.Layer.Google( '%s' , {type: google.maps.MapTypeId.SATELLITE, numZoomLevels: 22} );
        map.addLayer(googlesat);
                    """ % google.Satellite
                if google.Maps:
                    if googleMapmaker:
                        layers_google += """
        var googlemaps = new OpenLayers.Layer.Google( '%s' , {type: G_NORMAL_MAP, 'sphericalMercator': true} );
        map.addLayer(googlemaps);
                    """ % google.Maps
                    else:
                        layers_google += """
        var googlemaps = new OpenLayers.Layer.Google( '%s' , {numZoomLevels: 20} );
        map.addLayer(googlemaps);
                    """ % google.Maps
                if google.Hybrid:
                    if googleMapmaker:
                        layers_google += """
        var googlehybrid = new OpenLayers.Layer.Google( '%s' , {type: G_HYBRID_MAP, 'sphericalMercator': true} );
        map.addLayer(googlehybrid);
                    """ % google.Hybrid
                    else:
                        layers_google += """
        var googlehybrid = new OpenLayers.Layer.Google( '%s' , {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20} );
        map.addLayer(googlehybrid);
                    """ % google.Hybrid
                if google.Terrain:
                    if googleMapmaker:
                        layers_google += """
        var googleterrain = new OpenLayers.Layer.Google( '%s' , {type: G_PHYSICAL_MAP, 'sphericalMercator': true} )
        map.addLayer(googleterrain);
                    """ % google.Terrain
                    else:
                        layers_google += """
        var googleterrain = new OpenLayers.Layer.Google( '%s' , {type: google.maps.MapTypeId.TERRAIN} )
        map.addLayer(googleterrain);
                    """ % google.Terrain
                if google.MapMaker:
                    layers_google += """
        var googlemapmaker = new OpenLayers.Layer.Google( '%s' , {type: G_MAPMAKER_NORMAL_MAP, 'sphericalMercator': true } )
        map.addLayer(googlemapmaker);
                    """ % google.MapMaker
                if google.MapMakerHybrid:
                    layers_google += """
        var googlemapmakerhybrid = new OpenLayers.Layer.Google( '%s' , {type: G_MAPMAKER_HYBRID_MAP, 'sphericalMercator': true } )
        map.addLayer(googlemapmakerhybrid);
                    """ % google.MapMakerHybrid

            # Yahoo
            gis_layer_yahoo_subtypes = self.layer_subtypes("yahoo")
            yahoo = Storage()
            yahoo_enabled = db(db.gis_layer_yahoo.enabled == True).select()
            if yahoo_enabled:
                yahoo.key = self.get_api_key("yahoo")
                for layer in yahoo_enabled:
                    if layer.role_required and not auth.s3_has_role(layer.role_required):
                        continue
                    for subtype in gis_layer_yahoo_subtypes:
                        if layer.subtype == subtype:
                            yahoo["%s" % subtype] = layer.name
            if yahoo:
                html.append(SCRIPT(_type="text/javascript",
                                   _src="http://api.maps.yahoo.com/ajaxymap?v=3.8&appid=%s" % yahoo.key))
                if yahoo.Satellite:
                    layers_yahoo += """
        var yahoosat = new OpenLayers.Layer.Yahoo( '%s' , {type: YAHOO_MAP_SAT, 'sphericalMercator': true } );
        map.addLayer(yahoosat);
                    """ % yahoo.Satellite
                if yahoo.Maps:
                    layers_yahoo += """
        var yahoomaps = new OpenLayers.Layer.Yahoo( '%s' , {'sphericalMercator': true } );
        map.addLayer(yahoomaps);
                    """ % yahoo.Maps
                if yahoo.Hybrid:
                    layers_yahoo += """
        var yahoohybrid = new OpenLayers.Layer.Yahoo( '%s' , {type: YAHOO_MAP_HYB, 'sphericalMercator': true } );
        map.addLayer(yahoohybrid);
                    """ % yahoo.Hybrid

            gis_layer_bing_subtypes = self.layer_subtypes("bing")
            bing = Storage()
            bing_enabled = db(db.gis_layer_bing.enabled == True).select()
            if bing_enabled:
                bing.key = self.get_api_key("bing")
                if bing.key:
                    for layer in bing_enabled:
                        if layer.role_required and not auth.s3_has_role(layer.role_required):
                            continue
                        for subtype in gis_layer_bing_subtypes:
                            if layer.subtype == subtype:
                                bing["%s" % subtype] = layer.name
                else:
                    response.warning = T("Bing Layers Disabled as no API Key available")
                    bing = False
            if bing:
                layers_bing += """
        var bingApiKey = '%s';
                    """ % bing.key
                if bing.Satellite:
                    layers_bing += """
        var bingsat = new OpenLayers.Layer.Bing( {key: bingApiKey, type: 'Aerial', name: '%s'} );
        map.addLayer(bingsat);
                    """ % bing.Satellite
                if bing.Maps:
                    layers_bing += """
        var bingmaps = new OpenLayers.Layer.Bing( {key: bingApiKey, type: 'Road', name: '%s'} );
        map.addLayer(bingmaps);
                    """ % bing.Maps
                if bing.Hybrid:
                    layers_bing += """
        var binghybrid = new OpenLayers.Layer.Bing( {key: bingApiKey, type: 'AerialWithLabels', name: '%s'} );
        map.addLayer(binghybrid);
                    """ % bing.Hybrid
        #        if bing.Terrain:
        #            layers_bing += """
        #var bingterrain = new OpenLayers.Layer.VirtualEarth( '%s' , {type: VEMapStyle.Shaded, 'sphericalMercator': true } );
        #map.addLayer(bingterrain);
        #            """ % bing.Terrain

        # WFS
        layers_wfs = ""
        wfs_enabled = db(db.gis_layer_wfs.enabled == True).select()
        if wfs_enabled:
            layers_wfs = cluster_style_options
        for layer in wfs_enabled:
            if layer.role_required and not auth.s3_has_role(layer.role_required):
                continue
            name = layer.name
            name_safe = re.sub("\W", "_", name)
            url = layer.url
            try:
                wfs_version = layer.version
            except:
                wfs_version = ""
            featureType = "featureType: '%s'" % layer.featureType
            if layer.featureNS:
                featureNS = """,
                    featureNS: '%s'""" % layer.featureNS
            else:
                featureNS = ""
            if layer.geometryName:
                geometryName = """,
                    geometryName: '%s'""" % layer.geometryName
            else:
                geometryName = ""
            try:
                query = (db.gis_projection.id == layer.projection_id)
                wfs_projection = db(query).select(db.gis_projection.epsg,
                                                  limitby=(0, 1),
                                                  cache=cache).first().epsg
                wfs_projection1 = "projection: new OpenLayers.Projection('EPSG:%i')," % wfs_projection
                wfs_projection2 = "srsName: 'EPSG:%i'," % wfs_projection
            except:
                wfs_projection = ""
                wfs_projection2 = ""
            if layer.visible:
                wfs_visibility = ""
            else:
                wfs_visibility = "wfsLayer%s.setVisibility(false);" % name_safe
            #if layer.editable:
            #    wfs_strategy = "strategies: [new OpenLayers.Strategy.BBOX(), new OpenLayers.Strategy.Save()],"
            wfs_strategy = """
                            new OpenLayers.Strategy.BBOX({
                                // only load features for the visible extent
                                ratio: 1,
                                // fetch features after every resolution change
                                resFactor: 1
                                })
            """
            layers_wfs  += cluster_style + """
        var wfsLayer""" + name_safe + """ = new OpenLayers.Layer.Vector( '""" + name + """', {
                // limit the number of features to avoid browser freezes
                maxFeatures: 1000,
                strategies: [""" + wfs_strategy + ", " + strategy_cluster + """],
                """ + wfs_projection1 + """
                //outputFormat: "json",
                //readFormat: new OpenLayers.Format.GeoJSON(),
                protocol: new OpenLayers.Protocol.WFS({
                    version: '""" + wfs_version + """',
                    """ + wfs_projection2 + """
                    url:  '""" + url + """',
                    """ + featureType + featureNS + geometryName + """
                }),
                styleMap: featureClusterStyleMap
            });
        map.addLayer(wfsLayer""" + name_safe + """);
        """ + wfs_visibility + """
        """

        # WMS
        layers_wms = ""
        wms_enabled = db(db.gis_layer_wms.enabled == True).select()
        for layer in wms_enabled:
            if layer.role_required and not auth.s3_has_role(layer.role_required):
                continue
            name = layer.name
            name_safe = re.sub("\W", "_", name)
            url = layer.url
            try:
                wms_version = "version: '%s'," % layer.version
            except:
                wms_version = ""
            try:
                wms_map = "map: '%s'," % layer.map
            except:
                wms_map = ""
            wms_layers = layer.layers
            try:
                format = "type: '%s'," % layer.img_format
            except:
                format = ""
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
                if layer.opacity:
                    options += """,
                    opacity: %f""" % layer.opacity
                if layer.buffer:
                    options += """,
                    buffer: %i""" % layer.buffer
                else:
                    options += """,
                    buffer: 0"""

            layers_wms  += """
        var wmsLayer""" + name_safe + """ = new OpenLayers.Layer.WMS(
            '""" + name + """', '""" + url + """', {
               """ + wms_map + """
               layers: '""" + wms_layers + """',
               """ + format + """
               """ + transparent + """
               """ + wms_version + """
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
            if layer.role_required and not auth.s3_has_role(layer.role_required):
                continue
            name = layer.name
            name_safe = re.sub("\W", "_", name)
            url = layer.url
            tms_layers = layer.layers
            try:
                format = "type: '%s'" % layer.img_format
            except:
                format = ""

            layers_tms  += """
        var tmsLayer%s = new OpenLayers.Layer.TMS( '%s', '%s', {
                layername: '%s',
                %s
            });
        map.addLayer(tmsLayer""" + name_safe + """);
        """ % (name_safe, name, url, tms_layers, format)

        # XYZ
        layers_xyz = ""
        xyz_enabled = db(db.gis_layer_tms.enabled == True).select()
        for layer in xyz_enabled:
            if layer.role_required and not auth.s3_has_role(layer.role_required):
                continue
            name = layer.name
            name_safe = re.sub("\W", "_", name)
            url = layer.url
            if layer.sphericalMercator:
                sphericalMercator = "sphericalMercator: 'true',"
            else:
                sphericalMercator = ""
            if layer.transitionEffect:
                transitionEffect = "transitionEffect: '%s'," % layer.transitionEffect
            else:
                transitionEffect = ""
            if layer.numZoomLevels:
                xyz_numZoomLevels = "numZoomLevels: '%i'" % layer.numZoomLevels
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
                    base += "opacity: '%f'," % layer.opacity
                base += "isBaseLayer: 'false'"

            layers_xyz  += """
        var xyzLayer%s = new OpenLayers.Layer.XYZ( '%s', '%s', {
                %s
                %s
                %s
                %s
            });
        map.addLayer(xyzLayer%s);
        """ % (name_safe, name, url, sphericalMercator, transitionEffect,
               xyz_numZoomLevels, base, name_safe)

        # JS
        layers_js = ""
        js_enabled = db(db.gis_layer_js.enabled == True).select()
        for layer in js_enabled:
            if layer.role_required and not auth.s3_has_role(layer.role_required):
                continue
            layers_js  += layer.code

        #
        # Overlays
        #

        # Can we cache downloaded feeds?
        # Needed for unzipping & filtering as well
        cachepath = os.path.join(request.folder, "uploads", "gis_cache")
        if os.access(cachepath, os.W_OK):
            cacheable = True
        else:
            cacheable = False

        # Duplicate Features to go across the dateline?
        if deployment_settings.get_gis_duplicate_features():
            uuid_from_fid = """
            var uuid = fid.replace('_', '');
            """
        else:
            uuid_from_fid = """
            var uuid = fid;
            """
        #
        # Features
        #
        layers_features = ""
        if feature_queries or add_feature:

            if not wfs_enabled:
                layers_features = cluster_style_options

            layers_features += """
        var featureLayers = new Array();
        var features = [];
        var parser = new OpenLayers.Format.WKT();
        var geom, featureVec;

        function addFeature(feature_id, name, geom, styleMarker, image, popup_url) {
            geom = geom.transform(proj4326, projection_current);
            // Needs to be uniquely instantiated
            var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
            if ('' == styleMarker.iconURL) {
                style_marker.graphicName = styleMarker.graphicName;
                style_marker.pointRadius = styleMarker.pointRadius;
                style_marker.fillColor = styleMarker.fillColor;
                style_marker.fillOpacity = styleMarker.opacity;
                style_marker.strokeColor = styleMarker.fillColor;
                style_marker.strokeWidth = 2;
                style_marker.strokeOpacity = styleMarker.opacity;
            } else {
                // Set icon dims (set in onload)
                style_marker.graphicWidth = image.width;
                style_marker.graphicHeight = image.height;
                style_marker.graphicXOffset = -(image.width / 2);
                style_marker.graphicYOffset = -image.height;
                style_marker.graphicOpacity = styleMarker.opacity;
                style_marker.externalGraphic = styleMarker.iconURL;
            }
            // Create Feature Vector
            var featureVec = new OpenLayers.Feature.Vector(geom, null, style_marker);
            featureVec.fid = feature_id;
            // Store the popup_url in the feature so that onFeatureSelect can read it
            featureVec.popup_url = popup_url;
            featureVec.attributes.name = name;
            return featureVec;
        }

        function onFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var id = 'featureLayerPopup';
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            if (feature.cluster) {
                // Cluster
                var name, fid, uuid, url;
                var html = '%s:<ul>';
                for (var i = 0; i < feature.cluster.length; i++) {
                    name = feature.cluster[i].attributes.name;
                    fid = feature.cluster[i].fid;
                    %s
                    if ( feature.cluster[i].popup_url.match("<id>") != null ) {
                        url = feature.cluster[i].popup_url.replace("<id>", uuid);
                    } else {
                        url = feature.cluster[i].popup_url + uuid;
                    }
                    html += "<li><a href='javascript:loadClusterPopup(" + "\\"" + url + "\\", \\"" + id + "\\"" + ")'>" + name + "</a></li>";
                }
                html += '</ul>';
                html += "<div align='center'><a href='javascript:zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    html,
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                map.addPopup(popup);
            } else {
                // Single Feature
                var popup_url = feature.popup_url;
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    "%s...<img src='%s' border=0>",
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                map.addPopup(popup);
                // call AJAX to get the contentHTML
                var fid = feature.fid;
                %s
                if ( popup_url.match("<id>") != null ) {
                    popup_url = popup_url.replace("<id>", uuid)
                }
                else {
                    popup_url = popup_url + uuid;
                }
                loadDetails(popup_url, id, popup);
            }
        }

        function loadDetails(url, id, popup) {
            $.get(
                    url,
                    function(data) {
                        $('#' + id + '_contentDiv').html(data);
                        popup.updateSize();
                    },
                    'html'
                );
        }

        """ % (T("There are multiple records at this location"), uuid_from_fid,
               T("Loading"),
               URL(r=request, c="static", f="img", args="ajax-loader.gif"),
               uuid_from_fid)
            # Draft Features
            # This is currently used just to select the Lat/Lon for a Location, so no Features pre-loaded
            if add_feature:
                layers_features += """
            //features = [];
        """ + cluster_style + """
        draftLayer = new OpenLayers.Layer.Vector(
            '%s', {}
            //{
            //    strategies: [ %s ],
            //    styleMap: featureClusterStyleMap
            //}
        );
        draftLayer.setVisibility(true);
        map.addLayer(draftLayer);
        """ % (T("Draft Features"), strategy_cluster)

            if None:
                layers_features += """
        //draftLayer.events.on({
        //    "featureselected": onFeatureSelect,
        //    "featureunselected": onFeatureUnselect
        //});
        // Don't include here as we don't want the highlightControl & currently gain nothing else from it
        //featureLayers.push(draftLayer);

        // We don't currently do anything here
        //function onFeatureSelect(event) {
            // unselect any previous selections
        //    tooltipUnselect(event);
        //    var feature = event.feature;
        //    var id = 'draftLayerPopup';
        //    if(feature.cluster) {
                // Cluster
        //        centerPoint = feature.geometry.getBounds().getCenterLonLat();
        //    } else {
                // Single Feature
        //    }
        //}
        """

            # Feature Queries
            for layer in feature_queries:
                # NB Security for these layers has to come at an earlier stage (e.g. define_map())
                # Features passed as Query
                if "name" in layer:
                    name = str(T(layer["name"]))
                else:
                    name = "Query%i" % int(random.random()*1000)

                if "marker" in layer:
                    marker = layer["marker"]
                    try:
                        # query
                        marker_id = marker.id
                        markerLayer = marker
                    except:
                        # integer (marker_id)
                        query = (db.gis_marker.id == layer["marker"])
                        markerLayer = db(query).select(db.gis_marker.image,
                                                       db.gis_marker.height,
                                                       db.gis_marker.width,
                                                       limitby=(0, 1),
                                                       cache=cache).first()
                else:
                    markerLayer = ""

                if "opacity" in layer:
                    opacity = layer["opacity"]
                else:
                    opacity = 1

                if "popup_url" in layer:
                    _popup_url = urllib.unquote(layer["popup_url"])
                else:
                    _popup_url = urllib.unquote(URL(r=request, c="gis", f="location",
                                                    args=["read.popup?location.id="]))

                if "polygon" in layer and layer.polygon:
                    polygons = True
                else:
                    polygons = False

                # Generate HTML snippet
                name_safe = re.sub("\W", "_", name)
                if "active" in layer and layer["active"]:
                    visibility = "featureLayer%s.setVisibility(true);" % name_safe
                else:
                    visibility = "featureLayer%s.setVisibility(false);" % name_safe
                layers_features += """
        features = [];
        var popup_url = '%s';
        %s
        var featureLayer%s = new OpenLayers.Layer.Vector(
            '%s',
            {
                strategies: [ %s ],
                styleMap: featureClusterStyleMap
            }
        );
        %s
        map.addLayer(featureLayer%s);
        featureLayer%s.events.on({
            'featureselected': onFeatureSelect,
            'featureunselected': onFeatureUnselect
        });
        featureLayers.push(featureLayer%s);
        """ % (_popup_url, cluster_style, name_safe, name, strategy_cluster,
               visibility, name_safe, name_safe, name_safe)
                features = layer["query"]
                for _feature in features:
                    try:
                        _feature.gis_location.id
                        # Query was generated by a Join
                        feature = _feature.gis_location
                    except (AttributeError, KeyError):
                        # Query is a simple select
                        feature = _feature
                    # Should we use Polygons or Points?
                    if polygons:
                        if feature.get("wkt"):
                            wkt = feature.wkt
                        else:
                            # Deal with manually-imported Features which are missing WKT
                            try:
                                lat = feature.lat
                                lon = feature.lon
                                if (lat is None) or (lon is None):
                                    # Zero is allowed but not None
                                    if feature.get("parent"):
                                        # Skip the current record if we can
                                        latlon = self.get_latlon(feature.parent)
                                    elif feature.get("id"):
                                        latlon = self.get_latlon(feature.id)
                                    else:
                                        # nothing we can do!
                                        continue
                                    if latlon:
                                        lat = latlon["lat"]
                                        lon = latlon["lon"]
                                    else:
                                        # nothing we can do!
                                        continue
                            except:
                                if feature.get("parent"):
                                    # Skip the current record if we can
                                    latlon = self.get_latlon(feature.parent)
                                elif feature.get("id"):
                                    latlon = self.get_latlon(feature.id)
                                else:
                                    # nothing we can do!
                                    continue
                                if latlon:
                                    lat = latlon["lat"]
                                    lon = latlon["lon"]
                                else:
                                    # nothing we can do!
                                    continue
                            wkt = self.latlon_to_wkt(lat, lon)
                    else:
                        # Just display Point data, even if we have Polygons
                        # @ToDo: DRY with Polygon
                        try:
                            lat = feature.lat
                            lon = feature.lon
                            if (lat is None) or (lon is None):
                                # Zero is allowed but not None
                                if feature.get("parent"):
                                    # Skip the current record if we can
                                    latlon = self.get_latlon(feature.parent)
                                elif feature.get("id"):
                                    latlon = self.get_latlon(feature.id)
                                else:
                                    # nothing we can do!
                                    continue
                                if latlon:
                                    lat = latlon["lat"]
                                    lon = latlon["lon"]
                                else:
                                    # nothing we can do!
                                    continue
                        except:
                            if feature.get("parent"):
                                # Skip the current record if we can
                                latlon = self.get_latlon(feature.parent)
                            elif feature.get("id"):
                                latlon = self.get_latlon(feature.id)
                            else:
                                # nothing we can do!
                                continue
                            if latlon:
                                lat = latlon["lat"]
                                lon = latlon["lon"]
                            else:
                                # nothing we can do!
                                continue
                        wkt = self.latlon_to_wkt(lat, lon)

                    try:
                        # Has a per-feature Vector Shape been added to the query?
                        graphicName = feature.shape
                        if graphicName not in ["circle", "square", "star", "x",
                                               "cross", "triangle"]:
                            # Default to Circle
                            graphicName = "circle"
                        try:
                            pointRadius = feature.size
                            if not pointRadius:
                                pointRadius = 12
                        except (AttributeError, KeyError):
                            pointRadius = 12
                        try:
                            fillColor = feature.color
                            if not fillColor:
                                fillColor = "orange"
                        except (AttributeError, KeyError):
                            fillColor = "orange"
                        marker_url = ""
                    except (AttributeError, KeyError):
                        # Use a Marker not a Vector Shape
                        try:
                            # Has a per-feature marker been added to the query?
                            _marker = feature.marker
                            if _marker:
                                marker = _marker
                            else:
                                marker = marker_default
                        except (AttributeError, KeyError):
                            if markerLayer:
                                marker = markerLayer
                            else:
                                marker = marker_default
                        # Faster to bypass the download handler
                        marker_url = URL(r=request, c="static", f="img",
                                         args=["markers", marker.image])

                    try:
                        # Has a per-feature popup_label been added to the query?
                        popup_label = feature.popup_label
                    except (AttributeError, KeyError):
                        popup_label = feature.name

                    # Allows map API to be used with Storage instead of Rows
                    if not popup_label:
                        popup_label = feature.name
                    # Deal with apostrophes in Feature Names
                    fname = re.sub("'", "\\'", popup_label)

                    if marker_url:
                        layers_features += """
        styleMarker.iconURL = '%s';
        styleMarker.opacity = '%f';
        // Need unique names
        // More reliable & faster to use the height/width calculated on upload
        s3_gis_image = new Array();
        s3_gis_image.height = %i;
        s3_gis_image.width = %i;
        scaleImage(s3_gis_image);
        """ % (marker_url, opacity, marker.height, marker.width)
                    else:
                        layers_features += """
        s3_gis_image = '';
        styleMarker.iconURL = '';
        styleMarker.opacity = '%f';
        styleMarker.graphicName = '%s';
        styleMarker.pointRadius = %i;
        styleMarker.fillColor = '%s';
        """ % (opacity, graphicName, pointRadius, fillColor)
                    layers_features += """
        geom = parser.read('%s').geometry;
        featureVec = addFeature('%i', '%s', geom, styleMarker, s3_gis_image, popup_url)
        features.push(featureVec);
        """ % (wkt, feature.id, fname)
                    if deployment_settings.get_gis_duplicate_features():
                        # Add an additional Point feature to provide wrapping around the Data Line
                        # lon<0 have a duplicate at lon+360
                        if lon < 0:
                            lon = lon + 360
                        # lon>0 have a duplicate at lon-360
                        else:
                            lon = lon - 360
                        wkt = self.latlon_to_wkt(lat, lon)
                        layers_features += """
        geom = parser.read('%s').geometry;
        featureVec = addFeature('_%i', '%s', geom, styleMarker, i, popup_url)
        features.push(featureVec);
        """ % (wkt, feature.id, fname)
                # Append to Features layer
                layers_features += """
        featureLayer%s.addFeatures(features);
        """ % name_safe
            # Append to allLayers
            layers_features += """
        allLayers = allLayers.concat(featureLayers);
        """

        else:
            # No Feature Layers requested
            pass

        layer_coordinategrid = ""
        layers_geojson = ""
        layers_georss = ""
        layers_gpx = ""
        layers_kml = ""
        if catalogue_overlays:
            # GeoJSON
            geojson_enabled = db(db.gis_layer_geojson.enabled == True).select()
            if geojson_enabled:
                layers_geojson += """
        var geojsonLayers = new Array();
        var format_geojson = new OpenLayers.Format.GeoJSON();
        function onGeojsonFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            var selectedFeature = feature;
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            if (feature.cluster) {
                // Cluster
                var name, fid, uuid, url;
                var html = '""" + T("There are multiple records at this location") + """:<ul>';
                for (var i = 0; i < feature.cluster.length; i++) {
                    name = feature.cluster[i].attributes.name;
                    fid = feature.cluster[i].fid;
                    """ + uuid_from_fid + """
                    //if ( feature.cluster[i].popup_url.match("<id>") != null ) {
                    //    url = feature.cluster[i].popup_url.replace("<id>", uuid);
                    //} else {
                    //    url = feature.cluster[i].popup_url + uuid;
                    //}
                    //html += "<li><a href='javascript:loadClusterPopup(" + "\\"" + url + "\\", \\"" + id + "\\"" + ")'>" + name + "</a></li>";
                }
                html += '</ul>';
                html += "<div align='center'><a href='javascript:zoomToSelectedFeature(" + centerPoint.lon + "," + centerPoint.lat + ", 3)'>Zoom in</a></div>";
                var popup = new OpenLayers.Popup.FramedCloud(
                    id,
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    html,
                    null,
                    true,
                    onPopupClose
                );
                feature.popup = popup;
                map.addPopup(popup);
            } else {
                // Single Feature
                if (undefined == feature.attributes.description) {
                    var popup = new OpenLayers.Popup.FramedCloud('geojsonpopup',
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    '<h2>' + feature.attributes.name + '</h2>',
                    null, true, onPopupClose);
                } else {
                    var popup = new OpenLayers.Popup.FramedCloud('geojsonpopup',
                    centerPoint,
                    new OpenLayers.Size(200, 200),
                    '<h2>' + feature.attributes.name + '</h2>' + feature.attributes.description,
                    null, true, onPopupClose);
                };
            };
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in geojson_enabled:
                    if layer.role_required and not auth.s3_has_role(layer.role_required):
                        continue
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    geojson_projection = db(db.gis_projection.id == layer["projection_id"]).select(db.gis_projection.epsg, limitby=(0, 1)).first().epsg
                    if geojson_projection == 4326:
                        projection_str = "projection: proj4326,"
                    else:
                        projection_str = "projection: new OpenLayers.Projection('EPSG:" + geojson_projection + "'),"
                    marker_id = layer["marker_id"]
                    if marker_id:
                        marker = db(db.gis_marker.id == marker_id).select(db.gis_marker.image, db.gis_marker.height, db.gis_marker.width, limitby=(0, 1)).first()
                    else:
                        marker = db(db.gis_marker.id == marker__id_default).select(db.gis_marker.image, db.gis_marker.height, db.gis_marker.width, limitby=(0, 1)).first()
                    marker_url = URL(r=request, c="static", f="img", args=["markers", marker.image])
                    height = marker.height
                    width = marker.width

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "geojsonLayer" + name_safe + ".setVisibility(true);"
                    else:
                        visibility = "geojsonLayer" + name_safe + ".setVisibility(false);"
                    layers_geojson += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        s3_gis_image = new Image();
        s3_gis_image.onload = scaleImage;
        s3_gis_image.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = i.width;
        style_marker.graphicHeight = i.height;
        style_marker.graphicXOffset = -(i.width / 2);
        style_marker.graphicYOffset = -i.height;
        style_marker.externalGraphic = iconURL;
        // Style Rule For Clusters
        var style_cluster_style = {
            label: '${label}',
            pointRadius: '${radius}',
            fillColor: '${fill}',
            fillOpacity: 0.5,
            strokeColor: '${stroke}',
            strokeWidth: 2,
            strokeOpacity: 1,
            graphicWidth: '${graphicWidth}',
            graphicHeight: '${graphicHeight}',
            graphicXOffset: '${graphicXOffset}',
            graphicYOffset: '${graphicYOffset}',
            graphicOpacity: 1, //'${graphicOpacity}'
            externalGraphic: '${externalGraphic}'
        };
        var style_cluster_options = {
            context: {
                graphicWidth: function(feature) {
                    // Unclustered Point
                    var pix = i.width;
                    // Clustered Point
                    if (feature.cluster) {
                        pix = '';
                    }
                    return pix;
                },
                graphicHeight: function(feature) {
                    // Unclustered Point
                    var pix = i.width;
                    // Clustered Point
                    if (feature.cluster) {
                        pix = '';
                    }
                    return pix;
                },
                graphicXOffset: function(feature) {
                    // Unclustered Point
                    var pix = -(i.width / 2);
                    // Clustered Point
                    if (feature.cluster) {
                        pix = '';
                    }
                    return pix;
                },
                graphicYOffset: function(feature) {
                    // Unclustered Point
                    var pix = -i.height;
                    // Clustered Point
                    if (feature.cluster) {
                        pix = '';
                    }
                    return pix;
                },
                //graphicOpacity: function(feature) {
                    // Unclustered Point
                //    var opacity = styleMarker.opacity;
                    // Clustered Point
                //    if (feature.cluster) {
                //        opacity = '';
                //    }
                //    return opacity;
                //},
                externalGraphic: function(feature) {
                    // Unclustered Point
                    var url = iconURL;
                    // Clustered Point
                    if (feature.cluster) {
                        url = '';
                    }
                    return url;
                },
                radius: function(feature) {
                    // Size for Unclustered Point
                    var pix = 12;
                    // Size for Clustered Point
                    if (feature.cluster) {
                        pix = Math.min(feature.attributes.count/2, 8) + 12;
                    }
                    return pix;
                },
                fill: function(feature) {
                    // fillColor for Unclustered Point
                    var color = '#f5902e';
                    // fillColor for Clustered Point
                    if (feature.cluster) {
                        color = '#8087ff';
                    }
                    return color;
                },
                stroke: function(feature) {
                    // strokeColor for Unclustered Point
                    var color = '#f5902e';
                    // strokeColor for Clustered Point
                    if (feature.cluster) {
                        color = '#2b2f76';
                    }
                    return color;
                },
                label: function(feature) {
                    // Label For Unclustered Point or Cluster of just 2
                    var label = '';
                    // Label For Clustered Point
                    if (feature.cluster && feature.attributes.count > 2) {
                        label = feature.attributes.count;
                    }
                    return label;
                }
            }
        };
        // Needs to be uniquely instantiated
        var style_cluster = new OpenLayers.Style(style_cluster_style, style_cluster_options);
        // Define StyleMap, Using 'style_cluster' rule for 'default' styling intent
        var featureClusterStyleMap = new OpenLayers.StyleMap({
                                          'default': style_cluster,
                                          'select': {
                                              fillColor: '#ffdc33',
                                              strokeColor: '#ff9933'
                                          }
        });
        var geojsonLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                """ + projection_str + """
                strategies: [ new OpenLayers.Strategy.BBOX(), """ + strategy_cluster + """ ],
                //style: style_marker,
                styleMap: featureClusterStyleMap,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_geojson
                })
            }
        );
        """ + visibility + """
        map.addLayer(geojsonLayer""" + name_safe + """);
        geojsonLayers.push(geojsonLayer""" + name_safe + """);
        geojsonLayer""" + name_safe + """.events.on({ "featureselected": onGeojsonFeatureSelect, "featureunselected": onFeatureUnselect });
        """
                layers_geojson += """
        allLayers = allLayers.concat(geojsonLayers);
        """

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
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            if (undefined == feature.attributes.description) {
                var popup = new OpenLayers.Popup.FramedCloud('georsspopup',
                centerPoint,
                new OpenLayers.Size(200, 200),
                '<h2>' + feature.attributes.title + '</h2>',
                null, true, onPopupClose);
            } else {
                var popup = new OpenLayers.Popup.FramedCloud('georsspopup',
                centerPoint,
                new OpenLayers.Size(200, 200),
                '<h2>' + feature.attributes.title + '</h2>' + feature.attributes.description,
                null, true, onPopupClose);
            };
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in georss_enabled:
                    if layer.role_required and not auth.s3_has_role(layer.role_required):
                        continue
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    query = (db.gis_projection.id == layer["projection_id"])
                    georss_projection = db(query).select(db.gis_projection.epsg,
                                                         limitby=(0, 1)).first().epsg
                    if georss_projection == 4326:
                        projection_str = "projection: proj4326,"
                    else:
                        projection_str = "projection: new OpenLayers.Projection('EPSG:%i')," % georss_projection
                    marker_id = layer["marker_id"]
                    if marker_id:
                        query = (db.gis_marker.id == marker_id)
                        marker = db(query).select(db.gis_marker.image,
                                                  db.gis_marker.height,
                                                  db.gis_marker.width,
                                                  limitby=(0, 1)).first()
                    else:
                        query = (db.gis_marker.id == marker__id_default)
                        marker = db(query).select(db.gis_marker.image,
                                                  db.gis_marker.height,
                                                  db.gis_marker.width,
                                                  limitby=(0, 1)).first()
                    marker_url = URL(r=request, c="static", f="img",
                                     args=["markers", marker.image])
                    height = marker.height
                    width = marker.width

                    if cacheable:
                        # Download file
                        try:
                            file = fetch(url)
                            warning = ""
                        except urllib2.URLError:
                            warning = "URLError"
                        except urllib2.HTTPError:
                            warning = "HTTPError"
                        _name = name.replace(" ", "_")
                        _name = _name.replace(",", "_")
                        filename = "gis_cache.file.%s.rss" % _name
                        filepath = os.path.join(cachepath, filename)
                        f = open(filepath, "w")
                        # Handle errors
                        if "URLError" in warning or "HTTPError" in warning:
                            # URL inaccessible
                            if os.access(filepath, os.R_OK):
                                # Use cached version
                                query = (db.gis_cache.name == name)
                                date = db(query).select(db.gis_cache.modified_on,
                                                        limitby=(0, 1)).first().modified_on
                                response.warning += "%s %s %s\n" % (url,
                                                                    T("not accessible - using cached version from"),
                                                                    str(date))
                                url = URL(r=request, c="default", f="download", args=[filename])
                            else:
                                # No cached version available
                                response.warning += "%s %s\n" (url,
                                                                  T("not accessible - no cached version available!"))
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
                            url = URL(r=request, c="default", f="download",
                                      args=[filename])
                    else:
                        # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                        pass

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "georssLayer%s.setVisibility(true);" % name_safe
                    else:
                        visibility = "georssLayer%s.setVisibility(false);" % name_safe
                    layers_georss += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        s3_gis_image = new Image();
        s3_gis_image.onload = scaleImage;
        s3_gis_image.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = s3_gis_image.width;
        style_marker.graphicHeight = s3_gis_image.height;
        style_marker.graphicXOffset = -(s3_gis_image.width / 2);
        style_marker.graphicYOffset = -s3_gis_image.height;
        style_marker.externalGraphic = iconURL;
        var georssLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                """ + projection_str + """
                strategies: [ new OpenLayers.Strategy.Fixed(), """ + strategy_cluster + """ ],
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
        var gpxLayers = new Array();
        function onGpxFeatureSelect(event) {
            // unselect any previous selections
            tooltipUnselect(event);
            var feature = event.feature;
            // Anything we want to do here?
        }
        """
                for layer in gpx_enabled:
                    if layer.role_required and not auth.s3_has_role(layer.role_required):
                        continue
                    name = layer["name"]
                    query = (db.gis_track.id == layer.track_id)
                    track = db(query).select(db.gis_track.track,
                                             limitby=(0, 1)).first()
                    if track:
                        url = "%s/%s" % (URL(r=request, c="default", f="download"),
                                         track.track)
                    else:
                        url = ""
                    visible = layer["visible"]
                    waypoints = layer["waypoints"]
                    tracks = layer["tracks"]
                    routes = layer["routes"]
                    marker_id = layer["marker_id"]
                    if marker_id:
                        query = (db.gis_marker.id == marker_id)
                        marker = db(query).select(db.gis_marker.image,
                                                  limitby=(0, 1)).first().image
                    else:
                        marker = marker_default.image
                    marker_url = URL(r=request, c="static", f="img",
                                     args=["markers", marker])

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if visible:
                        visibility = "gpxLayer%s.setVisibility(true);" % name_safe
                    else:
                        visibility = "gpxLayer%s.setVisibility(false);" % name_safe
                    gpx_format = "extractAttributes:true"
                    if not waypoints:
                        gpx_format += ", extractWaypoints:false"
                        style_marker = """
        style_marker.externalGraphic = '';
        """
                    else:
                        style_marker = """
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = i.width;
        style_marker.graphicHeight = i.height;
        style_marker.graphicXOffset = -(i.width / 2);
        style_marker.graphicYOffset = -i.height;
        style_marker.externalGraphic = iconURL;
        """
                    if not tracks:
                        gpx_format += ", extractTracks:false"
                    if not routes:
                        gpx_format += ", extractRoutes:false"
                    layers_gpx += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        s3_gis_image = new Image();
        s3_gis_image.onload = scaleImage;
        s3_gis_image.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        """ + style_marker + """
        style_marker.strokeColor = 'blue';
        style_marker.strokeWidth = 6;
        style_marker.strokeOpacity = 0.5;
        var gpxLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name_safe + """',
            {
                projection: proj4326,
                strategies: [ new OpenLayers.Strategy.Fixed(), """ + strategy_cluster + """ ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: new OpenLayers.Format.GPX({""" + gpx_format + """})
                })
            }
        );
        """ + visibility + """
        map.addLayer(gpxLayer""" + name_safe + """);
        gpxLayers.push(gpxLayer""" + name_safe + """);
        gpxLayer""" + name_safe + """.events.on({ 'featureselected': onGpxFeatureSelect, 'featureunselected': onFeatureUnselect });
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
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            var selectedFeature = feature;
            var title = feature.layer.title;
            var _attributes = feature.attributes;
            var type = typeof _attributes[title];
            if ('object' == type) {
                _title = _attributes[title].value;
            } else {
                _title = _attributes[title];
            }
            var body = feature.layer.body.split(' ');
            var content = '';
            for (var i = 0; i < body.length; i++) {
                type = typeof _attributes[body[i]];
                if ('object' == type) {
                    // Geocommons style
                    var displayName = _attributes[body[i]].displayName;
                    if (displayName == '') {
                        displayName = body[i];
                    }
                    var value = _attributes[body[i]].value;
                    var row = '<b>' + displayName + '</b>: ' + value + '<br />';
                } else {
                    var row = _attributes[body[i]] + '<br />';
                }
                content += row;
            }
            // Protect the content against JavaScript attacks
            if (content.search('<script') != -1) {
                content = 'Content contained Javascript! Escaped content below.<br />' + content.replace(/</g, '<');
            }
            var contents = '<h2>' + _title + '</h2>' + content;

            var popup = new OpenLayers.Popup.FramedCloud('kmlpopup',
                centerPoint,
                new OpenLayers.Size(200, 200),
                contents,
                null, true, onPopupClose
            );
            feature.popup = popup;
            popup.feature = feature;
            map.addPopup(popup);
        }
        """
                for layer in kml_enabled:
                    if layer.role_required and not auth.s3_has_role(layer.role_required):
                        continue
                    name = layer["name"]
                    url = layer["url"]
                    visible = layer["visible"]
                    title = layer["title"] or "name"
                    body = layer["body"] or "description"
                    projection_str = "projection: proj4326,"
                    marker_id = layer["marker_id"]
                    if marker_id:
                        query = (db.gis_marker.id == marker_id)
                        marker = db(query).select(db.gis_marker.image,
                                                  db.gis_marker.height,
                                                  db.gis_marker.width,
                                                  limitby=(0, 1)).first()
                    else:
                        marker = marker_default
                    marker_url = URL(r=request, c="static", f="img",
                                     args=["markers", marker.image])
                    height = marker.height
                    width = marker.width
                    if cacheable:
                        # Download file
                        file, warning = self.download_kml(url, public_url)
                        _name = name.replace(" ", "_")
                        _name = _name.replace(",", "_")
                        filename = "gis_cache.file.%s.kml" % _name
                        filepath = os.path.join(cachepath, filename)
                        f = open(filepath, "w")
                        # Handle errors
                        if "URLError" in warning or "HTTPError" in warning:
                            # URL inaccessible
                            if os.access(filepath, os.R_OK):
                                statinfo = os.stat(filepath)
                                if statinfo.st_size:
                                    # Use cached version
                                    query = (db.gis_cache.name == name)
                                    date = db(query).select(db.gis_cache.modified_on,
                                                            limitby=(0, 1)).first().modified_on
                                    response.warning += "%s %s %s\n" % (url,
                                                                        T("not accessible - using cached version from"),
                                                                        str(date))
                                    url = URL(r=request, c="default", f="download",
                                              args=[filename])
                                else:
                                    # 0k file is all that is available
                                    response.warning += "%s %s\n" % (url,
                                                                     T("not accessible - no cached version available!"))
                                    # skip layer
                                    continue
                            else:
                                # No cached version available
                                response.warning += "%s %s\n" % (url,
                                                                 T("not accessible - no cached version available!"))
                                # skip layer
                                continue
                        else:
                            # Download was succesful
                            if "ParseError" in warning:
                                # @ToDo Parse detail
                                response.warning += "%s: %s %s\n" % (T("Layer"),
                                                                   name,
                                                                   T("couldn't be parsed so NetworkLinks not followed."))
                            if "GroundOverlay" in warning or "ScreenOverlay" in warning:
                                response.warning += "%s: %s %s\n" % (T("Layer"),
                                                                     name,
                                                                     T("includes a GroundOverlay or ScreenOverlay which aren't supported in OpenLayers yet, so it may not work properly."))
                            # Write file to cache
                            f.write(file)
                            f.close()
                            query = (db.gis_cache.name == name)
                            record = db(query).select().first()
                            if record:
                                record.update(modified_on=response.utcnow)
                            else:
                                db.gis_cache.insert(name=name, file=filename)
                            url = URL(r=request, c="default", f="download",
                                      args=[filename])
                    else:
                        # No caching possible (e.g. GAE), display file direct from remote (using Proxy)
                        pass

                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    layer_name = "kmlLayer%s" % name_safe
                    if visible:
                        visibility = "%s.setVisibility(true);" % layer_name
                    else:
                        visibility = "%s.setVisibility(false);" % layer_name
                    layers_kml += """
        iconURL = '""" + marker_url + """';
        // Pre-cache this image
        // Need unique names
        var s3_gis_image = new Image();
        s3_gis_image.onload = scaleImage;
        s3_gis_image.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = s3_gis_image.width;
        style_marker.graphicHeight = s3_gis_image.height;
        style_marker.graphicXOffset = -(s3_gis_image.width / 2);
        style_marker.graphicYOffset = -s3_gis_image.height;
        style_marker.externalGraphic = iconURL;
        var kmlLayer""" + name_safe + """ = new OpenLayers.Layer.Vector(
            '""" + name + """',
            {
                """ + projection_str + """
                strategies: [ new OpenLayers.Strategy.Fixed(), """ + strategy_cluster + """ ],
                style: style_marker,
                protocol: new OpenLayers.Protocol.HTTP({
                    url: '""" + url + """',
                    format: format_kml
                })
            }
        );
        """ + visibility + """
        kmlLayer""" + name_safe + """.title = '""" + title + """';
        kmlLayer""" + name_safe + """.body = '""" + body + """';
        map.addLayer(kmlLayer""" + name_safe + """);
        kmlLayers.push(kmlLayer""" + name_safe + """);
        kmlLayer""" + name_safe + """.events.on({ 'featureselected': onKmlFeatureSelect, 'featureunselected': onFeatureUnselect });
        """
                layers_kml += """
        allLayers = allLayers.concat(kmlLayers);
        """

            # Coordinate Grid
            coordinate_enabled = db(db.gis_layer_coordinate.enabled == True).select(db.gis_layer_coordinate.name,
                                                                                    db.gis_layer_coordinate.visible,
                                                                                    db.gis_layer_coordinate.role_required)
            if coordinate_enabled:
                layer = coordinate_enabled.first()
                if layer.role_required and not auth.s3_has_role(layer.role_required):
                    pass
                else:
                    name = layer["name"]
                    # Generate HTML snippet
                    name_safe = re.sub("\W", "_", name)
                    if "visible" in layer and layer["visible"]:
                        visibility = ""
                    else:
                        visibility = ", visibility: false"
                    layer_coordinategrid = """
        map.addLayer(new OpenLayers.Layer.cdauth.CoordinateGrid(null, { name: '%s', shortName: 'grid' %s }));
        """ % (name_safe, visibility)

        #############
        # Main script
        #############

        # Configure settings to pass through to Static script
        html.append(SCRIPT("""
var s3_gis_projection = '%i';
var s3_gis_units = '%s';
var s3_gis_maxResolution = %f;
var s3_gis_maxExtent = new OpenLayers.Bounds(%s);
var s3_gis_numZoomLevels = %i;
var s3_gis_max_w = %i;
var s3_gis_max_h = %i;
""" % (projection, units, maxResolution, maxExtent, numZoomLevels,
       deployment_settings.get_gis_marker_max_width(),
       deployment_settings.get_gis_marker_max_height()
       )))

        # Static Script
        if session.s3.debug:
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/S3/s3.gis.js")))
        else:
            html.append(SCRIPT(_type="text/javascript",
                               _src=URL(r=request, c="static", f="scripts/S3/s3.gis.min.js")))

        # Dynamic Script (stuff which should, as far as possible, be moved to static)
        html.append(SCRIPT("""
    """ + center + """
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
        // WFS
        """ + layers_wfs + """
        // WMS
        """ + layers_wms + """
        // XYZ
        """ + layers_xyz + """
        // JS
        """ + layers_js + """

        // Overlays
        // Features
        """ + layers_features + """

        // GeoJSON
        """ + layers_geojson + """

        // GeoRSS
        """ + layers_georss + """

        // GPX
        """ + layers_gpx + """

        // KML
        """ + layers_kml + """

        // CoordinateGrid
        """ + layer_coordinategrid + """
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
        popupControl.unselectAll();
    }

    // Supports highlightControl for All Vector Layers
    var lastFeature = null;
    var tooltipPopup = null;
    function tooltipSelect(event) {
        var feature = event.feature;
        if (feature.cluster) {
            // Cluster
            // no tooltip
        } else {
            // Single Feature
            var selectedFeature = feature;
            // if there is already an opened details window, don\'t draw the tooltip
            if (feature.popup != null) {
                return;
            }
            // if there are other tooltips active, destroy them
            if (tooltipPopup != null) {
                map.removePopup(tooltipPopup);
                tooltipPopup.destroy();
                if (lastFeature != null) {
                    delete lastFeature.popup;
                    tooltipPopup = null;
                }
            }
            lastFeature = feature;
            centerPoint = feature.geometry.getBounds().getCenterLonLat();
            _attributes = feature.attributes;
            if (undefined == _attributes.name && undefined == _attributes.title) {
                // KML Layer
                var title = feature.layer.title;
                if (undefined == title) {
                    // We don't have a suitable title, so don't display a tooltip
                    tooltipPopup = null;
                } else {
                    var type = typeof _attributes[title];
                    if ('object' == type) {
                        _title = _attributes[title].value;
                    } else {
                        _title = _attributes[title];
                    }
                    tooltipPopup = new OpenLayers.Popup("activetooltip",
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        _title,
                        false
                    );
                }
            } else if (undefined == _attributes.title) {
                // Features
                tooltipPopup = new OpenLayers.Popup("activetooltip",
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        _attributes.name,
                        false
                );
            } else {
                // GeoRSS
                tooltipPopup = new OpenLayers.Popup("activetooltip",
                        centerPoint,
                        new OpenLayers.Size(80, 12),
                        _attributes.title,
                        false
                );
            }
            if (tooltipPopup != null) {
                // should be moved to CSS
                tooltipPopup.contentDiv.style.backgroundColor='ffffcb';
                tooltipPopup.contentDiv.style.overflow='hidden';
                tooltipPopup.contentDiv.style.padding='3px';
                tooltipPopup.contentDiv.style.margin='10px';
                tooltipPopup.closeOnMove = true;
                tooltipPopup.autoSize = true;
                tooltipPopup.opacity = 0.7;
                feature.popup = tooltipPopup;
                map.addPopup(tooltipPopup);
            }
        }
    }
    function tooltipUnselect(event){
        var feature = event.feature;
        if (feature != null && feature.popup != null) {
            map.removePopup(feature.popup);
            feature.popup.destroy();
            delete feature.popup;
            tooltipPopup = null;
            lastFeature = null;
        }
    }

    Ext.onReady(function() {
        map = new OpenLayers.Map('center', s3_gis_options);
        addLayers(map);

        map.addControl(new OpenLayers.Control.ScaleLine());
        """ + mouse_position + """
        map.addControl(new OpenLayers.Control.Permalink());
        map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: s3_gis_options}));

        // Popups (add these after the layers)
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
                //renderIntent: 'temporary',
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
            height: """ + str(map_height) + """,
            width: """ + str(map_width) + """,
            id: 'mappanel',
            xtype: 'gx_mappanel',
            map: map,
            center: center,
            zoom: """ + str(zoom) + """,
            plugins: [],
            tbar: new Ext.Toolbar()
        });

        """ + print_tool1 + """

        """ + toolbar + """

        """ + search + """

        var layerTreeBase = {
            text: '""" + T("Base Layers") + """',
            nodeType: 'gx_baselayercontainer',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: false
        };

        var layerTreeFeaturesExternal = {
            text: '""" + T("External Features") + """',
            nodeType: 'gx_overlaylayercontainer',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        };

        var layerTreeFeaturesInternal = {
            //text: '""" + T("Internal Features") + """',
            text: '""" + T("Overlays") + """',
            nodeType: 'gx_overlaylayercontainer',
            layerStore: mapPanel.layers,
            leaf: false,
            expanded: true
        };

        """ + layers_wms_browser + """

        var layerTree = new Ext.tree.TreePanel({
            id: 'treepanel',
            title: '""" + T("Layers") + """',
            loader: new Ext.tree.TreeLoader({applyLoader: false}),
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

        """ + legend1 + """

        """ + layout + """
            autoScroll: true,
            maximizable: true,
            titleCollapse: true,
            height: """ + str(map_height) + """,
            width: """ + str(map_width) + """,
            layout: 'border',
            items: [{
                    region: 'west',
                    id: 'tools',
                    //title: '""" + T("Tools") + """',
                    header: false,
                    border: true,
                    width: 250,
                    autoScroll: true,
                    collapsible: true,
                    collapseMode: 'mini',
                    collapsed: """ + collapsed + """,
                    split: true,
                    items: [
                        layerTree""" + layers_wms_browser2 + search2 + print_tool2 + legend2 + """
                        ]
                    },
                    mapPanel
                    ]
        });
        """ + layout2 + """
        """ + zoomToExtent + """
        """ + toolbar2 + """
    });
    """))

        return html

# -----------------------------------------------------------------------------
class Geocoder(object):
    """
        Base class for all Geocoders
    """

    def __init__(self, db):
        " Initializes the page content object "
        self.db = db
        self.api_key = self.get_api_key()

# -----------------------------------------------------------------------------
class GoogleGeocoder(Geocoder):
    """
        Google Geocoder module
        http://code.google.com/apis/maps/documentation/javascript/v2/reference.html#GGeoStatusCode
        Should convert this to be a thin wrapper for modules.geopy.geocoders.google
    """

    def __init__(self, location, db):
        " Initialise parent class & make any necessary modifications "
        Geocoder.__init__(self, db)
        params = {"q": location, "key": self.api_key}
        self.url = "http://maps.google.com/maps/geo?%s" % urllib.urlencode(params)

    def get_api_key(self):
        " Acquire API key from the database "
        db = self.db
        query = db.gis_apikey.name == "google"
        return db(query).select(db.gis_apikey.apikey,
                                limitby=(0, 1)).first().apikey

    def get_kml(self):
        " Returns the output in KML format "
        url = self.url
        page = fetch(url)
        return page

# -----------------------------------------------------------------------------
class YahooGeocoder(Geocoder):
    """
        Yahoo Geocoder module
        Should convert this to be a thin wrapper for modules.geopy.geocoders.`
    """

    def __init__(self, location, db):
        " Initialise parent class & make any necessary modifications "
        Geocoder.__init__(self, db)
        params = {"location": location, "appid": self.api_key}
        self.url = "http://local.yahooapis.com/MapsService/V1/geocode?%s" % urllib.urlencode(params)

    def get_api_key(self):
        " Acquire API key from the database "
        db = self.db
        query = db.gis_apikey.name == "yahoo"
        return db(query).select(db.gis_apikey.apikey,
                                limitby=(0, 1)).first().apikey

    def get_xml(self):
        " Return the output in XML format "
        url = self.url
        page = fetch(url)
        return page
