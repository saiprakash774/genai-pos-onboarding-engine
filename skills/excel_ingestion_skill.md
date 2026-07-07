---
name: excel_ingestion_skill
description: Use this skill to parse, unmerge, and normalize multi-tab .xlsx files into pandas dataframes securely.
---
# Excel Ingestion Skill

## Procedural Instructions

When extracting data from multi-tab Excel spreadsheets, the agent MUST follow these steps:

1. **Environment & Security**: Ensure `pandas` and `openpyxl` are used. Do not execute any VBA macros.
2. **Tab Discovery**: Iterate through all relevant sheets/tabs. Ignore any hidden sheets unless explicitly requested.
3. **Unmerging Cells**: Identify merged cells (which are common in POS spreadsheets for categories) and unmerge them, replicating the merged value to all individual constituent cells.
4. **Header Normalization**: Locate the true header row (it may not be row 1). Strip whitespace, lower-case, and replace spaces with underscores for column names.
5. **Data Extraction**: Load the data into a pandas DataFrame.
6. **Data Cleaning**: 
   - Drop completely empty rows and columns.
   - Forward-fill category or base item columns where implied by the visual hierarchy.
   - Replace or handle NaN values appropriately.
7. **Return Format**: Output a clean, standardized pandas DataFrame ready for further mapping by the Parsing Agent.
