# AI Job Application & Candidate Profiling Platform

## Goal

Build a FastAPI backend that helps job seekers and recruiters by:
- Structuring resumes into clean candidate profiles
- Generating tailored job application answers
- Creating personalized recruiter outreach messages
- Tracking job applications
- Generating shareable candidate profiles

The system should act as an AI-assisted career automation backend.

---

## Core Principles

- Keep the MVP simple and functional first
- Prefer clarity over complexity
- Build features incrementally
- Everything should be API-driven
- AI outputs must be structured and usable
- Design for extensibility, but avoid overengineering early

---

## Architecture Rules

### Layers
- `api/routes/` → HTTP layer only (no business logic)
- `services/` → all business logic + AI calls
- `models/` → database models only
- `schemas/` → Pydantic request/response validation
- `db/` → database connection and session handling

### Strict Rules
- No AI calls inside routes
- No DB queries inside routes
- Services must be reusable and testable
- Always validate input using Pydantic schemas

---

## Core Entities

### User
- id
- email

### Profile
- id
- user_id
- resume_url (stored file location)
- raw_resume (extracted text)
- structured_profile (JSON)
- headline
- summary
- created_at

### Job
- title
- company
- description

### Application
- user_id
- job_id
- status

### Generated Content
- user_id
- job_id
- type (answer / outreach)
- content

---

## File Handling

- Users can upload resume files (PDF/DOCX)
- Files should be stored in Supabase Storage
- Store file URL in database (`resume_url`)
- Extract text from file and store in `raw_resume`
- AI processing must use extracted text, not raw file

Do not store binary files in the database.

## AI Features

### 1. Resume Parsing
Convert raw resume text into:
- headline
- summary
- skills
- experience (structured JSON)

### 2. Answer Generation
Generate tailored responses for job application questions using:
- user profile
- job description
- question context

### 3. Outreach Generation
Generate short, personalized recruiter messages:
- concise
- professional
- role-specific
- include a relevant subject line
- content should be crisp, meaningful, no emojis/hyphens/dashes, catchy and meaningful

---
## Service Responsibilities

### resume_service
- Handles resume upload flow
- Calls file parser
- Calls AI parsing
- Stores profile data

### ai_service
- Handles all LLM interactions
- Resume parsing
- Answer generation
- Outreach generation

### storage_service
- Uploads files to Supabase Storage
- Returns public URL

### application_service
- Handles job application tracking logic

## Output Format Rules (VERY IMPORTANT)

All AI responses MUST be structured JSON.

Examples:

Profile:
{
  "headline": "",
  "summary": "",
  "skills": [],
  "experience": []
}

Answer:
{
  "answer": ""
}

Outreach:
{
  "subject": "",
  "message": ""
}