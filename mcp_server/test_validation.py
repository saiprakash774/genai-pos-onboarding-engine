import json
import os
import sys

# Import the server functions directly to test logic
from server import validate_menu_payload, fetch_infor_schema

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(base_dir, 'data', 'output', 'menu_parsed.json')
    
    if not os.path.exists(output_file):
        print(f"Error: Could not find {output_file}")
        sys.exit(1)
        
    with open(output_file, 'r') as f:
        payload_str = f.read()
        
    print("Fetching Infor POS schema...")
    schema = fetch_infor_schema()
    print(json.dumps(schema, indent=2))
    
    print("\nValidating menu payload...")
    result = validate_menu_payload(payload_str)
    
    print("\nValidation Result:")
    print(json.dumps(result, indent=2))
    
    if result.get("status") == "failed":
        print(f"\nSuccessfully caught {len(result.get('errors', []))} Pricing Schema Anomalies!")
    else:
        print("\nUnexpected result: All items were valid, but the raw data had empty/0.00 prices.")

if __name__ == "__main__":
    main()
