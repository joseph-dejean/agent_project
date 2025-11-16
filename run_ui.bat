@echo off
echo ========================================
echo   Multi-Agent Email Generator - UI
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Starting Gradio UI...
echo The UI will open in your browser at http://localhost:7860
echo.
echo Press Ctrl+C to stop the server
echo.

python ui.py

pause

