from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import JSONType, TransportType, enum_column

if TYPE_CHECKING:
    from app.models.travel import TravelPlan


class TransportOption(Base):
    __tablename__ = "transport_options"
    __table_args__ = (
        CheckConstraint("duration_minutes >= 0", name="ck_transport_duration_nonnegative"),
        CheckConstraint("price_per_person >= 0", name="ck_transport_price_nonnegative"),
        CheckConstraint("total_price >= 0", name="ck_transport_total_nonnegative"),
        CheckConstraint("traveller_count > 0", name="ck_transport_travellers_positive"),
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_transport_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    external_reference: Mapped[str] = mapped_column(String(100), index=True)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    transport_type: Mapped[TransportType] = mapped_column(
        enum_column(TransportType, "transport_type"), nullable=False
    )
    service_number: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(120), index=True)
    destination: Mapped[str] = mapped_column(String(120), index=True)
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_person: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    traveller_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    available_seats: Mapped[int | None] = mapped_column(Integer)
    number_of_stops: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float)
    cancellation_policy: Mapped[str | None] = mapped_column(Text)
    booking_class: Mapped[str | None] = mapped_column(String(50))
    normalized_score: Mapped[float | None] = mapped_column(Float)
    recommendation_type: Mapped[str | None] = mapped_column(String(50))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(
        back_populates="transport_options", foreign_keys=[travel_plan_id]
    )


class HotelOption(Base):
    __tablename__ = "hotel_options"
    __table_args__ = (
        CheckConstraint("price_per_night >= 0", name="ck_hotel_price_nonnegative"),
        CheckConstraint("number_of_nights > 0", name="ck_hotel_nights_positive"),
        CheckConstraint("number_of_rooms > 0", name="ck_hotel_rooms_positive"),
        CheckConstraint("total_price >= 0", name="ck_hotel_total_nonnegative"),
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_hotel_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    external_reference: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    city: Mapped[str] = mapped_column(String(120), index=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    number_of_nights: Mapped[int] = mapped_column(Integer, nullable=False)
    number_of_rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rating: Mapped[float | None] = mapped_column(Float)
    room_type: Mapped[str | None] = mapped_column(String(80))
    amenities: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cancellation_policy: Mapped[str | None] = mapped_column(Text)
    distance_from_city_centre: Mapped[float | None] = mapped_column(Float)
    check_in_time: Mapped[time | None] = mapped_column(Time)
    check_out_time: Mapped[time | None] = mapped_column(Time)
    normalized_score: Mapped[float | None] = mapped_column(Float)
    recommendation_type: Mapped[str | None] = mapped_column(String(50))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(
        back_populates="hotel_options", foreign_keys=[travel_plan_id]
    )


class Attraction(Base):
    __tablename__ = "attractions"
    __table_args__ = (
        CheckConstraint("entry_fee >= 0", name="ck_attraction_fee_nonnegative"),
        CheckConstraint(
            "average_visit_duration_minutes > 0",
            name="ck_attraction_duration_positive",
        ),
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_attraction_rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    external_reference: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    city: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    entry_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    opening_time: Mapped[time | None] = mapped_column(Time)
    closing_time: Mapped[time | None] = mapped_column(Time)
    average_visit_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float)
    environment_type: Mapped[str] = mapped_column(String(20), default="mixed", nullable=False)
    closed_days: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    distance_from_hotel: Mapped[float | None] = mapped_column(Float)
    weather_suitable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="attractions")


class WeatherRecord(Base):
    __tablename__ = "weather_records"
    __table_args__ = (
        CheckConstraint(
            "rain_probability IS NULL OR (rain_probability >= 0 AND rain_probability <= 100)",
            name="ck_weather_rain_probability",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    travel_plan_id: Mapped[int] = mapped_column(
        ForeignKey("travel_plans.id", ondelete="CASCADE"), index=True
    )
    city: Mapped[str] = mapped_column(String(120), index=True)
    weather_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    condition: Mapped[str] = mapped_column(String(80), nullable=False)
    minimum_temperature: Mapped[float | None] = mapped_column(Float)
    maximum_temperature: Mapped[float | None] = mapped_column(Float)
    rain_probability: Mapped[float | None] = mapped_column(Float)
    wind_speed: Mapped[float | None] = mapped_column(Float)
    weather_alert: Mapped[str | None] = mapped_column(Text)
    outdoor_suitability: Mapped[str | None] = mapped_column(String(50))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    travel_plan: Mapped["TravelPlan"] = relationship(back_populates="weather_records")
