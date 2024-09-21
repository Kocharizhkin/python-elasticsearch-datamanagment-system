import pandas as pd
import json

def find_common_rows(all_sheets, mapping, rows_limit=10):
    combined_data = pd.DataFrame()
    selected_data = {}
    errors = []

    # Combining data from all sheets with an additional column for sheet name
    for sheet_name, data in all_sheets.items():
        column_map = mapping.get(sheet_name, {})
        isbn_col = column_map.get('isbn')
        author_col = column_map.get('author')
        title_col = column_map.get('title')
        pub_year_col = column_map.get('publication_year')

        # Check if necessary columns exist in this sheet
        if isbn_col and author_col and title_col:
            combined_data = pd.concat([combined_data, data.assign(SheetName=sheet_name)])
        else:
            errors.append(f"Missing key columns in sheet '{sheet_name}'")
            continue

    # Finding common rows based on key columns
    key_columns = [isbn_col, author_col, title_col, pub_year_col]
    combined_data['is_common'] = combined_data[key_columns].duplicated(keep=False)

    # Extracting common rows from each sheet
    common_rows = combined_data[combined_data['is_common']]
    for sheet_name in all_sheets.keys():
        sheet_common_rows = common_rows[common_rows['SheetName'] == sheet_name].head(rows_limit)
        selected_data[sheet_name] = sheet_common_rows.drop(columns=['SheetName', 'is_common'])

    return selected_data, errors

def create_smaller_excel(original_file_path, new_file_path, mapping, rows_limit=10):
    all_sheets = pd.read_excel(original_file_path, sheet_name=None)
    selected_data, errors = find_common_rows(all_sheets, mapping, rows_limit)

    with pd.ExcelWriter(new_file_path) as writer:
        for sheet_name, data in selected_data.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)

    return errors

# Load the column mappings from the JSON file
with open('fields_map.json', 'r') as file:
    column_mapping = json.load(file)

original_file_path = 'test_data.xlsx'
new_file_path = 'sample_dataset.xlsx'

errors = create_smaller_excel(original_file_path, new_file_path, column_mapping)

# Print errors, if any
if errors:
    print("Errors encountered:")
    for error in errors:
        print(error)
