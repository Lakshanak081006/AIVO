from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import UserPublic
from app.schemas.user import PreferenceDecision, PreferenceResponse, PreferenceUpdate, ProfileUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users", "Preferences"])


def success(data=None, message: str = "Success"):
    return {"success": True, "message": message, "data": data}


@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
    return success(UserPublic.model_validate(user).model_dump(mode="json"))


@router.put("/profile")
def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = UserService(db).update_profile(user, payload)
    return success(UserPublic.model_validate(updated).model_dump(mode="json"), "Profile updated")


@router.get("/preferences")
def preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = UserService(db).get_preferences(user)
    return success(PreferenceResponse.model_validate(pref).model_dump(mode="json"))


@router.put("/preferences")
def update_preferences(payload: PreferenceUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = UserService(db).update_preferences(user, payload)
    return success(PreferenceResponse.model_validate(pref).model_dump(mode="json"), "Preferences updated")


@router.post("/preferences/confirm")
def confirm_preference(payload: PreferenceDecision, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = UserService(db).decide_suggestion(user, payload)
    return success(PreferenceResponse.model_validate(pref).model_dump(mode="json"), "Preference decision saved")
