import os
import json
import subprocess
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Infor POS Orchestrator Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_OUT_DIR = os.path.join(BASE_DIR, 'data', 'output')
STATIC_DIR = os.path.join(BASE_DIR, 'ui', 'static')

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/status")
def get_status():
    ui_state_path = os.path.join(DATA_OUT_DIR, "ui_state.json")
    state = {"status": "idle", "error_logs": ""}
    if os.path.exists(ui_state_path):
        try:
            with open(ui_state_path, "r") as f:
                state = json.load(f)
        except:
            pass
            
    parsed_path = os.path.join(DATA_OUT_DIR, "menu_parsed.json")
    parsed_data = []
    if os.path.exists(parsed_path):
        try:
            with open(parsed_path, "r") as f:
                parsed_data = json.load(f)
        except:
            pass

    return {
        "pipeline": state,
        "parsed_items": len(parsed_data),
        "preview": parsed_data[-3:] if parsed_data else []
    }

@app.post("/api/trigger_attack")
def trigger_attack():
    script_path = os.path.join(BASE_DIR, 'security', 'slop_squatting_injector.py')
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    return {"message": "Attack injected! Orchestrator should pick it up automatically.", "logs": result.stdout}

@app.post("/api/ion_sync")
async def ion_sync(payload: list):
    # Mock Infor ION endpoint
    print(f"Received sync payload for {len(payload)} items.")
    return {"status": "success", "message": f"Successfully ingested {len(payload)} items into Infor ION."}

if __name__ == "__main__":
    print("Starting Dashboard Server on http://localhost:8085")
    uvicorn.run(app, host="0.0.0.0", port=8085)
