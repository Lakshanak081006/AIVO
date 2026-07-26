# API Summary

Swagger documentation is available at `http://localhost:8000/docs`.

## Authentication
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

## Travel workflow
- `POST /api/travel/extract-requirements`
- `POST /api/travel/validate-requirements`
- `POST /api/travel/plan`
- `POST /api/travel/clarify`
- `GET /api/travel/plans`
- `GET /api/travel/plans/{id}`
- `POST /api/travel/plans/{id}/replan`
- `GET /api/travel/plans/{id}/stream`

## Results
Transport, hotels, weather, attractions, itinerary, budget, alternatives, tasks, progress, logs and events each have plan-specific GET endpoints.

## Safety and learning
Confirmation, simulated booking, booking cancellation, feedback and preference-approval endpoints are included.
