# Changelog

## v2.5.36

- Corrección de errores en la interfaz gráfica.
- Mejoras en el proceso de instalación.
- Actualización de dependencias.

## v2.5.35

- Implementación del modo simulador.
- Optimización del rendimiento.
- Eliminados los métodos no utilizados `move_to_position` y `receive_response` en `PLCSimulator` (`models/plc_simulator.py`).

## v2.5.34

- Refactorizada la GUI (`main_gui.py`) para que consuma únicamente la API REST y elimine cualquier acceso directo al PLC. Ahora todos los comandos se envían vía HTTP a `/v1/command`.
- Mejorado el hilo de monitoreo (`main.py`): ahora implementa reconexión automática y mantiene la conexión persistente al PLC. Se notifican eventos de reconexión a la GUI/WMS y se refuerza la robustez del sistema.

## v2.5.33

- Mejorados y unificados los logs en la API (`api.py`), controlador (`carousel_controller.py`) y monitor (`main.py`): ahora todos los eventos críticos, advertencias y errores quedan registrados con contexto relevante y formato consistente, facilitando el monitoreo y diagnóstico.
- Refuerzo de la validación de parámetros en la API (`api.py`): ahora se verifica tipo y rango de `command` y `argument` en `/v1/command`, rechazando datos inválidos con mensajes claros y códigos HTTP apropiados.

## v2.5.32

- Mejorada la configuración de CORS: solo se permiten orígenes explícitamente autorizados y se documenta el uso de la variable de entorno `API_ALLOWED_ORIGINS` para producción.
- Estandarización de respuestas y manejo de errores en la API: todos los endpoints principales responden con el formato `{success, data, error, code}` y usan códigos de error internos claros y documentados. Mensajes en español.

## v2.5.31

- Estandarización del formato de eventos SocketIO: todos los eventos relevantes (`plc_status`, `plc_status_error`, `plc_reconnecting`, `plc_reconnected`) siguen el formato `{success, data, error, code}` y usan los mismos códigos de error internos que la API REST.
- Centralización de los códigos de error internos en `commons/error_codes.py` y actualización de la API y eventos para usar estas constantes, facilitando la mantenibilidad y la integración profesional.

## v2.5.30

- Implementado mecanismo de bloqueo interproceso usando filelock, integrado en la API y el monitor para evitar acceso concurrente al PLC desde procesos distintos.
- Despliegue y pruebas reales satisfactorias en entorno productivo.
- Instalador y servicio verificados, operación continua confirmada.
- Documentación y procesos actualizados.
- Solo quedan observaciones menores y seguimiento post-producción.
- **Versión consolidada y lista para producción.**

---

## v1.x (histórico)

- Implementación inicial de la API REST para control de carrusel vertical.
- Integración básica con PLC Delta AS Series (comunicación TCP/IP).
- Primeros endpoints: `/v1/status` y `/v1/command`.
- Validación básica de parámetros y manejo de errores genérico.
- Interfaz gráfica inicial (Tkinter) para operación manual.
- Simulador de PLC básico para pruebas sin hardware.
- Primeros scripts de instalación y dependencias.
- Documentación inicial y ejemplos de uso.
- Seguridad básica: CORS restringido y validaciones mínimas.
- Primeros tests unitarios y de integración.

---
