# Multi-Agent Architecture

## Orchestrator Agent
Manages the pipeline flow and user chat interface.

## Parsing Agent
Specialized in reading Python pandas outputs and mapping complex, floating Excel modifiers to base product codes.

## Validation Agent
Acts as the enterprise gatekeeper, checking the final JSON schema against Infor ION requirements (e.g., flagging $0.00 base prices).
Communication with the Infor ION backend is strictly handled via the local MCP (Model Context Protocol) server located in `mcp_server/server.py`. The Validation Agent relies exclusively on this standardized transport layer instead of fragile, hard-coded API scripts.
