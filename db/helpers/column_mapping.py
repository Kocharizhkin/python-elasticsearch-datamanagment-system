import json
import pandas as pd
import numpy as np
import re
from db.helpers.cosine_similarity import Book_similarity

similairity = Book_similarity()

class Mapping():
    
    async def extract_data_preview(self, filename):
        data_info = {}
        df = pd.read_excel(f'db/upload/{filename}', engine='openpyxl', sheet_name=None)
        
        for sheet_name, sheet_df in df.items():
            data_info[sheet_name] = {}
            # Store column names
            data_info[sheet_name]["column_names"] = list(sheet_df.columns)
            
            # Replace all null-like values (NaN, None) with None explicitly
            sheet_df = sheet_df.applymap(lambda x: None if pd.isna(x) else x)
            
            # Store first 3 rows of data
            data_info[sheet_name]["data_preview"] = sheet_df.head(3).to_dict(orient='records')
        
        return data_info

    def sanitize_name(self, name):
        if name[0].isdigit():
            name = 'supplier_' + name
        return re.sub(r'\W+', '_', name)

    def columns_mapping(self, sheet_name, columns):
        # Load the existing fields_map from the file
        with open('db/fields_map.json', 'r') as f:
            fields_map = json.load(f)
        
        sheet_name_sanitized = self.sanitize_name(sheet_name)

        # Check if sheet_name already exists in fields_map
        if sheet_name_sanitized in fields_map:
            existing_columns = fields_map[sheet_name_sanitized]

            mapped_columns_list = list(existing_columns.values())
            filtered_mapped_columns = [value for value in mapped_columns_list if value is not None]

            columns_filtered = [value.replace('\n', '') for value in columns]

            # Check if the existing columns match the provided columns
            if set(columns_filtered).issuperset(set(filtered_mapped_columns)):
                print("is subset")
                return {sheet_name: existing_columns}
            else:
                print(f"Updating fields map for sheet '{sheet_name}'.")
                map_to_send = {}
                lost_and_found = []
                combined_column_names = self.combine_dicts(fields_map.values())
                combined_column_names_copy = combined_column_names
                for column in columns:
                    defined_name = self.define_map_for_unknown_columns(column, combined_column_names)
                    if defined_name == "undefined":
                        lost_and_found.append(column)
                    else:
                        map_to_send[defined_name] = column
                        del combined_column_names[defined_name]
                remaining_columns = set(combined_column_names_copy.keys()) - set(map_to_send.keys())
                for key in remaining_columns:
                    if lost_and_found != []:
                        map_to_send[key] = lost_and_found.pop()
                    else:
                        map_to_send[key] = None
                return {sheet_name: map_to_send}
        else:
            map_to_send = {}
            combined_column_names = self.combine_dicts(fields_map.values())
            for column in columns:
                defined_name = self.define_map_for_unknown_columns(column, combined_column_names)
                map_to_send[defined_name] = column
            return {sheet_name: map_to_send}

    def update_map(self, new_map):
        # Load existing fields map from the file
        with open('db/fields_map.json', 'r') as f:
            fields_map = json.load(f)

        # Iterate through the incoming data
        for publisher, fields in new_map.items():
            publisher = self.sanitize_name(publisher)
            print(f"{publisher}\n\n\n{fields}")
            # Replace None with null in the incoming fields
            fields_map[publisher] = fields

        # Save the updated fields map back to the file
        with open('db/fields_map.json', 'w') as f:
            json.dump(fields_map, f, indent=2)

    def define_map_for_unknown_columns(self, column_name, target_names):
        max_average = 0
        defined_column = ""
        print('for column: ', column_name)
        for db_name, possible_names in target_names.items():
            possible_names = [item for item in possible_names if item != None]
            if possible_names == []:
                continue
            if column_name in possible_names:
                defined_column = db_name
                break
            similarity_scores = similairity.get_cosine_similarity(column_name, possible_names)
            average = sum(similarity_scores) / len(similarity_scores)
            if average > max_average:
                print(possible_names)
                print('new average: ', average, db_name)
                max_average = average
                defined_column = db_name
        if defined_column == "":
            defined_column = "undefined"
        print('defined_name: ', defined_column, "\n\n\n\n")
        return defined_column


    def combine_dicts(self, dicts):
        combined_dict = {}
        for d in dicts:
            for key, value in d.items():
                if key not in combined_dict:
                    combined_dict[key] = [value]
                else:
                    combined_dict[key].append(value)
        print(combined_dict)
        return combined_dict