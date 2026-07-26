from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, DatabaseOperationError, ResourceNotFoundError, ValidationFailureError
from app.models.enums import TransportType
from app.models.user import User, UserPreference
from app.repositories.preference_repository import PreferenceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import PreferenceDecision, PreferenceUpdate, ProfileUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.preferences = PreferenceRepository(db)

    def update_profile(self, user: User, data: ProfileUpdate) -> User:
        values = data.model_dump(exclude_unset=True)
        try:
            self.users.update(user, values)
            if "preferred_language" in values:
                preference = self.get_preferences(user)
                preference.preferred_language = values["preferred_language"]
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseOperationError("Could not update user profile") from exc

    def get_preferences(self, user: User) -> UserPreference:
        preference = self.preferences.get_by_user_id(user.id)
        if preference is not None:
            return preference
        try:
            preference = self.preferences.create_default(user.id, user.preferred_language)
            self.db.commit()
            self.db.refresh(preference)
            return preference
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseOperationError("Could not create user preferences") from exc

    def update_preferences(self, user: User, data: PreferenceUpdate) -> UserPreference:
        preference = self.get_preferences(user)
        values = data.model_dump(exclude_unset=True)
        try:
            self.preferences.update(preference, values)
            if "preferred_language" in values:
                user.preferred_language = values["preferred_language"]
            self.db.commit()
            self.db.refresh(preference)
            return preference
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseOperationError("Could not update user preferences") from exc

    def decide_suggestion(self, user: User, data: PreferenceDecision) -> UserPreference:
        preference = self.get_preferences(user)
        suggestions = [dict(item) for item in (preference.pending_suggestions or [])]
        target = next((item for item in suggestions if item.get("id") == data.suggestion_id), None)
        if target is None:
            raise ResourceNotFoundError("Preference suggestion was not found")
        if str(target.get("status", "")).upper() != "PENDING":
            raise ConflictError("Preference suggestion has already been processed")

        target["status"] = data.decision
        target["responded_at"] = datetime.now(timezone.utc).isoformat()

        if data.decision == "APPROVED":
            field = str(target.get("field", ""))
            value = target.get("suggested_value")
            value = self._validate_suggested_value(field, value)
            setattr(preference, field, value)
            if field == "preferred_language":
                user.preferred_language = value

        preference.pending_suggestions = suggestions
        try:
            self.db.commit()
            self.db.refresh(preference)
            return preference
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise DatabaseOperationError("Could not save preference decision") from exc

    @staticmethod
    def _validate_suggested_value(field: str, value: Any) -> Any:
        allowed_fields = {
            "preferred_language",
            "preferred_currency",
            "preferred_transport_type",
            "preferred_hotel_category",
            "minimum_hotel_rating",
            "maximum_hotel_distance",
            "preferred_food_type",
            "tourist_interests",
            "avoid_early_morning",
            "avoid_late_night",
        }
        if field not in allowed_fields:
            raise ValidationFailureError("Unsupported suggested preference")

        if field == "preferred_transport_type":
            try:
                return TransportType(str(value).upper())
            except ValueError as exc:
                raise ValidationFailureError("Invalid suggested transport type") from exc
        if field == "preferred_language":
            normalized = str(value).strip().title()
            if normalized not in {"English", "Tamil", "Hindi"}:
                raise ValidationFailureError("Invalid suggested language")
            return normalized
        if field == "preferred_currency":
            normalized = str(value).strip().upper()
            if len(normalized) != 3 or not normalized.isalpha():
                raise ValidationFailureError("Invalid suggested currency")
            return normalized
        if field == "minimum_hotel_rating":
            rating = float(value)
            if rating < 0 or rating > 5:
                raise ValidationFailureError("Invalid suggested hotel rating")
            return rating
        if field == "maximum_hotel_distance":
            distance = float(value)
            if distance < 0:
                raise ValidationFailureError("Invalid suggested hotel distance")
            return distance
        if field in {"avoid_early_morning", "avoid_late_night"}:
            if not isinstance(value, bool):
                raise ValidationFailureError("Suggested value must be true or false")
            return value
        if field == "tourist_interests":
            if not isinstance(value, list):
                raise ValidationFailureError("Suggested tourist interests must be a list")
            cleaned: list[str] = []
            for item in value:
                text = str(item).strip()
                if text and text.lower() not in {x.lower() for x in cleaned}:
                    cleaned.append(text[:100])
            return cleaned
        return str(value).strip() if value is not None else None
