# Testing Guide

## Backend

```bash
cd backend
pytest -q
python -m compileall app
```

The suite covers configuration, models, authentication, profiles, preferences, requirement extraction, ranking, full planning, clarification, budget alternatives, feedback and fallback recovery.

## Frontend

```bash
cd frontend
npm install
npm test
npm run build
```

## API demonstration
Use Swagger at `http://localhost:8000/docs` and authenticate with the demo account.
