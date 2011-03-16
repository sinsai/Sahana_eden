# -*- coding: utf-8 -*-

""" Data Model Extensions (S3XRC)

    @version: 2.3.4
    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}

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

__all__ = ["S3ResourceModel", "S3ResourceLinker"]

from gluon.storage import Storage
from gluon.sql import Table, Field
from gluon.validators import IS_EMPTY_OR, IS_IN_DB

# *****************************************************************************
class S3ResourceModel(object):

    """
    S3 Model extensions

    """

    def __init__(self, db):
        """
        Constructor

        @param db: the database

        """

        self.db = db
        self.components = {}
        self.config = Storage()
        self.methods = {}
        self.cmethods = {}


    # Components ==============================================================

    def add_component(self, prefix, name, joinby=None, multiple=True):
        """
        Define a component join

        @param prefix: prefix of the component name (=module name)
        @param name: name of the component (=without prefix)
        @param joinby: join key, or dict of join keys

        """

        if joinby:
            tablename = "%s_%s" % (prefix, name)
            table = self.db.get(tablename, None)
            if not table:
                raise SyntaxError("Undefined table: %s" % tablename)
            component = Storage(prefix = prefix,
                                name = name,
                                tablename = tablename,
                                table = table,
                                multiple = multiple)
            hook = self.components.get(name, Storage())
            if isinstance(joinby, dict):
                for tn in joinby:
                    key = joinby[tn]
                    if key not in table.fields:
                        raise SyntaxError("Undefined key: %s.%s" %
                                          (tablename, key))
                    hook[tn] = Storage(_joinby = ("id", key),
                                       _component = component)
            elif isinstance(joinby, str):
                if joinby not in table.fields:
                    raise SyntaxError("Undefined key: %s.%s" %
                                      (tablename, joinby))
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
        """
        Retrieve a component join

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
        """
        Retrieves all component joins for a table

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
        """
        Check whether the specified resource has components

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
    def primary_resources(self, prefixes=[]):
        """
        Get primay resources (tablenames)

        """

        tablenames = []
        for t in self.db.tables:
            if "_" not in t:
                continue
            else:
                prefix, name = t.split("_", 1)
            table = self.db[t]

            if "id" in table.fields and prefix in prefixes:
                is_component = False
                if not self.has_components(prefix, name):
                    hook = self.components.get(name, None)
                    if hook:
                        link = hook.get("_component", None)
                        if link and link.tablename == t:
                            continue
                        for h in hook.values():
                            if isinstance(h, dict):
                                link = h.get("_component", None)
                                if link and link.tablename == t:
                                    is_component = True
                                    break
                        if is_component:
                            continue
                tablenames.append(t)

        return tablenames


    # Resource Methods ========================================================

    def set_method(self, prefix, name,
                   component_name=None,
                   method=None,
                   action=None):
        """
        Adds a custom method for a resource or component

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
        """
        Retrieves a custom method for a resource or component

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
        """
        Update the extra configuration of a table

        @param table: the table
        @param attr: dict of attributes to update

        """

        cfg = self.config.get(table._tablename, Storage())
        cfg.update(attr)
        self.config[table._tablename] = cfg


    # -------------------------------------------------------------------------
    def get_config(self, table, key, default=None):
        """
        Reads a configuration attribute of a resource

        @param table: the resource DB table
        @param key: the key (name) of the attribute

        """

        if table._tablename in self.config:
            return self.config[table._tablename].get(key, default)
        else:
            return default


    # -------------------------------------------------------------------------
    def clear_config(self, table, *keys):
        """
        Removes configuration attributes of a resource

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
        """
        Define a super-entity table

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
    @staticmethod
    def super_key(supertable):
        """
        Get the name of the key for a super-entity

        @param supertable: the super-entity table

        """

        try:
            return supertable._id.name
        except AttributeError: pass

        raise SyntaxError("No id-type key found in %s" % supertable._tablename)


    # -------------------------------------------------------------------------
    def super_link(self, supertable):
        """
        Get a foreign key field for a super-entity

        @param supertable: the super-entity table

        """

        key = self.super_key(supertable)

        return Field(key, supertable,
                     requires = IS_EMPTY_OR(IS_IN_DB(self.db, "%s.%s" %
                                                    (supertable._tablename, key))),
                     readable = False,
                     writable = False,
                     ondelete = "RESTRICT")


    # -------------------------------------------------------------------------
    def update_super(self, table, record):
        """
        Updates the super-entity links of an instance record

        @param table: the instance table
        @param record: the instance record

        """

        # Get the record
        id = record.get("id", None)
        record = self.db(table.id == id).select(table.ALL, limitby=(0, 1)).first()
        if not record:
            return True

        # Get the super-entities of this table
        supertable = self.get_config(table, "super_entity")
        if not supertable:
            return True
        elif not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

        for s in supertable:

            # Get the key
            for key in s.fields:
                if str(s[key].type) == "id":
                    break

            # Get the shared field map
            shared = self.get_config(table, "%s_fields" % s._tablename)
            if shared:
                data = dict([(f, record[shared[f]])
                             for f in shared
                             if shared[f] in record and f in s.fields and f != key])
            else:
                data = dict([(f, record[f])
                             for f in s.fields if f in record and f != key])

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
                    self.db(table.id == id).update(**k)
            else:
                k = s.insert(**data)
                if k:
                    self.db(table.id == id).update(**{key:k})

        return True


    # -------------------------------------------------------------------------
    def delete_super(self, table, record):
        """
        Removes the super-entity links of an instance record

        @param table: the instance table
        @param record: the instance record

        """

        supertable = self.get_config(table, "super_entity")
        if not supertable:
            return True
        if not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

        uid = record.get("uuid", None)
        if uid:
            for s in supertable:
                if "deleted" in s.fields:
                    self.db(s.uuid == uid).update(deleted=True)

        return True


