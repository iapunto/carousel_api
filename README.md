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
- **Simulador de PLC** para pruebas sin hardware.
- **Comunicación en tiempo real** mediante Socket.IO (sin polling agresivo).
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

```
[GUI] <---Socket.IO---> [API Flask] <---TCP/IP---> [PLC Delta / Simulador]
```

- `api.py`: API principal y servidor de eventos.
- `models/plc.py`: Comunicación con PLC real.
- `models/plc_simulator.py`: Simulador de PLC.
- `controllers/carousel_controller.py`: Lógica de negocio y validaciones.
- `commons/utils.py`: Utilidades y validaciones centralizadas.
- `main.py`: Lanzador de la aplicación (API + GUI).

---

## 🔗 Endpoints principales

| Método | Ruta           | Descripción                        | Parámetros         |
|--------|----------------|------------------------------------|--------------------|
| GET    | /v1/status     | Consulta el estado actual del PLC  | -                  |
| POST   | /v1/command    | Envía un comando al PLC/simulador  | `command`, `argument` |

**Ejemplo de uso:**

```bash
curl -X GET http://localhost:5000/v1/status
curl -X POST http://localhost:5000/v1/command -H "Content-Type: application/json" -d '{"command":1,"argument":3}'
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

Configura `config.json` según tu entorno (ver ejemplo en el archivo).

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

## 👨‍🏭 Créditos y soporte

- Desarrollado por **IA Punto Soluciones Tecnológicas** para **Industrias Pico S A S**.
- Para soporte, sugerencias o incidencias, abre un issue o contacta a los responsables del proyecto.

---
