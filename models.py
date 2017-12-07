from sqlalchemy.orm import relationship, backref
from database import Base

print(Base.metadata.tables)

class Users(Base):
    __tablename__ = Base.metadata.tables['users']

class Games(Base):
    __tablename__ = Base.metadata.tables['games']

class Missions(Base):
    __tablename__ = Base.metadata.tables['missions']

class Turns(Base):
    __tablename__ = Base.metadata.tables['turns']

class Nominees(Base):
    __tablename__ = Base.metadata.tables['nominees']

class Votes(Base):
    __tablename__ = Base.metadata.tables['votes']
