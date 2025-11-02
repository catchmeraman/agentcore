"""
AWS Diagram MCP Server - Generate AWS architecture diagrams
"""
from bedrock_agentcore.mcp import MCPServer
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda, EC2
from diagrams.aws.storage import S3
from diagrams.aws.network import APIGateway, CloudFront
from diagrams.aws.database import RDS, Dynamodb
from diagrams.aws.security import IAM, Cognito
import json
import os

server = MCPServer()

@server.tool()
def create_aws_diagram(title: str, components: str, filename: str = None) -> str:
    """Create AWS architecture diagram from component list"""
    try:
        if not filename:
            filename = title.lower().replace(' ', '_')
        
        components_list = json.loads(components)
        
        with Diagram(title, show=False, filename=filename, direction="TB"):
            aws_components = {}
            
            for comp in components_list:
                comp_type = comp.get('type', '').lower()
                comp_name = comp.get('name', 'Component')
                
                if comp_type == 'lambda':
                    aws_components[comp_name] = Lambda(comp_name)
                elif comp_type == 'ec2':
                    aws_components[comp_name] = EC2(comp_name)
                elif comp_type == 's3':
                    aws_components[comp_name] = S3(comp_name)
                elif comp_type == 'apigateway':
                    aws_components[comp_name] = APIGateway(comp_name)
                elif comp_type == 'cloudfront':
                    aws_components[comp_name] = CloudFront(comp_name)
                elif comp_type == 'rds':
                    aws_components[comp_name] = RDS(comp_name)
                elif comp_type == 'dynamodb':
                    aws_components[comp_name] = Dynamodb(comp_name)
                elif comp_type == 'iam':
                    aws_components[comp_name] = IAM(comp_name)
                elif comp_type == 'cognito':
                    aws_components[comp_name] = Cognito(comp_name)
            
            # Create connections if specified
            for comp in components_list:
                if 'connects_to' in comp:
                    source = aws_components.get(comp['name'])
                    for target_name in comp['connects_to']:
                        target = aws_components.get(target_name)
                        if source and target:
                            source >> target
        
        return f"Diagram created: {filename}.png"
    except Exception as e:
        return f"Error creating diagram: {str(e)}"

@server.tool()
def list_aws_services() -> str:
    """List available AWS services for diagrams"""
    services = {
        "compute": ["lambda", "ec2", "ecs", "fargate"],
        "storage": ["s3", "ebs", "efs"],
        "database": ["rds", "dynamodb", "elasticache"],
        "network": ["apigateway", "cloudfront", "elb", "vpc"],
        "security": ["iam", "cognito", "kms"],
        "analytics": ["athena", "glue", "kinesis"],
        "ml": ["bedrock", "sagemaker", "comprehend"]
    }
    return json.dumps(services, indent=2)

@server.tool()
def create_serverless_diagram(app_name: str) -> str:
    """Create a standard serverless architecture diagram"""
    try:
        with Diagram(f"{app_name} Serverless Architecture", show=False, filename=f"{app_name}_serverless"):
            user = EC2("User")
            
            with Cluster("Frontend"):
                s3 = S3("Static Website")
                cdn = CloudFront("CDN")
            
            with Cluster("API Layer"):
                api = APIGateway("API Gateway")
                lambda_fn = Lambda("Lambda Function")
            
            with Cluster("Data Layer"):
                db = Dynamodb("DynamoDB")
            
            with Cluster("Security"):
                auth = Cognito("Authentication")
                iam = IAM("IAM Roles")
            
            # Connections
            user >> s3 >> cdn
            user >> api >> lambda_fn >> db
            api >> auth
            lambda_fn >> iam
        
        return f"Serverless diagram created: {app_name}_serverless.png"
    except Exception as e:
        return f"Error creating serverless diagram: {str(e)}"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)
