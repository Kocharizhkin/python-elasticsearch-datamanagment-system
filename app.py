from quart import Quart, jsonify, request, url_for
from quart_cors import cors


import os
import json
import asyncio
import traceback
from io import BytesIO
import pandas as pd
from urllib.parse import quote
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from models.db.get_books import Book
from models.db.search import Search
from models.db.column_mapping import Mapping
from models.db.update_data_in_db import DatabaseUpdater, Updates


# Database URI
database_url = os.getenv('ASYNC_DATABASE_URL')
elasticsearch_url = os.getenv('ELASTICSEARCH_URL')

engine = create_async_engine(database_url)
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Create an instance of the Book class
books = Book()
search = Search()
mapping = Mapping()
update_books_in_db = DatabaseUpdater()

# Initialize Quart app
app = Quart(__name__)
# Apply CORS to your app
app = cors(app)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

@app.route('/progress', methods=['GET'])
async def get_progress():
    async with Session() as session:
        progress = (await session.execute(select(Updates).order_by(Updates.id.desc()).limit(1))).scalar()
        if progress:
            return jsonify({
                'current_sheet': progress.current_sheet,
                'processed_rows': progress.processed_rows,
                'total_rows': progress.total_rows,
                'update_start_time': progress.update_start_time,
                'time_total': str(progress.time_total)
            })
        else:
            return jsonify({'error': 'Update ID not found'}), 404

@app.route('/get_books')
async def get_books():
    try:
        # Extracting the 'cardsPerRow' parameter from the request, defaulting to None if not provided
        cards_per_row = request.args.get('cardsPerRow', default=None, type=int)

        # Assuming get_next_entries can optionally take a number of entries to fetch
        # If cards_per_row is None, get_next_entries can default to a standard number
        entries = books.get_next_entries(limit=cards_per_row)

        return jsonify(entries)
    except Exception as e:
        # Handle exceptions, possibly logging them
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_book_supplier')
async def get_book_supplier():
    try:
        # Extracting the book ID parameter from the request
        book_id = request.args.get('bookId', default=None, type=int)

        # Validate that book_id is provided
        if book_id is None:
            return jsonify({'error': 'Book ID is required'}), 400

        # Assuming get_supplier_info is a method to fetch supplier details by book ID
        supplier_info = await books.get_supplier_info(book_id)

        return jsonify(supplier_info)
    except Exception as e:
        # Handle exceptions, possibly logging them
        return jsonify({'error': str(e)}), 500
    
async def call_search_for_row(row):
    print(f'call serch for row {row}')
    # Replace commas with underscores in the values of the dictionary
    search_terms = {key: str(value).replace(',', '_') for key, value in row.items()}
    search_terms = {key: value for key, value in search_terms.items() if value != '<NA>'}

    print(f'serch terms {search_terms}')

    results = await search.search_by_ts_vector(search_params = search_terms)

    df = pd.DataFrame(results)

    # Save the DataFrame to a CSV file
    filename_parts = [str(search_terms.get(field, '')) for field in ['author', 'title', 'publication_year']]
    xlsx_filename = "-".join(part.replace(" ", "-") for part in filename_parts if part)

    # Add additional information or suffix to the filename if needed
    xlsx_filename += "-mkniga-search.xlsx"
    df.to_excel('static/files/'+xlsx_filename, index=False)

    return xlsx_filename

@app.route("/search")
async def search_endpoint():
    # Get the search term from the request arguments
    if request.args.get('multiple'):
        # If multiple parameters are present, it means _switch is true
        multiple_params = request.args.get('multiple', default='', type=str)

        internal = request.args.get('internal', default=False, type=bool)

        search_terms = dict(param.split('=') for param in multiple_params.split(','))
        search_terms = {k: v.strip() for k, v in search_terms.items()}
        print(search_terms)

        # Check if saveToFile is present in the request
        save_to_file = request.args.get('saveToFile', default='false', type=str).lower() == 'true'

        print(f"Save to File: {save_to_file}")
        
        # Perform the search with the received parameters
        results = await search.search_by_ts_vector(search_params = search_terms)

        # Save to file if saveToFile is true (you need to implement this logic)
        if save_to_file:
            df = pd.DataFrame(results)

            # Save the DataFrame to a CSV file
            xlsx_filename = f"files/{search_terms['author']}-{search_terms['title']}-{search_terms['publication_year']}-mkniga-search.xlsx"
            xlsx_filename = xlsx_filename.replace("<NA>", "")
            df.to_excel('static/'+xlsx_filename, index=False)

            if internal:
                print('INTERNAL')
                return f"static/{xlsx_filename}"

            return url_for('static', filename=xlsx_filename, _external=True, _scheme='https')

        # Return the results
        return jsonify(results)
    else:
        # If _switch is false, get the search term directly
        search_term = request.args.get('searchTerm', default=None, type=str)
        search_term = search_term.strip()
        print(search_term)

        # Check if saveToFile is present in the request
        save_to_file = request.args.get('saveToFile', default='false', type=str).lower() == 'true'

        print(f"Save to File: {save_to_file}")

        # Perform the search
        results = await search.search_by_ts_vector(single_term = search_term)

        if save_to_file:
            # Create a Pandas DataFrame from results
            df = pd.DataFrame(results)

            # Save the DataFrame to a xlsx file
            xlsx_filename = f'files/{search_term}-mkniga-search.xlsx'
            df.to_excel('static/'+xlsx_filename, index=False)

            return url_for('static', filename=xlsx_filename, _external=True, _scheme='https')

        # Return the results
        return jsonify(results)
    
