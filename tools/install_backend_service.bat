@echo off
REM === Instalar el servicio VerticalPIC_Backend usando NSSM ===

REM Definir rutas
setlocal enableextensions
set "NSSM_PATH=%~dp0nssm.exe"
set "APP_PATH=%~dp0.."
set "PYTHON_PATH=%APP_PATH%\python_portable\python.exe"
set "SCRIPT_PATH=%APP_PATH%\main.py"
set "SERVICE_NAME=VerticalPIC_Backend"

echo Instalando el servicio %SERVICE_NAME%...

REM Validar que NSSM exista
if not exist "%NSSM_PATH%" (
    echo [ERROR] No se encontró NSSM en: %NSSM_PATH%
    exit /b 1
)

REM Crear el servicio
"%NSSM_PATH%" install "%SERVICE_NAME%" "%PYTHON_PATH%" "%SCRIPT_PATH%"
if %errorlevel% neq 0 (
    echo [ERROR] Falló la creación del servicio.
    exit /b 1
)

REM Configurar parámetros del servicio
"%NSSM_PATH%" set "%SERVICE_NAME%" AppDirectory "%APP_PATH%"
"%NSSM_PATH%" set "%SERVICE_NAME%" DisplayName "Vertical PIC Backend"
"%NSSM_PATH%" set "%SERVICE_NAME%" Description "Servicio de control y GUI para Vertical PIC"
"%NSSM_PATH%" set "%SERVICE_NAME%" Start SERVICE_AUTO_START
"%NSSM_PATH%" set "%SERVICE_NAME%" Type SERVICE_INTERACTIVE_PROCESS
"%NSSM_PATH%" set "%SERVICE_NAME%" ObjectName "LocalSystem"

echo [OK] Servicio %SERVICE_NAME% instalado correctamente.
pause
endlocal
