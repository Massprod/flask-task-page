from database.database import Base
from sqlalchemy import Column, String, Integer
from flask_login import UserMixin


class Users(Base, UserMixin):
    __tablename__ = "users"
    local_id: int = Column(Integer(), primary_key=True)
    id: int = Column(Integer(), nullable=False)
    login: str = Column(String(), nullable=False)
    token: str = Column(String(), nullable=True)
