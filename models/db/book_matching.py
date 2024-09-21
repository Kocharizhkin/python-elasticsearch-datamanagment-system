import psycopg2
import pandas as pd
import numpy as np
import os
from urllib.parse import urlparse

class BookSimilarity:

    def __init__(self):
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
        
        self.db_config = db_config

        # Establish the connection using psycopg2
        self.connection = psycopg2.connect(**db_config)

    def levenshteinDistanceDP(self, token1, token2):
        token1, token2 = str(token1), str(token2)
        distances = np.zeros((len(token1) + 1, len(token2) + 1))

        for t1 in range(len(token1) + 1):
            distances[t1][0] = t1

        for t2 in range(len(token2) + 1):
            distances[0][t2] = t2

        for t1 in range(1, len(token1) + 1):
            for t2 in range(1, len(token2) + 1):
                if token1[t1 - 1] == token2[t2 - 1]:
                    distances[t1][t2] = distances[t1 - 1][t2 - 1]
                else:
                    distances[t1][t2] = min(distances[t1 - 1][t2] + 1,
                                            distances[t1][t2 - 1] + 1,
                                            distances[t1 - 1][t2 - 1] + 1)
        return distances[len(token1)][len(token2)]

    def sanitize_tsquery_input(self, input_string):
        # Join terms with the '&' operator for tsquery
        tsquery_string = ' & '.join(input_string.split())
        return tsquery_string

    def search_by_ts_vector(self, search_params):
        with self.connection.cursor() as cursor:
            # Sanitize and format the search parameters
            search_params = {key: value for key, value in search_params.items() if value}
            search_params = {key: self.sanitize_tsquery_input(value) for key, value in search_params.items()}
            
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
            cursor.execute(query, query_params)
            db_rows = cursor.fetchall()

        data = []
        for result in db_rows:
            data.append({
                'id': result[0],
                'isbn': result[1],
                'author': result[2],
                'title': result[3],
                'publication_year': result[4],
                'publisher': result[5],
            })

        return data

    def do_we_have_this_book(self, input_book_row):

        input_isbn = input_book_row['isbn']
        input_author = input_book_row['author']
        input_title = input_book_row['title']
        input_year = str(input_book_row['publication_year']).replace('.0', '')
        if 'publisher' in input_book_row.keys():
            input_publisher = input_book_row['publisher']

        search_params = {
            'isbn': input_isbn,
            'author': input_author,
            'title': input_title,
            'publication_year': input_year,
        }

        if 'publisher' in input_book_row.keys():
            search_params['publisher'] = input_publisher

        search_results = self.search_by_ts_vector(search_params)

        if search_results:
            
            db_book = search_results[0]
            db_isbn = db_book['isbn']
            db_author = db_book['author']
            db_title = db_book['title']
            db_year = str(db_book['publication_year']).replace('.0', '')
            db_publisher = db_book['publisher']

            return {'book_isbn': input_isbn, 'matched_isbn': db_isbn}

            distances = [
                self.levenshteinDistanceDP(input_author, db_author) if input_author and db_author else float('inf'),
                self.levenshteinDistanceDP(input_title, db_title) if input_title and db_title else float('inf'),
                self.levenshteinDistanceDP(input_year, db_year) if input_year and db_year else float('inf'),
                self.levenshteinDistanceDP(input_publisher, db_publisher) if input_publisher and db_publisher else float('inf')
            ]

            valid_distances = [d for d in distances if d != float('inf')]
            if valid_distances and sum(valid_distances) / len(valid_distances) < 50:
                return {'book_isbn': input_isbn, 'matched_isbn': db_isbn}
            else:
                with open('./update_unmatched.txt', 'a') as f:
                    f.write(f'input row: {input_book_row}\nmatch: {db_book}\ndistance: {sum(valid_distances) / len(valid_distances)}\n\n\n')
                return None
        else:
            with open('./update_unmatched.txt', 'a') as f:
                f.write(f'input row: {input_book_row}\nsearch_params:\n{search_params}\n\n\n')
    