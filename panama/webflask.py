#!/usr/bin/env python
from flask import Flask, request, jsonify
app = Flask(__name__)

import urllib
from urlparse import parse_qs
from panama.settings import basedir
BADDATA = 'DATA COULD NOT BE SCRAPED'
import traceback
from datamodel import Person, Company, SQLObjectNotFound

HTMLHEAD = '''<html>
 <STYLE type="text/css">

.warning {
  color: #D8000C;
  background-color: #FFBABA;
  font-size: 20px;
  font-weight: bold;
  padding: 20px;
  margin: 20px;
          }
</STYLE>
<body>
<div class="warning">
Beware: the information on these pages may be inaccurate or outdated. Please check any results against the <a href="http://registro-publico.gob.pa/">official registry</a>
</div>
'''
HTMLTAIL = '</body></html>'
BASEURL = '/panama'
ABOUTTEXT = """
<h3>What is this?</h3>

Panama corporate records have recently been made available <a href="https://www.registro-publico.gob.pa/scripts/nwwisapi.dll/conweb/prinpage">online</a>. Unfortunately the official site won't let you search by the name of company directors - a gap which we're filling.

Once you have found a company, you can use the official site to find the complete entry in the Companies Register, and <a href="https://www.registro-publico.gob.pa/RediWeb/default.asp">scans</a> of documents they have submitted.
"""

def escape_name(name):
    try:
        return urllib.quote(name)
    except Exception:
        return name


def google(text):
    return '(<a href="http://www.google.com/search?q=%%22%s%%22">google</a>)' % text

def getarg(fromqs, name):
    if fromqs:
        return fromqs
    else:
        arguments = parse_qs(self.request.query)
        return arguments.get(name)[0] 

@app.route('/panama/bulksearch/<searchterms>')
def bulkSearch(searchterms):
    data = {'who?': 'me'}
    return jsonify(data)

@app.route('/panama/company/id/<companyid>', methods=['POST', 'GET'])
def companyPage(companyid):
    try:
        companyid = int(companyid)
        record = Company.byRecordid(companyid)
    except (ValueError, SQLObjectNotFound):
        self.quitWithMsg('No company with ID %s' % companyid)
        return
    if record.hidden:
        self.quitWithMsg('Company %s is not currently available' % companyid)
        return
    subscribers = record.subscribers
    directors = record.directors
    html = '<h1>%s</h1>' % record.name
    companyurl = 'https://www.registro-publico.gob.pa/scripts/nwwisapi.dll/conweb/MESAMENU?TODO=SHOW&ID=%s' % record.recordid
    html += '<!--<h3><a href="%s">Full Details</a></h3>-->' % companyurl
    html += '<h2>Directors</h2><ul>' 
    for director in directors:
        if not director.hidden:
            html += '<li><a href="%s/person/%s">%s</a> %s </li>' % (BASEURL, director.name, director.name, google(director.name))
    html += '</ul>'
    html += '<h2>Subscribers</h2><ul>' 
    for subscriber in subscribers:
        if not subscriber.hidden:
            html += '<li><a href="%s/person/%s">%s</a></li>' % (BASEURL, subscriber.name, subscriber.name)
    html += '</ul>'
    agentlist = record.agent
    if len(agentlist):
        agent = agentlist[0]
        if not agent.hidden:
            html += '<h2>Agent</h2>'
            html += '<ul><li><a href="%s/person/%s">%s</a></li></ul>' % (BASEURL, agent.name, agent.name)
    if record.registerdate:
        html += '<h3>Date Registered</h3>'
        html += record.registerdate.strftime('%F')
    html += '<!--<h3><a href="https://www.registro-publico.gob.pa/RediWeb/default.asp">Look up complete file</a></h3>--> </br></br>'
    html += 'To find complete details, consult the <a href="http://registro-publico.gob.pa/">official registry</a>. Search for %s as "Numero de Ficha"' % record.recordid
    return html



@app.route('/panama/person/<rawname>', methods=['POST', 'GET'])
def personPage(rawname):
    html = ''
    name = urllib.unquote(rawname).upper()
    try:
        record = Person.byName(name)
    except SQLObjectNotFound:
        html += 'could not find %s' % name
        self.write(html)
        return
    if record.hidden:
        self.quitWithMsg("Details of this person are not currently available")
        return
    subscriberships = record.subscriberships
    directorships = record.directorships
    agencies = record.agencys
    html += '<h1>%s</h1>' % name
    html += '<h2>Director</h2><ul>' 
    for company in directorships:
        if not company.hidden:
            html += '<li><a href="%s/company/id/%s">%s</a></li>' % (BASEURL, company.recordid, company.name)
    html += '</ul>'
    html += '<h2>Subscriber</h2><ul>' 
    for company in subscriberships:
        if not company.hidden:
            html += '<li><a href="%s/company/id/%s">%s</a></li>' % (BASEURL, company.recordid, company.name)
    html += '</ul>'
    html += '<h2>Agent</h2><ul>' 
    for company in agencies:
        if not company.hidden:
            html += '<li><a href="%s/company/id/%s">%s</a></li>' % (BASEURL, company.recordid, company.name)
    html += '</ul>'
    return html



@app.route('/panama/personsearch/', methods=['POST', 'GET'])
@app.route('/panama/search/person/', methods=['POST', 'GET'])
def searchPerson():
    rawSearchterm = (request.args.get('name', ''))
    html = HTMLHEAD
    unquotedTerm = urllib.unquote(rawSearchterm).upper()
    liketerm = Person.sqlrepr('%%%s%%' % unquotedTerm)
    sqlquery = "person.name LIKE %s" % liketerm
    html += '<h2>Search results</h2><h3>searching for %s</h3><ul>' % sqlquery
    people = Person.select(sqlquery)
    for thisone in people:
        if not thisone.hidden:
            html += "<li><a href='%s/person/%s'>%s</a></li>" %(BASEURL, escape_name(thisone.name), thisone.name)
    html += '</ul>'
    html += HTMLTAIL
    return html

@app.route('/panama/search/company/', methods=['POST', 'GET'])
def searchCompany():
    rawSearchterm = (request.args.get('name', ''))
    html = HTMLHEAD
    unquotedTerm = urllib.unquote(rawSearchterm).upper()
    liketerm = Company.sqlrepr('%%%s%%' % unquotedTerm)
    sqlquery = "company.name LIKE %s" % liketerm
    html += '<h2>Company Search results</h2><h3>searching for %s</h3><ul>' % sqlquery
    people = Company.select(sqlquery)
    for thisone in people:
        if not thisone.hidden:
            html += "<li><a href='%s/company/id/%s'>%s</a></li>" %(BASEURL, thisone.recordid, thisone.name)
    html += '</ul>'
    html += HTMLTAIL
    return html


@app.route('/panama/')
def index():
        html = HTMLHEAD + '<h2>Search Panama company records</h2>\
        <form action="%s/personsearch" method="get">\
        <b>Name of person</b><input type = "text" name = "name"><br>\
        <input type="submit" value="Search"></form><br/>\
        <form action="%s/search/company" method="get">\
        <b>Name of company</b><input type = "text" name = "name"><br>\
        <input type="submit" value="Search"></form><br/>\
        ' % (BASEURL, BASEURL)
        html += ABOUTTEXT
        html += HTMLTAIL
        return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = '8090')

