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
#from datamodel import Person, Company, SQLObjectNotFound
from gendb import Person, Company, Link, Session
#database sc:ehema
import os
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

    officials = {
       'presidente' : 'president',
       'secretario' : 'secretary',
       'tesorero'   : 'treasurer',
       }

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

    def wideHead(self, soup, term):
        marker = soup.find(hastext('font', term)) or nosoup
        value = tagtext(marker.findNext('td', width='49%')).strip()
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
        session = Session()
        datadict = self.scrapeData(rawtext)
        crecord = Company(
                        name = datadict['nombredelasociedad'],
                        recordid = int(datadict['nodeficha']),
                        scrape_date = None,
                        scrape_source = None,
                        is_current = None,
                        data = None)
        try: # XXX does this really need to be a register thing
            dateobj = time.strptime(datadict['registerdate'], '%d-%m-%Y')
            cleandate = time.strftime('%Y-%m-%d', dateobj)
            crecord.date_founded = cleandate
        except ValueError:
            log('invalid date: %s' % datadict['registerdate'])
        for subscriber in datadict['suscriptores']:
            crecord.addPerson(
                    role = 'subscriber',
                    name = subscriber,
                    session = session)
        if datadict['agent']:
            crecord.addPerson(
                    role = 'agent',
                    name = datadict['agent'],
                    session = session)
        for director in datadict['directors']:
            crecord.addPerson(
                    role = 'director',
                    name = director,
                    session = session)
        for (role, name) in datadict['titles'].items():
            role = role.lower()
            title = self.officials.get(role, role)
            crecord.addPerson(
                    role = title,
                    name = name,
                    session = session)
        session.commit()
        return crecord


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
            #'Status de la Prenda',
            )
        for heading in headings:
            scrapeddata[heading] = self.smallHead(soup, heading)
        scrapeddata['status_de_la_prenda'] = self.wideHead(soup,
                'Prenda')
        scrapeddata['titles'] = self.dictOfTitles(soup)
        scrapeddata['directors'] = self.listOfDirectors(soup)
        scrapeddata['suscriptores'] = self.listFromTable(soup, 'Nombre de los Suscriptores')

        # we don't really care about the boilerplate explanations of share
        # distribution
        # scrapeddata['capital'] = self.listFromTable(soup, 'Capital')
        # scrapeddata['representantelegal'] = tagtext(soup.find(hastext('font', '(?m)Representante Legal')).findNext('table')).strip()
        for item in scrapeddata:
            if not(isinstance(scrapeddata[item], unicode)):
                print(scrapeddata[item])
        return scrapeddata

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
            
            #basics
            'Fecha de Registro', #date registered
            'Status', #status
            
            # Apostiled document (???)
            'No. de Escritura',  # signed document number
            'Fecha de Escritura', # date of signed documents
            
            # registration details
            'Notaria', #may be odd
            'Provincia Notaria', #notary provice
            'Duraci.n', #duration
            'Domicilio', #domicile

            # Capital
            'Moneda', # currency
            'Monto de Capital', # amount of capital

            #tax details
            'Fecha de Pago', # date paid company tax
            'Agente Residente', #resident agent

            #'Status de la Prenda',
            )
        #for heading in headings:
        #    scrapeddata[heading] = smallHead(soup, heading)
        #scrapeddata['representantelegal'] = tagtext(soup.find(hastext('font', '(?m)Representante Legal')).findNext('table')).strip()
        scrapeddata['titles'] = self.dictOfTitles(soup)
        scrapeddata['directors'] = self.listOfDirectors(soup)
        scrapeddata['suscriptores'] = self.listFromTable(soup, 'Nombre de los Suscriptores')
        #scrapeddata['capital'] = self.listFromTable(soup, 'Capital')
        for item in scrapeddata:
            if not(isinstance(scrapeddata[item], unicode)):
                print(scrapeddata[item])
        return scrapeddata


class TestScraper(object):
    testfilepaths = ()
    scraper = None #add this in subclasses
    test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')

    def run(self): #xxx retrofit into this the whole nosetests shit
        self.test_parsing()
        # test_db disabled, since it seems to be runnign
        # into the live DB
        #self.test_db

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
    def __init__(self, *args, **kwargs):
        self.testfilepaths = (os.path.join(self.test_data_dir, 'sample_panama_company.html'),)

        self.scraper = PanamaCompanyScraper()

class TestPanamaFoundationScraper(TestScraper):

    def __init__(self, *args, **kwargs):
        self.testfilepaths = (os.path.join(self.test_data_dir, 'sample_panama_foundation.html'),)
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


