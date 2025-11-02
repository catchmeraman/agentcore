"""
Simple Filesystem MCP Server
"""
import os
import json
from bedrock_agentcore.mcp import MCPServer

server = MCPServer()

ALLOWED_PATHS = os.getenv('ALLOWED_PATHS', '/app/data').split(':')

def is_path_allowed(path):
    """Check if path is within allowed directories"""
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(allowed) for allowed in ALLOWED_PATHS)

@server.tool()
def read_file(file_path: str) -> str:
    """Read contents of a file"""
    if not is_path_allowed(file_path):
        return "Access denied: Path not allowed"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            return content[:2000]  # Limit content size
    except Exception as e:
        return f"Error reading file: {str(e)}"

@server.tool()
def list_directory(directory_path: str) -> str:
    """List contents of a directory"""
    if not is_path_allowed(directory_path):
        return "Access denied: Path not allowed"
    
    try:
        files = []
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
            })
        return json.dumps(files[:50])  # Limit to 50 items
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@server.tool()
def file_info(file_path: str) -> str:
    """Get information about a file"""
    if not is_path_allowed(file_path):
        return "Access denied: Path not allowed"
    
    try:
        stat = os.stat(file_path)
        info = {
            "path": file_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path)
        }
        return json.dumps(info)
    except Exception as e:
        return f"Error getting file info: {str(e)}"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)
