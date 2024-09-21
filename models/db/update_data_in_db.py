import time
from datetime import datetime, timedelta
import pandas as pd
import json
import re
import os
import numpy as np
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, JSON, MetaData, Table, text, update, insert, DateTime, Interval, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select

from models.db.init_db import tablesDefinition
from models.db.book_matching import BookSimilarity
from models.db.test.test_relations import Tests

# Database setup
prepare_db = tablesDefinition()
Base = declarative_base()

class Updates(Base):
    __tablename__ = 'updates'
    
    id = Column(Integer, primary_key=True)
    current_sheet = Column(String)
    processed_rows = Column(Integer)
    total_rows = Column(Integer)
    update_start_time = Column(DateTime, server_default=func.now())
    time_total = Column(Interval)

class Books(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    isbn = Column(String)
    author = Column(String)
    title = Column(String)
    publication_year = Column(String)
    publisher = Column(String)

class DatabaseUpdater:
    def __init__(self):
        self.db_search = BookSimilarity()
        self.test = Tests()
        self.DATABASE_URI = os.getenv('ASYNC_DATABASE_URL')
        self.engine = create_async_engine(self.DATABASE_URI)
        self.Session = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def sanitize_name(self, name):
        if name[0].isdigit():
            name = 'supplier_' + name
        return re.sub(r'\W+', '_', name)
    
    def sanitize_sheets_name(self, df):
        sanitized_sheets = {}
        for sheet_name in df.keys():
            sanitized_name = self.sanitize_name(sheet_name)
            sanitized_sheets[sanitized_name] = df[sheet_name]
        return sanitized_sheets

    async def preprocess_excel(self, filename):
        with open('models/db/fields_map.json') as file:
            map_file = json.load(file)
        df = pd.read_excel(f'models/db/upload/{filename}', engine='openpyxl', sheet_name=None)
        
        df = self.sanitize_sheets_name(df)
        df = self.rename_and_clean_columns(df, map_file)

        supplier_tables = await self.setup_supplier_tables(df)

        return df, supplier_tables

    def rename_and_clean_columns(self, df, map_file):
        import_sheets = df.keys()
        known_sources = map_file.keys()

        for sheet in known_sources:
            if sheet in import_sheets:
                mapped_fields = map_file[sheet]
                df[sheet] = self.rename_columns(df[sheet], mapped_fields)
                df[sheet] = self.clean_columns(df[sheet], mapped_fields)
        return df

    def rename_columns(self, sheet_df, mapped_fields):
        for field, col in mapped_fields.items():
            if col and field != 'special_fields':
                sheet_df = sheet_df.rename(columns={col: field})
        return sheet_df

    def clean_columns(self, sheet_df, mapped_fields):
        column_names = list(mapped_fields.keys())
        column_names.remove('special_fields')
        columns_to_delete = list(set(sheet_df.columns) - set(column_names))
        sheet_df.drop(columns=columns_to_delete, inplace=True)
        null_values = [None, 'Null', np.nan, '', ' ']
        sheet_df.replace(null_values, None, inplace=True)
        return sheet_df

    async def setup_supplier_tables(self, df):
        metadata = MetaData()
        supplier_tables = {}

        async with self.engine.begin() as conn:
            for sheet_name in df.keys():
                table_name = self.sanitize_name(sheet_name)
                await conn.run_sync(self._sync_inspect_table, table_name, supplier_tables, metadata)
        
        return supplier_tables

    def _sync_inspect_table(self, sync_conn, table_name, supplier_tables, metadata):
        supplier_table = Table(table_name, metadata, autoload_with=sync_conn)
        supplier_tables[table_name] = supplier_table
        setattr(Books, f"{table_name}_id", Column(JSON))

    async def update_db(self, df, supplier_tables):
        time_start = time.time()
        total_rows = sum(len(sheet_df) for sheet_df in df.values())
        processed_rows = 0

        async with self.Session() as session:
            await session.execute(
                insert(Updates).values(
                    current_sheet='',
                    processed_rows=0,
                    total_rows=total_rows
                )
            )
            await session.commit()

            update_id = (await session.execute(select(Updates.id).order_by(Updates.id.desc()).limit(1))).scalar()

            for sheet_name, sheet_df in df.items():
                with open("./update_errors.txt", "a") as f:
                    f.write(f"\n\n\nnext sheet\n\n\n")
                supplier_table = supplier_tables.get(self.sanitize_name(sheet_name.lower()))
                if supplier_table is not None:
                    processed_rows = await self.process_sheet(session, update_id, sheet_df, supplier_table, sheet_name, total_rows, processed_rows)
        
        time_end = time.time()
        time_total = timedelta(seconds=(time_end - time_start))

        async with self.Session() as session:
            await session.execute(
                update(Updates).where(Updates.id == update_id).values(
                    time_total=time_total
                )
            )
            await session.commit()

        return time_total

    async def process_sheet(self, session, update_id, sheet_df, supplier_table, sheet_name, total_rows, processed_rows):
        await self.update_progress(session, update_id, sheet_name, processed_rows, total_rows)
        for input_book_row in sheet_df.to_dict('records'):
            if input_book_row['isbn'] == None:
                continue
            book_match = self.db_search.do_we_have_this_book(input_book_row)

            supplier_column = self.sanitize_name(sheet_name) + '_id'

            mapped_row = self.prepare_mapped_row(input_book_row)

            if book_match != None:
                await self.update_existing_books(session, mapped_row, book_match, supplier_table, supplier_column) 
            else:
                await self.insert_new_books(session, mapped_row, supplier_table, supplier_column)

            processed_rows += 1
            if processed_rows % 10 == 0:
                await self.update_progress(session, update_id, sheet_name, processed_rows, total_rows)

        return processed_rows

    async def update_existing_books(self, session, mapped_row, book_match, supplier_table, supplier_column):
        db_isbn = book_match['matched_isbn']
        try:
            book_by_isbn = await session.execute(
                select(Books).filter(Books.isbn == db_isbn)
            )
            book_by_isbn = book_by_isbn.scalar()
            supplier_table_ids = getattr(book_by_isbn, supplier_column, [])
            if supplier_table_ids is None:
                supplier_table_ids = []
            with open("./update_progress.txt", "a") as f:
                f.write(f"supplier_table_ids: {supplier_table_ids}, mapped_row: {mapped_row}, supplier_table: {supplier_table}, supplier_column: {supplier_column}\n\n")
            await self.upsert_supplier_table(session, supplier_table, mapped_row, supplier_table_ids)
            setattr(book_by_isbn, supplier_column, supplier_table_ids)

        except SQLAlchemyError as e:
            with open("./update_errors.txt", "a") as f:
                f.write(f"An error occurred while updating existing book: {e}\n")
            await session.rollback()

    async def insert_new_books(self, session, mapped_row, supplier_table, supplier_column):
        supplier_table_ids = []
        try:
            supplier_table_ids = await self.upsert_supplier_table(session, supplier_table, mapped_row, supplier_table_ids)
            new_book = Books(
                isbn=mapped_row['isbn'], author=mapped_row['author'],
                title=mapped_row['title'], publication_year=mapped_row['publication_year'],
                publisher=mapped_row['publisher'], **{supplier_column: supplier_table_ids}
            )
            session.add(new_book)
        except SQLAlchemyError as e:
            with open("./update_errors.txt", "a") as f:
                f.write(f"An error occurred while inserting new book: {e}\n")
            await session.rollback()
    
    async def upsert_supplier_table(self, session, supplier_table, mapped_row, supplier_table_ids):
        if supplier_table_ids != [] and mapped_row['id'] is not None and mapped_row['id'] in supplier_table_ids:
            update_query = (
                supplier_table.update()
                .where(supplier_table.c.id == mapped_row['id'])
                .values(**mapped_row)
            )
            await session.execute(update_query)
        else:
            ins = supplier_table.insert().values(**mapped_row)
            result = await session.execute(ins)
            mapped_row['id'] = result.inserted_primary_key[0]
            supplier_table_ids.append(mapped_row['id'])
        return supplier_table_ids
    async def update_progress(self, session, update_id, current_sheet, processed_rows, total_rows):
        
        await session.execute(
            update(Updates)
            .where(Updates.id == update_id)
            .values(
                current_sheet=current_sheet,
                processed_rows=processed_rows,
                total_rows=total_rows,
            )
        )
        await session.commit()

    def prepare_mapped_row(self, row):
        mapped_row = {
            'id': None,
            'update_date': datetime.today().date(),
            'publication_year': None,
            'page_count': None,
            'weight': None,
            'supplier_price': None,
            'display_price': None,
            'delivery_timelines': None,
            'isbn': None,
            'dimensions': None,
            'author': None,
            'book_supplier': None,
            'title': None,
            'publisher': None,
            'cover': None
        }

        for key, value in row.items():
            if key == 'id':
                try:
                    mapped_row[key] = int(value)
                except (TypeError, ValueError):
                    mapped_row[key] = None
            elif key == 'publication_year' or key == 'page_count':
                mapped_row[key] = str(value) if value is not None else None
            elif key in ['weight', 'supplier_price', 'display_price']:
                try:
                    mapped_row[key] = float(value)
                except (TypeError, ValueError):
                    mapped_row[key] = None
            else:
                mapped_row[key] = value
        
        return mapped_row

    def get_progress(self):
        return self.progress_tracker

    async def run_update(self, filename):
        with open("./update_progress.txt", "w") as f:
            f.write(" ")
        with open("./update_errors.txt", "w") as f:
            f.write(" ")
        with open('./update_search_results.txt', 'w') as f:
            f.write(" ")
        with open('./update_unmatched.txt', 'a') as f:
            f.write(" ")
        prepare_db.prepareStructure()
        df, supplier_tables = await self.preprocess_excel(filename)
        time_total = await self.update_db(df, supplier_tables)
        return time_total
