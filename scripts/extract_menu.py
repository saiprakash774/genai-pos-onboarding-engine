import pandas as pd
import json
import os
import sys
from langsmith.run_helpers import traceable

from neo4j import GraphDatabase

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.sdk.resources import Resource

class JsonFileSpanExporter(SpanExporter):
    def __init__(self, filename):
        self.filename = filename

    def export(self, spans):
        try:
            with open(self.filename, 'a') as f:
                for span in spans:
                    span_data = {
                        "name": span.name,
                        "context": {
                            "trace_id": format(span.context.trace_id, "032x"),
                            "span_id": format(span.context.span_id, "016x"),
                        },
                        "attributes": dict(span.attributes) if span.attributes else {},
                        "events": [{"name": event.name, "attributes": dict(event.attributes) if event.attributes else {}} for event in span.events]
                    }
                    f.write(json.dumps(span_data) + '\n')
            return SpanExportResult.SUCCESS
        except Exception:
            return SpanExportResult.FAILURE

    def shutdown(self):
        pass

@traceable(name="map_modifiers")
def map_modifiers(category):
    allowed_modifiers = []
    
    URI = "bolt://neo4j:7687"
    AUTH = ("neo4j", "password")
    
    try:
        with tracer.start_as_current_span("map_modifiers") as span:
            span.set_attribute("category", category)
            with GraphDatabase.driver(URI, auth=AUTH, connection_timeout=2.0) as driver:
                with driver.session() as session:
                    result = session.run(
                        "MATCH (m:Modifier)-[:APPLIES_TO]->(c:Category {name: $category}) "
                        "RETURN m.name AS modifier_name",
                        category=category
                    )
                    for record in result:
                        modifier = record["modifier_name"]
                        allowed_modifiers.append(modifier)
                        span.add_event("Rule Invocation", {"modifier": modifier, "category": category, "rule": "Applies_To"})
    except Exception as e:
        print(f"Neo4j Query Error: {e}")
        
    return allowed_modifiers

@traceable(name="extract_menu_execution")
def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Always try to read from the attacked file if it exists (for the Red Team scenario)
    input_file = os.path.join(base_dir, 'data', 'raw', 'Starbucks_Infor_POS_Foundation_Attacked.xlsx')
    if not os.path.exists(input_file):
        input_file = os.path.join(base_dir, 'data', 'raw', 'Starbucks_Infor_POS_Foundation.xlsx')
        
    output_file = os.path.join(base_dir, 'data', 'output', 'menu_parsed.json')
    traces_file = os.path.join(base_dir, 'data', 'output', 'traces.json')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if os.path.exists(traces_file):
        os.remove(traces_file)

    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({"service.name": "parsing-agent"}))
    )
    span_processor = SimpleSpanProcessor(JsonFileSpanExporter(traces_file))
    trace.get_tracer_provider().add_span_processor(span_processor)
    global tracer
    tracer = trace.get_tracer(__name__)

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

    # Track inheritance logic
    previous_base_drink = None
    previous_category = None
    
    for index, row in df.iterrows():
        base_drink = str(row['Base_Drink']) if pd.notnull(row['Base_Drink']) and str(row['Base_Drink']).strip() not in ['nan', 'None', ''] else None
        category = str(row['Category']) if pd.notnull(row['Category']) and str(row['Category']).strip() not in ['nan', 'None', ''] else None
        
        # Simulated ffill for trace event
        if not base_drink and previous_base_drink:
            base_drink = previous_base_drink
            inherited_drink = True
        else:
            inherited_drink = False
            
        if not category and previous_category:
            category = previous_category
            inherited_category = True
        else:
            inherited_category = False
            
        previous_base_drink = base_drink
        previous_category = category
        
        # update row for further processing
        df.at[index, 'Base_Drink'] = base_drink
        df.at[index, 'Category'] = category
        df.at[index, 'Inherited_Drink'] = inherited_drink
        df.at[index, 'Inherited_Category'] = inherited_category

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
            
        inherited_drink = row.get('Inherited_Drink', False)
        inherited_category = row.get('Inherited_Category', False)
        
        with tracer.start_as_current_span("process_row") as span:
            span.set_attribute("base_drink", base_drink)
            span.set_attribute("size", size)
            span.set_attribute("category", category)

            if inherited_drink or inherited_category:
                span.add_event("Inheritance", {"type": "ffill", "base_drink": base_drink, "size": size})

            # GREEN TEAM PATCH: Sanitize Slop Squatting Attack!
            if base_price < 0 or category == "__proto__":
                print(f"Green Team: Quarantined malicious row {base_drink}")
                span.add_event("Anomaly Quarantined", {"reason": "Slop Squatting Detected", "base_drink": base_drink, "category": category})
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