# AgentCore Internet Assistant - Detailed Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Code Explanation](#code-explanation)
4. [Deployment Process](#deployment-process)
5. [Configuration Details](#configuration-details)
6. [Security Considerations](#security-considerations)

## Architecture Overview

The AgentCore Internet Assistant is built using Amazon Bedrock AgentCore services to create an AI agent capable of fetching internet data with persistent memory and a web frontend.

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Web Frontend  │───▶│   API Gateway    │───▶│      Lambda         │
│   (S3 Static)   │    │                  │    │   (API Handler)     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                                           │
                                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock AgentCore                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────┤
│  AgentCore      │  AgentCore      │  AgentCore      │  AgentCore    │
│  Runtime        │  Memory         │  Gateway        │  Identity     │
│                 │                 │                 │               │
│ • Serverless    │ • STM/LTM       │ • MCP Tools     │ • JWT Auth    │
│ • Auto-scaling  │ • Preferences   │ • Tool Discovery│ • Cognito     │
│ • Session Mgmt  │ • Cross-session │ • Secure Access │ • Token Mgmt  │
└─────────────────┴─────────────────┴─────────────────┴───────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │   Internet APIs     │
                        │                     │
                        │ • Web Search        │
                        │ • URL Fetching      │
                        │ • External Data     │
                        └─────────────────────┘
```

## Core Components

### 1. AgentCore Runtime (`agent.py`)

**Purpose**: Main application entry point that orchestrates all AgentCore services.

**Key Features**:
- Serverless execution environment
- Automatic scaling based on demand
- Session management and isolation
- Integration with other AgentCore services

**Code Structure**:
```python
# Core imports for AgentCore services
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.mcp import MCPServer

# Initialize AgentCore components
app = BedrockAgentCoreApp()          # Runtime container
mcp_server = MCPServer()             # MCP tool server
memory_client = MemoryClient()       # Memory service client
```

### 2. AgentCore Memory Integration

**Purpose**: Provides persistent memory across conversations and sessions.

**Memory Types**:
- **Short-Term Memory (STM)**: Stores raw conversation within sessions
- **Long-Term Memory (LTM)**: Extracts and retains user preferences across sessions

**Implementation**:
```python
class MemoryHook(HookProvider):
    def on_agent_initialized(self, event):
        # Load previous conversation context
        turns = memory_client.get_last_k_turns(...)
        
    def on_message_added(self, event):
        # Save new messages to memory
        memory_client.create_event(...)
```

### 3. MCP Tools for Internet Access

**Purpose**: Secure, standardized tools for fetching internet data.

**Available Tools**:
- `fetch_url_data(url)`: Direct URL content retrieval
- `search_web(query)`: Web search using DuckDuckGo API

**Security Features**:
- Request timeout limits
- Response size restrictions
- Error handling and sanitization

### 4. Web Frontend (`frontend/index.html`)

**Purpose**: User interface for interacting with the AgentCore agent.

**Features**:
- Real-time chat interface
- CORS-enabled API calls
- Responsive design
- Error handling

## Code Explanation

### 1. Main Agent Implementation (`agent.py`)

#### Imports and Initialization
```python
import os
import json
import requests
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.mcp import MCPServer
from strands import Agent
```

**Explanation**:
- `BedrockAgentCoreApp`: Main runtime container for the agent
- `MemoryClient`: Interface to AgentCore Memory service
- `MCPServer`: Server for hosting MCP (Model Context Protocol) tools
- `Agent`: Strands framework agent for LLM interactions

#### MCP Tool Definitions
```python
@mcp_server.tool()
def fetch_url_data(url: str) -> str:
    """Fetch data from a URL"""
    try:
        response = requests.get(url, timeout=10)
        return response.text[:1000]  # Limit response size
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"
```

**Explanation**:
- `@mcp_server.tool()`: Decorator registers function as MCP tool
- `timeout=10`: Prevents hanging requests
- `[:1000]`: Limits response size to prevent memory issues
- Exception handling ensures graceful error responses

#### Memory Hook Implementation
```python
class MemoryHook(HookProvider):
    def on_agent_initialized(self, event):
        if not MEMORY_ID: return
        turns = memory_client.get_last_k_turns(
            memory_id=MEMORY_ID,
            actor_id="user",
            session_id=event.agent.state.get("session_id", "default"),
            k=3  # Last 3 conversation turns
        )
```

**Explanation**:
- `HookProvider`: Base class for agent lifecycle hooks
- `on_agent_initialized`: Called when agent starts new session
- `get_last_k_turns`: Retrieves recent conversation history
- `k=3`: Limits context to prevent token overflow

#### Main Entry Point
```python
@app.entrypoint
def invoke(payload, context):
    """Main entry point"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    agent.tools = [fetch_url_data, search_web]
    response = agent(payload.get("prompt", "Hello"))
    return response.message['content'][0]['text']
```

**Explanation**:
- `@app.entrypoint`: Marks function as AgentCore Runtime entry point
- Session ID management for memory isolation
- Dynamic tool assignment to agent
- Response extraction from Strands agent format

### 2. Memory Setup (`setup_memory.py`)

```python
memory = client.create_memory_and_wait(
    name=f"InternetAgent_{uuid.uuid4().hex[:8]}",
    strategies=[
        {"userPreferenceMemoryStrategy": {
            "name": "prefs",
            "namespaces": ["/user/preferences"]
        }},
        {"semanticMemoryStrategy": {
            "name": "facts", 
            "namespaces": ["/user/facts"]
        }}
    ],
    event_expiry_days=30
)
```

**Explanation**:
- `create_memory_and_wait`: Synchronous memory creation
- `userPreferenceMemoryStrategy`: Extracts user preferences automatically
- `semanticMemoryStrategy`: Extracts factual information
- `namespaces`: Organize different types of extracted information
- `event_expiry_days`: Automatic cleanup of old conversations

### 3. Infrastructure as Code (`infrastructure.yaml`)

#### S3 Frontend Hosting
```yaml
FrontendBucket:
  Type: AWS::S3::Bucket
  Properties:
    WebsiteConfiguration:
      IndexDocument: index.html
    PublicAccessBlockConfiguration:
      BlockPublicAcls: false
```

**Explanation**:
- Static website hosting for frontend
- Public access configuration for web serving
- Cost-effective hosting solution

#### API Gateway Integration
```yaml
ApiMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    HttpMethod: POST
    AuthorizationType: NONE
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
```

**Explanation**:
- RESTful API endpoint for frontend communication
- AWS_PROXY integration for Lambda backend
- CORS support for cross-origin requests

#### Lambda API Handler
```yaml
ApiLambda:
  Type: AWS::Lambda::Function
  Properties:
    Runtime: python3.9
    Environment:
      Variables:
        AGENT_ARN: 'REPLACE_WITH_AGENTCORE_ARN'
```

**Explanation**:
- Serverless API handler
- Environment variable for AgentCore agent ARN
- Automatic scaling and pay-per-use pricing

## Deployment Process

### 1. Prerequisites Setup
```bash
# Install AgentCore CLI
pip install bedrock-agentcore-cli

# Configure AWS credentials
aws configure
```

### 2. Memory Initialization
```bash
python setup_memory.py
export MEMORY_ID=<generated-memory-id>
```

**Process**:
1. Creates AgentCore Memory resource
2. Configures extraction strategies
3. Returns memory ID for agent configuration

### 3. Infrastructure Deployment
```bash
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name agentcore-internet-assistant \
  --capabilities CAPABILITY_IAM
```

**Resources Created**:
- S3 bucket for frontend hosting
- API Gateway for REST API
- Lambda function for API handling
- IAM roles with least-privilege permissions

### 4. AgentCore Agent Deployment
```bash
agentcore configure -e agent.py
agentcore launch
```

**Process**:
1. Packages agent code and dependencies
2. Creates container image
3. Deploys to AgentCore Runtime
4. Configures auto-scaling and monitoring

### 5. Frontend Configuration
```bash
# Update frontend with API endpoint
sed -i "s|YOUR_AGENTCORE_ENDPOINT|$API_ENDPOINT|g" frontend/index.html

# Upload to S3
aws s3 cp frontend/index.html s3://$BUCKET_NAME/
```

## Configuration Details

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MEMORY_ID` | AgentCore Memory resource ID | `mem-abc123def456` |
| `AGENT_ARN` | AgentCore Runtime agent ARN | `arn:aws:bedrock-agentcore:...` |
| `AWS_REGION` | AWS region for services | `us-west-2` |

### Memory Strategies Configuration

```python
strategies=[
    {
        "userPreferenceMemoryStrategy": {
            "name": "prefs",
            "namespaces": ["/user/preferences"]
        }
    },
    {
        "semanticMemoryStrategy": {
            "name": "facts", 
            "namespaces": ["/user/facts"]
        }
    }
]
```

**Strategy Types**:
- **User Preference**: Extracts statements like "I prefer Python"
- **Semantic Memory**: Extracts factual information like "My birthday is January 15"

### MCP Tool Configuration

```python
@mcp_server.tool()
def fetch_url_data(url: str) -> str:
    """Fetch data from a URL"""
```

**Configuration Options**:
- Function signature defines tool parameters
- Docstring provides tool description
- Return type annotation for response format
- Automatic schema generation for tool discovery

## Security Considerations

### 1. AgentCore Identity Integration

```python
# JWT token validation (handled by AgentCore)
headers = {"Authorization": f"Bearer {access_token}"}
```

**Security Features**:
- JWT-based authentication
- Cognito User Pool integration
- Token validation and refresh
- Session isolation

### 2. Network Security

```yaml
# IAM role with minimal permissions
Policies:
  - PolicyName: BedrockAgentCoreAccess
    PolicyDocument:
      Statement:
        - Effect: Allow
          Action:
            - bedrock:InvokeAgent
          Resource: '*'
```

**Security Measures**:
- Least-privilege IAM roles
- VPC endpoints for private communication
- HTTPS-only API endpoints
- CORS configuration for frontend security

### 3. Data Protection

```python
# Response size limiting
return response.text[:1000]

# Request timeout
response = requests.get(url, timeout=10)
```

**Protection Mechanisms**:
- Response size limits prevent memory exhaustion
- Request timeouts prevent hanging connections
- Input validation and sanitization
- Error message sanitization

### 4. Memory Data Security

```python
event_expiry_days=30  # Automatic data cleanup
```

**Data Governance**:
- Automatic data expiration
- Encrypted storage (AgentCore managed)
- Access logging and monitoring
- Session-based data isolation

## Performance Optimization

### 1. AgentCore Runtime Scaling

- **Auto-scaling**: Automatic capacity adjustment based on demand
- **Cold start optimization**: Pre-warmed containers for faster response
- **Resource allocation**: Optimized CPU/memory allocation per request

### 2. Memory Performance

- **Context limiting**: `k=3` limits conversation history
- **Namespace organization**: Efficient data retrieval
- **Async processing**: Non-blocking memory operations

### 3. Frontend Optimization

- **Static hosting**: S3 for fast content delivery
- **CDN integration**: CloudFront for global distribution
- **Caching**: Browser caching for static assets

## Monitoring and Observability

### 1. AgentCore Observability

```python
# Built-in monitoring (automatic)
- Request/response logging
- Performance metrics
- Error tracking
- Usage analytics
```

### 2. CloudWatch Integration

```yaml
# Automatic CloudWatch logs
- Lambda function logs
- API Gateway access logs
- AgentCore Runtime metrics
```

### 3. Custom Metrics

```python
# Add custom metrics in Lambda
import boto3
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(...)
```

## Troubleshooting Guide

### Common Issues

1. **Memory ID not found**
   - Verify `MEMORY_ID` environment variable
   - Check memory resource exists in correct region

2. **MCP tools not available**
   - Ensure tools are properly registered with `@mcp_server.tool()`
   - Verify agent has access to tool definitions

3. **Frontend API errors**
   - Check API Gateway endpoint URL
   - Verify CORS configuration
   - Confirm Lambda function permissions

4. **AgentCore deployment failures**
   - Validate agent code syntax
   - Check IAM permissions
   - Verify region availability

### Debug Commands

```bash
# Check AgentCore agent status
agentcore status <agent-name>

# View agent logs
agentcore logs <agent-name>

# Test memory connection
python -c "from bedrock_agentcore.memory import MemoryClient; print(MemoryClient().list_memories())"

# Test API endpoint
curl -X POST $API_ENDPOINT -d '{"prompt":"Hello"}' -H "Content-Type: application/json"
```

## Extension Points

### 1. Additional MCP Tools

```python
@mcp_server.tool()
def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text"""
    # Implementation here
    pass
```

### 2. Enhanced Memory Strategies

```python
strategies=[
    {
        "customMemoryStrategy": {
            "name": "custom",
            "extraction_prompt": "Extract key insights from conversation"
        }
    }
]
```

### 3. Advanced Frontend Features

```javascript
// WebSocket integration for real-time updates
const ws = new WebSocket('wss://api.example.com/ws');

// File upload capability
const formData = new FormData();
formData.append('file', file);
```

### 4. Multi-Agent Workflows

```python
# Agent orchestration
primary_agent = Agent(...)
specialist_agent = Agent(...)

# Route requests based on intent
if intent == 'technical':
    response = specialist_agent(prompt)
else:
    response = primary_agent(prompt)
```

This documentation provides a comprehensive understanding of the AgentCore Internet Assistant architecture, implementation details, and operational considerations.
