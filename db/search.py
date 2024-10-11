import os
from urllib.parse import urlparse
from elasticsearch import AsyncElasticsearch, NotFoundError
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd
import traceback

from db.storage.books import Book

class Search():

    def __init__(self):
        # Elasticsearch client setup
        elastic_url = os.getenv("ELASTICSEARCH_URL")
        self.es_client = AsyncElasticsearch(elastic_url)
        self.book = Book()

        # SQLAlchemy engine and session setup
        database_url = os.getenv('SYNC_DATABASE_URL')
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def connect_to_db(self):
        # The engine and session are now managed using SQLAlchemy.
        session = self.Session()
        return session

    def get_prices(self, book_id):
        suppliers_info = self.book.get_supplier_info(book_id)
        prices = ''
        for entry in suppliers_info:
            if entry:
                supplier_name, supplier_info = next(iter(entry.items()), ('', {}))
                supplier_price = supplier_info.get('supplier_price', '')

                if supplier_name and supplier_price:
                    prices += f"{supplier_name.replace('_', ' ')}: €{supplier_price} "     

        return prices

    async def search_by_es(self, search_params, single_term: bool):
        try:
            # Sanitize and format the search parameters
            if not single_term:
                search_params = {key: value for key, value in search_params.items() if value}

            es_query = await self._construct_es_query(search_params=search_params, single_term=single_term)
            

            # Execute the asynchronous Elasticsearch search
            response = await self.es_client.search(index="books", body=es_query)

            # Extract the data from the Elasticsearch response
            data = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                data.append({
                    'id': source['id'],
                    'isbn': source['isbn'],
                    'author': source['author'],
                    'title': source['title'],
                    'publication_year': source['publication_year'],
                    'publisher': source['publisher'],
                })

            return data
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())


    async def do_we_have_this_book(self, input_book_row):

        input_year = str(input_book_row['publication_year']).replace('.0', '')
        
        search_params = {
            'isbn': input_book_row['isbn'],
            'author': input_book_row['author'],
            'title': input_book_row['title'],
            'publication_year': input_year,
        }

        if 'publisher' in input_book_row.keys():
            search_params['publisher'] = input_book_row['publisher']

        search_results = await self.search_by_es(search_params)

        if search_results:
            with open('./update_progress.txt', 'a') as f:
                f.write(f'input row: {search_params}\nsearch_result:\n{search_results}\n\n\n')
            return search_results['id']
        
        else:
            with open('./update_unmatched.txt', 'a') as f:
                f.write(f'input row: {input_book_row}\nsearch_params:\n{search_params}\n\n\n')
            return False
        

        
    async def _construct_es_query(self, search_params, single_term: bool):
        if single_term:
            # When search is a single term, use query_string for matching across all fields.
            query = {
                "query": {
                    "query_string": {
                        "query": search_params
                    }
                }
            }
            return query  # Return the query for single term search.
        else:
            must_conditions = []
            for key, value in search_params.items():
                # Create match conditions for each key-value pair.
                match_query = {
                    "match": {
                        f"{key}": {
                            "query": value,
                            "operator": "and"
                        }
                    }
                }
                must_conditions.append(match_query)

            # Construct the full Elasticsearch query for multiple terms.
            es_query = {
                "query": {
                    "bool": {
                        "must": must_conditions
                    }
                },
                "size": 30  # Set the limit to 30.
            }
            return es_query 



    async def call_search_for_row(self, row):
        print(f'call serch for row {row}')
        # Replace commas with underscores in the values of the dictionary
        search_terms = {key: str(value).replace(',', '_') for key, value in row.items()}
        search_terms = {key: value for key, value in search_terms.items() if value != '<NA>'}

        print(f'serch terms {search_terms}')

        results = await self.search_by_es(search_params=search_terms)

        df = pd.DataFrame(results)

        # Save the DataFrame to a CSV file
        filename_parts = [str(search_terms.get(field, '')) for field in ['author', 'title', 'publication_year']]
        xlsx_filename = "-".join(part.replace(" ", "-") for part in filename_parts if part)

        # Add additional information or suffix to the filename if needed
        xlsx_filename += "-mkniga-search.xlsx"
        df.to_excel('static/files/' + xlsx_filename, index=False)

        return xlsx_filename

    async def bulk_search(self, bytes):
        df = pd.read_excel(bytes)

        expected_columns = ['isbn', 'author', 'title', 'publication_year', 'publisher']

        # Check if the first row contains the expected column names
        if all(item in expected_columns for item in df.iloc[0]):
            df.columns = df.iloc[0]  # Rename columns
            df = df[1:]  # Remove the first row
            df.reset_index(drop=True, inplace=True)  # Reset index after dropping the row

        columns_to_drop = [
            col for col in df.columns
            if col not in expected_columns and
            df.iloc[0][col] not in expected_columns
        ]

        # Drop the identified columns
        df.drop(columns=columns_to_drop, inplace=True)
        df = df.convert_dtypes()
        print(df)

        results_dict = {}
        for _, row in df.iterrows():
            result = await self.call_search_for_row(row)
            sheet_name = result.replace('-mkniga-search.xlsx', '')
            results_dict[sheet_name] = pd.read_excel('static/files/' + result)
            os.remove('static/files/' + result)

        excel_filename = f"files/mkniga_search_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        with pd.ExcelWriter('static/' + excel_filename) as writer:
            # Iterate through the dictionary and write each DataFrame to a sheet
            for sheet_name, df in results_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        return excel_filename