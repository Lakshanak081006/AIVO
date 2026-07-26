# Autonomous Personal Assistant Agent for Multi-Step Real-World Tasks

A complete academic full-stack project that demonstrates Agentic AI through autonomous travel planning. It accepts one high-level instruction, decomposes it into tasks, runs multiple agents, creates an itinerary, calculates cost, recovers from failures and transparently explains what it did.

## Included phases

All 16 planned phases are included. See [PHASES.md](PHASES.md).

## Main features

- Registration, login and JWT authentication
- Profile and approved preference learning
- Text and browser voice input
- English, Tamil and Hindi request detection
- Requirement extraction and clarification
- Priority-based task decomposition
- Parallel Transport, Hotel, Weather and Attraction agents
- Weighted option comparison
- Day-wise itinerary generation
- Budget breakdown and cheaper alternatives
- Exponential retries and local fallback data
- Dynamic replanning and plan versions
- Live-style SSE event playback and transparent action logs
- Confirmation gates and simulated booking
- Feedback-based preference suggestions
- Responsive React dashboard
- SQLite local mode and PostgreSQL Docker mode

## Project structure

```text
autonomous-personal-assistant-all-phases/
├── backend/        FastAPI, agents, workflow, models, tests and simulated data
├── frontend/       React, Vite, dashboard, voice input and result pages
├── database/       SQL schema
├── docs/           Complete academic and technical documentation
├── docker-compose.yml
├── setup_windows.bat
└── start_all_windows.bat
```

## Fastest Windows setup

1. Extract the ZIP.
2. Open the extracted folder.
3. Run `setup_windows.bat` once.
4. Run `start_all_windows.bat`.
5. Open `http://localhost:5173`.

The backend runs at `http://localhost:8000`. Swagger is at `http://localhost:8000/docs`.

## Manual backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

SQLite is used by default, so PostgreSQL is not required for the basic demo.

## Manual frontend setup

Open a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`, not port 8080.

## Demo credentials

```text
Email: demo@example.com
Password: Demo@12345
```

These credentials are for local demonstration only.

## Sample request

```text
Plan a two-day trip from Coimbatore to Chennai for two people next weekend under ₹20000. I prefer train travel and museums.
```

## Docker

```bash
docker compose up --build
```

Open:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Testing

```bash
cd backend
pytest -q
python -m compileall app
```

```bash
cd frontend
npm install
npm test
npm run build
```

## Important safety behavior

All booking and payment operations are simulations. The application requires confirmation before simulated booking and never executes a real financial transaction.

## Troubleshooting

### Browser says localhost refused to connect
Make sure the backend terminal says Uvicorn is running, and use `http://localhost:8000/docs`. The React site uses `http://localhost:5173`.

### Port is already in use
Run the backend on another port, for example `python -m uvicorn app.main:app --reload --port 8001`, then update `VITE_API_BASE_URL` in the frontend `.env`.

### npm is not recognized
Install the current Node.js LTS release and reopen the terminal.

### Database error
Delete `backend/assistant.db` for a clean local demo database, then restart the backend.
