"""
AWS EKS MCP Server - Manage EKS clusters and operations
"""
from bedrock_agentcore.mcp import MCPServer
import boto3
import json
import subprocess

server = MCPServer()

@server.tool()
def list_eks_clusters(region: str = "us-west-2") -> str:
    """List all EKS clusters in a region"""
    try:
        eks = boto3.client('eks', region_name=region)
        response = eks.list_clusters()
        
        clusters = []
        for cluster_name in response['clusters']:
            cluster_info = eks.describe_cluster(name=cluster_name)
            clusters.append({
                'name': cluster_name,
                'status': cluster_info['cluster']['status'],
                'version': cluster_info['cluster']['version'],
                'endpoint': cluster_info['cluster']['endpoint']
            })
        
        return json.dumps(clusters, indent=2)
    except Exception as e:
        return f"Error listing EKS clusters: {str(e)}"

@server.tool()
def get_cluster_info(cluster_name: str, region: str = "us-west-2") -> str:
    """Get detailed information about an EKS cluster"""
    try:
        eks = boto3.client('eks', region_name=region)
        response = eks.describe_cluster(name=cluster_name)
        cluster = response['cluster']
        
        info = {
            'name': cluster['name'],
            'status': cluster['status'],
            'version': cluster['version'],
            'endpoint': cluster['endpoint'],
            'platform_version': cluster['platformVersion'],
            'role_arn': cluster['roleArn'],
            'vpc_config': cluster['resourcesVpcConfig'],
            'logging': cluster.get('logging', {}),
            'created_at': cluster['createdAt'].isoformat()
        }
        
        return json.dumps(info, indent=2, default=str)
    except Exception as e:
        return f"Error getting cluster info: {str(e)}"

@server.tool()
def list_nodegroups(cluster_name: str, region: str = "us-west-2") -> str:
    """List node groups for an EKS cluster"""
    try:
        eks = boto3.client('eks', region_name=region)
        response = eks.list_nodegroups(clusterName=cluster_name)
        
        nodegroups = []
        for ng_name in response['nodegroups']:
            ng_info = eks.describe_nodegroup(clusterName=cluster_name, nodegroupName=ng_name)
            nodegroups.append({
                'name': ng_name,
                'status': ng_info['nodegroup']['status'],
                'instance_types': ng_info['nodegroup']['instanceTypes'],
                'scaling_config': ng_info['nodegroup']['scalingConfig'],
                'health': ng_info['nodegroup']['health']
            })
        
        return json.dumps(nodegroups, indent=2)
    except Exception as e:
        return f"Error listing node groups: {str(e)}"

@server.tool()
def get_cluster_pods(cluster_name: str, namespace: str = "default") -> str:
    """Get pods in an EKS cluster (requires kubectl access)"""
    try:
        # Update kubeconfig
        subprocess.run(['aws', 'eks', 'update-kubeconfig', '--name', cluster_name], 
                      capture_output=True, check=True)
        
        # Get pods
        result = subprocess.run(['kubectl', 'get', 'pods', '-n', namespace, '-o', 'json'], 
                               capture_output=True, text=True, check=True)
        
        pods_data = json.loads(result.stdout)
        pods = []
        
        for pod in pods_data['items']:
            pods.append({
                'name': pod['metadata']['name'],
                'namespace': pod['metadata']['namespace'],
                'status': pod['status']['phase'],
                'node': pod['spec'].get('nodeName', 'Unknown'),
                'created': pod['metadata']['creationTimestamp']
            })
        
        return json.dumps(pods, indent=2)
    except Exception as e:
        return f"Error getting pods: {str(e)}"

@server.tool()
def generate_eks_manifest(app_name: str, image: str, replicas: int = 2) -> str:
    """Generate Kubernetes deployment manifest"""
    manifest = {
        'apiVersion': 'apps/v1',
        'kind': 'Deployment',
        'metadata': {
            'name': app_name,
            'labels': {'app': app_name}
        },
        'spec': {
            'replicas': replicas,
            'selector': {'matchLabels': {'app': app_name}},
            'template': {
                'metadata': {'labels': {'app': app_name}},
                'spec': {
                    'containers': [{
                        'name': app_name,
                        'image': image,
                        'ports': [{'containerPort': 80}],
                        'resources': {
                            'requests': {'cpu': '100m', 'memory': '128Mi'},
                            'limits': {'cpu': '500m', 'memory': '512Mi'}
                        }
                    }]
                }
            }
        }
    }
    
    service = {
        'apiVersion': 'v1',
        'kind': 'Service',
        'metadata': {'name': f"{app_name}-service"},
        'spec': {
            'selector': {'app': app_name},
            'ports': [{'port': 80, 'targetPort': 80}],
            'type': 'LoadBalancer'
        }
    }
    
    return f"# Deployment\n{json.dumps(manifest, indent=2)}\n---\n# Service\n{json.dumps(service, indent=2)}"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8001)
