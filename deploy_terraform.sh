#!/bin/bash

echo "🚀 AgentCore Internet Assistant - Terraform Deployment"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup memory
echo "🧠 Setting up AgentCore Memory..."
python setup_memory.py > memory_output.txt
export MEMORY_ID=$(grep "export MEMORY_ID" memory_output.txt | cut -d'=' -f2)
echo "Memory ID: $MEMORY_ID"

# Deploy AgentCore agent first
echo "🤖 Deploying AgentCore agent..."
agentcore configure -e agent.py
agentcore launch > agentcore_output.txt

# Get AgentCore ARN
AGENT_ARN=$(grep "Agent ARN" agentcore_output.txt | cut -d':' -f2- | tr -d ' ')
echo "Agent ARN: $AGENT_ARN"

# Initialize and deploy Terraform
echo "🏗️ Deploying infrastructure with Terraform..."
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="agent_arn=$AGENT_ARN"

# Apply deployment
terraform apply -var="agent_arn=$AGENT_ARN" -auto-approve

# Get outputs
API_ENDPOINT=$(terraform output -raw api_endpoint)
BUCKET_NAME=$(terraform output -raw s3_bucket_name)

cd ..

# Update frontend with API endpoint
echo "🌐 Configuring frontend..."
sed -i "s|YOUR_AGENTCORE_ENDPOINT|$API_ENDPOINT|g" frontend/index.html

# Upload frontend to S3
echo "📤 Uploading frontend..."
aws s3 cp frontend/index.html s3://$BUCKET_NAME/

echo "✅ Deployment Complete!"
echo "🌐 Frontend URL: $(cd terraform && terraform output -raw frontend_url)"
echo "🔗 API Endpoint: $API_ENDPOINT"
echo "🧠 Memory ID: $MEMORY_ID"
echo "🤖 Agent ARN: $AGENT_ARN"
