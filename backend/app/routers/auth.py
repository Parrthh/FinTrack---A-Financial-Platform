"""Auth endpoints: signup, login, refresh, logout, me.

Token model:
- Access token (JWT, 15 min) returned in the JSON body; frontend keeps it in
  memory and sends it as a Bearer header.
- Refresh token (opaque, 30 days) set as an httpOnly cookie scoped to
  /api/auth so JS can never read it; rotated on every refresh and revoked on
  logout. Only its SHA-256 hash is stored server-side.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit_event
from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import RefreshToken, User
from app.rate_limit import enforce_auth_rate_limit
from app.schemas import (
    LoginRequest,
    MessageResponse,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        max_age=settings.refresh_token_ttl_seconds,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path="/api/auth",
    )


def _issue_session(db: Session, response: Response, user: User) -> TokenResponse:
    raw, token_hash, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()
    _set_refresh_cookie(response, raw)
    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.access_token_ttl_seconds,
    )


def _get_valid_refresh_token(db: Session, raw: str) -> RefreshToken | None:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw))
    )
    if token is None or token.revoked:
        return None
    expires_at = token.expires_at
    if expires_at.tzinfo is None:  # SQLite drops tzinfo
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        return None
    return token


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_auth_rate_limit)],
)
def signup(body: SignupRequest, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="An account with this email exists"
        )
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        # TODO(Phase 6): send a verification email instead of auto-verifying.
        email_verified=True,
    )
    db.add(user)
    db.commit()
    record_audit_event(db, "signup", user_id=user.id, metadata={"email": email})
    return _issue_session(db, response, user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_auth_rate_limit)],
)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        record_audit_event(
            db,
            "login_failure",
            user_id=user.id if user else None,
            metadata={"email": email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    record_audit_event(db, "login_success", user_id=user.id)
    return _issue_session(db, response, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get(settings.refresh_cookie_name)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    token = _get_valid_refresh_token(db, raw)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )
    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    # Rotate: revoke the presented token, issue a fresh one.
    token.revoked = True
    db.commit()
    return _issue_session(db, response, user)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get(settings.refresh_cookie_name)
    if raw:
        token = _get_valid_refresh_token(db, raw)
        if token is not None:
            token.revoked = True
            db.commit()
            record_audit_event(db, "logout", user_id=token.user_id)
    response.delete_cookie(settings.refresh_cookie_name, path="/api/auth")
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
