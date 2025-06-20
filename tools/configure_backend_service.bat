@echo off
REM Configura el servicio del backend para permitir GUI
set NSSM_PATH=%~dp0nssm.exe

echo Configurando servicio VerticalPIC_Backend para permitir GUI...
"%NSSM_PATH%" set VerticalPIC_Backend Type SERVICE_INTERACTIVE_PROCESS
"%NSSM_PATH%" set VerticalPIC_Backend ObjectName LocalSystem
"%NSSM_PATH%" set VerticalPIC_Backend DisplayName "Vertical PIC Backend"
"%NSSM_PATH%" set VerticalPIC_Backend Description "Servicio de control y GUI para Vertical PIC"
echo Configuracion completada.
pause 