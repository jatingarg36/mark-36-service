# mark-36-service

A production-ready, modular Python backend service built with FastAPI.

## Stack

| Layer | Library |
|---|---|
| Framework | FastAPI + Uvicorn |
| MongoDB ODM | Beanie + Motor (async) |
| Redis Client | `redis[asyncio]` |
| JWT | `python-jose[cryptography]` |
| OAuth | `httpx` (manual PKCE-safe flow) |
| Settings | `pydantic-settings` |
| Testing | `pytest` + `pytest-asyncio` + `httpx` |

---

## Quick Start

### 1. Local (without Docker)

```bash
# Create and activate a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Start MongoDB and Redis locally, then:
uvicorn app.main:app --reload
```

API docs available at: <http://localhost:8000/docs>

### 2. Docker Compose

```bash
cp .env.example .env
# Fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY

docker compose up --build
```

---

## Project Layout

```
app/
├── main.py                  # FastAPI entry point
├── core/
│   ├── config.py            # pydantic-settings
│   ├── security.py          # JWT + password hashing
│   ├── dependencies.py      # get_current_user FastAPI dependency
│   ├── database.py          # MongoDB / Beanie init
│   └── redis.py             # Redis client + refresh-token helpers
└── modules/
    └── auth/
        ├── router.py        # Route definitions
        ├── service.py       # Business logic
        ├── models.py        # Beanie User document
        ├── schemas.py       # Pydantic schemas
        └── oauth/
            ├── base.py      # Abstract OAuthProvider
            └── google.py    # Google OAuth 2.0
tests/
└── modules/
    └── auth/
        ├── test_router.py
        └── test_service.py
```

---

## Auth Module

### Public Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/auth/google/login` | Returns Google OAuth authorization URL |
| `GET` | `/auth/google/callback?code=…` | Handles callback, upserts user, returns tokens |
| `POST` | `/auth/refresh` | Rotates refresh token, returns new token pair |
| `POST` | `/auth/logout` | Revokes refresh token |
| `GET` | `/health` | Health check |

### Protected Endpoints *(Bearer JWT required)*

| Method | Path | Description |
|---|---|---|
| `GET` | `/users/me` | Returns current user's profile |
| `PATCH` | `/users/me` | Updates `name` or `avatar_url` |

### Token Flow

```
Client → GET /auth/google/login
       ← { authorization_url }

Client → redirect to Google → Google callback
       → GET /auth/google/callback?code=…
       ← { access_token, refresh_token }

Client → Authorization: Bearer <access_token>   (15 min lifetime)
Client → POST /auth/refresh { refresh_token }   (7-day rotation)
Client → POST /auth/logout  { refresh_token }   (immediate revocation)
```

---

## Adding a New OAuth Provider

1. Create `app/modules/auth/oauth/<provider>.py`
2. Subclass `OAuthProvider` and implement `get_authorization_url`, `exchange_code_for_token`, and `get_user_info`
3. Add a new pair of endpoints to `router.py` — no changes to `service.py` required

---

## Running Tests

```bash
pytest
```

---

## Environment Variables

See [`.env.example`](.env.example) for all required keys.
