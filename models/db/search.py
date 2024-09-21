import psycopg2
import os
from urllib.parse import urlparse
from models.db.get_books import Book

book = Book()

class Search():
    def connect_to_db(self):
        database_url = os.getenv('SYNC_DATABASE_URL')

        # Parse the DATABASE_URL to extract individual components
        result = urlparse(database_url)
        
        db_config = {
            'dbname': result.path[1:],  # Remove the leading '/' from the path
            'user': result.username,
            'password': result.password,
            'host': result.hostname,
            'port': result.port
        }

        # Establish the connection using psycopg2
        connection = psycopg2.connect(**db_config)
        return connection
    
    def get_prices(self, book_id):
        suppliers_info = book.get_supplier_info(book_id)
        prices = ''
        for entry in suppliers_info:
            if entry:
                supplier_name, supplier_info = next(iter(entry.items()), ('', {}))
                supplier_price = supplier_info.get('supplier_price', '')

                if supplier_name and supplier_price:
                    prices += f"{supplier_name.replace('_', ' ')}: €{supplier_price} "     

        return prices
    
    async def search_by_ts_vector(self, search_params={}, single_term=False):
        connection = self.connect_to_db()
        cursor = connection.cursor()

        if single_term:
            print('single word')
            # single_term = single_term.replace(' ', ' & ')
            # Use tsquery for single term search
            query = """
            SELECT b.id, b.isbn, b.author, b.title, b.publication_year, b.publisher
            FROM books b
            JOIN book_tsvectors dt ON b.id = dt.book_id
            WHERE dt.tsv_all @@ plainto_tsquery('russian', %s)
            LIMIT 30
            """
            cursor.execute(query, (single_term,))
        else:
            print('multiple words')
            # Filter out empty values from search_params
            search_params = {key: value for key, value in search_params.items() if value != ''}

            # Replace spaces with ' & ' inside search_params values
            search_params = {key: value.replace(' ', ' & ') for key, value in search_params.items()}

            # Build the full-text search query dynamically
            conditions = []
            query_params = []
            for key, value in search_params.items():
                tsv_column = f"tsv_{key}"
                conditions.append(f"dt.{tsv_column} @@ plainto_tsquery('russian', %s)")
                query_params.append(value)

            conditions_combined = ' AND '.join(conditions)
            query = f"""
            SELECT b.id, b.isbn, b.author, b.title, b.publication_year, b.publisher
            FROM books b
            JOIN book_tsvectors dt ON b.id = dt.book_id
            WHERE {conditions_combined}
            LIMIT 30
            """

            # Execute the query with query_params
            cursor.execute(query, query_params)

        # Fetch all results
        db_rows = cursor.fetchall()

        connection.close()

        # Initialize lists
        data = []

        for result in db_rows:
            suppliers = self.get_prices(result[0])

            data.append({
                'id': result[0],
                'isbn': result[1],
                'author': result[2],
                'title': result[3],
                'publication_year': result[4],
                'publisher': result[5],
                'supliers': suppliers
            })

        return data
