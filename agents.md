# Multi-Agent Architecture

## Orchestrator Agent
Manages the pipeline flow and user chat interface.

## Parsing Agent
Specialized in reading Python pandas outputs and mapping complex, floating Excel modifiers to base product codes.

## Validation Agent
Acts as the enterprise gatekeeper, checking the final JSON schema against Infor ION requirements (e.g., flagging $0.00 base prices).
Communication with the Infor ION backend will eventually be handled via an MCP (Model Context Protocol) server. Do not use fragile, hard-coded API wrappers.
