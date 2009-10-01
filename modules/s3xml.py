# -*- coding: utf-8 -*-

"""
    SahanaPy XML Interface

    Copyright (c) 2009 Dominic König (nursix.org)

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

from gluon.storage import Storage, Messages
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *
from gluon.contrib.markdown import WIKI
try:
    from gluon.contrib.gql import SQLTable, SQLStorage
except ImportError:
    from gluon.sql import SQLTable, SQLStorage
import traceback

from gluon.html import *
import uuid

#******************************************************************************
# Errors
#
S3XML_BAD_RESOURCE = "Invalid Resource"
S3XML_PARSE_ERROR = "XML Parse Error"
S3XML_TRANFORMATION_ERROR = "XSL Transformation Error"
S3XML_NO_XSLT = "XSL Transformation not available"
S3XML_BAD_SOURCE = "Invalid XML Source"
S3XML_BAD_RECORD = "Invalid Record ID"
S3XML_NO_MATCH = "No Matching Element"
S3XML_VALIDATION_ERROR = "Validation Error"
S3XML_DATA_IMPORT_ERROR = "Data Import Error"

#******************************************************************************
# lxml
#
try:
    from lxml import etree
    NO_XSL=False
except ImportError:
    NO_XSL=True
    try:
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                import cElementTree as etree
            except ImportError:
                # normal ElementTree install
                import elementtree.ElementTree as etree

# *****************************************************************************
# XMLImport
#
class XMLImport(object):
    """
        Helper class for S3XML to handle XML imports
    """

    def __init__(self,
        db=None,
        prefix=None,
        name=None,
        id=None,
        record=None,
        permit=None,
        onvalidation=None,
        onaccept=None):

        self.db=db
        self.prefix=prefix
        self.name=name
        self.id=id
        self.record=record

        self.method=None
        self.onvalidation=onvalidation
        self.onaccept=onaccept

        self.accepted=True
        self.permitted=True
        self.committed=False

        self.PERMISSION = dict(create="create", update="update")
        self._UUID = "uuid"

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        if not self.id:
            self.method = "create"
            permission = self.PERMISSION["create"]
            self.id = 0

            _uuid = self.record.get(self._UUID, None)
            if _uuid is not None:
                if self.db(self.table.uuid==_uuid).count():
                    del self.record[self._UUID]
                    self.method = "update"
                    permission = self.PERMISSION["update"]
                    self.id = self.db(self.table.uuid==_uuid).select(self.table.id)[0].id
        else:
            self.method = "update"
            permission = self.PERMISSION["update"]

            if self._UUID in record:
                del self.record[self._UUID]

            if not self.db(self.table.id==id).count():
                self.method = None
                self.id = 0

        if permit and not permit(permission, self.tablename, record_id=self.id):
            self.permitted=False

    # -------------------------------------------------------------------------
    def commit(self):
        """
            Commits the record to the database

            Returns: boolean
        """

        if self.committed:
            return True

        if self.accepted and self.permitted:

            form = Storage() # PseudoForm for callbacks
            form.method = self.method
            form.vars = self.record
            form.vars.id = self.id

            if self.onvalidation:
                self.onvalidation(form)

            try:
                if self.method == "update":
                    self.id = self.db(self.table.id==self.id).update(**dict(self.record))
                elif self.method == "create":
                    self.id = self.table.insert(**dict(self.record))
                    # Re-init the uuid default value, otherwise it gets re-used
                    # web2py does not execute lambdas as field defaults!
                    if self._UUID in self.table:
                        self.table[self._UUID].default=uuid.uuid4()
                self.committed=True
            except:
                self.id=0
                self.method=None
                self.accepted=False
                self.committed=False
                return False

            form.vars.id = self.id

            if self.onaccept:
                self.onaccept(form)

            return True
        else:
            return False

# *****************************************************************************
# S3XML
#
class S3XML(object):
    """
        Class to handle XML imports/exports
    """

    _UUID = "uuid"

    IGNORE_FIELDS = ["deleted", "id"]

    FIELDS_TO_ATTRIBUTES = [
            "created_on",
            "modified_on",
            "created_by",
            "modified_by",
            "uuid",
            "admin"]

    ATTRIBUTES_TO_FIELDS = [
            "admin"]

    TAG = dict(
        root="sahanapy",
        resource="resource",
        reference="reference",
        data="data"
        )

    ATTRIBUTE = dict(
        name="name",
        table="table",
        field="field",
        value="value",
        prefix="prefix",
        resource="resource"
        )

    PERMISSION = dict(
        read="read",
        create="create",
        update="update"
    )

    def __init__(self, db):
        self.db = db
        self.error = None

        self.imports = []
        self.exports = []

    # -------------------------------------------------------------------------
    def parse(self, source):
        """
            Deserialize an XML source into an ElementTree object

            returns: ElementTree
        """
        self.error = None

        try:
            parser = etree.XMLParser(no_network=False)
            result = etree.parse(source, parser)
            return result
        except:
            self.error = S3XML_PARSE_ERROR
            return None

    # -------------------------------------------------------------------------
    def transform(self, tree, template_path):
        """
            Transform an element tree using the given XSLT template

            returns: ElementTree
        """

        if not NO_XSL:
            template = self.parse(template_path)
            if template:
                try:
                    transformer = etree.XSLT(template)
                    result = transformer(tree)
                    return result
                except:
                    self.error = S3XML_TRANFORMATION_ERROR
                    return None
            else:
                # Error parsing the XSL template
                return None
        else:
            self.error = S3XML_NO_XSLT
            return None

    # -------------------------------------------------------------------------
    def tostring(self, tree):
        """
            Serialize an element tree as string object

            returns: str
        """
        return etree.tostring(tree, xml_declaration=True, encoding="utf-8", pretty_print=True)

    # -------------------------------------------------------------------------
    def element(self, prefix, name, record, skip=[]):
        """
            Builds an element from a record

            prefix:         the resource prefix
            name:           the resource name
            record:         the record (as dict of fields)
            skip:           list of fields to skip (optional)

            returns: Element

            Resource Routing:
            References will be mapped to UUID's and represented as <reference> elements. If
            the referenced table doesn't contain UUID's, the reference field will not be
            represented at all.
        """

        _table = "%s_%s" % (prefix, name)
        if _table in self.db:
            table = self.db[_table]
        else:
            self.error = S3XML_BAD_RESOURCE
            return None

        element = etree.Element(self.TAG["resource"])

        for f in table.fields:
            if f in self.IGNORE_FIELDS or f in skip:
                continue
            if f == self._UUID:
                if record[f] is None:
                    element.set(f, "")
                else:
                    value = table[f].formatter(record[f])
                    element.set(f, str(value))
            elif f in self.FIELDS_TO_ATTRIBUTES:
                if record[f] is None:
                    element.set(f, "")
                else:
                    value = table[f].formatter(record[f])
                    element.set(f, str(value).decode('utf-8'))

                if record[f] is None:
                    element.set(f, "")
                elif table[f].represent:
                    element.set(f, str(table[f].represent(record[f])).decode('utf-8'))
                else:
                    element.set(f, str(table[f].formatter(record[f])).decode('utf-8'))
            elif table[f].type.startswith("reference"):
                _rtable = table[f].type.split()[1]
                if _rtable in self.db and self._UUID in self.db[_rtable]:
                    rtable = self.db[_rtable]
                    try:
                        _uuid = self.db(rtable.id==record[f]).select(rtable._uuid)[0].uuid
                    except:
                        continue
                    prefix, resource = _rtable.split("_", 1)
                    reference = etree.SubElement(element, self.TAG["reference"])
                    reference.set(self.ATTRIBUTE["field"], str(f))
                    reference.set(self.ATTRIBUTE["prefix"], str(prefix))
                    reference.set(self.ATTRIBUTE["resource"], str(resource))
                    reference.set(self._UUID, str(_uuid))
                else:
                    continue
            else:
                if record[f] is None and not table[f].readable:
                    continue
                else:
                    data = etree.SubElement(element, self.TAG["data"])
                    data.set(self.ATTRIBUTE["field"], str(f))
                    if record[f] is not None:
                        value = table[f].formatter(record[f])
                        if table[f].represent:
                            data.set(self.ATTRIBUTE["value"], str(value).decode('utf-8'))
                            data.text = str(table[f].represent(record[f])).decode('utf-8')
                        else:
                            data.text = str(value).decode('utf-8')

        return element

    # -------------------------------------------------------------------------
    def record(self, prefix, name, element, skip=[]):
        """
            Builds a record from an element and validates it

            prefix:         the resource prefix
            name:           the resource name
            element:        the element
            skip:           list of fields to skip (optional)

            returns: Storage

            Resource Routing:
            Reference elements will be mapped to record id's, provided that a
            UUID match exists => otherwise the particular <reference> element
            will be ignored.
        """

        _table = "%s_%s" % (prefix, name)
        if _table in self.db:
            table = self.db[_table]
        else:
            self.error = S3XML_BAD_RESOURCE
            return None

        record = Storage()
        original = None
        update = False

        if self._UUID in table.fields and self._UUID not in skip:
            _uuid = element.get(self._UUID, None)
            if _uuid and len(_uuid)>0:
                record[self._UUID] = _uuid
                if self.db(table.uuid==_uuid).count():
                    original = self.db(table.uuid==_uuid).select(table.ALL)[0]
                    update = True

        for child in element:
            fieldname = child.get(self.ATTRIBUTE["field"], None)
            if fieldname in skip:
                continue
            if child.tag==self.TAG["data"]:
                if not fieldname:
                    continue
                if fieldname not in table.fields:
                    continue
                if table[fieldname].type.startswith('reference'):
                    continue
                value = child.get(self.ATTRIBUTE["value"], None)
                if value is None:
                    value = child.text
                if value is None:
                    value = table[fieldname].default
                if value is None and table[fieldname].type == "string":
                    value = ''

                skip_validation=False
                if update:
                    if table[fieldname].type=="string" and original[fieldname]==None:
                        skip_validation=False
                    elif original[fieldname]==value:
                        skip_validation=True

                if not skip_validation:
                    requires = table[fieldname].requires
                    if requires:
                        if not isinstance(requires, (list, tuple)):
                            requires = [requires]
                        for validator in requires:
                            (value, error) = validator(value)
                            if error is not None:
                                self.error = error
                                return None

                record[fieldname] = value

            elif child.tag==self.TAG["reference"]:
                fieldname = child.get(self.ATTRIBUTE["field"], None)
                if not fieldname or fieldname not in table.fields:
                    continue
                prefix = child.get(self.ATTRIBUTE["prefix"], None)
                resource = child.get(self.ATTRIBUTE["resource"], None)
                _uuid = child.get(self._UUID, None)
                if not (prefix and resource and _uuid):
                    continue
                _rtable = "%s_%s" % (prefix, resource)
                if _rtable in self.db and self._UUID in self.db[_rtable]:
                    rtable = self.db[_rtable]
                    try:
                        rid = self.db(rtable.uuid==_uuid).select(rtable.id)[0].id
                    except:
                        continue
                    record[fieldname] = rid
                else:
                    continue

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in skip:
                continue
            if f in table.fields:
                value = element.get(f, None)
                if value is not None:
                    skip_validation=False
                    if update:
                        if table[f].type=="string" and original[f]==None:
                            skip_validation=False
                        elif original[f]==value:
                            skip_validation=True
                    if not skip_validation:
                        requires = table[f].requires
                        if requires:
                            if not isinstance(requires, (list, tuple)):
                                requires = [requires]
                            for validator in requires:
                                (value, error) = validator(value)
                                if error is not None:
                                    self.error = error
                                    return None

                    record[f]=value

        return record

    # -------------------------------------------------------------------------
    def commit(self):
        """
            Commits all pending imports to the database.

            returns: void
        """

        for r in self.imports:
            r.commit()

    # -------------------------------------------------------------------------
    def __export(self, prefix, name, query, joins=[], skip=[], permit=None):
        """
            Exports data from the database as list of <resource> elements

            prefix:         Module prefix
            name:           Resource name
            query:          web2py DB Query
            joins:          List of joins =[dict(prefix, name, pkey, fkey)]
            skip:           List of fields to skip

            returns: [Element]
        """

        try:
            _table = "%s_%s" % (prefix, name)

            if permit and not permit(self.PERMISSION["read"], _table):
                return None

            table = self.db[_table]

            records = self.db(query).select(table.ALL) or []
            resources = []

            for record in records:
                if permit and not permit(self.PERMISSION["read"], _table, record_id=record.id):
                    continue

                self.exports.append(dict(prefix=prefix, name=name, id=record.id))

                resource = self.element(prefix, name, record, skip=skip)
                resource.set(self.ATTRIBUTE["prefix"], prefix)
                resource.set(self.ATTRIBUTE["name"], name)

                for join in joins:
                    _jtable = "%s_%s" % (join["prefix"], join["name"])
                    jtable = self.db[_jtable]

                    _query = (jtable[join["fkey"]]==record[join["pkey"]])
                    if "id" in join and join["id"]:
                        _query = (jtable.id==join["id"]) & _query
                    if "deleted" in jtable:
                        _query = ((jtable.deleted==False) | (jtable.deleted==None)) & _query

                    jresources = self.__export(join["prefix"], join["name"], _query, skip=[join["fkey"]])
                    if jresources:
                        resource.extend(jresources)

                resources.append(resource)

            return resources

        except:
            return None

    # -------------------------------------------------------------------------
    def get(self, prefix, name, id, joins=[], permit=None):
        """
            Interface function to export data through JRC

            returns: ElementTree
        """

        self.error = None

        _table = "%s_%s" % (prefix, name)
        root = etree.Element(self.TAG["root"])

        if _table in self.db:
            table = self.db[_table]

            if id and isinstance(id, (list, tuple)):
                query = (table.id.belongs(id))
            elif id:
                query = (table.id==id)
            else:
                query = (table.id>0)

            if "deleted" in table:
                query = ((table.deleted==False) | (table.deleted==None)) & query

            resources = self.__export(prefix, name, query, joins=joins, permit=permit)
            if resources:
                root.extend(resources)

        tree = etree.ElementTree(root)
        return tree

    # -------------------------------------------------------------------------
    def put(self, prefix, name, id, tree, joins=[], jrequest=False, permit=None, onvalidation=None, onaccept=None):
        """
            Interface function to import data through JRC

            returns: boolean
        """

        if not tree: # nothing to import actually
            return True

        self.error = None
        self.imports = []

        root = tree.getroot()
        if not root.tag==self.TAG["root"]:
            self.error = S3XML_BAD_SOURCE
            return False

        expr = './/resource[@%s="%s" and @%s="%s"]' % (self.ATTRIBUTE["prefix"], prefix, self.ATTRIBUTE["name"], name)
        elements = root.xpath(expr)

        if not len(elements): # still nothing to import
            return True

        _table = "%s_%s" % (prefix, name)
        if _table in self.db:
            table = self.db[_table]
        else:
            self.error = S3XML_BAD_RESOURCE
            return False

        if id:
            try:
                db_record = self.db(table.id==id).select(table.ALL)[0]
            except:
                self.error = S3XML_BAD_RECORD
                return False
        else:
            db_record = None

        if id and len(elements)>1:
            # ID given, but multiple elements of that type => try to find UUID match
            if self._UUID in table:
                _uuid = db_record[self._UUID]
                for element in elements:
                    if element.get(self._UUID)==_uuid:
                        elements = [element]
                        break

            if len(elements)>1:
                # Error: multiple input elements, but only one target record
                self.error = S3XML_NO_MATCH
                return False

        for element in elements:

            if not jrequest:
                record = self.record(prefix, name, element)
                if not record:
                    self.error = S3XML_VALIDATION_ERROR
                    continue

                xml_import = XMLImport(self.db, prefix, name, id, record, permit=permit, onvalidation=onvalidation, onaccept=onaccept)

                if not xml_import.method: # possibly unnecessary to check here
                    self.error = S3XML_DATA_IMPORT_ERROR
                    continue

                xml_import.commit()
                record_id = xml_import.id
                if not record_id:
                    self.error = S3XML_DATA_IMPORT_ERROR
                    continue

                db_record = self.db(table.id==record_id).select(table.ALL)[0]

            else:
                record_id = db_record.id

            for join in joins:
                jprefix, jname = join["prefix"], join["name"]
                expr = './resource[@%s="%s" and @%s="%s"]' % (self.ATTRIBUTE["prefix"], jprefix, self.ATTRIBUTE["name"], jname)
                jelements = element.xpath(expr)
                for jelement in jelements:
                    jrecord = self.record(jprefix, jname, jelement)
                    if not jrecord:
                        self.error = S3XML_VALIDATION_ERROR
                        continue
                    xml_import = XMLImport(self.db, jprefix, jname, None, jrecord, permit=permit)
                    if xml_import.method:
                        xml_import.record[join["fkey"]]=db_record[join["pkey"]]
                        self.imports.append(xml_import)
                    else:
                        self.error = S3XML_DATA_IMPORT_ERROR
                        continue
        return True
