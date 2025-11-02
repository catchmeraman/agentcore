"""
AgentCore agent with multiple MCP tools integrated
"""
import os
import json
import requests
import subprocess
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.mcp import MCPServer
from strands import Agent
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent

app = BedrockAgentCoreApp()
mcp_server = MCPServer()
memory_client = MemoryClient(region_name='us-west-2')
MEMORY_ID = os.getenv('MEMORY_ID')

# Internet Data Fetching Tools
@mcp_server.tool()
def fetch_url_data(url: str) -> str:
    """Fetch data from a URL"""
    try:
        response = requests.get(url, timeout=10)
        return response.text[:1000]
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

@mcp_server.tool()
def search_web(query: str) -> str:
    """Search the web using DuckDuckGo API"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('AbstractText', 'No results found')[:500]
    except Exception as e:
        return f"Search error: {str(e)}"

# File System Tools
@mcp_server.tool()
def read_file(file_path: str) -> str:
    """Read contents of a file"""
    try:
        with open(file_path, 'r') as f:
            return f.read()[:1000]
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp_server.tool()
def list_directory(directory_path: str) -> str:
    """List contents of a directory"""
    try:
        import os
        files = os.listdir(directory_path)
        return json.dumps(files[:20])  # Limit to 20 files
    except Exception as e:
        return f"Error listing directory: {str(e)}"

# System Tools
@mcp_server.tool()
def run_command(command: str) -> str:
    """Execute a system command (restricted)"""
    # Whitelist safe commands
    safe_commands = ['ls', 'pwd', 'date', 'whoami', 'df', 'free']
    cmd_parts = command.split()
    
    if not cmd_parts or cmd_parts[0] not in safe_commands:
        return "Command not allowed. Safe commands: " + ", ".join(safe_commands)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout[:500] if result.stdout else result.stderr[:500]
    except Exception as e:
        return f"Command error: {str(e)}"

# Database Tools (SQLite example)
@mcp_server.tool()
def query_database(query: str) -> str:
    """Execute a SQLite query (read-only)"""
    if not query.upper().startswith('SELECT'):
        return "Only SELECT queries are allowed"
    
    try:
        import sqlite3
        # Use in-memory database for demo
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create sample table
        cursor.execute('''CREATE TABLE users (id INTEGER, name TEXT, email TEXT)''')
        cursor.execute('''INSERT INTO users VALUES (1, 'John', 'john@example.com')''')
        cursor.execute('''INSERT INTO users VALUES (2, 'Jane', 'jane@example.com')''')
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        return json.dumps(results)
    except Exception as e:
        return f"Database error: {str(e)}"

# Memory Hook (same as before)
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

# Create agent with all tools
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="You're a helpful assistant with internet access, file system access, and database capabilities.",
    hooks=[MemoryHook()] if MEMORY_ID else [],
    state={"session_id": "default"}
)

@app.entrypoint
def invoke(payload, context):
    """Main entry point with all MCP tools"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    # Add all MCP tools to agent
    agent.tools = [
        fetch_url_data, search_web,      # Internet tools
        read_file, list_directory,       # File system tools
        run_command,                     # System tools
        query_database                   # Database tools
    ]
    
    response = agent(payload.get("prompt", "Hello"))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
