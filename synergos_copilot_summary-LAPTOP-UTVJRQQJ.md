# Synergos AI Interview Co-Pilot - Session Summary

**Date:** 2025-04-21 (Approximate)

**Goal:** Align the application's competency-based question generation with the specific 38 competencies, descriptions, and preset questions defined in the Cigna PDF guide (`Competencies_InterviewGuide_iPDF-Final.pdf`).

**Key Steps & Changes:**

1.  **Data Extraction:** Competency data (names, descriptions, leadership flag, 2 preset questions) was extracted from the PDF into JSON format and saved locally (assumed path: `c:/Users/jchen/Downloads/competenciesmap.txt`).
2.  **Database Model Update (`synergos/synergos/models/question.py`):** Added an integer column `preset_order` to the `Question` model to distinguish the two preset questions for each competency.
3.  **Database Population (`populate_competencies.py`):**
    *   Created a script to read the JSON data.
    *   The script clears the `competencies` and `questions` DynamoDB tables (requires confirmation).
    *   It populates the tables with the 38 standard competencies (using `category` field for leadership flag) and their 76 corresponding preset questions (marked with `preset_order` 1 or 2).
    *   **Last Action:** This script was run successfully, clearing old data and populating the correct Cigna competencies/questions.
4.  **Backend Logic Update (`synergos/app.py`):**
    *   Refactored `analyze_job_responsibilities`:
        *   Removed keyword-based analysis.
        *   Fetches standard competencies/descriptions from DynamoDB.
        *   Uses LLM (GPT-3.5-turbo, temp=0) to analyze *each* responsibility against the standard list+descriptions.
        *   Assigns the single best-fit standard competency tag to each responsibility.
        *   Aggregates counts and determines the overall top 5 standard competencies (using LLM refinement if needed).
    *   Refactored `get_recommended_questions`:
        *   Takes the top 5 standard competency names.
        *   Uses DynamoDB `Scan` to find the 2 preset questions (`preset_order` 1 & 2) for each of the top 5 competencies.
        *   Returns data in the format expected by the frontend (`primary_question`, `backup_question`).
5.  **Frontend Rendering Update (`synergos/templates/index.html`):**
    *   Modified the JavaScript within the HTML file.
    *   Removed logic that added a "General" tag when no standard competency was matched for responsibilities under "Essential Functions".
    *   Removed competency analysis/tagging for the "Position Summary" section (LLM call needs async implementation - marked with TODO).
6.  **Docker Configuration (`docker-compose.override.yml`):**
    *   Added a volume mount (`.:/app`) to sync local code changes into the container.
    *   Added the `--reload` flag to the `gunicorn` command for automatic Python code reloading (though manual restarts were needed frequently).
7.  **Last Action:** Docker containers were restarted (`docker-compose down`, `docker-compose up -d`) after the final code and database updates.

**Current Status:**

*   The database should contain only the 38 standard Cigna competencies and their preset questions.
*   The backend logic should correctly identify standard competencies based on LLM analysis of responsibilities (assigning exactly one best-fit tag per responsibility) and retrieve the corresponding preset questions.
*   The frontend should display tags under "Essential Functions" based on the backend analysis (exactly one standard tag per responsibility). "General" tags should not appear. The "Position Summary" section currently shows no tags.
*   The correct 5 pairs of competency-based questions should be displayed.

**Next Steps on New Computer:**

1.  Ensure all code changes are transferred (e.g., via Git or direct copy).
2.  Verify Docker and Docker Compose are installed.
3.  Set up necessary environment variables (`.env` file - especially `OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`).
4.  Ensure the DynamoDB tables (`competencies`, `questions`, `competency_keywords`) exist and contain the correct data (populated by `populate_competencies.py`). If starting fresh, run the population script. Remember its dependency on `c:/Users/jchen/Downloads/competenciesmap.txt` or update the path.
5.  Ensure the necessary Python dependencies (`requirements.txt`) are installed (Docker build should handle this).
6.  Run `docker-compose up -d`.
7.  Test the application by uploading a job posting and verify the competency tags and questions match expectations. 