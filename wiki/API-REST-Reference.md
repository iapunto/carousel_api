# 🌐 API REST Reference

Esta página documenta todos los endpoints disponibles en la API REST de carousel_api v2.6.0, incluyendo tanto el sistema Single-PLC (legacy) como el nuevo sistema Multi-PLC.

---

## 📋 Información General

- **Base URL:** `http://localhost:5000`
- **Versión API:** v1
- **Formato:** JSON
- **Autenticación:** No requerida (configurable)
- **CORS:** Habilitado para desarrollo

---

## 🏗️ Arquitecturas Soportadas

### Single-PLC (Legacy)

Para sistemas con una sola máquina controlada.

### Multi-PLC (Recomendado)

Para sistemas con múltiples máquinas controladas desde una sola API.

---

## 📡 Endpoints Single-PLC

### 1. Consultar Estado del Carrusel

```http
GET /v1/status
```

**Descripción:** Obtiene el estado actual del carrusel único.

**Respuesta Exitosa (200):**

```json
{
  "success": true,
  "data": {
    "status": {
      "READY": "OK",
      "RUN": "Detenido", 
      "MODO_OPERACION": "Remoto",
      "ALARMA": "Desactivada"
    },
    "position": 2,
    "raw_status": 218,
    "timestamp": "2025-01-27T10:30:45.123Z"
  },
  "error": null,
  "code": null
}
```

**Ejemplo cURL:**

```bash
curl -X GET http://localhost:5000/v1/status
```

### 2. Enviar Comando al Carrusel

```http
POST /v1/command
Content-Type: application/json
```

**Descripción:** Envía un comando al carrusel único.

**Body:**

```json
{
  "command": 1,
  "argument": 15
}
```

**Parámetros:**

- `command` (int): Tipo de comando (1 = mover a posición)
- `argument` (int): Posición destino (1-255)

**Respuesta Exitosa (200):**

```json
{
  "success": true,
  "data": {
    "command_sent": 1,
    "argument": 15,
    "result": "Comando ejecutado correctamente",
    "timestamp": "2025-01-27T10:30:45.123Z"
  },
  "error": null,
  "code": null
}
```

**Ejemplo cURL:**

```bash
curl -X POST http://localhost:5000/v1/command \
  -H "Content-Type: application/json" \
  -d '{"command":1,"argument":15}'
```

---

## 🏭 Endpoints Multi-PLC

### 1. Listar Todas las Máquinas

```http
GET /v1/machines
```

**Descripción:** Obtiene la lista de todas las máquinas configuradas.

**Respuesta Exitosa (200):**

```json
{
  "success": true,
  "data": [
    {
      "id": "machine_1",
      "name": "Carrusel Principal - Línea A",
      "ip": "192.168.1.50",
      "port": 3200,
      "type": "Real PLC",
      "status": "available",
      "description": "Carrusel principal de la línea de producción A"
    },
    {
      "id": "machine_2", 
      "name": "Carrusel Secundario - Línea A",
      "ip": "192.168.1.51",
      "port": 3200,
      "type": "Simulator",
      "status": "available",
      "description": "Carrusel secundario de respaldo"
    }
  ],
  "error": null,
  "code": null
}
```

**Ejemplo cURL:**

```bash
curl -X GET http://localhost:5000/v1/machines
```

### 2. Estado de Máquina Específica

```http
GET /v1/machines/{machine_id}/status
```

**Descripción:** Obtiene el estado de una máquina específica.

**Parámetros de URL:**

- `machine_id` (string): ID de la máquina (ej: "machine_1")

**Respuesta Exitosa (200):**

```json
{
  "success": true,
  "machine_id": "machine_1",
  "data": {
    "status": {
      "READY": "OK",
      "RUN": "Detenido",
      "MODO_OPERACION": "Remoto", 
      "ALARMA": "Desactivada"
    },
    "position": 15,
    "raw_status": 218,
    "connection_status": "connected",
    "last_update": "2025-01-27T10:30:45.123Z"
  },
  "error": null,
  "code": null
}
```

**Ejemplo cURL:**

```bash
curl -X GET http://localhost:5000/v1/machines/machine_1/status
```

### 3. Enviar Comando a Máquina Específica

```http
POST /v1/machines/{machine_id}/command
Content-Type: application/json
```

**Descripción:** Envía un comando a una máquina específica.

**Parámetros de URL:**

- `machine_id` (string): ID de la máquina

**Body:**

```json
{
  "command": 1,
  "argument": 25
}
```

**Parámetros del Body:**

- `command` (int): Tipo de comando (1 = mover a posición)
- `argument` (int): Posición destino (1-255)

**Respuesta Exitosa (200):**

```json
{
  "success": true,
  "machine_id": "machine_1",
  "data": {
    "command_sent": 1,
    "argument": 25,
    "result": "Comando ejecutado correctamente",
    "timestamp": "2025-01-27T10:30:45.123Z"
  },
  "error": null,
  "code": null
}
```

