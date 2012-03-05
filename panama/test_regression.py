
import os
import urllib2

old_hostname = 'http://ohuiginn.net/panama'
new_hostname = 'http://localhost:8888'

def make_urls(basename):
    '''return test urls attached to a given server'''
    datafile = os.path.join(os.path.dirname(__file__), 'testdata/urls_noprefix.txt')
    urls = open(datafile).readlines()
    return ['%s%s' % (basename, url) for url in urls if not url.startswith('#')]

def test_urls():
    urls = zip(*map(make_urls, (old_hostname, new_hostname)))
    for (old, new) in urls:
        print('testing %s vs %s' % (old, new))
        oldpage = urllib2.urlopen(old).read()
        newpage = urllib2.urlopen(new).read()
        assert oldpage == newpage
        print('%s == %s' % (old, new))
    
