# Amazon Nova Sonic Integration

This document provides guidance for using the new Nova Sonic speech analysis capabilities in Synergos.

## Overview

Synergos now uses Amazon Nova Sonic for advanced speech analysis, providing:

- Speaker diarization (detecting who is speaking)
- Emotional analysis of speech
- Sentiment detection
- Prosody analysis (patterns, emphasis, pace)
- Hesitation detection
- Confidence assessment

## Migration from Azure

The application has been migrated from Azure Speech Services to Amazon Nova Sonic. All speech processing now uses Nova Sonic by default. If you need to continue using Azure for a transitional period, set the `SPEECH_SERVICE` environment variable to `azure` in your `.env` file.

## New Features

### 1. Emotional Analysis

The application now analyzes the emotional aspects of interview responses, detecting:

- Emotional tone (confidence, uncertainty, enthusiasm)
- Authenticity markers
- Engagement with different topics
- Stress indicators
- Emotional congruence with content

### 2. Enhanced Evaluation Reports

Interview evaluation reports now include:

- Emotional pattern analysis
- Confidence assessment by topic
- Authenticity indicators
- Stress pattern detection
- Emphasis analysis
- Hesitation detection

### 3. Real-time Speaker Identification

Nova Sonic provides improved speaker identification capabilities:

- Register speakers at the beginning of interviews
- Automatically detect and label speakers (interviewer vs. candidate)
- Track when speakers change during the conversation

## API Endpoints

### Nova Sonic Core Endpoints

- `POST /nova/get-nova-credentials`: Get session credentials for Nova Sonic
- `POST /nova/api/register-speaker`: Register a speaker's voice profile
- `POST /nova/api/nova-real-time-diarization`: Process real-time audio with diarization
- `POST /nova/api/get-session-transcript`: Get the full transcript with speaker identification
- `POST /nova/api/analyze-speech-emotions`: Analyze speech emotions in detail

### Evaluation Endpoints with Emotional Analysis

- `POST /api/analyze_response_emotions`: Analyze emotional aspects of a response
- `POST /api/analyze_confidence`: Analyze confidence patterns in speech
- `POST /api/emotional_pattern_report`: Generate a report on emotional patterns 
- `POST /api/enhanced_interview_evaluation`: Perform evaluation with emotional analysis

## Usage Example

```javascript
// Register speakers at the beginning of the interview
async function registerSpeakers(sessionId, interviewerAudio, candidateAudio) {
  // Register interviewer
  await fetch('/nova/api/register-speaker', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      speaker_role: 'interviewer',
      sample_audio: interviewerAudio // base64 encoded audio
    })
  });
  
  // Register candidate
  await fetch('/nova/api/register-speaker', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      speaker_role: 'candidate',
      sample_audio: candidateAudio // base64 encoded audio
    })
  });
}

// Process real-time audio chunks
async function processAudioChunk(sessionId, audioChunk) {
  const response = await fetch('/nova/api/nova-real-time-diarization', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      audio_chunk: audioChunk // base64 encoded audio
    })
  });
  
  return await response.json();
}

// Generate enhanced evaluation with emotional analysis
async function generateEvaluation(sessionId) {
  // Get full transcript with emotional data
  const transcriptResponse = await fetch('/nova/api/get-session-transcript', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  
  const transcript = await transcriptResponse.json();
  
  // Send for enhanced evaluation
  const evaluationResponse = await fetch('/api/enhanced_interview_evaluation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transcript: transcript.transcript,
      emotional_data: transcript.emotional_data
    })
  });
  
  return await evaluationResponse.json();
}
```

## Environment Variables

Add these to your `.env` file:

```
# Speech service selection (nova or azure)
SPEECH_SERVICE=nova

# AWS credentials for Nova Sonic
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1

# Keep Azure keys for legacy support if needed
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=your_azure_region
``` 