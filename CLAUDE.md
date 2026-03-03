# Repository Analyzer API - Backend Gitzy

## Overview
FastAPI backend that searches and analyzes code repositories across GitHub, GitLab, and Azure DevOps. Uses cookie-based session persistence (in-memory, not DB).

## Tech Stack
- **Python 3.14** / **FastAPI** / **Pydantic v2** / **httpx** (async HTTP)
- Dependencies in `requeriments.text` (not requirements.txt)
- No database — sessions stored in RAM (`sessions_store` dict)

## Run
```bash
pip install -r requeriments.text
uvicorn app.main:app --reload
```

## Project Structure
```
app/
├── main.py                    # FastAPI app + CORS config
├── core/config.py             # Settings from .env (tokens, cookie config)
├── models/
│   ├── request_models.py      # SearchRequest, SearchFilters, enums
│   └── response_models.py     # SearchResponse, SessionResponse, etc.
├── routers/repository.py      # 3 endpoints: /search, /session, /analyze
├── services/
│   ├── session_service.py     # In-memory session management (UUID cookies)
│   ├── github_search_service.py  # GitHub Search API + filter qualifiers
│   ├── github_service.py      # GitHub repo detail (analyze endpoint)
│   ├── gitlab_service.py      # GitLab Projects API + language post-filter
│   ├── azure_service.py       # Stub (returns empty)
│   └── provider_detector.py   # URL parser → detect github/gitlab/azure
└── utils/http_client.py       # Async HTTP GET wrapper
```

## Endpoints
- `POST /repository/search` — Multi-provider search with optional filters
- `GET /repository/session` — Get session data (last search, results, filters)
- `POST /repository/analyze` — Detailed analysis of a single repo by URL

## Search Filters
`POST /repository/search` accepts optional `filters` in the request body:

| Filter | Type | Valid Values |
|--------|------|-------------|
| `language` | enum | `Python`, `JavaScript`, `TypeScript`, `Java`, `Go`, `Rust`, `C++`, `C`, `C#`, `Ruby`, `PHP`, `Swift`, `Kotlin` |
| `category` | enum | `Library`, `Framework`, `Application`, `Tool`, `API` |
| `topic` | string | Free text (e.g., `"machine-learning"`, `"react"`, `"docker"`) |

- Max 3 filters at once. All optional. Omit or send `null` (not `""`).
- `category` maps to GitHub/GitLab topics internally via `CATEGORY_TO_TOPICS` dict.
- GitHub: filters become query qualifiers (`language:Python`, `topic:framework`).
- GitLab: `topic` is native param; `language` requires post-filtering via `/projects/:id/languages`.

## Branches
- `main` — Production config (CORS from env vars, secure cookies, docs disabled)
- `dev` — Development config (localhost CORS, lax cookies, Swagger enabled)

## Key Patterns
- Cookies: `httponly=True`, `secure=True`, `samesite="none"` (main branch)
- CORS origins configured via `ALLOWED_ORIGINS` env var (comma-separated)
- Swagger docs disabled when `ENVIRONMENT=production`
- `SECRET_KEY` must be set in production (no insecure default)

## Environment Variables (.env)
```
GITHUB_TOKEN=       # Required for GitHub API (5000 req/hr vs 60)
GITLAB_TOKEN=       # Optional
AZURE_TOKEN=        # Optional
SECRET_KEY=         # Required in production
ALLOWED_ORIGINS=    # Comma-separated frontend URLs
ENVIRONMENT=        # "production" disables /docs
```

## Important Notes
- `.env` is in `.gitignore` — never commit tokens
- Sessions are lost on server restart (in-memory only)
- Azure service is a stub (returns empty list)
- GitLab search doesn't return language natively — uses async parallel calls to `/projects/:id/languages` when language filter is active
