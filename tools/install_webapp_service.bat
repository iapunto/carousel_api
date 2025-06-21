@echo off
REM === Instala el servicio VerticalPIC_WebApp usando NSSM ===

setlocal enableextensions

REM Definir rutas
set "NSSM_PATH=%~dp0nssm.exe"
set "APP_PATH=%~dp0.."
set "PYTHON_PATH=%APP_PATH%\python_portable\python.exe"
set "SCRIPT_PATH=%APP_PATH%\web_remote_control.py"
set "SERVICE_NAME=VerticalPIC_WebApp"

echo Instalando el servicio %SERVICE_NAME%...

REM Verificar que NSSM exista
if not exist "%NSSM_PATH%" (
    echo [ERROR] NSSM no se encontró en: %NSSM_PATH%
    exit /b 1
)

REM Crear el servicio
"%NSSM_PATH%" install "%SERVICE_NAME%" "%PYTHON_PATH%" "%SCRIPT_PATH%"
if %errorlevel% neq 0 (
    echo [ERROR] Falló la creación del servicio.
    exit /b 1
)

REM Configurar parámetros
"%NSSM_PATH%" set "%SERVICE_NAME%" AppDirectory "%APP_PATH%"
"%NSSM_PATH%" set "%SERVICE_NAME%" DisplayName "Vertical PIC WebApp"
"%NSSM_PATH%" set "%SERVICE_NAME%" Description "Servicio de interfaz web para Vertical PIC"
"%NSSM_PATH%" set "%SERVICE_NAME%" Start SERVICE_DEMAND_START
"%NSSM_PATH%" set "%SERVICE_NAME%" ObjectName "LocalSystem"

echo [OK] Servicio %SERVICE_NAME% instalado exitosamente.
pause
endlocal
