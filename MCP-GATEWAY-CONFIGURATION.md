# MCP Gateway Configuration Guide

## Overview

This guide explains how to configure MCP server endpoints when creating an AgentCore Gateway, with examples for GitHub MCP server and AWS Core MCP server integration.

## Configuration Methods

### 1. AWS Console Method (Point-and-Click)

**Step 1: Create AgentCore Gateway**
```
AWS Console → Amazon Bedrock → AgentCore → Gateways → Create Gateway
- Gateway Name: internet-assistant-gateway
- Authentication: OAuth/Cognito
- Auto-scaling: Enabled
```

**Step 2: Register MCP Targets**
```
Gateway Details → MCP Targets → Add Target

GitHub MCP Server:
- Target Name: github-mcp
- Endpoint URL: https://api.gateway.region.amazonaws.com/github-mcp
- Authentication: JWT
- Health Check: /health

AWS Core MCP Server:
- Target Name: aws-core-mcp  
- Endpoint URL: https://api.gateway.region.amazonaws.com/aws-mcp
- Authentication: JWT
- Health Check: /health
```

### 2. AWS CLI/API Method

**Create Gateway with MCP Endpoints:**

```bash
# Create Gateway
aws bedrock-agent-core create-gateway \
  --gateway-name "internet-assistant-gateway" \
  --authentication-config '{
    "type": "OAUTH",
    "cognitoConfig": {
      "userPoolId": "us-east-1_XXXXXXXXX",
      "clientId": "your-client-id"
    }
  }' \
  --auto-scaling-config '{
    "minCapacity": 1,
    "maxCapacity": 10,
    "targetUtilization": 70
  }'

# Register GitHub MCP Target
aws bedrock-agent-core register-mcp-target \
  --gateway-id "gateway-12345" \
  --target-config '{
    "name": "github-mcp",
    "endpoint": "https://api.gateway.us-east-1.amazonaws.com/github-mcp",
    "authentication": {
      "type": "JWT",
      "jwtConfig": {
        "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
        "audience": "your-client-id"
      }
    },
    "healthCheck": {
      "path": "/health",
      "intervalSeconds": 30
    }
  }'

# Register AWS Core MCP Target  
aws bedrock-agent-core register-mcp-target \
  --gateway-id "gateway-12345" \
  --target-config '{
    "name": "aws-core-mcp",
    "endpoint": "https://api.gateway.us-east-1.amazonaws.com/aws-mcp",
    "authentication": {
      "type": "JWT",
      "jwtConfig": {
        "issuer": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
        "audience": "your-client-id"
      }
    },
    "healthCheck": {
      "path": "/health", 
      "intervalSeconds": 30
    }
  }'
```

### 3. Terraform Configuration

```hcl
resource "aws_bedrock_agent_core_gateway" "main" {
  name = "internet-assistant-gateway"
  
  authentication_config {
    type = "OAUTH"
    cognito_config {
      user_pool_id = aws_cognito_user_pool.main.id
      client_id    = aws_cognito_user_pool_client.main.id
    }
  }
  
  auto_scaling_config {
    min_capacity        = 1
    max_capacity        = 10
    target_utilization  = 70
  }
}

resource "aws_bedrock_agent_core_mcp_target" "github" {
  gateway_id = aws_bedrock_agent_core_gateway.main.id
  name       = "github-mcp"
  endpoint   = "https://api.gateway.${var.aws_region}.amazonaws.com/github-mcp"
  
  authentication {
    type = "JWT"
    jwt_config {
      issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
      audience = aws_cognito_user_pool_client.main.id
    }
  }
  
  health_check {
    path             = "/health"
    interval_seconds = 30
  }
}

resource "aws_bedrock_agent_core_mcp_target" "aws_core" {
  gateway_id = aws_bedrock_agent_core_gateway.main.id
  name       = "aws-core-mcp"
  endpoint   = "https://api.gateway.${var.aws_region}.amazonaws.com/aws-mcp"
  
  authentication {
    type = "JWT"
    jwt_config {
      issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.main.id}"
      audience = aws_cognito_user_pool_client.main.id
    }
  }
  
  health_check {
    path             = "/health"
    interval_seconds = 30
  }
}
```

### 4. Lambda Proxy Functions

