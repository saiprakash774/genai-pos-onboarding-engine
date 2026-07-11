import os
import time
import subprocess
import logging
import json
from typing import TypedDict, Annotated
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
DATA_OUT_DIR = os.path.join(BASE_DIR, 'data', 'output')
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')

import sys
sys.path.append(BASE_DIR)
from mcp_server.server import validate_menu_payload

# 1. Define State
class PipelineState(TypedDict):
    filepath: str
    error_logs: str
    retry_count: int
    status: str

# 2. Define Nodes
def build_and_run_parsing(state: PipelineState) -> PipelineState:
    logging.info("Node: run_parsing - Building & Running Docker Sandbox...")
    
    # Build to ensure the latest extract_menu.py is baked in
    build_cmd = ["docker", "build", "-t", "parsing-agent", "."]
    b_result = subprocess.run(build_cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if b_result.returncode != 0:
        return {"status": "parsing_failed", "error_logs": b_result.stderr, "retry_count": state.get("retry_count", 0)}

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{DATA_RAW_DIR}:/app/data/raw:ro",
        "-v", f"{DATA_OUT_DIR}:/app/data/output"
    ]
    
    # Pass LangSmith tracing variables into the container if they exist
    for env_var in ["LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"]:
        if os.environ.get(env_var):
            docker_cmd.extend(["-e", f"{env_var}={os.environ[env_var]}"])
            
    docker_cmd.append("parsing-agent")
    
    result = subprocess.run(docker_cmd, cwd=BASE_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Docker execution failed:\n{result.stderr}")
        return {"status": "parsing_failed", "error_logs": result.stderr, "retry_count": state.get("retry_count", 0)}
        
    logging.info("Parsing succeeded.")
    return {"status": "parsed", "error_logs": "", "retry_count": state.get("retry_count", 0)}

def run_bdd_tests(state: PipelineState) -> PipelineState:
    logging.info("Node: run_bdd_tests - Executing BDD Quality Gates...")
    pytest_exe = os.path.join(BASE_DIR, '.venv_sandbox', 'Scripts', 'pytest.exe')
    if not os.path.exists(pytest_exe):
        pytest_exe = "pytest"

    pytest_cmd = [pytest_exe, "tests/test_menu_mapping.py", "-v"]
    result = subprocess.run(pytest_cmd, cwd=BASE_DIR, capture_output=True, text=True)
    
    if result.returncode != 0:
        logging.error("BDD tests failed. Forwarding to self-healing.")
        return {"status": "bdd_failed", "error_logs": result.stdout + "\n" + result.stderr, "retry_count": state.get("retry_count", 0)}
        
    logging.info("BDD tests passed.")
    return {"status": "bdd_passed", "error_logs": "", "retry_count": state.get("retry_count", 0)}

def run_mcp_validation(state: PipelineState) -> PipelineState:
    logging.info("Node: run_mcp_validation - Validating via MCP Blue Team Agent...")
    output_file = os.path.join(DATA_OUT_DIR, 'menu_parsed.json')
    if not os.path.exists(output_file):
         return {"status": "validation_failed", "error_logs": "menu_parsed.json not found.", "retry_count": state.get("retry_count", 0)}
         
    with open(output_file, 'r') as f:
        payload_str = f.read()
        
    result = validate_menu_payload(payload_str)
    
    if result.get("status") != "success":
        error_msg = json.dumps(result, indent=2)
        logging.error(f"MCP Validation failed:\n{error_msg}")
        return {"status": "validation_failed", "error_logs": error_msg, "retry_count": state.get("retry_count", 0)}
        
    logging.info("MCP Validation passed. Pipeline Complete.")
    return {"status": "validated", "error_logs": "", "retry_count": state.get("retry_count", 0)}

def self_heal(state: PipelineState) -> PipelineState:
    retry_count = state.get("retry_count", 0)
    logging.info(f"Node: self_heal - Green Team Agent activated (Retry {retry_count + 1}/3)")
    
    if retry_count >= 3:
        logging.error("Max retries reached. Halting pipeline.")
        return {"status": "failed_max_retries", "error_logs": state["error_logs"], "retry_count": retry_count}
        
    logging.info("Green Team Agent analyzing trace logs via Gemini...")
    extract_script_path = os.path.join(SCRIPTS_DIR, 'extract_menu.py')
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
        
        with open(extract_script_path, 'r') as f:
            current_code = f.read()
            
        system_msg = SystemMessage(content="You are an expert Python data engineer fixing a menu extraction script.")
        human_msg = HumanMessage(content=f"The following python script is extracting data from an Excel file but failing BDD or schema validation tests:\n\n```python\n{current_code}\n```\n\nThe pipeline error logs are:\n{state['error_logs']}\n\nPlease rewrite the entire Python script to fix this bug. You must output ONLY valid Python code inside a ```python block. Do not include any explanations.")
        
        response = llm.invoke([system_msg, human_msg])
        content = response.content
        
        if "```python" in content:
            new_code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            new_code = content.split("```")[1].split("```")[0].strip()
        else:
            new_code = content.strip()
            
        with open(extract_script_path, 'w') as f:
            f.write(new_code)
            
        logging.info("Live AI Patch applied to extract_menu.py. Routing back to parsing.")
        return {"status": "healed", "error_logs": "", "retry_count": retry_count + 1}
        
    except Exception as e:
        logging.error(f"Failed to use Live LLM for self-healing: {e}")
        # Force a failure state to avoid infinite loops if the LLM crashes repeatedly
        return {"status": "failed_max_retries", "error_logs": f"LLM Connection Error: {str(e)}", "retry_count": 3}

def sync_to_ion(state: PipelineState) -> PipelineState:
    logging.info("Node: sync_to_ion - Deploying payload to mock Infor ION endpoint...")
    output_file = os.path.join(DATA_OUT_DIR, 'menu_parsed.json')
    if not os.path.exists(output_file):
         return {"status": "sync_failed", "error_logs": "menu_parsed.json not found.", "retry_count": state.get("retry_count", 0)}
         
    with open(output_file, 'r') as f:
        payload = json.load(f)
        
    import requests
    try:
        response = requests.post("http://localhost:8085/api/ion_sync", json=payload)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Sync to ION failed:\n{e}")
        return {"status": "sync_failed", "error_logs": str(e), "retry_count": state.get("retry_count", 0)}
        
    logging.info("Successfully synced to Infor ION. Pipeline Complete.")
    return {"status": "synced", "error_logs": "", "retry_count": state.get("retry_count", 0)}

# 3. Build Graph
workflow = StateGraph(PipelineState)

workflow.add_node("run_parsing", build_and_run_parsing)
workflow.add_node("run_bdd_tests", run_bdd_tests)
workflow.add_node("run_mcp_validation", run_mcp_validation)
workflow.add_node("self_heal", self_heal)
workflow.add_node("sync_to_ion", sync_to_ion)

workflow.set_entry_point("run_parsing")

def route_parsing(state: PipelineState):
    if state["status"] == "parsed":
        return "run_bdd_tests"
    return "self_heal"

def route_bdd(state: PipelineState):
    if state["status"] == "bdd_passed":
        return "run_mcp_validation"
    return "self_heal"

def route_validation(state: PipelineState):
    if state["status"] == "validated":
        return "sync_to_ion"
    return "self_heal"

def route_heal(state: PipelineState):
    if state["status"] == "healed":
        return "run_parsing"
    return END

workflow.add_conditional_edges("run_parsing", route_parsing)
workflow.add_conditional_edges("run_bdd_tests", route_bdd)
workflow.add_conditional_edges("run_mcp_validation", route_validation)
workflow.add_conditional_edges("self_heal", route_heal)
workflow.add_edge("sync_to_ion", END)

app = workflow.compile()

class PipelineOrchestrator(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            logging.info(f"New file detected: {event.src_path}")
            self.run_pipeline(event.src_path)
            
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            logging.info(f"Modified file detected: {event.src_path}")
            time.sleep(1)
            self.run_pipeline(event.src_path)

    def run_pipeline(self, filepath):
        logging.info("--- Starting Cyclical Orchestration Pipeline ---")
        initial_state = {"filepath": filepath, "error_logs": "", "retry_count": 0, "status": "init"}
        
        ui_state_path = os.path.join(DATA_OUT_DIR, "ui_state.json")
        def update_ui(state_status, error_logs=""):
            try:
                with open(ui_state_path, "w") as f:
                    json.dump({"status": state_status, "error_logs": error_logs}, f)
            except Exception:
                pass

        update_ui("init")
        for s in app.stream(initial_state):
            node_state = list(s.values())[0]
            current_status = node_state['status']
            logging.info(f"Graph executed step. Current status: {current_status}")
            update_ui(current_status, node_state.get('error_logs', ''))
            
        logging.info("--- Orchestration Pipeline Complete ---")

if __name__ == "__main__":
    logging.info(f"Starting LangGraph Orchestrator daemon. Watching: {DATA_RAW_DIR}")
    
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_OUT_DIR, exist_ok=True)

    event_handler = PipelineOrchestrator()
    observer = Observer()
    observer.schedule(event_handler, DATA_RAW_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
