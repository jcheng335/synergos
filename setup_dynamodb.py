import boto3
import os
import json
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_env_vars():
    """Load environment variables from .env or env.txt"""
    # First try to load from .env (preferred)
    if os.path.exists('.env'):
        load_dotenv('.env')
        logger.info("Loading environment variables from .env")
    # Fall back to env.txt 
    elif os.path.exists('env.txt'):
        logger.info("Loading environment variables from env.txt")
        with open('env.txt', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        logger.warning(".env and env.txt not found. Make sure AWS credentials are set in environment variables")

def create_dynamodb_tables():
    """Create required DynamoDB tables if they don't exist"""
    # Load environment variables
    load_env_vars()
    
    # Get AWS credentials
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not aws_access_key_id or not aws_secret_access_key:
        logger.error("AWS credentials are not set in environment variables or env.txt")
        return False
    
    # Connect to DynamoDB
    logger.info(f"Connecting to DynamoDB in region {region_name}")
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    
    # Define tables to create
    tables_to_create = {
        'competencies': {
            'KeySchema': [
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'name', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'NameIndex',
                    'KeySchema': [
                        {'AttributeName': 'name', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        },
        'competency_keywords': {
            'KeySchema': [
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'keyword', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'KeywordIndex',
                    'KeySchema': [
                        {'AttributeName': 'keyword', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        },
        'questions': {
            'KeySchema': [
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'competency_name', 'AttributeType': 'S'}
            ],
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'CompetencyIndex',
                    'KeySchema': [
                        {'AttributeName': 'competency_name', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }
            ],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        }
    }
    
    # Create tables
    tables_created = []
    existing_tables = [table.name for table in dynamodb.tables.all()]
    logger.info(f"Existing tables: {existing_tables}")
    
    for table_name, table_definition in tables_to_create.items():
        if table_name in existing_tables:
            logger.info(f"Table {table_name} already exists")
            continue
        
        try:
            logger.info(f"Creating table: {table_name}")
            table = dynamodb.create_table(
                TableName=table_name,
                **table_definition
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            logger.info(f"Table {table_name} created successfully")
            tables_created.append(table_name)
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {str(e)}")
    
    return tables_created

def load_sample_data():
    """Load sample data into DynamoDB tables"""
    # Load environment variables
    load_env_vars()
    
    # Get AWS credentials
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Connect to DynamoDB
    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    
    # Load competencies
    competencies_table = dynamodb.Table('competencies')
    logger.info("Loading sample competencies")
    
    # Check if we have a competencies.json file
    if os.path.exists('competencies.json'):
        with open('competencies.json', 'r') as f:
            competencies_data = json.load(f)
            
        # Add each competency to the table
        for comp_id, comp_data in enumerate(competencies_data, 1):
            try:
                competencies_table.put_item(
                    Item={
                        'id': f"comp_{comp_id}",
                        'name': comp_data.get('name', f"Competency {comp_id}"),
                        'description': comp_data.get('description', '')
                    }
                )
                
                # Add keywords for this competency
                keywords_table = dynamodb.Table('competency_keywords')
                for kw_id, keyword in enumerate(comp_data.get('keywords', []), 1):
                    keywords_table.put_item(
                        Item={
                            'id': f"kw_{comp_id}_{kw_id}",
                            'keyword': keyword,
                            'competency_id': f"comp_{comp_id}",
                            'competency_name': comp_data.get('name', f"Competency {comp_id}")
                        }
                    )
                
                # Add sample questions for this competency
                questions_table = dynamodb.Table('questions')
                for q_id, question in enumerate(comp_data.get('questions', []), 1):
                    questions_table.put_item(
                        Item={
                            'id': f"q_{comp_id}_{q_id}",
                            'question_text': question,
                            'competency_id': f"comp_{comp_id}",
                            'competency_name': comp_data.get('name', f"Competency {comp_id}"),
                            'popularity': 1,
                            'feedback_score': 0,
                            'is_active': True
                        }
                    )
                
            except Exception as e:
                logger.error(f"Error adding competency {comp_id}: {str(e)}")
    else:
        # Add default sample data if no competencies.json exists
        sample_competencies = [
            {
                'id': 'comp_1',
                'name': 'Introduction',
                'description': 'Basic introductory questions'
            },
            {
                'id': 'comp_2',
                'name': 'Leadership',
                'description': 'Leadership and team management skills'
            },
            {
                'id': 'comp_3',
                'name': 'Problem Solving',
                'description': 'Analytical and problem solving abilities'
            }
        ]
        
        for comp in sample_competencies:
            try:
                competencies_table.put_item(Item=comp)
            except Exception as e:
                logger.error(f"Error adding sample competency {comp['id']}: {str(e)}")
        
        # Add sample questions
        questions_table = dynamodb.Table('questions')
        sample_questions = [
            {
                'id': 'q_1_1',
                'question_text': 'Tell me about yourself.',
                'competency_id': 'comp_1',
                'competency_name': 'Introduction',
                'popularity': 10,
                'feedback_score': 5,
                'is_active': True
            },
            {
                'id': 'q_1_2',
                'question_text': 'Why are you interested in this position?',
                'competency_id': 'comp_1',
                'competency_name': 'Introduction',
                'popularity': 8,
                'feedback_score': 4,
                'is_active': True
            },
            {
                'id': 'q_2_1',
                'question_text': 'Describe a time when you had to lead a team through a difficult situation.',
                'competency_id': 'comp_2',
                'competency_name': 'Leadership',
                'popularity': 7,
                'feedback_score': 4,
                'is_active': True
            },
            {
                'id': 'q_3_1',
                'question_text': 'Tell me about a complex problem you solved recently.',
                'competency_id': 'comp_3',
                'competency_name': 'Problem Solving',
                'popularity': 6,
                'feedback_score': 3,
                'is_active': True
            }
        ]
        
        for question in sample_questions:
            try:
                questions_table.put_item(Item=question)
            except Exception as e:
                logger.error(f"Error adding sample question {question['id']}: {str(e)}")
        
        # Add sample keywords
        keywords_table = dynamodb.Table('competency_keywords')
        sample_keywords = [
            {
                'id': 'kw_1_1',
                'keyword': 'experience',
                'competency_id': 'comp_1',
                'competency_name': 'Introduction'
            },
            {
                'id': 'kw_1_2',
                'keyword': 'background',
                'competency_id': 'comp_1',
                'competency_name': 'Introduction'
            },
            {
                'id': 'kw_2_1',
                'keyword': 'lead',
                'competency_id': 'comp_2',
                'competency_name': 'Leadership'
            },
            {
                'id': 'kw_2_2',
                'keyword': 'team',
                'competency_id': 'comp_2',
                'competency_name': 'Leadership'
            },
            {
                'id': 'kw_3_1',
                'keyword': 'solve',
                'competency_id': 'comp_3',
                'competency_name': 'Problem Solving'
            },
            {
                'id': 'kw_3_2',
                'keyword': 'analyze',
                'competency_id': 'comp_3',
                'competency_name': 'Problem Solving'
            }
        ]
        
        for keyword in sample_keywords:
            try:
                keywords_table.put_item(Item=keyword)
            except Exception as e:
                logger.error(f"Error adding sample keyword {keyword['id']}: {str(e)}")
    
    logger.info("Sample data loaded successfully")

if __name__ == "__main__":
    logger.info("Setting up DynamoDB tables")
    created_tables = create_dynamodb_tables()
    
    if created_tables:
        logger.info(f"Created tables: {created_tables}")
        load_sample_data()
    else:
        logger.info("No new tables created. Loading sample data...")
        load_sample_data()
    
    logger.info("Setup complete") 