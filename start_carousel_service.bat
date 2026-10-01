@echo off
REM ============================================================
REM  carousel_api - arranque de servicios (API :5000, Web :8181, WS :8765) + GUI
REM  IA Punto Soluciones Tecnologicas - Industrias Pico S.A.S
REM  Rutas absolutas: este archivo puede invocarse desde cualquier
REM  ubicacion (p.ej. la carpeta Startup de Windows)
REM ============================================================
set BASE=D:\carrusel\carousel_api
set PYW=%BASE%\venv\Scripts\pythonw.exe
set PYTHONUTF8=1
cd /d "%BASE%"

start "carousel_api_backend" /min %PYW% "%BASE%\service_api.py"
REM Web remote :8181 DEPRECADO — era herramienta de demo; ya no arranca
REM start "carousel_api_web" /min %PYW% "%BASE%\web_remote_control.py"
start "carousel_api_ws" /min %PYW% "%BASE%\start_websocket_server.py"
REM GUI de escritorio: main.py espera internamente a que el backend responda en :5000
start "carousel_gui" %PYW% "%BASE%\main.py"
