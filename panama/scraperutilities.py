"""
"""


from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from ClientForm import ItemNotFoundError
from operator import isCallable
from itertools import takewhile
import logging
import mechanize
import os
import random
import re
import sys
import time
import traceback
import urllib
import urllib2
import urlparse
import warnings

debug = False

def cleanWhitespace(text):
    whitespaceRegex = re.compile('([\n\t\r ])+')
    return whitespaceRegex.sub('\g<1>', text)

def tidyText(text):
    newtext = cleanWhitespace(text)
    newertext = stripHTMLEntities(newtext)
    newesttext = newertext.strip()
    return newesttext

def tidyList(somelist):
    return [tidyText(x) for x in somelist]

nosoup = BeautifulSoup("") 

def tagtext(element, sep = ' ', strip = False):
    """
    Remove the html tags from a BeautifulSoup element,
    and return the text
    strip: whether to pass the text through 'strip' before returning it
     False: do not strip (default)
     True:  stip with standard strip() function
     [string]: pass the string to the strip() function, e.g. to remove particular characters
    sep: string to use when re-joining blocks of text
    """

    def dostrip(item):
        if not strip:
            return item
        elif strip is True:
            return item.strip()
        elif isinstance(strip, unicode) or isinstance(strip, str):
            return item.strip(strip)
        else:
            raise ValueError(
                "tagtext recieved an invalid argument for strip \
                - should be True, or unicode/string")
    items = []
    if not element:
        return ""
    if isinstance(element, unicode) or isinstance(element, str):
        return dostrip(element)
    for x in element.recursiveChildGenerator():
        if not isinstance(x, unicode):
            continue
        items.append(dostrip(x))
    return sep.join(items)

def toStr(item, formatstring = '%.2f'):
    """Cast to string, with decent rounding/formatting
    includes re-formatting strings that contain numbers"""
    if item == None or item == "":
        return ""
    if isinstance(item, str) or isinstance(item, unicode):
        try:
            item = float(item)
        except ValueError:
            return item
    if isinstance(item, int) or isinstance(item, float):
        return formatstring % item
    try:
        return item.__str__()
    except AttributeError:
        return ""

def tableToArray(table, textOnly = True, *args, **kwargs):
    """
    Turns an html table into a 2-dimensional array, with each
    <td> or <th> represented by one element.
    Beware of using this on html tables with elements spanning multiple
    rows or multiple columns
    """
    lists = []
    try:
        for row in table.findAll('tr'):
            lists.append([x for x in row.findAll(['td', 'th'])])
        if not textOnly:
            return lists
    except AttributeError: #wasn't a real beautifulsoup object,probably None
        return lists
    textlists = []
    for row in lists:
        textlists.append([tagtext(x) for x in row])
    return textlists
                
def hastext(name, regex):
    """
    Utility to overcome BS's issues with searching for both text and
    name
    """
    return lambda x: x.name == name and re.search(regex, tagtext(x))

def findBetween(start, end):
    """Find the section of HTML between two BeautifulSoup tags
    NB: this doesn't work!
    This is used by the following classes - they all need checking
     miscsites/lfvacations and escapia/e2 have their own versions
     miscsites/rentalsathtebeach
     visualdata/seaside,outerbanks,palmsprings,joelamb
    """
    forwards = start.findAllNext()
    backwards = end.findAllPrevious()
    #forwards = start.findAllNext(lambda x: x == x._lastRecursiveChild())
    #backwards = end.findAllPrevious(lambda x: x == x._lastRecursiveChild())
    intersection = []
    for element in forwards:
        if element in backwards:
            # print "adding element..."
            #print element
            intersection.append(element)
    return intersection


def findBetweenText(startPoint, endPoint, sep = ''):
    """This one might work!"""
    nextitems  = startPoint.nextGenerator()
    betweenList = list(takewhile(lambda x: x is not endPoint, nextitems))
    betweenText = [x for x in betweenList if isinstance(x, unicode)]
    return sep.join(betweenText)


