import time
import os
from datetime import datetime, timedelta
import pandas as pd
import json
import re
import numpy as np
from elasticsearch import AsyncElasticsearch

from db.init_db import TablesDefinition
from db.search import Search
from db.storage.updates import UpdatesStorage
from db.storage.books import BooksStorage

class DatabaseUpdater:
    def __init__(self):
        self.db_schema = TablesDefinition()
        self.db_search = Search()
        self.updates_storage = UpdatesStorage()
        self.books_storage = BooksStorage()

        elastic_url = os.getenv("ELASTICSEARCH_URL")
        self.es_client = AsyncElasticsearch(elastic_url)
        

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
        with open('db/fields_map.json') as file:
            map_file = json.load(file)
        df = pd.read_excel(f'db/upload/{filename}', engine='openpyxl', sheet_name=None)
        
        df = self.sanitize_sheets_name(df)
        df = self.rename_and_clean_columns(df, map_file)

        supplier_tables = self.db_schema.setup_supplier_tables(df)

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

    async def update_db(self, df, supplier_tables):
        time_start = time.time()
        total_rows = sum(len(sheet_df) for sheet_df in df.values())
        processed_rows = 0

        async with self.driver.session_scope_async() as session:
            self.update = await self.updates_storage.create(session, total_rows=total_rows)

        for sheet_name, sheet_df in df.items():
            with open("./update_errors.txt", "a") as f:
                f.write(f"\n\n\nnext sheet\n\n\n")
            supplier_table = supplier_tables.get(self.sanitize_name(sheet_name.lower()))
            if supplier_table is not None:
                processed_rows = await self.process_sheet(session, self.update.id, sheet_df, supplier_table, sheet_name, total_rows, processed_rows)
        
        time_end = time.time()
        time_total = timedelta(seconds=(time_end - time_start))

        async with self.driver.session_scope_async() as session:
            self.updates_storage.update(session, self.update, {'time_total': time_total})

        return time_total
    

    async def process_sheet(self, session, update_id, sheet_df, supplier_table, sheet_name, total_rows, processed_rows):
        async with self.driver.session_scope_async() as session:
            await self.updates_storage.update(session, self.update, {'sheet_name': sheet_name, 'processed_rows': processed_rows, 'total_rows': total_rows})
        for input_book_row in sheet_df.to_dict('records'):
            if input_book_row['isbn'] == None:
                continue
            matched_id = await self.db_search.do_we_have_this_book(input_book_row)

            supplier_column = self.sanitize_name(sheet_name) + '_id'

            mapped_row = self.prepare_mapped_row(input_book_row)

            if matched_id:
                await self.books_storage.update_existing_books(session, mapped_row, matched_id, supplier_table, supplier_column) 
            else:
                new_book = await self.books_storage.insert_new_books(session, mapped_row, supplier_table, supplier_column)
                if new_book:
                    await self.update_es_index(new_book.to_dict())

            processed_rows += 1
            if processed_rows % 10 == 0:
                async with self.driver.session_scope_async() as session:
                    await self.updates_storage.update(session, self.update, {'sheet_name': sheet_name, 'processed_rows': processed_rows, 'total_rows': total_rows})

        return processed_rows
    
    
    async def update_es_index(self, book_data):
        """
        Add a new book entry to Elasticsearch if it was not found in search results.
        book_data should be a dictionary with keys: id, isbn, author, title, publication_year, publisher
        """
        # Ensure that all necessary fields are present in book_data
        required_fields = ['id', 'isbn', 'author', 'title', 'publication_year', 'publisher']
        for field in required_fields:
            if field not in book_data:
                raise ValueError(f"Missing required field: {field}")

        # Try to index the new book data in Elasticsearch
        try:
            await self.es_client.index(index="books", id=book_data['id'], body=book_data)
            return True
        except Exception as e:
            return f"Failed to add book to Elasticsearch: {e}"
        

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
    


    async def run(self, filename):
        with open("./update_progress.txt", "w") as f:
            f.write(" ")
        with open("./update_errors.txt", "w") as f:
            f.write(" ")
        with open('./update_search_results.txt', 'w') as f:
            f.write(" ")
        with open('./update_unmatched.txt', 'a') as f:
            f.write(" ")
        self.db_schema.prepare_structure()
        df, supplier_tables = await self.preprocess_excel(filename)
        time_total = await self.update_db(df, supplier_tables)
        return time_total
