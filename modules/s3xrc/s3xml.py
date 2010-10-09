# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - XML/JSON toolkit

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
    @contact: dominic AT nursix DOT org
    @copyright: 2009-2010 (c) Sahana Software Foundation
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

__all__ = ["S3XML"]

from gluon.storage import Storage
import gluon.contrib.simplejson as json

try:
    from xml.etree.cElementTree import ElementTree
except ImportError:
    from xml.etree.ElementTree import ElementTree

from lxml import etree


# *****************************************************************************
class S3XML(object):

    """ XML+JSON toolkit for S3XRC """

    S3XRC_NAMESPACE = "http://eden.sahanafoundation.org/wiki/S3XRC"
    S3XRC = "{%s}" % S3XRC_NAMESPACE #: LXML namespace prefix
    NSMAP = {None: S3XRC_NAMESPACE} #: LXML default namespace

    namespace = "sahana"

    CACHE_TTL = 5 # time-to-live of RAM cache for field representations

    UID = "uuid"
    MCI = "mci"
    MTIME = "modified_on"

    # GIS field names
    Lat = "lat"
    Lon = "lon"
    FeatureClass = "feature_class_id"
    #Marker = "marker_id"

    IGNORE_FIELDS = ["deleted", "id"]

    FIELDS_TO_ATTRIBUTES = [
            "id",
            "created_on",
            "modified_on",
            "created_by",
            "modified_by",
            "uuid",
            "mci",
            "admin"]

    ATTRIBUTES_TO_FIELDS = ["admin", "mci"]

    TAG = Storage(
        root="s3xrc",
        resource="resource",
        reference="reference",
        data="data",
        list="list",
        item="item",
        object="object",
        select="select",
        field="field",
        option="option",
        options="options",
        fields="fields"
    )

    ATTRIBUTE = Storage(
        id="id",
        name="name",
        table="table",
        field="field",
        value="value",
        resource="resource",
        ref="ref",
        domain="domain",
        url="url",
        filename="filename",
        error="error",
        start="start",
        limit="limit",
        success="success",
        results="results",
        lat="lat",
        latmin="latmin",
        latmax="latmax",
        lon="lon",
        lonmin="lonmin",
        lonmax="lonmax",
        marker="marker",
        sym="sym",
        type="type",
        readable="readable",
        writable="writable",
        has_options="has_options"
    )

    ACTION = Storage(
        create="create",
        read="read",
        update="update",
        delete="delete"
    )

    PREFIX = Storage(
        resource="$",
        options="$o",
        reference="$k",
        attribute="@",
        text="$"
    )

    PY2XML = [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
              ('"', "&quot;"), ("'", "&apos;")]

    XML2PY = [("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"),
              ("'", "&apos;"), ("&", "&amp;")]


    # -------------------------------------------------------------------------
    def __init__(self, db, domain=None, base_url=None, gis=None, cache=None):

        """ Constructor

            @param db: the database (DAL)
            @param domain: name of the current domain
            @param base_url: base URL of the current instance
            @param gis: GIS toolkit to use
            @param cache: the cache

            @todo 2.2: pass resource controller?
            
        """

        self.db = db
        self.error = None
        self.domain = domain
        self.base_url = base_url
        self.domain_mapping = True
        self.gis = gis
        self.cache = cache

        self.filter_mci = False # Set to true to suppress export at MCI<0


    # XML+XSLT tools ==========================================================

    def parse(self, source):

        """ Parse an XML source into an element tree

            @param source: the XML source,
                can be a file-like object, a filename or a URL

        """

        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            e = sys.exc_info()[1]
            self.error = e
            return None


    # -------------------------------------------------------------------------
    def transform(self, tree, template_path, **args):

        """ Transform an element tree with XSLT

            @param tree: the element tree
            @param template_path: pathname of the XSLT stylesheet
            @param args: dict of arguments to pass to the stylesheet

        """

        self.error = None

        if args:
            _args = [(k, "'%s'" % args[k]) for k in args]
            _args = dict(_args)
        else:
            _args = None
        ac = etree.XSLTAccessControl(read_file=True, read_network=True)
        template = self.parse(template_path)

        if template:
            try:
                transformer = etree.XSLT(template, access_control=ac)
                if _args:
                    result = transformer(tree, **_args)
                else:
                    result = transformer(tree)
                return result
            except:
                e = sys.exc_info()[1]
                self.error = e
                return None
        else:
            # Error parsing the XSL template
            return None


    # -------------------------------------------------------------------------
    def tostring(self, tree, pretty_print=False):

        """ Convert an element tree into XML as string

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output

        """

        return etree.tostring(tree,
                              xml_declaration=True,
                              encoding="utf-8",
                              pretty_print=pretty_print)


    # -------------------------------------------------------------------------
    def tree(self, resources,
             domain=None,
             url=None,
             start=None,
             limit=None,
             results=None):

        """ Builds a tree from a list of elements

            @param resources: list of <resource> elements
            @param domain: name of the current domain
            @param url: url of the request
            @param start: the start record (in server-side pagination)
            @param limit: the page size (in server-side pagination)
            @param results: number of total available results

        """

        # For now we do not nsmap, because the default namespace cannot be
        # matched in XSLT templates (need explicit prefix) and thus this
        # would require a rework of all existing templates (which is
        # however useful)
        root = etree.Element(self.TAG.root) #, nsmap=self.NSMAP)

        root.set(self.ATTRIBUTE.success, str(False))

        if resources is not None:
            if resources:
                root.set(self.ATTRIBUTE.success, str(True))
            if start is not None:
                root.set(self.ATTRIBUTE.start, str(start))
            if limit is not None:
                root.set(self.ATTRIBUTE.limit, str(limit))
            if results is not None:
                root.set(self.ATTRIBUTE.results, str(results))
            root.extend(resources)

        if domain:
            root.set(self.ATTRIBUTE.domain, self.domain)

        if url:
            root.set(self.ATTRIBUTE.url, self.base_url)

        root.set(self.ATTRIBUTE.latmin,
                 str(self.gis.get_bounds()["min_lat"]))
        root.set(self.ATTRIBUTE.latmax,
                 str(self.gis.get_bounds()["max_lat"]))
        root.set(self.ATTRIBUTE.lonmin,
                 str(self.gis.get_bounds()["min_lon"]))
        root.set(self.ATTRIBUTE.lonmax,
                 str(self.gis.get_bounds()["max_lon"]))

        return etree.ElementTree(root)


    # -------------------------------------------------------------------------
    def xml_encode(self, obj):

        """ Encodes a Python string into an XML text node

            @param obj: string to encode

        """

        if obj:
            for (x,y) in self.PY2XML:
                obj = obj.replace(x, y)
        return obj


    # -------------------------------------------------------------------------
    def xml_decode(self, obj):

        """ Decodes an XML text node into a Python string

            @param obj: string to decode

        """

        if obj:
            for (x,y) in self.XML2PY:
                obj = obj.replace(y, x)
        return obj


    # -------------------------------------------------------------------------
    def export_uid(self, uid):

        """ Exports UIDs with domain prefix

            @param uid: the UID

        """

        if not uid:
            return uid

        if uid.startswith("urn:"):
            return uid
        else:
            x = uid.find("/")
            if (x < 1 or x == len(uid)-1) and self.domain:
                return "%s/%s" % (self.domain, uid)
            else:
                return uid


    # -------------------------------------------------------------------------
    def import_uid(self, uid):

        """ Imports UIDs with domain prefixes

            @param uid: the UID

        """

        if not uid or not self.domain:
            return uid

        if uid.startswith("urn:"):
            return uid
        else:
            x = uid.find("/")
            if x < 1 or x == len(uid)-1:
                return uid
            else:
                (_domain, _uid) = uid.split("/", 1)
                if _domain == self.domain:
                    return _uid
                else:
                    return uid


    # Data export =============================================================

    def represent(self, table, f, v):

        """ Get the representation of a field value

            @param table: the database table
            @param f: the field name
            @param v: the value

            @todo 2.2: use S3ResourceManager.represent()

        """

        text = str(table[f].represent(v)).decode("utf-8")
        # Filter out markup from text
        if "<" in text:
            try:
                markup = etree.XML(text)
                text = markup.xpath(".//text()")
                if text:
                    text = " ".join(text)
                else:
                    text = ""
            except etree.XMLSyntaxError:
                pass
        text = self.xml_encode(text)
        return text


    # -------------------------------------------------------------------------
    def rmap(self, table, record, fields):

        """ Generates a reference map for a record

            @param table: the database table
            @param record: the record
            @param fields: list of reference field names in this table

        """

        reference_map = []

        for f in fields:

            ids = record.get(f, None)
            if not ids:
                continue
            if not isinstance(ids, (list, tuple)):
                ids = [ids]

            multiple = False
            fieldtype = str(table[f].type)
            if fieldtype.startswith("reference"):
                ktablename = fieldtype[10:]
            elif fieldtype.startswith("list:reference"):
                ktablename = fieldtype[15:]
                multiple = True
            else:
                continue

            ktable = self.db[ktablename]
            if "id" not in ktable.fields:
                continue

            uid = None
            uids = None
            if self.UID in ktable.fields:
                query = (ktable.id.belongs(ids))
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                if self.filter_mci and "mci" in ktable:
                    query = (ktable.mci >= 0) & query
                krecords = self.db(query).select(ktable[self.UID])
                if krecords:
                    uids = [r[self.UID] for r in krecords if r[self.UID]]
                    if self.domain_mapping:
                        uids = [self.export_uid(u) for u in uids]
                else:
                    continue
            else:
                query = (ktable.id.belongs(ids))
                if "deleted" in ktable:
                    query = (ktable.deleted == False) & query
                if self.filter_mci and "mci" in ktable:
                    query = (ktable.mci >= 0) & query
                if not self.db(query).count():
                    continue

            value = record[f]
            value = text = self.xml_encode(str(
                           table[f].formatter(value)).decode("utf-8"))
            if table[f].represent:
                text = self.represent(table, f, record[f])

            reference_map.append(Storage(field=f,
                                         table=ktablename,
                                         multiple=multiple,
                                         id=ids,
                                         uid=uids,
                                         text=text,
                                         value=value))

        return reference_map


    # -------------------------------------------------------------------------
    def add_references(self, element, rmap, show_ids=False):

        """ Adds <reference> elements to a <resource>

            @param element: the <resource> element
            @param rmap: the reference map for the corresponding record
            @param show_ids: insert the record ID as attribute in references

        """

        for i in xrange(0, len(rmap)):
            r = rmap[i]
            reference = etree.SubElement(element, self.TAG.reference)
            reference.set(self.ATTRIBUTE.field, r.field)
            reference.set(self.ATTRIBUTE.resource, r.table)
            if show_ids:
                if r.multiple:
                    ids = "|%s|" % "|".join(map(str, r.id))
                else:
                    ids = "%s" % r.id[0]
                reference.set(self.ATTRIBUTE.id, self.xml_encode(ids))
            if r.uid:
                if r.multiple:
                    uids = "|%s|" % "|".join(map(str, r.uid))
                else:
                    uids = "%s" % r.uid[0]
                reference.set(self.UID, self.xml_encode(str(uids).decode("utf-8")))
                reference.text = r.text
            else:
                reference.set(self.ATTRIBUTE.value, r.value)
                # TODO: add in-line resource
            r.element = reference


    # -------------------------------------------------------------------------
    def gis_encode(self, rmap, download_url="", marker=None):

        """ GIS-encodes location references

            @param rmap: list of references to encode
            @param download_url: download URL of this instance
            @param marker: filename to override filenames in marker URLs

        """

        if not self.gis:
            return

        db = self.db

        references = filter(lambda r:
                            r.element is not None and \
                            self.Lat in self.db[r.table].fields and \
                            self.Lon in self.db[r.table].fields,
                            rmap)

        for i in xrange(0, len(references)):
            r = references[i]
            if len(r.id) == 1:
                r_id = r.id[0]
            else:
                continue # Multi-reference
            ktable = db[r.table]
            LatLon = db(ktable.id == r_id).select(ktable[self.Lat],
                                                  ktable[self.Lon],
                                                  #ktable[self.FeatureClass],
                                                  limitby=(0, 1))
            if LatLon:
                LatLon = LatLon.first()
                if LatLon[self.Lat] is not None and \
                   LatLon[self.Lon] is not None:
                    r.element.set(self.ATTRIBUTE.lat,
                                  self.xml_encode("%.6f" % LatLon[self.Lat]))
                    r.element.set(self.ATTRIBUTE.lon,
                                  self.xml_encode("%.6f" % LatLon[self.Lon]))
                    # Lookup Marker (Icon)
                    if marker:
                        marker_url = "%s/gis_marker.image.%s.png" % \
                                     (download_url, marker)
                    else:
                        marker = self.gis.get_marker(r.value)
                        marker_url = "%s/%s" % (download_url, marker.image)
                    r.element.set(self.ATTRIBUTE.marker,
                                  self.xml_encode(marker_url))
                    # Lookup GPS Marker
                    # @ToDo Fix for new FeatureClass
                    symbol = None
                    #if LatLon[self.FeatureClass]:
                    #    fctbl = db.gis_feature_class
                    #    query = (fctbl.id == str(LatLon[self.FeatureClass]))
                    #    try:
                    #        symbol = db(query).select(fctbl.gps_marker,
                    #                    limitby=(0, 1)).first().gps_marker
                    #    except:
                    #        pass
                    if not symbol:
                        symbol = "White Dot"
                    r.element.set(self.ATTRIBUTE.sym,
                                  self.xml_encode(symbol))


    # -------------------------------------------------------------------------
    def element(self, table, record,
                fields=[],
                url=None,
                download_url=None,
                marker=None):

        """ Creates an element from a Storage() record

            @param table: the database table
            @param record: the record
            @param fields: list of field names to include
            @param url: URL of the record
            @param download_url: download URL of the current instance
            @param marker: filename of the marker to override
                marker URLs in location references

        """

        if not download_url:
            download_url = ""

        resource = etree.Element(self.TAG.resource)
        resource.set(self.ATTRIBUTE.name, table._tablename)

        if self.UID in table.fields and self.UID in record:
            _value = str(table[self.UID].formatter(record[self.UID])).decode("utf-8")
            if self.domain_mapping:
                value = self.export_uid(_value)
            resource.set(self.UID, self.xml_encode(value))
            if table._tablename == "gis_location" and self.gis:
                # Look up the marker to display
                marker = self.gis.get_marker(_value)
                marker_url = "%s/%s" % (download_url, marker.image)
                resource.set(self.ATTRIBUTE.marker,
                                self.xml_encode(marker_url))
                # Look up the GPS Marker
                symbol = None
                try:
                    db = self.db
                    query = (db.gis_feature_class.id == record.feature_class_id)
                    symbol = db(query).select(limitby=(0, 1)).first().gps_marker
                except:
                    # No Feature Class
                    pass
                if not symbol:
                    symbol = "White Dot"
                resource.set(self.ATTRIBUTE.sym, self.xml_encode(symbol))

        for i in xrange(0, len(fields)):
            f = fields[i]
            v = record.get(f, None)
            if f == self.MCI and v is None:
                v = 0
            if f not in table.fields or v is None:
                continue

            fieldtype = str(table[f].type)

            if fieldtype.startswith("list:") and \
               isinstance(v, (list, tuple)):
                text = value = self.xml_encode("|%s|" % "|".join(map(str, v)))
            else:
                text = value = self.xml_encode(
                               str(table[f].formatter(v)).decode("utf-8"))

            if table[f].represent:
                text = self.represent(table, f, v)

            if f in self.FIELDS_TO_ATTRIBUTES:
                if f == self.MCI:
                    resource.set(self.MCI, str(int(v) + 1))
                else:
                    resource.set(f, text)

            elif fieldtype == "upload":
                data = etree.SubElement(resource, self.TAG.data)
                data.set(self.ATTRIBUTE.field, f)
                fileurl = self.xml_encode("%s/%s" % (download_url, value))
                filename = self.xml_encode(value)
                data.set(self.ATTRIBUTE.url, fileurl)
                data.set(self.ATTRIBUTE.filename, filename)

            elif fieldtype == "password":
                # Do not export password fields
                continue

            elif fieldtype == "blob":
                # Not implemented yet
                continue

            else:
                data = etree.SubElement(resource, self.TAG.data)
                data.set(self.ATTRIBUTE.field, f)
                if table[f].represent:
                    data.set(self.ATTRIBUTE.value, value)
                data.text = text

        if url:
            resource.set(self.ATTRIBUTE.url, url)

        return resource


    # Data import =============================================================

    def select_resources(self, tree, tablename):

        """ Selects resources from an element tree

            @param tree: the element tree
            @param tablename: table name to search for

        """

        resources = []

        if isinstance(tree, etree._ElementTree):
            root = tree.getroot()
            if not root.tag == self.TAG.root:
                return resources
        else:
            root = tree

        if root is None or not len(root):
            return resources

        expr = './%s[@%s="%s"]' % (
               self.TAG.resource,
               self.ATTRIBUTE.name,
               tablename)

        resources = root.xpath(expr)
        return resources


    # -------------------------------------------------------------------------
    def lookahead(self, table, element, fields, tree=None, directory=None):

        """ Resolves references in XML resources

            @param table: the database table
            @param element: the element to resolve
            @param fields: fields to check for references
            @param tree: the element tree of the input source
            @param directory: the resource directory of the input tree

        """

        reference_list = []
        references = element.findall("reference")

        for r in references:

            field = r.get(self.ATTRIBUTE.field, None)
            if not field or field not in fields:
                continue

            multiple = False
            fieldtype = str(table[field].type)
            if fieldtype.startswith("reference"):
                ktablename = fieldtype[10:]
            elif fieldtype.startswith("list:reference"):
                ktablename = fieldtype[15:]
                multiple = True
            else:
                continue

            resource = r.get(self.ATTRIBUTE.resource, None)
            if not resource or resource != ktablename:
                continue
            ktable = self.db.get(resource, None)
            if not ktable or "id" not in ktable.fields:
                continue

            uids = r.get(self.UID, None)
            if uids and multiple:
                uids = uids.strip("|").split("|")
            elif uids:
                uids = [uids]

            relements = []

            if not uids:
                expr = './/%s[@%s="%s"]' % (
                    self.TAG.resource,
                    self.ATTRIBUTE.name, resource)
                relements = r.xpath(expr)
                if relements and not multiple:
                    relements = [relements[0]]

            elif tree and self.UID in ktable:
                root = tree.getroot()

                for uid in uids:
                    entry = None
                    if directory is not None and resource in directory:
                        entry = directory[resource].get(uid, None)
                    if not entry:
                        expr = './/%s[@%s="%s" and @%s="%s"]' % (
                                self.TAG.resource,
                                self.ATTRIBUTE.name, resource,
                                self.UID, uid)
                        e = root.xpath(expr)
                        if e:
                            relements.append(e[0])

                    else:
                        reference_list.append(Storage(field=field, entry=entry))

                _uids = uids
                if self.domain_mapping:
                    _uids = map(self.import_uid, uids)
                records = self.db(ktable[self.UID].belongs(_uids)).select(ktable.id, ktable[self.UID])
                id_map = dict()
                map(lambda r: id_map.update({r[self.UID]:r.id}), records)

            for relement in relements:

                uid = _uid = relement.get(self.UID, None)
                if self.domain_mapping:
                    _uid = self.import_uid(uid)
                id = _uid and id_map and id_map.get(_uid, None) or None

                entry = dict(vector=None,
                             resource=resource,
                             element=relement,
                             uid=uid,
                             id=id)

                if uid and directory is not None:
                    if resource not in directory:
                        directory[resource] = {}
                    if _uid not in directory[resource]:
                        directory[resource][uid] = entry

                reference_list.append(Storage(field=field, entry=entry))

        return reference_list


    # -------------------------------------------------------------------------
    def record(self, table, element, original=None, files=[], validate=None, skip=[]):

        """ Creates a Storage() record from an element and validates it

            @param table: the database table
            @param element: the element
            @param validate: validate hook (function to validate fields)
            @param skip: fields to skip

        """

        valid = True
        record = Storage()

        if self.UID in table.fields and self.UID not in skip:
            uid = element.get(self.UID, None)
            if uid:
                if self.domain_mapping:
                    uid = self.import_uid(uid)
                record[self.UID] = uid

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            if f in table.fields:
                v = value = self.xml_decode(element.get(f, None))
                if value is not None:
                    if validate is not None:
                        if not isinstance(value, (str, unicode)):
                            v = str(value)
                        (value, error) = validate(table, original, f, v)
                        if error:
                            element.set(self.ATTRIBUTE.error,
                                        "%s: %s" % (f, error))
                            valid = False
                            continue
                    record[f]=value

        for child in element:
            if child.tag == self.TAG.data:
                f = child.get(self.ATTRIBUTE.field, None)
                if not f or f not in table.fields:
                    continue
                if f in self.IGNORE_FIELDS or f in skip:
                    continue

                field_type = str(table[f].type)
                if field_type in ("id", "blob", "password"):
                    continue
                elif field_type == "upload":
                    # Handling of uploads
                    download_url = child.get(self.ATTRIBUTE.url, None)
                    filename = child.get(self.ATTRIBUTE.filename, None)
                    file = None
                    if filename:
                        if filename in files:
                            file = files[filename]
                        elif download_url:
                            # Try to download the file
                            import urllib
                            try:
                                file = urllib.urlopen(download_url)
                            except IOError:
                                pass
                        if file:
                            field = table[f]
                            value = field.store(file, filename)
                        else:
                            continue
                    elif filename is not None:
                        value = ""
                else:
                    value = child.get(self.ATTRIBUTE.value, None)
                    value = self.xml_decode(value)

                if field_type == "boolean":
                    if value and value in ["True", "true"]:
                        value = True
                    else:
                        value = False

                if value is None:
                    value = self.xml_decode(child.text)
                if value == "" and not field_type == "string":
                    value = None
                if value is None:
                    value = table[f].default
                if value is None and field_type == "string":
                    value = ""

                if value is not None:
                    if field_type.startswith("list:"):
                        value = value.strip("|").split("|")
                    if validate is not None:
                        if not isinstance(value, (basestring, list, tuple)):
                            v = str(value)
                        else:
                            v = value
                        (value, error) = validate(table, original, f, v)
                        if isinstance(v, (list, tuple)):
                            child.set(self.ATTRIBUTE.value, str(v))
                        else:
                            child.set(self.ATTRIBUTE.value, v)
                        if error:
                            child.set(self.ATTRIBUTE.error, "%s: %s" % (f, error))
                            valid = False
                            continue
                    record[f] = value

        if valid:
            return record
        else:
            return None


    # Data model helpers ======================================================

    def get_field_options(self, table, fieldname):

        """ Get options of a field as <select>

            @todo 2.2: fix docstring
            
        """

        select = etree.Element(self.TAG.select)

        if fieldname in table.fields:
            field = table[fieldname]
        else:
            return select

        requires = field.requires
        select.set(self.ATTRIBUTE.id, "%s_%s" % (table._tablename, fieldname))
        select.set(self.ATTRIBUTE.name, fieldname)

        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            r = requires[0]
            options = []
            if isinstance(r, IS_EMPTY_OR):
                r = r.other
            try:
                options = r.options()
            except:
                pass
            for (value, text) in options:
                value = self.xml_encode(str(value).decode("utf-8"))
                text = self.xml_encode(str(text).decode("utf-8"))
                option = etree.SubElement(select, self.TAG.option)
                option.set(self.ATTRIBUTE.value, value)
                option.text = text

        return select


    # -------------------------------------------------------------------------
    def get_options(self, prefix, name, fields=None):

        """ Get options of option fields in a table as <select>s

            @todo 2.2: fix docstring
            
        """

        db = self.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        options = etree.Element(self.TAG.options)

        if fields:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]
            if len(fields) == 1:
                return(self.get_field_options(table, fields[0]))

        if table:
            options.set(self.ATTRIBUTE.resource, tablename)
            for f in table.fields:
                if fields and f not in fields:
                    continue
                select = self.get_field_options(table, f)
                if select is not None and len(select):
                    options.append(select)

        return options


    # -------------------------------------------------------------------------
    def get_fields(self, prefix, name):

        """ Get fields in a table as <fields> element

            @todo 2.2: fix docstring
            
        """

        db = self.db
        tablename = "%s_%s" % (prefix, name)
        table = db.get(tablename, None)

        fields = etree.Element(self.TAG.fields)

        if table:
            fields.set(self.ATTRIBUTE.resource, tablename)
            for f in table.fields:
                field = etree.Element(self.TAG.field)
                field.set(self.ATTRIBUTE.name, self.xml_encode(f))
                ftype = str(table[f].type)
                field.set(self.ATTRIBUTE.type, self.xml_encode(ftype))
                readable = table[f].readable
                writable = table[f].writable
                field.set(self.ATTRIBUTE.readable, str(readable))
                field.set(self.ATTRIBUTE.writable, str(writable))
                options = self.get_field_options(table, f)
                field.set(self.ATTRIBUTE.has_options,
                          str(len(options) and True or False))
                fields.append(field)

        return fields


    # JSON toolkit ============================================================

    def __json2element(self, key, value, native=False):

        """ Converts a data field from JSON into an element

            @param key: key (field name)
            @param value: value for the field
            @param native: use native mode
            @type native: bool

        """

        if isinstance(value, dict):
            return self.__obj2element(key, value, native=native)

        elif isinstance(value, (list, tuple)):
            if not key == self.TAG.item:
                _list = etree.Element(key)
            else:
                _list = etree.Element(self.TAG.list)
            for obj in value:
                item = self.__json2element(self.TAG.item, obj,
                                           native=native)
                _list.append(item)
            return _list

        else:
            if native:
                element = etree.Element(self.TAG.data)
                element.set(self.ATTRIBUTE.field, key)
            else:
                element = etree.Element(key)
            if not isinstance(value, (str, unicode)):
                value = str(value)
            element.text = self.xml_encode(value)
            return element


    # -------------------------------------------------------------------------
    def __obj2element(self, tag, obj, native=False):

        """ Converts a JSON object into an element

            @param tag: tag name for the element
            @param obj: the JSON object
            @param native: use native mode for attributes

        """

        prefix = name = resource = field = None

        if not tag:
            tag = self.TAG.object

        elif native:
            if tag.startswith(self.PREFIX.reference):
                field = tag[len(self.PREFIX.reference) + 1:]
                tag = self.TAG.reference
            elif tag.startswith(self.PREFIX.options):
                resource = tag[len(self.PREFIX.options) + 1:]
                tag = self.TAG.options
            elif tag.startswith(self.PREFIX.resource):
                resource = tag[len(self.PREFIX.resource) + 1:]
                tag = self.TAG.resource
            elif not tag == self.TAG.root:
                field = tag
                tag = self.TAG.data

        element = etree.Element(tag)

        if native:
            if resource:
                if tag == self.TAG.resource:
                    element.set(self.ATTRIBUTE.name, resource)
                else:
                    element.set(self.ATTRIBUTE.resource, resource)
            if field:
                element.set(self.ATTRIBUTE.field, field)

        for k in obj:
            m = obj[k]
            if isinstance(m, dict):
                child = self.__obj2element(k, m, native=native)
                element.append(child)
            elif isinstance(m, (list, tuple)):
                #l = etree.SubElement(element, k)
                for _obj in m:
                    child = self.__json2element(k, _obj, native=native)
                    element.append(child)
            else:
                if k == self.PREFIX.text:
                    element.text = self.xml_encode(m)
                elif k.startswith(self.PREFIX.attribute):
                    a = k[len(self.PREFIX.attribute):]
                    element.set(a, self.xml_encode(m))
                else:
                    child = self.__json2element(k, m, native=native)
                    element.append(child)

        return element


    # -------------------------------------------------------------------------
    def json2tree(self, source, format=None):

        """ Converts JSON into an element tree

            @param source: the JSON source
            @param format: name of the XML root element

        """

        try:
            root_dict = json.load(source)
        except (ValueError,):
            e = sys.exc_info()[1]
            raise HTTP(400, body=self.json_message(False, 400, e))

        native=False

        if not format:
            format=self.TAG.root
            native=True

        if root_dict and isinstance(root_dict, dict):
            root = self.__obj2element(format, root_dict, native=native)
            if root:
                return etree.ElementTree(root)

        return None


    # -------------------------------------------------------------------------
    def __element2json(self, element, native=False):

        """ Converts an element into JSON

            @param element: the element
            @param native: use native mode for attributes

        """

        if element.tag == self.TAG.list:
            obj = []
            for child in element:
                tag = child.tag
                if tag[0] == "{":
                    tag = tag.rsplit("}",1)[1]
                child_obj = self.__element2json(child, native=native)
                if child_obj:
                    obj.append(child_obj)
            return obj
        else:
            obj = {}
            for child in element:
                tag = child.tag
                if tag[0] == "{":
                    tag = tag.rsplit("}",1)[1]
                collapse = True
                if native:
                    if tag == self.TAG.resource:
                        resource = child.get(self.ATTRIBUTE.name)
                        tag = "%s_%s" % (self.PREFIX.resource, resource)
                        collapse = False
                    elif tag == self.TAG.options:
                        resource = child.get(self.ATTRIBUTE.resource)
                        tag = "%s_%s" % (self.PREFIX.options, resource)
                    elif tag == self.TAG.reference:
                        tag = "%s_%s" % (self.PREFIX.reference,
                                         child.get(self.ATTRIBUTE.field))
                    elif tag == self.TAG.data:
                        tag = child.get(self.ATTRIBUTE.field)
                child_obj = self.__element2json(child, native=native)
                if child_obj:
                    if not tag in obj:
                        if isinstance(child_obj, list) or not collapse:
                            obj[tag] = [child_obj]
                        else:
                            obj[tag] = child_obj
                    else:
                        if not isinstance(obj[tag], list):
                            obj[tag] = [obj[tag]]
                        obj[tag].append(child_obj)

            attributes = element.attrib
            for a in attributes:
                if native:
                    if a == self.ATTRIBUTE.name and \
                       element.tag == self.TAG.resource:
                        continue
                    if a == self.ATTRIBUTE.resource and \
                       element.tag == self.TAG.options:
                        continue
                    if a == self.ATTRIBUTE.field and \
                    element.tag in (self.TAG.data, self.TAG.reference):
                        continue
                obj[self.PREFIX.attribute + a] = \
                    self.xml_decode(attributes[a])

            if element.text:
                obj[self.PREFIX.text] = self.xml_decode(element.text)

            if len(obj) == 1 and obj.keys()[0] in \
               (self.PREFIX.text, self.TAG.item, self.TAG.list):
                obj = obj[obj.keys()[0]]

            return obj


    # -------------------------------------------------------------------------
    def tree2json(self, tree, pretty_print=False):

        """ Converts an element tree into JSON

            @param tree: the element tree
            @param pretty_print: provide pretty formatted output

        """

        root = tree.getroot()

        if root.tag == self.TAG.root:
            native = True
        else:
            native = False

        root_dict = self.__element2json(root, native=native)

        if pretty_print:
            js = json.dumps(root_dict, indent=4)
            return "\n".join([l.rstrip() for l in js.splitlines()])
        else:
            return json.dumps(root_dict)


    # -------------------------------------------------------------------------
    def json_message(self,
                     success=True,
                     status_code="200",
                     message=None,
                     tree=None):

        """ Provide a nicely-formatted JSON Message

            @param success: action succeeded or failed
            @param status_code: the HTTP status code
            @param message: the message text
            @param tree: result tree to enclose

            @todo 2.2: extend to report number of results/successful imports

        """

        if success:
            status='"status": "success"'
        else:
            status='"status": "failed"'

        code = '"statuscode": "%s"' % status_code

        output = "{%s, %s" % (status, code)

        if message:
            output = '%s, "message": "%s"' % (output, message)

        if not success and tree:
            output = '%s, "tree": "%s"' % (output, tree)

        return "%s}" % output


# *****************************************************************************
