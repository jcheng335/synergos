import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)

# Initialize DynamoDB connection
def get_dynamodb_resource():
    """Get a configured DynamoDB resource"""
    # Load environment variables from env.txt if it exists
    if os.path.exists('env.txt'):
        with open('env.txt', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    return boto3.resource('dynamodb',
        region_name=os.environ.get('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )

dynamodb = get_dynamodb_resource()

# Cache for table references
_tables = {}

def get_table(table_name):
    """Get a DynamoDB table reference with caching"""
    if table_name not in _tables:
        _tables[table_name] = dynamodb.Table(table_name)
    return _tables[table_name]

# Competency operations
def get_competencies():
    """Get all competencies"""
    table = get_table('Competencies')
    response = table.scan()
    return response.get('Items', [])

def get_competency(competency_id):
    """Get a competency by ID"""
    table = get_table('Competencies')
    response = table.get_item(Key={'id': competency_id})
    return response.get('Item')

def get_competency_by_name(name):
    """Get a competency by name"""
    table = get_table('Competencies')
    response = table.query(
        IndexName='NameIndex',
        KeyConditionExpression=Key('name').eq(name)
    )
    items = response.get('Items', [])
    return items[0] if items else None

# Question operations
def get_questions_by_competency(competency_name, limit=2):
    """Get questions for a specific competency"""
    table = get_table('Questions')
    response = table.query(
        IndexName='CompetencyIndex',
        KeyConditionExpression=Key('competency_name').eq(competency_name),
        Limit=limit
    )
    return response.get('Items', [])

def get_all_preset_questions():
    """Get all preset questions"""
    table = get_table('Questions')
    response = table.scan(
        FilterExpression=Attr('is_active').eq(True)
    )
    return response.get('Items', [])

def update_question_feedback(question_id, feedback_value):
    """Update question feedback"""
    table = get_table('Questions')
    table.update_item(
        Key={'id': question_id},
        UpdateExpression="SET feedback_score = feedback_score + :val, popularity = popularity + :one",
        ExpressionAttributeValues={
            ':val': feedback_value,
            ':one': 1
        }
    )