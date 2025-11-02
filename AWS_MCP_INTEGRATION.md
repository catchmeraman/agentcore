# AWS MCP Integration Guide

This guide covers the integration of specialized AWS MCP servers with your AgentCore agent for comprehensive AWS operations.

## 🏗️ AWS MCP Servers Overview

### 1. AWS Diagram MCP Server (Port 8000)
**Purpose**: Generate AWS architecture diagrams programmatically

**Available Tools**:
- `create_aws_diagram(title, components, filename)` - Create custom AWS diagrams
- `list_aws_services()` - List available AWS services for diagrams  
- `create_serverless_diagram(app_name)` - Generate standard serverless architecture

**Example Usage**:
```json
{
  "title": "My Web App Architecture",
  "components": [
    {"type": "s3", "name": "Frontend", "connects_to": ["CloudFront"]},
    {"type": "cloudfront", "name": "CloudFront", "connects_to": ["APIGateway"]},
    {"type": "apigateway", "name": "API", "connects_to": ["Lambda"]},
    {"type": "lambda", "name": "Backend", "connects_to": ["DynamoDB"]},
    {"type": "dynamodb", "name": "Database"}
  ]
}
```

### 2. AWS EKS MCP Server (Port 8001)
**Purpose**: Manage EKS clusters and Kubernetes operations

**Available Tools**:
- `list_eks_clusters(region)` - List all EKS clusters
- `get_cluster_info(cluster_name, region)` - Get detailed cluster information
- `list_nodegroups(cluster_name, region)` - List node groups
- `get_cluster_pods(cluster_name, namespace)` - Get pods in cluster
- `generate_eks_manifest(app_name, image, replicas)` - Generate K8s manifests

**Prerequisites**:
- AWS CLI configured with EKS permissions
- kubectl installed and configured
- EKS clusters accessible

### 3. AWS Terraform MCP Server (Port 8002)
**Purpose**: Generate and manage Terraform configurations

**Available Tools**:
- `generate_terraform_s3(bucket_name, versioning)` - S3 bucket configuration
- `generate_terraform_lambda(function_name, runtime)` - Lambda function configuration
- `generate_terraform_vpc(vpc_name, cidr_block)` - VPC with subnets configuration
- `generate_terraform_eks(cluster_name, node_group_name)` - EKS cluster configuration
- `validate_terraform(directory)` - Validate Terraform files
- `terraform_plan(directory)` - Run terraform plan

**Prerequisites**:
- Terraform installed
- AWS provider configured

### 4. AWS Cost MCP Server (Port 8003)
**Purpose**: Cost analysis and optimization recommendations

**Available Tools**:
- `get_monthly_costs(months)` - Get monthly cost breakdown
- `get_cost_by_service(days)` - Costs by AWS service
- `get_rightsizing_recommendations()` - EC2 rightsizing suggestions
- `get_savings_plans_recommendations()` - Savings Plans opportunities
- `analyze_cost_anomalies(days)` - Detect unusual spending
- `get_budget_status()` - Current budget status and alerts

**Prerequisites**:
- AWS Cost Explorer API access
- Billing permissions in AWS account

### 5. GitHub MCP Server (Port 8004)
**Purpose**: GitHub repository and operations management

**Available Tools**:
- `list_repositories(username, type)` - List user/org repositories
- `get_repository_info(owner, repo)` - Get detailed repo information
- `list_commits(owner, repo, limit)` - List recent commits
- `list_issues(owner, repo, state, limit)` - List repository issues
- `list_pull_requests(owner, repo, state, limit)` - List pull requests
- `get_file_content(owner, repo, path, branch)` - Get file contents
- `search_repositories(query, sort, limit)` - Search GitHub repositories

**Prerequisites**:
- GitHub token (optional, for higher rate limits)
- Set `GITHUB_TOKEN` environment variable

## 🚀 Quick Start

### 1. Deploy All AWS MCP Servers
```bash
# Clone repository
git clone https://github.com/catchmeraman/agentcore.git
cd agentcore

# Deploy everything with one command
./deploy_aws_mcp.sh
```

### 2. Manual Setup
```bash
# Start MCP servers
docker-compose -f docker-compose-aws.yml up -d

# Deploy AgentCore agent
agentcore configure -e agent_with_aws_mcp.py
agentcore launch
```

### 3. Test Integration
```bash
# Test AWS diagram generation
agentcore invoke '{"prompt": "Create a serverless architecture diagram for my web app"}'

# Test EKS operations
agentcore invoke '{"prompt": "List my EKS clusters and show their status"}'

# Test Terraform generation
agentcore invoke '{"prompt": "Generate Terraform for an S3 bucket with versioning"}'

# Test cost analysis
agentcore invoke '{"prompt": "Show my AWS costs by service for the last month"}'

# Test GitHub operations
agentcore invoke '{"prompt": "List repositories for user catchmeraman"}'
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
export MEMORY_ID=<your-agentcore-memory-id>
export AWS_DEFAULT_REGION=us-west-2

# Optional
export GITHUB_TOKEN=<your-github-token>
export AWS_PROFILE=<your-aws-profile>
```

