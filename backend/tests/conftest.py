from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./phase12_test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-not-used-in-production"
os.environ["DEBUG"] = "false"
os.environ["AUTO_CREATE_DB"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.database.base import Base
from app.database.session import get_db
from app.models.user import User, UserPreference
import app.models  # noqa: F401
from app.main import app

TEST_DB_PATH = Path("phase12_test.db")
TEST_DATABASE_URL = f"sqlite+pysqlite:///{TEST_DB_PATH}"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)


@pytest.fixture(autouse=True)
def database_schema() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory(db_session: Session):
    def create_user(
        *,
        email: str = "lakshana@example.com",
        password: str = "Strong@123",
        full_name: str = "Lakshana K",
        language: str = "English",
        active: bool = True,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email.lower(),
            password_hash=hash_password(password),
            preferred_language=language,
            is_active=active,
        )
        user.preference = UserPreference(
            preferred_language=language,
            preferred_currency="INR",
            tourist_interests=[],
            accessibility_requirements=[],
            pending_suggestions=[],
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return create_user


@pytest.fixture
def auth_header(client: TestClient, user_factory):
    user_factory()
    response = client.post(
        "/api/auth/login",
        json={"email": "lakshana@example.com", "password": "Strong@123"},
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def pytest_sessionfinish(session, exitstatus):
    test_engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            pass

