#!/bin/bash

echo "🚀 AgentCore AWS MCP Integration Deployment"

# Check prerequisites
echo "🔍 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup AgentCore Memory
echo "🧠 Setting up AgentCore Memory..."
python setup_memory.py > memory_output.txt
export MEMORY_ID=$(grep "export MEMORY_ID" memory_output.txt | cut -d'=' -f2)
echo "Memory ID: $MEMORY_ID"

# Create Dockerfiles for MCP servers
echo "🐳 Creating Dockerfiles for MCP servers..."

# AWS Diagram MCP Dockerfile
mkdir -p mcp-servers/aws-diagram
cat > mcp-servers/aws-diagram/Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN pip install bedrock-agentcore diagrams
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
EOF

# AWS EKS MCP Dockerfile
mkdir -p mcp-servers/aws-eks
cat > mcp-servers/aws-eks/Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && ./aws/install && rm -rf aws awscliv2.zip
RUN pip install bedrock-agentcore boto3
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
EOF

# AWS Terraform MCP Dockerfile
mkdir -p mcp-servers/aws-terraform
cat > mcp-servers/aws-terraform/Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y wget unzip && \
    wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip && \
    unzip terraform_1.6.0_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_1.6.0_linux_amd64.zip
RUN pip install bedrock-agentcore
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
EOF

# AWS Cost MCP Dockerfile
mkdir -p mcp-servers/aws-cost
cat > mcp-servers/aws-cost/Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN pip install bedrock-agentcore boto3
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
EOF

# GitHub MCP Dockerfile
mkdir -p mcp-servers/github
cat > mcp-servers/github/Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN pip install bedrock-agentcore requests
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
EOF

# Create AgentCore Agent Dockerfile
cat > Dockerfile.aws-agent << 'EOF'
FROM python:3.9-slim
WORKDIR /app
RUN pip install bedrock-agentcore strands-agents mcp requests
COPY agent_with_aws_mcp.py .
EXPOSE 8080
CMD ["python", "agent_with_aws_mcp.py"]
EOF

# Start AWS MCP servers
echo "🔧 Starting AWS MCP servers..."
docker-compose -f docker-compose-aws.yml up -d --build

# Wait for servers to start
echo "⏳ Waiting for MCP servers to start..."
sleep 30

# Test MCP server connections
echo "🧪 Testing MCP server connections..."
for port in 8000 8001 8002 8003 8004; do
    if curl -s http://localhost:$port/health >/dev/null 2>&1; then
        echo "✅ MCP server on port $port is running"
    else
        echo "⚠️ MCP server on port $port may not be ready yet"
    fi
done

# Deploy AgentCore agent with AWS MCP integration
echo "🤖 Deploying AgentCore agent with AWS MCP integration..."
agentcore configure -e agent_with_aws_mcp.py
agentcore launch > agentcore_aws_output.txt

# Get AgentCore ARN
AGENT_ARN=$(grep "Agent ARN" agentcore_aws_output.txt | cut -d':' -f2- | tr -d ' ')
echo "Agent ARN: $AGENT_ARN"

# Deploy infrastructure (optional - choose Terraform or CloudFormation)
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
          --stack-name agentcore-aws-mcp-assistant \
          --capabilities CAPABILITY_IAM
        API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name agentcore-aws-mcp-assistant --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
        BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name agentcore-aws-mcp-assistant --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' --output text | cut -d'/' -f3)
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

echo "✅ AWS MCP Integration Deployment Complete!"
echo ""
echo "📋 Summary:"
echo "🧠 Memory ID: $MEMORY_ID"
echo "🤖 Agent ARN: $AGENT_ARN"
echo "🔧 MCP Servers: 5 AWS MCP servers running"
echo "🌐 API Endpoint: ${API_ENDPOINT:-'Not deployed'}"
echo ""
echo "🧪 Test your agent:"
echo "agentcore invoke '{\"prompt\": \"List my EKS clusters and create a diagram\"}'"
echo "agentcore invoke '{\"prompt\": \"Show my AWS costs for the last 3 months\"}'"
echo "agentcore invoke '{\"prompt\": \"Generate Terraform for an S3 bucket\"}'"
