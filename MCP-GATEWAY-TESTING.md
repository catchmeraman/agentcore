# MCP Gateway Validation and Testing Guide

This guide provides comprehensive methods to validate and test AgentCore Gateway configuration with AWS API MCP server integration.

## 1. AWS Console Validation

### Check Gateway Status:
```
AWS Console → Amazon Bedrock → AgentCore → Gateways → [Your Gateway]
- Status: Should show "Active" or "Running"
- Health: All MCP targets should show "Healthy"
- Metrics: Check request count and latency
```

### Validate MCP Target Registration:
```
Gateway Details → MCP Targets → aws-api-mcp
- Status: Active ✅
- Health Check: Passing ✅
- Last Health Check: Recent timestamp
- Endpoint: Responding
```

## 2. CLI Health Check Commands

### Test Gateway Connectivity:
```bash
# Check gateway status
aws bedrock-agent-core describe-gateway --gateway-id "gateway-12345"

# List registered MCP targets
aws bedrock-agent-core list-mcp-targets --gateway-id "gateway-12345"

# Test specific MCP target health
aws bedrock-agent-core get-mcp-target-health \
  --gateway-id "gateway-12345" \
  --target-name "aws-api-mcp"
```

### Direct Health Check:
```bash
# Test gateway endpoint directly
curl -X GET \
  "https://gateway-12345.agentcore.us-east-1.amazonaws.com/health" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Test MCP target endpoint
curl -X GET \
  "https://api.gateway.us-east-1.amazonaws.com/aws-api-mcp/health" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## 3. MCP Protocol Testing

### Test MCP Tools List:
```bash
curl -X POST \
  "https://api.gateway.us-east-1.amazonaws.com/aws-api-mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {"name": "call_aws", "description": "Execute AWS CLI commands"},
      {"name": "suggest_aws_commands", "description": "Suggest AWS CLI commands"},
      {"name": "get_regional_availability", "description": "Check AWS service availability"}
    ]
  }
}
```

### Test MCP Tool Execution:
```bash
curl -X POST \
  "https://api.gateway.us-east-1.amazonaws.com/aws-api-mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "call_aws",
      "arguments": {
        "cli_command": "aws s3 ls"
      }
    }
  }'
```

## 4. Python Test Script

Create a test script to validate the gateway:

```python
import requests
import json
import boto3

