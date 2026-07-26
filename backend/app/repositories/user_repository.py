from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Database access methods for users."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        normalized = email.strip().lower()
        return self.db.scalar(select(User).where(User.email == normalized))

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def update(self, user: User, values: dict) -> User:
        for field, value in values.items():
            setattr(user, field, value)
        self.db.flush()
        return user
