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

## Próximos pasos sugeridos

- [ ] **Optimización de experiencia de usuario** (indicadores visuales, reconexión, feedback avanzado)
- [ ] **Monitoreo avanzado y logging centralizado**
- [ ] **Integración con otros clientes (web, móvil) si se requiere**

---

**Estado actual:**
El sistema cuenta con comunicación robusta, pruebas, documentación, seguridad, código optimizado y actualización de estados en tiempo real profesional.
