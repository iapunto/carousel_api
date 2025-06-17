# Changelog

## v2.5.36

- Corrección de errores en la interfaz gráfica.
- Mejoras en el proceso de instalación.
- Actualización de dependencias.

## v2.5.35

- Implementación del modo simulador.
- Optimización del rendimiento.

- Eliminados los métodos no utilizados move_to_position y receive_response en PLCSimulator (models/plc_simulator.py) como parte de la limpieza de código muerto para la versión 2.0.0.

- Refactorizada la GUI (main_gui.py) para que consuma únicamente la API REST y elimine cualquier acceso directo al PLC. Ahora todos los comandos se envían vía HTTP a /v1/command.

- Mejorado el hilo de monitoreo (main.py): ahora implementa reconexión automática y mantiene la conexión persistente al PLC. Se notifican eventos de reconexión a la GUI/WMS y se refuerza la robustez del sistema.