# *****************************************************************************
class S3ResourceLinker(object):

    """
    Hyperlinks between resources

    """

    def __init__(self, manager):
        """
        Constructor

        @param manager: the S3ResourceController

        """

        self.db = manager.db
        self.tablename = manager.rlink_tablename
        migrate = manager.migrate

        self.table = self.db.get(self.tablename, None)
        if not self.table:
            self.table = self.db.define_table(self.tablename,
                                              Field("link_class", length=128),
                                              Field("origin_table"),
                                              Field("origin_id", "list:integer"),
                                              Field("target_table"),
                                              Field("target_id", "integer"),
                                              migrate=migrate)


    # -------------------------------------------------------------------------
    def link(self, from_table, from_id, to_table, to_id, link_class=None):
        """
        Create a hyperlink between resources

        @param from_table: the originating table
        @param from_id: ID or list of IDs of the originating record(s)
        @param to_table: the target table
        @param to_id: ID or list of IDs of the target record(s)
        @param link_class: link class name

        @returns: a list of record IDs of the created links

        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename
        links = []
        if not from_id:
            return links
        elif not isinstance(from_id, (list, tuple)):
            o_id = [str(from_id)]
        else:
            o_id = map(str, from_id)
        if not to_id:
            return links
        elif not isinstance(to_id, (list, tuple)):
            t_id = [str(to_id)]
        else:
            t_id = map(str, to_id)
        table = self.table
        query = ((table.origin_table == o_tn) &
                 (table.target_table == t_tn) &
                 (table.link_class == link_class) &
                 (table.target_id.belongs(t_id)))
        rows = self.db(query).select()
        rows = dict([(str(r.target_id), r) for r in rows])
        success = True
        for target_id in t_id:
            if target_id in rows:
                row = rows[target_id]
                ids = map(str, row.origin_id)
                add = [i for i in o_id if i not in ids]
                ids += add
                row.update_record(origin_id=ids)
                links.append(row.id)
            else:
                row = table.insert(origin_table=o_tn,
                                   target_table=t_tn,
                                   link_class=link_class,
                                   target_id=target_id,
                                   origin_id=o_id)
                links.append(row)
        return links


    # -------------------------------------------------------------------------
    def unlink(self, from_table, from_id, to_table, to_id, link_class=None):
        """
        Remove a hyperlink between resources

        @param from_table: the originating table
        @param from_id: ID or list of IDs of the originating record(s)
        @param to_table: the target table
        @param to_id: ID or list of IDs of the target record(s)
        @param link_class: link class name

        @note: None for from_id or to_id means *any* record

        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename

        table = self.table
        query = ((table.origin_table == o_tn) &
                 (table.target_table == t_tn) &
                 (table.link_class == link_class))
        q = None
        if from_id is not None:
            if not isinstance(from_id, (list, tuple)):
                o_id = [str(from_id)]
            else:
                o_id = map(str, from_id)
            for origin_id in o_id:
                iq = table.origin_id.contains(origin_id)
                if q is None:
                    q = iq
                else:
                    q = q | iq
        else:
            o_id = None
        if q is not None:
            query = query & (q)
        q = None
        if to_id is not None:
            if not isinstance(to_id, (list, tuple)):
                q = table.target_id == str(to_id)
            else:
                t_id = map(str, to_id)
                q = table.target_id.belongs(t_id)
        if q is not None:
            query = query & (q)
        rows = self.db(query).select()
        for row in rows:
            if o_id:
                ids = [i for i in row.origin_id if str(i) not in o_id]
            else:
                ids = []
            if ids:
                row.update_record(origin_id=ids)
            else:
                row.delete_record()
        return


    # -------------------------------------------------------------------------
    def get_origin_query(self, from_table, to_table, to_id,
                         link_class=None,
                         union=False):
        """
        Get a query for the origin table to retrieve records that are
        linked to a set of target table records.

        @param from_table: the origin table
        @param to_table: the target table
        @param to_id: target record ID or list of target record IDs
        @param link_class: link class name
        @param union: retrieve a union (True) or an intersection (False, default)
                        of all sets of links (in case of multiple target records)

        @note: None for to_id means *any* record

        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename

        table = self.table
        if not to_id:
            query = (table.target_id != None)
        elif not isinstance(to_id, (list, tuple)):
            query = (table.target_id == to_id)
        else:
            query = (table.target_id.belongs(to_id))
        query = (table.origin_table == o_tn) & \
                (table.target_table == t_tn) & \
                (table.link_class == link_class) & query
        ids = []
        rows = self.db(query).select(table.origin_id)
        for row in rows:
            if union:
                add = [i for i in row.origin_id if i not in ids]
                ids += add
            elif not ids:
                ids = row.origin_id
            else:
                ids = [i for i in ids if i in row.origin_id]
        if ids and len(ids) == 1:
            mq = (from_table.id == ids[0])
        elif ids:
            mq = (from_table.id.belongs(ids))
        else:
            mq = (from_table.id == None)
        return mq


    # -------------------------------------------------------------------------
    def get_target_query(self, from_table, from_id, to_table,
                         link_class=None,
                         union=False):
        """
        Get a query for the target table to retrieve records that are
        linked to a set of origin table records.

        @param from_table: the origin table
        @param from_id: origin record ID or list of origin record IDs
        @param to_table: the target table
        @param link_class: link class name
        @param union: retrieve a union (True) or an intersection (False, default)
                        of all sets of links (in case of multiple origin records)

        @note: None for from_id means *any* record

        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename
        table = self.table
        if not from_id:
            query = (table.origin_id != None)
        elif not isinstance(from_id, (list, tuple)):
            query = (table.origin_id.contains(from_id))
        else:
            q = None
            for origin_id in from_id:
                iq = table.origin_id.contains(origin_id)
                if q and union:
                    q = q | iq
                elif q and not union:
                    q = q & iq
                else:
                    q = iq
            if q:
                query = (q)
        query = (table.origin_table == o_tn) & \
                (table.target_table == t_tn) & \
                (table.link_class == link_class) & query
        rows = self.db(query).select(table.target_id, distinct=True)
        ids = [row.target_id for row in rows]
        if ids and len(ids) == 1:
            mq = (to_table.id == ids[0])
        elif ids:
            mq = (to_table.id.belongs(ids))
        else:
            mq = (to_table.id == None)
        return mq


# *****************************************************************************
