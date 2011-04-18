
import urllib2
import os
import time
from settings import *

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-t", "--highnum", dest="highnum", type = "int", default = 400000)
parser.add_option("-l", "--lownum",  dest="lownum", type = "int", default= 1 )

(options, args) = parser.parse_args()

highnum = options.highnum
lownum = options.lownum

for recordnum in range(highnum, lownum, -1):
    filename = '%srecord_%s.html' % (basedir, recordnum)
    if os.path.exists(filename):
        log('skipping %s' % recordnum)
        continue
    fh = open(filename, 'w')
    url = 'https://www.registro-publico.gob.pa/scripts/nwwisapi.dll/conweb/MESAMENU?TODO=SHOW&ID=%s' % recordnum
    try:
        pagetext = urllib2.urlopen(url).read()
    except (urllib2.URLError, urllib2.httplib.BadStatusLine): #I forget what error
        log('failed download for record %s' % recordnum)
        continue
    fh.write(pagetext)
    fh.close()
    log('stored record %s' % recordnum)
    time.sleep(1)

