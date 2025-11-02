#!/bin/bash

echo "🚀 Complete AgentCore Internet Assistant Deployment"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Setup memory
echo "Setting up AgentCore Memory..."
python setup_memory.py > memory_output.txt
export MEMORY_ID=$(grep "export MEMORY_ID" memory_output.txt | cut -d'=' -f2)
echo "Memory ID: $MEMORY_ID"

# Deploy infrastructure
echo "Deploying infrastructure..."
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name agentcore-internet-assistant \
  --capabilities CAPABILITY_IAM

# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name agentcore-internet-assistant \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Update frontend with API endpoint
sed -i "s|YOUR_AGENTCORE_ENDPOINT|$API_ENDPOINT|g" frontend/index.html

# Deploy AgentCore agent
echo "Deploying AgentCore agent..."
agentcore configure -e agent.py
agentcore launch > agentcore_output.txt

# Get AgentCore ARN
AGENT_ARN=$(grep "Agent ARN" agentcore_output.txt | cut -d':' -f2- | tr -d ' ')

# Update Lambda with AgentCore ARN
aws lambda update-function-configuration \
  --function-name agentcore-api-handler \
  --environment Variables="{AGENT_ARN=$AGENT_ARN}"

# Upload frontend to S3
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name agentcore-internet-assistant \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' \
  --output text | cut -d'/' -f3)

aws s3 cp frontend/index.html s3://$BUCKET_NAME/

echo "✅ Deployment Complete!"
echo "Frontend URL: $(aws cloudformation describe-stacks --stack-name agentcore-internet-assistant --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' --output text)"
echo "API Endpoint: $API_ENDPOINT"
