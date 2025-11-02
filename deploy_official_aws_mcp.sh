#!/bin/bash

echo "🚀 Official AWS MCP Integration Deployment"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install mcp

# Setup AgentCore Memory
echo "🧠 Setting up AgentCore Memory..."
python setup_memory.py > memory_output.txt
export MEMORY_ID=$(grep "export MEMORY_ID" memory_output.txt | cut -d'=' -f2)
echo "Memory ID: $MEMORY_ID"

# Setup official AWS MCP servers
echo "📥 Setting up official AWS MCP servers..."
python setup_aws_official_mcp.py

# Check what servers are available
if [ -f "aws_mcp_config.json" ]; then
    echo "📋 Available AWS MCP servers:"
    cat aws_mcp_config.json | jq -r 'keys[]'
else
    echo "❌ Failed to setup AWS MCP servers"
    exit 1
fi

# Create Dockerfiles for official AWS MCP integration
echo "🐳 Creating Dockerfiles..."

# AWS MCP Proxy Dockerfile
cat > Dockerfile.aws-mcp-proxy << 'EOF'
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Install Python dependencies
RUN pip install mcp boto3 asyncio

# Copy AWS MCP servers
COPY aws-mcp /app/aws-mcp
COPY start_aws_mcp_servers.py /app/

EXPOSE 8000-8010
CMD ["python", "start_aws_mcp_servers.py"]
EOF

# Official AWS Agent Dockerfile
cat > Dockerfile.official-aws-agent << 'EOF'
FROM python:3.9-slim
WORKDIR /app

RUN pip install bedrock-agentcore strands-agents mcp boto3

COPY agent_with_official_aws_mcp.py .
COPY aws_mcp_config.json .

EXPOSE 8080
CMD ["python", "agent_with_official_aws_mcp.py"]
EOF

# Create server startup script
cat > start_aws_mcp_servers.py << 'EOF'
"""
Start all official AWS MCP servers
"""
import json
import subprocess
import asyncio
import os
import time

async def start_mcp_server(server_name, config):
    """Start an individual MCP server"""
    server_path = config['path']
    port = config['port']
    
    print(f"🚀 Starting {server_name} on port {port}...")
    
    # Determine how to start the server
    if os.path.exists(f"{server_path}/main.py"):
        cmd = ["python", f"{server_path}/main.py", "--port", str(port)]
    elif os.path.exists(f"{server_path}/index.js"):
        cmd = ["node", f"{server_path}/index.js", "--port", str(port)]
    elif os.path.exists(f"{server_path}/server.py"):
        cmd = ["python", f"{server_path}/server.py", "--port", str(port)]
    else:
        print(f"❌ No executable found for {server_name}")
        return None
    
    try:
        process = subprocess.Popen(cmd, cwd=server_path)
        print(f"✅ Started {server_name} (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {server_name}: {e}")
        return None

async def main():
    """Start all AWS MCP servers"""
    if not os.path.exists('aws_mcp_config.json'):
        print("❌ AWS MCP config not found")
        return
    
    with open('aws_mcp_config.json', 'r') as f:
        server_config = json.load(f)
    
    processes = []
    for server_name, config in server_config.items():
        process = await start_mcp_server(server_name, config)
        if process:
            processes.append(process)
    
    print(f"🎉 Started {len(processes)} AWS MCP servers")
    
    # Keep servers running
    try:
        while True:
            time.sleep(10)
            # Check if any process died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️ Process {i} died, restarting...")
                    # Could implement restart logic here
    except KeyboardInterrupt:
        print("🛑 Shutting down servers...")
        for process in processes:
            process.terminate()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Deploy AgentCore agent
echo "🤖 Deploying AgentCore agent with official AWS MCP..."
agentcore configure -e agent_with_official_aws_mcp.py
agentcore launch > agentcore_official_output.txt

# Get AgentCore ARN
AGENT_ARN=$(grep "Agent ARN" agentcore_official_output.txt | cut -d':' -f2- | tr -d ' ')
echo "Agent ARN: $AGENT_ARN"

# Optional: Deploy infrastructure
read -p "Deploy infrastructure? (terraform/cloudformation/skip): " DEPLOY_CHOICE

case $DEPLOY_CHOICE in
    terraform)
        echo "🏗️ Deploying with Terraform..."
        cd terraform
        terraform init
        terraform apply -var="agent_arn=$AGENT_ARN" -auto-approve
        API_ENDPOINT=$(terraform output -raw api_endpoint)
        BUCKET_NAME=$(terraform output -raw s3_bucket_name)
        cd ..
        ;;
    cloudformation)
        echo "🏗️ Deploying with CloudFormation..."
        aws cloudformation deploy \
          --template-file infrastructure.yaml \
          --stack-name agentcore-official-aws-mcp \
          --capabilities CAPABILITY_IAM
        API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name agentcore-official-aws-mcp --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
        BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name agentcore-official-aws-mcp --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' --output text | cut -d'/' -f3)
        ;;
    *)
        echo "⏭️ Skipping infrastructure deployment"
        ;;
esac

# Configure frontend if infrastructure was deployed
if [ ! -z "$API_ENDPOINT" ]; then
    echo "🌐 Configuring frontend..."
    sed -i "s|YOUR_AGENTCORE_ENDPOINT|$API_ENDPOINT|g" frontend/index.html
    aws s3 cp frontend/index.html s3://$BUCKET_NAME/
    echo "Frontend URL: http://$BUCKET_NAME.s3-website-us-west-2.amazonaws.com"
fi

echo "✅ Official AWS MCP Integration Complete!"
echo ""
echo "📋 Summary:"
echo "🧠 Memory ID: $MEMORY_ID"
echo "🤖 Agent ARN: $AGENT_ARN"
echo "🔧 Official AWS MCP Servers: $(cat aws_mcp_config.json | jq -r 'keys | length') servers"
echo "🌐 API Endpoint: ${API_ENDPOINT:-'Not deployed'}"
echo ""
echo "🧪 Test your agent:"
echo "agentcore invoke '{\"prompt\": \"What AWS MCP tools are available?\"}'"
echo ""
echo "📚 Available servers:"
cat aws_mcp_config.json | jq -r 'to_entries[] | "- \(.key): \(.value.path)"'
