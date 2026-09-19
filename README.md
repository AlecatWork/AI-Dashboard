# AI Dashboard

## Overview

A Streamlit dashboard for managing tasks, backed by a FastAPI API. Users log
in, track tasks with priorities and completion status, see them summarized
on a dashboard, and can chat with an AI assistant that has visibility into
their current task list.

## Backend

The API (`backend/`) is a FastAPI app with JWT authentication and a
SQLAlchemy/SQLite database behind it. It handles:

- **Auth** — `POST /auth/register` and `POST /auth/login`, bcrypt-hashed
passwords, JWT access tokens
- **Tasks** — full CRUD under `/tasks`, scoped per user so nobody can see or
edit another user's tasks. Supports filtering by `completed` and
`priority`, plus pagination
- **Notifications** — a background task logs a notification whenever a task
is created, updated, or deleted
- **Rate limiting** — per-endpoint request limits so the API can't be
hammered
- Auto-generated docs at `/docs` if you want to poke at the API directly

The Streamlit frontend talks to it entirely through `api_client.py` — it
never touches the database directly.

## Setup

1. Install frontend dependencies:
    
    ```bash
    cd frontend
    pip install -r requirements.txt
    ```
    
2. Start the backend:
    
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
    ```
    
3. Add your secrets in `frontend/.streamlit/secrets.toml`:
    
    ```toml
    BACKEND_URL = "http://127.0.0.1:8000"
    OPENAI_API_KEY = "sk-ant-..."
    ```
    
    The AI chat works without a real key too — it falls back to a rule-based
    mock response so the app is fully usable offline.
    
4. Run the app:
    
    ```bash
    cd frontend
    streamlit run app.py
    ```
    

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Main Streamlit app — layout, tabs, session state |
| `api_client.py` | All backend + AI calls, centralized in one place |
| `requirements.txt` | Frontend dependencies |
| `.streamlit/secrets.toml` | Backend URL and AI API key (not committed) |

## Features

1. **Authentication** — login/register forms, JWT stored in session state, working logout
2. **Dashboard** — metrics row, a task table, and a priority breakdown chart
3. **Task management** — add tasks, mark complete, delete, filter by status and priority
4. **AI chat** — a chat tab that answers questions about the current task list, streamed word-by-word; uses a real LLM when an API key is configured, otherwise a mock that still reasons over the real task data
5. **Layout** — wide layout, sidebar filters, tabbed sections, loading states and error handling on every backend call

## Tips

- All backend and AI calls go through `api_client.py` — no inline `requests` calls in `app.py`
- Every `st.session_state` key is initialized up front with the `if "key" not in st.session_state` pattern
- The mock chat responses in `api_client.py` are just a fallback for working without an API key — swap in a real key in `secrets.toml` and nothing else needs to change