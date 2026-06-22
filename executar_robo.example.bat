@echo off
REM ====================================================================
REM Robo SISAB - execucao agendada
REM Ajuste PROJ para o caminho real do projeto no seu computador.
REM ====================================================================

set "PROJ=C:\caminho\para\robo-sisab-aps"

cd /d "%PROJ%"

REM Usa o Python da venv se existir; senao usa o Python do sistema.
if exist "%PROJ%\.venv\Scripts\python.exe" (
    "%PROJ%\.venv\Scripts\python.exe" -m src.main
) else (
    python -m src.main
)

exit /b %errorlevel%