**GitHub MCP Proxy:**
```python
import json
import boto3

def lambda_handler(event, context):
    # Extract MCP request
    mcp_request = json.loads(event['body'])
    
    # Route to GitHub MCP server
    if mcp_request['method'] == 'tools/list':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'tools': [
                    {'name': 'create_repository'},
                    {'name': 'list_repositories'},
                    {'name': 'create_issue'}
                ]
            })
        }
    
    # Forward to actual GitHub MCP implementation
    return forward_to_github_mcp(mcp_request)
```

**AWS Core MCP Proxy:**
```python
import json
import boto3

def lambda_handler(event, context):
    mcp_request = json.loads(event['body'])
    
    # Route to AWS MCP tools
    if mcp_request['method'] == 'tools/list':
        return {
            'statusCode': 200,
            'body': json.dumps({
                'tools': [
                    {'name': 'call_aws'},
                    {'name': 'suggest_aws_commands'},
                    {'name': 'get_regional_availability'}
                ]
            })
        }
    
    # Forward to AWS MCP implementation
    return forward_to_aws_mcp(mcp_request)
```

### 5. Agent Configuration

```python
from bedrock_agent_core import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Configure MCP endpoints
app.configure_mcp_gateway({
    'gateway_endpoint': 'https://gateway-12345.agentcore.us-east-1.amazonaws.com',
    'targets': [
        {
            'name': 'github-mcp',
            'tools': ['create_repository', 'list_repositories', 'create_issue']
        },
        {
            'name': 'aws-core-mcp', 
            'tools': ['call_aws', 'suggest_aws_commands', 'get_regional_availability']
        }
    ]
})

@app.agent
def internet_assistant(query: str):
    # Agent can now use both GitHub and AWS MCP tools
    if 'github' in query.lower():
        return app.call_mcp_tool('github-mcp', 'list_repositories')
    elif 'aws' in query.lower():
        return app.call_mcp_tool('aws-core-mcp', 'call_aws', {'command': 'aws s3 ls'})
```

## Integration with This Repository

### Repository Structure Mapping:
```
agentcore-app/
├── agents/                    # Agent implementations
├── mcp-servers/              # MCP server code
├── terraform/                # Infrastructure as Code
├── deployment-scripts/       # Automated deployment
└── docs/                     # Documentation
```

### 1. Terraform Integration (`terraform/` directory)
Add MCP target resources to existing Terraform code:
```hcl
# Add to existing terraform configuration
resource "aws_bedrock_agent_core_mcp_target" "github_mcp" {
  gateway_id = aws_bedrock_agent_core_gateway.main.id
  name       = "github-mcp"
  endpoint   = "https://your-gateway.amazonaws.com/github-mcp"
}
```

### 2. MCP Server Updates (`mcp-servers/` directory)
Add Gateway compatibility to existing MCP servers:
```python
# Add to existing mcp-servers/github_mcp.py
@app.route('/health')
def health_check():
    return {'status': 'healthy'}

@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    # Handle Gateway-routed MCP requests
    return process_mcp_request(request.json)
```

### 3. Deployment Script Updates
Update existing deployment scripts to include MCP target registration:
```bash
# Add to deploy_gateway_official_mcp.sh
aws bedrock-agent-core register-mcp-target \
  --gateway-id $GATEWAY_ID \
  --target-config file://github-mcp-config.json
```

### 4. Agent Code Updates (`agents/` directory)
Modify agents to use Gateway endpoints:
```python
# Update existing agents/internet_assistant.py
class InternetAssistant:
    def __init__(self):
        self.gateway_endpoint = "https://gateway-xyz.agentcore.amazonaws.com"
        self.mcp_targets = ["github-mcp", "aws-core-mcp"]
    
    def call_github_tool(self, tool_name, params):
        # Route through Gateway instead of direct MCP call
        return self.gateway_client.call_mcp_tool("github-mcp", tool_name, params)
```

## Key Benefits

1. **Centralized Routing**: Gateway handles all MCP server communication
2. **Enterprise Security**: JWT authentication instead of direct access
3. **Auto-scaling**: Gateway scales MCP servers based on demand
4. **Observability**: Built-in monitoring and tracing
5. **Production Ready**: Enterprise-grade reliability

## Implementation Steps

1. **Update Terraform**: Add MCP target resources
2. **Modify MCP Servers**: Add Gateway compatibility endpoints
3. **Update Deployment Scripts**: Include MCP target registration
4. **Modify Agents**: Use Gateway endpoints instead of direct MCP calls
5. **Add Configuration**: Gateway endpoint configurations

This transforms the current direct MCP integration into an enterprise-grade Gateway-mediated architecture, aligning with the comprehensive AgentCore documentation and deployment methods in this repository.
