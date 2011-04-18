#!/usr/bin/python
# -*- coding: latin-1 -*-
from BeautifulSoup import BeautifulSoup, UnicodeDammit
from scraperutilities import hastext, tagtext, nosoup
from settings import ThuleSettings
from settings import *

settings = ThuleSettings()
BADDATA = 'DATA COULD NOT BE SCRAPED'
import codecs
import traceback
from datamodel import Person, Company, SQLObjectNotFound
#database sc:ehema
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-t", "--highnum", dest="highnum", type = "int", default = 400000)
parser.add_option("-l", "--lownum",  dest="lownum", type = "int", default= 1 )
parser.add_option("-b", "--breakonmiss",  dest="skipmissing", action = "store_false", default= True )

(options, args) = parser.parse_args()

highnum = options.highnum
lownum = options.lownum


class BaseScraper(object):
    pass

class PanamaScraper(BaseScraper):
    highnum = 40
    lownum = 1
    basedir = '/home/dan/panama/records/'

    def __init__(self, highnum = None, lownum = None, *args, **kwargs):
        self.highnum = highnum and self.highnum
        self.lownum = lownum and self.lownum
        self.skipmissing = options.skipmissing

    def filename(self, recordid):
        return '%srecord_%s.html' % (self.basedir, recordid)

    def addNewRecords(self):
        """XXX: should this be a classmethod?"""
        records = xrange(self.highnum, self.lownum, -1)
        for recordid in records:
            try:
                company = Company.byRecordid(recordid)
                print('already handled record %s' % recordid)
                continue
            except SQLObjectNotFound:
                filename = self.filename(recordid)
            try:
                #pagetext = codecs.open(filename, 'r', 'windows-1252').read()
                pagetext = open(filename, 'r').read()
            except IOError:
                if options.skipmissing:
                    print('skipping missing record %s' % recordid)
                    continue
                print('halting on missing record %s' % recordid)
                raise
            if not pagetext:
                log('%s is empty' % recordid)
                continue
            try:
                self.processRecord(pagetext)
            except AttributeError:
                traceback.print_exc()
                log('failed to process record %s' % recordid)
                continue
            print('added record %s' % recordid)


    def smallHead(self, soup, term):
        marker = soup.find(hastext('font', term)) or nosoup
        value = tagtext(marker.findNext('td')).strip()
        return value or BADDATA

    def dictOfTitles(self, soup):
        table = soup.find(hastext('font', 'T.tulo del Dignatario')).findNext('table')
        titledict = {}
        for row in table.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) != 2:
                print('unexpected table layout: ' + row.prettify())
            title = tagtext(cells[0])
            name = tagtext(cells[1])
            if name and title:
                titledict[title] = name
        return titledict

    def listOfDirectors(self, soup):
        return self.listFromTable(soup, 'Nombre de los Directores')

    def listFromTable(self, soup, term):
        table = soup.find(hastext('font', term)).findNext('table')
        directors = []
        for row in table.findAll('tr'):
            text = tagtext(row).strip()
            if text:
                directors.append(text)
        return directors

    def processRecord(self, rawtext):
        #clean up the markup a bit - document has two HEADs, which confuses beautiful soup
        datadict = self.scrapeData(rawtext)
        crecord = Company(
                        name = datadict['nombredelasociedad'],
                        recordid = int(datadict['nodeficha']))
        try:
            dateobj = time.strptime(datadict['registerdate'], '%d-%m-%Y')
            cleandate = time.strftime('%Y-%m-%d', dateobj)
            crecord.registerdate = cleandate
        except ValueError:
            log('invalid date: %s' % datadict['registerdate'])
        for subscriber in datadict['suscriptores']:
            try:
                #print repr(subscriber)
                #su = UnicodeDammit(repr(subscriber))
                #print(su)
                #su = unicode(subscriber, 'utf-8')
                #print subscriber
                susc = Person.byName(subscriber)
            except SQLObjectNotFound:
                susc = Person(name = subscriber)
            susc.addSubscribership(crecord)
        if datadict['agent']:
            agentname = datadict['agent']
            try:
                agent = Person.byName(agentname)
            except SQLObjectNotFound:
                agent = Person(name = agentname)
            agent.addAgency(crecord)
        for director in datadict['directors']:
            dname = director
            try:
                drecord = Person.byName(dname)
            except SQLObjectNotFound:
                drecord = Person(name = dname)
            drecord.addDirectorship(crecord)

