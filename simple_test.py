import os
import json
import requests
from pprint import pprint

def test_generate_questions_endpoint():
    """Test the generate_initial_questions API endpoint directly"""
    
    # API endpoint
    url = "http://localhost:5000/api/generate_initial_questions"
    
    # Sample data
    data = {
        "resume_text": "Experienced software engineer with 5 years of experience in Python and web development. Previously worked as a Senior Software Engineer at Tech Solutions Inc. where I led development of cloud-based applications using Python and AWS. Also worked as a Software Developer at Code Innovations, developing web applications using Django and React. Skills include Python, JavaScript, AWS, Django, React, and SQL. Education: Bachelor of Computer Science from State University.",
        
        "job_text": "Senior Python Developer at Innovative Tech. We are looking for an experienced Python developer to join our team. Requirements: 5+ years of experience with Python, experience with web frameworks such as Django or Flask, knowledge of AWS services, strong problem-solving skills. Responsibilities: Develop and maintain web applications, work collaboratively with the team to design solutions, implement best practices for code quality and security, mentor junior developers.",
        
        "competencies": [
            "Technical Expertise",
            "Problem Solving",
            "Communication",
            "Leadership",
            "Adaptability"
        ],
        
        "question_type": "initial"
    }
    
    # Make the POST request
    print("Sending request to generate interview questions...")
    response = requests.post(url, json=data)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        result = response.json()
        
        # Print the results
        print("\n=== Generated Questions ===")
        if "questions" in result and result["questions"]:
            for i, q in enumerate(result["questions"], 1):
                if isinstance(q, dict):
                    print(f"{i}. {q.get('question', '')}")
                    if "competency" in q:
                        print(f"   Competency: {q.get('competency', '')}")
                    if "look_for" in q:
                        print(f"   Look for: {q.get('look_for', '')}")
                else:
                    print(f"{i}. {q}")
                print()
        else:
            print("No questions were generated.")
        
        # Print additional context if available
        if "context" in result:
            print("\n=== Context ===")
            pprint(result["context"])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_generate_questions_endpoint() 