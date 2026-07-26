from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, DatabaseOperationError, DuplicateResourceError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.preferences = PreferenceRepository(db)

    def register(self, data: RegisterRequest) -> User:
        if self.users.email_exists(data.email):
            raise DuplicateResourceError("An account with this email already exists")

        user = User(
            full_name=data.full_name,
            email=str(data.email).strip().lower(),
            password_hash=hash_password(data.password),
            preferred_language=data.preferred_language,
        )

        try:
            self.users.create(user)
            self.preferences.create_default(user.id, data.preferred_language)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateResourceError("An account with this email already exists") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseOperationError("Could not create user account") from exc

    def authenticate_user(self, data: LoginRequest) -> User:
        user = self.users.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    def create_login_response(self, user: User) -> tuple[str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        token = create_access_token(str(user.id), {"email": user.email})
        return token, expires_at

    def login(self, data: LoginRequest) -> tuple[User, str, datetime]:
        user = self.authenticate_user(data)
        token, expires_at = self.create_login_response(user)
        return user, token, expires_at
