#!/bin/bash

echo "🚀 Setting up GitHub repository for catcmeraman/agentcore"

echo "📋 Steps to complete:"
echo "1. Go to https://github.com/new"
echo "2. Repository name: agentcore"
echo "3. Description: Production-ready AI assistant built with Amazon Bedrock AgentCore for internet data fetching"
echo "4. Make it Public"
echo "5. DO NOT initialize with README, .gitignore, or license (we have them)"
echo "6. Click 'Create repository'"
echo ""
echo "After creating the repository, press Enter to continue..."
read -p ""

echo "🔗 Adding GitHub remote..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/catcmeraman/agentcore.git

echo "📤 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 Repository URL: https://github.com/catcmeraman/agentcore"
    echo ""
    echo "🏷️ Recommended repository topics:"
    echo "aws, bedrock, agentcore, ai, mcp, serverless, python, cloudformation, lambda, s3"
    echo ""
    echo "📖 Your repository is ready! Others can now clone and deploy with:"
    echo "git clone https://github.com/catcmeraman/agentcore.git"
    echo "cd agentcore"
    echo "./deploy_complete.sh"
else
    echo "❌ Failed to push. Please check if the repository was created correctly."
fi
