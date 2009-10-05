# -*- coding: utf-8 -*-

"""
    SahanaPy XML Interface

    @version: 1.0-2, 2009-10-04
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: nursix
    @copyright: (c) 2009 Dominic König (nursix.org)
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

__name__ = "S3XML"

import uuid

from gluon.storage import Storage

#******************************************************************************
# Errors
#
S3XML_BAD_RESOURCE = "Invalid Resource"
S3XML_PARSE_ERROR = "XML Parse Error"
S3XML_TRANFORMATION_ERROR = "XSL Transformation Error"
S3XML_NO_LXML = "lxml not installed"
S3XML_BAD_SOURCE = "Invalid XML Source"
S3XML_BAD_RECORD = "Invalid Record ID"
S3XML_NO_MATCH = "No Matching Element"
S3XML_VALIDATION_ERROR = "Validation Error"
S3XML_DATA_IMPORT_ERROR = "Data Import Error"

#******************************************************************************
# lxml
#
NO_LXML=True
try:
    from lxml import etree
    NO_LXML=False
except ImportError:
    try:
        import xml.etree.cElementTree as etree
        print "WARNING: %s: lxml not installed - using cElementTree" % __name__
    except ImportError:
        try:
            import xml.etree.ElementTree as etree
            print "WARNING: %s: lxml not installed - using ElementTree" % __name__
        except ImportError:
            try:
                import cElementTree as etree
                print "WARNING: %s: lxml not installed - using cElementTree" % __name__
            except ImportError:
                # normal ElementTree install
                import elementtree.ElementTree as etree
                print "WARNING: %s: lxml not installed - using ElementTree" % __name__

# *****************************************************************************
# XMLImport
#
class XMLImport(object):

    """ Helper class to represent database imports """

    PERMISSION = dict(create="create", update="update")

    def __init__(self,
                 db=None,
                 prefix=None,
                 name=None,
                 id=None,
                 record=None,
                 permit=None,
                 onvalidation=None,
                 onaccept=None):
        """
            @param db:              the database to use
            @param prefix:          the resource prefix (module name)
            @param name:            the resource name
            @param id:              the record ID of the target record
            @param record:          the record to import (as dict of fields)
            @param onvalidation:    callback to invoke before DB commit
            @param onaccept:        callback to invoke after DB commit
        """

        self.db=db
        self.prefix=prefix
        self.name=name
        self.id=id

        self.tablename = "%s_%s" % (self.prefix, self.name)
        self.table = self.db[self.tablename]

        self.method=None
        self.record=record

        self.onvalidation=onvalidation
        self.onaccept=onaccept

        self.accepted=True
        self.permitted=True
        self.committed=False

        self._UUID = "uuid"

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

        if permit and not \
           permit(permission, self.tablename, record_id=self.id):
            self.permitted=False

    # -------------------------------------------------------------------------
    def commit(self):
        """
            Commits this record to the database.

            @return: True at success, False at error
            @rtype: boolean
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
                    self.db(self.table.id==self.id).update(**dict(self.record))
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

    """ Class to handle XML imports/exports """

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
        resource="resource",
        domain="domain",
        url="url"
        )

    PERMISSION = dict(
        read="read",
        create="create",
        update="update"
    )

    def __init__(self, db, domain=None, base_url=None):

        self.db = db
        self.error = None

        self.imports = []
        self.exports = []

        self.domain = domain
        self.base_url = base_url

    # -------------------------------------------------------------------------
    def parse(self, source):
        """
            Deserialize an XML source into an ElementTree object

            @param source:
                the source to be parsed, can be a file or a file-like object,
                or a filename or URL

            @rtype: ElementTree
            @return:
                the corresponding element tree, I{None} at error
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
            Transforms an element tree using the given XSLT template.

            @param tree: the element tree to be transformed
            @type tree: ElementTree
            @param template_path: the XSLT template as file, file-like object, filename or URL

            @rtype: ElementTree
            @return:
                The transformed element tree, I{None} at any error.

            @note:
                if U{B{I{lxml}} <http://codespeak.net/lxml>} is not installed,
                this function will always fail!
        """

        if not NO_LXML:
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
            self.error = S3XML_NO_LXML
            return None

    # -------------------------------------------------------------------------
    def tostring(self, tree):
        """
            Serializes an element tree as string object

            @rtype: str
            @return:
                The string representation of the element tree.

            @note:
                pretty-printed, with XML declaration, encoding="utf-8"
        """
        if NO_LXML:
            return etree.tostring(tree.getroot(), encoding="utf-8")
        else:
            return etree.tostring(tree,
                                  xml_declaration=True,
                                  encoding="utf-8",
                                  pretty_print=True)

    # -------------------------------------------------------------------------
    def element(self, prefix, name, record, skip=[]):
        """
            Builds an element from a record

            @param prefix:      the resource prefix (=module name)
            @param name:        the resource name
            @param record:      the record (as dict of fields)
            @param skip:        list of fields to skip (optional)

            @rtype: Element

            @note:
                References will be mapped to UUID's and represented as
                <reference> elements. If the referenced table doesn't
                contain UUID's, the reference field will not be represented
                at all.
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
                        _uuid = self.db(rtable.id==record[f]).select(rtable.uuid)[0].uuid
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
            Builds a record from an element and validates it.

            @param prefix: the resource prefix (=module name)
            @param name: the resource name
            @param element: the element
            @type element: Element
            skip:           list of fields to skip (optional)

            @rtype: Storage
            @return:
                a Storage dictionary of fields for this record

            @note:
            References will be mapped from UUID's to internal record ID's,
            provided that a UUID match exists => otherwise the particular
            reference element will be ignored.
        """

        _table = "%s_%s" % (prefix, name)
        if _table in self.db:
            table = self.db[_table]
        else:
            self.error = S3XML_BAD_RESOURCE
            return None

        record = Storage()
        original = None

        if self._UUID in table.fields and self._UUID not in skip:
            _uuid = element.get(self._UUID, None)
            if _uuid and len(_uuid)>0:
                record[self._UUID] = _uuid
                try:
                    original = self.db(table.uuid==_uuid).select(table.ALL)[0]
                except:
                    original = None

        for child in element:
            if child.tag==self.TAG["data"]:
                fieldname = child.get(self.ATTRIBUTE["field"], None)
                if not fieldname or fieldname not in table.fields:
                    continue
                if fieldname in self.IGNORE_FIELDS or fieldname in skip:
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

                if value is not None:
                    (value, error) = self.validate(table, original, fieldname, value)
                    if error:
                        self.error = error
                        return None
                    else:
                        record[fieldname]=value

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
            else:
                continue

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in skip:
                continue
            if f in table.fields:
                value = element.get(f, None)
                if value is not None:
                    (value, error) = self.validate(table, original, f, value)
                    if error:
                        self.error = error
                        return None
                    else:
                        record[f]=value

        return record

    # -------------------------------------------------------------------------
    def validate(self, table, record, fieldname, value):
        """
            Validates a value for that field.

            @param table: the database table
            @param record: the original record in case of update action
            @param fieldname: the name of the field
            @param value: the value to validate for this field

            @rtype: tuple(value, error)
            @return:
                I{value} is the validated value,
                I{error} is None unless the value is invalid for this field

            @note:
            The returned value can be different from the input value - always use
            the returned (B{!}) value for DB commit.
        """

        requires = table[fieldname].requires

        if not requires:
            return (value, None)
        else:
            if record is not None:
                # Skip validation of unchanged values on update
                if record[fieldname] is not None and record[fieldname]==value:
                    return (value, None)

            if not isinstance(requires, (list, tuple)):
                requires = [requires]

            for validator in requires:
                (value, error) = validator(value)
                if error:
                    return (value, error)

            return(value, None)

    # -------------------------------------------------------------------------
    def commit(self):
        """
            Commits all pending imports to the database.
        """

        for r in self.imports:
            r.commit()
        return

    # -------------------------------------------------------------------------
    def __export(self, prefix, name, query, joins=[], skip=[], permit=None, url=None):
        """
            Exports data from the database as list of elements

            @param prefix: resource prefix (=module name)
            @param name: resource name
            @param query: web2py DB Query
            @param joins: list of joins to export
            @type joins:
                [dict(prefix=str, name=str, pkey=str, fkey=str, multiple=boolean)]
            @param skip: list of fields to skip
            @type skip:
                [str]

            @rtype: [Element]
            @return:
                list of elements
        """

        if self.base_url and not url:
            url = "%s/%s" % (self.base_url, prefix)

        try:
            _table = "%s_%s" % (prefix, name)

            if permit and not permit(self.PERMISSION["read"], _table):
                return None

            table = self.db[_table]

            records = self.db(query).select(table.ALL) or []
            resources = []

            for record in records:
                if permit and not \
                   permit(self.PERMISSION["read"], _table, record_id=record.id):
                    continue

                self.exports.append(dict(prefix=prefix, name=name, id=record.id))

                resource = self.element(prefix, name, record, skip=skip)
                resource.set(self.ATTRIBUTE["prefix"], prefix)
                resource.set(self.ATTRIBUTE["name"], name)

                if url:
                    resource_url = "%s/%s/%s" % (url, name, record.id)
                    resource.set(self.ATTRIBUTE["url"], resource_url)
                else:
                    resource_url = None

                for join in joins:
                    _jtable = "%s_%s" % (join["prefix"], join["name"])
                    jtable = self.db[_jtable]

                    _query = (jtable[join["fkey"]]==record[join["pkey"]])
                    if "id" in join and join["id"]:
                        _query = (jtable.id==join["id"]) & _query
                    if "deleted" in jtable:
                        _query = ((jtable.deleted==False) |
                                  (jtable.deleted==None)) & _query

                    jresources = self.__export(join["prefix"], join["name"],
                                               _query, skip=[join["fkey"]], url=resource_url)
                    if jresources:
                        if NO_LXML:
                            for r in jresources:
                                resource.append(r)
                        else:
                            resource.extend(jresources)

                resources.append(resource)

            return resources

        except:
            return None

    # -------------------------------------------------------------------------
    def get(self, prefix, name, id, joins=[], permit=None):
        """
            Interface function to export data through JRC

            @param prefix: the resource prefix (=module name)
            @param name: the resource name
            @param id: the record ID (None or 0 for all records)
            @param permit: callback function to check read permission
            @type permit:
                lambda permission_name, table, record_id: return [True|False]

            @rtype: ElementTree
            @return:
                the element tree generated for this request
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

            resources = self.__export(prefix, name, query,
                                      joins=joins, permit=permit)
            if resources:
                if NO_LXML:
                    for r in resources:
                        root.append(r)
                else:
                    root.extend(resources)

        if self.domain:
            root.set(self.ATTRIBUTE["domain"], self.domain)

        if self.base_url:
            root.set(self.ATTRIBUTE["url"], self.base_url)

        tree = etree.ElementTree(root)
        return tree

    # -------------------------------------------------------------------------
    def put(self,
            prefix,
            name,
            id,
            tree,
            joins=[],
            jrequest=False,
            permit=None,
            onvalidation=None,
            onaccept=None):

        """
            Interface function to import data through JRC

            @requires: lxml XPath

            @param prefix: the resource prefix (=module name)
            @param name: the resource name
            @param id: the target record ID
            @param tree: the element tree to import
            @type tree:
                ElementTree
            @param joins: list of joins to be imported (if available in the tree)
            @type joins:
                B{[dict(prefix=str, name=str, pkey=str, fkey=str, multiple=boolean)]}
            @param jrequest: True to import only joined resources
            @type jrequest:
                boolean
            @param permit: callback function or lambda to check permission
            @type permit:
                B{lambda permission_name, tablename, record_id: return [True|False]}
            @param onvalidation: callback function or lambda to be invoked before DB commit
            @type onvalidation:
                B{lambda form: return [unchecked]}
            @param onaccept: callback function to be invoked after DB commit
            @type onaccept:
                B{lambda form: return [unchecked]}

            @rtype: boolean
            @return:
                False at fatal error, otherwise True
        """

        if NO_LXML:
            self.error = S3XML_NO_LXML
            return False

        if not tree: # nothing to import actually
            return True

        self.error = None
        self.imports = []

        root = tree.getroot()
        if not root.tag==self.TAG["root"]:
            self.error = S3XML_BAD_SOURCE
            return False

        expr = './/resource[@%s="%s" and @%s="%s"]' % \
               (self.ATTRIBUTE["prefix"], prefix, self.ATTRIBUTE["name"], name)
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
            # ID given, but multiple elements of that type
            # => try to find UUID match
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

                xml_import = XMLImport(self.db, prefix, name, id, record,
                    permit=permit,
                    onvalidation=onvalidation,
                    onaccept=onaccept)
                if not xml_import.method:
                    # possibly unnecessary to check here
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
                expr = './resource[@%s="%s" and @%s="%s"]' % (
                       self.ATTRIBUTE["prefix"], jprefix,
                       self.ATTRIBUTE["name"], jname)
                jelements = element.xpath(expr)
                for jelement in jelements:
                    jrecord = self.record(jprefix, jname, jelement)
                    if not jrecord:
                        self.error = S3XML_VALIDATION_ERROR
                        continue
                    xml_import = XMLImport(self.db, jprefix, jname,
                                           None, jrecord, permit=permit)
                    if xml_import.method:
                        xml_import.record[join["fkey"]]=db_record[join["pkey"]]
                        self.imports.append(xml_import)
                    else:
                        self.error = S3XML_DATA_IMPORT_ERROR
                        continue
        return True
