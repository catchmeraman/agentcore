"""
Setup AgentCore Gateway with official AWS MCP servers as targets
"""
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import uuid
import subprocess
import os
import time

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

def create_lambda_proxy_for_mcp(server_info):
    """Create Lambda function code that proxies to MCP server"""
    server_name = server_info['name']
    server_path = server_info['path']
    
    lambda_code = f'''
import json
import subprocess
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def call_mcp_tool(tool_name, arguments):
    """Call tool on MCP server via stdio"""
    server_path = "{server_path}"
    
    if os.path.exists(os.path.join(server_path, "main.py")):
        cmd = ["python", os.path.join(server_path, "main.py")]
    elif os.path.exists(os.path.join(server_path, "server.py")):
        cmd = ["python", os.path.join(server_path, "server.py")]
    else:
        cmd = ["node", os.path.join(server_path, "index.js")]
    
    try:
        async with stdio_client(cmd) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text if result.content else "No result"
    except Exception as e:
        return f"MCP call error: {{str(e)}}"

def lambda_handler(event, context):
    """Lambda handler for MCP proxy"""
    try:
        # Extract tool call from Gateway
        tool_name = event.get("tool_name")
        arguments = event.get("arguments", {{}})
        
        # Call MCP server
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
    
    # Create generic tool schema for the MCP server
    tool_schema = {
        "inlinePayload": [
            {
                "name": f"{server_name}_proxy",
                "description": f"Proxy to official {server_name} MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the MCP tool to call"
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Arguments for the MCP tool"
                        }
                    },
                    "required": ["tool_name"]
                }
            }
        ]
    }
    
    return {
        "toolSchema": tool_schema,
        "lambdaCode": lambda_code
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
    
    if not servers:
        print("❌ No MCP servers found in repository")
        return
    
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
    print("⏳ Waiting for IAM propagation...")
    time.sleep(30)
    
    # Add each official MCP server as a Lambda target
    targets = {}
    for server_info in servers:
        print(f"🎯 Adding {server_info['name']} as gateway target...")
        
        try:
            # Create Lambda proxy for this MCP server
            lambda_payload = create_lambda_proxy_for_mcp(server_info)
            
            target = client.create_mcp_gateway_target(
                gateway=gateway,
                name=f"Official_{server_info['name'].replace('-', '_')}",
                target_type="lambda",
                target_payload=lambda_payload
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
    print(f"🎯 Targets created: {len(targets)}")
    
    # Print environment variables for agent
    print("\n📋 Environment variables for your agent:")
    print(f"export GATEWAY_URL={gateway['gatewayUrl']}")
    print(f"export GATEWAY_TOKEN={access_token}")
    
    return config

if __name__ == "__main__":
    setup_gateway_with_official_mcp()
