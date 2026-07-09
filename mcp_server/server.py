import sys
import json
import logging
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Infor POS Validation Server")

@mcp.tool()
def fetch_infor_schema() -> Dict[str, Any]:
    """Returns the target Infor POS schema requirements."""
    return {
        "required_fields": ["Base_Drink", "Category", "Size", "Base_Price"],
        "price_rules": {
            "min_base_price": 0.01,
            "disallow_zero_price": True
        }
    }

@mcp.tool()
def validate_menu_payload(payload_json_str: str) -> Dict[str, Any]:
    """Validates the menu JSON payload against schema rules, explicitly flagging $0.00 base prices."""
    try:
        payload = json.loads(payload_json_str)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON payload format."}
        
    errors = []
    validated_items = []
    
    for idx, item in enumerate(payload):
        # Rule: check for $0.00 base prices
        base_price = item.get("Base_Price")
        if base_price is None or float(base_price) == 0.0:
            errors.append({
                "index": idx,
                "item": item.get("Base_Drink", "Unknown"),
                "error": "Pricing Schema Anomaly: Base_Price cannot be 0.00 or empty."
            })
        else:
            validated_items.append(item)
            
    if errors:
        return {
            "status": "failed",
            "errors": errors,
            "message": f"Validation failed with {len(errors)} Pricing Schema Anomalies."
        }
        
    return {
        "status": "success",
        "validated_payload": validated_items,
        "message": "Payload is strictly valid."
    }

@mcp.tool()
def push_to_infor_ion(payload_json_str: str) -> Dict[str, Any]:
    """Mocks pushing a validated JSON payload to the Infor ION API."""
    try:
        payload = json.loads(payload_json_str)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON payload format."}
        
    return {
        "status": "success",
        "message": f"Successfully pushed {len(payload)} validated items to Infor ION."
    }

if __name__ == "__main__":
    mcp.run()
