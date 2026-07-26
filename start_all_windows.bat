@echo off
cd /d %~dp0
start "AIVA Backend" cmd /k "cd backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"
start "AIVA Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 4 >nul
start http://localhost:5173
