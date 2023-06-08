from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

# Création de la base de données SQLite
engine = create_engine('sqlite:///requetes_gratuites.db')
Base = declarative_base()


class UserRequest(Base):
    __tablename__ = 'user_requests'

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    question = Column(String)
    completor = Column(String)
    request_date = Column(DateTime, default=datetime.now)


# Création des tables dans la base de données
Base.metadata.create_all(engine)
# Création d'une session SQLAlchemy
Session = sessionmaker(bind=engine)
