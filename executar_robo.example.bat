@echo off
REM 
REM 
REM 
REM 

set "PROJ=C:\caminho\para\robo-sisab-aps"

cd /d "%PROJ%"

REM 
if exist "%PROJ%\.venv\Scripts\python.exe" (
    "%PROJ%\.venv\Scripts\python.exe" -m src.main
) else (
    python -m src.main
)

exit /b %errorlevel%
