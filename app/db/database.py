from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


# Creates a bridge between the database and the application, allowing us to create sessions to interact with the database
engine = create_engine(settings.DATABASE_URL)

# Session Maker is a factory for creating new Session objects, which are used to interact with the database
# Each API request will get its own session, ensuring thread safety and proper resource management
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for our SQLAlchemy models. All models will inherit from this class, which provides the underlying functionality for mapping Python classes to database tables.
class Base(DeclarativeBase):
    pass


def get_db():
    # Creates a new session
    db = SessionLocal()
    try:
        # Gives session to an API route
        yield db
    finally:
        db.close()


# def init_db():
#     """Initialize database tables"""
#     # Imports models to ensure they are registered with SQLAlchemy before creating tables
#     from app.models.sqlmodels import User, Project, Bug, Comment
#     Base.metadata.create_all(bind=engine)



