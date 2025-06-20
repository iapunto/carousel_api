@echo off
REM Desinstala el servicio de Windows para el backend de Vertical PIC

set NSSM_PATH=%~dp0nssm.exe
set SERVICE_NAME=VerticalPIC_Backend

"%NSSM_PATH%" stop %SERVICE_NAME%
"%NSSM_PATH%" remove %SERVICE_NAME% confirm
echo Servicio %SERVICE_NAME% desinstalado.
pause