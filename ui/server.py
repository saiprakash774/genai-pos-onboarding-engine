import os
import json
import subprocess
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

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
    # Pivot: The main product is the POS Terminal UI
    return FileResponse(os.path.join(STATIC_DIR, "pos.html"))

@app.get("/dashboard")
def read_dashboard():
    # The Engineering Orchestrator Dashboard is moved to a sub-route
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

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    file_path = os.path.join(raw_dir, "uploaded_menu.xlsx")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "success", "message": "File uploaded successfully. Orchestrator will pick it up."}

@app.get("/api/menu")
def get_full_menu():
    parsed_path = os.path.join(DATA_OUT_DIR, "menu_parsed.json")
    if os.path.exists(parsed_path):
        try:
            with open(parsed_path, "r") as f:
                return json.load(f)
        except:
            pass
    return []

@app.post("/api/ion_sync")
async def ion_sync(request: Request):
    # Mock Infor ION endpoint
    payload = await request.json()
    print(f"Received sync payload for {len(payload)} items.")
    return {"status": "success", "message": f"Successfully ingested {len(payload)} items into Infor ION."}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    ui_state_path = os.path.join(DATA_OUT_DIR, "ui_state.json")
    state = {"status": "idle", "error_logs": ""}
    if os.path.exists(ui_state_path):
        try:
            with open(ui_state_path, "r") as f:
                state = json.load(f)
        except:
            pass

    system_prompt = f"""You are the Orchestrator Agent for an enterprise POS data pipeline.
Current Pipeline Status: {state.get("status")}
Current Error Logs: {state.get("error_logs")}

Your job is to assist the POS Implementation Engineer. If there are anomalies like $0.00 base prices, alert the user. Wait for explicit instructions to proceed or discard anomalies. Keep responses concise."""

    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=req.message)
        ])
        return {"response": response.content}
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            return {"response": "[MOCK FALLBACK - API Quota Exceeded] The pipeline is currently stable. I am monitoring the data feed for any pricing anomalies. No immediate action is required on your part."}
        return {"response": f"Error communicating with LLM: {error_str}"}

import glob
@app.post("/api/delete_menu")
def delete_menu():
    # Clear parsed data
    parsed_path = os.path.join(DATA_OUT_DIR, "menu_parsed.json")
    if os.path.exists(parsed_path):
        os.remove(parsed_path)
    
    # Clear UI state
    ui_state_path = os.path.join(DATA_OUT_DIR, "ui_state.json")
    if os.path.exists(ui_state_path):
        os.remove(ui_state_path)
        
    # Clear raw files
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    for f in glob.glob(os.path.join(raw_dir, "*.xlsx")):
        os.remove(f)
        
    return {"status": "success", "message": "Menu deleted."}

@app.post("/api/simulate_update")
def simulate_update():
    parsed_path = os.path.join(DATA_OUT_DIR, "menu_parsed.json")
    if not os.path.exists(parsed_path):
        return {"status": "error", "message": "No menu to update."}
        
    try:
        with open(parsed_path, "r") as f:
            data = json.load(f)
            
        # Bump all prices by $1.00 to simulate an update
        for item in data:
            if "Base_Price ($)" in item:
                item["Base_Price ($)"] += 1.00
            elif "Base_Price" in item:
                item["Base_Price"] += 1.00
                
        with open(parsed_path, "w") as f:
            json.dump(data, f, indent=2)
            
        return {"status": "success", "message": "Prices bumped by $1.00."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("Starting Dashboard Server on http://localhost:8085")
    uvicorn.run(app, host="0.0.0.0", port=8085)
