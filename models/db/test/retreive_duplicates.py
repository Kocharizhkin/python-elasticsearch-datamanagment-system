import pandas as pd
import json

def find_common_books(all_sheets, mapping, rows_per_sheet=5):
    combined_data = pd.DataFrame()
    errors = []

    for sheet_name, data in all_sheets.items():
        print(f"Columns in sheet '{sheet_name}': {data.columns.tolist()}")  # Print column names

        column_map = mapping.get(sheet_name, {})
        isbn_col = column_map.get('isbn')
        author_col = column_map.get('author')
        title_col = column_map.get('title')
        pub_year_col = column_map.get('publication_year')
        # Check for missing columns and log errors
        missing_columns = [col for col in [isbn_col, author_col, title_col, pub_year_col] if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing columns {missing_columns} in sheet '{sheet_name}'")
            continue

        combined_data = pd.concat([combined_data, data[[isbn_col, author_col, title_col, pub_year_col]].assign(SheetName=sheet_name)])

    if not combined_data.empty:
        common_books = combined_data.duplicated(subset=[isbn_col, author_col, title_col, pub_year_col], keep=False)
        selected_data = {}

        for sheet_name, data in all_sheets.items():
            column_map = mapping.get(sheet_name, {})
            isbn_col = column_map.get('isbn')
            author_col = column_map.get('author')
            title_col = column_map.get('title')
            pub_year_col = column_map.get('publication_year')

            for _, book in combined_data[common_books].iterrows():
                matching_rows = data[(data[isbn_col] == book[isbn_col]) & 
                                     (data[author_col] == book[author_col]) & 
                                     (data[title_col] == book[title_col]) & 
                                     (data[pub_year_col] == book[pub_year_col])]
                selected_rows = matching_rows.head(rows_per_sheet)

                if sheet_name in selected_data:
                    selected_data[sheet_name] = pd.concat([selected_data[sheet_name], selected_rows])
                else:
                    selected_data[sheet_name] = selected_rows
    else:
        selected_data = {}

    return selected_data, errors

def create_smaller_excel(original_file_path, new_file_path, mapping, rows_per_sheet=5):
    all_sheets = pd.read_excel(original_file_path, sheet_name=None)
    selected_data, errors = find_common_books(all_sheets, mapping, rows_per_sheet)

    with pd.ExcelWriter(new_file_path) as writer:
        for sheet_name, data in selected_data.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)

    return errors

# Load the column mappings from the JSON file
with open('fields_map.json', 'r') as file:
    column_mapping = json.load(file)

original_file_path = 'mk_price.xlsx'  # Replace with your file path
new_file_path = 'test_data.xlsx'  # Replace with your desired new file path

errors = create_smaller_excel(original_file_path, new_file_path, column_mapping)

# Print errors, if any
if errors:
    print("Errors encountered:")
    for error in errors:
        print(error)

'''


stash

def define_publisher_id(line):
    isbn = str(line['isbn']).replace("-", "")
    isbn = isbn.replace(" ","")
    isbn = isbn.replace("х","X")
    isbn = isbn.replace("Х","X")

    country_codes = {"Russia" : "5",
                     "Belarus" : "985",
                     "Ukraine" : "966",
                     "Kazakhstan" : "601",
                     "Armenia" : "9939",
                     "Germany" : "3"

    }

    isbn_13_patterns = {"Russia" : r"\b\d{3}5\d{8}[\dXx]\b",
                        "Belarus" : r"\b\d{3}985\d{6}[\dXx]\b",
                        "Ukraine" : r"\b\d{3}966\d{6}[\dXx]\b",
                        "Kazakhstan" : r"\b\d{3}601\d{6}[\dXx]\b",
                        "Armenia" : r"\b\d{3}9939\d{5}[\dXx]\b",
                        "Germany" : r"\b\d{3}3\d{8}[\dXx]\b"
    }
    
    isbn_10_patterns = {"Russia" : r"\b5\d{8}[\dXx]\b",
                        "Belarus" : r"\b985\d{6}[\dXx]\b",
                        "Ukraine" : r"\b966\d{6}[\dXx]\b",
                        "Kazakhstan" : r"\b601\d{6}[\dXx]\b",
                        "Armenia" : r"\b9939\d{5}[\dXx]\b",
                        "Germany" : r"\b3\d{8}[\dXx]\b"
    }
    if len(isbn) == 13:
        for country, isbn_pattern in isbn_13_patterns.items():
            if re.fullmatch(isbn_pattern, isbn):
                if str(line['isbn']).count("-") == 4:
                    return str(line['isbn']).split("-")[2]
                if str(line['isbn']).count("-") == 0:
                    publisher_id = str(line['isbn'])[2:11]
                    publisher_id = publisher_id.replace(country_codes[country], "", 1)
                    return publisher_id
            
                
    elif len(isbn) == 10:       
        for country, isbn_pattern in isbn_10_patterns.items():
            if re.fullmatch(isbn_pattern, isbn):
                if str(line['isbn']).count("-") == 3:
                    return str(line['isbn']).split("-")[1]
                if str(line['isbn']).count("-") == 0:
                    publisher_id = str(line['isbn'])[:11]
                    publisher_id = publisher_id.replace(country_codes[country], "", 1)
                    return publisher_id

    else:
        isbn = "000"+str(isbn)
        return isbn


#writing publisher id for indexing
#for sheet in import_sheets:
#    df[sheet]['publisher_id'] = df[sheet].apply(define_publisher_id, axis=1)

'''