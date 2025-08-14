# Function to analyze responsibilities and tag with competencies
def analyze_job_responsibilities(responsibilities):
    """
    Analyze job responsibilities and tag them with relevant competencies using AI.
    Uses LLM to analyze each responsibility and determine the appropriate competency tag.
    Ensures each responsibility has 1-5 tags.
    """
    if not responsibilities or not isinstance(responsibilities, list):
        return {
            "tagged_responsibilities": [],
            "top_competencies": []
        }
    
    # Track competency counts
    competency_counts = Counter()
    tagged_responsibilities = []
    
    # Fetch standard competencies from DynamoDB
    try:
        # Get AWS credentials
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Create DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Get competencies table
        competencies_table = dynamodb.Table('competencies')
        
        # Scan all competencies
        response = competencies_table.scan()
        competencies_data = response.get('Items', [])
        
        # Create a list of standard competency names and a dictionary of descriptions
        standard_competency_names = []
        standard_competencies_details = {}
        
        for comp in competencies_data:
            name = comp.get('name', '')
            description = comp.get('description', '')
            if name:
                standard_competency_names.append(name)
                standard_competencies_details[name] = description
        
        # If no competencies found, use reasonable defaults
        if not standard_competency_names:
            logger.warning("No competencies found in database, using default set for analysis")
            standard_competency_names = [
                "Action Oriented", "Balances Stakeholders", "Being Resilient", "Builds Effective Teams",
                "Builds Networks", "Business Insight", "Collaborates", "Communicates Effectively",
                "Courage", "Customer Focus", "Decision Quality", "Develops Talent",
                "Directs Work", "Drives Engagement", "Drives Results", "Drives Vision and Purpose",
                "Financial Acumen", "Global Perspective", "Instills Trust", "Interpersonal Savvy",
                "Manages Ambiguity", "Manages Complexity", "Manages Conflict", "Nimble Learning",
                "Optimizes Work Processes", "Persuades", "Plans and Aligns", "Political Savvy",
                "Resourcefulness", "Self-Development", "Situational Adaptability", "Strategic Mindset",
                "Tech Savvy", "Values Differences"
            ]
    except Exception as e:
        logger.error(f"Error fetching competencies from DynamoDB: {str(e)}")
        # Use default competencies if database retrieval fails
        standard_competency_names = [
            "Action Oriented", "Balances Stakeholders", "Being Resilient", "Builds Effective Teams",
            "Builds Networks", "Business Insight", "Collaborates", "Communicates Effectively",
            "Courage", "Customer Focus", "Decision Quality", "Develops Talent",
            "Directs Work", "Drives Engagement", "Drives Results", "Drives Vision and Purpose",
            "Financial Acumen", "Global Perspective", "Instills Trust", "Interpersonal Savvy",
            "Manages Ambiguity", "Manages Complexity", "Manages Conflict", "Nimble Learning",
            "Optimizes Work Processes", "Persuades", "Plans and Aligns", "Political Savvy",
            "Resourcefulness", "Self-Development", "Situational Adaptability", "Strategic Mindset",
            "Tech Savvy", "Values Differences"
        ]
        standard_competencies_details = {}
    
    # Prepare the competency list for the LLM prompt
    competency_list_for_prompt = ", ".join(sorted(standard_competency_names))
    competency_details_for_prompt = ""
    for name in sorted(standard_competency_names):
        description = standard_competencies_details.get(name, "")
        if description:
            competency_details_for_prompt += f"\n- {name}: {description}"
        else:
            competency_details_for_prompt += f"\n- {name}"
    
    # Call LLM to analyze each responsibility
    for responsibility in responsibilities:
        if not responsibility or not isinstance(responsibility, str):
            continue
            
        # Call OpenAI to determine the competency for this responsibility
        try:
            # Prepare prompt for competency analysis
            if USE_NEW_OPENAI_SDK:
                response = client.chat.completions.create(
                    model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": f"""
                        You are a job analysis expert. Your task is to analyze a job responsibility and identify 
                        the most relevant competencies it relates to. You MUST ONLY choose from the following 
                        specific competencies:
                        {competency_details_for_prompt}
                        
                        Return your analysis as a JSON array with the competency names (using the exact names as listed).
                        You MUST return between 1-5 most relevant competencies - at least 1, but no more than 5.
                        
                        Example output format:
                        ["Decision Quality", "Strategic Mindset", "Business Insight"]
                        """},
                        {"role": "user", "content": f"Analyze this job responsibility and identify the competencies: '{responsibility}'"}
                    ],
                    temperature=0.3,
                    max_tokens=150
                )
                response_content = response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": f"""
                        You are a job analysis expert. Your task is to analyze a job responsibility and identify 
                        the most relevant competencies it relates to. You MUST ONLY choose from the following 
                        specific competencies:
                        {competency_details_for_prompt}
                        
                        Return your analysis as a JSON array with the competency names (using the exact names as listed).
                        You MUST return between 1-5 most relevant competencies - at least 1, but no more than 5.
                        
                        Example output format:
                        ["Decision Quality", "Strategic Mindset", "Business Insight"]
                        """},
                        {"role": "user", "content": f"Analyze this job responsibility and identify the competencies: '{responsibility}'"}
                    ],
                    temperature=0.3,
                    max_tokens=150
                )
                response_content = response.choices[0].message['content']
            
            # Parse response to extract competencies
            try:
                # Find JSON array in response content
                array_match = re.search(r'(\[.*\])', response_content, re.DOTALL)
                if array_match:
                    json_str = array_match.group(1)
                    competencies = json.loads(json_str)
                else:
                    competencies = json.loads(response_content)
                    
                # Format competencies and update counts
                if isinstance(competencies, list) and competencies:
                    # Filter out any competencies not in our standard list
                    filtered_competencies = [comp for comp in competencies if comp in standard_competency_names]
                    
                    # If no valid competencies remain after filtering, use a default
                    if not filtered_competencies:
                        filtered_competencies = ["Business Insight"]  # A reasonable default
                    
                    # Add each competency to the counts
                    for comp in filtered_competencies:
                        competency_counts[comp] += 1
                    
                    # Ensure we have at least 1 and at most 5 competencies
                    if len(filtered_competencies) > 5:
                        filtered_competencies = filtered_competencies[:5]
                    
                    # Add to tagged responsibilities
                    tagged_responsibilities.append({
                        "responsibility": responsibility,
                        "tags": filtered_competencies
                    })
                else:
                    # Default if parsing issue
                    logger.warning(f"Couldn't parse competencies from LLM response for: {responsibility[:30]}...")
                    tagged_responsibilities.append({
                        "responsibility": responsibility,
                        "tags": ["Business Insight"] # A reasonable default
                    })
                    competency_counts["Business Insight"] += 1
            except json.JSONDecodeError:
                # Handle parsing errors
                logger.warning(f"JSON parsing error for competency analysis of: {responsibility[:30]}...")
                tagged_responsibilities.append({
                    "responsibility": responsibility,
                    "tags": ["Business Insight"] # A reasonable default
                })
                competency_counts["Business Insight"] += 1
        except Exception as e:
            logger.error(f"Error analyzing competency for responsibility: {str(e)}")
            tagged_responsibilities.append({
                "responsibility": responsibility,
                "tags": ["Business Insight"] # A reasonable default
            })
            competency_counts["Business Insight"] += 1
    
    # Get top 5 competencies
    top_competencies = [comp for comp, _ in competency_counts.most_common(5)]
    
    return {
        "tagged_responsibilities": tagged_responsibilities,
        "top_competencies": top_competencies
    }

# Function to analyze position summary and tag with competencies
def analyze_position_summary(summary):
    """
    Analyze position summary and tag with 1-5 relevant competencies using AI.
    Uses LLM to determine the appropriate competency tags.
    """
    if not summary or not isinstance(summary, str):
        return []
    
    # Fetch standard competencies from DynamoDB
    try:
        # Get AWS credentials
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Create DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Get competencies table
        competencies_table = dynamodb.Table('competencies')
        
        # Scan all competencies
        response = competencies_table.scan()
        competencies_data = response.get('Items', [])
        
        # Create a list of standard competency names and a dictionary of descriptions
        standard_competency_names = []
        standard_competencies_details = {}
        
        for comp in competencies_data:
            name = comp.get('name', '')
            description = comp.get('description', '')
            if name:
                standard_competency_names.append(name)
                standard_competencies_details[name] = description
        
        # If no competencies found, use reasonable defaults
        if not standard_competency_names:
            logger.warning("No competencies found in database, using default set for summary analysis")
            standard_competency_names = [
                "Action Oriented", "Balances Stakeholders", "Being Resilient", "Builds Effective Teams",
                "Builds Networks", "Business Insight", "Collaborates", "Communicates Effectively",
                "Courage", "Customer Focus", "Decision Quality", "Develops Talent",
                "Directs Work", "Drives Engagement", "Drives Results", "Drives Vision and Purpose",
                "Financial Acumen", "Global Perspective", "Instills Trust", "Interpersonal Savvy",
                "Manages Ambiguity", "Manages Complexity", "Manages Conflict", "Nimble Learning",
                "Optimizes Work Processes", "Persuades", "Plans and Aligns", "Political Savvy",
                "Resourcefulness", "Self-Development", "Situational Adaptability", "Strategic Mindset",
                "Tech Savvy", "Values Differences"
            ]
    except Exception as e:
        logger.error(f"Error fetching competencies from DynamoDB: {str(e)}")
        # Use default competencies if database retrieval fails
        standard_competency_names = [
            "Action Oriented", "Balances Stakeholders", "Being Resilient", "Builds Effective Teams",
            "Builds Networks", "Business Insight", "Collaborates", "Communicates Effectively",
            "Courage", "Customer Focus", "Decision Quality", "Develops Talent",
            "Directs Work", "Drives Engagement", "Drives Results", "Drives Vision and Purpose",
            "Financial Acumen", "Global Perspective", "Instills Trust", "Interpersonal Savvy",
            "Manages Ambiguity", "Manages Complexity", "Manages Conflict", "Nimble Learning",
            "Optimizes Work Processes", "Persuades", "Plans and Aligns", "Political Savvy",
            "Resourcefulness", "Self-Development", "Situational Adaptability", "Strategic Mindset",
            "Tech Savvy", "Values Differences"
        ]
        standard_competencies_details = {}
    
    # Prepare the competency list for the LLM prompt
    competency_list_for_prompt = ", ".join(sorted(standard_competency_names))
    competency_details_for_prompt = ""
    for name in sorted(standard_competency_names):
        description = standard_competencies_details.get(name, "")
        if description:
            competency_details_for_prompt += f"\n- {name}: {description}"
        else:
            competency_details_for_prompt += f"\n- {name}"
    
    # Call OpenAI to determine the competencies for this summary
    try:
        # Prepare prompt for competency analysis
        if USE_NEW_OPENAI_SDK:
            response = client.chat.completions.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": f"""
                    You are a job analysis expert. Your task is to analyze a job position summary and identify 
                    the most relevant competencies it relates to. You MUST ONLY choose from the following 
                    specific competencies:
                    {competency_details_for_prompt}
                    
                    Return your analysis as a JSON array with the competency names (using the exact names as listed).
                    You MUST return between 1-5 competencies - at least 1, but no more than 5.
                    
                    Example output format:
                    ["Customer Focus", "Drives Results", "Communicates Effectively"]
                    """},
                    {"role": "user", "content": f"Analyze this job position summary and identify the competencies: '{summary}'"}
                ],
                temperature=0.3,
                max_tokens=150
            )
            response_content = response.choices[0].message.content
        else:
            response = openai.ChatCompletion.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": f"""
                    You are a job analysis expert. Your task is to analyze a job position summary and identify 
                    the most relevant competencies it relates to. You MUST ONLY choose from the following 
                    specific competencies:
                    {competency_details_for_prompt}
                    
                    Return your analysis as a JSON array with the competency names (using the exact names as listed).
                    You MUST return between 1-5 competencies - at least 1, but no more than 5.
                    
                    Example output format:
                    ["Customer Focus", "Drives Results", "Communicates Effectively"]
                    """},
                    {"role": "user", "content": f"Analyze this job position summary and identify the competencies: '{summary}'"}
                ],
                temperature=0.3,
                max_tokens=150
            )
            response_content = response.choices[0].message['content']
        
        # Parse response to extract competencies
        try:
            # Find JSON array in response content
            array_match = re.search(r'(\[.*\])', response_content, re.DOTALL)
            if array_match:
                json_str = array_match.group(1)
                competencies = json.loads(json_str)
            else:
                competencies = json.loads(response_content)
                
            # Format competencies and return
            if isinstance(competencies, list) and competencies:
                # Filter out any competencies not in our standard list
                filtered_competencies = [comp for comp in competencies if comp in standard_competency_names]
                
                # If no valid competencies remain after filtering, use a default
                if not filtered_competencies:
                    filtered_competencies = ["Business Insight"]  # A reasonable default
                
                # Ensure we have at least 1 and at most 5 competencies
                if len(filtered_competencies) > 5:
                    filtered_competencies = filtered_competencies[:5]
                
                return filtered_competencies
            else:
                # Default if parsing issue
                logger.warning(f"Couldn't parse competencies from LLM response for position summary")
                return ["Business Insight"] # A reasonable default
        except json.JSONDecodeError:
            # Handle parsing errors
            logger.warning(f"JSON parsing error for competency analysis of position summary")
            return ["Business Insight"] # A reasonable default
    except Exception as e:
        logger.error(f"Error analyzing competency for position summary: {str(e)}")
        return ["Business Insight"] # A reasonable default

# Function to get recommended questions based on competencies
def get_recommended_questions(top_competencies):
    """
    Get recommended questions based on top competencies.
    For each of the top 5 competencies, return 2 questions (primary and backup).
    If DynamoDB fails, use AI to generate questions.
    """
    recommended_questions = []
    
    try:
        # Get AWS credentials directly
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        logger.info(f"Creating direct DynamoDB connection for questions")
        
        # Create direct DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Get questions table
        questions_table = dynamodb.Table('questions')
        
        # Process up to 5 competencies
        competency_count = 0
        for competency in top_competencies:
            # Skip General category
            if competency == "General":
                continue
                
            # Scan questions for this competency
            response = questions_table.scan(
                FilterExpression="competency_name = :name",
                ExpressionAttributeValues={':name': competency}
            )
            
            questions = response.get('Items', [])
            
            # Sort by popularity and feedback score
            questions.sort(key=lambda x: (
                float(x.get('popularity', 0)), 
                float(x.get('feedback_score', 0))
            ), reverse=True)
            
            if len(questions) >= 2:
                # If we have at least 2 questions, use them
                recommendation = {
                    "competency": competency,
                    "rank": competency_count + 1,  # Rank from 1 to 5 based on position
                    "primary_question": questions[0].get('question_text', f"Tell me about your experience with {competency}"),
                    "backup_question": questions[1].get('question_text', f"Describe a situation where you demonstrated {competency}")
                }
                recommended_questions.append(recommendation)
                competency_count += 1
            elif len(questions) == 1:
                # If we have just 1 question, create a generic backup
                recommendation = {
                    "competency": competency,
                    "rank": competency_count + 1,  # Rank from 1 to 5 based on position
                    "primary_question": questions[0].get('question_text', f"Tell me about your experience with {competency}"),
                    "backup_question": f"Describe a situation where you demonstrated {competency}"
                }
                recommended_questions.append(recommendation)
                competency_count += 1
            else:
                # If no questions found, create generic ones
                recommendation = {
                    "competency": competency,
                    "rank": competency_count + 1,  # Rank from 1 to 5 based on position
                    "primary_question": f"Tell me about your experience with {competency}",
                    "backup_question": f"Describe a situation where you demonstrated {competency}"
                }
                recommended_questions.append(recommendation)
                competency_count += 1
            
            # Limit to 5 competencies
            if competency_count >= 5:
                break
        
        # If we still need more questions (less than 5 competencies were found)
        if competency_count < 5:
            # Generate additional questions using LLM
            missing_count = 5 - competency_count
            logger.info(f"Generating {missing_count} additional competency questions using LLM")
            
            # Default competencies to ensure we have 5
            default_competencies = ["Problem Solving", "Communication", "Leadership", "Adaptability", "Teamwork"]
            
            # Use competencies that weren't already used
            for competency in default_competencies:
                if competency_count >= 5:
                    break
                    
                if competency not in [q["competency"] for q in recommended_questions]:
                    recommendation = {
                        "competency": competency,
                        "rank": competency_count + 1,
                        "primary_question": f"Tell me about your experience with {competency}",
                        "backup_question": f"Describe a situation where you demonstrated {competency}"
                    }
                    recommended_questions.append(recommendation)
                    competency_count += 1
    
    except Exception as e:
        logger.error(f"Error in get_recommended_questions: {str(e)}")
        # Return default questions on error
        recommended_questions = [
            {
                "competency": "Problem Solving",
                "rank": 1,
                "primary_question": "Tell me about a time you solved a complex problem.",
                "backup_question": "What approach do you take when facing challenging problems?"
            },
            {
                "competency": "Communication",
                "rank": 2,
                "primary_question": "Describe a situation where your communication skills made a difference.",
                "backup_question": "How do you adapt your communication style to different audiences?"
            },
            {
                "competency": "Leadership",
                "rank": 3,
                "primary_question": "Give me an example of when you demonstrated leadership.",
                "backup_question": "How do you motivate team members to achieve goals?"
            },
            {
                "competency": "Adaptability",
                "rank": 4,
                "primary_question": "Tell me about a time when you had to adapt to a significant change.",
                "backup_question": "How do you approach new or unfamiliar situations?"
            },
            {
                "competency": "Teamwork",
                "rank": 5,
                "primary_question": "Describe your approach to working in a team.",
                "backup_question": "How do you handle conflicts within a team?"
            }
        ]
    
    return recommended_questions 

@app.route("/api/search_questions", methods=['GET'])
def search_questions():
    """
    Search for interview questions by competency or keyword.
    Used by the frontend search bar to find relevant questions.
    """
    try:
        # Get search query parameter
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"error": "Search query is required"}), 400
            
        logger.info(f"Searching for questions with query: {query}")
        
        # Get AWS credentials
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Create DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Get questions table
        questions_table = dynamodb.Table('questions')
        
        # First try exact competency match
        response = questions_table.scan(
            FilterExpression="contains(competency_name, :query)",
            ExpressionAttributeValues={':query': query}
        )
        
        questions = response.get('Items', [])
        
        # If no results, try searching in question text
        if not questions:
            response = questions_table.scan(
                FilterExpression="contains(question_text, :query)",
                ExpressionAttributeValues={':query': query}
            )
            questions.extend(response.get('Items', []))
            
        # Format questions for display
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                "question_text": q.get('question_text', ''),
                "competency_name": q.get('competency_name', ''),
                "id": q.get('id', '')
            })
            
        # If no questions found in DynamoDB, generate some using LLM
        if not formatted_questions:
            logger.info(f"No questions found in database, generating with LLM for: {query}")
            
            # Generate questions using OpenAI
            if USE_NEW_OPENAI_SDK:
                response = client.chat.completions.create(
                    model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": """
                        You are an expert at creating behavioral interview questions. Generate 5 high-quality
                        behavioral interview questions that follow the STAR method (Situation, Task, Action, Result)
                        for the specified competency or topic. These should be questions that help identify a 
                        candidate's past experience demonstrating this competency.
                        
                        Format your response as a JSON array of strings.
                        """},
                        {"role": "user", "content": f"Generate 5 interview questions about {query}"}
                    ],
                    temperature=0.7
                )
                response_content = response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": """
                        You are an expert at creating behavioral interview questions. Generate 5 high-quality
                        behavioral interview questions that follow the STAR method (Situation, Task, Action, Result)
                        for the specified competency or topic. These should be questions that help identify a 
                        candidate's past experience demonstrating this competency.
                        
                        Format your response as a JSON array of strings.
                        """},
                        {"role": "user", "content": f"Generate 5 interview questions about {query}"}
                    ],
                    temperature=0.7
                )
                response_content = response.choices[0].message['content']
                
            # Parse response to extract questions
            try:
                # Extract JSON array from response if needed
                json_match = re.search(r'(\[.*\])', response_content, re.DOTALL)
                if json_match:
                    json_array = json_match.group(1)
                    ai_questions = json.loads(json_array)
                else:
                    ai_questions = json.loads(response_content)
                    
                # Add generated questions to results
                for q in ai_questions:
                    formatted_questions.append({
                        "question_text": q,
                        "competency_name": query,
                        "id": f"generated-{uuid.uuid4()}"
                    })
            except Exception as parse_error:
                logger.error(f"Error parsing AI-generated questions: {str(parse_error)}")
                # Add the raw response as a fallback
                formatted_questions.append({
                    "question_text": f"Tell me about your experience with {query}",
                    "competency_name": query,
                    "id": f"fallback-{uuid.uuid4()}"
                })
        
        return jsonify({
            "questions": formatted_questions,
            "count": len(formatted_questions),
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Error searching questions: {str(e)}")
        return jsonify({"error": f"Error: {str(e)}"}), 500 

@app.route('/api/job-analysis', methods=['POST'])
def job_analysis():
    try:
        data = request.json
        job_description = data.get('jobDescription', '')
        
        # Use mock response if mock services are enabled
        if os.environ.get('MOCK_SERVICES') == 'true':
            logger.info(f"Using mock response for job analysis")
            mock_response = get_mock_job_analysis()
            
            # Generate recommended questions based on mock competencies
            competencies = [comp.get('name') for comp in mock_response.get('competencies', [])]
            questions = get_recommended_questions(competencies)
            mock_response['questions'] = questions
            
            return jsonify(mock_response)
        
        # Extract position summary if available
        position_summary = ""
        if job_description:
            # Try to find a position summary section
            summary_sections = re.split(
                r'\b(position summary|job summary|summary|about the role|about this role|overview)\b[:]*',
                job_description,
                flags=re.IGNORECASE
            )
            
            if len(summary_sections) > 1:
                # Get the text after the summary header
                summary_text = summary_sections[2].strip()
                
                # Find the next section header
                next_section = re.search(
                    r'\b(responsibilities|duties|what you\'ll do|requirements|qualifications|essential functions)\b[:]*',
                    summary_text,
                    flags=re.IGNORECASE
                )
                
                if next_section:
                    position_summary = summary_text[:next_section.start()].strip()
                else:
                    # Limit to a reasonable length if no next section found
                    position_summary = summary_text[:500].strip()
            
            # If we couldn't find a specific summary section, use the first paragraph
            if not position_summary:
                paragraphs = job_description.split('\n\n')
                if paragraphs:
                    position_summary = paragraphs[0].strip()
        
        # Extract job responsibilities if available
        responsibilities = []
        if job_description:
            # Look for section headers like "Responsibilities:" or "Duties:"
            responsibility_sections = re.split(
                r'\b(responsibilities|duties|what you\'ll do|job duties|key responsibilities|essential functions)\b[:]*',
                job_description, 
                flags=re.IGNORECASE
            )
            
            if len(responsibility_sections) > 1:
                # Get the text after the header
                resp_text = responsibility_sections[2].strip()
                
                # Find the next section header
                next_section = re.search(
                    r'\b(requirements|qualifications|what you\'ll need|skills|about you|who you are)\b[:]*',
                    resp_text,
                    flags=re.IGNORECASE
                )
                
                if next_section:
                    resp_text = resp_text[:next_section.start()].strip()
                
                # Split into bullet points if they exist
                if '•' in resp_text or '*' in resp_text or '-' in resp_text:
                    # Handle bullet points
                    bullet_items = re.split(r'[\n\r]\s*[•*\-]\s*', resp_text)
                    for item in bullet_items:
                        if item.strip():
                            responsibilities.append(item.strip())
                else:
                    # Split by sentences or newlines
                    sentences = re.split(r'[\.\n\r]+', resp_text)
                    for sentence in sentences:
                        if len(sentence.strip()) > 20:  # Ignore short fragments
                            responsibilities.append(sentence.strip())
            
            # If we couldn't extract responsibilities, use line-by-line approach
            if not responsibilities:
                lines = job_description.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    # Identify likely responsibility statements
                    if clean_line and len(clean_line) > 20 and not clean_line.endswith(':'):
                        # Lines starting with bullets or having action verbs
                        if (clean_line.startswith('•') or clean_line.startswith('-') or clean_line.startswith('*') or 
                            re.match(r'^[A-Z][a-z]+ing\b', clean_line) or re.match(r'^[A-Z][a-z]+e\b', clean_line)):
                            responsibilities.append(clean_line.lstrip('•*- '))
        
        # Analyze position summary
        summary_tags = []
        if position_summary:
            summary_tags = analyze_position_summary(position_summary)
            logger.info(f"Position summary tags: {summary_tags}")
        
        # Process responsibilities if found
        if responsibilities:
            # Analyze responsibilities 
            analysis_results = analyze_job_responsibilities(responsibilities)
            tagged_responsibilities = analysis_results.get("tagged_responsibilities", [])
            top_competencies = analysis_results.get("top_competencies", [])
            
            # Get competency analysis from LLM
            if USE_NEW_OPENAI_SDK:
                response = client.chat.completions.create(
                    model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": """
                        You are a job analysis agent. Your task is to analyze a job description and identify the top 5 most 
                        important competencies for this role. Focus on extracting competencies that are clearly important based 
                        on the job description, not general competencies that would apply to any job.
                        
                        For each competency, provide:
                        1. The competency name (e.g., "Project Management", "Data Analysis")
                        2. A brief explanation of why this competency is important for the role (1-2 sentences)
                        3. A list of 5 keywords associated with this competency
                        
                        Format your response as valid JSON with the following structure:
                        {
                          "competencies": [
                            {
                              "name": "Competency Name",
                              "importance": "Brief explanation of importance",
                              "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                            },
                            ...
                          ]
                        }
                        
                        Ensure you identify exactly 5 unique competencies. Your response must be valid JSON.
                        """},
                        {"role": "user", "content": job_description}
                    ],
                    temperature=0.7
                )
                response_content = response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": """
                        You are a job analysis agent. Your task is to analyze a job description and identify the top 5 most 
                        important competencies for this role. Focus on extracting competencies that are clearly important based 
                        on the job description, not general competencies that would apply to any job.
                        
                        For each competency, provide:
                        1. The competency name (e.g., "Project Management", "Data Analysis")
                        2. A brief explanation of why this competency is important for the role (1-2 sentences)
                        3. A list of 5 keywords associated with this competency
                        
                        Format your response as valid JSON with the following structure:
                        {
                          "competencies": [
                            {
                              "name": "Competency Name",
                              "importance": "Brief explanation of importance",
                              "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                            },
                            ...
                          ]
                        }
                        
                        Ensure you identify exactly 5 unique competencies. Your response must be valid JSON.
                        """},
                        {"role": "user", "content": job_description}
                    ],
                    temperature=0.7
                )
                response_content = response.choices[0].message['content']
            
            # Try to extract valid JSON from the response
            try:
                # Find JSON object in the response
                json_match = re.search(r'(\{.*\})', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    analysis_result = json.loads(json_str)
                else:
                    analysis_result = json.loads(response_content)
                    
                # Extract competency names for question generation
                llm_competencies = [comp.get('name') for comp in analysis_result.get('competencies', [])]
                
                # Combine LLM competencies with those from responsibility analysis
                combined_competencies = []
                
                # First add top competencies from responsibility analysis 
                for comp in top_competencies:
                    if comp != "General" and comp not in combined_competencies:
                        combined_competencies.append(comp)
                
                # Add LLM competencies not already included
                for comp in llm_competencies:
                    if comp not in combined_competencies:
                        combined_competencies.append(comp)
                
                # Keep only top 5
                top_competencies = combined_competencies[:5]
                
                # Generate recommended questions based on these competencies
                questions = get_recommended_questions(top_competencies)
                
                # Add to analysis result
                analysis_result['questions'] = questions
                analysis_result['top_competencies'] = top_competencies
                analysis_result['tagged_responsibilities'] = tagged_responsibilities
                analysis_result['position_summary'] = position_summary
                analysis_result['summary_tags'] = summary_tags
                
                return jsonify(analysis_result)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {response_content}")
                return jsonify({
                    "error": "Failed to parse analysis result",
                    "competencies": [],
                    "questions": get_recommended_questions(top_competencies),
                    "top_competencies": top_competencies,
                    "tagged_responsibilities": tagged_responsibilities,
                    "position_summary": position_summary,
                    "summary_tags": summary_tags
                }), 500
        
        # Call OpenAI API with specified prompt if no responsibilities found
        if USE_NEW_OPENAI_SDK:
            response = client.chat.completions.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": """
                    You are a job analysis agent. Your task is to analyze a job description and identify the top 5 most 
                    important competencies for this role. Focus on extracting competencies that are clearly important based 
                    on the job description, not general competencies that would apply to any job.
                    
                    For each competency, provide:
                    1. The competency name (e.g., "Project Management", "Data Analysis")
                    2. A brief explanation of why this competency is important for the role (1-2 sentences)
                    3. A list of 5 keywords associated with this competency
                    
                    Format your response as valid JSON with the following structure:
                    {
                      "competencies": [
                        {
                          "name": "Competency Name",
                          "importance": "Brief explanation of importance",
                          "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                        },
                        ...
                      ]
                    }
                    
                    Ensure you identify exactly 5 unique competencies. Your response must be valid JSON.
                    """},
                    {"role": "user", "content": job_description}
                ],
                temperature=0.7
            )
            response_content = response.choices[0].message.content
        else:
            response = openai.ChatCompletion.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": """
                    You are a job analysis agent. Your task is to analyze a job description and identify the top 5 most 
                    important competencies for this role. Focus on extracting competencies that are clearly important based 
                    on the job description, not general competencies that would apply to any job.
                    
                    For each competency, provide:
                    1. The competency name (e.g., "Project Management", "Data Analysis")
                    2. A brief explanation of why this competency is important for the role (1-2 sentences)
                    3. A list of 5 keywords associated with this competency
                    
                    Format your response as valid JSON with the following structure:
                    {
                      "competencies": [
                        {
                          "name": "Competency Name",
                          "importance": "Brief explanation of importance",
                          "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
                        },
                        ...
                      ]
                    }
                    
                    Ensure you identify exactly 5 unique competencies. Your response must be valid JSON.
                    """},
                    {"role": "user", "content": job_description}
                ],
                temperature=0.7
            )
            response_content = response.choices[0].message['content']
        
        # Try to extract valid JSON from the response
        try:
            # Find JSON object in the response
            json_match = re.search(r'(\{.*\})', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                analysis_result = json.loads(json_str)
            else:
                analysis_result = json.loads(response_content)
                
            # Extract competency names for question generation
            competencies = [comp.get('name') for comp in analysis_result.get('competencies', [])]
            
            # Generate recommended questions based on these competencies
            questions = get_recommended_questions(competencies)
            analysis_result['questions'] = questions
            analysis_result['position_summary'] = position_summary
            analysis_result['summary_tags'] = summary_tags
            
            return jsonify(analysis_result)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from OpenAI response: {response_content}")
            return jsonify({
                "error": "Failed to parse analysis result",
                "competencies": [],
                "position_summary": position_summary,
                "summary_tags": summary_tags
            }), 500
            
    except Exception as e:
        logger.error(f"Error in job analysis: {str(e)}")
        return jsonify({
            "error": str(e),
            "competencies": []
        }), 500 

@app.route("/api/get_competencies", methods=['GET'])
def get_competencies():
    """Return all competencies and their descriptions from the database"""
    try:
        # Get AWS credentials
        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Create DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        
        # Get competencies table
        competencies_table = dynamodb.Table('competencies')
        
        # Scan all competencies
        response = competencies_table.scan()
        competencies = response.get('Items', [])
        
        # Create a dictionary with competency name as key and description as value
        competencies_dict = {}
        for comp in competencies:
            name = comp.get('name', '')
            description = comp.get('description', '')
            if name:
                competencies_dict[name] = description
        
        # If no competencies found, use default ones as fallback
        if not competencies_dict:
            logger.warning("No competencies found in database, using default set")
            competencies_dict = {
                "Customer Focus": "Building strong customer relationships and delivering customer-centric solutions",
                "Financial Acumen": "Understanding financial concepts and making sound financial decisions",
                "Decision Quality": "Making good decisions based on analysis, experience, and judgment",
                "Strategic Mindset": "Seeing ahead to future possibilities and translating them into breakthrough strategies",
                "Business Insight": "Applying knowledge of business and the marketplace to advance the organization's goals",
                "Drives Results": "Consistently achieving results, even under tough circumstances",
                "Manages Complexity": "Making sense of complex, high-quantity, and sometimes contradictory information",
                "Tech Savvy": "Anticipating and adopting innovations in technology-based solutions",
                "Collaborates": "Building partnerships and working collaboratively with others",
                "Communicates Effectively": "Developing and delivering multi-mode communications that convey a clear understanding"
            }
        
        return jsonify({"competencies": competencies_dict})
        
    except Exception as e:
        logger.error(f"Error fetching competencies: {str(e)}")
        # Return hardcoded fallback
        fallback_competencies = {
            "Customer Focus": "Building strong customer relationships and delivering customer-centric solutions",
            "Financial Acumen": "Understanding financial concepts and making sound financial decisions",
            "Decision Quality": "Making good decisions based on analysis, experience, and judgment",
            "Strategic Mindset": "Seeing ahead to future possibilities and translating them into breakthrough strategies",
            "Business Insight": "Applying knowledge of business and the marketplace to advance the organization's goals"
        }
        return jsonify({"competencies": fallback_competencies}) 

# Endpoint for Evernorth demo
@app.route('/api/evernorth_demo', methods=['GET'])
def evernorth_demo():
    """
    Load the Risk and Underwriting Lead Analyst Evernorth PDF as a job posting.
    This is a specific demo endpoint for demonstration purposes.
    """
    try:
        # Path to the Evernorth demo file
        demo_file_path = 'Risk and Underwriting Lead Analyst Evernorth.pdf'
        content = ""
        
        # Check if the file exists
        if os.path.exists(demo_file_path):
            # Extract text from the job posting
            content = extract_text_from_document(demo_file_path)
        else:
            # Use hardcoded sample text for demo purposes if file not found
            logger.warning(f"Evernorth demo file not found at {demo_file_path}. Using hardcoded content instead.")
            content = """
Risk and Underwriting Lead Analyst, Evernorth

Position Summary:
The Risk and Underwriting Lead Analyst will provide analytical support to the Underwriting team and coordinate with the Risk team to ensure proper risk assessment and management. The role involves analyzing complex data sets, developing models, and providing insights to inform underwriting decisions, while also implementing risk management strategies to minimize exposure.

Responsibilities:
• Analyze financial and operational data to identify trends, risks, and opportunities for underwriting decisions
• Develop statistical and predictive models to assist in risk assessment and pricing
• Create comprehensive reports and dashboards to communicate findings to stakeholders
• Collaborate with cross-functional teams to understand business requirements and objectives
• Implement risk management strategies to ensure compliance with regulatory requirements
• Monitor key risk indicators and develop early warning systems for potential issues
• Conduct scenario analyses to evaluate potential impacts of market changes
• Provide analytical support for special projects and initiatives
• Document processes and methodologies to ensure consistency and transparency
• Stay current with industry trends and best practices in risk management and underwriting

Qualifications:
• Bachelor's degree in Finance, Economics, Mathematics, Statistics, or related field
• 3-5 years of experience in risk analysis, underwriting, or similar analytical role
• Strong analytical and problem-solving skills
• Proficiency in data analysis tools and techniques
• Experience with statistical modeling and predictive analytics
• Knowledge of insurance or financial services industry preferred
• Excellent written and verbal communication skills
• Ability to translate complex analyses into actionable insights
• Detail-oriented with strong organizational skills
• Ability to work independently and as part of a team
            """
        
        if not content or len(content.strip()) < 10:
            content = "Risk and Underwriting Lead Analyst position for Evernorth requiring analytical skills, risk assessment experience, and strong communication abilities."
        
        # Parse job posting
        job_data = parse_job_posting(content)
        
        # Store in session
        if "job_posting" not in SESSION_STORE:
            SESSION_STORE["job_posting"] = {}
        
        SESSION_STORE["job_posting"]["content"] = content
        SESSION_STORE["job_posting"]["job_data"] = job_data
        
        # Extract responsibilities
        responsibilities = job_data.get("responsibilities", [])
        SESSION_STORE["job_posting"]["responsibilities"] = responsibilities
        
        # If responsibilities were extracted, analyze them
        if responsibilities:
            # Get competency analysis
            analysis_results = analyze_job_responsibilities(responsibilities)
            tagged_responsibilities = analysis_results.get("tagged_responsibilities", [])
            top_competencies = analysis_results.get("top_competencies", [])
            
            # Store competency analysis
            SESSION_STORE["job_posting"]["tagged_responsibilities"] = tagged_responsibilities
            SESSION_STORE["job_posting"]["top_competencies"] = top_competencies
            
            # Generate recommended questions
            recommended_questions = get_recommended_questions(top_competencies)
            SESSION_STORE["job_posting"]["recommended_questions"] = recommended_questions
            
            # Extract and analyze position summary
            position_summary = job_data.get("summary", "")
            summary_tags = []
            if position_summary:
                summary_tags = analyze_position_summary(position_summary)
            
            # Return success with relevant data
            return jsonify({
                "success": True,
                "message": "Evernorth demo job posting loaded and analyzed successfully!",
                "job_description": content,
                "responsibilities": responsibilities,
                "tagged_responsibilities": tagged_responsibilities,
                "top_competencies": top_competencies,
                "recommended_questions": recommended_questions,
                "job_data": job_data,
                "position_summary": position_summary,
                "summary_tags": summary_tags
            })
        
        # Return success even without responsibilities
        return jsonify({
            "success": True,
            "message": "Evernorth demo job posting loaded successfully!",
            "job_description": content,
            "job_data": job_data
        })
        
    except Exception as e:
        logger.error(f"Error loading Evernorth demo: {str(e)}")
        return jsonify({"error": f"Error loading Evernorth demo: {str(e)}"}), 500 