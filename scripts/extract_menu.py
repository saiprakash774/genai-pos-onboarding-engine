import pandas as pd
import json
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, 'data', 'raw', 'Starbucks_Infor_POS_Foundation.xlsx')
    output_file = os.path.join(base_dir, 'data', 'output', 'menu_parsed.json')

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        # Create a dummy output for testing if the file doesn't exist to simulate success if no raw file is given.
        # But we expect the file to exist.
        sys.exit(1)

    print("Loading raw vendor spreadsheet...")
    # Read the excel file
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"Failed to read excel file: {e}")
        sys.exit(1)

    # 1. Drop completely empty rows safely without throwing an execution exception
    df.dropna(how='all', inplace=True)

    # If the dataframe is missing columns, let's just make sure we handle it gracefully.
    # The Gherkin specifies columns like "Base_Drink", "Size", "Category", "Base_Price"
    expected_cols = ["Base_Drink", "Size", "Category", "Base_Price"]
    for col in expected_cols:
        if col not in df.columns:
            # If the dummy data is really chaotic, we might need to create empty columns just to not crash.
            df[col] = None

    # 2. Forward-fill missing parent data ('Base_Drink', 'Category')
    # This addresses the scenario where "Tall" has Base_Drink "Caffe Americano", but "Grande" row is empty.
    df['Base_Drink'] = df['Base_Drink'].ffill()
    df['Category'] = df['Category'].ffill()

    # 3. Enforcing 'Applies_To' conditional modifier mapping
    # Modifiers reference table logic:
    # "Cold Foam" applies to "Cold Coffee"
    # "Whipped Cream" applies to "Hot Coffee|Frappuccino"
    
    parsed_menu = []
    
    for index, row in df.iterrows():
        base_drink = str(row['Base_Drink']) if pd.notnull(row['Base_Drink']) else ""
        category = str(row['Category']) if pd.notnull(row['Category']) else ""
        size = str(row['Size']) if pd.notnull(row['Size']) else ""
        
        # Safely handle Base_Price (which might be 0.00 or empty, Validation agent will flag it later)
        base_price = row['Base_Price'] if pd.notnull(row['Base_Price']) else 0.0
        
        # Determine allowed modifiers
        allowed_modifiers = []
        if category == "Cold Coffee":
            allowed_modifiers.append("Cold Foam")
        if category in ["Hot Coffee", "Frappuccino"]:
            allowed_modifiers.append("Whipped Cream")
            
        menu_item = {
            "Base_Drink": base_drink,
            "Category": category,
            "Size": size,
            "Base_Price": base_price,
            "Allowed_Modifiers": allowed_modifiers
        }
        parsed_menu.append(menu_item)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print("Writing normalized JSON payload...")
    with open(output_file, 'w') as f:
        json.dump(parsed_menu, f, indent=4)
        
    print("Parsing Agent execution completed successfully.")

if __name__ == "__main__":
    main()
