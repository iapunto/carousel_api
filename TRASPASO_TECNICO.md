# Traspaso Técnico — IA Punto WMS / Vertical PIC

**Fecha de corte:** 2026-10-02
**Propósito:** resumen de lo hecho y lo pendiente para continuar el
desarrollo en otro PC/IDE sin perder contexto.
**Documentos hermanos:**
`iap_carousel_integrtion_odoo/PLAN_WMS_INDUSTRIAS_PICO.md` (plan maestro),
`carousel_api/REQUERIMIENTOS_PROGRAMADOR_PLC.md` (25 preguntas para el
técnico del PLC).

---

## 1. Repositorios y ubicaciones

| Componente | Ruta | Repo remoto |
|---|---|---|
| WMS Odoo (módulos IA Punto) | `D:\carrusel\iap_carousel_integrtion_odoo` | `github.com/iapunto/iap_carousel_integration_odoo` — `main` limpio |
| Middleware PLC (`carousel_api`) | `D:\carrusel\carousel_api` | `github.com/iapunto/carousel_api` — `main` al día |
| Módulos OCA (no versionado) | `D:\carrusel\oca-addons` | clones de `OCA/*` |
| Plan WMS | `iap_carousel_integrtion_odoo/PLAN_WMS_INDUSTRIAS_PICO.md` | versionado con el repo de Odoo |
| Requerimientos PLC / este doc | `carousel_api/` (raíz) | versionado con `carousel_api` |

**Último commit carousel_api:** `9bd0b18` (snapshots barrera).
Cadena de latencia: `7b26e08` → `8038bc8` → `56f7a65` → `9bd0b18`.

## 2. Infraestructura de este PC

| Pieza | Detalle |
|---|---|
| Odoo | `C:\Program Files\Odoo 19.0.20260919` — Community 19 |
| Config | `odoo.conf` en el dir del server; addons_path incluye `iap_carousel_integrtion_odoo` y `oca-addons` |
| BD | PostgreSQL `localhost:5432`, DB `carrusel`, user `odoo` |
| URL | `http://192.168.1.10:8069` (LAN demos) |
| PLC | Delta AS218P en `192.168.1.50` — `:3200` protocolo propio, `:502` Modbus TCP |
| Servicios carousel_api | `service_api.py` (:5000), `start_websocket_server.py` (:8765), `main.py` (GUI) — arrancan por `start_carousel_service.bat` |
| Watchdog | Tarea `IAP_Carousel_Watchdog` cada 5 min relanza servicios — **deshabilitada** al entregar PC; rehabilitar: `schtasks /change /tn "IAP_Carousel_Watchdog" /enable` |
| Logs API | `carousel_api/logs/carousel_service.log`, `websocket_server.log` |

## 3. Estado funcional (lo que ya opera)

### WMS (`iap_wms_storage` + `iap_carousel_vlm`)
- Multi-bodega: MED (racks + Vertical PIC) y BGA demo; ubicaciones
  Pasillo→Rack→Nivel→Celda; 5 cangilones activos (no usar 6–8).
- Put-away dirigido por capacidad/ABC, caótico racks↔carrusel.
- Oleadas, picking con escaneo (wizard propio Community), rutas
  consolidadas, reabastecimiento, conteos cíclicos con aprobación.
- Discrepancias → conteo → aprobación; alertas con re-notificación y
  cola "Mi trabajo" por operario/zona.
- Etiquetas ZPL/PDF (ubicación, cangilón, LPN).
- **Gemelo digital 3D** (Three.js local): pasillos de dos caras,
  colores por ocupación/ABC/rotación-30d, búsqueda con marcadores
  numerados exactos, alertas parpadeantes, posición en vivo.
- Crons en producción: alertas VLM 15 min, WMS 30 min, reintento PLC
  1 min, ABC/conteos diarios.

### Integración PLC
- Comandos por `:3200` (ladder existente, seguro). Telemetría por
  Modbus `:502`: D0 posición real, D2 target, **D1000 byte de estado
  completo**, D1001 posición espejada.
- Socket TCP persistente (commit `56f7a65`) → comando llega al PLC en
  ~0.5–1 s tras el clic. Lo que queda de espera es rampa del VFD.
- Guardias: `_safety_blockers` (READY/RUN/manual/alarma/E-stop/VFD/
  error-pos) + anti-loop "ya está en posición" (`skipped:true`).
- Caché compartida `plc_status_cache.json` (FileLock) alimentada por
  el poller WS (3 s idle / 1 s moviendo).
- Diagnostics endpoint estilo OBD: `GET /v1/machines/<id>/diagnostics`.

## 4. Pendientes (prioridad de taller)

1. **Barrera de seguridad no expuesta** — escaneo completo de
   D/X/Y/M/T/C sin correlato. Necesita: rung `X_barrera→D50.bit0`,
   contacto auxiliar del relé, o dirección que lee la HMI.
   *Alternativa propia:* conectar ISPSoft en modo **monitoreo online**
   (solo lectura) y accionar la barrera viendo qué X cambia — si hay X,
   agregar el rung nosotros mismos; si no, es hardwired.
2. **Entregar `REQUERIMIENTOS_PROGRAMADOR_PLC.md` al técnico** —
   mapa de registros, bit de barrera, datos VFD, contadores, códigos
   de alarma, y (opcional) interfaz de comando por Modbus
   (D60=target, D61=trigger/ack, D62=resultado) con enclavamientos.
3. **Migrar telemetría a Modbus** cuando `D1000` se confirme — hoy el
   poller usa `:3200` para el byte de estado; una sola lectura Modbus
   traería todo en ~50 ms.
4. **Bug ladder reportado**: byte posición del `:3200` siempre 0;
   tras paro el target queda registrado sin ejecutar; movimiento a
   index 0 puede loopear si falla marca de home.
5. WMS roadmap abierto (del plan): cross-docking, picking-face
   replenishment, ABC count frequency, LPN search en 3D, pack/staging,
   PDF gerencial.
6. Dependabot: 30 vulnerabilidades reportadas en `carousel_api`.

## 5. Notas operativas para el nuevo IDE

- Python de Odoo requiere restart para cambios `.py` en módulos;
  JS/XML/SCSS solo Ctrl+F5.
- `carousel_api` cambia → reiniciar `service_api.py` + WS poller.
- Logs con timing por fase: buscar `[PLC][T]` en
  `logs/carousel_service.log`.
- Git: autor local `Sergio Rondon <desarrollo@iapunto.com>`; en esta
  máquina se commitea con `git -c user.name=... -c user.email=...`.
- Si el PLC rechaza conexiones `:3200`: hay circuit-breaker (15–120 s);
  esperar o revisar sesiones zombie — el PLC tarda ~2 s en liberar.
- No escribir registros Modbus de movimiento hasta tener mapa oficial.
- La máquina opera solo en **Modo Remoto** + READY; Modo Manual bloquea
  por hardware — correcto, no es bug.
