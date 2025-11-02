#!/bin/bash

echo "🗑️ Cleaning up AgentCore Internet Assistant resources..."

# Destroy Terraform resources
echo "🏗️ Destroying Terraform infrastructure..."
terraform destroy -auto-approve

# Clean up local files
echo "🧹 Cleaning up local files..."
rm -f api_handler.zip
rm -f terraform.tfstate*
rm -f .terraform.lock.hcl
rm -rf .terraform/

echo "✅ Terraform cleanup complete!"
echo "ℹ️ Don't forget to manually delete:"
echo "   - AgentCore agent (agentcore delete <agent-name>)"
echo "   - AgentCore memory resources"
