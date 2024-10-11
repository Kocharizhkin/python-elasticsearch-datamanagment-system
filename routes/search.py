from quart import Blueprint, jsonify, request, url_for
import pandas as pd
from io import BytesIO

def create_search_blueprint(db):
    # Create a blueprint for books
    search_bp = Blueprint('search', __name__)

    @search_bp.route("/search")
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
            results = await db.search.search_by_es(search_params = search_terms, single_term = False)

            # Save to file
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
            results = await db.search.search_by_es(search_params = search_term, single_term  = True)

            if save_to_file:
                # Create a Pandas DataFrame from results
                df = pd.DataFrame(results)

                # Save the DataFrame to a xlsx file
                xlsx_filename = f'files/{search_term}-mkniga-search.xlsx'
                df.to_excel('static/'+xlsx_filename, index=False)

                return url_for('static', filename=xlsx_filename, _external=True, _scheme='https')

            # Return the results
            return jsonify(results)
        
        
    @search_bp.route('/search', methods=['POST'])
    async def upload_and_parse_file():
        uploaded_file = await request.files
        uploaded_file = uploaded_file['file']
        if uploaded_file:
            # Parse the uploaded file into a DataFrame
            file_content = uploaded_file.read()

            # Determine the file type based on the file extension
            file_extension = uploaded_file.filename.rsplit('.', 1)[-1].lower()

            if file_extension == 'xlsx':
                excel_filename = db.search.bulk_search(BytesIO(file_content))
                # For Excel files, use pd.read_excel
            else:
                return jsonify({'error': 'Unsupported file format'}), 400

            return url_for('static', filename=excel_filename, _external=True, _scheme='https')
        else:
            return 'No file in the request', 400
        
    return search_bp