@echo off
REM 42 Macro Collection Script for Windows Task Scheduler
REM Runs macro42_local.py with the correct environment
REM Schedule to run daily (e.g., 7am) after Discord collection

REM Change to project root directory
cd /d "C:\Users\14102\Documents\Sebastian Ames\Projects\Confluence"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the 42 Macro collection script (uploads to Railway web tool)
python dev\scripts\macro42_local.py --railway-api

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM Log completion
echo [%date% %time%] 42 Macro collection completed with exit code %EXIT_CODE% >> logs\macro42_scheduler.log

exit /b %EXIT_CODE%
