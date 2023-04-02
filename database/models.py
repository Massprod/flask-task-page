from database.database import Base
from sqlalchemy import Column, String, Integer
from flask_login import UserMixin


class Users(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer(), primary_key=True)
    login = Column(String(), nullable=False)
    token = Column(String(), nullable=True)
