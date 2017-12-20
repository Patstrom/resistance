from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
database_url = os.environ["DATABASE_URL"]
engine = create_engine(database_url, convert_unicode=True)
Base = declarative_base()
Base.metadata.reflect(engine)

def load_session():
    metadata = Base.metadata
    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)
    return session
