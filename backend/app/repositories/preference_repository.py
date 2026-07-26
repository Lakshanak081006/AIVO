from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserPreference


class PreferenceRepository:
    """Database access for user preferences.

    Transaction boundaries are intentionally controlled by the service layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> UserPreference | None:
        return self.db.scalar(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )

    def create_default(self, user_id: int, language: str = "English") -> UserPreference:
        preference = UserPreference(
            user_id=user_id,
            preferred_language=language,
            preferred_currency="INR",
            tourist_interests=[],
            accessibility_requirements=[],
            pending_suggestions=[],
        )
        self.db.add(preference)
        self.db.flush()
        return preference

    def update(self, preference: UserPreference, values: dict) -> UserPreference:
        for field, value in values.items():
            setattr(preference, field, value)
        self.db.flush()
        return preference
