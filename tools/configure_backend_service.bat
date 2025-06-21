@echo off
REM === Configura el servicio VerticalPIC_Backend para permitir GUI ===

setlocal enableextensions
set "NSSM_PATH=%~dp0nssm.exe"
set "SERVICE_NAME=VerticalPIC_Backend"

echo Configurando servicio %SERVICE_NAME% para permitir GUI...

REM Validar que NSSM exista
if not exist "%NSSM_PATH%" (
    echo [ERROR] No se encontró NSSM en: %NSSM_PATH%
    exit /b 1
)

REM Aplicar configuración
"%NSSM_PATH%" set "%SERVICE_NAME%" Type SERVICE_INTERACTIVE_PROCESS
"%NSSM_PATH%" set "%SERVICE_NAME%" ObjectName "LocalSystem"
"%NSSM_PATH%" set "%SERVICE_NAME%" DisplayName "Vertical PIC Backend"
"%NSSM_PATH%" set "%SERVICE_NAME%" Description "Servicio de control y GUI para Vertical PIC"

echo [OK] Configuración completada para %SERVICE_NAME%.
pause
endlocal
