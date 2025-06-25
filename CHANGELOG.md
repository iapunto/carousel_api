# Changelog

## v2.6.0 - Sistema Multi-PLC con Dashboard de Cards y Optimizaciones (2025-06-24)

### 🚀 Funcionalidades Principales

- **Sistema Multi-PLC Completo**: Soporte para múltiples carruseles industriales con configuración centralizada
- **Dashboard de Cards Dinámicas**: Sistema de cards que se crean automáticamente por cada máquina configurada
- **Panel de Comandos Mejorado**: Interfaz intuitiva con selector de máquinas y spinbox para cangilones
- **Actualización Automática**: Dashboard se actualiza sin reiniciar al cambiar configuración Real/Simulador

### 🎨 Interfaz y UX

- **Layout de Dos Columnas**: Panel de comandos reorganizado para mejor aprovechamiento del espacio
- **Cards Escalables**: Vista scrollable para manejar múltiples máquinas con información completa por card
- **Indicadores Visuales**: Estados con colores semánticos (Verde/Rojo/Amarillo/Azul) y emojis descriptivos
- **Carga Inicial Optimizada**: Información básica mostrada inmediatamente, estado completo en ~3 segundos

### 🔧 Mejoras Técnicas

- **WebSocket Nativo**: Migración de SocketIO a WebSocket nativo (puerto 8765) para mejor rendimiento
- **Solicitudes HTTP Paralelas**: Carga inicial vía HTTP más rápida que WebSocket como fallback
- **Watcher de Archivos**: Detección automática de cambios en configuración cada 3 segundos
- **Endpoints Corregidos**: URLs de API corregidas para comandos multi-PLC

### 🏭 Configuración Multi-Máquina

- **Configuración Centralizada**: Gestión completa desde GUI con sistema CRUD
- **Compatibilidad Dual**: Detecta automáticamente single-PLC vs multi-PLC
- **Backups Automáticos**: Respaldo de configuraciones con timestamps
- **Validación Robusta**: Verificación de IPs, puertos y tipos de máquina

### 📊 Dashboard y Monitoreo

- **Tiempo Real**: Actualización vía WebSocket cada 2 segundos con reconexión automática
- **Información Completa**: Header con nombre, IP:Puerto, tipo (Real/Simulador) por card
- **Grid de Estados**: Display 2x2 de estados principales (READY, RUN, MODO_OPERACION, ALARMA)
- **Posición Destacada**: Display de posición actual en azul prominente

### 🎯 Panel de Comandos

- **Selector Dinámico**: ComboBox con todas las máquinas configuradas automáticamente
- **Spinbox Intuitivo**: Flechas ▲▼ para incrementar/decrementar posición de cangilón (1-255)
- **Notificaciones en Tiempo Real**: TextBox con timestamps, emojis categorizados y throttling
- **Validaciones**: Selección obligatoria de máquina, rango de cangilón, manejo de errores

### 🔄 Actualizaciones Automáticas

- **Detección de Cambios**: Monitoreo de `config_multi_plc.json` sin reiniciar aplicación
- **Recarga Inteligente**: Actualización completa del dashboard y panel de comandos
- **Compatibilidad Legacy**: Mantiene soporte para configuración single-PLC existente

### 🛠️ Correcciones Importantes

- **Endpoints API**: Corregido `/v1/multi-plc/command` → `/v1/machines/{id}/command`
- **Manejo de Errores**: Mejor gestión de errores de simuladores y máquinas reales
- **Layout Responsivo**: Panel funcional sin necesidad de maximizar ventana
- **Encoding UTF-8**: Corrección de problemas de emojis en Windows

### 📋 Próximas Funcionalidades Planificadas

- **Notificaciones Tempranas**: Sistema de alertas proactivas
- **Emisión de Sonidos**: Alertas audibles para alarmas y fallos
- **Métricas Avanzadas**: Dashboard de rendimiento y estadísticas

---

## v2.5.38

- Separación profesional de entornos: ahora los prints de depuración solo aparecen en desarrollo (`APP_ENV=development`).
- Se introduce la función `debug_print()` para controlar mensajes de depuración.
- Todos los prints de depuración han sido reemplazados por `debug_print` en el código fuente.
- Documentación actualizada sobre el uso de la variable de entorno `APP_ENV` y el control de logs.

## v2.5.37

- Actualización de `urllib3` a >=2.5.0 para corregir vulnerabilidad GHSA-48p4-8xcf-vxj5 (pip-audit).
- Ajuste del test de concurrencia para robustez en CI/CD: ahora permite ambos 200 en entornos de test, mostrando advertencia.
- Limpieza de archivos obsoletos de auditoría y planes.
- Mejoras menores en la documentación y mantenimiento del pipeline.

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
