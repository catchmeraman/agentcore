# Project Structure

```
agentcore-app/
├── README.md                          # Main project documentation
├── DETAILED_DOCUMENTATION.md          # Comprehensive technical guide
├── PROJECT_STRUCTURE.md              # This file - project organization
├── LICENSE                           # MIT License
├── .gitignore                        # Git ignore patterns
├── requirements.txt                  # Python dependencies
├── architecture-diagram.png          # System architecture diagram
│
├── Core Application Files
├── agent.py                          # Main AgentCore agent with MCP tools
├── setup_memory.py                   # AgentCore Memory configuration
├── api_gateway.py                    # Lambda function for API integration
│
├── Infrastructure as Code
├── infrastructure.yaml               # CloudFormation template
├── deploy.sh                         # Basic deployment script
├── deploy_complete.sh                # Complete CloudFormation deployment
├── deploy_terraform.sh               # Complete Terraform deployment
│
├── Terraform Infrastructure
├── terraform/
│   ├── main.tf                       # Provider configuration
│   ├── variables.tf                  # Input variables
│   ├── outputs.tf                    # Output values
│   ├── s3.tf                         # S3 bucket for frontend
│   ├── iam.tf                        # IAM roles and policies
│   ├── lambda.tf                     # Lambda function
│   ├── api_gateway.tf                # API Gateway configuration
│   ├── cognito.tf                    # Cognito User Pool
│   └── destroy.sh                    # Terraform cleanup script
│
├── Frontend
└── frontend/
    └── index.html                    # Web chat interface
```

## File Descriptions

### Core Application Files

#### `agent.py`
- **Purpose**: Main AgentCore agent implementation
- **Components**:
  - AgentCore Runtime app initialization
  - MCP server with internet fetching tools
  - Memory hooks for conversation persistence
  - Strands agent integration
- **Key Features**:
  - `fetch_url_data()` tool for direct URL access
  - `search_web()` tool for web search
  - Automatic memory management
  - Session isolation

#### `setup_memory.py`
- **Purpose**: Creates and configures AgentCore Memory resources
- **Memory Types**:
  - Short-term memory (STM) for session context
  - Long-term memory (LTM) with extraction strategies
- **Strategies**:
  - User preference extraction
  - Semantic memory for facts
- **Output**: Memory ID for agent configuration

#### `api_gateway.py`
- **Purpose**: Lambda function for API Gateway integration
- **Features**:
  - CORS handling for frontend requests
  - AgentCore Runtime invocation
  - Error handling and response formatting
  - Session management

### Infrastructure as Code

#### `infrastructure.yaml`
- **Purpose**: Complete AWS infrastructure definition
- **Resources**:
  - S3 bucket for frontend hosting
  - API Gateway with REST endpoints
  - Lambda function for API handling
  - IAM roles with least-privilege permissions
  - Cognito User Pool for authentication
- **Outputs**: Frontend URL and API endpoint

#### `deploy_complete.sh`
- **Purpose**: Automated end-to-end deployment
- **Process**:
  1. Install Python dependencies
  2. Create AgentCore Memory resources
  3. Deploy CloudFormation infrastructure
  4. Configure and deploy AgentCore agent
  5. Update frontend with API endpoints
  6. Upload frontend to S3
- **Features**: Error handling and status reporting

### Frontend

#### `frontend/index.html`
- **Purpose**: Web-based chat interface
- **Features**:
  - Responsive design for mobile/desktop
  - Real-time chat with AgentCore agent
  - API integration with error handling
  - HTTPS-only communication
- **Technologies**: HTML5, CSS3, JavaScript (ES6+)

### Configuration Files

#### `requirements.txt`
- **Dependencies**:
  - `bedrock-agentcore`: Core AgentCore SDK
  - `strands-agents`: Agent framework
  - `requests`: HTTP client for MCP tools
  - `mcp`: Model Context Protocol client

#### `.gitignore`
- **Excludes**:
  - Python cache and build files
  - Virtual environments
  - AWS credentials and keys
  - Generated configuration files
  - IDE and OS specific files

### Documentation Files

#### `README.md`
- **Content**: User-facing documentation
- **Sections**: Features, quick start, architecture, examples
- **Audience**: Developers and users

#### `DETAILED_DOCUMENTATION.md`
- **Content**: Comprehensive technical documentation
- **Sections**: 
  - Architecture deep-dive
  - Code explanations
  - Deployment processes
  - Security considerations
  - Troubleshooting guides
- **Audience**: Technical implementers and maintainers

#### `PROJECT_STRUCTURE.md`
- **Content**: This file - project organization
- **Purpose**: Help developers understand codebase structure
- **Audience**: Contributors and maintainers

## Development Workflow

### Local Development
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure AWS credentials
4. Run memory setup: `python setup_memory.py`
5. Test agent locally: `python agent.py`

### Deployment
1. **Development**: Use `deploy.sh` for basic deployment
2. **Production**: Use `deploy_complete.sh` for full automation
3. **Testing**: Access frontend URL after deployment
4. **Monitoring**: Check CloudWatch logs for issues

### Customization
1. **Add MCP Tools**: Extend `agent.py` with new `@mcp_server.tool()` functions
2. **Modify Memory**: Update strategies in `setup_memory.py`
3. **Frontend Changes**: Edit `frontend/index.html`
4. **Infrastructure**: Modify `infrastructure.yaml` for additional AWS resources

## Security Considerations

### Secrets Management
- No hardcoded credentials in code
- Use IAM roles for service authentication
- Environment variables for configuration
- AWS Secrets Manager for sensitive data

### Network Security
- HTTPS-only communication
- CORS configuration for frontend
- VPC endpoints for private communication
- Security groups with minimal access

### Data Protection
- Encrypted storage (AgentCore managed)
- Request size and timeout limits
- Input validation and sanitization
- Automatic data expiration

## Monitoring and Observability

### Logging
- CloudWatch Logs for all components
- AgentCore built-in observability
- Structured logging with correlation IDs
- Error tracking and alerting

### Metrics
- Request/response times
- Error rates and types
- Usage patterns and trends
- Resource utilization

### Debugging
- Local testing capabilities
- Log aggregation and search
- Performance profiling
- Error reproduction tools
