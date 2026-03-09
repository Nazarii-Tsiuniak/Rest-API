from sqlalchemy import Column, Integer, String

from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
