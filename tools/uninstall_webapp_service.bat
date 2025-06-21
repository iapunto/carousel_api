@echo off
REM === Desinstalar el servicio VerticalPIC_WebApp usando NSSM ===

setlocal enableextensions

set "NSSM_PATH=%~dp0nssm.exe"
set "SERVICE_NAME=VerticalPIC_WebApp"

echo Desinstalando el servicio %SERVICE_NAME%...

REM Verificar que NSSM exista
if not exist "%NSSM_PATH%" (
    echo [ERROR] NSSM no se encontró en: %NSSM_PATH%
    exit /b 1
)

REM Detener el servicio
"%NSSM_PATH%" stop "%SERVICE_NAME%"
if %errorlevel% neq 0 (
    echo [AVISO] El servicio no se pudo detener o ya estaba detenido.
)

REM Eliminar el servicio
"%NSSM_PATH%" remove "%SERVICE_NAME%" confirm
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo eliminar el servicio.
    exit /b 1
)

echo [OK] Servicio %SERVICE_NAME% desinstalado correctamente.
pause
endlocal
