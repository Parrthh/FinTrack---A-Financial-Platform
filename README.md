# FinTrack

A read-only market intelligence platform: track stocks, ETFs, and crypto, with
daily-scraped news classified by whether it signals genuine company progress.
Not a trading platform — no orders, no brokerage, no investment advice.

**Hard constraint: everything runs on free tiers.** No paid APIs, data feeds,
or hosting plans. Where that limits a feature (e.g. stock quotes are ~15-minute
delayed rather than real-time), the UI says so instead of pretending otherwise.

## Status — Phase 1 of 6 complete

| Phase | Scope | Status |
|---|---|---|
| 1 | Skeleton, DB schema, auth (JWT + refresh), dashboard shell | ✅ Done |
| 2 | Asset universe + price data (free provider, delayed quotes) | ⬜ |
| 3 | Watchlists + dashboard home | ⬜ |
| 4 | News scraping + LLM "progress" classification | ⬜ |
| 5 | Real-time layer (WebSocket push; crypto genuinely near-real-time) | ⬜ |
| 6 | Alerts, monitoring, security hardening, polish | ⬜ |

## Stack

- **Frontend** — Next.js (App Router, TypeScript, Tailwind CSS v4) → Vercel free tier
- **Backend** — FastAPI (Python 3.11), SQLAlchemy 2 + Alembic → Render free tier
- **Database** — PostgreSQL in production (SQLite locally for zero-setup dev);
  TimescaleDB hypertable planned for `price_history` in Phase 2
- **Auth** — email/password with bcrypt; short-lived JWT access token + rotating
  refresh token stored as an httpOnly cookie (only its SHA-256 hash is persisted)
- **Logging** — structured JSON via structlog with separate `app` / `audit` /
  `jobs` streams; security events also persisted to the `audit_log` table
- **CI** — GitHub Actions: ruff + pytest + migration check (backend),
  ESLint + build (frontend), advisory `pip-audit`

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head          # creates fintrack_dev.db (SQLite) by default
uvicorn app.main:app --reload --port 8000
```

API docs at http://localhost:8000/api/docs. Run tests with `pytest`, lint with
`ruff check .`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # points at http://localhost:8000 by default
npm run dev
```

App at http://localhost:3000.

### Configuration

Copy `.env.example` (repo root) values into `backend/.env` and
`frontend/.env.local`. Real secrets live only in the host's environment
variable manager — never in the repo.

## API (Phase 1)

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create account, returns access token + refresh cookie |
| POST | `/api/auth/login` | Log in (rate-limited per IP) |
| POST | `/api/auth/refresh` | Rotate refresh token, mint new access token |
| POST | `/api/auth/logout` | Revoke refresh token, clear cookie |
| GET | `/api/auth/me` | Current user (Bearer token) |
| GET | `/api/health` | Liveness + DB check |
| GET | `/api/status` | Job-run status page (populated from Phase 2) |

## Deployment (planned hosts, all free tier)

1. **Frontend → Vercel**: import the repo, set root directory to `frontend/`,
   set `NEXT_PUBLIC_API_URL` to the Render API URL.
2. **Backend → Render**: web service from `backend/`, build
   `pip install -r requirements.txt`, start
   `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. **Render Postgres** (free tier): set `DATABASE_URL` on the API service.
4. Backend env vars: `JWT_SECRET` (long random), `CORS_ORIGINS` (the Vercel
   URL), `REFRESH_COOKIE_SECURE=true`, `REFRESH_COOKIE_SAMESITE=none`, `ENV=prod`.

## Known Phase 1 stubs / TODOs

- Email verification is stubbed (`email_verified` set true at signup).
- Password reset flow not yet built (planned alongside email verification).
- Rate limiting is in-process; moves to Redis when the API scales past one instance.
- Landing-page ticker shows labeled sample data until Phase 2 wires real quotes.
