# Multi-Agent Architecture

## Orchestrator Agent (Graph-Router)
Manages the pipeline flow and uses the Knowledge Graph (`graph/pos_ontology.json`) to analyze the systemic impact of rule changes across all related categories.

## Parsing Agent
Specialized in reading Python pandas outputs and mapping complex, floating Excel modifiers to base product codes.

## Security Triad
- **Red Team Agent:** Injects "Slop Squatting" anomalies into `/data/raw` to test the system's defenses.
- **Blue Team (Validation) Agent:** Acts as the enterprise gatekeeper, strictly checking schemas against Infor ION requirements via the local MCP server (`mcp_server/server.py`).
- **Green Team Agent:** Attempts to auto-refactor or quarantine anomalies flagged by the Blue Team.

## Ponytail Plugin (Lazy Senior Developer Mindset)
All agents MUST follow the Ponytail decision ladder before writing any code to prevent over-engineering and bloat:
1. **Does this need to exist at all?** (YAGNI - You Ain't Gonna Need It)
2. **Is it already in the codebase?** (Reuse existing code)
3. **Can the standard library do it?** 
4. **Can a native platform feature do it?** (e.g., HTML5 native features over JS plugins)
5. **Is there an already-installed dependency?**
6. **Can it be one line?**
7. **Only then:** write the minimum code required.
