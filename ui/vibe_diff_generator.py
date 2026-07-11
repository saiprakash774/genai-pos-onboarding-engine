import os

def generate_vibe_diff():
    """
    Simulates parsing OpenTelemetry traces to generate a human-readable Vibe Diff.
    """
    diff_content = """# Vibe Diff: Menu Extraction Run

## Trajectory Analysis
The Parsing Agent successfully executed the spreadsheet extraction. 

### Rule Invocations:
- **[MATCH]** Agent linked `Cold Foam` to `Cold Coffee` because it triggered the `Applies_To` rule in the ontology.
- **[MATCH]** Agent linked `Whipped Cream` to `Frappuccino` because it triggered the `Applies_To` rule.
- **[INHERITANCE]** Agent carried `Caffe Americano` to `Grande` size via `ffill()` logic.

### Anomaly Report (Blue Team):
- 18 items flagged with `$0.00` base pricing. 
- *Awaiting Green Team Auto-Refactor or Human Sign-off.*
"""
    
    # We output to the local project dir, but the agent will also create an artifact
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ui_dir = os.path.join(base_dir, 'ui')
    os.makedirs(ui_dir, exist_ok=True)
    
    diff_path = os.path.join(ui_dir, 'vibe_diff.md')
    with open(diff_path, 'w') as f:
        f.write(diff_content)
        
    print(f"Generated Vibe Diff at {diff_path}")

if __name__ == "__main__":
    generate_vibe_diff()
