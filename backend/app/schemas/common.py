from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: T | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class HealthResponse(BaseModel):
    status: str
    application: str
    database: str | None = None


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
