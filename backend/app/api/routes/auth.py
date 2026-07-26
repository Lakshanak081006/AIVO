from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginData, LoginRequest, RegisterRequest, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def success(data=None, message: str = "Success"):
    return {"success": True, "message": message, "data": data}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService(db).register(payload)
    return success(
        UserPublic.model_validate(user).model_dump(mode="json"),
        "User registered successfully",
    )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user, token, expires_at = AuthService(db).login(payload)
    data = LoginData(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires_at=expires_at,
        user=UserPublic.model_validate(user),
    )
    return success(data.model_dump(mode="json"), "Login successful")


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return success(UserPublic.model_validate(user).model_dump(mode="json"))
