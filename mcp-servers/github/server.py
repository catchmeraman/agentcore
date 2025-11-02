"""
GitHub MCP Server - GitHub repository and operations management
"""
from bedrock_agentcore.mcp import MCPServer
import requests
import json
import os
import base64

server = MCPServer()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_BASE = 'https://api.github.com'

def get_headers():
    """Get GitHub API headers"""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    return headers

@server.tool()
def list_repositories(username: str, type: str = "owner") -> str:
    """List repositories for a user or organization"""
    try:
        url = f"{GITHUB_API_BASE}/users/{username}/repos"
        params = {'type': type, 'sort': 'updated', 'per_page': 20}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        repos = []
        for repo in response.json():
            repos.append({
                'name': repo['name'],
                'full_name': repo['full_name'],
                'description': repo['description'],
                'language': repo['language'],
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'updated_at': repo['updated_at'],
                'html_url': repo['html_url']
            })
        
        return json.dumps(repos, indent=2)
    except Exception as e:
        return f"Error listing repositories: {str(e)}"

@server.tool()
def get_repository_info(owner: str, repo: str) -> str:
    """Get detailed information about a repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        
        repo_data = response.json()
        info = {
            'name': repo_data['name'],
            'full_name': repo_data['full_name'],
            'description': repo_data['description'],
            'language': repo_data['language'],
            'size': repo_data['size'],
            'stars': repo_data['stargazers_count'],
            'forks': repo_data['forks_count'],
            'open_issues': repo_data['open_issues_count'],
            'created_at': repo_data['created_at'],
            'updated_at': repo_data['updated_at'],
            'clone_url': repo_data['clone_url'],
            'topics': repo_data.get('topics', [])
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting repository info: {str(e)}"

@server.tool()
def list_commits(owner: str, repo: str, limit: int = 10) -> str:
    """List recent commits for a repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
        params = {'per_page': limit}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        commits = []
        for commit in response.json():
            commits.append({
                'sha': commit['sha'][:8],
                'message': commit['commit']['message'].split('\n')[0],
                'author': commit['commit']['author']['name'],
                'date': commit['commit']['author']['date'],
                'url': commit['html_url']
            })
        
        return json.dumps(commits, indent=2)
    except Exception as e:
        return f"Error listing commits: {str(e)}"

@server.tool()
def list_issues(owner: str, repo: str, state: str = "open", limit: int = 10) -> str:
    """List issues for a repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
        params = {'state': state, 'per_page': limit}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        issues = []
        for issue in response.json():
            if 'pull_request' not in issue:  # Exclude pull requests
                issues.append({
                    'number': issue['number'],
                    'title': issue['title'],
                    'state': issue['state'],
                    'author': issue['user']['login'],
                    'created_at': issue['created_at'],
                    'labels': [label['name'] for label in issue['labels']],
                    'html_url': issue['html_url']
                })
        
        return json.dumps(issues, indent=2)
    except Exception as e:
        return f"Error listing issues: {str(e)}"

@server.tool()
def list_pull_requests(owner: str, repo: str, state: str = "open", limit: int = 10) -> str:
    """List pull requests for a repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
        params = {'state': state, 'per_page': limit}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        prs = []
        for pr in response.json():
            prs.append({
                'number': pr['number'],
                'title': pr['title'],
                'state': pr['state'],
                'author': pr['user']['login'],
                'created_at': pr['created_at'],
                'head_branch': pr['head']['ref'],
                'base_branch': pr['base']['ref'],
                'html_url': pr['html_url']
            })
        
        return json.dumps(prs, indent=2)
    except Exception as e:
        return f"Error listing pull requests: {str(e)}"

@server.tool()
def get_file_content(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """Get content of a file from repository"""
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        params = {'ref': branch}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        file_data = response.json()
        
        if file_data['type'] == 'file':
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return f"File: {path}\nSize: {file_data['size']} bytes\n\nContent:\n{content[:2000]}{'...' if len(content) > 2000 else ''}"
        else:
            return f"Path {path} is not a file"
    except Exception as e:
        return f"Error getting file content: {str(e)}"

@server.tool()
def search_repositories(query: str, sort: str = "stars", limit: int = 10) -> str:
    """Search GitHub repositories"""
    try:
        url = f"{GITHUB_API_BASE}/search/repositories"
        params = {'q': query, 'sort': sort, 'per_page': limit}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        results = []
        for repo in response.json()['items']:
            results.append({
                'name': repo['name'],
                'full_name': repo['full_name'],
                'description': repo['description'],
                'language': repo['language'],
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'html_url': repo['html_url']
            })
        
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching repositories: {str(e)}"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8004)
