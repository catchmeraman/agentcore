#!/bin/bash

echo "🚀 Deploying AgentCore Internet Assistant..."

# Setup memory
echo "Setting up memory..."
python setup_memory.py > memory_output.txt
export MEMORY_ID=$(grep "export MEMORY_ID" memory_output.txt | cut -d'=' -f2)
echo "Memory ID: $MEMORY_ID"

# Configure and deploy agent
echo "Configuring AgentCore..."
agentcore configure -e agent.py

echo "Deploying to AgentCore Runtime..."
agentcore launch

echo "✅ Deployment complete!"
echo "Your agent is now running on AgentCore Runtime"
echo "Update the API_ENDPOINT in frontend/index.html with your agent's endpoint"
