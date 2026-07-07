"""FinTrack API entrypoint."""

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logging_config import app_log, configure_logging
from app.routers import assets, auth, jobs, status

settings = get_settings()
configure_logging(settings.env)

app = FastAPI(
    title="FinTrack API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS locked to the configured frontend origin(s); credentials needed for
# the httpOnly refresh cookie.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    app_log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round((time.perf_counter() - start) * 1000, 2),
    )
    return response


app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(jobs.router)
app.include_router(status.router)
