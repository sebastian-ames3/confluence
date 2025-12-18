@echo off
REM 42 Macro Collection Script for Task Scheduler
REM Runs 42macro Selenium collector and uploads to Railway API

setlocal

REM Set project directory
set PROJECT_DIR=C:\Users\14102\Documents\Sebastian Ames\Projects\Confluence

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Log start time
echo ============================================================ >> "%PROJECT_DIR%\logs\macro42_batch.log"
echo 42 Macro Collection Started: %date% %time% >> "%PROJECT_DIR%\logs\macro42_batch.log"
echo ============================================================ >> "%PROJECT_DIR%\logs\macro42_batch.log"

REM Run the Python script with Railway API mode (headless)
python "%PROJECT_DIR%\dev\scripts\macro42_local.py" --railway-api >> "%PROJECT_DIR%\logs\macro42_batch.log" 2>&1

REM Log completion
echo ============================================================ >> "%PROJECT_DIR%\logs\macro42_batch.log"
echo 42 Macro Collection Completed: %date% %time% >> "%PROJECT_DIR%\logs\macro42_batch.log"
echo Exit Code: %ERRORLEVEL% >> "%PROJECT_DIR%\logs\macro42_batch.log"
echo ============================================================ >> "%PROJECT_DIR%\logs\macro42_batch.log"
echo. >> "%PROJECT_DIR%\logs\macro42_batch.log"

exit /b %ERRORLEVEL%