class PanamaCompanyScraper(PanamaScraper):

    def scrapeData(self, rawtext):
        """
        Does the gritty data extraction from HTML
        returns a dictionary of what it found
        """
        scrapeddata = {}
        pagetext = '<html>' + rawtext[rawtext.find('output.html - end'):]
        soup = BeautifulSoup(pagetext)
        marker = soup.find(hastext('b', '(?m)No.\W+de\W+Ficha')) or nosoup
        scrapeddata['nodeficha'] = tagtext(marker.findNext('p'))
        scrapeddata['nodocumento'] = tagtext(soup.find(hastext('b', '(?m)No.\W+Documento')).findNext('p'))
        scrapeddata['nombredelasociedad'] = tagtext(soup.find(hastext('b', '(?m)Nombre de la Sociedad')).findNext('table')).strip()
        #scrapeddata['Tomo'] = smallHead(soup, 'Tomo:')
        #scrapeddata['Folio'] = smallHead(soup, 'Folio:')
        #scrapeddata['Asiento'] = smallHead(soup, 'Asiento:')
        scrapeddata['registerdate'] = self.smallHead(soup, 'Fecha de Registro:')
        scrapeddata['agent'] = self.smallHead(soup, 'Agente Residente')
        headings = (
            'Fecha de Registro', 
            'Status', 
            'No. de Escritura', 
            'Notaria', #may be odd
            'Provincia Notaria',
            'Duración',
            'Domicilio',
            'Status de la Prenda',)
        #for heading in headings:
        #    scrapeddata[heading] = smallHead(soup, heading)
        scrapeddata['representantelegal'] = tagtext(soup.find(hastext('font', '(?m)Representante Legal')).findNext('table')).strip()
        scrapeddata['titles'] = self.dictOfTitles(soup)
        scrapeddata['directors'] = self.listOfDirectors(soup)
        scrapeddata['suscriptores'] = self.listFromTable(soup, 'Nombre de los Suscriptores')
        scrapeddata['capital'] = self.listFromTable(soup, 'Capital')
        for item in scrapeddata:
            if not(isinstance(scrapeddata[item], unicode)):
                print(scrapeddata[item])
        return scrapeddata

    pass

class PanamaFoundationScraper(PanamaScraper):
    
    def scrapeData(self, rawtext):
        """
        Does the gritty data extraction from HTML
        returns a dictionary of what it found
        """
        scrapeddata = {}
        pagetext = '<html>' + rawtext[rawtext.find('output.html - end'):]
        soup = BeautifulSoup(pagetext)
        marker = soup.find(hastext('b', '(?m)No.\W+de\W+Ficha')) or nosoup
        scrapeddata['nodeficha'] = tagtext(marker.findNext('p'))
        scrapeddata['nodocumento'] = tagtext(soup.find(hastext('b', '(?m)No.\W+Documento')).findNext('p'))
        scrapeddata['nombredelasociedad'] = tagtext(soup.find(hastext('b', '(?m)Nombre de la Funda')).findNext('table')).strip()
        #scrapeddata['Tomo'] = smallHead(soup, 'Tomo:')
        #scrapeddata['Folio'] = smallHead(soup, 'Folio:')
        #scrapeddata['Asiento'] = smallHead(soup, 'Asiento:')
        scrapeddata['registerdate'] = self.smallHead(soup, 'Fecha de Registro:')
        scrapeddata['agent'] = self.smallHead(soup, 'Agente Residente')
        headings = (
            'Fecha de Registro', 
            'Status', 
            'No. de Escritura', 
            'Notaria', #may be odd
            'Provincia Notaria',
            'Duración',
            'Domicilio',
            'Status de la Prenda',)
        #for heading in headings:
        #    scrapeddata[heading] = smallHead(soup, heading)
        #scrapeddata['representantelegal'] = tagtext(soup.find(hastext('font', '(?m)Representante Legal')).findNext('table')).strip()
        scrapeddata['titles'] = self.dictOfTitles(soup)
        scrapeddata['directors'] = self.listOfDirectors(soup)
        scrapeddata['suscriptores'] = self.listFromTable(soup, 'Nombre de los Suscriptores')
        scrapeddata['capital'] = self.listFromTable(soup, 'Capital')
        for item in scrapeddata:
            if not(isinstance(scrapeddata[item], unicode)):
                print(scrapeddata[item])
        return scrapeddata

    pass

class TestScraper(object):
    testfilepaths = ()
    scraper = None #add this in subclasses

    def run(self): #xxx retrofit into this the whole nosetests shit
        self.test_parsing()
        self.test_db

    def test_parsing(self):
        results = []
        for path in self.testfilepaths:
            pagetext = open(path).read()
            results.append(self.scraper.scrapeData(pagetext))
        return results

    def test_db(self):
        for path in self.testfilepaths:
            pagetext = open(path).read()
            self.scraper.processRecord(pagetext)
        


class TestPanamaCompanyScraper(TestScraper):
    testfilepaths = ('./testdata/sample_panama_company.html',)

    def __init__(self, *args, **kwargs):
        self.scraper = PanamaCompanyScraper()

class TestPanamaFoundationScraper(TestScraper):
    testfilepaths = ('./testdata/sample_panama_foundation.html',)

    def __init__(self, *args, **kwargs):
        self.scraper = PanamaFoundationScraper()
     
"""
XXX: general code cleanup todo:
 move to standard python logging
 single classes for each country (separate ones for scraper and extractor)
 codify storage_on_disk as 
 utility functions for managing the zip files (needed?)
 allow for flexible database-interface (so tests can use memory)
"""

if __name__ == '__main__':
    scraper = PanamaCompanyScraper()
    scraper.addNewRecords()


