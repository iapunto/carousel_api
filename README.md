# carousel_api

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-API-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-blue?logo=socket.io)](https://socket.io/)
[![Build Status](https://github.com/iapunto/carousel_api/actions/workflows/ci.yml/badge.svg)](https://github.com/iapunto/carousel_api/actions)
[![Coverage](https://img.shields.io/badge/Coverage-Automático-brightgreen?logo=pytest)](https://github.com/iapunto/carousel_api/actions)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![License](https://img.shields.io/github/license/iapunto/carousel_api?color=blue)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/iapunto/carousel_api?color=informational)](https://github.com/iapunto/carousel_api/commits/main)

---

## 🚀 Descripción

**carousel_api** es una solución integral para la gestión y control de sistemas de almacenamiento automatizado tipo carrusel vertical, orientada a la industria 4.0. Permite la integración directa con hardware industrial (PLC Delta AS Series) o su simulador, facilitando tanto la operación en entornos productivos como el desarrollo y pruebas seguras.

- **API REST robusta** para integración con sistemas externos.
- **Interfaz gráfica moderna** para operación manual y monitoreo en tiempo real.
- **Aplicación web moderna** con diseño responsive y soporte multi-PLC.
- **Sistema Multi-PLC** para gestión de múltiples máquinas desde una sola interfaz.
- **Simulador de PLC** para pruebas sin hardware.
- **Comunicación en tiempo real** mediante WebSocket y Socket.IO.
- **Seguridad reforzada** y buenas prácticas de desarrollo.

---

## 🛠️ Tecnologías principales

- **Python 3.12+**
- **Flask** (API REST)
- **Flask-SocketIO** y **python-socketio** (comunicación en tiempo real)
- **Eventlet** (servidor asíncrono)
- **CustomTkinter** (GUI)
- **Bandit, pip-audit** (seguridad)
- **Pytest** (tests y cobertura)

---

## 📦 Arquitectura

```md
[GUI] <---WebSocket---> [API Flask] <---TCP/IP---> [PLC Delta / Simulador]
[Web App] <---REST----> [Multi-PLC Manager] <---TCP/IP---> [Multiple PLCs]
```

**Archivos principales:**

- `api.py`: API principal y servidor de eventos.
- `web_remote_control.py`: Aplicación web moderna con soporte multi-PLC.
- `models/plc_manager.py`: Gestor de múltiples PLCs.
- `models/plc.py`: Comunicación con PLC real.
- `models/plc_simulator.py`: Simulador de PLC.
- `controllers/carousel_controller.py`: Lógica de negocio y validaciones.
- `commons/utils.py`: Utilidades y validaciones centralizadas.
- `main.py`: Lanzador de la aplicación (API + GUI).

---

## 🔗 Endpoints principales

### API Backend (Puerto 5000)

| Método | Ruta                          | Descripción                        | Parámetros         |
|--------|-------------------------------|------------------------------------|--------------------|
| GET    | /v1/status                    | Consulta el estado actual del PLC  | -                  |
| POST   | /v1/command                   | Envía un comando al PLC/simulador  | `command`, `argument` |
| GET    | /v1/machines                  | Lista todas las máquinas configuradas | -               |
| GET    | /v1/machines/{id}/status      | Consulta estado de máquina específica | -               |
| POST   | /v1/machines/{id}/command     | Envía comando a máquina específica | `command`, `argument` |

### Aplicación Web (Puerto 8181)

| Ruta           | Descripción                                    |
|----------------|------------------------------------------------|
| /              | Interfaz web de control remoto                 |
| /api/config    | Configuración de máquinas disponibles         |
| /api/move      | Endpoint para envío de comandos desde la web  |

**Ejemplos de uso:**

```bash
# API Backend
curl -X GET http://localhost:5000/v1/status
curl -X POST http://localhost:5000/v1/command -H "Content-Type: application/json" -d '{"command":1,"argument":3}'

# Multi-PLC
curl -X GET http://localhost:5000/v1/machines
curl -X POST http://localhost:5000/v1/machines/plc_001/command -H "Content-Type: application/json" -d '{"command":1,"argument":5}'

# Aplicación Web
curl -X GET http://localhost:8181/api/config
curl -X POST http://localhost:8181/api/move -H "Content-Type: application/json" -d '{"machine_id":"plc_001","position":5}'
```

---

## ⚡ Comunicación en tiempo real

- La GUI y cualquier cliente pueden suscribirse a eventos `plc_status` vía Socket.IO.
- Actualizaciones instantáneas ante cualquier cambio de estado, sin necesidad de polling.

---

## 🧑‍💻 Instalación rápida

```bash
git clone https://github.com/iapunto/carousel_api.git
cd carousel_api
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
python main.py
```

### Configuración

1. **Configuración básica:** Edita `config.json` para configuración single-PLC
2. **Configuración Multi-PLC:** Edita `config_multi_plc.json` para múltiples máquinas
3. **Aplicación web:** Se inicia automáticamente en `http://localhost:8181`

### Acceso a las interfaces

- **GUI Principal:** Se abre automáticamente al ejecutar `main.py`
- **Aplicación Web:** <http://localhost:8181>
- **API Backend:** <http://localhost:5000>

---

## 🧪 Pruebas y calidad

- Ejecuta todos los tests:

  ```bash
  python -m unittest discover -s tests
  ```

- Cobertura y seguridad se validan automáticamente en CI/CD (GitHub Actions).

---

## 🔒 Seguridad y buenas prácticas

- **Análisis estático** con Bandit y pip-audit en cada commit/push.
- **CORS restringido** y validaciones estrictas de entrada.
- **No se almacenan credenciales sensibles** en texto plano.
- **Manejo global de errores** y límites de payload.
- **Documentación y código limpio** siguiendo PEP8 y buenas prácticas.

---

## 🛠️ Entornos y depuración

- El comportamiento de logs y prints de depuración se controla mediante la variable de entorno `APP_ENV`:
  - `APP_ENV=development`: Se muestran prints de depuración y logs detallados.
  - `APP_ENV=production` (por defecto): Solo se muestran logs importantes, sin prints de depuración.
- Usa la función `debug_print()` para mensajes de depuración que solo deben aparecer en desarrollo.

---

## 👨‍🏭 Créditos y soporte

- Desarrollado por **IA Punto Soluciones Tecnológicas** para **Industrias Pico S A S**.
- Para soporte, sugerencias o incidencias, abre un issue o contacta a los responsables del proyecto.

---
