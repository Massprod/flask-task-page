from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


SQLALCHEMY_DB_URL = "sqlite:///database/database.db"

engine = create_engine(SQLALCHEMY_DB_URL)

Session = sessionmaker(autoflush=False,
                       autocommit=False,
                       bind=engine,
                       )

Base = declarative_base()


def get_session():
    db = Session()
    try:
        yield db
    finally:
        db.close()
