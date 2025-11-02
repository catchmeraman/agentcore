"""Setup AgentCore Memory"""
from bedrock_agentcore.memory import MemoryClient
import uuid

client = MemoryClient(region_name='us-west-2')

# Create memory with user preferences and facts extraction
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

print(f"Memory created: {memory['id']}")
print(f"export MEMORY_ID={memory['id']}")
