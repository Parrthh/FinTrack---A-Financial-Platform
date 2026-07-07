"""Audit trail: security-relevant events go to both the DB and the audit log stream."""

import uuid

from sqlalchemy.orm import Session

from app.logging_config import audit_log
from app.models import AuditLog


def record_audit_event(
    db: Session,
    event_type: str,
    user_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(AuditLog(user_id=user_id, event_type=event_type, event_metadata=metadata))
    db.commit()
    audit_log.info(event_type, user_id=str(user_id) if user_id else None, **(metadata or {}))
