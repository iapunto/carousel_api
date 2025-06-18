@echo off
REM Instala el servicio de la App Web
set NSSM_PATH=%~dp0nssm.exe
set PYTHON_PATH=%~dp0..\venv\Scripts\python.exe
set SCRIPT_PATH=%~dp0..\web_remote_control.py

set SERVICE_NAME=VerticalPIC_WebApp

"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "%SCRIPT_PATH%"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_DEMAND_START
echo Servicio %SERVICE_NAME% instalado.
pause 