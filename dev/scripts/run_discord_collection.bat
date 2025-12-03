@echo off
REM Discord Collection Script for Windows Task Scheduler
REM Runs discord_local.py with the correct environment

REM Change to project root directory
cd /d "C:\Users\14102\Documents\Sebastian Ames\Projects\Confluence"

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the Discord collection script
python dev\scripts\discord_local.py --local-db

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM Log completion
echo [%date% %time%] Discord collection completed with exit code %EXIT_CODE% >> logs\discord_scheduler.log

exit /b %EXIT_CODE%
