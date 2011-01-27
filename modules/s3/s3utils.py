# -*- coding: utf-8 -*-

""" Utilities

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <fran[at]aidiq.com>
    @author: Michael Howden <michael[at]aidiq.com>
    @author: Pradnya Kulkarni

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

__all__ = ["URL2",
           "URL3",
           "getBrowserName",
           "s3_debug",
           "shn_split_multi_value",
           "shn_get_db_field_value",
           "jaro_winkler",
           "jaro_winkler_distance_row",
           "soundex",
           "docChecksum"]

import sys
import os
import re
import hashlib

from gluon.html import *
from gluon.http import *
from gluon.validators import *
from gluon.sqlhtml import *

try:
    from xlrd import *
except ImportError:
    import sys
    # On server shows up in Apache error log
    print >> sys.stderr, "WARNING: %s: XLRD not installed" % __name__

# Modified versions of URL from gluon/html.py
# we need simplified versions for our jquery functions
def URL2(a=None, c=None, r=None):
    """
    example:

    >>> URL(a="a",c="c")
    "/a/c"

    generates a url "/a/c" corresponding to application a & controller c
    If r=request is passed, a & c are set, respectively,
    to r.application, r.controller

    The more typical usage is:

    URL(r=request) that generates a base url with the present application and controller.

    The function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if c:
        controller = c
    if not (application and controller):
        raise SyntaxError, "not enough information to build the url"
    #other = ""
    url = "/%s/%s" % (application, controller)
    return url


