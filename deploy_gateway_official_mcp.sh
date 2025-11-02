#!/bin/bash

echo "🚀 AgentCore Gateway + Official AWS MCP Integration"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install bedrock-agentcore-starter-toolkit mcp

# Setup AgentCore Memory
echo "🧠 Setting up AgentCore Memory..."
python setup_memory.py > memory_output.txt
export MEMORY_ID=$(grep "export MEMORY_ID" memory_output.txt | cut -d'=' -f2)
echo "Memory ID: $MEMORY_ID"

# Setup Gateway with Official MCP
echo "🌐 Setting up Gateway with Official AWS MCP servers..."
python setup_gateway_with_official_mcp.py

# Check if Gateway setup was successful
if [ ! -f "official_mcp_gateway_config.json" ]; then
    echo "❌ Gateway setup failed"
    exit 1
fi

echo "📋 Gateway configuration:"
cat official_mcp_gateway_config.json | jq -r '.servers | keys[]'

# Deploy AgentCore Agent
echo "🤖 Deploying AgentCore agent with Gateway integration..."
agentcore configure -e agent_with_gateway_official_mcp.py
agentcore launch > agentcore_gateway_output.txt

# Get AgentCore ARN
AGENT_ARN=$(grep "Agent ARN" agentcore_gateway_output.txt | cut -d':' -f2- | tr -d ' ')
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
          --stack-name agentcore-gateway-mcp \
          --capabilities CAPABILITY_IAM
        API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name agentcore-gateway-mcp --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
        BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name agentcore-gateway-mcp --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' --output text | cut -d'/' -f3)
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

# Test the integration
echo "🧪 Testing Gateway + Official MCP integration..."
agentcore invoke '{"prompt": "What official AWS MCP tools are available through the Gateway?"}' > test_output.txt
echo "Test result:"
cat test_output.txt

echo "✅ Gateway + Official AWS MCP Integration Complete!"
echo ""
echo "📋 Summary:"
echo "🧠 Memory ID: $MEMORY_ID"
echo "🤖 Agent ARN: $AGENT_ARN"
echo "🌐 Gateway: $(cat official_mcp_gateway_config.json | jq -r '.gateway_url')"
echo "🎯 MCP Targets: $(cat official_mcp_gateway_config.json | jq -r '.official_mcp_targets | keys | length') official AWS MCP servers"
echo "🌐 API Endpoint: ${API_ENDPOINT:-'Not deployed'}"
echo ""
echo "🧪 Test commands:"
echo "agentcore invoke '{\"prompt\": \"List my S3 buckets using official AWS MCP\"}'"
echo "agentcore invoke '{\"prompt\": \"Show my EC2 instances via Gateway\"}'"
echo "agentcore invoke '{\"prompt\": \"Get my AWS costs through official MCP tools\"}'"
echo ""
echo "📚 Available official MCP servers:"
cat official_mcp_gateway_config.json | jq -r '.servers | to_entries[] | "- \(.key): \(.value.path)"'
