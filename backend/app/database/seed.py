from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.user import User, UserPreference

logger = logging.getLogger(__name__)


def seed_demo_user(db: Session | None = None) -> None:
    """Create a local demonstration user and default preferences if absent."""
    owns_session = db is None
    session = db or SessionLocal()
    try:
        existing = session.scalar(select(User).where(User.email == settings.DEMO_USER_EMAIL.lower()))
        if existing:
            return
        user = User(
            full_name=settings.DEMO_USER_NAME,
            email=settings.DEMO_USER_EMAIL.lower(),
            password_hash=hash_password(settings.DEMO_USER_PASSWORD),
            preferred_language="English",
        )
        user.preference = UserPreference(
            preferred_language="English",
            preferred_currency="INR",
            tourist_interests=[],
            accessibility_requirements=[],
            pending_suggestions=[],
        )
        session.add(user)
        session.commit()
        logger.info("Created demo user: %s", settings.DEMO_USER_EMAIL)
    except Exception:
        session.rollback()
        logger.exception("Failed to seed demonstration user")
        raise
    finally:
        if owns_session:
            session.close()


if __name__ == "__main__":
    seed_demo_user()
