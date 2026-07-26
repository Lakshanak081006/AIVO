@echo off
cd /d %~dp0\backend
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --port 8000
