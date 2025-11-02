"""
Lambda function to integrate AgentCore with API Gateway for frontend
"""
import json
import boto3
import os

def lambda_handler(event, context):
    """Handle API Gateway requests to AgentCore"""
    
    # Parse request
    body = json.loads(event.get('body', '{}'))
    prompt = body.get('prompt', '')
    
    # Call AgentCore Runtime
    agentcore_client = boto3.client('bedrock-agentcore-runtime')
    
    try:
        response = agentcore_client.invoke_agent(
            agentArn=os.environ['AGENT_ARN'],
            sessionId=event.get('requestContext', {}).get('requestId', 'default'),
            inputText=prompt
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'response': response.get('output', {}).get('text', 'No response')
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