**Ejemplo cURL:**

```bash
curl -X POST http://localhost:5000/v1/machines/machine_1/command \
  -H "Content-Type: application/json" \
  -d '{"command":1,"argument":25}'
```

### 4. Mover a Posición Específica (Shortcut)

```http
POST /v1/machines/{machine_id}/move
Content-Type: application/json
```

**Descripción:** Comando simplificado para mover a una posición específica.

**Body:**

```json
{
  "position": 7
}
```

**Parámetros:**

- `position` (int): Posición destino (1-255)

**Respuesta Exitosa (200):**

```json
{
  "success": true,
  "machine_id": "machine_1",
  "data": {
    "command_sent": 1,
    "argument": 7,
    "result": "Movimiento a posición 7 ejecutado correctamente",
    "timestamp": "2025-01-27T10:30:45.123Z"
  },
  "error": null,
  "code": null
}
```

---

## 🔢 Códigos de Estado HTTP

| Código | Descripción | Cuándo se produce |
|--------|-------------|-------------------|
| **200** | OK | Operación exitosa |
| **400** | Bad Request | Parámetros inválidos o faltantes |
| **404** | Not Found | Máquina no encontrada (Multi-PLC) |
| **409** | Conflict | PLC ocupado por otro proceso |
| **429** | Too Many Requests | Demasiadas solicitudes (throttling) |
| **500** | Internal Server Error | Error interno del servidor |
| **503** | Service Unavailable | Servicio temporalmente no disponible |

---

## 📊 Formato de Respuestas

### Respuesta Exitosa

```json
{
  "success": true,
  "data": { /* datos específicos */ },
  "error": null,
  "code": null,
  "timestamp": "2025-01-27T10:30:45.123Z"
}
```

### Respuesta de Error

```json
{
  "success": false,
  "data": null,
  "error": "Descripción del error",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-27T10:30:45.123Z"
}
```

---

## 🏷️ Tipos de Comando

| Comando | Valor | Descripción | Parámetros |
|---------|-------|-------------|------------|
| **Mover a Posición** | 1 | Mueve el carrusel a la posición especificada | `argument`: posición (1-255) |

> **Nota:** Actualmente solo está implementado el comando de movimiento. Futuros comandos se agregarán en próximas versiones.

---

## 🔍 Estados Interpretados

### Status Fields

- **`READY`**: "OK" | "Fallo"
- **`RUN`**: "Detenido" | "En movimiento"
- **`MODO_OPERACION`**: "Remoto" | "Manual"
- **`ALARMA`**: "Desactivada" | "Activa"

### Connection Status (Multi-PLC)

- **`connected`**: Máquina conectada y disponible
- **`disconnected`**: Máquina desconectada
- **`error`**: Error de comunicación
- **`busy`**: Máquina ocupada procesando comando

---

## 🛡️ Validaciones

### Validaciones de Entrada

- **Posición:** Debe estar entre 1 y 255
- **Command:** Debe ser un entero válido (actualmente solo 1)
- **Machine ID:** Debe existir en la configuración (Multi-PLC)
- **Content-Type:** Debe ser `application/json` para POST

### Throttling

- **Límite:** 1 comando por segundo por máquina
- **Respuesta:** HTTP 429 si se excede el límite

---

## 🔧 Ejemplos de Integración

### Python con requests

```python
import requests
import json

# Configuración
BASE_URL = "http://localhost:5000"
MACHINE_ID = "machine_1"

# Obtener estado
response = requests.get(f"{BASE_URL}/v1/machines/{MACHINE_ID}/status")
status = response.json()
print(f"Posición actual: {status['data']['position']}")

# Enviar comando
command_data = {"command": 1, "argument": 10}
response = requests.post(
    f"{BASE_URL}/v1/machines/{MACHINE_ID}/command",
    headers={"Content-Type": "application/json"},
    data=json.dumps(command_data)
)
result = response.json()
print(f"Comando enviado: {result['success']}")
```

### JavaScript con fetch

```javascript
const BASE_URL = "http://localhost:5000";
const MACHINE_ID = "machine_1";

// Obtener estado
async function getStatus() {
    const response = await fetch(`${BASE_URL}/v1/machines/${MACHINE_ID}/status`);
    const status = await response.json();
    console.log(`Posición actual: ${status.data.position}`);
}

// Enviar comando
async function sendCommand(position) {
    const response = await fetch(`${BASE_URL}/v1/machines/${MACHINE_ID}/command`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            command: 1,
            argument: position
        })
    });
    const result = await response.json();
    console.log(`Comando enviado: ${result.success}`);
}
```

---

## 🔗 Enlaces Relacionados

- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[Guía de Integración WMS](Guía-de-Integración-WMS)** - Integración completa con WMS
- **[Códigos de Estado y Errores](Códigos-de-Estado-y-Errores)** - Referencia detallada de errores
- **[Ejemplos de Código](Ejemplos-de-Código)** - Más ejemplos de integración
