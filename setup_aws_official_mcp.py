"""
Setup official AWS MCP servers from https://github.com/awslabs/mcp
"""
import subprocess
import os
import json

def clone_aws_mcp_repo():
    """Clone the official AWS MCP repository"""
    if not os.path.exists('aws-mcp'):
        print("📥 Cloning official AWS MCP repository...")
        subprocess.run(['git', 'clone', 'https://github.com/awslabs/mcp.git', 'aws-mcp'], check=True)
    else:
        print("📁 AWS MCP repository already exists")

def setup_mcp_server(server_name, port):
    """Setup individual MCP server"""
    server_path = f"aws-mcp/{server_name}"
    
    if not os.path.exists(server_path):
        print(f"❌ Server {server_name} not found in repository")
        return False
    
    print(f"🔧 Setting up {server_name} on port {port}...")
    
    # Install dependencies
    if os.path.exists(f"{server_path}/requirements.txt"):
        subprocess.run(['pip', 'install', '-r', f"{server_path}/requirements.txt"], check=True)
    elif os.path.exists(f"{server_path}/package.json"):
        subprocess.run(['npm', 'install'], cwd=server_path, check=True)
    
    return True

def main():
    """Setup all official AWS MCP servers"""
    
    # Clone repository
    clone_aws_mcp_repo()
    
    # List available servers
    aws_mcp_path = 'aws-mcp'
    if os.path.exists(aws_mcp_path):
        servers = [d for d in os.listdir(aws_mcp_path) 
                  if os.path.isdir(os.path.join(aws_mcp_path, d)) and not d.startswith('.')]
        
        print(f"📋 Available AWS MCP servers: {servers}")
        
        # Setup each server
        port = 8000
        server_config = {}
        
        for server in servers:
            if setup_mcp_server(server, port):
                server_config[server] = {
                    "path": f"aws-mcp/{server}",
                    "port": port,
                    "url": f"http://localhost:{port}"
                }
                port += 1
        
        # Save configuration
        with open('aws_mcp_config.json', 'w') as f:
            json.dump(server_config, f, indent=2)
        
        print("✅ AWS MCP servers setup complete!")
        print(f"📄 Configuration saved to aws_mcp_config.json")
        
        return server_config
    
    return {}

if __name__ == "__main__":
    main()
