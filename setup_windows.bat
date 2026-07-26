@echo off
setlocal
cd /d %~dp0
if not exist backend\.venv (
  python -m venv backend\.venv
)
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if not exist backend\.env copy backend\.env.example backend\.env
cd frontend
call npm install
cd ..
echo Setup complete.
echo Run start_all_windows.bat
pause
