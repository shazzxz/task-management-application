@echo off
setlocal
cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cd frontend
npm install
cd ..
echo.
echo Setup complete.
echo Start backend with: run_backend.bat
echo Start frontend with: run_frontend.bat
pause
