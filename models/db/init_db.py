import psycopg2
import json
import re
import os
from urllib.parse import urlparse

class tablesDefinition:

    def prepareStructure(self):
        # Load the known sources from the JSON file
        with open('models/db/fields_map.json') as file:
            map_file = json.load(file)
        known_sources = list(map_file.keys())
        for i in range(len(known_sources)):
            known_sources[i] = self.sanitize_name(known_sources[i])
        known_sources = set(known_sources)

        # Get the full DATABASE_URL from environment variables
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

        try:
            cur = connection.cursor()

            # Retrieve existing tables
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            existing_tables = set(row[0].lower() for row in cur.fetchall())

            # Retrieve existing columns in the books table
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'books';")
            existing_columns = set(row[0].lower() for row in cur.fetchall())

            # Determine columns to add to the books table
            columns_to_add = {f'{source}_id' for source in known_sources} - existing_columns

            # Define the columns for the new tables
            new_table_columns = (
                "id SERIAL PRIMARY KEY, "
                "update_date DATE, "
                "publication_year VARCHAR(255), "
                "page_count VARCHAR(255), "
                "weight FLOAT, "
                "supplier_price FLOAT, "
                "display_price FLOAT, "
                "delivery_timelines TEXT, "
                "isbn VARCHAR(255), "
                "dimensions VARCHAR(255), "
                "author VARCHAR(255), "
                "book_supplier VARCHAR(255), "
                "title VARCHAR(255), "
                "publisher VARCHAR(255), "
                "cover TEXT"
            )

            # Create missing tables and add missing columns to the books table
            for table in known_sources - existing_tables:
                table_lower = table.lower()
                cur.execute(f"CREATE TABLE {table_lower} ({new_table_columns});")

            for column in columns_to_add:
                table_lower = column.lower()
                table_lower = table_lower.replace('_id', '')
                cur.execute(f"""
                ALTER TABLE books 
                ADD COLUMN {column} JSON;
                """)

            connection.commit()

        except Exception as e:
            print("An error occurred:", e)
            connection.rollback()

        finally:
            connection.close()

    def sanitize_name(self, name):
        # Check if the name starts with a digit and prefix with 'supplier_' if it does
        if name[0].isdigit():
            name = 'supplier_' + name

        # Replace any non-alphanumeric character with an underscore
        return re.sub(r'\W+', '_', name)