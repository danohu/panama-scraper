
"""
Generic corporation database

9 April 2012: rewriting the database layer
The plan here is to:
 - move from mysql to postgres
 - aabstract away much of the panama-specific information
 - support multiple versions of records
    - work with json to store more of the data


Companies and People

 Logically, companies and people could be identical. But in terms of practical implementation, it is much easier to share the same code for both

"""

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Enum, Unicode, Boolean, ForeignKey, UnicodeText, TypeDecorator
from sqlalchemy.orm import relationship, sessionmaker
from doh.private import CORP_DB_URL
import copy
import json

Base = declarative_base()
engine = sqlalchemy.create_engine(CORP_DB_URL)
Session = sessionmaker(bind=engine)




class JSONText(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode) # XXX: break into first and last names
    data = Column(JSONText) # JSON data

    companies = relationship('Link', backref="person")

    @classmethod
    def create_or_update(cls, session, name, data = {}):
        person = session.query(cls).filter(cls.name == name).first()
        if person:
            # roundabout, because our JSONText implementation fails
            # to make oolumns mutable
            newdata = copy.copy(person.data or {})
            newdata.update(data)
            person.data = newdata
        else:
            person = cls(name = name, data = data)
        return person
           

    def countries_active(self):
        pass

    def first_seen(self):
        pass

    def last_seen(self):
        pass

    def currently_active(self):
        pass

    def companies(self):
        """
        XXX: this will need expansion to handle current/past directorships
        of companies active and inactive
        """
        return [x.company for x in self.company_links]


class Company(Base):

    __tablename__ = 'company'

    id = Column(Integer, primary_key=True)
    country = Column(Enum('Panama', 'Other', name="country_enum"), index=True)
    # recordid is the official registry's company data
    recordid = Column(Integer, index=True)
    name = Column(Unicode, index=True)
    status = Column(Unicode, index=True) #XXX make an enum, once we know all valid statuses
    date_founded = Column(Date)
    scrape_date = Column(Date)
    scrape_source = Column(Unicode) 
    is_current = Column(Boolean, index=True, default=False) # calculated, but cached here
    data = Column(JSONText) #JSON data
    
    #people = relationship('Person', backref="companies")

    def addPerson(self, role, name, linkdata = {}, persondata = {}, session = None):
        """add person, linked to this company.
        """
        if session is None:
            session = Session()
        person = Person.create_or_update(session, name = name, data = persondata)
        session.add_all([self, person])
        session.commit()
        link = Link(role=role, data = linkdata,
                company_id = self.id,
                person_id = person.id)
        session.add(link)
        session.commit()
        return (person, link)


    @classmethod
    def update_current(cls):
        """Loop through all companies, ensuring that they are only marked
        current if they are genuinely the latest company to have been
        scraped"""
        pass

    def get_source_file(self):
        """source file should be a colon-separated
        zipfilename:filepath"""
        pass

    def people(self):
        return [x.person for x in self.person_links]

class Link(Base):

    __tablename__ = 'link'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'), primary_key=True)
    person_id = Column(Integer, ForeignKey('person.id'), primary_key=True)
    role = Column(Unicode) # XXX should this be an enum?
    data = Column(JSONText)

    company = relationship('Company', backref='person_links')
    person = relationship('Person', backref='company_links')

Base.metadata.create_all(engine)


