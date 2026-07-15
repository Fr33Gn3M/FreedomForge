# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FreedomForge is a personal automation hub with a FastAPI backend (Python) and a Naive UI admin frontend (Vue 3). The project combines two independent codebases under a single repo — backend and frontend have separate dependency management and dev servers.

## Repository Layout

```
FreedomForge/
├── backend/               # FastAPI + SQLite (Python 3.14+)
│   ├── main.py            # API entry: /token, /register, /users/me, /auth/*
│   ├── database.py        # SQLite init, user CRUD, role→access-codes mapping
│   ├── data/users.db      # SQLite database (gitignored)
│   └── common/
│       ├── models.py      # Pydantic request/response models
│       └── response.py    # ResponseModel wrapper {code, message, data}
├── frontend/              # pnpm monorepo (Vben Admin Pro v5.7)
│   └── apps/web-naive/    # The only app entrypoint (Naive UI variant)
│       ├── src/api/        # API layer: request client + auth endpoints
│       ├── src/views/      # Page components (_core/, dashboard/)
│       ├── src/store/      # Pinia auth store
│       └── src/router/     # Vue Router + access control
└── readme.md              # Human-facing project docs
```

## Common Commands

### Backend (Python)

```bash
# Install dependencies (run from backend/)
cd backend
pip install -r requirements.txt

# Dev server with hot-reload (port 8000)
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# API docs once running: http://127.0.0.1:8000/docs
```

### Frontend (Node.js / pnpm)

```bash
# Install all workspace deps (run from frontend/)
cd frontend
pnpm install

# Dev server (port 5888)
cd frontend
pnpm dev:naive         # or: pnpm -F @vben/web-naive run dev

# Lint & typecheck
cd frontend
pnpm lint
pnpm check:type
```

### Git

The repo root is `FreedomForge/` (NOT `frontend/`). All git commands should be run from the repo root.

## Architecture

### API Contract: Python Backend ↔ Vue Frontend

The Python backend returns `{ code: 200, message: "...", data: ... }` via `ResponseModel`. The frontend's request client is configured to:

- **Success detection**: `codeField: 'code'`, `successCode: 200`
- **Data extraction**: `responseReturn: 'data'` — the `data` field is auto-unwrapped
- **Auth header**: JWT token sent as `Bearer <token>` via request interceptor

When adding new API endpoints:
1. Define Pydantic models in `backend/common/models.py`
2. Add the route to `backend/main.py`, returning `ResponseModel(...)`
3. Create a frontend API function in `frontend/apps/web-naive/src/api/core/`

### Backend Auth System

- Passwords hashed with **bcrypt** via `passlib`
- JWT tokens signed with **HS256** (secret in `main.py::SECRET_KEY` — change in production)
- Token expiry: 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Role-based access codes: `ROLE_ACCESS_CODES` dict in `database.py`
  - `super`: `["*"]` (full access)
  - `admin`: dashboard + system management
  - `user`: dashboard view only

### Frontend Auth Flow

1. User logs in at `/login` → `loginApi()` calls `POST /api/token`
2. Backend returns `{access_token, token_type}` → mapped to `{accessToken}` for frontend
3. Token stored in `useAccessStore().accessToken` (Pinia)
4. All subsequent requests inject `Authorization: Bearer <token>` via request interceptor
5. On 401, `authenticateResponseInterceptor` triggers re-auth or logout

### Frontend Framework Conventions

- This is a **Vben Admin Pro** monorepo. The framework provides prefab stores, request client, layouts, and access control via `@vben/*` workspace packages.
- Path alias `#/` maps to `apps/web-naive/src/`
- Env vars prefixed with `VITE_` in `.env.development` (port 5888, API base `/api`)
- The Nitro mock server (`VITE_NITRO_MOCK`) is **disabled** — all API calls go to the real Python backend
- **UI components MUST use Naive UI library** (already installed and configured). Never use raw HTML `<input>`, `<select>`, or `<textarea>` elements — always use `NInput`, `NSelect`, `NButton`, `NTag`, `NTree`, `NSpace`, `NDataTable`, `NModal`, etc. from `naive-ui`. The project has dark theme enabled, and raw HTML elements will render white/unstyled

### Database Notes

- SQLite file at `backend/data/users.db` (auto-created on first `init_db()`)
- Schema migrations are done inline in `init_db()` via `ALTER TABLE ... ADD COLUMN` with try/except for existing columns
- Default users are NOT auto-created — register via `POST /api/register` or insert manually
