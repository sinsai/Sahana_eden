#!/usr/bin/env python
# coding: utf8
"""
    duplicator 
    
    @author: Pradnya Kulkarni
"""
try:
    from xlrd import *
except ImportError:
    import sys
    # On server shows up in Apache error log
    #print >> sys.stderr, "WARNING: %s: XLRD not installed" % __name__

import os
import hashlib
import math
#from gluon.html import *
#from gluon.http import *
#from gluon.validators import *
#from gluon.sqlhtml import *
# request, response, session, cache, T, db(s)
# must be passed and cannot be imported!

def foo(str1,str2):
    print "Hello"

    '''
       Used as a measure of similarity between two strings,
       see http://en.wikipedia.org/wiki/Jaro-Winkler_distance
    '''
    
def jaro_winkler(str1, str2):
    """
        Return Jaro_Winkler distance of two strings (between 0.0 and 1.0)

        ARGUMENTS:
          str1  The first string
          str2  The second string
    """

    jaro_winkler_marker_char = chr(1)

    if (str1 == str2):
        return 1.0
    #print str1
    #print str2
    
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
    if isinstance(workstr2,list):
    	for item1 in workstr1:
    		for item2 in workstr2:
    			for i in range(len1):
    				start = max(0, i - halflen)
        	                end   = min(i + halflen + 1, len2)
				index = item2.find(item1[i], start, end)
				if (index > -1):    # Found common character
				    common1 += 1
				ass1 = ass1 + item1[i]
				item2 = item2[:index] + jaro_winkler_marker_char + item2[index + 1:]        	
    else:
	    for i in range(len1):
		start = max(0, i - halflen)
		end   = min(i + halflen + 1, len2)
		index = workstr2.find(str1[i], start, end)
		if (index > -1):    # Found common character
		    common1 += 1
		ass1 = ass1 + str1[i]
		workstr2 = workstr2[:index] + jaro_winkler_marker_char + workstr2[index + 1:]
    		
    # If the type is list 		
    if isinstance(workstr1,list):
    	for item1 in workstr2:
    		for item2 in workstr1:
    			for i in range(len2):
				start = max(0, i - halflen)
				end   = min(i + halflen + 1, len1)
				index = item2.find(item1[i], start, end)
				#print 'len2', str2[i], start, end, index, ass1, workstr1, common2
				if (index > -1):    # Found common character
				    common2 += 1
				#ass2 += item1[i]
				ass2 = ass2 + item1[i]
				item1 = item1[:index] + jaro_winkler_marker_char + item1[index + 1:]
    else:
	    for i in range(len2):
		start = max(0, i - halflen)
		end   = min(i + halflen + 1, len1)
		index = workstr1.find(str2[i], start, end)
		#print 'len2', str2[i], start, end, index, ass1, workstr1, common2
		if (index > -1):    # Found common character
		    common2 += 1
		#ass2 += str2[i]
		ass2 = ass2 + str2[i]
		workstr1 = workstr1[:index] + jaro_winkler_marker_char + workstr1[index + 1:]

    if (common1 != common2):
        common1 = float(common1 + common2) / 2.0

    if (common1 == 0):
        return 0.0

    # Compute number of transpositions
    if(len1==len2):
        transposition = 0
        for i in range(len(ass1)):
            if (ass1[i] != ass2[i]):
                transposition += 1
        transposition = transposition / 2.0
    elif (len1>len2):
        transposition = 0
        for i in range(len(ass2)): #smaller length one
            if (ass1[i] != ass2[i]):
                transposition += 1
        while(i<len1):
            transposition +=1
            i +=1
        transposition = transposition / 2.0	
    elif (len1<len2):
        transposition = 0
        for i in range(len(ass1)): #smaller length one
            if (ass1[i] != ass2[i]):
                transposition += 1
        while(i<len2):
            transposition +=1
            i +=1
        transposition = transposition / 2.0	
	    
    # Compute number of characters are common at beginning of both strings, for Jaro-Winkler distance

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

#
# This code will calculate the percentage match for two db records
#
def jaro_winkler_distance_row(row1, row2):
    '''
       Used as a measure of similarity between two strings,
       see http://en.wikipedia.org/wiki/Jaro-Winkler_distance
    '''
    dw = 0
    num_similar = 0
    if len(row1)!=len(row2):
            print "The records columns does not match."
            return
    for x in range(0, len(row1)):
    	str1 = row1[x]		# get row fields
    	str2 = row2[x]          # get row fields
    	dw += jaro_winkler(str1, str2) #Calculate match value for two column values
    	#print dw
    dw = dw /len(row1) # Average of all column match value.
    dw = dw * 100      # convert in percentage	
    #print dw
    return dw

# Code referenced from http://code.activestate.com/recipes/52213-soundex-algorithm/

def soundex(name, len=4):
    # digits holds the soundex values for the alphabet
    digits = '01230120022455012623010202'
    sndx = ''
    fc = ''

    # translate alpha chars in name to soundex digits
    for c in name.upper():
        if c.isalpha():
            if not fc: fc = c   # remember first letter
            d = digits[ord(c)-ord('A')]
            # duplicate consecutive soundex digits are skipped
            if not sndx or (d != sndx[-1]):
                sndx += d

    # replace first digit with first alpha character
    sndx = fc + sndx[1:]

    # remove all 0s from the soundex code
    sndx = sndx.replace('0','')

    # return soundex code padded to len characters
    return (sndx + (len * '0'))[:len]
    

def docChecksum(docStr):
    converted = hashlib.sha1(docStr).hexdigest()
    return converted

def greatCircleDistance(lat1,lon1,lat2,lon2):
    ptlon1_radians = math.radians(lon1)
    ptlat1_radians = math.radians(lat1)
    ptlon2_radians = math.radians(lon2)
    ptlat2_radians = math.radians(lat2)

    distance_radians=2*math.asin(math.sqrt(math.pow((math.sin((ptlat1_radians-ptlat2_radians)/2)),2) + math.cos(ptlat1_radians)*math.cos(ptlat2_radians)*math.pow((math.sin((ptlon1_radians-ptlon2_radians)/2)),2)))
    # 6371.009 represents the mean radius of the earth
    # shortest path distance
    distance_km = 6371.009 * distance_radians
    return int(distance_km)
