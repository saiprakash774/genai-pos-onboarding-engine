import pandas as pd
import json
import os

def parse_and_validate(excel_path):
    xl = pd.ExcelFile(excel_path)
    
    # 1. Ingest Menu Products
    df_menu = xl.parse('Menu_Products')
    
    # Drop rows where all elements are NaN
    df_menu.dropna(how='all', inplace=True)
    
    # Forward-fill Base_Drink and Category
    df_menu['Category'] = df_menu['Category'].ffill()
    df_menu['Base_Drink'] = df_menu['Base_Drink'].ffill()
    
    # Flag zero-dollar base prices
    df_menu['Pricing_Anomaly'] = df_menu['Base_Price ($)'].apply(
        lambda x: True if pd.isna(x) or float(x) == 0.00 else False
    )
    
    # 2. Ingest Modifiers mapping
    df_map = xl.parse('Drink_Modifier_Map')
    df_mods = xl.parse('Modifiers')
    
    # Group modifiers by their group
    mods_by_group = df_mods.groupby('Modifier_Group')['Modifier_Name'].apply(list).to_dict()
    
    # Map allowed modifiers to each category/drink
    allowed_modifiers = {}
    category_level_modifiers = {}
    
    for _, row in df_map.iterrows():
        cat = row['Category']
        drink = row['Base_Drink']
        group = row['Modifier_Group']
        
        if pd.isna(drink):
            if cat not in category_level_modifiers:
                category_level_modifiers[cat] = []
            if group in mods_by_group:
                category_level_modifiers[cat].extend(mods_by_group[group])
        else:
            if (cat, drink) not in allowed_modifiers:
                allowed_modifiers[(cat, drink)] = []
            if group in mods_by_group:
                allowed_modifiers[(cat, drink)].extend(mods_by_group[group])
                
    # Apply allowed modifiers to menu items
    def get_modifiers(row):
        cat = row['Category']
        drink = row['Base_Drink']
        mods = list(category_level_modifiers.get(cat, []))
        mods.extend(allowed_modifiers.get((cat, drink), []))
        # Remove duplicates while preserving order
        mods = list(dict.fromkeys(mods))
        
        # BDD Business Rule Overrides
        if cat == 'Cold Coffee' and 'Whipped Cream' in mods:
            mods.remove('Whipped Cream')
            
        return mods
        
    df_menu['Allowed_Modifiers'] = df_menu.apply(get_modifiers, axis=1)
    
    return df_menu

def serialize_to_json(df, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    records = df.where(pd.notnull(df), None).to_dict(orient='records')
    
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)

if __name__ == "__main__":
    excel_path = os.path.join('data', 'raw', 'Starbucks_Infor_POS_Foundation.xlsx')
    output_path = os.path.join('data', 'output', 'infor_pos_payload.json')
    df = parse_and_validate(excel_path)
    serialize_to_json(df, output_path)
    print(f"Data parsed and saved to {output_path}")
