import sys
import os
import logging
from orchestrator import PipelineOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("--- Starting Manual Orchestration Pipeline ---")
    
    orchestrator = PipelineOrchestrator()
    filepath = "/app/data/raw/Starbucks_Infor_POS_Foundation_Attacked.xlsx"
    orchestrator.run_pipeline(filepath)
    
    logging.info("--- Orchestration Pipeline Complete ---")

if __name__ == "__main__":
    main()
