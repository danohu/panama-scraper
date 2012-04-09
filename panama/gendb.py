
"""
Generic corporation database

9 April 2012: rewriting the database layer
The plan here is to:
 - move from mysql to postgres
 - aabstract away much of the panama-specific information
 - support multiple versions of records
    - work with json to store more of the data

"""

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Enum, Unicode
from doh.private import CORP_DB_URL

Base = declarative_base()
engine = sqlalchemy.create_engine(CORP_DB_URL)


class Entity(Base):
    """
    An entity could be either a company or a person -- in many legal
    contexts there is no difference between the two
    """

    __tablename__ = 'entity'

    id = Column(Integer, primary_key=True)
    entity_type = Column(Enum('Company', 'Person', name="entity_enum"), index=True)
    country = Column(Enum('Panama', 'Other', name="country_enum"), index=True)
    scrape_date = Column(DateTime)
    scrape_source = Column(Unicode)
    current = Column(Boolean, index=True)
    data = Column(Unicode) #JSON data

class Link(Base):

    __tablename__ = 'link'

    id = Column(Integer, primary_key=True)
    linkfrom = Column(Integer, ForeignKey('entity.id'))
    linkto = Column(Integer, ForeignKey('entity.id'))
    date = Column(DateTime)
    current = Column(Boolean, index=True)
    data = Column(Unicode)

Base.metadata.create_all(engine)


