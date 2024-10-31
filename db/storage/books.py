import os
import traceback

from sqlalchemy import create_engine, MetaData, Table, inspect, select
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from db.models import Book

database_url = os.getenv('ASYNC_DATABASE_URL')
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

class BooksStorage():

    async def get_next_entries(self, last_entry_number=0, limit=20):
        try:
            async with self.driver.session_scope_async() as session:
                # Query the next 20 books asynchronously starting from the last_entry_number
                stmt = select(Book).filter(Book.id > last_entry_number).order_by(Book.id).limit(limit)
                result = await session.execute(stmt)
                next_books = result.scalars().all()
                books_json = [book.to_dict() for book in next_books]
                return books_json
        except SQLAlchemyError as e:
            # Handle any errors that occur during the query
            print(f"An error occurred: {e}")
            return []
        
    async def get_id_columns(self):
        # Access the async engine directly without calling it
        async_engine: AsyncEngine = self.driver.async_engine

        # Use async connection
        async with async_engine.connect() as connection:
            # Run the inspection in a synchronous block
            columns = await connection.run_sync(self._get_columns_sync)

        # Filter columns that end with '_id'
        id_columns = [col['name'] for col in columns if col['name'].endswith('_id')]
        return id_columns

    # Helper function to run synchronous inspection
    def _get_columns_sync(self, connection):
        inspector: Inspector = inspect(connection)  # Use sync connection here
        return inspector.get_columns('books')

    async def get_related_data(self):
        id_columns = await self.get_id_columns()
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
        
    async def get_supplier_info(self, book_id): 
        id_columns = await self.get_id_columns()
        supplier_info_list = []
        
        try:
            async with self.driver.session_scope_async() as session:
                # Obtain an async connection by awaiting the connection coroutine
                conn = await session.connection()

                # Define a function to reflect the table synchronously
                def reflect_table(connection, table_name):
                    metadata = MetaData()
                    return Table(table_name, metadata, autoload_with=connection)

                # Reflect the book table using run_sync with the connection
                book_table = await conn.run_sync(reflect_table, Book.__tablename__)
                stmt = select(book_table).where(book_table.c.id == book_id)
                result = await session.execute(stmt)
                book_entry = result.fetchone()

                if not book_entry:
                    return []

                # Loop through ID columns and fetch supplier info
                for col in id_columns:
                    supplier_table_ids = getattr(book_entry, col, None)

                    if supplier_table_ids is not None and isinstance(supplier_table_ids, list):
                        table_name = col[:-3]  # Get the supplier table name

                        # Reflect the supplier table using run_sync with the connection
                        supplier_table = await conn.run_sync(reflect_table, table_name)

                        # Query the supplier table for each supplier ID in the list
                        for supplier_table_id in supplier_table_ids:
                            stmt = select(supplier_table).where(supplier_table.c.id == supplier_table_id)
                            supplier_result = await session.execute(stmt)
                            data = supplier_result.fetchone()

                            if data:
                                # Convert row data to a dictionary
                                data_dict = {column.name: getattr(data, column.name) for column in supplier_table.columns}
                                supplier_info_list.append({table_name: data_dict})

                return supplier_info_list

        except SQLAlchemyError as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()
            return None
        
    async def update_existing_books(self, session: AsyncSession, mapped_row: dict, matched_id: int, supplier_table, supplier_column: str) -> None:
        """
        Updates an existing book record with data from the mapped row and supplier info.
        """

        try:
            book_by_id = await session.execute(
                select(Book).filter(Book.id == matched_id)
            )
            book_by_id = book_by_id.scalar()
            
            supplier_table_ids = getattr(book_by_id, supplier_column, [])
            if supplier_table_ids is None:
                supplier_table_ids = []
            
            # Update supplier table entries
            await self.upsert_supplier_table(session, supplier_table, mapped_row, supplier_table_ids)
            
            # Set updated supplier IDs
            setattr(book_by_id, supplier_column, supplier_table_ids)
            
            await session.commit()

        except SQLAlchemyError as e:
            print(e)
            await session.rollback()

    async def insert_new_books(self, session: AsyncSession, mapped_row: dict, supplier_table, supplier_column: str) -> None:
        """
        Inserts a new book record into the database and associates it with a supplier.
        """
        supplier_table_ids = []
        try:
            # Insert into supplier table and get IDs
            supplier_table_ids = await self.upsert_supplier_table(session, supplier_table, mapped_row, supplier_table_ids)
            
            # Create and add a new book record
            new_book = Book(
                isbn=mapped_row['isbn'], 
                author=mapped_row['author'],
                title=mapped_row['title'], 
                publication_year=mapped_row['publication_year'],
                publisher=mapped_row['publisher'], 
                **{supplier_column: supplier_table_ids}
            )
            session.add(new_book)
            
            await session.commit()
            return new_book

        except SQLAlchemyError as e:
            print(e)
            await session.rollback()
            return False


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