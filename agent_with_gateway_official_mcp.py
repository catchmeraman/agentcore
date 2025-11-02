"""
AgentCore agent that uses Gateway to access official AWS MCP servers
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

class MemoryHook(HookProvider):
    """Memory management hook"""
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

async def connect_to_gateway():
    """Connect to AgentCore Gateway and discover official MCP tools"""
    
    # Load gateway configuration
    if not os.path.exists('official_mcp_gateway_config.json'):
        print("❌ Gateway config not found. Run setup_gateway_with_official_mcp.py first")
        return []
    
    with open('official_mcp_gateway_config.json', 'r') as f:
        config = json.load(f)
    
    gateway_url = config["gateway_url"]
    access_token = config["access_token"]
    
    print(f"🔗 Connecting to Gateway: {gateway_url}")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with streamablehttp_client(gateway_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Discover all available tools from Gateway
                tools_result = await session.list_tools()
                
                print(f"🔧 Discovered {len(tools_result.tools)} tools from Gateway")
                
                # Group tools by MCP server
                mcp_tools = {}
                for tool in tools_result.tools:
                    # Tool names are prefixed with target name
                    if 'Official_' in tool.name:
                        server_name = tool.name.split('_')[1]
                        if server_name not in mcp_tools:
                            mcp_tools[server_name] = []
                        mcp_tools[server_name].append(tool)
                
                print(f"📋 Available MCP servers via Gateway: {list(mcp_tools.keys())}")
                
                return tools_result.tools
                
    except Exception as e:
        print(f"❌ Failed to connect to Gateway: {e}")
        return []

class GatewayToolExecutor:
    """Handles tool execution through Gateway"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        """Load Gateway configuration"""
        try:
            with open('official_mcp_gateway_config.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    
    async def execute_tool(self, tool_name: str, arguments: dict):
        """Execute a tool via AgentCore Gateway"""
        if not self.config:
            return "Gateway not configured"
        
        gateway_url = self.config["gateway_url"]
        access_token = self.config["access_token"]
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with streamablehttp_client(gateway_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    print(f"🔧 Executing via Gateway: {tool_name}")
                    
                    # For MCP proxy tools, we need to pass the actual MCP tool name
                    if '_proxy' in tool_name:
                        # Extract the actual MCP tool name from arguments or tool name
                        actual_tool_name = arguments.get('tool_name', tool_name.replace('_proxy', ''))
                        mcp_arguments = arguments.get('arguments', arguments)
                        
                        result = await session.call_tool(tool_name, {
                            'tool_name': actual_tool_name,
                            'arguments': mcp_arguments
                        })
                    else:
                        result = await session.call_tool(tool_name, arguments)
                    
                    if result.content:
                        return result.content[0].text
                    else:
                        return "Tool executed successfully"
                        
        except Exception as e:
            error_msg = f"Gateway tool execution error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

# Create global tool executor
tool_executor = GatewayToolExecutor()

# Create agent
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="""You're an AWS expert assistant with access to official AWS MCP tools via AgentCore Gateway:

🌐 GATEWAY-CONNECTED OFFICIAL AWS MCP TOOLS:
- Official AWS MCP servers from AWS Labs (https://github.com/awslabs/mcp)
- Secure, scalable access via AgentCore Gateway
- JWT-authenticated tool access with Cognito
- Production-ready, AWS-maintained tools

Available through Gateway:
- AWS CLI operations for all services
- CloudFormation stack management
- EC2 instance and VPC operations
- S3 bucket and object management
- Lambda function operations
- RDS database management
- IAM identity and access management
- CloudWatch monitoring and logging
- Cost analysis and optimization
- And more official AWS tools

When users ask about AWS operations, use the appropriate official MCP tools through the Gateway.
The tools are prefixed with 'Official_' followed by the service name.

For MCP proxy tools, you'll need to specify both the tool_name and arguments parameters.""",
    hooks=[MemoryHook()] if MEMORY_ID else [],
    state={"session_id": "default"}
)

@app.entrypoint
def invoke(payload, context):
    """Main entry point with Gateway integration"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    # Connect to Gateway and load tools
    try:
        gateway_tools = asyncio.run(connect_to_gateway())
        if gateway_tools:
            # Create wrapper functions for each tool that use the executor
            wrapped_tools = []
            for tool in gateway_tools:
                def create_wrapper(tool_name):
                    async def wrapper(**kwargs):
                        return await tool_executor.execute_tool(tool_name, kwargs)
                    wrapper.__name__ = tool_name
                    return wrapper
                
                wrapped_tools.append(create_wrapper(tool.name))
            
            agent.tools = wrapped_tools
            print(f"🚀 Loaded {len(wrapped_tools)} Gateway tools")
        else:
            print("⚠️ No Gateway tools loaded")
    except Exception as e:
        print(f"❌ Error connecting to Gateway: {e}")
    
    response = agent(payload.get("prompt", "Hello! I'm your AWS expert with Gateway-connected official MCP tools."))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
