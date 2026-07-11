# Multi-Agent Architecture

## Orchestrator Agent (Graph-Router)
Manages the pipeline flow and uses the Knowledge Graph (`graph/pos_ontology.json`) to analyze the systemic impact of rule changes across all related categories.

## Parsing Agent
Specialized in reading Python pandas outputs and mapping complex, floating Excel modifiers to base product codes.

## Security Triad
- **Red Team Agent:** Injects "Slop Squatting" anomalies into `/data/raw` to test the system's defenses.
- **Blue Team (Validation) Agent:** Acts as the enterprise gatekeeper, strictly checking schemas against Infor ION requirements via the local MCP server (`mcp_server/server.py`).
- **Green Team Agent:** Attempts to auto-refactor or quarantine anomalies flagged by the Blue Team.
