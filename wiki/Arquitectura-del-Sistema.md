# 🏗️ Arquitectura del Sistema

Documentación detallada de la arquitectura de carousel_api v2.6.0, incluyendo componentes, flujos de datos y patrones de diseño.

---

## 📊 Visión General

carousel_api está diseñado como una arquitectura modular que soporta tanto sistemas Single-PLC (legacy) como Multi-PLC (recomendado), con múltiples interfaces de usuario y APIs robustas.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAROUSEL API v2.6.0                     │
├─────────────────────────────────────────────────────────────────┤
│  🖥️ GUI Desktop    🌐 Web App    📱 Mobile    🔗 External APIs  │
├─────────────────────────────────────────────────────────────────┤
│           🌐 REST API           📡 WebSocket API                │
├─────────────────────────────────────────────────────────────────┤
│               🏭 Multi-PLC Manager / Single-PLC                 │
├─────────────────────────────────────────────────────────────────┤
│  🔧 PLC Real #1   🔧 PLC Real #2   🎮 Simulador #3   🎮 Sim #4  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes Principales

### 1. **Capa de Presentación**

#### GUI de Escritorio (`gui/`)

- **Tecnología:** CustomTkinter
- **Archivo principal:** `gui/main_gui.py`
- **Características:**
  - Interfaz nativa multiplataforma
  - Panel de comandos con selector de máquinas
  - Sistema de notificaciones en tiempo real
  - Configuración visual de parámetros

#### Aplicación Web (`web_remote_control.py`)

- **Tecnología:** HTML5, CSS3, JavaScript ES6+
- **Puerto:** 8181
- **Características:**
  - Diseño responsive (móvil/desktop)
  - Glassmorphism UI
  - Control de múltiples máquinas
  - Notificaciones en tiempo real

### 2. **Capa de API**

#### REST API (`api.py`)

- **Framework:** Flask + Flask-SocketIO
- **Puerto:** 5000
- **Endpoints principales:**
  - `/v1/status` (Single-PLC)
  - `/v1/command` (Single-PLC)
  - `/v1/machines` (Multi-PLC)
  - `/v1/machines/{id}/status` (Multi-PLC)
  - `/v1/machines/{id}/command` (Multi-PLC)

#### WebSocket API

- **Puerto:** 8765
- **Protocolo:** WebSocket RFC 6455
- **Características:**
  - Comunicación bidireccional
  - Eventos en tiempo real
  - Suscripciones selectivas
  - Reconexión automática

### 3. **Capa de Lógica de Negocio**

#### Controladores (`controllers/`)

- **Carousel Controller:** Lógica principal
- **Command Handler:** Procesamiento de comandos
- **Validaciones:** Entrada y estados

#### Gestión de PLCs (`models/`)

- **PLC Manager:** Administrador Multi-PLC
- **PLC:** Comunicación TCP/IP real
- **PLC Simulator:** Simulador integrado

---

## 🔄 Flujos de Datos

### Comando Multi-PLC

```
Cliente → API → Validación → PLC Manager → PLC → Respuesta → WebSocket Broadcast
```

### Polling de Estados

```
Timer → PLC Manager → PLCs → Cache → WebSocket → Clientes
```

---

## 🔧 Configuración

### Multi-PLC (`config_multi_plc.json`)

```json
{
  "plc_machines": [
    {
      "id": "machine_1",
      "name": "Carrusel Principal",
      "ip": "192.168.1.50",
      "port": 3200,
      "simulator": false
    }
  ],
  "api_config": {
    "port": 5000,
    "websocket_port": 8765
  }
}
```

### Single-PLC (`config.json`)

```json
{
  "plc_ip": "192.168.1.50",
  "plc_port": 3200,
  "api_port": 5000,
  "simulator_enabled": false
}
```

---

## 🛡️ Seguridad y Robustez

- **Validación de entrada** con schemas
- **Rate limiting** por máquina
- **Manejo de errores** robusto
- **Timeouts** configurables
- **Reintentos** automáticos
- **Logs** estructurados

---

## 📊 Escalabilidad

- **Concurrencia** con ThreadPoolExecutor
- **Cache** de estados con TTL
- **Pool de conexiones** TCP
- **Métricas** de rendimiento
- **Health checks** automáticos

---

## 🔗 Enlaces Relacionados

- **[API REST Reference](API-REST-Reference)** - Documentación de endpoints
- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[Guía de Integración WMS](Guía-de-Integración-WMS)** - Integración con sistemas WMS
- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Solución de problemas
