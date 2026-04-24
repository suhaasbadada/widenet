# WideNet

AI-powered job application copilot — FastAPI + PostgreSQL backend.

---

## Overview

WideNet automates the repetitive parts of job searching. Upload a resume, add a job description, and instantly generate tailored application answers, cover letters, cold outreach emails, and an ATS-optimized resume. Everything is tied to applications and stored per user.

---

## Stack

- **Runtime**: Python 3.12, FastAPI
- **Database**: PostgreSQL (Supabase)
- **AI**: Groq (llama-3.3-70b-versatile)
- **Storage**: Supabase Storage
- **Auth**: JWT (HS256), PBKDF2-HMAC-SHA256 password hashing

---

## Authorization Model

All users have a persisted `role` field in the database: `user` or `admin`.

- Role is included in the JWT on login
- `get_current_user` resolves the caller from DB on every protected request
- `require_admin` dependency enforces admin-only access at the route level

| Access level | Who | How to get it |
|---|---|---|
| Public | Anyone | No token needed |
| Authenticated | Registered users | Bearer JWT from login |
| Admin | Admin users | Email listed in `ADMIN_EMAILS`, then re-login |

---

## API Reference

All routes are prefixed `/api/v1`.

### Auth

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Register and receive a JWT |
| POST | `/auth/login` | Public | Login and receive a JWT |
| POST | `/auth/logout` | Authenticated | Stateless logout (discard token client-side) |

`POST /auth/register` requires `name`, and `users.name` is persisted as a non-null field.

### Users

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/users/me` | Authenticated | Fetch own record |
| PUT | `/users/me` | Authenticated | Update own name and/or email |
| GET | `/users` | Admin | List all users |
| GET | `/users/{user_id}` | Admin | Fetch a user by id |
| POST | `/users` | Admin | Provision a user directly (name required) |
| PUT | `/users/{user_id}` | Admin | Update a user's name, email, or role |
| DELETE | `/users/{user_id}` | Admin | Delete a user (cascades to related records) |

### Resume Upload

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/upload/resume` | Authenticated | Upload PDF or DOCX — extracts text, runs AI parse, stores profile |

### Resumes

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/resumes/me` | Authenticated | Fetch latest stored resume/profile |
| POST | `/resumes/generate` | Authenticated | Generate an ATS-tailored, render-ready resume JSON from stored profile and a JD |
| POST | `/resumes/generate-file` | Authenticated | One-click generate and directly download tailored DOCX or PDF from JD |
| POST | `/resumes/render-file` | Authenticated | Alias of generate-file; returns PDF when output_format is omitted |
| POST | `/resumes/render-docx` | Authenticated | Render resume JSON to a downloadable DOCX file |
| POST | `/resumes/render-pdf` | Authenticated | Render resume JSON to a downloadable PDF file |

`/resumes/generate` now returns:
- `resume_json`: directly consumable by `/resumes/render-docx` and `/resumes/render-pdf`
- `render_docx_payload`: request body ready to POST to `/resumes/render-docx`
- `render_pdf_payload`: request body ready to POST to `/resumes/render-pdf`

If the stored profile is missing render-critical fields (`name`, `contact_number`, `links`, `projects`, `education`), pass `profile_overrides` in `/resumes/generate` to fill them.

One-click flow via `/resumes/generate-file`:
- Send `job_description` + `output_format` (`docx` or `pdf`)
- Optionally include `profile_overrides`
- API responds with the generated file directly (no second render call needed)

### Profiles

| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/profiles/{user_id}` | Public | Fetch structured profile for a user |
| PATCH | `/profiles/me` | Authenticated | Persist updates to latest profile fields (name, contact_number, links, structured profile fields) |
| PUT | `/profiles/{user_id}/refresh` | Public | Re-parse and update profile from stored raw resume |

`PATCH /profiles/me` supports normalized links using:
- `{ "type": "linkedin|github|portfolio|website|email|other", "url": "...", "is_primary": true|false }`
- Legacy `links: ["https://..."]` remains supported and is auto-normalized into `profile_links`.

### Jobs

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/jobs` | Authenticated | Create a job |
| GET | `/jobs` | Authenticated | List all jobs |
| GET | `/jobs/{job_id}` | Authenticated | Fetch a job by id |

### Applications

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/applications` | Authenticated | Create an application (links user to a job) |
| GET | `/applications` | Authenticated | List applications |
| GET | `/applications/{application_id}` | Authenticated | Fetch an application by id |
| PUT | `/applications/{application_id}` | Authenticated | Update application status |

### Answers

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/answers/generate` | Authenticated | Generate a tailored answer to a job application question |

### Outreach

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/outreach/cover-letter` | Authenticated | Generate a cover letter tailored to a job |
| POST | `/outreach/cold-email` | Authenticated | Generate a cold recruiter outreach email |
| POST | `/outreach/copilot` | Authenticated | Unified AI copilot — generates answer, cover letter, or outreach in one call |

### Job Match

| Method | Path | Access | Description |
|---|---|---|---|
| POST | `/job-match/match` | Authenticated | Score and rank job listings against a user profile |

---

## API Response Format

Most JSON endpoints return a consistent envelope:

```json
{ "success": true, "data": {} }
{ "success": false, "error": "message" }
```

Exception: file download routes (`/resumes/generate-file`, `/resumes/render-file`, `/resumes/render-docx`, `/resumes/render-pdf`) return binary file responses on success.

---

## Architecture

```
apps/
  api/
    app/
      api/routes/  HTTP layer only — no business logic
      services/    All business logic and AI calls
      models/      SQLAlchemy models
      schemas/     Pydantic request/response validation
      core/        Security and authorization dependencies
      db/          Session management and startup schema sync
      utils/       File parsing utilities
  web/
    src/app/       Next.js App Router pages and layouts
    src/lib/       Frontend API client and shared browser utilities
```

---

## Out of Scope (Current Version)

- Shareable public candidate profiles
- Credit system and payments
- Chrome extension / auto-apply
- Recruiter-facing dashboards

---

## Vision

WideNet aims to become a job search operating system — combining applications, outreach, and personal branding into a single intelligent platform.
