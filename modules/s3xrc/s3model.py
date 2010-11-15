# -*- coding: utf-8 -*-

""" S3XRC Resource Framework - Data Model Extensions

    @version: 2.2.3

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>} on Eden wiki

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

__all__ = ["S3ResourceComponent",
           "S3ResourceModel"]

from gluon.storage import Storage
from gluon.sql import Table, Field
from gluon.validators import IS_EMPTY_OR, IS_IN_DB

# *****************************************************************************
class S3ResourceComponent(object):

    """ Class to represent component relations between resources

        @param db: the database (DAL)
        @param prefix: prefix of the resource name (=module name)
        @param name: name of the resource (=without prefix)
        @param attr: attributes

    """

    def __init__(self, db, prefix, name, **attr):

        self.db = db
        self.prefix = prefix
        self.name = name

        self.tablename = "%s_%s" % (prefix, name)
        self.table = self.db.get(self.tablename, None)
        if not self.table:
            raise SyntaxError("Table must exist in the database.")

        self.attr = Storage(attr)
        if not "multiple" in self.attr:
            self.attr.multiple = True
        if not "deletable" in self.attr:
            self.attr.deletable = True
        if not "editable" in self.attr:
            self.attr.editable = True


    # Configuration ===========================================================

    def set_attr(self, name, value):

        """ Sets an attribute for a component

            @param name: attribute name
            @param value: attribute value

        """

        self.attr[name] = value


    # -------------------------------------------------------------------------
    def get_attr(self, name):

        """ Reads an attribute of the component

            @param name: attribute name

        """

        if name in self.attr:
            return self.attr[name]
        else:
            return None


# *****************************************************************************
class S3ResourceModel(object):


    """ Class to handle the compound resources model

        @param db: the database (DAL)

    """

    def __init__(self, db):

        self.db = db
        self.components = {}
        self.config = Storage()
        self.methods = {}
        self.cmethods = {}


    # Components ==============================================================

    def add_component(self, prefix, name, **attr):

        """ Adds a component to the model

            @param prefix: prefix of the component name (=module name)
            @param name: name of the component (=without prefix)

        """

        joinby = attr.get("joinby", None)
        if joinby:
            component = S3ResourceComponent(self.db, prefix, name, **attr)
            hook = self.components.get(name, Storage())
            if isinstance(joinby, dict):
                for tablename in joinby:
                    hook[tablename] = Storage(
                        _joinby = ("id", joinby[tablename]),
                        _component = component)
            elif isinstance(joinby, str):
                hook._joinby=joinby
                hook._component=component
            else:
                raise SyntaxError("Invalid join key(s)")
            self.components[name] = hook
            return component
        else:
            raise SyntaxError("Join key(s) must be defined.")


    # -------------------------------------------------------------------------
    def get_component(self, prefix, name, component_name):

        """ Retrieves a component of a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        hook = self.components.get(component_name, None)
        if table and hook:
            h = hook.get(tablename, None)
            if h:
                pkey, fkey = h._joinby
                component = h._component
                return (hook[tablename]._component, pkey, fkey)
            else:
                nkey = hook._joinby
                component = hook._component
                if nkey and nkey in table.fields:
                    return (component, nkey, nkey)

        return (None, None, None)


    # -------------------------------------------------------------------------
    def get_components(self, prefix, name):

        """ Retrieves all components related to a resource

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        components = []
        if table:
            for hook in self.components.values():
                if tablename in hook:
                    h = hook[tablename]
                    pkey, fkey = h._joinby
                    component = h._component
                    components.append((component, pkey, fkey))
                else:
                    nkey = hook._joinby
                    component = hook._component
                    if nkey and nkey in table.fields:
                        components.append((component, nkey, nkey))

        return components


    # -------------------------------------------------------------------------
    def has_components(self, prefix, name):

        """ Check whether the specified resource has components

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)

        """

        tablename = "%s_%s" % (prefix, name)
        table = self.db.get(tablename, None)

        h = self.components.get(name, None)
        if h and h._component and h._component.tablename == tablename:
            k = h._joinby
        else:
            k = None

        if table:
            for hook in self.components.values():
                if tablename in hook:
                    return True
                else:
                    nkey = hook._joinby
                    if nkey and nkey in table.fields and nkey != k:
                        return True

        return False


    # -------------------------------------------------------------------------
    def set_attr(self, component_name, name, value):

        """ Sets an attribute for a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute
            @param value: value for the attribute

            @todo 2.3: deprecate?

        """

        return self.components[component_name].set_attr(name, value)


    # -------------------------------------------------------------------------
    def get_attr(self, component_name, name):

        """ Retrieves an attribute value of a component

            @param component_name: name of the component (without prefix)
            @param name: name of the attribute

            @todo 2.3: deprecate?

        """

        return self.components[component_name].get_attr(name)


    # Resource Methods ========================================================

    def set_method(self, prefix, name,
                   component_name=None,
                   method=None,
                   action=None):

        """ Adds a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method
            @param action: function to invoke for this method

        """

        if not method:
            raise SyntaxError("No method specified")

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component:
                if method not in self.cmethods:
                    self.cmethods[method] = {}
                if component.tablename not in self.cmethods[method]:
                    self.cmethods[method][component.tablename] = {}
                self.cmethods[method][component.tablename][tablename] = action


    # -------------------------------------------------------------------------
    def get_method(self, prefix, name, component_name=None, method=None):

        """ Retrieves a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component (=without prefix)
            @param method: name of the method

        """

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None
        else:
            component = self.get_component(prefix, name, component_name)[0]
            if component and \
               method in self.cmethods and \
               component.tablename in self.cmethods[method] and \
               tablename in self.cmethods[method][component.tablename]:
                return self.cmethods[method][component.tablename][tablename]
            else:
                return None


    # Resource configuration ==================================================

    def configure(self, table, **attr):

        """ Update the extra configuration of a table

            @param table: the table
            @param attr: dict of attributes to update

        """

        cfg = self.config.get(table._tablename, Storage())
        cfg.update(attr)
        self.config[table._tablename] = cfg


    # -------------------------------------------------------------------------
    def get_config(self, table, key, default=None):

        """ Reads a configuration attribute of a resource

            @param table: the resource DB table
            @param key: the key (name) of the attribute

        """

        if table._tablename in self.config:
            return self.config[table._tablename].get(key, default)
        else:
            return default


    # -------------------------------------------------------------------------
    def clear_config(self, table, *keys):

        """ Removes configuration attributes of a resource

            @param table: the resource DB table
            @param keys: keys of attributes to remove (maybe multiple)

        """

        if not keys:
            if table._tablename in self.config:
                del self.config[table._tablename]
        else:
            if table._tablename in self.config:
                for k in keys:
                    if k in self.config[table._tablename]:
                        del self.config[table._tablename][k]


    # Super-Entity API ========================================================

    def super_entity(self, tablename, key, types, *fields, **args):

        """ Create a new super-entity table

            @param tablename: the tablename
            @param key: name of the primary key
            @param types: a dictionary of instance types
            @param fields: any shared fields
            @param args: table arguments (e.g. migrate)

        """

        # postgres workaround
        if self.db._dbname == "postgres":
            sequence_name = "%s_%s_Seq" % (tablename, key)
        else:
            sequence_name = None

        table = self.db.define_table(tablename,
                                     Field(key, "id",
                                           readable=False,
                                           writable=False),
                                     Field("deleted", "boolean",
                                           readable=False,
                                           writable=False,
                                           default=False),
                                     Field("instance_type",
                                           readable=False,
                                           writable=False),
                                     Field("uuid", length=128,
                                           readable=False,
                                           writable=False),
                                     sequence_name=sequence_name,
                                     *fields, **args)

        table.instance_type.represent = lambda opt: types.get(opt, opt)

        return table


    # -------------------------------------------------------------------------
    def super_key(self, super):

        """ Get the name of the key for a super-entity

            @param super: the super-entity table

        """

        for key in super.fields:
            if str(super[key].type) == "id":
                return key

        raise SyntaxError("No id-type key found in %s" % super._tablename)


    # -------------------------------------------------------------------------
    def super_link(self, super):

        """ Get a foreign key field for a super-entity

            @param super: the super-entity table

        """

        key = self.super_key(super)

        return Field(key, super,
                     requires = IS_EMPTY_OR(IS_IN_DB(self.db, "%s.%s" %
                                                    (super._tablename, key))),
                     readable = False,
                     writable = False,
                     ondelete = "RESTRICT")


    # -------------------------------------------------------------------------
    def update_super(self, table, record):

        """ Updates the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record

        """

        # Get the record
        id = record.get("id", None)
        record = self.db(table.id == id).select(table.ALL, limitby=(0, 1)).first()
        if not record:
            return True

        # Get the super-entities of this table
        super = self.get_config(table, "super_entity")
        if not super:
            return True
        elif not isinstance(super, (list, tuple)):
            super = [super]

        for s in super:

            # Get the key
            for key in s.fields:
                if str(s[key].type) == "id":
                    break

            # Get the shared field map
            shared = self.get_config(table, "%s_fields" % s._tablename)
            if shared:
                data = dict([(f, record[shared[f]])
                             for f in shared if shared[f] in record and f in s.fields])
            else:
                data = dict([(f, record[f])
                             for f in s.fields if f in record])

            # Add instance type and deletion status
            data.update(instance_type=table._tablename,
                        deleted=record.get("deleted", False))

            # UID
            uid=record.get("uuid", None)
            data.update(uuid=uid)

            # Update records
            row = self.db(s.uuid == uid).select(s[key], limitby=(0, 1)).first()
            if row:
                k = {key:row[key]}
                self.db(s[key] == row[key]).update(**data)
                if record[key] != row[key]:
                    self.db(table.id==id).update(k)
            else:
                k = s.insert(**data)
                if k:
                    self.db(table.id == id).update(**{key:k})

        return True


    # -------------------------------------------------------------------------
    def delete_super(self, table, record):

        """ Removes the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record

        """

        super = self.get_config(table, "super_entity")
        if not super:
            return True
        if not isinstance(super, (list, tuple)):
            super = [super]

        uid = record.get("uuid", None)
        if uid:
            for s in super:
                if "deleted" in s.fields:
                    self.db(s.uuid == uid).update(deleted=True)

        return True


# *****************************************************************************
