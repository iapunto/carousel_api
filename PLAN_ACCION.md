# PLAN DE ACCIÓN PARA MEJORAS EN `carousel_api`

## Estado de avance

- [x] **Limpieza de dependencias** (`requirements.txt` optimizado)
- [x] **Mejoras de robustez y unificación en comunicación PLC/simulador**
- [x] **Eliminación de código muerto y métodos obsoletos**
- [x] **Ampliación y corrección de pruebas unitarias e integración para la API**
- [x] **Mejoras de documentación**
- [x] **Refuerzo de seguridad y validaciones**
- [x] **Refactorización y optimización de código**
- [x] **Integración de WebSocket y actualización en tiempo real**
  - El backend emite eventos solo ante cambios de estado del PLC usando Flask-SocketIO.
  - La GUI recibe y actualiza el estado en tiempo real mediante websocket-client, sin refresco agresivo.

## Mejoras implementadas recientemente

- **Migración a comunicación en tiempo real robusta:**
  - Se reemplazó `websocket-client` por `python-socketio` en la GUI para compatibilidad total con Flask-SocketIO.
  - Se corrigió la conexión para que use dinámicamente el puerto definido en la configuración (`api_port`).
  - Se actualizaron dependencias y documentación para reflejar estos cambios.

- **Resolución de conflictos y sincronización:**
  - Se forzó la actualización del repositorio en el servidor remoto para asegurar que la versión activa es la más reciente y estable.
  - Se reinstalaron todas las dependencias en el entorno del servidor.

## Próximos pasos sugeridos

- **Optimización de rendimiento:**
  - Revisar y optimizar el uso de recursos en backend y GUI.
  - Analizar posibles cuellos de botella en la comunicación Socket.IO.

- **Mejoras de experiencia de usuario:**
  - Refinar indicadores visuales y notificaciones en la GUI.
  - Añadir mensajes de error más descriptivos y sugerencias de solución.

- **Cobertura de pruebas:**
  - Ampliar y actualizar pruebas unitarias y de integración para cubrir los nuevos flujos de comunicación en tiempo real.

- **Documentación y mantenibilidad:**
  - Mantener actualizado el README y los docstrings.
  - Documentar claramente la arquitectura de eventos y la lógica de reconexión.

- **Seguridad:**
  - Revisar y reforzar validaciones de entrada y manejo de errores global.
  - Limitar orígenes permitidos en CORS y asegurar el backend ante posibles ataques.

---

**Estado actual:**
El sistema cuenta con comunicación robusta, pruebas, documentación, seguridad, código optimizado y actualización de estados en tiempo real profesional.

**El plan de acción se mantendrá vivo y se actualizará conforme se implementen nuevas mejoras y optimizaciones.**
