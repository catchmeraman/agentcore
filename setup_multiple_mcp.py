"""
Setup multiple MCP servers and AgentCore Gateway targets
"""
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import json
import uuid
import time

def setup_filesystem_mcp_target(gateway_client, gateway):
    """Add filesystem MCP server as gateway target"""
    filesystem_schema = {
        "inlinePayload": [
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "list_directory",
                "description": "List contents of a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory_path": {"type": "string", "description": "Path to the directory"}
                    },
                    "required": ["directory_path"]
                }
            }
        ]
    }
    
    return gateway_client.create_mcp_gateway_target(
        gateway=gateway,
        name="FilesystemMCP",
        target_type="lambda",
        target_payload={"toolSchema": filesystem_schema}
    )

def setup_database_mcp_target(gateway_client, gateway):
    """Add database MCP server as gateway target"""
    database_schema = {
        "inlinePayload": [
            {
                "name": "query_database",
                "description": "Execute a database query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to execute"},
                        "database": {"type": "string", "description": "Database name", "default": "main"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }
    
    return gateway_client.create_mcp_gateway_target(
        gateway=gateway,
        name="DatabaseMCP",
        target_type="lambda",
        target_payload={"toolSchema": database_schema}
    )

def setup_web_mcp_target(gateway_client, gateway):
    """Add web scraping MCP server as gateway target"""
    web_schema = {
        "inlinePayload": [
            {
                "name": "scrape_website",
                "description": "Scrape content from a website",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to scrape"},
                        "selector": {"type": "string", "description": "CSS selector (optional)"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "search_google",
                "description": "Search Google for information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        ]
    }
    
    return gateway_client.create_mcp_gateway_target(
        gateway=gateway,
        name="WebScrapingMCP",
        target_type="lambda",
        target_payload={"toolSchema": web_schema}
    )

def main():
    """Setup multiple MCP targets in AgentCore Gateway"""
    gateway_name = f"MultiMCP_Gateway_{uuid.uuid4().hex[:8]}"
    
    # Initialize client
    client = GatewayClient(region_name="us-west-2")
    
    print("🔐 Creating OAuth authorization...")
    cognito_response = client.create_oauth_authorizer_with_cognito(gateway_name)
    
    print("🚪 Creating Gateway...")
    gateway = client.create_mcp_gateway(
        name=gateway_name,
        role_arn=None,
        authorizer_config=cognito_response["authorizer_config"],
        enable_semantic_search=True,
    )
    
    print("🔧 Fixing IAM permissions...")
    client.fix_iam_permissions(gateway)
    time.sleep(30)  # Wait for IAM propagation
    
    print("📁 Adding Filesystem MCP target...")
    filesystem_target = setup_filesystem_mcp_target(client, gateway)
    
    print("🗄️ Adding Database MCP target...")
    database_target = setup_database_mcp_target(client, gateway)
    
    print("🌐 Adding Web Scraping MCP target...")
    web_target = setup_web_mcp_target(client, gateway)
    
    print("🔑 Getting access token...")
    access_token = client.get_access_token_for_cognito(cognito_response["client_info"])
    
    # Save configuration
    config = {
        "gateway_url": gateway["gatewayUrl"],
        "gateway_id": gateway["gatewayId"],
        "access_token": access_token,
        "targets": {
            "filesystem": filesystem_target,
            "database": database_target,
            "web": web_target
        }
    }
    
    with open("multi_mcp_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Multi-MCP Gateway setup complete!")
    print(f"Gateway URL: {gateway['gatewayUrl']}")
    print("Configuration saved to: multi_mcp_config.json")
    
    # Print environment variables for agent
    print("\n📋 Environment variables for your agent:")
    print(f"export GATEWAY_URL={gateway['gatewayUrl']}")
    print(f"export GATEWAY_TOKEN={access_token}")

if __name__ == "__main__":
    main()
