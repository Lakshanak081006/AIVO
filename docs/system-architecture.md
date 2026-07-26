# System Architecture

```text
React + Voice Input
        |
        v
FastAPI REST + SSE
        |
Coordinator / Workflow Service
        |
 +------+---------+---------+---------+
 | Transport | Hotel | Weather | Attraction |  (parallel)
 +------+---------+---------+---------+
        |
 Itinerary -> Budget -> Alternative -> Confirmation
        |
SQLAlchemy / SQLite or PostgreSQL
```

The frontend uses Axios and protected routes. FastAPI provides authentication, travel planning, progress, SSE, replanning, booking and feedback APIs. SQLAlchemy persists the full workflow.
