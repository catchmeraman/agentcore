# AgentCore Gateway + Official AWS MCP Integration

This guide shows how to integrate official AWS MCP servers with AgentCore Gateway for secure, scalable tool access.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AgentCore AI   │←→  │ AgentCore       │←→  │ Official AWS    │
│                 │    │ Gateway         │    │ MCP Servers     │
│                 │    │ (Secure Proxy)  │    │ (AWS Labs)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   AWS APIs      │
                                              │ • Cost Explorer │
                                              │ • EC2 API       │
                                              │ • S3 API        │
                                              └─────────────────┘
```

## 🔧 Step 1: Setup Official AWS MCP Servers as Gateway Targets

### 1.1 Create Gateway with Official MCP Targets

```python
"""
setup_gateway_with_official_mcp.py
Setup AgentCore Gateway with official AWS MCP servers as targets
"""
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import uuid
import subprocess
import os

def clone_official_aws_mcp():
    """Clone official AWS MCP repository"""
    if not os.path.exists('aws-mcp'):
        print("📥 Cloning official AWS MCP repository...")
        subprocess.run(['git', 'clone', 'https://github.com/awslabs/mcp.git', 'aws-mcp'], check=True)
    return 'aws-mcp'

def discover_mcp_servers(aws_mcp_path):
    """Discover available official MCP servers"""
    servers = []
    if os.path.exists(aws_mcp_path):
        for item in os.listdir(aws_mcp_path):
            server_path = os.path.join(aws_mcp_path, item)
            if os.path.isdir(server_path) and not item.startswith('.'):
                # Check if it's a valid MCP server
                if (os.path.exists(os.path.join(server_path, 'main.py')) or 
                    os.path.exists(os.path.join(server_path, 'server.py')) or
                    os.path.exists(os.path.join(server_path, 'index.js'))):
                    servers.append({
                        'name': item,
                        'path': server_path,
                        'type': 'python' if os.path.exists(os.path.join(server_path, 'main.py')) else 'node'
                    })
    return servers

def create_mcp_target_schema(server_info):
    """Create target schema for MCP server by introspecting it"""
    server_path = server_info['path']
    server_name = server_info['name']
    
    # Start the MCP server temporarily to get its schema
    try:
        if server_info['type'] == 'python':
            cmd = ['python', os.path.join(server_path, 'main.py'), '--list-tools']
        else:
            cmd = ['node', os.path.join(server_path, 'index.js'), '--list-tools']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse the tools from output
            tools_data = json.loads(result.stdout)
            return {
                "externalPayload": {
                    "serverType": "mcp",
                    "serverPath": server_path,
                    "serverCommand": cmd[:-1],  # Remove --list-tools
                    "tools": tools_data
                }
            }
    except Exception as e:
        print(f"⚠️ Could not introspect {server_name}: {e}")
    
    # Fallback: Create generic schema
    return {
        "externalPayload": {
            "serverType": "mcp",
            "serverPath": server_path,
            "serverCommand": ['python', os.path.join(server_path, 'main.py')] if server_info['type'] == 'python' else ['node', os.path.join(server_path, 'index.js')]
        }
    }

