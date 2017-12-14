from database import Base
from passlib.hash import pbkdf2_sha256

class Users(Base):
    __tablename__ = 'users'
    __table_args__ = {'autoload':True}

    def __init__(username, password):
        self.name = username.lower()
        self.set_password(password)

    def set_password(self, plaintext):
        self.pwhash = pbkdf2_sha256.hash(plaintext)

    def check_password(self, candidate):
        return pbkdf2_sha256.verify(candidate, self.pwhash)

class Games(Base):
    __tablename__ = 'games'
    __table_args__ = {'autoload':True}

class Players(Base):
    __tablename__ = 'players'
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

class Posts(Base):
    __tablename__ = 'posts'
    __table_args__ = {'autoload':True}
