from sqlobject import *

#'connection = connectionForURI('mysql://USERNAME:PASSWORD@localhost/panama?use_unicode=1&charset=utf8')
connection = connectionForURI('sqlite:/:memory:')
connection.encoding = 'utf-8'
sqlhub.processConnection = connection

class Person(SQLObject):
    name = UnicodeCol(alternateID=True, length = 120, varchar = True)
    directorships = RelatedJoin('Company', intermediateTable = 'directors', addRemoveName = 'Directorship')
    subscriberships = RelatedJoin('Company', intermediateTable = 'subscribers', addRemoveName = 'Subscribership')
    agencys = RelatedJoin('Company', intermediateTable = 'agents', addRemoveName = 'Agency')

class Company(SQLObject):
    recordid = IntCol(alternateID = True)
    name = UnicodeCol() #may not be unique?
    registerdate = DateCol(default = None)
    #persons = RelatedJoin('Person')
    #directors = RelatedJoin('Person')
    #subscribers = RelatedJoin('Person', intermediateTable = 'directorships')
    directors = RelatedJoin('Person', intermediateTable = 'directors', addRemoveName = 'Director')
    subscribers = RelatedJoin('Person', intermediateTable = 'subscribers', addRemoveName = 'Subscriber')
    agent= RelatedJoin('Person', intermediateTable = 'agents', addRemoveName = 'Agent')


Person.createTable( ifNotExists = True)
Company.createTable( ifNotExists = True)


