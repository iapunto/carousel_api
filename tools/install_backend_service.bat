@echo off
REM Instala el servicio de backend/PLC+GUI en background
set NSSM_PATH=%~dp0nssm.exe
set APP_PATH=%~dp0..
set PYTHON_PATH=%APP_PATH%\python_portable\python.exe
set SCRIPT_PATH=%APP_PATH%\main.py

set SERVICE_NAME=VerticalPIC_Backend

"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "\"%SCRIPT_PATH%\""
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%APP_PATH%"
"%NSSM_PATH%" set %SERVICE_NAME% DisplayName "Vertical PIC Backend"
"%NSSM_PATH%" set %SERVICE_NAME% Description "Servicio de control y GUI para Vertical PIC"
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM_PATH%" set %SERVICE_NAME% Type SERVICE_INTERACTIVE_PROCESS
"%NSSM_PATH%" set %SERVICE_NAME% ObjectName LocalSystem
echo Servicio %SERVICE_NAME% instalado y configurado para iniciar con Windows.
pause 