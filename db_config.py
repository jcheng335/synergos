import boto3
import os
from flask import g
from boto3.dynamodb.conditions import Key, Attr
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Configure DynamoDB
def get_db():
    """
    Establishes connection to DynamoDB and returns a cursor-like interface
    that mimics MySQL cursor behavior for backward compatibility.
    """
    if 'db' not in g:
        # Try to load from .env first, then fall back to env.txt
        if os.path.exists('.env'):
            load_dotenv('.env')
            logger.info("Loaded environment variables from .env")
        elif os.path.exists('env.txt'):
            with open('env.txt', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            logger.info("Loaded environment variables from env.txt")
        
        # Get AWS credentials from environment variables
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Create DynamoDB resource
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Create a cursor-like class for compatibility with MySQL code
        class DynamoDBCursor:
            def __init__(self, dynamodb):
                self.dynamodb = dynamodb
                self.dictionary = False
                self.results = []
                self.current_index = 0
                
            def cursor(self, dictionary=False):
                """Create a new cursor with dictionary flag set"""
                cursor = DynamoDBCursor(self.dynamodb)
                cursor.dictionary = dictionary
                return cursor
                
            def execute(self, query, params=None):
                """
                Mimic MySQL execute by interpreting the query and 
                performing equivalent DynamoDB operations
                """
                self.results = []
                self.current_index = 0
                
                # Handle queries for competency keywords
                if "SELECT k.keyword, c.name FROM competency_keywords k JOIN competencies c" in query:
                    # Get competency_keywords table
                    table = self.dynamodb.Table('competency_keywords')
                    response = table.scan()
                    items = response.get('Items', [])
                    
                    # Transform results to match expected structure
                    self.results = [
                        {'keyword': item.get('keyword', ''), 'name': item.get('competency_name', '')}
                        for item in items
                    ]
                    return len(self.results)
                
                # Handle queries for competency questions
                elif "SELECT q.id, q.question_text, c.name as competency_name FROM questions q JOIN competencies c" in query:
                    competency_name = params[0] if params else None
                    
                    # Get questions table
                    table = self.dynamodb.Table('questions')
                    
                    if competency_name:
                        # Query by competency name
                        response = table.scan(
                            FilterExpression='competency_name = :name',
                            ExpressionAttributeValues={':name': competency_name}
                        )
                    else:
                        # Get all questions
                        response = table.scan()
                        
                    items = response.get('Items', [])
                    
                    # Sort by popularity and feedback_score
                    items.sort(key=lambda x: (
                        float(x.get('popularity', 0)), 
                        float(x.get('feedback_score', 0))
                    ), reverse=True)
                    
                    # Limit to specified number if LIMIT clause exists
                    if " LIMIT " in query:
                        limit = int(query.split(" LIMIT ")[1].strip())
                        items = items[:limit]
                    
                    # Transform results
                    self.results = [
                        {
                            'id': item.get('id', ''),
                            'question_text': item.get('question_text', ''),
                            'competency_name': item.get('competency_name', '')
                        }
                        for item in items
                    ]
                    return len(self.results)
                
                # Handle other query types as needed
                # ...
                
                # Default case
                return 0
                
            def fetchall(self):
                """Return all results from the last query"""
                return self.results
                
            def fetchone(self):
                """Return the next result or None"""
                if self.current_index < len(self.results):
                    result = self.results[self.current_index]
                    self.current_index += 1
                    return result
                return None
                
            def close(self):
                """Close the cursor (no-op for DynamoDB)"""
                self.results = []
                self.current_index = 0
        
        # Create "db" object with cursor method
        class DynamoDBConnection:
            def __init__(self, dynamodb):
                self.dynamodb = dynamodb
                
            def cursor(self, dictionary=False):
                cursor = DynamoDBCursor(self.dynamodb)
                cursor.dictionary = dictionary
                return cursor
                
            def commit(self):
                """No-op for DynamoDB (changes are immediate)"""
                pass
                
            def close(self):
                """No-op for DynamoDB"""
                pass
        
        # Store in Flask's g object
        g.db = DynamoDBConnection(dynamodb)
    
    return g.db

def close_db(e=None):
    """
    Close database connection.
    Not strictly necessary for DynamoDB but kept for compatibility.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close() 