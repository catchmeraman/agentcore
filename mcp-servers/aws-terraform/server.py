"""
AWS Terraform MCP Server - Generate and manage Terraform configurations
"""
from bedrock_agentcore.mcp import MCPServer
import json
import subprocess
import os

server = MCPServer()

@server.tool()
def generate_terraform_s3(bucket_name: str, versioning: bool = True) -> str:
    """Generate Terraform configuration for S3 bucket"""
    config = f'''resource "aws_s3_bucket" "{bucket_name.replace('-', '_')}" {{
  bucket = "{bucket_name}"
}}

resource "aws_s3_bucket_versioning" "{bucket_name.replace('-', '_')}_versioning" {{
  bucket = aws_s3_bucket.{bucket_name.replace('-', '_')}.id
  versioning_configuration {{
    status = "{'Enabled' if versioning else 'Disabled'}"
  }}
}}

resource "aws_s3_bucket_server_side_encryption_configuration" "{bucket_name.replace('-', '_')}_encryption" {{
  bucket = aws_s3_bucket.{bucket_name.replace('-', '_')}.id

  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}'''
    return config

@server.tool()
def generate_terraform_lambda(function_name: str, runtime: str = "python3.9") -> str:
    """Generate Terraform configuration for Lambda function"""
    config = f'''resource "aws_iam_role" "{function_name}_role" {{
  name = "{function_name}-role"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "lambda.amazonaws.com"
        }}
      }}
    ]
  }})
}}

resource "aws_iam_role_policy_attachment" "{function_name}_basic" {{
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.{function_name}_role.name
}}

resource "aws_lambda_function" "{function_name}" {{
  filename         = "{function_name}.zip"
  function_name    = "{function_name}"
  role            = aws_iam_role.{function_name}_role.arn
  handler         = "index.handler"
  runtime         = "{runtime}"
  timeout         = 30

  source_code_hash = filebase64sha256("{function_name}.zip")
}}'''
    return config

@server.tool()
def generate_terraform_vpc(vpc_name: str, cidr_block: str = "10.0.0.0/16") -> str:
    """Generate Terraform configuration for VPC with subnets"""
    config = f'''resource "aws_vpc" "{vpc_name}" {{
  cidr_block           = "{cidr_block}"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name = "{vpc_name}"
  }}
}}

resource "aws_internet_gateway" "{vpc_name}_igw" {{
  vpc_id = aws_vpc.{vpc_name}.id

  tags = {{
    Name = "{vpc_name}-igw"
  }}
}}

resource "aws_subnet" "{vpc_name}_public_1" {{
  vpc_id                  = aws_vpc.{vpc_name}.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {{
    Name = "{vpc_name}-public-1"
  }}
}}

resource "aws_subnet" "{vpc_name}_private_1" {{
  vpc_id            = aws_vpc.{vpc_name}.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {{
    Name = "{vpc_name}-private-1"
  }}
}}

data "aws_availability_zones" "available" {{
  state = "available"
}}'''
    return config

@server.tool()
def generate_terraform_eks(cluster_name: str, node_group_name: str = None) -> str:
    """Generate Terraform configuration for EKS cluster"""
    if not node_group_name:
        node_group_name = f"{cluster_name}-nodes"
    
    config = f'''resource "aws_eks_cluster" "{cluster_name}" {{
  name     = "{cluster_name}"
  role_arn = aws_iam_role.{cluster_name}_cluster_role.arn
  version  = "1.27"

  vpc_config {{
    subnet_ids = [
      aws_subnet.{cluster_name}_private_1.id,
      aws_subnet.{cluster_name}_private_2.id,
      aws_subnet.{cluster_name}_public_1.id,
      aws_subnet.{cluster_name}_public_2.id
    ]
  }}

  depends_on = [
    aws_iam_role_policy_attachment.{cluster_name}_cluster_policy,
    aws_iam_role_policy_attachment.{cluster_name}_service_policy,
  ]
}}

resource "aws_eks_node_group" "{node_group_name}" {{
  cluster_name    = aws_eks_cluster.{cluster_name}.name
  node_group_name = "{node_group_name}"
  node_role_arn   = aws_iam_role.{cluster_name}_node_role.arn
  subnet_ids      = [aws_subnet.{cluster_name}_private_1.id, aws_subnet.{cluster_name}_private_2.id]

  scaling_config {{
    desired_size = 2
    max_size     = 4
    min_size     = 1
  }}

  instance_types = ["t3.medium"]

  depends_on = [
    aws_iam_role_policy_attachment.{cluster_name}_worker_policy,
    aws_iam_role_policy_attachment.{cluster_name}_cni_policy,
    aws_iam_role_policy_attachment.{cluster_name}_registry_policy,
  ]
}}

# IAM roles and policies would be included here...'''
    return config

@server.tool()
def validate_terraform(directory: str) -> str:
    """Validate Terraform configuration"""
    try:
        result = subprocess.run(['terraform', 'validate'], 
                               cwd=directory, capture_output=True, text=True)
        
        if result.returncode == 0:
            return "✅ Terraform configuration is valid"
        else:
            return f"❌ Terraform validation failed:\n{result.stderr}"
    except Exception as e:
        return f"Error validating Terraform: {str(e)}"

@server.tool()
def terraform_plan(directory: str) -> str:
    """Run terraform plan and return output"""
    try:
        # Initialize if needed
        subprocess.run(['terraform', 'init'], cwd=directory, capture_output=True)
        
        # Run plan
        result = subprocess.run(['terraform', 'plan'], 
                               cwd=directory, capture_output=True, text=True)
        
        return f"Terraform Plan Output:\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"Error running terraform plan: {str(e)}"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8002)
