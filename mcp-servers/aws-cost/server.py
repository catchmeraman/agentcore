"""
AWS Cost MCP Server - Cost analysis and optimization
"""
from bedrock_agentcore.mcp import MCPServer
import boto3
import json
from datetime import datetime, timedelta

server = MCPServer()

@server.tool()
def get_monthly_costs(months: int = 3) -> str:
    """Get monthly costs for the last N months"""
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months * 30)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        costs = []
        for result in response['ResultsByTime']:
            period = result['TimePeriod']
            for group in result['Groups']:
                service = group['Keys'][0]
                amount = float(group['Metrics']['BlendedCost']['Amount'])
                if amount > 0:
                    costs.append({
                        'period': f"{period['Start']} to {period['End']}",
                        'service': service,
                        'cost': round(amount, 2)
                    })
        
        return json.dumps(costs, indent=2)
    except Exception as e:
        return f"Error getting monthly costs: {str(e)}"

@server.tool()
def get_cost_by_service(days: int = 30) -> str:
    """Get costs broken down by AWS service"""
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        service_costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                amount = float(group['Metrics']['BlendedCost']['Amount'])
                service_costs[service] = service_costs.get(service, 0) + amount
        
        # Sort by cost descending
        sorted_costs = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
        
        return json.dumps([{'service': k, 'total_cost': round(v, 2)} for k, v in sorted_costs if v > 0], indent=2)
    except Exception as e:
        return f"Error getting costs by service: {str(e)}"

@server.tool()
def get_rightsizing_recommendations() -> str:
    """Get EC2 rightsizing recommendations"""
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        response = ce.get_rightsizing_recommendation(
            Service='AmazonEC2',
            Configuration={
                'BenefitsConsidered': True,
                'RecommendationTarget': 'SAME_INSTANCE_FAMILY'
            }
        )
        
        recommendations = []
        for rec in response.get('RightsizingRecommendations', []):
            recommendations.append({
                'instance_id': rec.get('CurrentInstance', {}).get('ResourceId', 'Unknown'),
                'current_type': rec.get('CurrentInstance', {}).get('InstanceType', 'Unknown'),
                'recommended_type': rec.get('RightsizingType', 'Unknown'),
                'estimated_monthly_savings': rec.get('EstimatedMonthlySavings', {}).get('Amount', '0'),
                'cpu_utilization': rec.get('CurrentInstance', {}).get('ResourceUtilization', {}).get('EC2ResourceUtilization', {}).get('MaxCpuUtilizationPercentage', 'Unknown')
            })
        
        return json.dumps(recommendations, indent=2)
    except Exception as e:
        return f"Error getting rightsizing recommendations: {str(e)}"

@server.tool()
def get_savings_plans_recommendations() -> str:
    """Get Savings Plans purchase recommendations"""
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        response = ce.get_savings_plans_purchase_recommendation(
            SavingsPlansType='COMPUTE_SP',
            TermInYears='ONE_YEAR',
            PaymentOption='NO_UPFRONT',
            LookbackPeriodInDays='SIXTY_DAYS'
        )
        
        recommendations = []
        for rec in response.get('SavingsPlansDetails', []):
            recommendations.append({
                'hourly_commitment': rec.get('HourlyCommitment', 'Unknown'),
                'estimated_monthly_savings': rec.get('EstimatedMonthlySavings', 'Unknown'),
                'estimated_annual_savings': rec.get('EstimatedAnnualSavings', 'Unknown'),
                'upfront_cost': rec.get('UpfrontCost', 'Unknown'),
                'estimated_roi': rec.get('EstimatedROI', 'Unknown')
            })
        
        return json.dumps(recommendations, indent=2)
    except Exception as e:
        return f"Error getting Savings Plans recommendations: {str(e)}"

@server.tool()
def analyze_cost_anomalies(days: int = 7) -> str:
    """Detect cost anomalies in the last N days"""
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        response = ce.get_anomalies(
            DateInterval={
                'StartDate': start_date.strftime('%Y-%m-%d'),
                'EndDate': end_date.strftime('%Y-%m-%d')
            }
        )
        
        anomalies = []
        for anomaly in response.get('Anomalies', []):
            anomalies.append({
                'anomaly_id': anomaly.get('AnomalyId', 'Unknown'),
                'service': anomaly.get('DimensionKey', 'Unknown'),
                'impact': anomaly.get('Impact', {}).get('MaxImpact', 'Unknown'),
                'start_date': anomaly.get('AnomalyStartDate', 'Unknown'),
                'end_date': anomaly.get('AnomalyEndDate', 'Unknown'),
                'feedback': anomaly.get('Feedback', 'NONE')
            })
        
        return json.dumps(anomalies, indent=2)
    except Exception as e:
        return f"Error analyzing cost anomalies: {str(e)}"

@server.tool()
def get_budget_status() -> str:
    """Get current budget status and alerts"""
    try:
        budgets = boto3.client('budgets')
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        response = budgets.describe_budgets(AccountId=account_id)
        
        budget_status = []
        for budget in response.get('Budgets', []):
            budget_status.append({
                'name': budget.get('BudgetName', 'Unknown'),
                'limit': budget.get('BudgetLimit', {}).get('Amount', 'Unknown'),
                'unit': budget.get('BudgetLimit', {}).get('Unit', 'USD'),
                'type': budget.get('BudgetType', 'Unknown'),
                'time_period': budget.get('TimePeriod', {}),
                'calculated_spend': budget.get('CalculatedSpend', {})
            })
        
        return json.dumps(budget_status, indent=2)
    except Exception as e:
        return f"Error getting budget status: {str(e)}"

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8003)
