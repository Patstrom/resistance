from database import Base

class Users(Base):
    __tablename__ = 'users'
    __table_args__ = {'autoload':True}

class Games(Base):
    __tablename__ = 'games'
    __table_args__ = {'autoload':True}

class Missions(Base):
    __tablename__ = 'missions'
    __table_args__ = {'autoload':True}

class Turns(Base):
    __tablename__ = 'turns'
    __table_args__ = {'autoload':True}

class Nominees(Base):
    __tablename__ = 'nominees'
    __table_args__ = {'autoload':True}

class Votes(Base):
    __tablename__ = 'votes'
    __table_args__ = {'autoload':True}
