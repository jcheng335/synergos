// Consolidated interview-copilot.js
// This file was created by merging multiple versions on 2025-04-22
// Base file: synergos\static\js\interview-copilot.js
// 
// Other versions that were consolidated:
// - interview-copilot.js
// - fixed-interview-copilot.js
// - interview-copilot.js.root_backup
//
// All functionality should be preserved.

// Synergos Interview Co-Pilot - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // State variables
    let isRecording = false;
    let selectedQuestions = [];
    let askedQuestions = [];
    let currentQuestion = null;
    let transcriptQueue = [];
    let isProcessing = false;
    let phaseState = "Not Started";
    let globalResumeContent = null;
    let globalJobPostingContent = null;
    let ws = null; // WebSocket connection
    let audioContext = null;
    let scriptProcessor = null;
    let mediaStreamSource = null;
    let audioInputBuffer = []; // Buffer for audio chunks
    let analysisTimeout = null; // Debounce timer for analysis
    const ANALYSIS_DEBOUNCE_MS = 1500; // Wait 1.5 seconds after last final segment
    let mediaRecorder = null; // For MediaRecorder API
    let audioChunks = [];    // To store audio chunks
    let recordedAudioBlob = null; // To store final blob
    
    // Add state variable for response tracking
    let analyzedQuestions = {}; // Store finalized analyses by question index
    let currentQuestionIndex = 0; // Track the current question's index
    let isAnalysisFinalized = false; // Flag for when analysis is complete
    let currentAnalysisElement = null; // Reference to current analysis element
    
    // UI Elements
    const startButton = document.getElementById('start');
    const stopButton = document.getElementById('stop');
    const testDemoButton = document.getElementById('testDemoButton');
    const analyzeButton = document.getElementById('analyzeButton');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const statusMessagesContainer = document.getElementById('statusMessages');
    const questionBox = document.getElementById('question_box');
    const selectedQuestionsBox = document.getElementById('selected_questions_box');
    const candidateTranscriptBox = document.getElementById('candidate_transcript_box');
    const responseSummaryBox = document.getElementById('response_summary_box');
    const followupQuestionsContainer = document.getElementById('followup_questions_container');
    const processingIndicator = document.getElementById('processingIndicator');
    const phaseIndicator = document.getElementById('currentPhase');
    const questionCountDisplay = document.getElementById('questionCount');
    const jobAnalysisSection = document.getElementById('jobAnalysisSection');
    
    // Form elements
    const resumeForm = document.getElementById('resumeForm');
    const jobPostingForm = document.getElementById('jobPostingForm');
    const jobUrlForm = document.getElementById('jobUrlForm');
    
    // Initialize global SESSION_STORE if it doesn't exist
    window.SESSION_STORE = window.SESSION_STORE || {};
    
    // Session ID for transcript/analysis API calls
    const sessionId = Date.now().toString();
    
    // Nova Sonic session management
    let novaSessionId = null;
    let isNovaInitialized = false;
    
    // Initialize global interview data object
    window.interviewData = {
        questions: {},
        timestamp: new Date().toISOString(),
        summary: {}
    };
    
    // Add event listeners for the transcript processing buttons
    const analyzeResponseBtn = document.getElementById('analyzeResponseBtn');
    if (analyzeResponseBtn) {
        analyzeResponseBtn.addEventListener('click', function() {
            processTranscript('analyzeResponseBtn');
        });
    }

    const finalizeResponseBtn = document.getElementById('finalizeResponseBtn');
    if (finalizeResponseBtn) {
        finalizeResponseBtn.addEventListener('click', function() {
            processTranscript('finalizeResponseBtn');
        });
    }
    
    // Resume form submit handler
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Resume form submitted');
        const formData = new FormData(resumeForm);
        
        // Log the file being uploaded
        const fileInput = document.getElementById('resumeFile');
        if (fileInput && fileInput.files.length > 0) {
            console.log('Uploading file:', fileInput.files[0].name);
        }
        
        // Show processing indicator
        showProcessingIndicator();
        
        fetch('/api/upload_resume', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Resume upload response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Resume upload response data:', data);
            hideProcessingIndicator();
            
            if (data.success) {
                addStatusMessage('Resume uploaded and analyzed successfully!', 'success');
                
                // Store resume data in SESSION_STORE
                if (!window.SESSION_STORE) {
                    window.SESSION_STORE = {};
                }
                window.SESSION_STORE.resume = {
                    uploaded: true,
                    analysis: data.resume_analysis || {},
                    questions: data.questions || []
                };
                
                // Display Resume-based Questions if available
                if (data.questions && data.questions.length > 0) {
                    console.log('Displaying', data.questions.length, 'resume questions');
                    displayResumeQuestions(data.questions);
                } else {
                    console.log('No questions returned from resume upload');
                    addStatusMessage('Resume processed but no questions generated. Check API configuration.', 'warning');
                }
                
                // --- Display Enhanced Resume Overview ---
                const resumeOverviewCard = document.getElementById('resumeOverviewCard');
                const resumeOverviewBox = document.getElementById('resume_overview_box');
                if (resumeOverviewCard && resumeOverviewBox && data.resume_analysis) {
                    // --- Log the received analysis data --- 
                    console.log("Received resume_analysis data:", JSON.stringify(data.resume_analysis, null, 2)); 
                    // --- End log ---
                    
                    resumeOverviewCard.style.display = 'block';
                    let overviewHTML = '';
                    const analysis = data.resume_analysis;
                    
                    if (analysis.current_role) {
                        overviewHTML += `<p><strong>Role:</strong> ${escapeHTML(analysis.current_role)}</p>`;
                    }
                    if (analysis.years_experience) {
                         overviewHTML += `<p><strong>Experience:</strong> ${escapeHTML(String(analysis.years_experience))} years</p>`;
                    }
                    if (analysis.skills && Array.isArray(analysis.skills) && analysis.skills.length > 0) {
                        overviewHTML += `<p><strong>Skills:</strong></p><ul class="list-unstyled ms-2 d-flex flex-wrap">`; // Use flex-wrap for badges
                        analysis.skills.slice(0, 7).forEach(skill => {
                            overviewHTML += `<li class="badge bg-secondary me-1 mb-1">${escapeHTML(skill)}</li>`;
                        });
                         if (analysis.skills.length > 7) {
                             overviewHTML += `<li class="badge bg-light text-dark me-1 mb-1">+${analysis.skills.length - 7} more</li>`;
                         }
                        overviewHTML += `</ul>`;
                    }

                    // Display Experience Details (assuming analysis.experience is an array of objects)
                     if (analysis.experience && Array.isArray(analysis.experience) && analysis.experience.length > 0) {
                         overviewHTML += `<hr><p><strong>Experience Highlights:</strong></p>`;
                         analysis.experience.slice(0, 3).forEach(exp => { // Show top 3 experiences
                             overviewHTML += `<div class="mb-2 ms-2">`;
                             overviewHTML += `<div class="small"><strong>${escapeHTML(exp.title || 'Position')}</strong> at ${escapeHTML(exp.company || 'Company')} (${escapeHTML(exp.duration || 'Duration')})</div>`;
                             // Display responsibilities/description if available (assuming a 'description' or 'responsibilities' key)
                             let points = exp.description || exp.responsibilities;
                             if (points && Array.isArray(points) && points.length > 0) {
                                 overviewHTML += `<ul class="list-unstyled ms-3 small">`;
                                 points.slice(0, 2).forEach(point => { // Show first 2 points
                                     overviewHTML += `<li>- ${escapeHTML(point)}</li>`;
                                 });
                                 overviewHTML += `</ul>`;
                             } else if (points && typeof points === 'string') {
                                 // Handle if it's just a string description
                                 overviewHTML += `<p class="ms-3 small fst-italic">${escapeHTML(points.substring(0, 100))}...</p>`; // Show excerpt
                             }
                             overviewHTML += `</div>`;
                         });
                     }
                      if (analysis.education && Array.isArray(analysis.education) && analysis.education.length > 0) {
                         overviewHTML += `<hr><p><strong>Education:</strong></p>`;
                         analysis.education.slice(0, 1).forEach(edu => { 
                             overviewHTML += `<p class="ms-2 small">${escapeHTML(edu.degree || 'Degree')} from ${escapeHTML(edu.institution || 'Institution')} (${escapeHTML(edu.year || 'Year')})</p>`;
                         });
                     }

                    resumeOverviewBox.innerHTML = overviewHTML || '<p class="text-muted">Could not extract detailed overview.</p>';
                } else if (resumeOverviewCard) {
                    resumeOverviewCard.style.display = 'block'; 
                    resumeOverviewBox.innerHTML = '<p class="text-muted">Could not extract resume overview details.</p>';
                }
                // --- END Resume Overview ---

                // Set phase
                updatePhase('Resume Uploaded');
                globalResumeContent = true;
            } else {
                console.error('Resume upload failed:', data.error);
                addStatusMessage(`Error: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Resume upload error:', error);
            hideProcessingIndicator();
            addStatusMessage(`Upload failed: ${error.message}`, 'danger');
        });
    });
    
    // Job Posting form submit handler
    jobPostingForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Job posting form submitted');
        const formData = new FormData(jobPostingForm);
        
        // Log the file being uploaded
        const fileInput = document.getElementById('jobPostingFile');
        if (fileInput && fileInput.files.length > 0) {
            console.log('Uploading job file:', fileInput.files[0].name);
        }
        
        showProcessingIndicator();
        
        fetch('/api/upload_job_posting', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Job posting upload response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Job posting upload response data:', data);
            hideProcessingIndicator();
            
            if (data.success) {
                addStatusMessage('Job posting uploaded and analyzed successfully!', 'success');
                globalJobPostingContent = true;
                
                // Store job data in session
                if (!window.SESSION_STORE.job_posting) {
                    window.SESSION_STORE.job_posting = {};
                }
                window.SESSION_STORE.job_posting.job_data = data.job_data || {};
                
                // Process and display job responsibilities with competencies
                if (data.tagged_responsibilities && data.tagged_responsibilities.length > 0) {
                    // Show job analysis section
                    jobAnalysisSection.style.display = 'block';
                    // Render tagged responsibilities
                    renderTaggedResponsibilities(data.tagged_responsibilities);
                } else if (data.responsibilities && data.responsibilities.length > 0) {
                    // If no tagged responsibilities but raw ones are available, analyze them
                    const analysis = analyzeJobResponsibilities(data.responsibilities);
                    
                    // Show job analysis section
                    jobAnalysisSection.style.display = 'block';
                    
                    // Render tagged responsibilities
                    renderTaggedResponsibilities(analysis.taggedResponsibilities);
                }
                
                // Display recommended questions
                if (data.recommended_questions && data.recommended_questions.length > 0) {
                    displayQuestions(data.recommended_questions, 'Competency-Based Questions');
                    updatePhase('Job Analysis Complete');
                }
            } else {
                addStatusMessage(`Error: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            hideProcessingIndicator();
            addStatusMessage(`Job posting upload failed: ${error.message}`, 'danger');
            console.error('Error:', error);
        });
    });
    
    // Job URL form submit handler
    jobUrlForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(jobUrlForm);
        
        showProcessingIndicator();
        
        fetch('/api/process_job_posting_url', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideProcessingIndicator();
            
            if (data.success) {
                addStatusMessage('Job posting URL processed successfully!', 'success');
                globalJobPostingContent = true;
                
                // Process responsibilities
                if (data.tagged_responsibilities && data.tagged_responsibilities.length > 0) {
                    // Show job analysis section
                    jobAnalysisSection.style.display = 'block';
                    
                    // Render tagged responsibilities
                    renderTaggedResponsibilities(data.tagged_responsibilities);
                    
                    // Update phase
                    updatePhase('Job Analysis Complete');
                } else if (data.responsibilities && data.responsibilities.length > 0) {
                    const analysis = analyzeJobResponsibilities(data.responsibilities);
                    
                    // Show job analysis section
                    jobAnalysisSection.style.display = 'block';
                    
                    // Render tagged responsibilities
                    renderTaggedResponsibilities(analysis.taggedResponsibilities);
                    
                    // Update phase
                    updatePhase('Job Analysis Complete');
                }
                
                // Display recommended questions
                if (data.recommended_questions && data.recommended_questions.length > 0) {
                    displayQuestions(data.recommended_questions, 'Competency-Based Questions');
                }
            } else {
                addStatusMessage(`Error: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            hideProcessingIndicator();
            addStatusMessage(`Job URL processing failed: ${error.message}`, 'danger');
            console.error('Error:', error);
        });
    });
    
    // Start button event listener
    startButton.addEventListener('click', function() {
        // Original check (commented out):
        // if (selectedQuestions.length === 0) {
        //    addStatusMessage('Please select at least one interview question before starting.', 'warning');
        //    return;
        // }

        // --- NEW CHECK: Check the UI element directly --- 
        const selectedBoxHasItems = selectedQuestionsBox.querySelector('.selected-question-item'); 
        if (!selectedBoxHasItems) { // If no items are displayed in the box
           addStatusMessage('Please select at least one interview question before starting.', 'warning');
           return;
        }
        // --- END NEW CHECK ---
        
        startInterview();
    });
    
    // Stop button event listener
    stopButton.addEventListener('click', function() {
        stopInterview();
    });
    
    // Test demo button
    testDemoButton.addEventListener('click', function() {
        // Make sure there's a selected question
        if (selectedQuestions.length === 0) {
            // Get intro questions if none selected
            fetch('/api/get_introductory_questions')
                .then(response => response.json())
                .then(data => {
                    if (data.questions && data.questions.length > 0) {
                        // Select the first question
                        const firstQuestion = data.questions[0];
                        addSelectedQuestion(firstQuestion);
                        
                        // Run the test with this question
                        runTestWithQuestion(firstQuestion);
                    } else {
                        addStatusMessage('Could not load test questions. Please select a question first.', 'warning');
                    }
                })
                .catch(error => {
                    console.error('Error getting intro questions:', error);
                    addStatusMessage('Error preparing test: ' + error.message, 'danger');
                });
        } else {
            // Use the first selected question
            const testQuestion = selectedQuestions[0];
            runTestWithQuestion(testQuestion);
        }
    });
    
    // Evernorth Demo button
    // Analyze button handler
    if (analyzeButton) {
        analyzeButton.addEventListener('click', function() {
            console.log("Analyze button clicked");
            
            // Check if resume or job posting has been uploaded
            const hasResume = window.SESSION_STORE && window.SESSION_STORE.resume;
            const hasJobPosting = window.SESSION_STORE && window.SESSION_STORE.job_posting;
            
            if (!hasResume && !hasJobPosting) {
                addStatusMessage('Please upload a resume or job posting first to analyze.', 'warning');
                return;
            }
            
            showProcessingIndicator();
            addStatusMessage('Analyzing documents and generating questions...', 'info');
            
            // If we have both, generate combined analysis
            if (hasResume && hasJobPosting) {
                fetch('/api/generate_recommendation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        has_resume: true,
                        has_job_posting: true
                    })
                })
                .then(response => response.json())
                .then(data => {
                    hideProcessingIndicator();
                    console.log('Combined analysis response:', data);
                    
                    if (data.questions && data.questions.length > 0) {
                        displayQuestions(data.questions, 'Interview Questions');
                        addStatusMessage('Analysis complete! Questions generated based on resume and job posting.', 'success');
                    } else {
                        addStatusMessage('Analysis complete but no questions were generated. Check API configuration.', 'warning');
                    }
                })
                .catch(error => {
                    hideProcessingIndicator();
                    console.error('Analysis error:', error);
                    addStatusMessage('Error during analysis: ' + error.message, 'danger');
                });
            }
            // If only resume, re-process it
            else if (hasResume) {
                addStatusMessage('Re-analyzing resume...', 'info');
                // Trigger the resume form submit programmatically
                const resumeForm = document.getElementById('resumeForm');
                const fileInput = document.getElementById('resumeFile');
                if (fileInput && fileInput.files.length > 0) {
                    resumeForm.dispatchEvent(new Event('submit'));
                } else {
                    hideProcessingIndicator();
                    addStatusMessage('Please re-upload the resume file.', 'warning');
                }
            }
            // If only job posting, re-process it
            else if (hasJobPosting) {
                addStatusMessage('Re-analyzing job posting...', 'info');
                // Trigger the job posting form submit programmatically
                const jobForm = document.getElementById('jobPostingForm');
                const fileInput = document.getElementById('jobPostingFile');
                if (fileInput && fileInput.files.length > 0) {
                    jobForm.dispatchEvent(new Event('submit'));
                } else {
                    hideProcessingIndicator();
                    addStatusMessage('Please re-upload the job posting file.', 'warning');
                }
            }
        });
    }
    
    const evernorthDemoButton = document.getElementById('evernorthDemoButton');
    if (evernorthDemoButton) {
        evernorthDemoButton.addEventListener('click', function() {
            console.log("Evernorth Demo button clicked");
            showProcessingIndicator();
            addStatusMessage('Loading Evernorth Demo...', 'info');
            
            // Show job analysis section immediately
            jobAnalysisSection.style.display = 'block';
            
            // Define hardcoded questions in specific order
            const hardcodedQuestions = [
                {
                    question: "Walk me through your resume.",
                    competency: "Introduction",
                    type: "introduction",
                    isOriginal: true
                },
                {
                    question: "Based on what you have learned about underwriting through the interview process, why would you be a good fit for this position?",
                    competency: "Underwriting Knowledge Question",
                    type: "standard",
                    isOriginal: true
                },
                {
                    question: "Share an example of a time when you used financial, industry, or economic data to make an informed decision.",
                    competency: "Financial Acumen",
                    type: "competency",
                    isOriginal: true
                },
                {
                    question: "How do you balance competing priorities to ensure progress is made and expectations are met?",
                    competency: "Resourcefulness",
                    type: "competency",
                    isOriginal: true
                },
                {
                    question: "Describe a complex project or initiative that you led or were part of – what steps did you take to organize yourself and your work?",
                    competency: "Plans And Aligns",
                    type: "competency",
                    isOriginal: true
                },
                {
                    question: "Give me an example of how you vary your communication style for different audiences.",
                    competency: "Communicates Effectively",
                    type: "competency",
                    isOriginal: true
                },
                {
                    question: "What is something you are learning right now (outside of the school or work environment)?",
                    competency: "Nimble Learning",
                    type: "competency",
                    isOriginal: true
                },
                {
                    question: "Do you have any questions for me?",
                    competency: "Closing",
                    type: "closing",
                    isOriginal: true
                }
            ];
            
            // Display questions in the suggested questions area only (not auto-selecting them)
            displayQuestions(hardcodedQuestions, 'Evernorth Interview Questions');
            
            // Clear the selected questions box to ensure it's empty
            if (selectedQuestionsBox) {
                selectedQuestionsBox.innerHTML = '<li class="text-muted">No questions selected yet. Click on suggested questions to add them here.</li>';
                updateQuestionCountDisplay(); // Update the count display
                
                // Clear the selectedQuestions array
                selectedQuestions = [];
                console.log("Cleared selectedQuestions array");
            }
            
            // Update phase right away
            updatePhase('Evernorth Demo Ready');
            
            // Initialize the job responsibilities list with placeholder text to make it show immediately
            const respList = document.getElementById('jobResponsibilitiesList');
            if (respList) {
                respList.innerHTML = '<div class="alert alert-info">Loading job analysis data...</div>';
            }
            
            // Get the competencies we want to fetch preset questions for
            const presetCompetencies = [
                "Financial Acumen", 
                "Resourcefulness", 
                "Plans And Aligns", 
                "Communicates Effectively", 
                "Nimble Learning"
            ];
            
            // Then call the API to get the job posting for the job analysis part
            console.log("Making API call to /api/evernorth_demo");
            
            fetch('/api/evernorth_demo')
                .then(response => {
                    console.log("API response received:", response.status, response.statusText);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("API data received:", data);
                    hideProcessingIndicator();
                    
                    if (data.success) {
                        addStatusMessage('Evernorth demo job posting loaded successfully!', 'success');
                        globalJobPostingContent = true;
                        
                        // Store job data in session
                        if (!window.SESSION_STORE) {
                            window.SESSION_STORE = {};
                        }
                        window.SESSION_STORE.job_posting = data;
                        
                        // Mark this as the Evernorth demo
                        window.SESSION_STORE.is_evernorth_demo = true;
                        
                        // Process responsibilities
                        if (data.tagged_responsibilities && Array.isArray(data.tagged_responsibilities)) {
                            console.log("Rendering tagged responsibilities:", data.tagged_responsibilities);
                            
                            try {
                                // Call the function we defined
                            renderTaggedResponsibilities(data.tagged_responsibilities);
                            } catch (err) {
                                console.error("Error rendering tagged responsibilities:", err);
                                // Fallback if function fails
                                const respList = document.getElementById('jobResponsibilitiesList');
                            if (respList) {
                                    respList.innerHTML = '<div class="alert alert-warning">Could not render job responsibilities. Please reload the page.</div>';
                            }
                        }
                    } else {
                            console.error("No valid tagged_responsibilities in API response:", data);
                        // Display error in the job analysis section
                            const respList = document.getElementById('jobResponsibilitiesList');
                        if (respList) {
                                respList.innerHTML = '<div class="alert alert-warning">Could not load job responsibilities</div>';
                            }
                        }
                        
                        // Display resume questions if available
                        if (data.resume_questions && Array.isArray(data.resume_questions) && data.resume_questions.length > 0) {
                            console.log("Displaying resume questions:", data.resume_questions);
                            // Use the new function to display in a separate card
                            displayResumeQuestions(data.resume_questions);
                        }
                        
                        // Show prompt to upload resume
                        const resumeOverviewCard = document.getElementById('resumeOverviewCard');
                        const resumeOverviewBox = document.getElementById('resume_overview_box');
                        
                        if (resumeOverviewCard && resumeOverviewBox) {
                            // Show the card with upload prompt
                            resumeOverviewCard.style.display = 'block';
                            resumeOverviewBox.innerHTML = `
                                <div class="alert alert-info">
                                    <p><strong>Upload a Resume</strong></p>
                                    <p>Please upload a resume using the form above to see candidate information here.</p>
                                </div>
                            `;
                        }
                        
                    } else {
                        console.error("API response indicates failure:", data);
                        addStatusMessage(`Error loading Evernorth demo: ${data.error || 'Unknown error'}`, 'danger');
                    }
                })
                .catch(error => {
                    hideProcessingIndicator();
                    console.error('Error loading Evernorth demo:', error);
                    addStatusMessage(`Error loading Evernorth demo: ${error.message}`, 'danger');
                });
        });
    } else {
        console.error("Evernorth Demo button not found in DOM");
    }
    
    // Function to run a test with a specific question
    function runTestWithQuestion(question) {
        showProcessingIndicator();
        
        // Call the test endpoint
        fetch('/api/test_interview_flow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question
            })
        })
        .then(response => response.json())
        .then(data => {
            hideProcessingIndicator();
            
            if (data.success) {
                // Display the simulated transcript
                if (data.transcript) {
                    candidateTranscriptBox.innerHTML = `
                        <div class="mb-2">
                            <span class="interviewer-text">Interviewer:</span> ${question}
                        </div>
                        <div>
                            <span class="candidate-text">Candidate:</span> ${data.transcript}
                        </div>
                    `;
                }
                
                // Display the analysis
                if (data.analysis_type === "star" && data.star_analysis) {
                    displayStarAnalysis(data.star_analysis);
                    
                    // Display follow-up questions
                    if (data.followup_questions && data.followup_questions.length > 0) {
                        displayFollowupQuestions(data.followup_questions);
                    }
                } else if (data.is_intro && data.bullets) {
                    // Create a properly formatted data object for the new function signature
                    const formattedData = {
                        bullet_points: data.bullets,
                        competencies: data.competencies || []
                    };
                    displayBulletPointSummary(formattedData, "introduction");
                }
                
                addStatusMessage('Test interview flow completed successfully!', 'success');
                updatePhase('Interview Analysis Demo');
            } else {
                addStatusMessage(`Test failed: ${data.error}`, 'danger');
            }
        })
        .catch(error => {
            hideProcessingIndicator();
            addStatusMessage(`Test error: ${error.message}`, 'danger');
            console.error('Error in test flow:', error);
        });
    }
    
    // Function to display questions in the suggestion box
    function displayQuestions(questions, category = 'Suggested Questions') {
        console.log("Displaying questions:", questions, "Category:", category);
        
        // Special handling for Resume-Based Questions - move to separate card
        if (category === 'Resume-Based Questions') {
            displayResumeQuestions(questions);
            return;
        }
        
        if (!questions || questions.length === 0) {
            questionBox.innerHTML = '<p class="text-muted">No questions available.</p>';
            return;
        }
        
        // Create header for question category
        let html = `<h5 class="mb-3">${category}</h5>`;
        
        // If this is "Competency-Based Questions" or "Evernorth Interview Questions", they should be displayed differently
        if (category === 'Competency-Based Questions' || category === 'Evernorth Interview Questions') {
            // Store existing content so we can prepend this category
            const existingContent = questionBox.innerHTML;
            
            // Check if "Introductory Questions" category already exists in a safer way
            const hasIntroQuestions = Array.from(questionBox.querySelectorAll('h5')).some(
                h5 => h5.textContent.includes('Introductory Questions')
            );
            
            // Group questions by competency
            const groupedQuestions = {};
            
            questions.forEach(rec => {
                const competency = rec.competency || 'General';
                if (!groupedQuestions[competency]) {
                    groupedQuestions[competency] = [];
                }
                
                // Handle different object structures
                if (rec.primary_question) {
                    groupedQuestions[competency].push({ 
                        text: rec.primary_question, 
                        is_primary: true, 
                        alternate_question: rec.backup_question || null 
                    });
                } else if (rec.question) {
                    // Handle Evernorth format
                    groupedQuestions[competency].push({ 
                        text: rec.question, 
                        is_primary: true, 
                        alternate_question: null 
                    });
                }
                
                if (rec.backup_question && rec.backup_question !== (rec.primary_question ? (rec.alternate_question || null) : null)) {
                     if (!rec.primary_question) {
                         groupedQuestions[competency].push({ text: rec.backup_question, is_primary: false, alternate_question: null });
                     }
                }
            });
            
            for (const [competency, competencyQuestions] of Object.entries(groupedQuestions)) {
                html += `<div class="competency-group mb-3">`;
                html += `<h6 class="competency-title">${escapeHTML(competency)}</h6>`;
                competencyQuestions.forEach(q => {
                    if (q.is_primary) {
                        html += `<div class="question primary-question" data-question="${escapeHTML(q.text)}" data-competency="${escapeHTML(competency)}"><strong>${escapeHTML(q.text)}</strong></div>`;
                        if (q.alternate_question) {
                             html += `<div class="question backup-question" data-question="${escapeHTML(q.alternate_question)}" data-competency="${escapeHTML(competency)}">${escapeHTML(q.alternate_question)}</div>`;
                        }
                    } else {
                         html += `<div class="question backup-question" data-question="${escapeHTML(q.text)}" data-competency="${escapeHTML(competency)}">${escapeHTML(q.text)}</div>`;
                    }
                });
                html += `</div>`;
            }
            
            // Preserve existing content for Evernorth category to prevent overwriting
            if (category === 'Evernorth Interview Questions') {
                // Preserve current content by prepending new content
                questionBox.innerHTML = html + questionBox.innerHTML;
        } else {
                questionBox.innerHTML = html;
            }
        } else {
            // Handle other categories (like Introductory) - simple list
             questions.forEach(question => {
                let questionText;
                if (typeof question === 'string') {
                    questionText = question;
                } else if (question.question) {
                    questionText = question.question;
                } else {
                    questionText = JSON.stringify(question);
                }
                 html += `<div class="question" data-question="${escapeHTML(questionText)}">${escapeHTML(questionText)}</div>`;
             });
            
            questionBox.innerHTML = html;
        }
        
        // Add click handlers to newly added questions IN THE CORRECT BOX
        questionBox.querySelectorAll('.question').forEach(questionElement => {
            // Remove existing listener if any to prevent duplicates
            questionElement.removeEventListener('click', handleQuestionClick);
            questionElement.addEventListener('click', handleQuestionClick);
        });
        
        // After updating, re-run filter in case search term exists
        if(questionBox === 'question_box' && searchInput) {
             filterSuggestedQuestions(searchInput.value.toLowerCase().trim());
        }
    }

    // Function to display resume-based questions in their own separate card
    function displayResumeQuestions(questions) {
        console.log("Displaying resume questions in separate card:", questions);
        
        // Use the existing resumeQuestionsCard from the HTML
        const resumeQuestionsCard = document.getElementById('resumeQuestionsCard');
        const resumeQuestionsBox = document.getElementById('resume_question_box');
        
        if (!resumeQuestionsCard || !resumeQuestionsBox) {
            console.error("Could not find resume questions card or box");
            return;
        }
        
        // Show the card
        resumeQuestionsCard.style.display = 'block';
        
        // Clear existing resume questions
        resumeQuestionsBox.innerHTML = '';
        
        // Check if we have questions to display
        if (!questions || questions.length === 0) {
            resumeQuestionsBox.innerHTML = '<p class="text-muted">No resume-based questions available.</p>';
            return;
        }
        
        // Process and display the resume questions
        questions.forEach(question => {
            let questionText, competency = '';
            
            if (typeof question === 'string') {
                questionText = question;
            } else if (question.question) {
                questionText = question.question;
                competency = question.competency || '';
            } else if (typeof question === 'object') {
                questionText = JSON.stringify(question);
            }
            
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question mb-2 p-2 border-bottom';
            questionDiv.setAttribute('data-question', questionText);
            if (competency) {
                questionDiv.setAttribute('data-competency', competency);
            }
            
            questionDiv.innerHTML = `
                <strong>${escapeHTML(questionText)}</strong>
                ${competency ? `<div class="text-primary small mt-1">${escapeHTML(competency)}</div>` : ''}
            `;
            
            resumeQuestionsBox.appendChild(questionDiv);
            
            // Add click handler
            questionDiv.addEventListener('click', handleQuestionClick);
        });
        
        console.log("Resume questions displayed successfully");
    }

    // Separate handler function for question clicks
    function handleQuestionClick() {
        const questionText = this.getAttribute('data-question');
        const competency = this.getAttribute('data-competency') || ''; 
        addSelectedQuestion(questionText, competency); 
    }
    
    // --- Modify addSelectedQuestion to accept competency ---
    function addSelectedQuestion(questionText, competency = '') { 
        // Check if already selected
        const existingSelected = Array.from(document.querySelectorAll('#selected_questions_box .selected-question-item'))
                                     .map(el => el.getAttribute('data-question'));
        if (existingSelected.includes(questionText)) {
             console.log("Selected question already exists:", questionText);
             // Optional highlight logic (ensure it finds the element correctly)
             try {
                 const items = document.querySelectorAll('#selected_questions_box .selected-question-item');
                 let existingItem = null;
                 items.forEach(item => {
                     if (item.getAttribute('data-question') === questionText) {
                         existingItem = item;
                     }
                 });
                 if (existingItem) {
                     existingItem.classList.add('border-warning', 'border-3');
                     setTimeout(() => existingItem.classList.remove('border-warning', 'border-3'), 1000);
                 }
             } catch (e) { console.error("Error highlighting existing selected Q:", e); }
            return;
        }
        
        // Add to the selectedQuestions array for tracking
        if (!selectedQuestions.includes(questionText)) {
            selectedQuestions.push(questionText);
            console.log("Added to selectedQuestions array:", questionText);
        }
        
        // --- Create and append the new list item directly --- 
        const selectedQuestionsBox = document.getElementById('selected_questions_box');
        if (!selectedQuestionsBox) return;

        // Remove placeholder if adding the first question
        const placeholder = selectedQuestionsBox.querySelector('.text-muted');
        if (placeholder) {
            placeholder.remove();
        }

        // Calculate question index/number (1-based)
        const questionIndex = selectedQuestionsBox.querySelectorAll('.selected-question-item').length + 1;

        const questionItem = document.createElement('li');
        const isAsked = askedQuestions.includes(questionText);
        questionItem.className = `selected-question-item${isAsked ? ' asked' : ''}`;
        questionItem.setAttribute('data-question', questionText);
        questionItem.setAttribute('data-question-index', questionIndex); // Store index on element
        if (competency) { // Use the passed competency
             questionItem.setAttribute('data-competency', competency);
        }

        let innerHTML = `
            <div class="d-flex justify-content-between align-items-center"> 
                <div class="flex-grow-1 me-2">
                    <span class="question-number badge bg-secondary me-2">Q${questionIndex}</span>
                    <div>${escapeHTML(questionText)}</div>
                    ${competency ? `<div class="text-primary small mt-1">${escapeHTML(competency)}</div>` : ''}
                </div>
                <div class="flex-shrink-0 ms-2"> 
                    <button class="btn btn-sm btn-outline-primary btn-ask me-1" title="Ask this question">Ask</button>
                    <button class="btn btn-sm btn-outline-danger btn-remove p-0 px-1 lh-1" title="Remove question">×</button>
                </div>
            </div>
        `;
        questionItem.innerHTML = innerHTML;
        selectedQuestionsBox.appendChild(questionItem);

        // Add listeners to the buttons on the NEWLY ADDED item
        questionItem.querySelector('.btn-remove').addEventListener('click', function() {
            questionItem.remove();
            updateQuestionCountDisplay();
             if (selectedQuestionsBox.children.length === 0) {
                 selectedQuestionsBox.innerHTML = '<li class="text-muted">No questions selected yet.</li>';
             }
        });
        questionItem.querySelector('.btn-ask').addEventListener('click', handleAskButtonClick); 
        // --- End direct item creation ---

        // Update the count display
        updateQuestionCountDisplay();
    }

    // Update just the question count display
    function updateQuestionCountDisplay() {
        const count = document.querySelectorAll('#selected_questions_box .selected-question-item').length;
        questionCountDisplay.textContent = count.toString();
    }

    // Function to handle Ask button clicks - updated to finalize previous analysis
    function handleAskButtonClick() {
        const listItem = this.closest('li.selected-question-item');
        if (!listItem) return;
        
        const question = listItem.getAttribute('data-question');
        const questionIndex = parseInt(listItem.getAttribute('data-question-index'), 10);
        
        // Finalize the previous question's analysis if needed
        finalizeCurrentAnalysis();
        
        // Update current question tracking
        currentQuestion = question;
        currentQuestionIndex = questionIndex;
        isAnalysisFinalized = false;
        
        console.log(`Current question set to: Q${currentQuestionIndex} - ${currentQuestion}`);

        // Mark all as inactive, then this one as active
        document.querySelectorAll('#selected_questions_box .selected-question-item').forEach(li => li.classList.remove('active'));
        listItem.classList.add('active');

        askQuestion(question); // Call function to display question in transcript
    }
    
    // Function to finalize the current analysis if it exists
    function finalizeCurrentAnalysis() {
        if (currentQuestion && !isAnalysisFinalized && currentAnalysisElement) {
            console.log(`Finalizing analysis for Q${currentQuestionIndex}: ${currentQuestion}`);
            
            // Mark the analysis as finalized in our tracking
            analyzedQuestions[currentQuestionIndex] = {
                question: currentQuestion,
                analysisElement: currentAnalysisElement
            };
            
            // Remove the 'current-analysis-container' class from temporary container
            currentAnalysisElement.classList.remove('current-analysis-container');
            currentAnalysisElement.classList.add('finalized-analysis');
            
            isAnalysisFinalized = true;
            currentAnalysisElement = null; // Clear reference to start fresh with next question
        }
    }
    
    // Function to ask a selected question (Displays in transcript)
    function askQuestion(question) {
        console.log("Asking question:", question);
        // Add question text to candidate transcript area
        const questionElement = document.createElement('div');
        questionElement.className = 'mb-2 p-2 bg-light rounded interviewer-text-container'; // Added classes for styling
        questionElement.innerHTML = `<span class="interviewer-text">Interviewer:</span> ${escapeHTML(question)}`;
        
        candidateTranscriptBox.appendChild(questionElement);
        candidateTranscriptBox.scrollTop = candidateTranscriptBox.scrollHeight; // Scroll to bottom
        
        // Mark question as asked if not already
        if (!askedQuestions.includes(question)) {
            askedQuestions.push(question);
             // Update the corresponding list item UI (find it again)
            const listItem = selectedQuestionsBox.querySelector(`li[data-question="${question}"]`);
            if(listItem) listItem.classList.add('asked');
        }
        
        // Phase update might happen here or in startInterview depending on flow
        // updatePhase('Asking Question'); 
    }
    
    // Function to start the interview - Using Web Speech API again
    async function startInterview() {
        if (isRecording) return;
        if (!selectedQuestionsBox.querySelector('.selected-question-item')) {
           addStatusMessage('Please select at least one interview question before starting.', 'warning');
           return;
        }

        try {
            // Initialize Nova transcription
            await startNovaTranscription();
        } catch (error) {
            addStatusMessage('Failed to start recording. Please check your microphone permissions and try again.', 'danger');
            console.error('Failed to start Nova transcription:', error);
            return;
        } 
        
        // Nova will handle transcription via the processNovaTranscription function
        // Set up interview state
        isRecording = true;
        startButton.disabled = true;
        stopButton.disabled = true; // Will be enabled once recording starts successfully
        
        // Clear previous transcript
        candidateTranscriptBox.innerHTML = '';
        
        // Show the first question
        if (selectedQuestions.length > 0) {
            currentQuestion = selectedQuestions[0].question_text || selectedQuestions[0];
            showCurrentQuestion();
        }

        
        // Update UI state
        updateRecordingIndicator('Recording...', 'text-danger');
        stopButton.disabled = false;
        addStatusMessage('Interview started! Listening with Nova...', 'info');
        updatePhase('Interviewing');
        
        // Clear previous analysis
        responseSummaryBox.innerHTML = '<p class="text-muted">Analysis will appear here after candidate responds.</p>';
        followupQuestionsContainer.innerHTML = '<p class="text-muted small">Follow-up questions will appear here.</p>';

        // Ask the first selected question
        const firstSelected = selectedQuestionsBox.querySelector('.selected-question-item');
        if(firstSelected) {
            currentQuestion = firstSelected.getAttribute('data-question');
            askQuestion(currentQuestion);
            firstSelected.classList.add('active'); // Mark first question as active
        } else {
            addStatusMessage('Error: No question found in selected list to start.', 'danger');
            stopInterview();
        }
    }
    
    // Function to stop the interview - Using Nova
    function stopInterview() {
        if (!isRecording) return;
        console.log("Stop interview called.");
        isRecording = false;
        clearTimeout(analysisTimeout); // Cancel any pending analysis

        // Stop Nova transcription
        stopNovaTranscription();

        updateRecordingIndicator('Stopped', 'text-muted');
        startButton.disabled = false;
        stopButton.disabled = true;

        // Get final accumulated transcript from all segments
        let fullTranscript = "";
        const responseDivs = candidateTranscriptBox.querySelectorAll('.candidate-response .candidate-words');
        responseDivs.forEach(div => {
            fullTranscript += div.textContent.replace(/<span class="interim">.*<\/span>/, '').trim() + " ";
        });
        fullTranscript = fullTranscript.trim();
        console.log("Final accumulated transcript on stop:", fullTranscript);

        // Trigger final analysis if needed
        if (currentQuestion && fullTranscript && fullTranscript.length > 10) {
            console.log("Triggering final analysis on stop.");
            analyzeResponse(fullTranscript, currentQuestion); 
            // Analysis will remain temporary until next question is selected
        } else {
            console.log("No analysis triggered on stop (no question/transcript).");
            hideProcessingIndicator(); // Ensure spinner is hidden if no analysis runs
            updatePhase('Interview Ended'); 
        }

        addStatusMessage('Interview recording ended.', 'info');
    }
    
    // Function to analyze the candidate's response
    function analyzeResponse(transcript, questionType) {
        console.log("Analyzing response for question type:", questionType);
        
        // Show processing indicators
        const processingIndicator = document.getElementById('processingIndicator');
        if (processingIndicator) {
            processingIndicator.classList.add('show');
        }
        
        // Retrieve the current question and question index
        const activeQuestion = document.querySelector('#selected_questions_box .selected-question-item.active');
        const questionText = activeQuestion ? activeQuestion.getAttribute('data-question') : '';
        const competency = activeQuestion ? activeQuestion.getAttribute('data-competency') || '' : '';
        const questionNumber = activeQuestion ? activeQuestion.getAttribute('data-question-index') : '';
        
        // Determine question type if not provided
        if (!questionType) {
            questionType = 'standard';
            // Check if this is the first question (introduction)
            if (questionNumber === '1') {
                questionType = 'introduction';
            }
            // Check if this might be a closing question
            if (questionText.toLowerCase().includes('questions for me') || 
                questionText.toLowerCase().includes('any questions')) {
                questionType = 'closing';
            }
        }
        
        // Get resume and job description content from session store if available
        let resumeText = '';
        let jobDescription = '';
        if (window.SESSION_STORE) {
            if (window.SESSION_STORE.resume) {
                resumeText = window.SESSION_STORE.resume.content || '';
            }
            if (window.SESSION_STORE.job_posting) {
                jobDescription = window.SESSION_STORE.job_posting.content || '';
            }
        }
        
        // Make the API call to analyze the response
        fetch('/api/analyze-response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transcript: transcript,
                question: questionText,
                question_type: questionType,
                question_number: questionNumber,
                competency: competency,
                resume: resumeText,
                job_description: jobDescription
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide the processing indicator
            if (processingIndicator) {
                processingIndicator.classList.remove('show');
            }
            
            console.log("Analysis data received:", data);
            
            // Display the bullet point summary
            if (data && data.analysis) {
                if (questionType === 'introduction' || questionType === 'closing') {
                    displayBulletPointSummary(data.analysis, questionType);
                    } else {
                    displayStarAnalysis(data.analysis);
                }
                
                // Store the analysis data for the current question
                storeQuestionAnalysis(questionNumber, transcript, data.analysis);
                
                // Show follow-up questions if available
                if (data.analysis.followup_questions || data.analysis.candidate_questions) {
                    const questions = data.analysis.followup_questions || data.analysis.candidate_questions;
                    if (questions && Array.isArray(questions) && questions.length > 0) {
                        displayFollowupQuestions(questions);
                    }
                }
                
                // Return success
                return true;
            } else {
                console.error('Invalid analysis data received:', data);
                
                // Handle fallback
                const fallbackAnalysis = createFallbackAnalysis(transcript, questionType, competency, questionNumber);
                if (questionType === 'introduction' || questionType === 'closing') {
                    displayBulletPointSummary(fallbackAnalysis, questionType);
                } else {
                    displayStarAnalysis(fallbackAnalysis);
                }
                
                // Return failure
                return false;
            }
        })
        .catch(error => {
            console.error('Error analyzing response:', error);
            
            // Hide the processing indicator
            if (processingIndicator) {
                processingIndicator.classList.remove('show');
            }
            
            // Handle fallback
            const fallbackAnalysis = createFallbackAnalysis(transcript, questionType, competency, questionNumber);
            if (questionType === 'introduction' || questionType === 'closing') {
                displayBulletPointSummary(fallbackAnalysis, questionType);
            } else {
                displayStarAnalysis(fallbackAnalysis);
            }
            
            // Return failure
            return false;
        });
    }

    // Helper function to store question analysis data
    function storeQuestionAnalysis(questionNumber, transcript, analysis) {
        // Initialize the interview data structure if it doesn't exist
        if (!window.interviewData) {
            window.interviewData = {
                questions: {}
            };
        }
        
        // Store the data for this question
        window.interviewData.questions[questionNumber] = {
            transcript: transcript,
            analysis: analysis,
            timestamp: new Date().toISOString()
        };
    }

    // Helper function to try both endpoints
    function fetchWithFallback(primaryEndpoint, fallbackEndpoint, options) {
        return fetch(primaryEndpoint, options)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Primary endpoint failed: ${response.status}`);
                }
                return response.json();
            })
            .catch(primaryError => {
                console.warn(`Primary endpoint error (${primaryEndpoint}):`, primaryError);
                console.log("Trying fallback endpoint:", fallbackEndpoint);
                
                // Try the fallback endpoint
                return fetch(fallbackEndpoint, options)
                    .then(fallbackResponse => {
                        if (!fallbackResponse.ok) {
                            throw new Error(`Fallback endpoint failed: ${fallbackResponse.status}`);
                        }
                        return fallbackResponse.json();
                    })
                    .catch(fallbackError => {
                        console.error(`Both endpoints failed. Fallback error (${fallbackEndpoint}):`, fallbackError);
                        throw new Error("All API endpoints failed");
                    });
            });
    }

    // Create a fallback analysis when API fails or times out
    function createFallbackAnalysis(transcript, questionType, competency, questionNumber) {
        console.log("Creating fallback analysis");
        
        if (questionType.toLowerCase() === 'introduction' || questionType.toLowerCase() === 'closing') {
            // For intro/closing, create bullet points
            return {
                transcript: transcript,
                bullet_points: [
                    "The candidate provided an introduction/closing response.",
                    "Automated analysis is not available for this response.",
                    "Please review the transcript directly."
                ],
                question_number: questionNumber,
                competency: competency
            };
        } else {
            // For behavioral questions, create STAR format
            return {
                transcript: transcript,
                situation: "Unable to automatically analyze the situation component.",
                task: "Unable to automatically analyze the task component.",
                action: "Unable to automatically analyze the action component.",
                result: "Unable to automatically analyze the result component.",
                question_number: questionNumber,
                competency: competency
            };
        }
    }
    
    // Function to update recording indicator
    function updateRecordingIndicator(text, className) {
        if (!text && !className) {
            // Legacy behavior - use recording state
            if (isRecording) {
                recordingIndicator.classList.add('recording');
                recordingIndicator.textContent = 'Recording...';
            } else {
                recordingIndicator.classList.remove('recording');
                recordingIndicator.textContent = '';
            }
        } else {
            // New behavior - use provided text and class
            recordingIndicator.textContent = text || '';
            recordingIndicator.className = className || '';
        }
    }
    
    // Function to update the current phase
    function updatePhase(phase) {
        phaseState = phase;
        phaseIndicator.textContent = phase;
    }
    
    // Function to add a status message
    function addStatusMessage(message, type) {
        const messageElement = document.createElement('div');
        messageElement.className = `status-message ${type}`;
        messageElement.textContent = message;
        
        // Add to container
        statusMessagesContainer.appendChild(messageElement);
        
        // Remove after 5 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
    
    // Updated STAR analysis display function to include question number
    function displayStarAnalysis(starAnalysis) {
        console.log("Displaying STAR analysis:", starAnalysis);
        
        // Get the current question index for the title
        const activeQuestion = document.querySelector('#selected_questions_box .selected-question-item.active');
        const questionNumber = activeQuestion ? activeQuestion.getAttribute('data-question-index') : '';
        const competency = activeQuestion ? activeQuestion.getAttribute('data-competency') || '' : '';
        
        // Determine the appropriate title based on domain information and question number
        let title = `Summary - Q${questionNumber}`;
        if (starAnalysis.domain) {
            title += ` - ${starAnalysis.domain}`;
        } else if (competency) {
            title += ` - ${competency}`;
        }
        
        let html = '<div class="card mb-3">';
        html += `<div class="card-header bg-info text-white">${title}</div>`;
        html += '<div class="card-body">';
        
        // Check if we have competencies to display
        if (starAnalysis.competencies && starAnalysis.competencies.length > 0) {
            // Display Competencies Demonstrated
            html += '<div class="competencies-section mb-4">';
            html += '<h5>Competencies Demonstrated:</h5>';
            html += '<ul class="competency-list">';
            
            starAnalysis.competencies.forEach(competency => {
                let competencyDisplay = escapeHTML(competency.name || competency);
                if (competency.level) {
                    competencyDisplay += ` (Level: ${escapeHTML(competency.level)})`;
                }
                
                html += `<li class="competency-item">${competencyDisplay}`;
                
                // Add evidence if available
                if (competency.evidence) {
                    html += `<div class="competency-evidence small text-muted mt-1">
                        <em>Evidence: ${escapeHTML(competency.evidence)}</em>
                    </div>`;
                }
                
                html += '</li>';
            });
            
            html += '</ul>';
            html += '</div>';
            
            // Show STAR analysis
        // Situation
            html += '<div class="star-section">';
        html += '<div class="star-category">Situation:</div>';
            html += `<div class="star-content">${escapeHTML(starAnalysis.situation)}</div>`;
            html += '</div>';
        
        // Task
            html += '<div class="star-section">';
        html += '<div class="star-category">Task:</div>';
            html += `<div class="star-content">${escapeHTML(starAnalysis.task)}</div>`;
            html += '</div>';
        
        // Action
            html += '<div class="star-section">';
        html += '<div class="star-category">Action:</div>';
            html += `<div class="star-content">${escapeHTML(starAnalysis.action)}</div>`;
            html += '</div>';
        
        // Result
            html += '<div class="star-section">';
        html += '<div class="star-category">Result:</div>';
            html += `<div class="star-content">${escapeHTML(starAnalysis.result)}</div>`;
            html += '</div>';
        } else {
            // If no competencies but we have STAR components, show them
            if (starAnalysis.situation || starAnalysis.task || starAnalysis.action || starAnalysis.result) {
                // Situation
                if (starAnalysis.situation) {
                    html += '<div class="star-section">';
                    html += '<div class="star-category">Situation:</div>';
                    html += `<div class="star-content">${escapeHTML(starAnalysis.situation)}</div>`;
                    html += '</div>';
                }
                
                // Task
                if (starAnalysis.task) {
                    html += '<div class="star-section">';
                    html += '<div class="star-category">Task:</div>';
                    html += `<div class="star-content">${escapeHTML(starAnalysis.task)}</div>`;
                    html += '</div>';
                }
                
                // Action
                if (starAnalysis.action) {
                    html += '<div class="star-section">';
                    html += '<div class="star-category">Action:</div>';
                    html += `<div class="star-content">${escapeHTML(starAnalysis.action)}</div>`;
                    html += '</div>';
                }
                
                // Result
                if (starAnalysis.result) {
                    html += '<div class="star-section">';
                    html += '<div class="star-category">Result:</div>';
                    html += `<div class="star-content">${escapeHTML(starAnalysis.result)}</div>`;
                    html += '</div>';
                }
            } else if (starAnalysis.bullet_points && starAnalysis.bullet_points.length > 0) {
                // If no STAR but we have bullet points
                html += '<div class="bullet-points-section">';
                html += '<h5>Key Points:</h5>';
                html += '<ul class="bullet-list">';
                
                starAnalysis.bullet_points.forEach(point => {
                    html += `<li>${escapeHTML(point)}</li>`;
                });
                
                html += '</ul>';
                html += '</div>';
            } else {
                // No structured data available
                html += '<p>No detailed analysis available for this response.</p>';
                
                // Show transcript if available
                if (starAnalysis.transcript) {
                    html += '<div class="transcript-section mt-3">';
                    html += '<h5>Response Summary:</h5>';
                    html += `<p>${escapeHTML(starAnalysis.transcript)}</p>`;
            html += '</div>';
                }
            }
        }
        
        html += '</div></div>';
        
        responseSummaryBox.innerHTML = html;
        currentAnalysisElement = responseSummaryBox.querySelector('.card');
    }
    
    // Updated bullet point summary display function to match original functionality with improvements
    function displayBulletPointSummary(summary, questionType) {
        console.log("Displaying bullet point summary:", summary);
        
        // Get the current question index for the title
        const activeQuestion = document.querySelector('#selected_questions_box .selected-question-item.active');
        const questionNumber = activeQuestion ? activeQuestion.getAttribute('data-question-index') : '';
        
        // Determine title based on question type
        let title = `Summary - Q${questionNumber}`;
        if (questionType === "introduction") {
            title += " - Introduction";
        } else if (questionType === "closing") {
            title += " - Closing";
        }
        
        let html = '<div class="card mb-3">';
        html += `<div class="card-header bg-info text-white">${title}</div>`;
        html += '<div class="card-body">';
        
        // Determine which bullet points to use, prioritizing API-provided ones
        let bulletPoints = [];
        
        // Check various places where bullet points might be in the API response
        if (summary.bullet_points && Array.isArray(summary.bullet_points)) {
            bulletPoints = summary.bullet_points;
        } else if (summary.bullets && Array.isArray(summary.bullets)) {
            bulletPoints = summary.bullets;
        } else if (summary.key_points && Array.isArray(summary.key_points)) {
            bulletPoints = summary.key_points;
        }
        
        // Display key points
        if (bulletPoints.length > 0) {
            html += '<div class="bullet-points-section mb-4">';
            html += '<h5>Key Points:</h5>';
            html += '<ul class="bullet-list">';
            
            bulletPoints.forEach(point => {
                html += `<li>${escapeHTML(point)}</li>`;
            });
            
            html += '</ul>';
            html += '</div>';
        } else {
            // If no bullet points are provided, display the transcript directly
            if (summary.transcript) {
                html += '<div class="transcript-section mb-4">';
                html += '<h5>Response Summary:</h5>';
                html += `<p>${escapeHTML(summary.transcript)}</p>`;
                html += '</div>';
            } else {
                html += '<p>No key points available for this response.</p>';
            }
    }
    
        // For closing questions, display candidate questions if available
        if (questionType === "closing") {
            let candidateQuestions = [];
            if (summary.candidate_questions && Array.isArray(summary.candidate_questions)) {
                candidateQuestions = summary.candidate_questions;
            }
            
            if (candidateQuestions.length > 0) {
                html += '<div class="candidate-questions-section">';
                html += '<h5>Candidate Questions:</h5>';
                html += '<ul class="question-list">';
                
                candidateQuestions.forEach(question => {
                    html += `<li>${escapeHTML(question)}</li>`;
        });
        
                html += '</ul>';
                html += '</div>';
            }
        }
        
        html += '</div></div>';
        
        responseSummaryBox.innerHTML = html;
        currentAnalysisElement = responseSummaryBox.querySelector('.card');
    }
    
    // Helper function to safely escape HTML
    function escapeHTML(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    // New processResponse function
    function processResponse(transcript, metadata = {}) {
        console.log("Processing response:", transcript, "with metadata:", metadata);
        
        if (!transcript || transcript.trim() === '') {
            console.warn("Empty transcript received, skipping processing");
            return;
    }
    
        // Show loading indicator
        showProcessingIndicator();

        // Get the current question
        const currentQuestion = questionsData.questions[currentQuestionIndex - 1];
        
        // Determine question type
        let questionType = "default";
        if (currentQuestionIndex === 1) {
            questionType = "introduction";
        } else if (currentQuestionIndex === questionsData.questions.length) {
            questionType = "closing";
        }
        
        // Create body for the API request
        const requestBody = {};
    }
    
    // Helper function for showing alerts to the user
    function alertUser(message, type = "info") {
        // Use addStatusMessage which already exists in the code
        addStatusMessage(message, type);
    }

    // Helper function for enabling the next button (if exists)
    function enableNextButton() {
        const nextButton = document.getElementById('nextButton');
        if (nextButton) {
            nextButton.disabled = false;
            }
    }

    // Function to show processing indicator
    function showProcessingIndicator() {
        console.log("DEBUG: Showing processing indicator");
        processingIndicator.classList.add('show');
    }

    // Function to hide processing indicator
    function hideProcessingIndicator() {
        console.log("DEBUG: Hiding processing indicator");
        processingIndicator.classList.remove('show');
    }

    // Function to render responsibilities with tags
    function renderTaggedResponsibilities(taggedResponsibilities) {
        console.log("Inside renderTaggedResponsibilities function with:", taggedResponsibilities);
        
        if (!taggedResponsibilities || !Array.isArray(taggedResponsibilities)) {
            console.error('Invalid tagged responsibilities data:', taggedResponsibilities);
            return;
        }
        
        const respList = document.getElementById('jobResponsibilitiesList');
        if (!respList) {
            console.error('Could not find jobResponsibilitiesList element');
            return;
        }
        
        respList.innerHTML = '';
        
        try {
            // First, add the Position Summary section
            const positionSummaryHeader = document.createElement('div');
            positionSummaryHeader.className = 'competency-header';
            positionSummaryHeader.textContent = 'Position Summary';
            respList.appendChild(positionSummaryHeader);
            
            // Get position summary from job posting data (if available)
            let positionSummary = "Position summary text will appear here when job description is processed.";
            
            // Try to get summary from SESSION_STORE
            try {
                if (window.SESSION_STORE && 
                    window.SESSION_STORE.job_posting && 
                    window.SESSION_STORE.job_posting.position_summary) {
                    positionSummary = window.SESSION_STORE.job_posting.position_summary;
                } else if (window.SESSION_STORE && 
                    window.SESSION_STORE.job_posting && 
                    window.SESSION_STORE.job_posting.job_data && 
                    window.SESSION_STORE.job_posting.job_data.summary) {
                    positionSummary = window.SESSION_STORE.job_posting.job_data.summary;
                }
            } catch (e) {
                console.error("Error accessing position summary:", e);
            }
            
            // Create position summary element
            const summaryItem = document.createElement('div');
            summaryItem.className = 'responsibility-item position-summary';
            
            // Create summary text
            const summaryText = document.createElement('div');
            summaryText.className = 'responsibility-text';
            summaryText.textContent = positionSummary;
            summaryItem.appendChild(summaryText);
            
            // Add tags container for summary
            const summaryTagsContainer = document.createElement('div');
            summaryTagsContainer.className = 'tag-container';
            
            // Add some default tags for the summary
            const defaultSummaryTags = ["Role Overview"];
            
            // Add each tag for the summary
            defaultSummaryTags.forEach(tag => {
                const tagBadge = document.createElement('span');
                tagBadge.className = 'competency-tag';
                tagBadge.textContent = tag;
                summaryTagsContainer.appendChild(tagBadge);
            });
            
            summaryItem.appendChild(summaryTagsContainer);
            respList.appendChild(summaryItem);
            
            // Add a divider
            const divider = document.createElement('hr');
            divider.className = 'section-divider';
            respList.appendChild(divider);
            
            // Now add the Essential Functions section
            const essentialFunctionsHeader = document.createElement('div');
            essentialFunctionsHeader.className = 'competency-header';
            essentialFunctionsHeader.textContent = 'Essential Functions';
            respList.appendChild(essentialFunctionsHeader);
            
            console.log("Tagged responsibilities to render:", taggedResponsibilities);
            
            // List all responsibilities/requirements with their tags
            taggedResponsibilities.forEach(item => {
                if (!item || typeof item !== 'object') {
                    console.warn("Invalid responsibility item:", item);
                    return; // Skip invalid items
                }
                
                const respItem = document.createElement('div');
                respItem.className = 'responsibility-item';
                
                // Create responsibility text
                const respText = document.createElement('div');
                respText.className = 'responsibility-text';
                respText.textContent = item.responsibility || '';
                respItem.appendChild(respText);
                
                // Add tags container
                const tagsContainer = document.createElement('div');
                tagsContainer.className = 'tag-container';
                
                // Get the tags safely
                let tags = [];
                if (item.tags && Array.isArray(item.tags)) {
                    tags = item.tags;
                } else {
                    console.warn("No tags found for responsibility:", item.responsibility);
                    tags = ["General"]; // Add a default tag if none provided
                }
                
                // Add each tag
                tags.forEach(tag => {
                    if (tag && typeof tag === 'string') {
                        const tagBadge = document.createElement('span');
                        tagBadge.className = 'competency-tag';
                        tagBadge.textContent = tag;
                        tagsContainer.appendChild(tagBadge);
                    }
                });
                
                respItem.appendChild(tagsContainer);
                respList.appendChild(respItem);
            });
        } catch (error) {
            console.error('Error rendering tagged responsibilities:', error);
            respList.innerHTML = '<div class="alert alert-danger">Error displaying job responsibilities</div>';
        }
    }

    // Expose key functions to the global scope for integration with other scripts
    window.addSelectedQuestion = addSelectedQuestion;
    window.askQuestion = askQuestion;
    window.startRecording = startInterview;  // Alias for compatibility
    window.stopRecording = stopInterview;    // Alias for compatibility 
    window.addStatusMessage = addStatusMessage;
    window.analyzeResponse = analyzeResponse;
    window.renderTaggedResponsibilities = renderTaggedResponsibilities;  // Expose this function as well

    // Add a function to create mock analysis when needed
    function createMockAnalysis(question, response, questionType) {
        console.log("Creating mock analysis for:", questionType);
        const mockData = {
            success: true,
            question: question,
            transcript: response,
            question_type: questionType
        };
        
        // Generate different bullet points based on question type
        if (questionType === 'introduction') {
            mockData.bullet_points = [
                "The candidate introduced their background and professional experience.",
                "They highlighted their key skills and qualifications relevant to the position.",
                "They discussed their career trajectory and major achievements."
            ];
        } else if (questionType === 'closing') {
            mockData.bullet_points = [
                "The candidate asked thoughtful questions about the role and company.",
                "They demonstrated interest in understanding more about the team dynamics.",
                "They inquired about next steps in the interview process."
            ];
            mockData.candidate_questions = [
                "What metrics would you use to measure success in this role?",
                "Can you tell me more about the team I would be working with?",
                "What are the next steps in the interview process?"
            ];
        } else if (questionType === 'competency') {
            mockData.bullet_points = [
                "The candidate described a relevant situation that demonstrated their skills.",
                "They outlined the specific actions they took to address the challenge.",
                "They explained the positive results and impact of their actions."
            ];
        } else {
            mockData.bullet_points = [
                "The candidate provided a comprehensive response to the question.",
                "They shared specific examples from their experience.",
                "They demonstrated relevant skills and knowledge for the position."
            ];
        }
        
        return mockData;
    }

    // Add utility function to test API endpoint manually
    function testAnalysisEndpoint() {
        console.log("Testing analysis endpoint...");
        
        // Sample test data
        const testData = {
            question: "Walk me through your resume.",
            transcript: "I have a background in finance with 5 years of experience at JP Morgan. I worked on risk analysis and investment strategies for major clients. Prior to that, I completed my MBA from NYU with a focus on financial markets. I'm skilled in financial modeling, Excel, and have experience with Bloomberg Terminal.",
            question_type: "introduction",
            competency: "Introduction"
        };
        
        // Check which endpoint is available
        const endpoints = [
            '/api/analyze_response_star',
            '/analyze-response',
            '/api/analyze-response',
            '/api/summarize_response'
        ];
        
        // Try each endpoint
        Promise.all(endpoints.map(endpoint => 
            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            })
            .then(response => {
                return { endpoint, status: response.status, ok: response.ok };
            })
            .catch(error => {
                return { endpoint, error: error.message, ok: false };
            })
        ))
        .then(results => {
            console.log("API endpoint test results:", results);
            
            // Find working endpoints
            const workingEndpoints = results.filter(r => r.ok);
            if (workingEndpoints.length > 0) {
                console.log("Working endpoints:", workingEndpoints);
                // Use the first working endpoint for a full test
                return fetch(workingEndpoints[0].endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(testData)
                })
                .then(response => response.json());
            } else {
                throw new Error("No working analysis endpoints found");
            }
        })
        .then(data => {
            console.log("Analysis API test successful. Response data:", data);
            alertUser("API endpoint test successful. Check console for details.", "success");
        })
        .catch(error => {
            console.error("Analysis API test failed:", error);
            alertUser("API endpoint test failed: " + error.message, "danger");
        });
    }

    // Expose the test function globally for debug purposes
    window.testAnalysisEndpoint = testAnalysisEndpoint;

    // Add a function to process transcript and trigger analysis
    function processTranscript() {
        // Get the current transcript
        const transcriptText = document.getElementById('transcriptText').value;
        
        // Check if transcript is empty
        if (!transcriptText || transcriptText.trim() === '') {
            // Show warning if empty
            const warningBox = document.getElementById('warningBox');
            if (warningBox) {
                warningBox.innerHTML = '<div class="alert alert-warning">No response detected. Please ensure there is a response to analyze.</div>';
                warningBox.style.display = 'block';
                setTimeout(() => {
                    warningBox.style.display = 'none';
                }, 3000);
            }
            return;
        }
        
        // Analyze the transcript
        analyzeResponse(transcriptText, (success, analysis) => {
            if (success) {
                // If successful, update UI elements
                const analysisContainer = document.getElementById('analysisContainer');
                if (analysisContainer) {
                    analysisContainer.style.display = 'block';
                }
                
                // If this is finalizing a response (moving to next question)
                if (this.id === 'finalizeResponseBtn') {
                    // Store the finalized response
                    finalizeCurrentResponse(transcriptText, analysis);
                    
                    // Clear the transcript for the next question
                    document.getElementById('transcriptText').value = '';
                    
                    // Move to the next question if available
                    moveToNextQuestion();
                }
            } else {
                // Handle analysis failure
                const errorBox = document.getElementById('errorBox');
                if (errorBox) {
                    errorBox.innerHTML = '<div class="alert alert-danger">Failed to analyze response. Please try again.</div>';
                    errorBox.style.display = 'block';
                    setTimeout(() => {
                        errorBox.style.display = 'none';
                    }, 3000);
                }
            }
        });
    }

    // Function to finalize the current response
    function finalizeCurrentResponse(transcript, analysis) {
        // Store the transcript and analysis for the current question
        const activeQuestion = document.querySelector('#selected_questions_box .selected-question-item.active');
        if (!activeQuestion) {
            return;
        }
        
        const questionNumber = activeQuestion.getAttribute('data-question-index');
        
        // Store the data
        if (window.interviewData && window.interviewData.questions) {
            window.interviewData.questions[questionNumber] = {
                transcript: transcript,
                analysis: analysis,
                timestamp: new Date().toISOString()
            };
        }
        
        // Mark this question as completed
        activeQuestion.classList.add('completed');
        
        // Clear the transcript for the next question
        document.getElementById('transcriptText').value = '';
        
        // Move to the next question if available
        moveToNextQuestion();
    }

    // Update the analyze button event handler
    document.getElementById('analyzeResponseBtn').addEventListener('click', function() {
        processTranscript();
    });

    // Update the voice record button if it exists
    const voiceRecordBtn = document.getElementById('voiceRecordBtn');
    if (voiceRecordBtn) {
        voiceRecordBtn.addEventListener('click', function() {
            toggleRecording();
        });
    }

    // Update the finalize response button if it exists
    const finalizeResponseBtn = document.getElementById('finalizeResponseBtn');
    if (finalizeResponseBtn) {
        finalizeResponseBtn.addEventListener('click', function() {
            processTranscript();
        });
    }

    // Function to handle recording toggle
    function toggleRecording() {
        const recordBtn = document.getElementById('voiceRecordBtn');
        if (!recordBtn) return;
        
        if (recordBtn.dataset.recording === 'true') {
            // Stop recording
            stopRecording();
            recordBtn.dataset.recording = 'false';
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
            recordBtn.classList.remove('btn-danger');
            recordBtn.classList.add('btn-primary');
            
            // Process the transcript after stopping recording
            processTranscript();
        } else {
            // Start recording
            startRecording();
            recordBtn.dataset.recording = 'true';
            recordBtn.innerHTML = '<i class="fas fa-stop-circle"></i> Stop Recording';
            recordBtn.classList.remove('btn-primary');
            recordBtn.classList.add('btn-danger');
        }
    }

    // Function to process the transcript
    function processTranscript(buttonId) {
        console.log("Processing transcript from button:", buttonId);
        
        // Get the transcript from the input
        const transcriptTextElement = document.getElementById('transcriptText');
        if (!transcriptTextElement) {
            console.error("Transcript text element not found");
            return;
        }
        
        const transcript = transcriptTextElement.value.trim();
        
        // Check if transcript is empty
        if (!transcript) {
            // Define showWarningMessage function if it doesn't exist
            if (typeof showWarningMessage !== 'function') {
                function showWarningMessage(message) {
                    const warningBox = document.getElementById('warningBox');
                    if (warningBox) {
                        warningBox.innerHTML = `<div class="alert alert-warning">${message}</div>`;
                        warningBox.style.display = 'block';
                        setTimeout(() => {
                            warningBox.style.display = 'none';
                        }, 3000);
                    } else {
                        console.warn(message);
                    }
                }
                // Add to global scope for reuse
                window.showWarningMessage = showWarningMessage;
            }
            
            showWarningMessage("Please provide a transcript before analyzing.");
            return;
        }
        
        // Determine if this is for introduction, closing, or a standard question
        let questionType = 'standard';
        const activeQuestion = document.querySelector('#selected_questions_box .selected-question-item.active');
        const questionNumber = activeQuestion ? activeQuestion.getAttribute('data-question-index') : '';
        const questionText = activeQuestion ? activeQuestion.getAttribute('data-question') : '';
        
        // Check if this is the first question (introduction)
        if (questionNumber === '1') {
            questionType = 'introduction';
        }
        
        // Check if this might be a closing question
        if (questionText.toLowerCase().includes('questions for me') || 
            questionText.toLowerCase().includes('any questions')) {
            questionType = 'closing';
        }
        
        // Analyze the response
        analyzeResponse(transcript, questionType);
        
        // If the button clicked is the "Finalize and Move to Next" button, finalize this response
        if (buttonId === 'finalizeResponseBtn') {
            finalizeCurrentResponse(transcript);
        }
    }

    // Function to create a fallback analysis when API fails
    function createFallbackAnalysis(transcript, questionType, competency, questionNumber) {
        console.log("Creating fallback analysis for question type:", questionType);
        
        // Create a basic structure for the analysis
        const fallbackAnalysis = {
            bullet_points: [
                "This is a simplified analysis as our detailed analysis service encountered an issue.",
                "Your response was " + transcript.split(' ').length + " words long.",
                "Consider reviewing this response in more detail after the interview."
            ],
            overall_score: 3,
            question_number: questionNumber || '0',
            question_type: questionType || 'standard',
            competency: competency || '',
            star_elements: {
                situation: "We couldn't analyze the situation component of your response.",
                task: "We couldn't analyze the task component of your response.",
                action: "We couldn't analyze the action component of your response.",
                result: "We couldn't analyze the result component of your response."
            }
        };
        
        // Add candidate questions for closing type questions
        if (questionType === 'closing') {
            fallbackAnalysis.candidate_questions = [
                "What are the next steps in the interview process?",
                "Can you tell me more about the team I would be working with?",
                "What does success look like in this role within the first 90 days?"
            ];
        }
        
        return fallbackAnalysis;
    }

    // Function to move to the next question
    function moveToNextQuestion() {
        // Get the current active question
        const activeQuestion = document.querySelector('#selected_questions_box .selected-question-item.active');
        if (!activeQuestion) {
            return;
        }
        
        // Find the next question
        let nextQuestion = activeQuestion.nextElementSibling;
        while (nextQuestion && !nextQuestion.classList.contains('selected-question-item')) {
            nextQuestion = nextQuestion.nextElementSibling;
        }
        
        // If there is a next question, activate it
        if (nextQuestion) {
            activeQuestion.classList.remove('active');
            nextQuestion.classList.add('active');
            
            // Update the current question display
            updateCurrentQuestionDisplay(nextQuestion);
            
            // Clear the transcript and analysis for the new question
            const transcriptTextElement = document.getElementById('transcriptText');
            if (transcriptTextElement) {
                transcriptTextElement.value = '';
            }
            
            // Clear the current analysis display
            clearAnalysisDisplay();
        } else {
            // If there are no more questions, show the interview completion
            showInterviewCompletion();
        }
    }

    // Function to clear the analysis display
    function clearAnalysisDisplay() {
        const analysisContainer = document.getElementById('analysisContainer');
        if (analysisContainer) {
            // Remove all current analysis cards
            const currentAnalysisCards = analysisContainer.querySelectorAll('.analysis-card');
            currentAnalysisCards.forEach(card => {
                card.remove();
            });
        }
    }

    // Function to update the current question display
    function updateCurrentQuestionDisplay(questionElement) {
        if (!questionElement) {
            return;
        }
        
        const questionText = questionElement.getAttribute('data-question');
        const questionIndex = questionElement.getAttribute('data-question-index');
        const competency = questionElement.getAttribute('data-competency') || '';
        
        // Update the current question display
        const currentQuestionElement = document.getElementById('currentQuestion');
        if (currentQuestionElement) {
            currentQuestionElement.textContent = `Q${questionIndex}: ${questionText}`;
        }
        
        // Update the competency display if available
        const competencyElement = document.getElementById('currentCompetency');
        if (competencyElement && competency) {
            competencyElement.textContent = competency;
            competencyElement.style.display = 'block';
        }
    }

    // API Configuration functionality
    function loadApiKeyStatus() {
        fetch('/api/get_api_key_status')
            .then(response => response.json())
            .then(data => {
                // Update UI to show API key status
                const configButton = document.querySelector('[data-bs-target="#configModal"]');
                if (data.openai_configured && data.aws_configured) {
                    configButton.classList.remove('btn-outline-secondary');
                    configButton.classList.add('btn-outline-success');
                    configButton.innerHTML = '<i class="fas fa-check-circle"></i> API Keys Configured';
                } else if (data.openai_configured) {
                    configButton.classList.remove('btn-outline-secondary');
                    configButton.classList.add('btn-outline-warning');
                    configButton.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Partial Configuration';
                } else {
                    configButton.classList.remove('btn-outline-success', 'btn-outline-warning');
                    configButton.classList.add('btn-outline-secondary');
                    configButton.innerHTML = '<i class="fas fa-cog"></i> Configure API Keys';
                }
                
                // Set AWS region in dropdown
                const regionSelect = document.getElementById('awsRegion');
                if (regionSelect) {
                    regionSelect.value = data.aws_region || 'us-east-1';
                }
            })
            .catch(error => {
                console.error('Error loading API key status:', error);
            });
    }

    // Save API configuration
    function saveApiConfiguration() {
        const openaiKey = document.getElementById('openaiApiKey').value.trim();
        const awsAccessKey = document.getElementById('awsAccessKey').value.trim();
        const awsSecretKey = document.getElementById('awsSecretKey').value.trim();
        const awsRegion = document.getElementById('awsRegion').value;

        const configData = {
            openai_api_key: openaiKey,
            aws_access_key_id: awsAccessKey,
            aws_secret_access_key: awsSecretKey,
            aws_region: awsRegion
        };

        // Show loading state
        const saveButton = document.getElementById('saveConfig');
        const originalText = saveButton.textContent;
        saveButton.textContent = 'Saving...';
        saveButton.disabled = true;

        fetch('/api/set_api_keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(configData)
        })
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('configStatus');
            if (data.success) {
                statusDiv.className = 'alert alert-success';
                statusDiv.textContent = 'Configuration saved successfully!';
                statusDiv.style.display = 'block';
                
                // Clear sensitive fields
                document.getElementById('openaiApiKey').value = '';
                document.getElementById('awsAccessKey').value = '';
                document.getElementById('awsSecretKey').value = '';
                
                // Update the configure button status
                loadApiKeyStatus();
                
                // Auto-close modal after 2 seconds
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('configModal'));
                    modal.hide();
                }, 2000);
            } else {
                statusDiv.className = 'alert alert-danger';
                statusDiv.textContent = 'Error: ' + (data.error || 'Failed to save configuration');
                statusDiv.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error saving configuration:', error);
            const statusDiv = document.getElementById('configStatus');
            statusDiv.className = 'alert alert-danger';
            statusDiv.textContent = 'Network error occurred while saving configuration';
            statusDiv.style.display = 'block';
        })
        .finally(() => {
            // Restore button state
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        });
    }

    // Event listeners for configuration modal
    document.getElementById('saveConfig').addEventListener('click', saveApiConfiguration);
    
    // Add test API button handler
    document.getElementById('testApiKeys').addEventListener('click', async function() {
        const statusDiv = document.getElementById('configStatus');
        statusDiv.className = 'alert alert-info';
        statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing API connections...';
        statusDiv.style.display = 'block';
        
        try {
            const response = await fetch('/api/test_api_keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const results = await response.json();
            
            let statusHTML = '<h6>API Test Results:</h6><ul class="mb-0">';
            
            // Check OpenAI
            if (results.openai.configured) {
                if (results.openai.working) {
                    statusHTML += '<li class="text-success"><i class="fas fa-check"></i> OpenAI API: Working</li>';
                } else {
                    statusHTML += `<li class="text-danger"><i class="fas fa-times"></i> OpenAI API: ${results.openai.error || 'Failed'}</li>`;
                }
            } else {
                statusHTML += '<li class="text-warning"><i class="fas fa-exclamation"></i> OpenAI API: Not configured</li>';
            }
            
            // Check AWS
            if (results.aws.configured) {
                if (results.aws.working) {
                    statusHTML += '<li class="text-success"><i class="fas fa-check"></i> AWS/Database: Working</li>';
                } else {
                    statusHTML += `<li class="text-danger"><i class="fas fa-times"></i> AWS/Database: ${results.aws.error || 'Failed'}</li>`;
                }
            } else {
                statusHTML += '<li class="text-warning"><i class="fas fa-exclamation"></i> AWS/Database: Not configured</li>';
            }
            
            statusHTML += '</ul>';
            
            statusDiv.className = 'alert ' + (
                (results.openai.working && results.aws.working) ? 'alert-success' :
                (results.openai.working || results.aws.working) ? 'alert-warning' : 'alert-danger'
            );
            statusDiv.innerHTML = statusHTML;
        } catch (error) {
            statusDiv.className = 'alert alert-danger';
            statusDiv.innerHTML = `<i class="fas fa-times"></i> Error testing APIs: ${error.message}`;
        }
    });
    
    // Clear status when modal is opened
    document.getElementById('configModal').addEventListener('show.bs.modal', function() {
        const statusDiv = document.getElementById('configStatus');
        statusDiv.style.display = 'none';
    });

    // Load API key status on page load
    loadApiKeyStatus();

    // ========== Nova Sonic Integration ==========
    
    async function initializeNovaSession() {
        try {
            const response = await fetch('/api/get-nova-credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            if (data.session_id) {
                novaSessionId = data.session_id;
                isNovaInitialized = true;
                console.log('Nova session initialized:', novaSessionId);
                
                // Update UI to show Nova is ready
                updateRecordingIndicator('Nova Ready', 'text-success');
                
                return true;
            } else {
                throw new Error('Failed to initialize Nova session');
            }
        } catch (error) {
            console.error('Error initializing Nova session:', error);
            updateRecordingIndicator('Nova Error', 'text-danger');
            return false;
        }
    }
    
    async function startNovaTranscription() {
        if (!isNovaInitialized) {
            console.log('Initializing Nova session...');
            const initialized = await initializeNovaSession();
            if (!initialized) {
                throw new Error('Failed to initialize Nova session');
            }
        }
        
        try {
            // Get user media for audio recording
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                } 
            });
            
            // Set up MediaRecorder for capturing audio chunks
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm; codecs=opus'
            });
            
            let audioChunks = [];
            
            mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                    
                    // Convert to base64 and send to Nova
                    const audioBlob = new Blob([event.data], { type: 'audio/webm' });
                    const reader = new FileReader();
                    reader.onloadend = async () => {
                        const base64Audio = reader.result.split(',')[1];
                        await sendAudioToNova(base64Audio);
                    };
                    reader.readAsDataURL(audioBlob);
                }
            };
            
            // Start recording with 1-second intervals for real-time processing
            mediaRecorder.start(1000);
            
            // Store reference for stopping later
            window.novaMediaRecorder = mediaRecorder;
            window.novaStream = stream;
            
            console.log('Nova transcription started');
            updateRecordingIndicator('Recording...', 'text-danger');
            
        } catch (error) {
            console.error('Error starting Nova transcription:', error);
            throw error;
        }
    }
    
    async function sendAudioToNova(base64Audio) {
        if (!novaSessionId) return;
        
        try {
            const response = await fetch('/api/nova-real-time-diarization', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: novaSessionId,
                    audio_chunk: base64Audio,
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            if (data.success && data.diarization) {
                processNovaTranscription(data.diarization);
            }
        } catch (error) {
            console.error('Error sending audio to Nova:', error);
        }
    }
    
    function processNovaTranscription(diarization) {
        if (!diarization.speakers || diarization.speakers.length === 0) return;
        
        // Process each speaker segment
        diarization.speakers.forEach(speaker => {
            if (speaker.transcript && speaker.transcript.trim()) {
                const speakerRole = speaker.speaker_role || 'Unknown';
                const transcript = speaker.transcript;
                const confidence = speaker.confidence || 0;
                const emotions = speaker.emotions || {};
                
                // Update the transcript display
                updateTranscriptDisplay(speakerRole, transcript, confidence, emotions);
                
                // If this is candidate speech, trigger analysis
                if (speakerRole === 'candidate' && transcript.length > 50) {
                    debounceAnalysis(transcript);
                }
            }
        });
    }
    
    function updateTranscriptDisplay(speaker, text, confidence, emotions) {
        const transcriptBox = document.getElementById('candidate_transcript_box');
        if (!transcriptBox) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const emotionBadges = emotions ? Object.entries(emotions)
            .filter(([_, value]) => value > 0.5)
            .map(([emotion, value]) => `<span class="badge bg-info">${emotion}: ${(value * 100).toFixed(0)}%</span>`)
            .join(' ') : '';
        
        const entry = document.createElement('div');
        entry.className = `transcript-entry ${speaker.toLowerCase()}`;
        entry.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-1">
                <span class="fw-bold text-${speaker === 'candidate' ? 'primary' : 'secondary'}">${speaker}:</span>
                <small class="text-muted">${timestamp} (${(confidence * 100).toFixed(0)}%)</small>
            </div>
            <div class="transcript-text">${text}</div>
            ${emotionBadges ? `<div class="mt-1">${emotionBadges}</div>` : ''}
        `;
        
        transcriptBox.appendChild(entry);
        transcriptBox.scrollTop = transcriptBox.scrollHeight;
    }
    
    function stopNovaTranscription() {
        if (window.novaMediaRecorder) {
            window.novaMediaRecorder.stop();
            window.novaMediaRecorder = null;
        }
        
        if (window.novaStream) {
            window.novaStream.getTracks().forEach(track => track.stop());
            window.novaStream = null;
        }
        
        updateRecordingIndicator('Stopped', 'text-muted');
        console.log('Nova transcription stopped');
    }
    
    function updateRecordingIndicator(text, className) {
        const indicator = document.getElementById('recordingIndicator');
        if (indicator) {
            indicator.textContent = text;
            indicator.className = className;
        }
    }
    
    // Debounced analysis to avoid too many API calls
    let analysisTimeout;
    function debounceAnalysis(transcript) {
        clearTimeout(analysisTimeout);
        analysisTimeout = setTimeout(() => {
            if (currentQuestion) {
                analyzeResponse(transcript, currentQuestion);
            }
        }, 2000);
    }
    
    // Nova integration is handled in the existing start/stop event listeners above
}); 