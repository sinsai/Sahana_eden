#!/usr/bin/python
"""

bulk_gis.py

A simple loader for GIS files in CSV format.  Developed primarily for loading Administrative Areas for Haiti.

LICENSE: This source file is subject to LGPL license 
that is available through the world-wide-web at the following URI:
http://www.gnu.org/copyleft/lesser.html

author     Timothy Caro-Bruce <tcarobruce@gmail.com> 
package    Sahana - http://sahana.lk/
module     haiti/bulk_gis 
copyright  Lanka Software Foundation - http://www.opensource.lk 
license    http://www.gnu.org/copyleft/lesser.html GNU Lesser General Public License (LGPL) 

"""

import csv
from shapely.wkt import loads as wkt_loads

# CONSTANTS
ADMIN_FEATURE_CLASS_NAME = "Administrative Area"

#BASEDIR = '/path/to/data'   # CHANGE ME!
BASEDIR = '/Users/tim/Documents/work/haiti/data'
FILES = {
    'Departments': 'Haiti_departementes_edited_01132010.csv',
    'Communes': 'Haiti_communes_edited_01132010.csv',
    'Sections': 'Haiti_Sections_Final_WGS84.csv'
}

NAME_MAP = {
    'Departments': 'DEPARTEMEN',
    'Communes': 'COMMUNE',
    'Sections': 'NOM_SECTIO'
}

PREFIXES = {
    'Country': 'L0',
    'Departments': 'L1',
    'Communes': 'L2',
    'Sections': 'L3'
}

GEOM_TYPES = {
    "Point": 1,
    "MultiPoint": 1,
    "LineString": 2,
    "MultiLineString": 2,
    "Polygon": 3,
    "MultiPolygon": 3,
}

# CSV READER

csv.field_size_limit(2**20 * 10)  # 10 megs

# from http://docs.python.org/library/csv.html#csv-examples 
def latin_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    for row in csv.reader(unicode_csv_data):
        yield [unicode(cell, 'latin-1') for cell in row]

def latin_dict_reader(data, dialect=csv.excel, **kwargs):
    reader = latin_csv_reader(data, dialect=dialect, **kwargs)
    headers = reader.next()
    for r in reader:
        yield dict(zip(headers, r))

# TEST 
def test():
    maxlen = 0
    from pprint import pprint
    names = {}
    for f in FILES:
        for d in latin_dict_reader(open(BASEDIR + '/' + FILES[f])):
            wkt = d.pop('WKT')
            names.setdefault(d[NAME_MAP[f]], []).append(d)
            maxlen = max(maxlen,len(wkt))
            #wkt_loads(wkt)
            pprint(d)
    for n, nn in names.items():
        if len(nn) > 1:
            for a in nn:
                print n, ": ", ','.join([a.get("DEPARTEMEN",''), a.get("COMMUNE",''), a.get("NOM_SECTIO",'')])
    
    #print "longest wkt was %d bytes" % maxlen

# LOCATION LOADING

def load_gis_locations(data, make_feature_group=False):
    """Loads locations from a list of dictionaries which must have, 
        at minimum 'name' and either 'wkt' or 'lat' and 'lon'.
        Also accepts:
            'parent'
            'feature_class_id'
        If make_feature_group is True, 
        a feature_group with the same name will be created.
        This function changes the dictionaries passed to it.
    """
    for i, d in enumerate(data):
        wkt = d.get('wkt')
        if not wkt:
            assert d.get('lon') is not None and d.get('lat') is not None, "Need either wkt or lat/lon"
            wkt = "POINT(%f %f)" % (d['lon'], d['lat'])
        else:
            shape = wkt_loads(wkt)
            if shape.type.lower() == "point":
                d['lon'] = shape.x
                d['lat'] = shape.y
            else:
                centroid = shape.centroid
                d['lon'] = centroid.x
                d['lat'] = centroid.y
        
        location_id = db.gis_location.insert(**d)
        if make_feature_group:
            db.gis_feature_group.insert(name=d['name'], enabled=False)
        print i, d['name']
    db.commit()

# HAITI-SPECIFIC

def ensure_admin_feature_class():
    admin_area_class = db(db.gis_feature_class.name==ADMIN_FEATURE_CLASS_NAME).select().first()
    if admin_area_class:
        return admin_area_class.id
    else:
        return db.gis_feature_class.insert(name=ADMIN_FEATURE_CLASS_NAME)

def make_name(name, admin_type):
    return ': '.join([PREFIXES[admin_type], name.title()])
    
def get_name(d, admin_type):
    return make_name(d[NAME_MAP[admin_type]], admin_type)

def get_parent_id(d, parent_type):
    parent_name = d[NAME_MAP[parent_type]]
    parent_db_name = make_name(parent_name, parent_type)
    parent_count = db(db.gis_location.name==parent_db_name).count()
    assert parent_count == 1, "%d parents found" % parent_count
    return db(db.gis_location.name==parent_db_name).select().first().id

def make_unique_sections(data):
    """Some Haiti Sections have duplicate names, but are in different Communes.
    If that is the case, postpend the Commune name to the Section name."""
    names = {}
    for d in data:
        if 'NOM_SECTIO' in d:  # only looking at sections
            names.setdefault(d['NOM_SECTIO'],[]).append(d)
    for name, ds in names.items():
        if len(ds) > 1:
            for d in ds:
                old = d['NOM_SECTIO']
                new = "%s [%s]" % (old, d['COMMUNE'])
                d['NOM_SECTIO'] = new
                print old, "=>", new

def load_level(admin_type, parent_type=None):
    """Load an administrative level.  Transforms dictionaries from csv, resolves naming conflicts for sections, and calls load_gis_locations to load into database."""
    filename = '/'.join([BASEDIR, FILES[admin_type]])
    
    admin_area_class_id = db(db.gis_feature_class.name==ADMIN_FEATURE_CLASS_NAME).select().first().id
        
    data = list(latin_dict_reader(open(filename)))

    if admin_type == 'Sections':
        make_unique_sections(data)

    def transformed_dict_gen():
        for d in data:
            transformed = {
                'name': get_name(d, admin_type),
                'wkt': d['WKT'],
                'feature_class_id': admin_area_class_id
            }
            if parent_type:
                transformed['parent'] = get_parent_id(d, parent_type)
            yield transformed
            
    load_gis_locations(transformed_dict_gen(), make_feature_group=True)

def create_haiti_admin_areas():
    ensure_admin_feature_class()
    load_level("Departments")
    load_level("Communes", parent_type="Departments")
    load_level("Sections", parent_type="Communes")
   

