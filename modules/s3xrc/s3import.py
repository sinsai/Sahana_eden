# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Resource Import Toolkit

    @version: 2.2.3

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

__all__ = ["S3Importer"]

from gluon.storage import Storage
from lxml import etree

# *****************************************************************************
class S3Importer(object):

    """ Importer class """

    # -------------------------------------------------------------------------
    def __init__(self, manager):

        """ Constructor

            @param manager: the resource controller

        """

        self.manager = manager
        self.db = self.manager.db


    # -------------------------------------------------------------------------
    def csv(self, file, table=None):

        """ Import CSV file into database

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

        """ Import data from URL query

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
            r.request.vars.update({xml.UID:record[xml.UID]})

        # Build tree
        element = etree.Element(xml.TAG.resource)
        element.set(xml.ATTRIBUTE.name, resource.tablename)
        for var in r.request.vars:
            if var.find(".") != -1:
                continue
            elif var in table.fields:
                field = table[var]
                value = xml.xml_encode(str(r.request.vars[var]).decode("utf-8"))
                if var in xml.FIELDS_TO_ATTRIBUTES:
                    element.set(var, value)
                else:
                    data = etree.Element(xml.TAG.data)
                    data.set(xml.ATTRIBUTE.field, var)
                    if field.type == "upload":
                        data.set(xml.ATTRIBUTE.filename, value)
                    else:
                        data.text = value
                    element.append(data)
        tree = xml.tree([element], domain=manager.domain)

        # Import data
        result = Storage(committed=False)
        manager.sync_resolve = lambda vector, result=result: \
                                      result.update(vector=vector)
        try:
            success = resource.import_xml(tree)
        except SyntaxError:
            pass

        # Check result
        if result.vector:
            result = result.vector

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
            template=None,
            ignore_errors=False, **args):

        """ Import data from an XML source into a resource

            @param resource: the resource to import to
            @param source: the XML source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        xml = self.manager.xml
        permit = self.manager.permit

        authorised = permit("create", resource.table) and \
                     permit("update", resource.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if isinstance(source, etree._ElementTree):
            tree = source
        else:
            tree = xml.parse(source)

        if tree:
            if template is not None:
                tree = xml.transform(tree, template, **args)
                if not tree:
                    raise SyntaxError(xml.error)

            if files is not None and isinstance(files, dict):
                resource.files(files=Storage(files))

            success = self.manager.import_tree(resource, id, tree,
                                               ignore_errors=ignore_errors)

            resource.files(files=Storage())
            return success
        else:
            raise SyntaxError("Invalid XML source")


    # -------------------------------------------------------------------------
    def json(self, resource, source,
             files=None,
             id=None,
             template=None,
             ignore_errors=False, **args):

        """ Import data from a JSON source into a resource

            @param resource: the resource to import data to
            @param source: the JSON source (or ElementTree)
            @param files: file attachments as {filename:file}
            @param id: the ID or list of IDs of records to update (None for all)
            @param template: the XSLT template
            @param ignore_errors: do not stop on errors (skip invalid elements)
            @param args: arguments to pass to the XSLT template

            @raise SyntaxError: in case of a parser or transformation error
            @raise IOError: at insufficient permissions

        """

        xml = self.manager.xml
        permit = self.manager.permit

        authorised = permit("create", resource.table) and \
                     permit("update", resource.table)
        if not authorised:
            raise IOError("Insufficient permissions")

        if isinstance(source, etree._ElementTree):
            tree = source
        elif isinstance(source, basestring):
            from StringIO import StringIO
            source = StringIO(source)
            tree = xml.json2tree(source)
        else:
            tree = xml.json2tree(source)

        if tree:
            if template is not None:
                tree = xml.transform(tree, template, **args)
                if not tree:
                    raise SyntaxError(xml.error)
            if files is not None and isinstance(files, dict):
                resource.files(files=Storage(files))

            success = self.manager.import_tree(resource, id, tree,
                                               ignore_errors=ignore_errors)

            resource.files(files=Storage())
            return success
        else:
            raise SyntaxError("Invalid JSON source.")


# *****************************************************************************
