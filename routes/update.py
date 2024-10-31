from quart import Blueprint, jsonify, request
import json
import traceback

def create_update_blueprint(db):
    # Create a blueprint for books
    update_bp = Blueprint('update', __name__)

    @update_bp.route('/progress', methods=['GET'])
    async def get_progress():
        async with db.driver.session_scope_async() as session:
            result = await db.update.updates_storage.get_progress(session)
            if result:
                return jsonify(result)
            else:
                return jsonify({'error': 'Update ID not found'}), 404
            
    @update_bp.route('/matching', methods=['POST'])
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
            await file.save(f'db/upload/{file.filename}')

            # Accessing the sheet_column_mapping directly from the received JSON data
            data_preview = await db.mapping.extract_data_preview(file.filename)

            print(data_preview)

            mapped_columns = {}

            for sheet_name in data_preview:
                mapped_columns[sheet_name] = {}
                print(sheet_name)
                sheet_map = db.mapping.columns_mapping(sheet_name, data_preview[sheet_name]["column_names"])
                print(sheet_map)
                mapped_columns[sheet_name]['map'] = sheet_map[sheet_name]
                mapped_columns[sheet_name]['data_preview'] = data_preview[sheet_name]["data_preview"]

            return jsonify(mapped_columns)

    @update_bp.route('/upload_map', methods=['POST'])
    async def upload_map():
        data = (await request.form).get("data")
        
        # Check if JSON data is empty
        if not data:
            return jsonify({"error": "JSON data is missing or empty"}), 400

        json_data = json.loads(data)

        # Check if json_data is empty
        if not json_data:
            return jsonify({"error": "JSON data is empty"}), 400
        
        db.mapping.update_map(json_data)
        return jsonify({"message": "Map uploaded successfully!"}), 200

    @update_bp.route('/update', methods=['POST'])
    async def update():
        data = await request.json
        filename = data.get("filename")

        try:
            await db.update.run(filename)
        except Exception as e:
            error_message = f"Error: {str(e)}\nTraceback: {e}\n"
            print(error_message)
            traceback.print_exc()
        
        # Return the response immediately
        return jsonify({"message": "Update started successfully!"}), 200

    @update_bp.route('/test_update')
    async def test_update():

        try:
            await db.update.run('mk_price_jun2023.xlsx')
        except Exception as e:
            print(e)
    
        # Return the response immediately
        return jsonify({"message": "Update started successfully!"}), 200
    
    return update_bp