def URL3(a=None, r=None):
    """
    example:

    >>> URL(a="a")
    "/a"

    generates a url "/a" corresponding to application a
    If r=request is passed, a is set
    to r.application

    The more typical usage is:

    URL(r=request) that generates a base url with the present application.

    The controller & function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if not (application and controller):
        raise SyntaxError, "not enough information to build the url"
    #other = ""
    url = "/%s" % application
    return url


def getBrowserName(userAgent):
    "Determine which browser is being used."
    if userAgent.find("MSIE") > -1:
        return "IE"
    elif userAgent.find("Firefox") > -1:
        return "Firefox"
    elif userAgent.find("Gecko") > -1:
        return "Mozilla"
    else:
        return "Unknown"


def s3_debug(message, value=None):

    """
       Debug Function (same name/parameters as JavaScript one)

       Provide an easy, safe, systematic way of handling Debug output
       (print to stdout doesn't work with WSGI deployments)
    """

    try:
        output = "S3 Debug: " + str(message)
        if value:
            output += ": " + str(value)
    except:
        output = "S3 Debug: " + unicode(message)
        if value:
            output += ": " + unicode(value)

    print >> sys.stderr, output


def shn_split_multi_value(value):
    """
    @author: Michael Howden (michael@aidiq.com)

    Converts a series of numbers delimited by |, or already in a string into a list

    If value = None, returns []

    """

    if not value:
        return []

    elif isinstance(value, ( str ) ):
        if "[" in value:
            #Remove internal lists
            value = value.replace("[", "")
            value = value.replace("]", "")
            value = value.replace("'", "")
            value = value.replace('"', "")
            return eval("[" + value + "]")
        else:
            return re.compile('[\w\-:]+').findall(str(value))
    else:
        return [str(value)]


def shn_get_db_field_value(db,
                           table,
                           field,
                           look_up,
                           look_up_field = "id",
                           match_case = True):
    """

    @author: Michael Howden (michael@aidiq.com)

    @summary:
        Returns the value of <field> from the first record in <table_name>
        with <look_up_field> = <look_up>

    @param table: The name of the table
    @param field: the field to find the value from
    @param look_up: the value to find
    @param look_up_field: the field to find <look_up> in
    @type match_case: boolean

    @returns:
        - Field Value if there is a record
        - None - if there is no matching record

    Example::
        shn_get_db_field_value("or_organisation", "id",
                               look_up = "UNDP",
                               look_up_field = "name" )

    """
    lt = db[table]
    lf = lt[look_up_field]
    if match_case or str(lf.type) != "string":
        query = (lf == look_up)
    else:
        query = (lf.lower() == str.lower(look_up))
    if "deleted" in lt:
        query = (lt.deleted == False) & query
    row = db(query).select(field, limitby=(0, 1)).first()
    return row and row[field] or None


def jaro_winkler(str1, str2):
    """
    Return Jaro_Winkler distance of two strings (between 0.0 and 1.0)

    Used as a measure of similarity between two strings

    @see http://en.wikipedia.org/wiki/Jaro-Winkler_distance

    @param str1: the first string
    @param str2: the second string

    @author: Pradnya Kulkarni

    """

    jaro_winkler_marker_char = chr(1)

    if (str1 == str2):
        return 1.0

    if str1 == None:
        return 0

    if str2 == None:
        return 0

    len1 = len(str1)
    len2 = len(str2)
    halflen = max(len1, len2) / 2 - 1

    ass1  = ""  # Characters assigned in str1
    ass2  = ""  # Characters assigned in str2
    workstr1 = str1
    workstr2 = str2

    common1 = 0    # Number of common characters
    common2 = 0

    # If the type is list  then check for each item in the list and find out final common value
    if isinstance(workstr2, list):
        for item1 in workstr1:
            for item2 in workstr2:
                for i in range(len1):
                    start = max(0, i - halflen)
                    end = min(i + halflen + 1, len2)
                    index = item2.find(item1[i], start, end)
                    if (index > -1):
                        # Found common character
                        common1 += 1
                    ass1 = ass1 + item1[i]
                    item2 = item2[:index] + jaro_winkler_marker_char + item2[index + 1:]
    else:
        for i in range(len1):
            start = max(0, i - halflen)
            end   = min(i + halflen + 1, len2)
            index = workstr2.find(str1[i], start, end)
            if (index > -1):
                # Found common character
                common1 += 1
            ass1 = ass1 + str1[i]
            workstr2 = workstr2[:index] + jaro_winkler_marker_char + workstr2[index + 1:]

    # If the type is list
    if isinstance(workstr1, list):
        for item1 in workstr2:
            for item2 in workstr1:
                for i in range(len2):
                    start = max(0, i - halflen)
                    end = min(i + halflen + 1, len1)
                    index = item2.find(item1[i], start, end)
                    if (index > -1):
                        # Found common character
                        common2 += 1
                    ass2 = ass2 + item1[i]
                    item1 = item1[:index] + jaro_winkler_marker_char + item1[index + 1:]
    else:
        for i in range(len2):
            start = max(0, i - halflen)
            end   = min(i + halflen + 1, len1)
            index = workstr1.find(str2[i], start, end)
            if (index > -1):
                # Found common character
                common2 += 1
            ass2 = ass2 + str2[i]
            workstr1 = workstr1[:index] + jaro_winkler_marker_char + workstr1[index + 1:]

    if (common1 != common2):
        common1 = float(common1 + common2) / 2.0

    if (common1 == 0):
        return 0.0

    # Compute number of transpositions
    if (len1 == len2):
        transposition = 0
        for i in range(len(ass1)):
            if (ass1[i] != ass2[i]):
                transposition += 1
        transposition = transposition / 2.0
    elif (len1 > len2):
        transposition = 0
        for i in range(len(ass2)): #smaller length one
            if (ass1[i] != ass2[i]):
                transposition += 1
        while (i < len1):
            transposition += 1
            i += 1
        transposition = transposition / 2.0
    elif (len1 < len2):
        transposition = 0
        for i in range(len(ass1)): #smaller length one
            if (ass1[i] != ass2[i]):
                transposition += 1
        while (i < len2):
            transposition += 1
            i += 1
        transposition = transposition / 2.0

    # Compute number of characters common to beginning of both strings, for Jaro-Winkler distance
    minlen = min(len1, len2)
    for same in range(minlen + 1):
        if (str1[:same] != str2[:same]):
            break
    same -= 1
    if (same > 4):
        same = 4

    common1 = float(common1)
    w = 1. / 3. * (common1 / float(len1) + common1 / float(len2) + (common1 - transposition) / common1)

    wn = w + same * 0.1 * (1.0 - w)
    if (wn < 0.0):
        wn = 0.0
    elif (wn > 1.0):
        wn = 1.0
    return wn


def jaro_winkler_distance_row(row1, row2):
    """
    Calculate the percentage match for two db records

    @author: Pradnya Kulkarni

    """

    dw = 0
    num_similar = 0
    if len(row1) != len(row2):
            #print "The records columns does not match."
            return
    for x in range(0, len(row1)):
        str1 = row1[x]    # get row fields
        str2 = row2[x]    # get row fields
        dw += jaro_winkler(str1, str2) #Calculate match value for two column values

    dw = dw / len(row1) # Average of all column match value.
    dw = dw * 100       # Convert to percentage
    return dw


def soundex(name, len=4):
    """
    Code referenced from http://code.activestate.com/recipes/52213-soundex-algorithm/

    @author: Pradnya Kulkarni

    """

    # digits holds the soundex values for the alphabet
    digits = "01230120022455012623010202"
    sndx = ""
    fc = ""

    # Translate alpha chars in name to soundex digits
    for c in name.upper():
        if c.isalpha():
            if not fc:
                # remember first letter
                fc = c
            d = digits[ord(c)-ord("A")]
            # duplicate consecutive soundex digits are skipped
            if not sndx or (d != sndx[-1]):
                sndx += d

    # replace first digit with first alpha character
    sndx = fc + sndx[1:]

    # remove all 0s from the soundex code
    sndx = sndx.replace("0", "")

    # return soundex code padded to len characters
    return (sndx + (len * "0"))[:len]


def docChecksum(docStr):
    """
    Calculate a checksum for a file

    """

    converted = hashlib.sha1(docStr).hexdigest()
    return converted
