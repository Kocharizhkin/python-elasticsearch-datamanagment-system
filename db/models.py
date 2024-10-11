from sqlalchemy import Column, String, Integer, DateTime, Interval, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Update(Base):
    __tablename__ = 'updates'
    id = Column(Integer, primary_key=True)
    current_sheet = Column(String)
    processed_rows = Column(Integer)
    total_rows = Column(Integer)
    update_start_time = Column(DateTime, server_default=func.now())
    time_total = Column(Interval)

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    isbn = Column(String)
    author = Column(String)
    title = Column(String)
    publication_year = Column(String)
    publisher = Column(String)

    def to_dict(self):
        return {
            'id': self.id,
            'isbn': self.isbn,
            'author': self.author,
            'title': self.title,
            'publication_year': self.publication_year,
            'publisher': self.publisher
        }