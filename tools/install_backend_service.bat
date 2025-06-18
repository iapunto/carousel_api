@echo off
REM Instala el servicio de backend/PLC+GUI en background
set NSSM_PATH=%~dp0nssm.exe
set PYTHON_PATH=%~dp0..\venv\Scripts\python.exe
set SCRIPT_PATH=%~dp0..\main.py

set SERVICE_NAME=VerticalPIC_Backend

"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "%SCRIPT_PATH%"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
echo Servicio %SERVICE_NAME% instalado y configurado para iniciar con Windows.
pause 