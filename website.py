#!/usr/bin/python
import web
import urllib
from settings import basedir
BADDATA = 'DATA COULD NOT BE SCRAPED'
import traceback
from datamodel import Person, Company, SQLObjectNotFound
#database schema

#render = web.templaterender('templates/')
urls = ('/?', 'indexPage',
        '/person/(.*)', 'personPage',
        '/company/id/(.*)', 'companyByNumberPage',
        '/personsearch', 'searchPersonPage',
        '/search/person/(.*)', 'searchPersonPage')

HTMLHEAD = '<html><body>'
HTMLTAIL = '</body></html>'
BASEURL = '/panama'
ABOUTTEXT = """
<h3>What is this?</h3>

Panama corporate records have recently been made available <a href="https://www.registro-publico.gob.pa/scripts/nwwisapi.dll/conweb/prinpage">online</a>. Unfortunately the official site won't let you search by the name of company directors - a gap which we're filling.

Once you have found a company, you can use the official site to find the complete entry in the Companies Register, and <a href="https://www.registro-publico.gob.pa/RediWeb/default.asp">scans</a> of documents they have submitted.
"""

class indexPage:

    def GET(self):
        web.header('Content-Type', 'text/html') 
        html = '<html><h2>Search Panama company records</h2>\
        <form action="%s/personsearch" method="get">\
        <b>Name of person</b><input type = "text" name = "name"><br>\
        <input type="submit" value="Search">\
        ' % BASEURL
        html += ABOUTTEXT
        html += '</html>'
        print(html)

def google(text):
    return '(<a href="http://www.google.com/search?q=%%22%s%%22">google</a>)' % text

class personPage:

    def GET(self, rawname):
        web.header('Content-Type', 'text/html') 
        html = ''
        name = urllib.unquote(rawname).upper()
        try:
            record = Person.byName(name)
        except SQLObjectNotFound:
            html += 'could not find %s' % name
            print(html)
            return
        subscriberships = record.subscriberships
        directorships = record.directorships
        agencies = record.agencys
        html += '<h1>%s</h1>' % name
        html += '<h2>Director</h2><ul>' 
        for company in directorships:
            html += '<li><a href="%s/company/id/%s">%s</a></li>' % (BASEURL, company.recordid, company.name)
        html += '</ul>'
        html += '<h2>Subscriber</h2><ul>' 
        for company in subscriberships:
            html += '<li><a href="%s/company/id/%s">%s</a></li>' % (BASEURL, company.recordid, company.name)
        html += '</ul>'
        html += '<h2>Agent</h2><ul>' 
        for company in agencies:
            html += '<li><a href="%s/company/id/%s">%s</a></li>' % (BASEURL, company.recordid, company.name)
        html += '</ul>'
        print(html)

class companyByNumberPage:

    def GET(self, companyid):
        web.header('Content-Type', 'text/html') 
        try:
            record = Company.byRecordid(companyid)
        except SQLObjectNotFound:
            print 'No company with ID %s' % companyid
            return
        subscribers = record.subscribers
        directors = record.directors
        html = '<h1>%s</h1>' % record.name
        companyurl = 'https://www.registro-publico.gob.pa/scripts/nwwisapi.dll/conweb/MESAMENU?TODO=SHOW&ID=%s' % record.recordid
        html += '<h3><a href="%s">Full Details</a></h3>' % companyurl
        html += '<h2>Directors</h2><ul>' 
        for director in directors:
            html += '<li><a href="%s/person/%s">%s</a> %s </li>' % (BASEURL, director.name, director.name, google(director.name))
        html += '</ul>'
        html += '<h2>Subscribers</h2><ul>' 
        for subscriber in subscribers:
            html += '<li><a href="%s/person/%s">%s</a></li>' % (BASEURL, subscriber.name, subscriber.name)
        html += '</ul>'
        agentlist = record.agent
        if len(agentlist):
            agent = agentlist[0]
            html += '<h2>Agent</h2>'
            html += '<ul><li><a href="%s/person/%s">%s</a></li></ul>' % (BASEURL, agent.name, agent.name)
        if record.registerdate:
            html += '<h3>Date Registered</h3>'
            html += record.registerdate.strftime('%F')
        html += '<h3><a href="https://www.registro-publico.gob.pa/RediWeb/default.asp">Look up complete file</a></h3> </br>'
        html += '(search for %s as "Numero de Ficha")' % record.recordid
        print(html)

class searchPersonPage:

    def GET(self, rawSearchterm = None):
        web.header('Content-Type', 'text/html') 
        #print dir(self)
        #print rawSearchterm
        #print globals()
        #print web.input()
        if rawSearchterm is None:
            rawSearchterm = web.input()['name']
        html = HTMLHEAD
        unquotedTerm = urllib.unquote(rawSearchterm).upper()
        liketerm = Person.sqlrepr('%%%s%%' % unquotedTerm)
        sqlquery = "person.name LIKE %s" % liketerm
        html += '<h2>Search results</h2><h3>searching for %s</h3><ul>' % sqlquery
        people = Person.select(sqlquery)
        for thisone in people:
            html += "<li><a href='%s/person/%s'>%s</a></li>" %(BASEURL, thisone.name, thisone.name)
        html += '</ul>'
        html += HTMLTAIL
        print(html)
web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
if __name__ == '__main__':
    web.run(urls, globals())
