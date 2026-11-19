@echo off
cd /d "%~dp0"

if not exist ".venv" (
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install streamlit chess
) else (
    call .venv\Scripts\activate.bat
)

streamlit run ChessApp.py
pause
