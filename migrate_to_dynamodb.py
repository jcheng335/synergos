import boto3
import json
import os
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from env.txt if it exists
if os.path.exists('env.txt'):
    logger.info("Loading environment variables from env.txt")
    with open('env.txt', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Connect to DynamoDB
logger.info("Connecting to DynamoDB")
try:
    dynamodb = boto3.resource('dynamodb',
        region_name=os.environ.get('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    logger.info(f"Connected to DynamoDB in region {os.environ.get('AWS_REGION', 'us-east-1')}")
except Exception as e:
    logger.error(f"Failed to connect to DynamoDB: {str(e)}")
    exit(1)

# Create tables if they don't exist
def create_tables():
    logger.info("Creating DynamoDB tables if they don't exist")
    
    # Check if Competencies table exists
    existing_tables = [table.name for table in dynamodb.tables.all()]
    logger.info(f"Existing tables: {existing_tables}")
    
    if 'Competencies' not in existing_tables:
        logger.info("Creating Competencies table")
        competencies_table = dynamodb.create_table(
            TableName='Competencies',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'name', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'NameIndex',
                    'KeySchema': [
                        {'AttributeName': 'name', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        competencies_table.meta.client.get_waiter('table_exists').wait(TableName='Competencies')
        logger.info("Competencies table created")
    
    if 'Questions' not in existing_tables:
        logger.info("Creating Questions table")
        questions_table = dynamodb.create_table(
            TableName='Questions',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'competency_name', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'CompetencyIndex',
                    'KeySchema': [
                        {'AttributeName': 'competency_name', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        questions_table.meta.client.get_waiter('table_exists').wait(TableName='Questions')
        logger.info("Questions table created")

# Migrate competencies from JSON file
def migrate_data():
    logger.info("Starting data migration")
    
    competencies_table = dynamodb.Table('Competencies')
    questions_table = dynamodb.Table('Questions')
    
    # Check if competencies.json exists
    if not os.path.exists('competencies.json'):
        logger.error("competencies.json file not found")
        return
    
    # Load competencies from JSON file
    with open('competencies.json', 'r') as f:
        competency_data = json.load(f)
    
    logger.info(f"Loaded {len(competency_data)} competencies from file")
    
    # Process each competency
    for comp in competency_data:
        comp_id = str(uuid.uuid4())
        name = comp.get('name', '')
        description = comp.get('description', '')
        keywords = comp.get('keywords', [])
        
        # If no explicit keywords, extract some from the description
        if not keywords and description:
            # Extract potential keywords from description
            desc = description.lower()
            # Remove common words
            stop_words = ['the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are']
            import re
            words = re.findall(r'\b\w+\b', desc)
            keywords = list(set([w for w in words if len(w) > 3 and w not in stop_words]))
        
        # Add to DynamoDB
        logger.info(f"Adding competency: {name}")
        competencies_table.put_item(Item={
            'id': comp_id,
            'name': name,
            'description': description,
            'keywords': keywords,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        })
        
        # Create some basic questions for each competency
        if name:
            logger.info(f"Adding questions for competency: {name}")
            
            # First question
            questions_table.put_item(Item={
                'id': str(uuid.uuid4()),
                'question_text': f"Tell me about a time when you demonstrated {name}.",
                'competency_id': comp_id,
                'competency_name': name,
                'feedback_score': 0,
                'popularity': 0,
                'is_active': True,
                'competency_description': description,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })
            
            # Second question
            questions_table.put_item(Item={
                'id': str(uuid.uuid4()),
                'question_text': f"How have you applied {name} in your previous roles?",
                'competency_id': comp_id,
                'competency_name': name,
                'feedback_score': 0,
                'popularity': 0,
                'is_active': True,
                'competency_description': description,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })

# Main execution
if __name__ == "__main__":
    try:
        # Create the tables first
        create_tables()
        
        # Then migrate the data
        migrate_data()
        
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")