def setup_gateway_with_official_mcp():
    """Main setup function"""
    gateway_name = f"Official_AWS_MCP_Gateway_{uuid.uuid4().hex[:8]}"
    
    # Initialize Gateway client
    client = GatewayClient(region_name="us-west-2")
    
    print("📥 Setting up official AWS MCP servers...")
    aws_mcp_path = clone_official_aws_mcp()
    servers = discover_mcp_servers(aws_mcp_path)
    
    print(f"🔍 Found {len(servers)} official MCP servers: {[s['name'] for s in servers]}")
    
    # Create OAuth authorizer
    print("🔐 Creating OAuth authorization...")
    cognito_response = client.create_oauth_authorizer_with_cognito(gateway_name)
    
    # Create Gateway
    print("🚪 Creating AgentCore Gateway...")
    gateway = client.create_mcp_gateway(
        name=gateway_name,
        role_arn=None,  # Auto-creates IAM role
        authorizer_config=cognito_response["authorizer_config"],
        enable_semantic_search=True,
    )
    
    # Fix IAM permissions
    print("🔧 Configuring IAM permissions...")
    client.fix_iam_permissions(gateway)
    
    # Wait for IAM propagation
    import time
    print("⏳ Waiting for IAM propagation...")
    time.sleep(30)
    
    # Add each official MCP server as a target
    targets = {}
    for server_info in servers:
        print(f"🎯 Adding {server_info['name']} as gateway target...")
        
        try:
            target_schema = create_mcp_target_schema(server_info)
            
            target = client.create_mcp_gateway_target(
                gateway=gateway,
                name=f"Official_{server_info['name'].replace('-', '_')}",
                target_type="external_mcp",  # New target type for external MCP servers
                target_payload=target_schema
            )
            
            targets[server_info['name']] = target
            print(f"✅ Added {server_info['name']} target")
            
        except Exception as e:
            print(f"❌ Failed to add {server_info['name']}: {e}")
    
    # Get access token
    print("🔑 Getting access token...")
    access_token = client.get_access_token_for_cognito(cognito_response["client_info"])
    
    # Save configuration
    config = {
        "gateway_url": gateway["gatewayUrl"],
        "gateway_id": gateway["gatewayId"],
        "access_token": access_token,
        "official_mcp_targets": targets,
        "servers": {server['name']: server for server in servers}
    }
    
    with open("official_mcp_gateway_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Official AWS MCP Gateway setup complete!")
    print(f"🌐 Gateway URL: {gateway['gatewayUrl']}")
    print(f"📄 Configuration saved to: official_mcp_gateway_config.json")
    
    return config

if __name__ == "__main__":
    setup_gateway_with_official_mcp()
```

### 1.2 Enhanced Gateway Client for MCP Integration

```python
"""
enhanced_gateway_client.py
Enhanced Gateway client that can manage external MCP servers
"""
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import subprocess
import asyncio
import json
import os

class MCPGatewayClient(GatewayClient):
    """Enhanced Gateway client with MCP server management"""
    
    def __init__(self, region_name="us-west-2"):
        super().__init__(region_name=region_name)
        self.mcp_processes = {}
    
    def create_mcp_gateway_target(self, gateway, name, target_type, target_payload):
        """Create gateway target for external MCP server"""
        
        if target_type == "external_mcp":
            # Start the MCP server process
            server_process = self._start_mcp_server(target_payload["externalPayload"])
            self.mcp_processes[name] = server_process
            
            # Convert to Lambda target with MCP proxy
            lambda_payload = self._create_mcp_proxy_lambda(target_payload)
            target_type = "lambda"
            target_payload = lambda_payload
        
        # Call parent method
        return super().create_mcp_gateway_target(gateway, name, target_type, target_payload)
    
    def _start_mcp_server(self, server_config):
        """Start an external MCP server process"""
        server_path = server_config["serverPath"]
        server_command = server_config["serverCommand"]
        
        print(f"🚀 Starting MCP server: {' '.join(server_command)}")
        
        try:
            process = subprocess.Popen(
                server_command,
                cwd=os.path.dirname(server_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it time to start
            import time
            time.sleep(2)
            
            if process.poll() is None:
                print(f"✅ MCP server started (PID: {process.pid})")
                return process
            else:
                print(f"❌ MCP server failed to start")
                return None
                
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            return None
    
    def _create_mcp_proxy_lambda(self, mcp_config):
        """Create Lambda function that proxies to MCP server"""
        
        # This would create a Lambda function that:
        # 1. Receives tool calls from Gateway
        # 2. Forwards them to the MCP server via stdio
        # 3. Returns the results back to Gateway
        
        lambda_code = f'''
import json
import subprocess
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def call_mcp_tool(tool_name, arguments):
    """Call tool on MCP server"""
    cmd = {mcp_config["externalPayload"]["serverCommand"]}
    
    async with stdio_client(cmd) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "No result"

def lambda_handler(event, context):
    """Lambda handler for MCP proxy"""
    tool_name = event.get("tool_name")
    arguments = event.get("arguments", {{}})
    
    try:
        result = asyncio.run(call_mcp_tool(tool_name, arguments))
        return {{
            "statusCode": 200,
            "body": json.dumps({{"result": result}})
        }}
    except Exception as e:
        return {{
            "statusCode": 500,
            "body": json.dumps({{"error": str(e)}})
        }}
'''
        
        return {
            "toolSchema": {
                "inlinePayload": [
                    {
                        "name": "mcp_proxy",
                        "description": "Proxy to external MCP server",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "tool_name": {"type": "string"},
                                "arguments": {"type": "object"}
                            },
                            "required": ["tool_name"]
                        }
                    }
                ]
            },
            "lambdaCode": lambda_code
        }
    
    def cleanup_mcp_servers(self):
        """Clean up running MCP server processes"""
        for name, process in self.mcp_processes.items():
            if process and process.poll() is None:
                print(f"🛑 Stopping MCP server: {name}")
                process.terminate()
                process.wait()
