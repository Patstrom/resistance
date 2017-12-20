from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
DB_DSN = os.environ["DSN"]
engine = create_engine('postgresql://{}'.format(DB_DSN), convert_unicode=True)
Base = declarative_base()
Base.metadata.reflect(engine)

def load_session():
    metadata = Base.metadata
    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)
    return session
