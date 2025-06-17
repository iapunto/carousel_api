# PLAN DE ACCIÓN PARA NUEVA VERSIÓN DE `carousel_api`

## Versionado y Flujo de Trabajo (Branching Flow)

- **Versión objetivo:** v2.0.0 (mayor, por cambios estructurales y de arquitectura)
- **Ramas principales:**
  - `main`: rama estable, solo recibe merges de versiones probadas.
  - `develop`: rama de integración de nuevas funcionalidades y correcciones.
  - `feature/<nombre>`: para cada nueva funcionalidad o mejora.
  - `fix/<nombre>`: para correcciones de bugs.
  - `docs/<nombre>`: para mejoras de documentación.
  - `release/v2.0.0`: rama temporal para pruebas finales y preparación de la versión.
- **Flow recomendado:**
  1. Crear rama `develop` desde `main` si no existe.
  2. Cada tarea se desarrolla en su propia rama `feature/` o `fix/` desde `develop`.
  3. Al completar una tarea, merge a `develop` (PR y revisión).
  4. Cuando todas las tareas estén listas, crear `release/v2.0.0` desde `develop` para pruebas finales.
  5. Tras validación, merge a `main` y tag `v2.0.0`.
  6. Mantener documentación y changelog actualizados en cada merge.

---

## Plan de Acción Detallado

### **Prioridad Alta**

1. **Eliminar código muerto y duplicado**
   - Remover funciones y archivos no utilizados (`receive_status`, `receive_position`, `api_info.py`, métodos no usados en simulador, etc.).
   - Documentar en el changelog los elementos eliminados.

2. **Corrección y robustez en manejo de errores PLC**
   - Revisar y mejorar `PLC.connect()` y `PLC.get_current_status()` para capturar todas las excepciones relevantes y propagar/loguear adecuadamente los errores.
   - Asegurar que los errores de comunicación no se oculten y sean claros para la API y la GUI.

3. **Confinar acceso PLC al backend**
   - Modificar la GUI para que no acceda directamente al PLC, sino que use la API REST o eventos SocketIO para enviar comandos y consultar estado.
   - Probar que la GUI funciona correctamente solo como cliente de la API.

4. **Unificar lógica de estado y comandos**
   - Centralizar la obtención de estado y el envío de comandos en el `CarouselController`.
   - Adaptar los endpoints `/v1/status` y `/v1/command` para usar siempre el controlador.
   - Garantizar que la interpretación de estados y comandos sea uniforme en toda la aplicación.

5. **Formato de respuesta API estandarizado**
   - Definir y aplicar un formato JSON uniforme para todas las respuestas de la API (`success`, `data`, `error`, `code`).
   - Incluir interpretaciones de estado y códigos de error claros.

6. **Reconexión automática y persistencia de conexión PLC**
   - Implementar reconexión automática en caso de caída de la comunicación con el PLC.
   - Mantener la conexión abierta mientras la app esté activa, cerrando solo en errores graves o al apagar.

7. **Documentación técnica y de integración**
   - Crear/actualizar documentación para integradores (API, WebSocket, ejemplos de uso, despliegue, troubleshooting).
   - Mantener el README y comentarios sincronizados con los cambios.

---

### **Prioridad Media**

8. **Auditoría y actualización de dependencias**
   - Ejecutar herramientas de seguridad (Bandit, pip-audit) y actualizar dependencias menores si es seguro.

9. **Validación y robustez de configuración**
   - Mejorar la carga y validación de `config.json` (IP, puerto, modo simulador, etc.).
   - Permitir override por variables de entorno.

10. **Mejoras en GUI (usabilidad y feedback)**
    - Mejorar mensajes de error y confirmación visual en la GUI.
    - Permitir reconexión manual y automática a la API.
    - Añadir soporte para token de API si se implementa autenticación.

11. **Logs y bitácora de operaciones**
    - Mejorar el logging técnico y funcional (bitácora de comandos ejecutados, errores, eventos importantes).
    - Implementar rotación y archivado de logs.

12. **Pruebas automatizadas y de integración**
    - Ampliar cobertura de tests unitarios y de integración para API, simulador y GUI.
    - Incluir pruebas de error, concurrencia y flujos completos.

---

### **Prioridad Baja**

13. **Webhook y notificaciones externas**
    - Implementar mecanismo opcional para notificar a sistemas externos (webhook) ante eventos relevantes.

14. **Soporte para ubicaciones lógicas y extensibilidad**
    - Diseñar (y si es viable, implementar) soporte para ubicaciones lógicas (SKU -> posición) y preparar la arquitectura para múltiples PLC o conectores.

15. **Endpoint de salud y monitoreo**
    - Crear endpoint `/v1/health` para monitoreo del estado general del sistema.

16. **Feedback y pruebas piloto**
    - Recopilar feedback de usuarios e integradores piloto.
    - Realizar pruebas de despliegue y operación en entorno real o simulado.

---

## Notas Finales

- Cada tarea debe desarrollarse en su propia rama y documentarse en el changelog.
- El avance debe ser incremental, asegurando que la rama `develop` siempre sea funcional.
- El objetivo es lanzar la versión `v2.0.0` con todas las mejoras estructurales, de robustez, usabilidad y documentación implementadas.
