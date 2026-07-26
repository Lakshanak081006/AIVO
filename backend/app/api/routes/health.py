from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import check_database_connection, get_db
from app.schemas.common import DatabaseHealthResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def application_health() -> HealthResponse:
    return HealthResponse(status="healthy", application=settings.APP_NAME)


@router.get("/database", response_model=DatabaseHealthResponse)
def database_health(db: Session = Depends(get_db)) -> DatabaseHealthResponse:
    check_database_connection(db)
    return DatabaseHealthResponse(status="healthy", database="connected")
