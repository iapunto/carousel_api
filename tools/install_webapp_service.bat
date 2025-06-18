@echo off
REM Instala el servicio de la App Web
set NSSM_PATH=%~dp0nssm.exe
set APP_PATH=%~dp0..
set PYTHON_PATH=%APP_PATH%\python_portable\python.exe
set SCRIPT_PATH=%APP_PATH%\web_remote_control.py

set SERVICE_NAME=VerticalPIC_WebApp

"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "\"%SCRIPT_PATH%\""
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%APP_PATH%"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_DEMAND_START
echo Servicio %SERVICE_NAME% instalado.
pause 