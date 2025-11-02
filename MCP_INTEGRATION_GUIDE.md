# MCP Integration Guide for AgentCore

This guide shows how to integrate multiple MCP (Model Context Protocol) servers with your AgentCore agents.

## Integration Methods

### 1. Direct Tool Integration (Simplest)

Add MCP tools directly to your AgentCore agent:

```python
# In your agent.py
@mcp_server.tool()
def your_custom_tool(param: str) -> str:
    """Your tool description"""
    # Tool implementation
    return result
```

**Pros**: Simple, no external dependencies
**Cons**: All tools in one process, limited scalability

### 2. AgentCore Gateway Integration (Recommended)

Use AgentCore Gateway to connect to external MCP servers:

```bash
# Setup multiple MCP targets
python setup_multiple_mcp.py

# Deploy agent with gateway integration
export GATEWAY_URL=<your-gateway-url>
export GATEWAY_TOKEN=<your-access-token>
agentcore configure -e agent_with_external_mcp.py
agentcore launch
```

**Pros**: Scalable, secure, managed by AWS
**Cons**: Requires AgentCore Gateway setup

### 3. Local MCP Servers (Development)

Run MCP servers locally for development:

```bash
# Start local MCP servers
docker-compose up -d

# Test agent locally
python agent_with_external_mcp.py
```

**Pros**: Full control, easy debugging
**Cons**: Not production-ready, requires infrastructure

## Available MCP Tool Categories

### Internet & Web Tools
- `fetch_url_data(url)` - Fetch content from URLs
- `search_web(query)` - Web search
- `scrape_website(url, selector)` - Web scraping

### File System Tools
- `read_file(file_path)` - Read file contents
- `list_directory(directory_path)` - List directory contents
- `file_info(file_path)` - Get file metadata

### Database Tools
- `query_database(query)` - Execute SQL queries
- `insert_data(table, data)` - Insert data
- `update_data(table, data, condition)` - Update records

### System Tools
- `run_command(command)` - Execute system commands (restricted)
- `get_system_info()` - System information
- `monitor_resources()` - Resource monitoring

## Quick Setup Examples

### Add Internet Tools
```python
@mcp_server.tool()
def fetch_url_data(url: str) -> str:
    response = requests.get(url, timeout=10)
    return response.text[:1000]
```

### Add Database Tools
```python
@mcp_server.tool()
def query_database(query: str) -> str:
    if not query.upper().startswith('SELECT'):
        return "Only SELECT queries allowed"
    # Execute query and return results
```

### Connect to External MCP Server
```python
# In your agent
async def get_external_tools():
    async with streamablehttp_client("http://localhost:8001/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.list_tools()
```

## Security Considerations

### Tool Restrictions
- Whitelist allowed commands for system tools
- Validate file paths for filesystem access
- Use read-only database connections
- Implement rate limiting for web requests

### Authentication
- Use JWT tokens for AgentCore Gateway
- Implement API keys for external MCP servers
- Validate all inputs and sanitize outputs

### Network Security
- Run MCP servers in isolated networks
- Use HTTPS for all communications
- Implement proper CORS policies

## Deployment Patterns

### Pattern 1: All-in-One Agent
```
AgentCore Agent
├── Internet Tools
├── File System Tools
├── Database Tools
└── Custom Tools
```

### Pattern 2: Gateway-Based
```
AgentCore Agent → AgentCore Gateway → Multiple MCP Servers
                                   ├── Filesystem MCP
                                   ├── Database MCP
                                   └── Web MCP
```

### Pattern 3: Hybrid
```
AgentCore Agent
├── Core Tools (built-in)
└── Gateway Connection → External MCP Servers
```

## Testing Your Integration

### 1. Test Individual Tools
```bash
# Test specific tool
agentcore invoke '{"prompt": "List files in /data directory"}'
```

### 2. Test Tool Combinations
```bash
# Test multiple tools in sequence
agentcore invoke '{"prompt": "Read the file /data/config.json and search web for related information"}'
```

### 3. Load Testing
```bash
# Test with multiple concurrent requests
for i in {1..10}; do
  agentcore invoke '{"prompt": "What is the current time?"}' &
done
```

## Troubleshooting

### Common Issues

1. **Tool Not Found**
   - Check tool registration with `@mcp_server.tool()`
   - Verify tool is added to agent.tools list

2. **Connection Errors**
   - Check MCP server is running
   - Verify network connectivity
   - Check authentication tokens

3. **Permission Errors**
   - Verify IAM roles and policies
   - Check file system permissions
   - Validate API access rights

### Debug Commands
```bash
# Check agent status
agentcore status <agent-name>

# View agent logs
agentcore logs <agent-name>

# Test MCP server directly
curl -X POST http://localhost:8001/mcp -d '{"method": "tools/list"}'
```

## Best Practices

1. **Tool Design**
   - Keep tools focused and single-purpose
   - Implement proper error handling
   - Add comprehensive documentation

2. **Performance**
   - Set appropriate timeouts
   - Implement caching where possible
   - Limit response sizes

3. **Security**
   - Validate all inputs
   - Use least-privilege access
   - Implement rate limiting

4. **Monitoring**
   - Log tool usage and performance
   - Monitor error rates
   - Track resource consumption

## Example Queries

Once integrated, your agent can handle complex queries like:

- "Read the config file and search for documentation about those settings"
- "Query the database for user data and fetch their profile from the API"
- "List all Python files in the project and analyze their imports"
- "Search for recent news about AI and save summaries to a file"

Your AgentCore agent now has access to a rich ecosystem of MCP tools! 🚀
