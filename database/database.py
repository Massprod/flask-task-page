from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


SQLALCHEMY_DB_URL = "sqlite:///database/database.db"

engine = create_engine(SQLALCHEMY_DB_URL,
                       pool_size=20,
                       max_overflow=-1,  # unlimited que to connect
                       )

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
