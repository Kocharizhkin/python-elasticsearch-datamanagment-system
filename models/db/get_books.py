import os

from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, MetaData, Table, Float, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

database_url = os.getenv('ASYNC_DATABASE_URL')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    isbn = Column(String, unique=True)
    author = Column(String)
    title = Column(String)
    publication_year = Column(String)

    def get_next_entries(self, last_entry_number=0, limit=20):
        try:
            # Query the next 20 books starting from the last_entry_number
            next_books = session.query(Book).filter(Book.id > last_entry_number).order_by(Book.id).limit(limit).all()
            books_json = [book.to_json() for book in next_books]
            return books_json
        except SQLAlchemyError as e:
            # Handle any errors that occur during the query
            print(f"An error occurred: {e}")
            return []
        
    @staticmethod
    def get_id_columns():
        # Inspect the columns of the Book table
        inspector = inspect(engine)
        columns = inspector.get_columns('books')
        # Filter columns that end with '_id'
        id_columns = [col['name'] for col in columns if col['name'].endswith('_id')]
        return id_columns

    def get_related_data(self):
        id_columns = self.get_id_columns()
        try:
            # Query the book with its ID and get the specified columns
            book = session.query(Book).with_entities(*[getattr(Book, col) for col in id_columns]).filter(Book.id == self.id).first()
            if book:
                return {col: getattr(book, col) for col in id_columns}
            else:
                return None
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return None
        
    @staticmethod
    def get_supplier_info(book_id):
        id_columns = Book.get_id_columns()
        supplier_info_list = []

        try:
            # Reflect the book table and fetch the row for the given book ID
            book_table = Table(Book.__tablename__, MetaData(), autoload_with=engine)
            result = session.execute(
                book_table.select().where(book_table.c.id == book_id)
            )
            book_entry = result.fetchone()
            if not book_entry:
                return []

            for col in id_columns:
                supplier_table_ids = getattr(book_entry, col, None)
                if supplier_table_ids is not None and isinstance(supplier_table_ids, list):
                    table_name = col[:-3]  # Get the supplier table name

                    # Dynamically reflect the supplier table
                    supplier_table = Table(table_name, MetaData(), autoload_with=engine)

                    # Query the supplier table for each supplier ID in the list
                    for supplier_table_id in supplier_table_ids:
                        result = session.execute(
                            supplier_table.select().where(supplier_table.c.id == supplier_table_id)
                        )
                        data = result.fetchone()

                        if data:
                            # Correct way to convert row data to dict
                            data_dict = {column.name: getattr(data, column.name) for column in supplier_table.columns}
                            supplier_info_list.append({table_name: data_dict})
                            print(supplier_info_list)

            return supplier_info_list
        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            return None
        

    def to_json(self):
    # Create a dictionary representation of the book instance
        return {
            'id': self.id,
            'isbn': self.isbn,
            'author': self.author,
            'title': self.title,
            'publication_year': self.publication_year
        }