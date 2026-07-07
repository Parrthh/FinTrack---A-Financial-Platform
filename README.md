# FinTrack - A Financial Platform

A read-only market intelligence platform: track stocks, ETFs, and crypto, with
daily-scraped news classified by whether it signals genuine company progress.
Not a trading platform — no orders, no brokerage, no investment advice.

**Hard constraint: everything runs on free tiers.** No paid APIs, data feeds,
or hosting plans. Where that limits a feature (e.g. stock quotes are ~15-minute
delayed rather than real-time), the UI says so instead of pretending otherwise.

## Status — Phase 2 of 6 complete

| Phase | Scope | Status |
|---|---|---|
| 1 | Skeleton, DB schema, auth (JWT + refresh), dashboard shell | ✅ Done |
| 2 | Asset universe + price data (free provider, delayed quotes) | ✅ Done |
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

## Market data (Phase 2)

- **Stocks/ETFs — Stooq** (free, keyless): end-of-day/delayed quotes and full
  daily history. The UI labels these as delayed; real-time stock data is a
  paid product and is deliberately out of scope.
- **Crypto — CoinGecko** (free, keyless): near-real-time prices, market caps,
  and daily history. The whole crypto universe fits one API call per refresh.
- **Universe**: a curated ~100-asset list (large caps, major ETFs, top crypto)
  in `backend/app/universe.py` — deliberately reduced to respect free-tier
  rate limits; grow it by adding rows there.
- **Scheduling**: Render's free tier has no cron/workers, so a scheduled
  GitHub Actions workflow (`.github/workflows/refresh-prices.yml`) calls the
  token-protected `/api/jobs/*` endpoints — every 30 min during market hours
  for quotes, daily for the full history backfill. Viewing an asset also
  triggers an on-demand history refresh if its data is stale.
- **Local dev without network**: `python -m app.seed --demo-data` generates
  clearly-synthetic price history so the UI works offline;
  `python -m app.seed --backfill` fetches real data instead.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create account, returns access token + refresh cookie |
| POST | `/api/auth/login` | Log in (rate-limited per IP) |
| POST | `/api/auth/refresh` | Rotate refresh token, mint new access token |
| POST | `/api/auth/logout` | Revoke refresh token, clear cookie |
| GET | `/api/auth/me` | Current user (Bearer token) |
| GET | `/api/assets` | Search/filter/sort the asset universe (paginated) |
| GET | `/api/assets/{symbol}` | Asset detail |
| GET | `/api/assets/{symbol}/history?range=1m..max` | Daily OHLCV bars |
| GET | `/api/market/ticker` | Top movers (landing strip / dashboard) |
| POST | `/api/jobs/refresh-prices` | Refresh quotes (X-Job-Token) |
| POST | `/api/jobs/backfill-history` | Full history backfill (X-Job-Token) |
| GET | `/api/health` | Liveness + DB check |
| GET | `/api/status` | Last run per background job |

## Deployment (planned hosts, all free tier)

1. **Frontend → Vercel**: import the repo, set root directory to `frontend/`,
   set `NEXT_PUBLIC_API_URL` to the Render API URL.
2. **Backend → Render**: web service from `backend/`, build
   `pip install -r requirements.txt`, start
   `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. **Postgres → Neon** (free tier — permanent, unlike Render's free Postgres
   which is deleted after 30 days): create a project at neon.tech and set its
   connection string as `DATABASE_URL` on the Render API service. To fit
   Neon's 0.5 GB storage cap, stored daily history is limited to ~5 years
   per asset (`HISTORY_MAX_DAYS`).
4. Backend env vars: `JWT_SECRET` (long random), `CORS_ORIGINS` (the Vercel
   URL), `REFRESH_COOKIE_SECURE=true`, `REFRESH_COOKIE_SAMESITE=none`,
   `ENV=prod`, `JOB_TOKEN` (long random).
5. GitHub repo secrets for the scheduled refresh workflow:
   `FINTRACK_API_URL` (the Render URL) and `FINTRACK_JOB_TOKEN` (same value
   as `JOB_TOKEN`). Then run the "Scheduled price refresh" workflow manually
   once (or `POST /api/jobs/backfill-history`) to load initial data.

## Known Phase 1 stubs / TODOs

- Email verification is stubbed (`email_verified` set true at signup).
- Password reset flow not yet built (planned alongside email verification).
- Rate limiting is in-process; moves to Redis when the API scales past one instance.
- Landing-page ticker shows labeled sample data until Phase 2 wires real quotes.
