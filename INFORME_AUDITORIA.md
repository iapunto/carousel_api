# INFORME DE AUDITORÍA DEL SISTEMA `carousel_api`

## 1. Resumen General

Este informe detalla los hallazgos tras un análisis exhaustivo del sistema `carousel_api`, incluyendo la API, el simulador, la interfaz gráfica, la configuración, el empaquetado y las pruebas.

---

## 2. Puntos de dolor y errores detectados

### 2.1. Conexión y manejo de errores con el PLC real

- El método `connect()` de la clase `PLC` solo captura algunos errores de red (`socket.timeout`, `ConnectionRefusedError`), pero no otros posibles fallos.
- No existe un sistema de reintentos ni reconexión automática.
- El método `get_current_status` de `PLC` imprime errores en consola, pero no los registra ni los propaga adecuadamente.
- El endpoint `/v1/status` depende de una conexión exitosa en cada llamada, lo que puede causar fallos intermitentes si el PLC está inestable.

### 2.2. Diferencias entre simulador y PLC real

- El simulador acepta argumentos de posición entre 0-9, pero el PLC real acepta 0-255.
- El simulador implementa métodos y validaciones diferentes, lo que puede llevar a inconsistencias entre pruebas y producción.

### 2.3. Código muerto y redundante

- Métodos como `receive_status` y `receive_position` en el simulador no están implementados ni usados en la lógica principal.
- El archivo `api_info.py` solo imprime información y no es usado en producción.
- El método `get_current_status` de la clase `PLC` no es usado por la API.

### 2.4. Pruebas automatizadas

- Solo existe un archivo de test y cubre parcialmente el simulador.
- No hay pruebas de integración ni de la API ni de la GUI.

### 2.5. Empaquetado y despliegue

- El script de instalación no verifica dependencias del sistema.
- La API se ejecuta en modo desarrollo desde la GUI, lo que puede causar problemas de concurrencia o seguridad.

### 2.6. Configuración y seguridad

- El archivo `config.json` puede quedar expuesto con credenciales o IPs reales.
- No hay validación de configuración al inicio.
- No se usan variables de entorno para datos sensibles.

### 2.7. Optimización y buenas prácticas

- El polling de estado en la GUI es cada 60 segundos, lo que puede ser poco reactivo.
- No hay logging estructurado ni centralizado.
- No hay manejo de reconexión automática ni de reintentos en la comunicación con el PLC.
- El código de interpretación de estados podría ser más robusto y extensible.

### 2.8. Documentación

- La documentación no está completamente alineada con la estructura real del proyecto.
- Faltan ejemplos de despliegue seguro y uso de variables de entorno.

---

## 3. Ejemplos concretos y observaciones técnicas

- En `models/plc.py`, el método `connect()` solo captura dos tipos de excepción y no implementa reintentos.
- En `models/plc_simulator.py`, los métodos `receive_status` y `receive_position` no existen en la lógica principal.
- En `main.py`, la API Flask se ejecuta en un hilo en modo desarrollo, lo que no es recomendable para producción.
- El archivo `requirements.txt` incluye dependencias que podrían estar desactualizadas o ser innecesarias.
- El archivo `config.json` contiene información sensible y no está protegido.
- El archivo `api_info.py` no es utilizado en el flujo principal.
- El test `tests/test_plc_simulator.py` prueba métodos que no existen en el simulador real.

---

## 4. Conclusión

El sistema es funcional, pero requiere mejoras importantes en robustez, seguridad, pruebas, documentación y buenas prácticas para garantizar su fiabilidad y mantenibilidad en entornos productivos.
