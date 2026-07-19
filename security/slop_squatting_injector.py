import pandas as pd
import os
import random

def inject_slop_squatting():
    """
    Red Team Agent: Periodically injects 'Slop Squatting' anomalies into the raw data.
    This simulates a malicious vendor trying to hallucinate a non-existent internal package or API.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    
    input_file = os.path.join(raw_dir, 'Starbucks_Infor_POS_Foundation.xlsx')
    
    # If the file doesn't exist, we'll create a dummy one for testing
    if not os.path.exists(input_file):
        df = pd.DataFrame({
            "Base_Drink": ["Caffe Americano", None],
            "Size": ["Tall", "Grande"],
            "Category": ["Hot Coffee", None],
            "Base_Price": [3.25, 3.75]
        })
    else:
        df = pd.read_excel(input_file, sheet_name="Menu_Products")
        
    # Inject a Slop Squatting attack
    anomaly_row = pd.DataFrame([{
        "Base_Drink": "System_Override_Hax",
        "Size": "Venti",
        "Category": "__proto__",
        "Base_Price": -999.00
    }])
    
    df = pd.concat([df, anomaly_row], ignore_index=True)
    
    # Write it back or to a new file
    output_file = os.path.join(raw_dir, 'Starbucks_Infor_POS_Foundation_Attacked.xlsx')
    df.to_excel(output_file, index=False, sheet_name="Menu_Products")
    print(f"Red Team: Slop Squatting injected into {output_file}")

if __name__ == "__main__":
    inject_slop_squatting()
