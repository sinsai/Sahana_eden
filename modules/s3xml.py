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
# S3XML
#
class S3XML(object):

    _UUID = 'uuid'

    IGNORE_FIELDS = ['deleted', 'id']

    FIELDS_TO_ATTRIBUTES = [
            'created_on',
            'modified_on',
            'created_by',
            'modified_by',
            'uuid',
            'admin']

    ATTRIBUTES_TO_FIELDS = [
            'admin']

    TAG = dict(
        root="sahanapy",
        resource="resource",
        data="data"
        )

    ATTRIBUTE = dict(
        prefix="prefix",
        name="name",
        table="table",
        field="field",
        value="value"
        )

    def __init__(self, db):
        self.db = db
        self.error = None

    # -------------------------------------------------------------------------
    def parse(self, source):
        """
            Deserialize an XML source into an ElementTree object

            returns: ElementTree
        """
        self.error = None
        try:
            result = etree.parse(source)
            return result
        except:
            self.error = "XML Parse Error"
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
                    self.error = "XSL Transformation Error"
                    return None
            else:
                # Error parsing the XSL template
                return None
        else:
            self.error = "XSL Transformation not available"
            return None

    # -------------------------------------------------------------------------
    def tostring(self, tree):
        """
            Serialize an element tree as string object

            returns: str
        """
        return etree.tostring(tree, xml_declaration=True, encoding="utf-8", pretty_print=True)

    # -------------------------------------------------------------------------
    def __element(self, table, record, skip=[]):
        """
            Builds an element from a record

            table:          the database table
            record:         the record (as dict of fields)
            skip:           list of fields to skip (optional)

            returns: Element
        """

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
    def __export(self, prefix, name, query, joins=[], skip=[]):
        """
            Exports data from the database as list of <resource> elements

            prefix:         Module prefix
            name:           Resource name
            query:          web2py DB Query
            joins:          List of joins =[dict(prefix, name, pkey, fkey)]
            skip:           List of fields to skip

            returns: [Element]
        """

        _table = "%s_%s" % (prefix, name)
        try:
            table = self.db[_table]

            records = self.db(query).select(table.ALL) or []
            resources = []
            for record in records:
                resource = self.__element(table, record, skip=skip)
                resource.set(self.ATTRIBUTE["prefix"], prefix)
                resource.set(self.ATTRIBUTE["name"], name)
                for join in joins:
                    _jtable = "%s_%s" % (join["prefix"], join["name"])
                    jtable = self.db[_jtable]
                    _query = (jtable[join["fkey"]]==record[join["pkey"]])
                    if "id" in join:
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
    def __record(self, table, element):
        """
            Builds a record from an element and validates it

            table:      the database table
            element:    the element

            Note: all web2py foreign keys (reference-fields) will be dropped

            returns: dict
        """

        record = {}
        for child in element:
            if child.tag==self.TAG["data"]:
                fieldname = child.get(self.ATTRIBUTE["field"], None)
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

        if self._UUID in table.fields:
            uuid = element.get(self._UUID, None)
            if uuid and len(uuid)>0:
                record[self._UUID] = uuid

        for f in self.ATTRIBUTES_TO_FIELDS:
            if f in table.fields:
                value = element.get(f, None)
                if value is not None:
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
    def __import(self, table, id, record):
        """
            Commits a record to the database (CRUD create/update)

            table:          the database table
            id:             the record ID in the table (0 for create)
            record:         the record (built with __record)

            NOTE:
            If id==0, but record.uuid matches an existing record, then this record
            will get updated instead of creating a new => drop uuid to force create!

            returns id (0 at error)
        """

        try:
            if id==0:
                uuid = record.get(self._UUID, None)
                if uuid is not None:
                    if self.db(table.uuid==uuid).count():
                        del record[self._UUID]
                        _id = self.db(table.uuid==uuid).update(**dict(record))
                        return _id
                _id = table.insert(**dict(record))
                return _id
            else:
                if self._UUID in record:
                    del record[self._UUID]
                if self.db(table.id==id).count():
                    _id = self.db(table.id==id).update(**dict(record))
                    return _id
                else:
                    # Error: invalid record ID
                    return 0
        except:
            # can raise IntegrityError
            return 0

    # -------------------------------------------------------------------------
    def serialize(self, prefix, name, query, joins=[]):

        root = etree.Element(self.TAG["root"])

        resources = self.__export(prefix, name, query, joins=joins)
        if resources:
            root.extend(resources)

        tree = etree.ElementTree(root)

        return tree