class GatewayTester:
    def __init__(self, gateway_endpoint, jwt_token):
        self.gateway_endpoint = gateway_endpoint
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def test_health(self):
        """Test gateway health endpoint"""
        response = requests.get(f"{self.gateway_endpoint}/health", headers=self.headers)
        print(f"Health Check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    
    def test_mcp_tools_list(self):
        """Test MCP tools/list method"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        response = requests.post(f"{self.gateway_endpoint}/aws-api-mcp", 
                               headers=self.headers, json=payload)
        print(f"Tools List: {response.status_code} - {response.json()}")
        return response.status_code == 200
    
    def test_aws_command(self, command="aws sts get-caller-identity"):
        """Test AWS CLI command execution"""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "call_aws",
                "arguments": {"cli_command": command}
            }
        }
        response = requests.post(f"{self.gateway_endpoint}/aws-api-mcp", 
                               headers=self.headers, json=payload)
        print(f"AWS Command: {response.status_code} - {response.json()}")
        return response.status_code == 200

# Usage
tester = GatewayTester(
    gateway_endpoint="https://gateway-12345.agentcore.us-east-1.amazonaws.com",
    jwt_token="your-jwt-token"
)

# Run tests
print("=== Gateway Validation Tests ===")
tester.test_health()
tester.test_mcp_tools_list()
tester.test_aws_command()
```

## 5. Agent Integration Test

Test with your actual agent code:

```python
from bedrock_agent_core import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Configure gateway
app.configure_mcp_gateway({
    'gateway_endpoint': 'https://gateway-12345.agentcore.us-east-1.amazonaws.com',
    'targets': [{'name': 'aws-api-mcp', 'tools': ['call_aws']}]
})

@app.agent
def test_agent(query: str):
    try:
        # Test AWS command through gateway
        result = app.call_mcp_tool('aws-api-mcp', 'call_aws', {
            'cli_command': 'aws sts get-caller-identity'
        })
        return f"Gateway test successful: {result}"
    except Exception as e:
        return f"Gateway test failed: {str(e)}"

# Test the agent
response = test_agent("test gateway")
print(response)
```

## 6. Monitoring and Logs

### Check CloudWatch Logs:
```bash
# Gateway logs
aws logs describe-log-groups --log-group-name-prefix "/aws/bedrock/agentcore/gateway"

# MCP target logs
aws logs get-log-events \
  --log-group-name "/aws/bedrock/agentcore/gateway/aws-api-mcp" \
  --log-stream-name "latest"
```

### Check Metrics:
```bash
# Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace "AWS/BedrockAgentCore/Gateway" \
  --metric-name "RequestCount" \
  --dimensions Name=GatewayId,Value=gateway-12345 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Sum
```

## 7. Automated Test Suite

Create a comprehensive test suite:

```python
#!/usr/bin/env python3
"""
AgentCore Gateway Test Suite
Validates gateway configuration and MCP server integration
"""

import requests
import json
import time
import boto3
from typing import Dict, List, Tuple

class AgentCoreGatewayTestSuite:
    def __init__(self, gateway_endpoint: str, jwt_token: str):
        self.gateway_endpoint = gateway_endpoint
        self.jwt_token = jwt_token
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        self.test_results = []
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"Running: {test_name}")
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            self.test_results.append((test_name, status, None))
            print(f"  {status}")
            return result
        except Exception as e:
            self.test_results.append((test_name, "ERROR", str(e)))
            print(f"  ERROR: {str(e)}")
            return False
    
    def test_gateway_health(self) -> bool:
        """Test gateway health endpoint"""
        response = requests.get(f"{self.gateway_endpoint}/health", headers=self.headers)
        return response.status_code == 200
    
    def test_mcp_tools_list(self) -> bool:
        """Test MCP tools/list endpoint"""
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        response = requests.post(f"{self.gateway_endpoint}/aws-api-mcp", 
                               headers=self.headers, json=payload)
        if response.status_code != 200:
            return False
        data = response.json()
        return 'result' in data and 'tools' in data['result']
    
    def test_aws_identity(self) -> bool:
        """Test AWS identity command"""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "call_aws",
                "arguments": {"cli_command": "aws sts get-caller-identity"}
            }
        }
        response = requests.post(f"{self.gateway_endpoint}/aws-api-mcp", 
                               headers=self.headers, json=payload)
        return response.status_code == 200
    
    def test_aws_s3_list(self) -> bool:
        """Test AWS S3 list command"""
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "call_aws",
                "arguments": {"cli_command": "aws s3 ls"}
            }
        }
        response = requests.post(f"{self.gateway_endpoint}/aws-api-mcp", 
                               headers=self.headers, json=payload)
        return response.status_code == 200
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=== AgentCore Gateway Test Suite ===")
        print(f"Gateway: {self.gateway_endpoint}")
        print("=" * 50)
        
        tests = [
            ("Gateway Health Check", self.test_gateway_health),
            ("MCP Tools List", self.test_mcp_tools_list),
            ("AWS Identity Command", self.test_aws_identity),
            ("AWS S3 List Command", self.test_aws_s3_list),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            time.sleep(1)  # Rate limiting
        
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        errors = sum(1 for _, status, _ in self.test_results if status == "ERROR")
        
        for test_name, status, error in self.test_results:
            print(f"{status:>6}: {test_name}")
            if error:
                print(f"        Error: {error}")
        
        print(f"\nTotal: {len(self.test_results)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
        
        if passed == len(self.test_results):
            print("🎉 All tests passed! Gateway is working correctly.")
        else:
            print("❌ Some tests failed. Check configuration and logs.")

# Usage
if __name__ == "__main__":
    # Configure your gateway details
    GATEWAY_ENDPOINT = "https://gateway-12345.agentcore.us-east-1.amazonaws.com"
    JWT_TOKEN = "your-jwt-token-here"
    
    # Run test suite
    test_suite = AgentCoreGatewayTestSuite(GATEWAY_ENDPOINT, JWT_TOKEN)
    test_suite.run_all_tests()
```

## Expected Success Indicators:

✅ **Gateway Status**: Active/Running  
✅ **Health Checks**: All passing  
✅ **MCP Tools**: Listed correctly  
✅ **AWS Commands**: Execute successfully  
✅ **Authentication**: JWT tokens accepted  
✅ **Logs**: No error messages  
✅ **Metrics**: Request counts increasing  

## Troubleshooting Common Issues:

### 1. Authentication Errors (401/403)
- Verify JWT token is valid and not expired
- Check Cognito user pool configuration
- Ensure proper IAM permissions

### 2. Gateway Not Found (404)
- Verify gateway ID and endpoint URL
- Check gateway deployment status
- Confirm region settings

### 3. MCP Target Unhealthy
- Check MCP server deployment
- Verify health check endpoint
- Review CloudWatch logs

### 4. Tool Execution Failures
- Verify AWS credentials for MCP server
- Check IAM permissions for AWS operations
- Review command syntax and parameters

Run these tests in sequence to validate your gateway configuration is working correctly and troubleshoot any issues that arise.
