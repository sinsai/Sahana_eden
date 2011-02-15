# -*- coding: utf-8 -*-

""" Custom Validators

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <fran[at]aidiq.com>
    @author: Dominic König <dominic[at]aidiq.com>
    @author: sunneach

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

__all__ = ["IS_LAT",
           "IS_LON",
           "IS_HTML_COLOUR",
           "THIS_NOT_IN_DB",
           "IS_UTC_OFFSET",
           "IS_UTC_DATETIME",
           "IS_ONE_OF",
           "IS_ONE_OF_EMPTY",
           "IS_NOT_ONE_OF",
           "IS_ACL"]

import time
import uuid
import re
from datetime import datetime, timedelta
from gluon.validators import Validator, IS_MATCH, IS_NOT_IN_DB, IS_IN_SET

def options_sorter(x, y):
    return (str(x[1]).upper() > str(y[1]).upper() and 1) or -1

class IS_LAT(object):
    """
    example:

    INPUT(_type="text", _name="name", requires=IS_LAT())

    latitude has to be in degrees between -90 & 90
    """
    def __init__(self,
            error_message = "Latitude/Northing should be between -90 & 90!"):
        self.minimum = -90
        self.maximum = 90
        self.error_message = error_message
    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

class IS_LON(object):
    """
    example:

    INPUT(_type="text", _name="name" ,requires=IS_LON())

    longitude has to be in degrees between -180 & 180
    """
    def __init__(self,
            error_message = "Longitude/Easting should be between -180 & 180!"):
        self.minimum = -180
        self.maximum = 180
        self.error_message = error_message
    def __call__(self, value):
        try:
            value = float(value)
            if self.minimum <= value <= self.maximum:
                return (value, None)
        except ValueError:
            pass
        return (value, self.error_message)

# -----------------------------------------------------------------------------
class IS_HTML_COLOUR(IS_MATCH):
    """
    example::

        INPUT(_type="text", _name="name", requires=IS_HTML_COLOUR())

    """

    def __init__(self, error_message="must be a 6 digit hex code!"):
        IS_MATCH.__init__(self, "^[0-9a-fA-F]{6}$", error_message)

# -----------------------------------------------------------------------------
class THIS_NOT_IN_DB(object):
    """
    Unused currently since doesn't quite work.
    See: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540
    """
    def __init__(self, dbset, field, this,
            error_message = "value already in database!"):
        if hasattr(dbset, "define_table"):
            self.dbset = dbset()
        else:
            self.dbset = dbset
        self.field = field
        self.value = this
        self.error_message = error_message
        self.record_id = 0
    def set_self_id(self, id):
        self.record_id = id
    def __call__(self, value):
        tablename, fieldname = str(self.field).split(".")
        field = self.dbset._db[tablename][fieldname]
        rows = self.dbset(field == self.value).select(limitby=(0, 1))
        if len(rows)>0 and str(rows[0].id) != str(self.record_id):
            return (self.value, self.error_message)
        return (value, None)

regex1 = re.compile("[\w_]+\.[\w_]+")
regex2 = re.compile("%\((?P<name>[^\)]+)\)s")

# IS_ONE_OF_EMPTY -------------------------------------------------------------------
# by sunneach 2010-02-03
# copy of nursix's IS_ONE_OF with removed 'options' method
class IS_ONE_OF_EMPTY(Validator):
    """
        Filtered version of IS_IN_DB():

        validates a given value as key of another table, filtered by the 'filterby'
        field for one of the 'filter_opts' options (=a selective IS_IN_DB())

        NB Filtering isn't active in GQL.

        For the dropdown representation:

        'label' can be a string template for the record, or a set of field
        names of the fields to be used as option labels, or a function or lambda
        to create an option label from the respective record (which has to return
        a string, of course). The function will take the record as an argument

        No 'options' method as designed to be called next to an Autocomplete field so don't download a large dropdown unnecessarily.
    """

    def __init__(
        self,
        dbset,
        field,
        label=None,
        filterby=None,
        filter_opts=None,
        error_message="invalid value!",
        orderby=None,
        groupby=None,
        cache=None,
        multiple=False,
        zero="",
        sort=False,
        _and=None,
        ):

        if hasattr(dbset, "define_table"):
            self.dbset = dbset()
        else:
            self.dbset = dbset
        self.field = field
        (ktable, kfield) = str(self.field).split(".")
        if not label:
            label = "%%(%s)s" % kfield
        if isinstance(label, str):
            if regex1.match(str(label)):
                label = "%%(%s)s" % str(label).split(".")[-1]
            ks = regex2.findall(label)
            if not kfield in ks:
                ks += [kfield]
            fields = ["%s.%s" % (ktable, k) for k in ks]
        else:
            ks = [kfield]
            fields =[str(f) for f in self.dbset._db[ktable]]
        self.fields = fields
        self.label = label
        self.ktable = ktable
        if not kfield or not len(kfield):
            self.kfield = "id"
        else:
            self.kfield = kfield
        self.ks = ks
        self.error_message = error_message
        self.theset = None
        self.orderby = orderby
        self.groupby = groupby
        self.cache = cache
        self.multiple = multiple
        self.zero = zero
        self.sort = sort
        self._and = _and

        self.filterby = filterby
        self.filter_opts = filter_opts

    def set_self_id(self, id):
        if self._and:
            self._and.record_id = id

    def build_set(self):

        if self.ktable in self.dbset._db:

            _table = self.dbset._db[self.ktable]

            if self.dbset._db._dbname != "gql":
                orderby = self.orderby or ", ".join(self.fields)
                groupby = self.groupby
                dd = dict(orderby=orderby, groupby=groupby, cache=self.cache)
                if "deleted" in _table:
                    query = (_table["deleted"] == False)
                else:
                    query = (_table["id"] > 0)
                if self.filterby and self.filterby in _table:
                    if self.filter_opts:
                        query = query & (_table[self.filterby].belongs(self.filter_opts))
                    if not self.orderby:
                        dd.update(orderby=_table[self.filterby])
                records = self.dbset(query).select(*self.fields, **dd)
            else:
                import contrib.gql
                orderby = self.orderby\
                     or contrib.gql.SQLXorable("|".join([k for k in self.ks
                        if k != "id"]))
                dd = dict(orderby=orderby, cache=self.cache)
                records = \
                    self.dbset.select(self.dbset._db[self.ktable].ALL, **dd)
            self.theset = [str(r[self.kfield]) for r in records]
            #labels = []
            label = self.label
            try:
                labels = map(label, records)
            except TypeError:
                if isinstance(label, str):
                    labels = map(lambda r: label % dict(r), records)
                elif isinstance(label, (list, tuple)):
                    labels = map(lambda r: \
                                 " ".join([r[l] for l in label if l in r]),
                                 records)
                elif hasattr(label, '__call__'):
                    # Is a function
                    labels = map(label, records)
                elif "name" in _table:
                    labels = map(lambda r: r.name, records)
                else:
                    labels = map(lambda r: r[self.kfield], records)
            self.labels = labels
        else:
            self.theset = None
            self.labels = None

    #def options(self):
    #   "Removed as we don't want any options downloaded unnecessarily"

    def __call__(self, value):

        try:
            _table = self.dbset._db[self.ktable]
            deleted_q = ("deleted" in _table) and (_table["deleted"] == False) or False
            filter_opts_q = False
            if self.filterby and self.filterby in _table:
                if self.filter_opts:
                    filter_opts_q = _table[self.filterby].belongs(self.filter_opts)

            if self.multiple:
                if isinstance(value, list):
                    values = value
                elif isinstance(value, basestring) and \
                     value[0] == "|" and value[-1] == "|":
                    values = value[1:-1].split("|")
                elif value:
                    values = [value]
                else:
                    values = []

                if self.theset:
                    if not [x for x in values if not x in self.theset]:
                        return ("|%s|" % "|".join(values), None)
                    else:
                        return (value, self.error_message)
                else:
                    for v in values:
                        q = (_table[self.kfield] == v)
                        query = query is not None and query | q or q
                    if filter_opts_q != False:
                        query = query is not None and \
                                (filter_opts_q & (query)) or filter_opts_q
                    if deleted_q != False:
                        query = query is not None and \
                                (deleted_q & (query)) or deleted_q
                    if self.dbset(query).count() < 1:
                        return (value, self.error_message)
                    return ("|%s|" % "|".join(values), None)
            elif self.theset:
                if value in self.theset:
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
            else:
                values = [value]
                query = None
                for v in values:
                    q = (_table[self.kfield] == v)
                    query = query is not None and query | q or q
                if filter_opts_q != False:
                    query = query is not None and \
                            (filter_opts_q & (query)) or filter_opts_q
                if deleted_q != False:
                    query = query is not None and \
                            (deleted_q & (query)) or deleted_q
                if self.dbset(query).count():
                    if self._and:
                        return self._and(value)
                    else:
                        return (value, None)
        except:
            pass

        return (value, self.error_message)

# IS_ONE_OF -------------------------------------------------------------------
# added 2009-08-23 by nursix
# converted to subclass 2010-02-03 by sunneach: NO CHANGES in the method bodies
class IS_ONE_OF(IS_ONE_OF_EMPTY):

    """
    Extends IS_ONE_OF_EMPTY by restoring the 'options' method.

    """

    def options(self):

        self.build_set()
        items = [(k, self.labels[i]) for (i, k) in enumerate(self.theset)]
        if self.sort:
            items.sort(options_sorter)
        if self.zero != None and not self.multiple:
            items.insert(0,("", self.zero))
        return items


# -----------------------------------------------------------------------------
class IS_NOT_ONE_OF(IS_NOT_IN_DB):

    """
    Filtered version of IS_NOT_IN_DB()
        - understands the 'deleted' field.
        - makes the field unique (amongst non-deleted field)

    Example:
        - INPUT(_type="text", _name="name", requires=IS_NOT_ONE_OF(db, db.table))

    """

    def __call__(self, value):
        if value in self.allowed_override:
            return (value, None)
        (tablename, fieldname) = str(self.field).split(".")
        _table = self.dbset._db[tablename]
        field = _table[fieldname]
        query = (field == value)
        if "deleted" in _table:
            query = (_table["deleted"] == False) & query
        rows = self.dbset(query).select(limitby=(0, 1))
        if len(rows) > 0 and str(rows[0].id) != str(self.record_id):
            return (value, self.error_message)
        return (value, None)


# -----------------------------------------------------------------------------
class IS_UTC_OFFSET(Validator):
    """
    Validates a given string value as UTC offset in the format +/-HHMM

    @author: nursix

    @param error_message:   the error message to be returned

    @note:
        all leading parts of the string (before the trailing offset specification)
        will be ignored and replaced by 'UTC ' in the return value, if the string
        passes through.
    """

    def __init__(self,
        error_message="invalid UTC offset!"
        ):
        self.error_message = error_message

    @staticmethod
    def get_offset_value(offset_str):
        if offset_str and len(offset_str) >= 5 and \
            (offset_str[-5] == "+" or offset_str[-5] == "-") and \
            offset_str[-4:].isdigit():
            offset_hrs = int(offset_str[-5] + offset_str[-4:-2])
            offset_min = int(offset_str[-5] + offset_str[-2:])
            offset = 3600*offset_hrs + 60*offset_min
            return offset
        else:
            return None

    def __call__(self,value):

        if value and isinstance(value, str):
            _offset_str = value.strip()

            offset = self.get_offset_value(_offset_str)

            if offset is not None and offset>-86340 and offset <86340:
                # Add a leading 'UTC ',
                # otherwise leading '+' and '0' will be stripped away by web2py
                return ("UTC " + _offset_str[-5:], None)

        return (value, self.error_message)


# -----------------------------------------------------------------------------
#
class IS_UTC_DATETIME(Validator):
    """
    Validates a given value as datetime string and returns the corresponding
    UTC datetime.

    Example:
        - INPUT(_type="text", _name="name", requires=IS_UTC_DATETIME())

    @author: nursix

    @param format:          strptime/strftime format template string, for
                            directives refer to your strptime implementation
    @param error_message:   dict of error messages to be returned
    @param utc_offset:      offset to UTC in seconds, if not specified, the value
                            is considered to be UTC
    @param allow_future:    whether future date/times are allowed or not, if
                            set to False, all date/times beyond now+max_future
                            will fail
    @type allow_future:     boolean
    @param max_future:      the maximum acceptable future time interval in
                            seconds from now for unsynchronized local clocks

    @note:
        datetime has to be in the ISO8960 format YYYY-MM-DD hh:mm:ss, with an
        optional trailing UTC offset specified as +/-HHMM (+ for eastern, - for
        western timezones)

    """

    isodatetime = "%Y-%m-%d %H:%M:%S"

    def __init__(self,
        format=None,
        error_message=None,
        utc_offset=None,
        allow_future=True,
        max_future=900):

        self.format = format or self.isodatetime

        self.error_message = dict(
            format = "Required format: YYYY-MM-DD HH:MM:SS!",
            offset = "Invalid UTC offset!",
            future = "Future times not allowed!")

        if error_message and isinstance(error_message, dict):
            self.error_message["format"] = error_message.get("format", None) or self.error_message["format"]
            self.error_message["offset"] = error_message.get("offset", None) or self.error_message["offset"]
            self.error_message["future"] = error_message.get("future", None) or self.error_message["future"]
        elif error_message:
            self.error_message["format"] = error_message

        validate = IS_UTC_OFFSET()
        offset, error = validate(utc_offset)

        if error:
            self.utc_offset = "UTC +0000" # fallback to UTC
        else:
            self.utc_offset = offset

        self.allow_future = allow_future
        self.max_future = max_future

    def __call__(self, value):

        _dtstr = value.strip()

        if len(_dtstr) > 6 and \
            (_dtstr[-6:-4] == " +" or _dtstr[-6:-4] == " -") and \
            _dtstr[-4:].isdigit():
            # UTC offset specified in dtstr
            dtstr = _dtstr[0:-6]
            _offset_str = _dtstr[-5:]
        else:
            # use default UTC offset
            dtstr = _dtstr
            _offset_str = self.utc_offset

        offset_hrs = int(_offset_str[-5] + _offset_str[-4:-2])
        offset_min = int(_offset_str[-5] + _offset_str[-2:])
        offset = 3600 * offset_hrs + 60 * offset_min

        # Offset must be in range -1439 to +1439 minutes
        if offset < -86340 or offset > 86340:
            return (dt, self.error_message["offset"])

        try:
            (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(dtstr, str(self.format))
            dt = datetime(y, m, d, hh, mm, ss)
        except:
            try:
                (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(dtstr+":00", str(self.format))
                dt = datetime(y, m, d, hh, mm, ss)
            except:
                return(value, self.error_message["format"])

        if self.allow_future:
            return (dt, None)
        else:
            latest = datetime.utcnow() + timedelta(seconds=self.max_future)
            dt_utc = dt - timedelta(seconds=offset)
            if dt_utc > latest:
                return (dt_utc, self.error_message["future"])
            else:
                return (dt_utc, None)

    def formatter(self, value):
        # Always format with trailing UTC offset
        return value.strftime(str(self.format)) + " +0000"


# -----------------------------------------------------------------------------
class IS_ACL(IS_IN_SET):

    """
    Validator for ACLs

    @attention: Incomplete! Does not validate yet, but just convert.

    @author: Dominic König <dominic@aidiq.com>

    """

    def __call__(self, value):
        """
        Validation

        @param value: the value to validate

        """

        if not isinstance(value, (list, tuple)):
            value = [value]

        acl = 0x0000
        for v in value:
            try:
                flag = int(v)
            except (ValueError, TypeError):
                flag = 0x0000
            else:
                acl |= flag

        return (acl, None)

# -----------------------------------------------------------------------------