@app.route('/search', methods=['POST'])
async def upload_and_parse_file():
    uploaded_file = await request.files
    uploaded_file = uploaded_file['file']
    print('I am definitely in the right function')
    if uploaded_file:
        # Parse the uploaded file into a DataFrame
        file_content = uploaded_file.read()

        # Determine the file type based on the file extension
        file_extension = uploaded_file.filename.rsplit('.', 1)[-1].lower()

        if file_extension == 'xlsx':
            # For Excel files, use pd.read_excel
            df = pd.read_excel(BytesIO(file_content))
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        print(df)

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
            result = await call_search_for_row(row)
            sheet_name = result.replace('-mkniga-search.xlsx', '')
            results_dict[sheet_name] = pd.read_excel('static/files/' + result)
            os.remove('static/files/' + result)

        excel_filename = f"files/mkniga_search_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        with pd.ExcelWriter('static/' + excel_filename) as writer:
            # Iterate through the dictionary and write each DataFrame to a sheet
            for sheet_name, df in results_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        return url_for('static', filename=excel_filename, _external=True, _scheme='https')
    else:
        return 'No file in the request', 400

@app.route('/matching', methods=['POST'])
async def match_column_names():

        if 'file' not in await request.files:
            print("No file part in the request")
            return jsonify({"error": "No file part in the request"}), 400

        file_object = await request.files
        file = file_object['file']
        if file.filename == '':
            print("No selected file")
            return jsonify({"error": "No selected file"}), 400

        # Example: Save the file
        await file.save(f'models/db/upload/{file.filename}')

        # Accessing the sheet_column_mapping directly from the received JSON data
        sheet_column_mapping = await mapping.extract_column_names(file.filename)

        mapped_columns = {}

        for sheet_name, column_names in sheet_column_mapping.items():
            print(sheet_name)
            sheet_map = mapping.columns_mapping(sheet_name, column_names)
            print(sheet_map)
            mapped_columns.update(sheet_map)
            mapped_columns[sheet_name]['all_columns'] = sheet_column_mapping[sheet_name]

        return jsonify(mapped_columns)

@app.route('/upload_map', methods=['POST'])
async def upload_map():
    data = (await request.form).get("data")
    
    # Check if JSON data is empty
    if not data:
        return jsonify({"error": "JSON data is missing or empty"}), 400

    json_data = json.loads(data)

    # Check if json_data is empty
    if not json_data:
        return jsonify({"error": "JSON data is empty"}), 400
    
    mapping.update_map(json_data)
    return jsonify({"message": "Map uploaded successfully!"}), 200

@app.route('/update', methods=['POST'])
async def update():
    data = await request.json
    filename = data.get("filename")

    async def background_task(filename):
        try:
            await update_books_in_db.run_update(filename)
        except Exception as e:
            error_message = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}\n"
            with open("./update_errors.txt", "a") as f:
                f.write(error_message)

    # Start the background task
    asyncio.create_task(background_task(filename))
    
    # Return the response immediately
    return jsonify({"message": "Update started successfully!"}), 200

@app.route('/test_update')
async def test_update():

    async def background_task(filename):
        try:
            await update_books_in_db.run_update(filename)
        except Exception as e:
            error_message = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}\n"
            with open("./update_errors.txt", "a") as f:
                f.write(error_message)

    # Start the background task
    asyncio.create_task(background_task('mk_price_jun2023.xlsx'))
    
    # Return the response immediately
    return jsonify({"message": "Update started successfully!"}), 200



if __name__ == "__main__": 
    app.debug = True
    app.run(host='0.0.0.0', port=8000)