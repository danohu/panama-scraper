import time
#highnum = 619300
#highnum = 469000 #we've made our way through the 600,000s
#XXX: below deprecated
highnum = 450000 #getting kassar to impress hacks
lownum = 350000
basedir = '/home/dan/panama/records/'
logfilename = '/home/dan/panama/log.txt'


class BaseSettings(object):
    highnum = 450000 #getting kassar to impress hacks
    lownum = 350000
    basedir = '/home/dan/panama/records/'
    logfilename = '/home/dan/panama/log.txt'

class ThuleSettings(BaseSettings):
    highnum = 450000 #getting kassar to impress hacks
    lownum = 350000
    basedir = '/home/dan/panama/records/'
    logfilename = '/home/dan/panama/log.txt'

def log(text):
    logfile = open(logfilename, 'a')
    print(text)
    curtime = time.strftime('%F %H:%M', time.gmtime())
    logfile.write("%s (%s)\n" % (text, curtime))
    logfile.flush()

