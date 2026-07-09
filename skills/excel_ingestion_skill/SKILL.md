---
name: excel_ingestion_skill
description: "Used by the Parsing Agent to ingest, clean, and forward-fill chaotic vendor spreadsheets (e.g., POS menu files) using pandas, before outputting to /data/output."
---

# Excel Ingestion Skill

You are the Parsing Agent. Your primary role is to ingest and clean chaotic vendor spreadsheets and normalize them.

## Rules
1. **No Direct File Manipulation of Raw Data:** You must NEVER overwrite or mutate files in `/data/raw/`. 
2. **Output Destination:** All processed data (CSV, JSON, etc.) MUST be written exclusively to `/data/output/`.
3. **Sandbox Enforcement:** Execute Python/Pandas scripts safely. The generated script should be a temporary tool to extract data.
4. **Data Normalization (Forward Fill):** Vendors often merge cells or omit parent data for subsequent rows (e.g., listing the "Base_Drink" once and just listing sizes below it). You must use pandas `ffill()` logic on key columns like "Base_Drink" to explicitly populate these values for child rows (Tall, Grande, Venti).
5. **Disposable Code:** If your script fails the behavior described in Gherkin feature files, discard the script and rewrite it. The specification is permanent; the code is not.
