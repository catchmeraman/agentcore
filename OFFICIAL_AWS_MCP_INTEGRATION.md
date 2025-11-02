# Official AWS MCP Integration Guide

This guide shows how to integrate the official AWS MCP servers from https://github.com/awslabs/mcp with your AgentCore agent.

## 🎯 Overview

Instead of creating custom MCP servers, this integration uses the official AWS MCP servers maintained by AWS Labs. These servers provide:

- **Official AWS API coverage** - Direct integration with AWS services
- **Maintained by AWS** - Regular updates and bug fixes
- **Production ready** - Tested and optimized by AWS
- **Comprehensive tooling** - Full AWS service coverage

## 🚀 Quick Start

### One-Command Deployment
```bash
git clone https://github.com/catchmeraman/agentcore.git
cd agentcore
./deploy_official_aws_mcp.sh
```

### Manual Setup
```bash
# 1. Setup official AWS MCP servers
python setup_aws_official_mcp.py

# 2. Deploy AgentCore agent
agentcore configure -e agent_with_official_aws_mcp.py
agentcore launch

# 3. Test integration
agentcore invoke '{"prompt": "What AWS MCP tools are available?"}'
```

## 📋 Available Official AWS MCP Servers

The setup script automatically discovers and configures all available servers from the official repository:

### Common Official AWS MCP Servers
- **AWS CLI MCP** - Direct AWS CLI integration
- **AWS CloudFormation MCP** - Stack management and templates
- **AWS EC2 MCP** - Instance and VPC management
- **AWS S3 MCP** - Bucket and object operations
- **AWS Lambda MCP** - Function management and deployment
- **AWS RDS MCP** - Database management
- **AWS IAM MCP** - Identity and access management
- **AWS CloudWatch MCP** - Monitoring and logging

*Note: Available servers depend on the current state of the official repository*

## 🔧 How It Works

### 1. Repository Cloning
```python
# Clones https://github.com/awslabs/mcp to local aws-mcp directory
git clone https://github.com/awslabs/mcp.git aws-mcp
```

### 2. Server Discovery
```python
# Automatically discovers available MCP servers
servers = [d for d in os.listdir('aws-mcp') 
          if os.path.isdir(os.path.join('aws-mcp', d))]
```

### 3. AgentCore Integration
```python
# Connects to servers via stdio protocol
async with stdio_client(cmd) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools_result = await session.list_tools()
```

## 🛠️ Configuration

### Environment Variables
```bash
export MEMORY_ID=<your-agentcore-memory-id>
export AWS_DEFAULT_REGION=us-west-2
export AWS_PROFILE=<your-aws-profile>  # Optional
```

### AWS Permissions
The official MCP servers require standard AWS permissions for the services they manage. Ensure your AWS credentials have appropriate permissions for:

- EC2 (if using EC2 MCP)
- S3 (if using S3 MCP)
- Lambda (if using Lambda MCP)
- CloudFormation (if using CloudFormation MCP)
- etc.

### Server Configuration
After running `setup_aws_official_mcp.py`, check `aws_mcp_config.json`:

```json
{
  "aws-cli": {
    "path": "aws-mcp/aws-cli",
    "port": 8000,
    "url": "http://localhost:8000"
  },
  "aws-s3": {
    "path": "aws-mcp/aws-s3", 
    "port": 8001,
    "url": "http://localhost:8001"
  }
}
```

## 💡 Example Queries

### General AWS Operations
- *"List all my EC2 instances across regions"*
- *"Show me my S3 buckets and their sizes"*
- *"What Lambda functions do I have deployed?"*

### CloudFormation Operations
- *"List my CloudFormation stacks and their status"*
- *"Show me the resources in my production stack"*
- *"Create a CloudFormation template for an S3 bucket"*

### Monitoring & Logs
- *"Show me CloudWatch alarms that are in ALARM state"*
- *"Get the latest logs from my Lambda function"*
- *"What are my top 5 most expensive AWS services this month?"*

## 🔍 Troubleshooting

### Common Issues

1. **Repository Clone Failed**
   ```bash
   # Manual clone
   git clone https://github.com/awslabs/mcp.git aws-mcp
   ```

2. **Server Dependencies Missing**
   ```bash
   # Install Python dependencies
   cd aws-mcp/<server-name>
   pip install -r requirements.txt
   
   # Install Node.js dependencies
   npm install
   ```

3. **AWS Permissions Denied**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Test specific service access
   aws ec2 describe-instances
   aws s3 ls
   ```

4. **MCP Server Connection Failed**
   ```bash
   # Check server process
   ps aux | grep python | grep aws-mcp
   
   # Test server directly
   cd aws-mcp/<server-name>
   python main.py  # or node index.js
   ```

### Debug Commands
```bash
# List discovered servers
cat aws_mcp_config.json | jq -r 'keys[]'

# Check server logs
agentcore logs <agent-name>

# Test specific server
cd aws-mcp/<server-name>
python main.py --help
```

## 🔄 Updates and Maintenance

### Updating Official Servers
```bash
# Update to latest official servers
cd aws-mcp
git pull origin main

# Reinstall dependencies
python setup_aws_official_mcp.py
```

### Adding New Servers
When AWS adds new MCP servers to the official repository:

1. Run `git pull` in the `aws-mcp` directory
2. Run `python setup_aws_official_mcp.py` to discover new servers
3. Restart your AgentCore agent to load new tools

## 🔒 Security Considerations

### Official Server Benefits
- **Maintained by AWS** - Security patches and updates
- **Standard AWS SDK** - Uses official AWS SDKs
- **IAM Integration** - Respects AWS IAM permissions
- **Audit Logging** - Standard AWS CloudTrail integration

### Best Practices
- Use least-privilege IAM roles
- Enable CloudTrail for audit logging
- Regularly update to latest server versions
- Monitor server resource usage

## 📊 Performance

### Advantages of Official Servers
- **Optimized by AWS** - Performance tuned for AWS APIs
- **Efficient protocols** - Uses stdio for fast communication
- **Caching** - Built-in caching for frequently accessed data
- **Rate limiting** - Respects AWS API rate limits

### Monitoring
```bash
# Monitor server processes
ps aux | grep aws-mcp

# Check resource usage
docker stats  # if using Docker

# Monitor API calls
aws logs filter-log-events --log-group-name /aws/lambda/<function-name>
```

## 🚀 Advanced Usage

### Custom Server Configuration
```python
# Modify server startup parameters
cmd = ["python", f"{server_path}/main.py", "--region", "us-west-2", "--profile", "production"]
```

### Multi-Region Setup
```python
# Configure servers for multiple regions
regions = ['us-east-1', 'us-west-2', 'eu-west-1']
for region in regions:
    # Start region-specific server instances
```

### Integration with CI/CD
```yaml
# GitHub Actions workflow
name: Deploy Official AWS MCP
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Official AWS MCP
        run: |
          python setup_aws_official_mcp.py
          ./deploy_official_aws_mcp.sh
```

## 📚 Resources

- **Official Repository**: https://github.com/awslabs/mcp
- **MCP Specification**: https://modelcontextprotocol.io/
- **AWS CLI Documentation**: https://docs.aws.amazon.com/cli/
- **AgentCore Documentation**: https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html

## 🤝 Contributing

To contribute to the official AWS MCP servers:

1. Fork https://github.com/awslabs/mcp
2. Make your changes
3. Submit a pull request to the official repository
4. Update your local integration once changes are merged

Your AgentCore agent now uses official AWS MCP servers for production-ready AWS operations! 🎉
