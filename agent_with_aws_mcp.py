"""
AgentCore agent with comprehensive AWS MCP servers integration
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

# AWS MCP Servers Configuration
AWS_MCP_SERVERS = {
    "aws_diagram": {
        "url": "http://localhost:8000/mcp",
        "description": "AWS architecture diagram generation"
    },
    "aws_eks": {
        "url": "http://localhost:8001/mcp", 
        "description": "EKS cluster management and operations"
    },
    "aws_terraform": {
        "url": "http://localhost:8002/mcp",
        "description": "Terraform configuration generation and management"
    },
    "aws_cost": {
        "url": "http://localhost:8003/mcp",
        "description": "AWS cost analysis and optimization"
    },
    "github": {
        "url": "http://localhost:8004/mcp",
        "description": "GitHub repository and operations management"
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

async def connect_to_mcp_server(server_name: str, config: dict):
    """Connect to a single MCP server and get its tools"""
    try:
        async with streamablehttp_client(config["url"]) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                
                # Prefix tool names with server name to avoid conflicts
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
    """Connect to all AWS MCP servers and collect tools"""
    all_tools = []
    
    for server_name, config in AWS_MCP_SERVERS.items():
        tools = await connect_to_mcp_server(server_name, config)
        all_tools.extend(tools)
    
    return all_tools

async def execute_aws_mcp_tool(tool_name: str, arguments: dict):
    """Execute a tool on the appropriate AWS MCP server"""
    # Extract server name from prefixed tool name
    server_name = tool_name.split('_')[0] + '_' + tool_name.split('_')[1]
    original_tool_name = '_'.join(tool_name.split('_')[2:])
    
    config = AWS_MCP_SERVERS.get(server_name)
    if not config:
        return f"Server {server_name} not found"
    
    try:
        async with streamablehttp_client(config["url"]) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(original_tool_name, arguments)
                return result.content[0].text if result.content else "No result"
    except Exception as e:
        return f"Tool execution error: {str(e)}"

# Create agent with enhanced system prompt
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="""You're an AWS expert assistant with access to comprehensive AWS tools:

🏗️ AWS DIAGRAM TOOLS:
- Create architecture diagrams for AWS services
- Generate serverless application diagrams
- Visualize infrastructure components

⚙️ AWS EKS TOOLS:
- List and manage EKS clusters
- Get cluster and node group information
- Generate Kubernetes manifests
- Monitor pods and services

🔧 AWS TERRAFORM TOOLS:
- Generate Terraform configurations for AWS services
- Create infrastructure as code templates
- Validate and plan Terraform deployments

💰 AWS COST TOOLS:
- Analyze monthly and service-based costs
- Get rightsizing and Savings Plans recommendations
- Detect cost anomalies and budget status

🐙 GITHUB TOOLS:
- Manage repositories and view commits
- List issues and pull requests
- Search repositories and get file contents

Use these tools to help users with AWS infrastructure, cost optimization, EKS management, and GitHub operations.""",
    hooks=[MemoryHook()] if MEMORY_ID else [],
    state={"session_id": "default"}
)

@app.entrypoint
def invoke(payload, context):
    """Main entry point with AWS MCP servers integration"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    # Load tools from all AWS MCP servers
    try:
        aws_tools = asyncio.run(get_all_aws_mcp_tools())
        if aws_tools:
            agent.tools = aws_tools
            print(f"🚀 Loaded {len(aws_tools)} AWS MCP tools")
        else:
            print("⚠️ No AWS MCP tools loaded - servers may not be running")
    except Exception as e:
        print(f"❌ Error loading AWS MCP tools: {e}")
    
    response = agent(payload.get("prompt", "Hello! I'm your AWS expert assistant."))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
