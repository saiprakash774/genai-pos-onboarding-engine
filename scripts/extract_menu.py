import pandas as pd
import json
import os
import sys
from langsmith.run_helpers import traceable

@traceable(name="map_modifiers")
def map_modifiers(category):
    allowed_modifiers = []
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ontology_path = os.path.join(base_dir, 'graph', 'pos_ontology.json')
    
    if os.path.exists(ontology_path):
        with open(ontology_path, 'r') as f:
            try:
                ontology = json.load(f)
                for edge in ontology.get('edges', []):
                    if edge.get('relation') == 'Applies_To' and edge.get('target') == f"Category:{category}":
                        modifier_name = edge.get('source').replace('Modifier:', '')
                        allowed_modifiers.append(modifier_name)
            except json.JSONDecodeError:
                pass
    return allowed_modifiers

@traceable(name="extract_menu_execution")
def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Always try to read from the attacked file if it exists (for the Red Team scenario)
    input_file = os.path.join(base_dir, 'data', 'raw', 'Starbucks_Infor_POS_Foundation_Attacked.xlsx')
    if not os.path.exists(input_file):
        input_file = os.path.join(base_dir, 'data', 'raw', 'Starbucks_Infor_POS_Foundation.xlsx')
        
    output_file = os.path.join(base_dir, 'data', 'output', 'menu_parsed.json')

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    try:
        df = pd.read_excel(input_file, sheet_name="Menu_Products")
    except Exception as e:
        print(f"Error reading excel: {e}")
        sys.exit(1)

    df.dropna(how='all', inplace=True)
    
    expected_cols = ["Base_Drink", "Size", "Category"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
            
    price_col = "Base_Price ($)" if "Base_Price ($)" in df.columns else "Base_Price"
    if price_col not in df.columns:
        df[price_col] = 0.0

    df['Base_Drink'] = df['Base_Drink'].ffill()
    df['Category'] = df['Category'].ffill()

    parsed_menu = []
    
    for index, row in df.iterrows():
        base_drink = str(row['Base_Drink']) if pd.notnull(row['Base_Drink']) and str(row['Base_Drink']).strip() not in ['nan', 'None', ''] else ""
        category = str(row['Category']) if pd.notnull(row['Category']) and str(row['Category']).strip() not in ['nan', 'None', ''] else ""
        size = str(row['Size']) if pd.notnull(row['Size']) and str(row['Size']).strip() not in ['nan', 'None', ''] else ""
        
        raw_price = row[price_col]
        try:
            base_price = float(raw_price) if pd.notnull(raw_price) else 0.0
        except ValueError:
            base_price = 0.0
        
        # GREEN TEAM PATCH: Sanitize Slop Squatting Attack!
        if base_price < 0 or category == "__proto__":
            print(f"Green Team: Quarantined malicious row {base_drink}")
            continue
            
        # Ignore completely empty structural rows
        if base_drink == "" and category == "" and size == "":
            continue
            
        allowed_modifiers = map_modifiers(category)
            
        menu_item = {
            "Base_Drink": base_drink,
            "Category": category,
            "Size": size,
            "Base_Price": base_price,
            "Allowed_Modifiers": allowed_modifiers
        }
        parsed_menu.append(menu_item)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(parsed_menu, f, indent=4)
        
    print("Parsing Agent execution completed successfully.")

if __name__ == "__main__":
    main()