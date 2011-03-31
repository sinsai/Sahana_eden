# -*- coding: utf-8 -*-

""" Resource Import Tools

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}
    @requires: U{B{I{lxml}} <http://codespeak.net/lxml>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

__all__ = ["S3Importer"]

import datetime

from gluon.storage import Storage
from lxml import etree

# *****************************************************************************
class S3Importer(object):

    """
    Data Import functions

    @todo 2.3: implement json

    """

    # -------------------------------------------------------------------------
    def __init__(self, manager):
        """
        Constructor

        @param manager: the S3ResourceController

        """

        self.manager = manager
        self.db = self.manager.db


    # -------------------------------------------------------------------------
    def csv(self, file, table=None):
        """
        Import CSV file into database

        @param file: file handle
        @param table: the table to import to

        @todo 2.3: make this resource-based (files!)

        """

        if table:
            table.import_from_csv_file(file)
        else:
            db = self.db
            # This is the preferred method as it updates reference fields
            db.import_from_csv_file(file)
            db.commit()


    # -------------------------------------------------------------------------
    def url(self, r):
        """
        Import data from URL query

        @param r: the S3Request
        @note: can only update single records (no mass-update)

        @todo 2.3: make this resource-based

        """

        manager = self.manager
        xml = manager.xml

        prefix, name, table, tablename = r.target()

        record = r.record
        resource = r.resource

        # Handle components
        if record and r.component:
            component = resource.components[r.component_name]
            resource = component.resource
            resource.load()
            if len(resource) == 1:
                record = resource.records()[0]
            else:
                record = None
            r.request.vars.update({component.fkey:r.record[component.pkey]})
        elif not record and r.component:
            item = xml.json_message(False, 400, "Invalid Request!")
            return dict(item=item)

        # Check for update
        if record and xml.UID in table.fields:
            r.request.vars.update({xml.UID:xml.export_uid(record[xml.UID])})

        # Build tree
        element = etree.Element(xml.TAG.resource)
        element.set(xml.ATTRIBUTE.name, resource.tablename)
        for var in r.request.vars:
            if var.find(".") != -1:
                continue
            elif var in table.fields:
                field = table[var]
                value = str(r.request.vars[var]).decode("utf-8")
                if var in xml.FIELDS_TO_ATTRIBUTES:
                    element.set(var, value)
                else:
                    data = etree.Element(xml.TAG.data)
                    data.set(xml.ATTRIBUTE.field, var)
                    if field.type == "upload":
                        data.set(xml.ATTRIBUTE.filename, value)
                    else:
                        data.text = xml.xml_encode(value)
                    element.append(data)
        tree = xml.tree([element], domain=manager.domain)

        # Import data
        result = Storage(committed=False)
        manager.resolve = lambda job, result=result: result.update(job=job)
        try:
            success = resource.import_xml(tree)
        except SyntaxError:
            pass

        # Check result
        if result.job:
            result = result.job

        # Build response
        if success and result.committed:
            id = result.id
            method = result.method
            if method == result.METHOD.CREATE:
                item = xml.json_message(True, 201, "Created as %s?%s.id=%s" %
                        (str(r.there(representation="html", vars=dict())),
                        result.name, result.id))
            else:
                item = xml.json_message(True, 200, "Record updated")
        else:
            item = xml.json_message(False, 403,
                        "Could not create/update record: %s" %
                            manager.error or xml.error,
                        tree=xml.tree2json(tree))

        return dict(item=item)


    # -------------------------------------------------------------------------
    def xml(self, resource, source,
            files=None,
            id=None,
            format="xml",
            stylesheet=None,
            ignore_errors=False, **args):
        """
        XML Importer

        @param resource: the target resource
        @param source: the data source, accepts source=xxx, source=[xxx, yyy, zzz] or
                       source=[(resourcename1, xxx), (resourcename2, yyy)], where the
                       xxx has to be either an ElementTree or a file-like object
        @param files: attached files (None to read in the HTTP request)
        @param id: ID (or list of IDs) of the record(s) to update (performs only update)
        @param format: type of source = "xml", "json" or "csv"
        @param stylesheet: stylesheet to use for transformation
        @param ignore_errors: skip invalid records silently
        @param args: parameters to pass to the transformation stylesheet

        """

        xml = self.manager.xml
        permit = self.manager.permit

        # Check permission for the resource
        authorised = permit("create", resource.table) and \
                     permit("update", resource.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        # Resource data
        prefix = resource.prefix
        name = resource.name

        # Additional stylesheet parameters
        tfmt = self.manager.xml.ISOFORMAT
        utcnow = datetime.datetime.utcnow().strftime(tfmt)
        domain = self.manager.domain
        base_url = self.manager.s3.base_url
        args.update(domain=domain,
                    base_url=base_url,
                    prefix=prefix,
                    name=name,
                    utcnow=utcnow)

        # Build import tree
        if not isinstance(source, (list, tuple)):
            source = [source]
        tree = None
        for item in source:
            if isinstance(item, (list, tuple)):
                resourcename, s = item[:2]
            else:
                resourcename, s = None, item
            if isinstance(s, etree._ElementTree):
                t = s
            elif format == "json":
                if isinstance(s, basestring):
                    from StringIO import StringIO
                    source = StringIO(s)
                    t = xml.json2tree(s)
                else:
                    t = xml.json2tree(s)
            elif format == "csv":
                t = xml.csv2tree(s, resourcename=resourcename)
            else:
                t = xml.parse(s)
            if not t:
                raise SyntaxError("Invalid source")

            if stylesheet is not None:
                t = xml.transform(t, stylesheet, **args)
                if not t:
                    raise SyntaxError(xml.error)
            if not tree:
                tree = t.getroot()
            else:
                tree.extend(list(t.getroot()))

        # Import the tree
        if files is not None and isinstance(files, dict):
            resource.files = Storage(files)
        success = self.manager.import_tree(resource, id, tree,
                                           ignore_errors=ignore_errors)
        resource.files = Storage()

        # Response message
        if success:
            return xml.json_message()
        else:
            tree = xml.tree2json(self.manager.error_tree)
            msg = xml.json_message(False, 400,
                                   message=self.manager.error,
                                   tree=tree)
            return msg


# *****************************************************************************
