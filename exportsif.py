"""
Export from the database to SIF format ('Simple interaction file')

link types:
director
subscriber
agent
"""

import datamodel as dm

def escape_name(name):
    return name.replace(' ', '_')

def personlist(person):
    escapedname = escape_name(person.name)
    directorships = [escape_name(x.name) for x in person.directorships[:10]]
    subscriberships = [escape_name(x.name) for x in person.subscriberships[:10]]
    agencys = [escape_name(x.name) for x in person.agencys[:10]]
    directorlist = '%s directorship %s' % (escapedname, ' '.join(directorships))
    subscriberlist = '%s directorship %s' % (escapedname, ' '.join(subscriberships))
    agentlist = '%s directorship %s' % (escapedname, ' '.join(agencys))
    return [directorlist, subscriberlist, agentlist]

def generatelist(limit = 100):
    nodelist = []
    people = dm.Person.select()[:limit]
    for person in people:
        nodelist.extend(personlist(person))
    return '\n'.join(nodelist)

