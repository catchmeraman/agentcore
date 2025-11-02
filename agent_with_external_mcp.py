"""
AgentCore agent connecting to external MCP servers via Gateway
"""
import os
import json
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands import Agent
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent

app = BedrockAgentCoreApp()
memory_client = MemoryClient(region_name='us-west-2')
MEMORY_ID = os.getenv('MEMORY_ID')

# Configuration for multiple MCP servers
MCP_SERVERS = {
    "filesystem": {
        "url": "http://localhost:8001/mcp",  # Local MCP server
        "auth": None
    },
    "database": {
        "url": "http://localhost:8002/mcp",  # Another local MCP server
        "auth": None
    },
    "agentcore_gateway": {
        "url": os.getenv('GATEWAY_URL'),     # AgentCore Gateway
        "auth": os.getenv('GATEWAY_TOKEN')
    }
}

class MemoryHook(HookProvider):
    def on_agent_initialized(self, event):
        if not MEMORY_ID: return
        turns = memory_client.get_last_k_turns(
            memory_id=MEMORY_ID,
            actor_id="user",
            session_id=event.agent.state.get("session_id", "default"),
            k=3
        )
        if turns:
            context = "\n".join([f"{m['role']}: {m['content']['text']}" 
                               for t in turns for m in t])
            event.agent.system_prompt += f"\n\nPrevious:\n{context}"

    def on_message_added(self, event):
        if not MEMORY_ID: return
        msg = event.agent.messages[-1]
        memory_client.create_event(
            memory_id=MEMORY_ID,
            actor_id="user",
            session_id=event.agent.state.get("session_id", "default"),
            messages=[(str(msg["content"]), msg["role"])]
        )

    def register_hooks(self, registry):
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)

async def get_mcp_tools_from_servers():
    """Connect to multiple MCP servers and collect all tools"""
    all_tools = []
    
    for server_name, config in MCP_SERVERS.items():
        if not config["url"]:
            continue
            
        try:
            headers = {}
            if config["auth"]:
                headers["Authorization"] = f"Bearer {config['auth']}"
            
            async with streamablehttp_client(config["url"], headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    
                    # Add server prefix to tool names to avoid conflicts
                    for tool in tools_result.tools:
                        tool.name = f"{server_name}_{tool.name}"
                        all_tools.append(tool)
                    
                    print(f"Connected to {server_name}: {len(tools_result.tools)} tools")
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
    
    return all_tools

async def execute_mcp_tool(tool_name: str, arguments: dict):
    """Execute a tool on the appropriate MCP server"""
    # Extract server name from tool name
    server_name = tool_name.split('_')[0]
    original_tool_name = '_'.join(tool_name.split('_')[1:])
    
    config = MCP_SERVERS.get(server_name)
    if not config or not config["url"]:
        return f"Server {server_name} not available"
    
    try:
        headers = {}
        if config["auth"]:
            headers["Authorization"] = f"Bearer {config['auth']}"
        
        async with streamablehttp_client(config["url"], headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(original_tool_name, arguments)
                return result.content[0].text if result.content else "No result"
    except Exception as e:
        return f"Tool execution error: {str(e)}"

# Create agent
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="You're a helpful assistant with access to multiple MCP servers for various capabilities.",
    hooks=[MemoryHook()] if MEMORY_ID else [],
    state={"session_id": "default"}
)

@app.entrypoint
def invoke(payload, context):
    """Main entry point with external MCP server integration"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    # Get tools from all MCP servers
    try:
        external_tools = asyncio.run(get_mcp_tools_from_servers())
        if external_tools:
            agent.tools = external_tools
            print(f"Loaded {len(external_tools)} tools from external MCP servers")
    except Exception as e:
        print(f"Error loading external tools: {e}")
    
    response = agent(payload.get("prompt", "Hello"))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