```

## 🤖 Step 2: AgentCore Agent Integration

### 2.1 Agent with Gateway + Official MCP Integration

```python
"""
agent_with_gateway_official_mcp.py
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

async def call_gateway_tool(tool_name: str, arguments: dict):
    """Call a tool via AgentCore Gateway"""
    
    with open('official_mcp_gateway_config.json', 'r') as f:
        config = json.load(f)
    
    gateway_url = config["gateway_url"]
    access_token = config["access_token"]
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with streamablehttp_client(gateway_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text if result.content else "No result"
                
    except Exception as e:
        return f"Gateway tool call error: {str(e)}"

# Create agent
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="""You're an AWS expert assistant with access to official AWS MCP tools via AgentCore Gateway:

🌐 GATEWAY-CONNECTED TOOLS:
- Official AWS MCP servers from AWS Labs
- Secure, scalable access via AgentCore Gateway
- JWT-authenticated tool access
- Comprehensive AWS service coverage

Available through Gateway:
- AWS CLI operations
- CloudFormation management
- EC2 instance operations
- S3 bucket management
- Lambda function operations
- Cost analysis and optimization
- And more official AWS tools

Use these tools to help users with comprehensive AWS operations.""",
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
            agent.tools = gateway_tools
            print(f"🚀 Loaded {len(gateway_tools)} tools from Gateway")
        else:
            print("⚠️ No Gateway tools loaded")
    except Exception as e:
        print(f"❌ Error connecting to Gateway: {e}")
    
    response = agent(payload.get("prompt", "Hello! I'm your AWS expert with Gateway-connected tools."))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
```

### 2.2 Tool Execution Handler

```python
"""
gateway_tool_handler.py
Handles tool execution through AgentCore Gateway
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

