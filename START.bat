@echo off
cd /d "%~dp0backend"

echo ==============================
echo    FCS Lab
echo ==============================
echo.

if not exist ".venv\Scripts\activate.bat" goto setup
goto run

:setup
echo [1/3] First run. Preparing... this takes a few minutes.
python -m venv .venv
if errorlevel 1 goto nopython
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
goto seed

:run
echo [1/3] Ready.
call ".venv\Scripts\activate.bat"

:seed
echo.
echo [2/3] Loading CSV files from data folder...
python seed.py

echo.
echo [3/3] Starting server. Browser will open shortly.
echo      Close this window to stop.
echo.
start "" http://127.0.0.1:8000/
python -m uvicorn app.main:app --reload
goto end

:nopython
echo.
echo [!] Python not found. Install it from python.org and run again.

:end
pause
