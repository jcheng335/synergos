import json
import boto3
import os
import sys
import uuid
from decimal import Decimal

# --- Configuration ---
JSON_FILE_PATH = 'c:/Users/jchen/Downloads/competenciesmap.txt' # Path to your JSON data
COMPETENCIES_TABLE_NAME = 'competencies'
QUESTIONS_TABLE_NAME = 'questions'
REGION_NAME = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
DELETE_EXISTING_DATA = True # SET TO False IF YOU DON'T WANT TO WIPE TABLES
# ---------------------

def clear_table(table):
    """Deletes all items from a DynamoDB table object."""
    table_name = table.name # Get table name from table object
    print(f"Attempting to clear table: {table_name}")
    try:
        # Use scan with pagination to get all keys
        scan_kwargs = {
            'ProjectionExpression': "id" # Assuming 'id' is the primary key
        }
        done = False
        start_key = None
        items_to_delete = []
        while not done:
            if start_key:
                scan_kwargs['ExclusiveStartKey'] = start_key
            response = table.scan(**scan_kwargs)
            items_to_delete.extend(response.get('Items', []))
            start_key = response.get('LastEvaluatedKey', None)
            done = start_key is None

        # Use batch_writer on the table object to delete items
        if items_to_delete:
            with table.batch_writer() as batch:
                for item in items_to_delete:
                    batch.delete_item(Key={'id': item['id']})
            print(f"Successfully cleared {len(items_to_delete)} items from table: {table_name}")
        else:
             print(f"Table {table_name} is already empty.")

    except Exception as e:
        print(f"Error clearing table {table_name}: {e}", file=sys.stderr)
        # Decide if you want to exit or continue if clearing fails
        # sys.exit(1)

def populate_data():
    """Reads JSON and populates DynamoDB tables."""
    # --- Load JSON Data ---
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'competencies' not in data:
            print(f"Error: JSON file {JSON_FILE_PATH} must have a top-level 'competencies' key containing a list.", file=sys.stderr)
            sys.exit(1)
        competencies_data = data['competencies']
        print(f"Successfully loaded {len(competencies_data)} competencies from {JSON_FILE_PATH}")
    except FileNotFoundError:
        print(f"Error: JSON file not found at {JSON_FILE_PATH}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {JSON_FILE_PATH}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred reading the JSON file: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Initialize DynamoDB Client ---
    try:
        # Use credentials from environment variables, IAM role, or config file
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        if not aws_access_key_id or not aws_secret_access_key:
            print("Warning: AWS credentials not found in environment variables. Ensure they are configured elsewhere (e.g., IAM role, ~/.aws/credentials).")
            # Depending on your setup, you might not need explicit keys if using IAM roles
            # For local development with specific keys:
            # session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=REGION_NAME)
            # dynamodb = session.resource('dynamodb')
            # For default credential chain (recommended for production/EC2/ECS):
            dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
        else:
             dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=REGION_NAME
            )

        competencies_table = dynamodb.Table(COMPETENCIES_TABLE_NAME)
        questions_table = dynamodb.Table(QUESTIONS_TABLE_NAME)
        # Test connection by describing one table
        competencies_table.load()
        print("DynamoDB connection successful.")
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}", file=sys.stderr)
        print("Please ensure AWS credentials are configured correctly and the tables exist.", file=sys.stderr)
        sys.exit(1)

    # --- Clear Existing Data (Optional) ---
    if DELETE_EXISTING_DATA:
        print("\n--- Deleting Existing Data ---")
        # Pass the table objects to clear_table
        clear_table(questions_table) 
        clear_table(competencies_table)
        print("--- Finished Deleting Data ---\n")
    else:
        print("\nSkipping deletion of existing data.\n")

    # --- Populate Tables ---
    print("--- Populating Tables ---")
    competency_count = 0
    question_count = 0

    try:
        with competencies_table.batch_writer() as comp_batch, questions_table.batch_writer() as ques_batch:
            for comp_data in competencies_data:
                competency_id = str(uuid.uuid4())
                competency_name = comp_data.get('name')
                if not competency_name:
                    print(f"Skipping competency due to missing name: {comp_data}")
                    continue

                print(f"Processing competency: {competency_name}")

                # Prepare competency item
                comp_item = {
                    'id': competency_id,
                    'name': competency_name,
                    'description': comp_data.get('description', ''),
                    # Use category for leadership flag
                    'category': 'Leadership' if comp_data.get('is_leadership_competency', False) else 'Standard'
                    # Add other fields if your model has them and they have defaults or are needed
                }
                comp_batch.put_item(Item=comp_item)
                competency_count += 1

                # Prepare question items
                preset_questions = comp_data.get('interview_questions', [])
                if len(preset_questions) >= 1:
                    q1_item = {
                        'id': str(uuid.uuid4()),
                        'question_text': preset_questions[0],
                        'competency_id': competency_id,
                        'competency_name': competency_name, # Denormalize for easier querying
                        'preset_order': 1,
                        'question_type': 'Preset Behavioral',
                        'popularity': 0, # Default value
                        'feedback_score': Decimal('0.0') # Use Decimal for DynamoDB numbers
                    }
                    ques_batch.put_item(Item=q1_item)
                    question_count += 1
                    print(f"  Added Question 1: {preset_questions[0][:50]}...")

                if len(preset_questions) >= 2:
                    q2_item = {
                        'id': str(uuid.uuid4()),
                        'question_text': preset_questions[1],
                        'competency_id': competency_id,
                        'competency_name': competency_name, # Denormalize
                        'preset_order': 2,
                        'question_type': 'Preset Behavioral',
                        'popularity': 0,
                        'feedback_score': Decimal('0.0')
                    }
                    ques_batch.put_item(Item=q2_item)
                    question_count += 1
                    print(f"  Added Question 2: {preset_questions[1][:50]}...")

        print("\n--- Population Complete ---")
        print(f"Successfully added {competency_count} competencies.")
        print(f"Successfully added {question_count} preset questions.")

    except Exception as e:
        print(f"An error occurred during batch writing: {e}", file=sys.stderr)
        print("Data population may be incomplete.", file=sys.stderr)
        # Consider adding cleanup logic here if needed

if __name__ == "__main__":
    print("Starting database population script...")
    # Add confirmation step before deleting data
    if DELETE_EXISTING_DATA:
        confirm = input(f"WARNING: This script is set to DELETE ALL DATA from tables '{COMPETENCIES_TABLE_NAME}' and '{QUESTIONS_TABLE_NAME}'.\nType 'YES' to confirm: ")
        if confirm != 'YES':
            print("Aborted. Data deletion not confirmed.")
            sys.exit(0)
    populate_data()
    print("Script finished.") 