class GatewayToolHandler:
    """Handles tool execution via AgentCore Gateway"""
    
    def __init__(self, gateway_config_path="official_mcp_gateway_config.json"):
        self.config_path = gateway_config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """Load Gateway configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load Gateway config: {e}")
            return {}
    
    async def list_available_tools(self):
        """List all tools available through Gateway"""
        if not self.config:
            return []
        
        gateway_url = self.config["gateway_url"]
        access_token = self.config["access_token"]
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with streamablehttp_client(gateway_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    
                    # Organize tools by MCP server
                    organized_tools = {}
                    for tool in tools_result.tools:
                        if 'Official_' in tool.name:
                            server_name = tool.name.split('_')[1]
                            if server_name not in organized_tools:
                                organized_tools[server_name] = []
                            organized_tools[server_name].append({
                                'name': tool.name,
                                'description': tool.description,
                                'schema': tool.inputSchema
                            })
                    
                    return organized_tools
                    
        except Exception as e:
            print(f"❌ Error listing Gateway tools: {e}")
            return {}
    
    async def execute_tool(self, tool_name: str, arguments: dict):
        """Execute a specific tool through Gateway"""
        if not self.config:
            return "Gateway not configured"
        
        gateway_url = self.config["gateway_url"]
        access_token = self.config["access_token"]
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with streamablehttp_client(gateway_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    print(f"🔧 Executing tool: {tool_name} with args: {arguments}")
                    
                    result = await session.call_tool(tool_name, arguments)
                    
                    if result.content:
                        return result.content[0].text
                    else:
                        return "Tool executed successfully but returned no content"
                        
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def get_server_info(self):
        """Get information about connected MCP servers"""
        if not self.config:
            return {}
        
        return {
            "gateway_url": self.config["gateway_url"],
            "servers": list(self.config.get("servers", {}).keys()),
            "targets": list(self.config.get("official_mcp_targets", {}).keys())
        }

# Usage example
async def demo_gateway_tools():
    """Demonstrate Gateway tool usage"""
    handler = GatewayToolHandler()
    
    # List available tools
    print("📋 Available tools through Gateway:")
    tools = await handler.list_available_tools()
    for server, server_tools in tools.items():
        print(f"\n🔧 {server} MCP Server:")
        for tool in server_tools:
            print(f"  - {tool['name']}: {tool['description']}")
    
    # Execute a tool (example)
    if 'aws_s3' in tools:
        print("\n🪣 Testing S3 tool...")
        result = await handler.execute_tool(
            "Official_aws_s3_list_buckets", 
            {}
        )
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(demo_gateway_tools())
```

## 🚀 Step 3: Complete Deployment Script

```python
"""
deploy_gateway_official_mcp.py
Complete deployment script for Gateway + Official MCP integration
"""
import subprocess
import os
import json

def deploy_gateway_official_mcp():
    """Deploy complete Gateway + Official MCP integration"""
    
    print("🚀 Deploying AgentCore Gateway + Official AWS MCP Integration")
    
    # Step 1: Install dependencies
    print("📦 Installing dependencies...")
    subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
    subprocess.run(['pip', 'install', 'bedrock-agentcore-starter-toolkit'], check=True)
    
    # Step 2: Setup AgentCore Memory
    print("🧠 Setting up AgentCore Memory...")
    result = subprocess.run(['python', 'setup_memory.py'], capture_output=True, text=True)
    memory_id = None
    for line in result.stdout.split('\n'):
        if 'export MEMORY_ID=' in line:
            memory_id = line.split('=')[1]
            break
    
    if memory_id:
        os.environ['MEMORY_ID'] = memory_id
        print(f"Memory ID: {memory_id}")
    
    # Step 3: Setup Gateway with Official MCP
    print("🌐 Setting up Gateway with Official AWS MCP servers...")
    subprocess.run(['python', 'setup_gateway_with_official_mcp.py'], check=True)
    
    # Step 4: Deploy AgentCore Agent
    print("🤖 Deploying AgentCore agent...")
    subprocess.run(['agentcore', 'configure', '-e', 'agent_with_gateway_official_mcp.py'], check=True)
    
    result = subprocess.run(['agentcore', 'launch'], capture_output=True, text=True)
    agent_arn = None
    for line in result.stdout.split('\n'):
        if 'Agent ARN' in line:
            agent_arn = line.split(':')[1:].join(':').strip()
            break
    
    print(f"Agent ARN: {agent_arn}")
    
    # Step 5: Test the integration
    print("🧪 Testing Gateway + MCP integration...")
    test_result = subprocess.run([
        'agentcore', 'invoke', 
        '{"prompt": "List available AWS MCP tools through Gateway"}'
    ], capture_output=True, text=True)
    
    print("Test result:", test_result.stdout)
    
    print("✅ Deployment complete!")
    print("\n📋 Summary:")
    print(f"🧠 Memory ID: {memory_id}")
    print(f"🤖 Agent ARN: {agent_arn}")
    print("🌐 Gateway: Configured with official AWS MCP servers")
    print("\n🧪 Test commands:")
    print('agentcore invoke \'{"prompt": "What AWS tools are available?"}\'')
    print('agentcore invoke \'{"prompt": "List my S3 buckets"}\'')

if __name__ == "__main__":
    deploy_gateway_official_mcp()
```

## 🔧 Key Integration Points

### 1. **Gateway Target Creation**
```python
# Official MCP servers become Gateway targets
target = client.create_mcp_gateway_target(
    gateway=gateway,
    name=f"Official_{server_name}",
    target_type="external_mcp",
    target_payload={
        "externalPayload": {
            "serverType": "mcp",
            "serverPath": server_path,
            "serverCommand": server_command
        }
    }
)
```

### 2. **Tool Discovery via Gateway**
```python
# Agent discovers tools through Gateway
async with streamablehttp_client(gateway_url, headers=headers) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools_result = await session.list_tools()  # Gets all MCP tools
```

### 3. **Secure Tool Execution**
```python
# All tool calls go through Gateway with JWT auth
result = await session.call_tool(tool_name, arguments)
# Gateway forwards to appropriate MCP server
# MCP server calls AWS API
# Result flows back through Gateway to Agent
```

## 🎯 Benefits of This Architecture

1. **Security**: JWT authentication, IAM roles, secure Gateway proxy
2. **Scalability**: Gateway handles multiple MCP servers, auto-scaling
3. **Maintainability**: Official AWS MCP servers, centralized management
4. **Observability**: Gateway provides logging, monitoring, tracing
5. **Flexibility**: Easy to add/remove MCP servers without changing agent code

This integration gives you the best of both worlds: the security and scalability of AgentCore Gateway with the comprehensive AWS coverage of official MCP servers! 🚀