### AWS Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:ListClusters",
        "eks:DescribeCluster",
        "eks:ListNodegroups",
        "eks:DescribeNodegroup",
        "ce:GetCostAndUsage",
        "ce:GetRightsizingRecommendation",
        "ce:GetSavingsPlansUtilization",
        "ce:GetAnomalies",
        "budgets:DescribeBudgets"
      ],
      "Resource": "*"
    }
  ]
}
```

## 💡 Example Queries

### Architecture & Diagrams
- *"Create an architecture diagram for a serverless web application"*
- *"Generate a diagram showing S3, CloudFront, API Gateway, Lambda, and DynamoDB"*
- *"List all available AWS services I can use in diagrams"*

### EKS Management
- *"List all my EKS clusters and their versions"*
- *"Show me the node groups for my production cluster"*
- *"Generate a Kubernetes deployment manifest for nginx with 3 replicas"*
- *"Get all pods running in the default namespace"*

### Terraform Generation
- *"Generate Terraform configuration for an S3 bucket with encryption"*
- *"Create Terraform for a Lambda function with Python runtime"*
- *"Generate a complete VPC setup with public and private subnets"*
- *"Create Terraform for an EKS cluster with managed node groups"*

### Cost Analysis
- *"Show my AWS costs for the last 3 months broken down by service"*
- *"What are my rightsizing recommendations for EC2 instances?"*
- *"Analyze any cost anomalies in the past week"*
- *"Show my current budget status and any alerts"*

### GitHub Operations
- *"List all repositories for my organization"*
- *"Show me the latest commits in the agentcore repository"*
- *"Get the content of the README.md file from my project"*
- *"Search for repositories related to AWS and Terraform"*

## 🔒 Security Considerations

### MCP Server Security
- Run MCP servers in isolated Docker containers
- Use read-only AWS credentials where possible
- Implement rate limiting for external API calls
- Validate all inputs and sanitize outputs

### Network Security
- MCP servers communicate over localhost only
- Use Docker networks for isolation
- No external network access required for core functionality

### AWS Permissions
- Use least-privilege IAM roles
- Separate roles for different MCP servers
- Enable CloudTrail for audit logging
- Regular permission reviews

## 🐛 Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```bash
   # Check if servers are running
   docker-compose -f docker-compose-aws.yml ps
   
   # Check server logs
   docker-compose -f docker-compose-aws.yml logs aws-eks-mcp
   ```

2. **AWS Permissions Denied**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Test specific permissions
   aws eks list-clusters
   aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-02-01 --granularity MONTHLY --metrics BlendedCost
   ```

3. **Terraform Validation Errors**
   ```bash
   # Check Terraform installation
   terraform version
   
   # Validate configuration manually
   cd terraform-configs
   terraform validate
   ```

4. **GitHub Rate Limiting**
   ```bash
   # Set GitHub token
   export GITHUB_TOKEN=your_token_here
   
   # Check rate limit status
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

### Debug Commands
```bash
# Test individual MCP servers
curl -X POST http://localhost:8000/mcp -d '{"method": "tools/list"}'
curl -X POST http://localhost:8001/mcp -d '{"method": "tools/list"}'

# Check AgentCore agent logs
agentcore logs <agent-name>

# Test agent with specific prompts
agentcore invoke '{"prompt": "Test connection to all MCP servers"}'
```

## 📈 Performance Optimization

### MCP Server Performance
- Use connection pooling for AWS API calls
- Implement caching for frequently accessed data
- Set appropriate timeouts for long-running operations
- Monitor resource usage and scale containers as needed

### AgentCore Integration
- Batch multiple tool calls when possible
- Use async operations for non-blocking calls
- Implement circuit breakers for external dependencies
- Monitor tool execution times and optimize slow operations

## 🔄 Maintenance

### Regular Tasks
- Update MCP server Docker images
- Rotate AWS credentials and GitHub tokens
- Review and update IAM permissions
- Monitor cost and usage patterns
- Update Terraform provider versions

### Monitoring
- Set up CloudWatch alarms for cost thresholds
- Monitor MCP server health and response times
- Track AgentCore agent usage and performance
- Log all tool executions for audit purposes

## 🚀 Advanced Usage

### Custom MCP Server Development
```python
# Create your own AWS MCP server
from bedrock_agentcore.mcp import MCPServer

server = MCPServer()

@server.tool()
def your_custom_aws_tool(param: str) -> str:
    """Your custom AWS operation"""
    # Implementation here
    return result

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8005)
```

### Multi-Region Operations
```python
# Configure MCP servers for multiple regions
AWS_REGIONS = ['us-east-1', 'us-west-2', 'eu-west-1']

for region in AWS_REGIONS:
    # Deploy region-specific MCP servers
    # Configure region-specific tools
```

### Integration with CI/CD
```yaml
# GitHub Actions workflow
name: Deploy AgentCore AWS MCP
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy AWS MCP Integration
        run: ./deploy_aws_mcp.sh
```

Your AgentCore agent now has comprehensive AWS capabilities through specialized MCP servers! 🎉
