import asyncio
import json
import urllib.request
import urllib.error
import base64
import uuid
from datetime import datetime, timezone
from typing import Any
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from mcp.server.models import InitializationOptions

server = Server("darwin-mcp")

def get_hash(text: str) -> str:
    import hashlib
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def push_to_terminus(action: str, capability: str, tag: str) -> str:
    base_url = "http://localhost:6363"
    db_id = "darwin"
    auth = base64.b64encode(b"admin:root").decode("ascii")
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    
    now = datetime.now(timezone.utc).isoformat()
    energy_cost = 1320.0
    
    documents = []
    
    # 1. Action State Node
    state_id = f"PhaseState/{uuid.uuid4().hex}"
    action_state = {
        "@type": "PhaseState",
        "@id": state_id,
        "timestamp": now,
        "accumulated_energy": energy_cost,
        "current_action": action
    }
    
    documents.append(action_state)
    
    try:
        url = f"{base_url}/api/document/admin/{db_id}?author=darwin_mcp&message=Agent%20Logged%20{tag}"
        req = urllib.request.Request(url, method="POST", headers=headers, data=json.dumps(documents).encode("utf-8"))
        urllib.request.urlopen(req)
        return f"Successfully logged phase change [{tag}] for '{action}' into DARWIN."
    except Exception as e:
        return f"Failed to log to TerminusDB: {e}"

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="log_phase_change",
            description="Log an agent's capability or action into the DARWIN TerminusDB physics engine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "The specific action taken by the agent."},
                    "capability_built": {"type": "string", "description": "The specific technical capability forming."},
                    "ontology_tag": {"type": "string", "enum": ["Kyinna", "Nnyini", "Ahodin", "Ignore"], "description": "The classification of the action."}
                },
                "required": ["action", "capability_built", "ontology_tag"]
            }
        ),
        types.Tool(
            name="read_capability_field",
            description="Read the current topological capability state from TerminusDB.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        arguments = {}
        
    if name == "log_phase_change":
        result = push_to_terminus(
            arguments.get("action", "Unknown Action"),
            arguments.get("capability_built", "Unknown Capability"),
            arguments.get("ontology_tag", "Kyinna")
        )
        return [types.TextContent(type="text", text=result)]
        
    elif name == "read_capability_field":
        # Stub for MVP: In future, query TerminusDB WOQL for the current graph state
        state_msg = "Currently tracking capability fields. Active phase: Nnyini."
        return [types.TextContent(type="text", text=state_msg)]
        
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="darwin-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
