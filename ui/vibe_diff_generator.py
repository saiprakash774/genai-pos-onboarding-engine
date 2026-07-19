import os
import json

def generate_vibe_diff():
    """
    Parses OpenTelemetry JSON traces to generate a human-readable Vibe Diff.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    traces_file = os.path.join(base_dir, 'data', 'output', 'traces.json')
    ui_dir = os.path.join(base_dir, 'ui')
    os.makedirs(ui_dir, exist_ok=True)
    
    diff_path = os.path.join(ui_dir, 'vibe_diff.md')

    if not os.path.exists(traces_file):
        with open(diff_path, 'w') as f:
            f.write("# Vibe Diff\n\nNo traces found. The pipeline may not have run yet.")
        print("No traces found.")
        return

    rule_invocations = []
    inheritance_events = []
    anomalies = []

    try:
        with open(traces_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    span = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Check events within the span
                events = span.get("events", [])
                for event in events:
                    name = event.get("name")
                    attrs = event.get("attributes", {})
                    
                    if name == "Rule Invocation":
                        modifier = attrs.get("modifier", "Unknown")
                        category = attrs.get("category", "Unknown")
                        rule = attrs.get("rule", "Unknown")
                        rule_invocations.append(f"- **[MATCH]** Agent linked `{modifier}` to `{category}` because it triggered the `{rule}` rule in the ontology.")
                    elif name == "Inheritance":
                        base_drink = attrs.get("base_drink", "Unknown")
                        size = attrs.get("size", "Unknown")
                        inheritance_events.append(f"- **[INHERITANCE]** Agent carried `{base_drink}` (Size: {size}) via `ffill()` logic.")
                    elif name == "Anomaly Quarantined":
                        base_drink = attrs.get("base_drink", "Unknown")
                        reason = attrs.get("reason", "Unknown")
                        anomalies.append(f"- **[QUARANTINED]** `{base_drink}` flagged for `{reason}`.")
    except Exception as e:
        print(f"Error reading traces: {e}")

    # Build the diff content dynamically
    diff_lines = [
        "# Vibe Diff: Menu Extraction Run",
        "",
        "## Trajectory Analysis",
        "The Parsing Agent successfully executed the spreadsheet extraction. Below is the traced reasoning path:",
        "",
        "### Rule Invocations:",
    ]
    
    # Deduplicate rule invocations to avoid clutter
    unique_rules = list(set(rule_invocations))
    if unique_rules:
        diff_lines.extend(unique_rules)
    else:
        diff_lines.append("- *No modifier rules triggered.*")

    diff_lines.extend(["", "### Implicit Inheritance:"])
    if inheritance_events:
        # Just show a few to avoid clutter if there are many
        if len(inheritance_events) > 5:
            diff_lines.extend(inheritance_events[:5])
            diff_lines.append(f"- *...and {len(inheritance_events) - 5} more inheritance events.*")
        else:
            diff_lines.extend(inheritance_events)
    else:
        diff_lines.append("- *No implicit inheritance logic used.*")

    diff_lines.extend(["", "### Anomaly Report (Green Team):"])
    if anomalies:
        diff_lines.extend(anomalies)
    else:
        diff_lines.append("- *No anomalies detected.*")

    diff_content = "\n".join(diff_lines) + "\n"

    with open(diff_path, 'w') as f:
        f.write(diff_content)
        
    print(f"Generated Vibe Diff at {diff_path}")

if __name__ == "__main__":
    generate_vibe_diff()
