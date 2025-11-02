"""
AgentCore app with MCP tools for internet data fetching
"""
import os
import json
import requests
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.mcp import MCPServer
from strands import Agent
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent

# Initialize AgentCore components
app = BedrockAgentCoreApp()
mcp_server = MCPServer()
memory_client = MemoryClient(region_name='us-west-2')
MEMORY_ID = os.getenv('MEMORY_ID')

# MCP Tools for internet data fetching
@mcp_server.tool()
def fetch_url_data(url: str) -> str:
    """Fetch data from a URL"""
    try:
        response = requests.get(url, timeout=10)
        return response.text[:1000]  # Limit response size
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

@mcp_server.tool()
def search_web(query: str) -> str:
    """Search the web using a simple API"""
    # Using a free search API (replace with your preferred service)
    try:
        # Example using DuckDuckGo Instant Answer API
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get('AbstractText', 'No results found')[:500]
    except Exception as e:
        return f"Search error: {str(e)}"

class MemoryHook(HookProvider):
    """Handle memory operations"""
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

# Create agent
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="You're a helpful assistant that can fetch internet data and remember conversations.",
    hooks=[MemoryHook()] if MEMORY_ID else [],
    state={"session_id": "default"}
)

@app.entrypoint
def invoke(payload, context):
    """Main entry point"""
    if hasattr(context, 'session_id'):
        agent.state.set("session_id", context.session_id)
    
    # Add MCP tools to agent
    agent.tools = [fetch_url_data, search_web]
    
    response = agent(payload.get("prompt", "Hello"))
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()
