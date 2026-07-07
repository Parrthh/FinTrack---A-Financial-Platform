"""Pydantic request/response schemas (input validation per security checklist)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str


class AssetResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    asset_type: str
    exchange: str | None
    sector: str | None
    currency: str
    last_price: float | None
    last_price_at: datetime | None
    day_change_pct: float | None
    market_cap: float | None

    model_config = {"from_attributes": True}


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    limit: int
    offset: int


class PriceBar(BaseModel):
    ts: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None

    model_config = {"from_attributes": True}


class AssetHistoryResponse(BaseModel):
    symbol: str
    range: str
    bars: list[PriceBar]


class TickerEntry(BaseModel):
    symbol: str
    asset_type: str
    last_price: float | None
    day_change_pct: float | None


class JobRunResponse(BaseModel):
    job_name: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    items_processed: int | None
    error: str | None

    model_config = {"from_attributes": True}
