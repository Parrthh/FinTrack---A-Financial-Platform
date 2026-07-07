"""Application configuration, loaded from environment variables.

All secrets (JWT secret, database URL) come from the environment — never
hardcode them. See ../.env.example at the repo root for the expected keys.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"  # dev | staging | prod

    # SQLite keeps local dev zero-setup; production uses Postgres (Render).
    database_url: str = "sqlite:///./fintrack_dev.db"

    jwt_secret: str = "dev-only-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 15 * 60  # 15 minutes
    refresh_token_ttl_seconds: int = 30 * 24 * 3600  # 30 days

    # Comma-separated list of allowed browser origins.
    cors_origins: str = "http://localhost:3000"

    # Auth endpoint rate limiting (per IP, sliding window).
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 60

    # Refresh-token cookie. Secure=True required in prod (cross-site cookie).
    refresh_cookie_name: str = "fintrack_refresh"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: str = "lax"  # use "none" + secure=True in prod

    # Shared secret for job endpoints (GitHub Actions cron -> /api/jobs/*).
    # Empty string disables the endpoints entirely.
    job_token: str = ""

    # Market data providers (both free; no API keys).
    stooq_base_url: str = "https://stooq.com"
    coingecko_base_url: str = "https://api.coingecko.com"
    provider_timeout_seconds: float = 20.0
    # Consider stock quotes stale after this many seconds (free data is
    # end-of-day/delayed anyway, so hourly is plenty).
    quote_stale_seconds: int = 3600
    # Re-fetch an asset's daily history when its newest bar is older than this.
    history_stale_seconds: int = 24 * 3600

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
