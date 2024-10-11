import json
import re
import os

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, Date, Text, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import urlparse
from db.models import Book

class TablesDefinition:

    def prepare_structure(self):
        # Load the known sources from the JSON file
        with open('db/fields_map.json') as file:
            map_file = json.load(file)
        known_sources = set(self.sanitize_name(source) for source in map_file.keys())

        # Get the full DATABASE_URL from environment variables
        database_url = os.getenv('SYNC_DATABASE_URL')
        
        # Create an SQLAlchemy engine
        self.engine = create_engine(database_url)

        # Create a session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        try:
            # Reflect the existing database schema
            metadata = MetaData()
            metadata.reflect(bind=self.engine)

            # Get existing tables
            existing_tables = set(metadata.tables.keys())

            # Check if the 'books' table exists and inspect its columns
            if 'books' in existing_tables:
                books_table = metadata.tables['books']
                existing_columns = set(books_table.c.keys())
            else:
                existing_columns = set()

            # Columns to add to the books table
            columns_to_add = {f'{source}_id' for source in known_sources} - existing_columns

            # Define new table columns
            new_table_columns = [
                Column('id', Integer, primary_key=True),
                Column('update_date', Date),
                Column('publication_year', String(255)),
                Column('page_count', String(255)),
                Column('weight', Float),
                Column('supplier_price', Float),
                Column('display_price', Float),
                Column('delivery_timelines', Text),
                Column('isbn', String(255)),
                Column('dimensions', String(255)),
                Column('author', String(255)),
                Column('book_supplier', String(255)),
                Column('title', String(255)),
                Column('publisher', String(255)),
                Column('cover', Text),
            ]

            # Create missing tables for each known source
            for table_name in known_sources - existing_tables:
                table = Table(table_name, metadata, *new_table_columns)
                table.create(self.engine)

            # Add missing columns to the books table
            if 'books' in existing_tables:
                with self.engine.connect() as conn:
                    for column in columns_to_add:
                        conn.execute(f"ALTER TABLE books ADD COLUMN {column} JSON;")

            self.session.commit()

        except SQLAlchemyError as e:
            print("An error occurred:", e)
            self.session.rollback()

        finally:
            self.session.close()

    def sanitize_name(self, name):
        # Check if the name starts with a digit and prefix with 'supplier_' if it does
        if name[0].isdigit():
            name = 'supplier_' + name

        # Replace any non-alphanumeric character with an underscore
        return re.sub(r'\W+', '_', name)
    
    def setup_supplier_tables(self, df):
        metadata = MetaData()
        supplier_tables = {}

        with self.engine.connect() as conn:
            for sheet_name in df.keys():
                table_name = self.sanitize_name(sheet_name)
                supplier_table = self._inspect_table(conn, table_name, metadata)
                supplier_tables[table_name] = supplier_table
                # Dynamically add a JSON column to Book for this table
                self._add_json_column(Book, table_name)

        return supplier_tables

    def _inspect_table(self, conn, table_name, metadata):
        return Table(table_name, metadata, autoload_with=conn)

    def _add_json_column(self, model, table_name):
        column_name = f"{table_name}_id"
        if not hasattr(model, column_name):
            setattr(model, column_name, Column(JSON))
