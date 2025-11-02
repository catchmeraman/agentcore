"""
AgentCore agent with official AWS MCP servers integration
"""
import os
import json
import asyncio
import subprocess
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from strands import Agent
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent

app = BedrockAgentCoreApp()
memory_client = MemoryClient(region_name='us-west-2')
MEMORY_ID = os.getenv('MEMORY_ID')

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

async def connect_to_aws_mcp_server(server_name: str, server_path: str):
    """Connect to official AWS MCP server via stdio"""
    try:
        # Start the MCP server process
        if os.path.exists(f"{server_path}/main.py"):
            cmd = ["python", f"{server_path}/main.py"]
        elif os.path.exists(f"{server_path}/index.js"):
            cmd = ["node", f"{server_path}/index.js"]
        elif os.path.exists(f"{server_path}/server.py"):
            cmd = ["python", f"{server_path}/server.py"]
        else:
            print(f"❌ No executable found for {server_name}")
            return []
        
        async with stdio_client(cmd) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Get available tools
                tools_result = await session.list_tools()
                
                # Prefix tool names with server name
                prefixed_tools = []
                for tool in tools_result.tools:
                    tool.name = f"{server_name}_{tool.name}"
                    prefixed_tools.append(tool)
                
                print(f"✅ Connected to {server_name}: {len(prefixed_tools)} tools")
                return prefixed_tools
                
    except Exception as e:
        print(f"❌ Failed to connect to {server_name}: {e}")
        return []

async def get_all_aws_mcp_tools():
    """Load all official AWS MCP servers and get their tools"""
    all_tools = []
    
    # Load server configuration
    if not os.path.exists('aws_mcp_config.json'):
        print("❌ AWS MCP config not found. Run setup_aws_official_mcp.py first")
        return []
    
    with open('aws_mcp_config.json', 'r') as f:
        server_config = json.load(f)
    
    # Connect to each server
    for server_name, config in server_config.items():
        tools = await connect_to_aws_mcp_server(server_name, config['path'])
        all_tools.extend(tools)
    
    return all_tools

# Create agent
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="""You're an AWS expert assistant with access to official AWS MCP tools:

🔧 OFFICIAL AWS MCP TOOLS:
- AWS service management and operations
- Infrastructure automation and monitoring
- Cost analysis and optimization
- Security and compliance tools

These are the official AWS MCP servers from https://github.com/awslabs/mcp
Use these tools to help users with comprehensive AWS operations.""",
    hooks=[MemoryHook()] if MEMORY_ID else [],
    state={"session_id": "default"}
)

@app.entrypoint
def invoke(payload, context):
    """Main entry point with official AWS MCP integration"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    # Load tools from official AWS MCP servers
    try:
        aws_tools = asyncio.run(get_all_aws_mcp_tools())
        if aws_tools:
            agent.tools = aws_tools
            print(f"🚀 Loaded {len(aws_tools)} official AWS MCP tools")
        else:
            print("⚠️ No official AWS MCP tools loaded")
    except Exception as e:
        print(f"❌ Error loading official AWS MCP tools: {e}")
    
    response = agent(payload.get("prompt", "Hello! I'm your AWS expert assistant with official AWS MCP tools."))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
