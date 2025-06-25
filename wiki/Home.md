# 🏭 Carousel API - Wiki de Documentación

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-API-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Multi-PLC](https://img.shields.io/badge/Multi--PLC-v2.6.0-green)](https://github.com/iapunto/carousel_api)
[![License](https://img.shields.io/github/license/iapunto/carousel_api?color=blue)](LICENSE)

---

## 🚀 Bienvenido a la Documentación de Carousel API

**carousel_api** es una solución integral para la gestión y control de sistemas de almacenamiento automatizado tipo carrusel vertical, orientada a la industria 4.0. Permite la integración directa con hardware industrial (PLC Delta AS Series) o su simulador, facilitando tanto la operación en entornos productivos como el desarrollo y pruebas seguras.

---

## 📚 Navegación del Wiki

### 🏗️ Arquitectura y Configuración

- **[Arquitectura del Sistema](Arquitectura-del-Sistema)** - Diseño general y componentes
- **[Configuración Multi-PLC](Configuración-Multi-PLC)** - Setup para múltiples máquinas
- **[Instalación y Configuración](Instalación-y-Configuración)** - Guía de instalación completa

### 🌐 API Documentation

- **[API REST Reference](API-REST-Reference)** - Documentación completa de endpoints
- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[Códigos de Estado y Errores](Códigos-de-Estado-y-Errores)** - Referencia de códigos

### 🔗 Integración

- **[Guía de Integración WMS](Guía-de-Integración-WMS)** - Integración con sistemas de almacén
- **[Ejemplos de Código](Ejemplos-de-Código)** - Ejemplos prácticos en diferentes lenguajes
- **[Patrones de Integración](Patrones-de-Integración)** - Mejores prácticas de integración

### 🖥️ Interfaces de Usuario

- **[Aplicación Web](Aplicación-Web)** - Control remoto web moderno
- **[GUI de Escritorio](GUI-de-Escritorio)** - Interfaz de escritorio con CustomTkinter

### 🛠️ Desarrollo y Mantenimiento

- **[Guía de Desarrollo](Guía-de-Desarrollo)** - Para desarrolladores del proyecto
- **[Testing y QA](Testing-y-QA)** - Pruebas y aseguramiento de calidad
- **[Roadmap](Roadmap)** - Futuras funcionalidades y mejoras

### 🆘 Soporte

- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Preguntas frecuentes y soluciones
- **[Logs y Debugging](Logs-y-Debugging)** - Diagnóstico y depuración

---

## 🎯 Características Principales

### 🏭 **Sistema Multi-PLC**

- Gestión de múltiples carruseles desde una sola interfaz
- Configuración dinámica de máquinas
- Balanceado de carga automático

### 🌐 **API REST Robusta**

- Endpoints RESTful para integración con sistemas externos
- Documentación OpenAPI/Swagger
- Autenticación y autorización configurable

### ⚡ **Comunicación en Tiempo Real**

- WebSocket para actualizaciones instantáneas
- Socket.IO para compatibilidad con navegadores
- Eventos de estado en tiempo real

### 🖥️ **Interfaces Modernas**

- Aplicación web responsive con diseño glassmorphism
- GUI de escritorio con CustomTkinter
- Panel de control unificado

### 🔧 **Simulador Integrado**

- Simulador de PLC para desarrollo y pruebas
- Modo híbrido: PLCs reales + simulados
- Testing sin hardware

---

## 🚀 Quick Start

```bash
# Clonar el repositorio
git clone https://github.com/iapunto/carousel_api.git
cd carousel_api

# Instalar dependencias
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar máquinas (opcional)
cp config_multi_plc.json.example config_multi_plc.json

# Ejecutar aplicación
python main.py
```

### 🌐 Acceso a las Interfaces

- **🖥️ GUI Principal:** Se abre automáticamente
- **🌐 Aplicación Web:** [http://localhost:8181](http://localhost:8181)
- **🔌 API Backend:** [http://localhost:5000](http://localhost:5000)
- **📡 WebSocket:** ws://localhost:8765

---

## 📊 Arquitectura General

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   WMS       │    │  API Server  │    │  PLCs/Machines  │
│             │◄──►│              │◄──►│                 │
│ - REST      │    │ - Multi-PLC  │    │ - machine_1     │
│ - WebSocket │    │ - WebSocket  │    │ - machine_2     │
└─────────────┘    └──────────────┘    │ - machine_N     │
                                       └─────────────────┘
```

---

## 🛠️ Tecnologías

- **Backend:** Python 3.12+, Flask, Flask-SocketIO
- **Frontend Web:** HTML5, CSS3, JavaScript ES6+
- **GUI:** CustomTkinter, tkinter
- **Comunicación:** WebSocket, Socket.IO, TCP/IP
- **Base de Datos:** JSON (configuración), SQLite (logs)
- **Testing:** Pytest, Coverage.py
- **Seguridad:** Bandit, pip-audit

---

## 👥 Créditos

- **Desarrollado por:** IA Punto Soluciones Tecnológicas
- **Cliente:** Industrias Pico S.A.S
- **Versión:** v2.6.0 (Multi-PLC)
- **Licencia:** [Ver LICENSE](https://github.com/iapunto/carousel_api/blob/main/LICENSE)

---

## 📞 Soporte

Para soporte técnico, sugerencias o reportar incidencias:

- 🐛 **Issues:** [GitHub Issues](https://github.com/iapunto/carousel_api/issues)
- 📧 **Email:** <soporte@iapunto.com>
- 📚 **Documentación:** Este wiki
- 💬 **Discusiones:** [GitHub Discussions](https://github.com/iapunto/carousel_api/discussions)

---

## 🔄 Última Actualización

**Fecha:** 2025-01-27  
**Versión:** v2.6.0  
**Cambios:** Documentación completa del sistema Multi-PLC, aplicación web modernizada

---

> 💡 **Tip:** Usa la navegación lateral o los enlaces de arriba para explorar la documentación completa. Cada sección incluye ejemplos prácticos y guías paso a paso.
