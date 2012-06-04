from sqlobject import *

"""
OBSOLETE: we're moving to a more generic system,
using sqlalchemy
"""

try: # import from a local key repository
    from doh.private import PANAMA_DB_URL
    connection = connectionForURI(PANAMA_DB_URL)
except ImportError:
    connection = connectionForURI('sqlite:/:memory:')
connection.encoding = 'utf-8'
sqlhub.processConnection = connection

class Person(SQLObject):
    name = UnicodeCol(alternateID=True, length = 120, varchar = True)
    hidden = BoolCol(default=False)
    directorships = RelatedJoin('Company', intermediateTable = 'directors', addRemoveName = 'Directorship')
    subscriberships = RelatedJoin('Company', intermediateTable = 'subscribers', addRemoveName = 'Subscribership')
    agencys = RelatedJoin('Company', intermediateTable = 'agents', addRemoveName = 'Agency')

class Company(SQLObject):
    recordid = IntCol(alternateID = True)
    name = UnicodeCol() #may not be unique?
    hidden = BoolCol(default=False)
    registerdate = DateCol(default = None)
    #persons = RelatedJoin('Person')
    #directors = RelatedJoin('Person')
    #subscribers = RelatedJoin('Person', intermediateTable = 'directorships')
    directors = RelatedJoin('Person', intermediateTable = 'directors', addRemoveName = 'Director')
    subscribers = RelatedJoin('Person', intermediateTable = 'subscribers', addRemoveName = 'Subscriber')
    agent= RelatedJoin('Person', intermediateTable = 'agents', addRemoveName = 'Agent')


Person.createTable( ifNotExists = True)
Company.createTable( ifNotExists = True)


