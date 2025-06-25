# 🚀 API Multi-PLC - Guía de Integración

## Descripción General

La API Multi-PLC permite controlar múltiples carruseles industriales desde sistemas WMS externos mediante:

- **REST API**: Para operaciones puntuales
- **WebSocket**: Para comunicación en tiempo real

## 🏗️ Arquitectura

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   WMS       │    │  API Server  │    │  PLCs/Machines  │
│             │◄──►│              │◄──►│                 │
│ - REST      │    │ - Multi-PLC  │    │ - machine_1     │
│ - WebSocket │    │ - WebSocket  │    │ - machine_2     │
└─────────────┘    └──────────────┘    │ - machine_N     │
                                       └─────────────────┘
```

## 📋 Configuración de Máquinas

### Archivo: `config_multi_plc.json`

```json
{
  "plc_machines": [
    {
      "id": "machine_1",
      "name": "Carrusel Principal - Línea A",
      "ip": "192.168.1.50",
      "port": 3200,
      "simulator": false,
      "description": "Carrusel principal de la línea de producción A"
    },
    {
      "id": "machine_2", 
      "name": "Carrusel Secundario - Línea A",
      "ip": "192.168.1.51",
      "port": 3200,
      "simulator": false,
      "description": "Carrusel secundario de respaldo"
    }
  ],
  "api_config": {
    "port": 5000,
    "websocket_port": 8765
  }
}
```

## 🌐 REST API Endpoints

### Base URL: `http://localhost:5000`

### 1. Listar Máquinas

```http
GET /v1/machines
```

**Respuesta:**

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
      "status": "available"
    }
  ],
  "error": null,
  "code": null
}
```

### 2. Estado de Máquina Específica

```http
GET /v1/machines/{machine_id}/status
```

**Ejemplo:**

```http
GET /v1/machines/machine_1/status
```

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "position": 3,
    "status": {
      "moving": false,
      "ready": true,
      "error": false
    },
    "raw_status": 128,
    "timestamp": "2025-03-13T10:30:00"
  },
  "error": null,
  "code": null
}
```

### 3. Enviar Comando a Máquina

```http
POST /v1/machines/{machine_id}/command
Content-Type: application/json

{
  "command": 1,
  "argument": 5
}
```

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "command_sent": 1,
    "argument": 5,
    "result": "Comando ejecutado correctamente",
    "timestamp": "2025-03-13T10:30:00"
  },
  "error": null,
  "code": null
}
```

### 4. Mover a Posición Específica

```http
POST /v1/machines/{machine_id}/move
Content-Type: application/json

{
  "position": 7
}
```

## 🔌 WebSocket API

### URL: `ws://localhost:8765`

### Conexión y Mensajes

#### 1. Mensaje de Bienvenida (Automático)

```json
{
  "type": "welcome",
  "timestamp": "2025-03-13T10:30:00.000Z",
  "mode": "multi-plc",
  "server_info": {
    "version": "1.0.0",
    "capabilities": ["status_updates", "command_execution", "real_time_notifications"]
  },
  "machines": [
    {
      "id": "machine_1",
      "name": "Carrusel Principal",
      "ip": "192.168.1.50",
      "port": 3200
    }
  ]
}
```

#### 2. Solicitar Estado

**Enviar:**

```json
{
  "type": "get_status",
  "machine_id": "machine_1",
  "timestamp": "2025-03-13T10:30:00.000Z"
}
```

**Recibir:**

```json
{
  "type": "machine_status",
  "machine_id": "machine_1",
  "status": {
    "position": 3,
    "status": {
      "moving": false,
      "ready": true
    }
  },
  "timestamp": "2025-03-13T10:30:00.000Z"
}
```

#### 3. Enviar Comando

**Enviar:**

```json
{
  "type": "send_command",
  "machine_id": "machine_1",
  "command": 1,
  "argument": 5,
  "timestamp": "2025-03-13T10:30:00.000Z"
}
```

**Recibir:**

```json
{
  "type": "command_result",
  "machine_id": "machine_1",
  "command": 1,
  "argument": 5,
  "result": {
    "success": true,
    "message": "Movimiento iniciado a posición 5"
  },
  "timestamp": "2025-03-13T10:30:00.000Z"
}
```

#### 4. Broadcast de Estado (Automático cada 2 segundos)

```json
{
  "type": "status_broadcast",
  "status": {
    "machine_1": {
      "position": 3,
      "status": {
        "moving": false,
        "ready": true
      }
    },
    "machine_2": {
      "position": 7,
      "status": {
        "moving": true,
        "ready": false
      }
    }
  },
  "timestamp": "2025-03-13T10:30:00.000Z"
}
```

#### 5. Notificación de Comando Ejecutado por Otro Cliente

```json
{
  "type": "command_executed",
  "machine_id": "machine_1",
  "command": 1,
  "argument": 5,
  "timestamp": "2025-03-13T10:30:00.000Z"
}
```

## 💻 Ejemplos de Código

### Python (REST API)

```python
import requests
import json

# Configuración
BASE_URL = "http://localhost:5000"
headers = {"Content-Type": "application/json"}

# Listar máquinas
response = requests.get(f"{BASE_URL}/v1/machines")
machines = response.json()["data"]
print(f"Máquinas disponibles: {len(machines)}")

# Obtener estado de máquina
machine_id = "machine_1"
response = requests.get(f"{BASE_URL}/v1/machines/{machine_id}/status")
status = response.json()["data"]
print(f"Posición actual: {status['position']}")

# Mover a posición 5
command_data = {"command": 1, "argument": 5}
response = requests.post(
    f"{BASE_URL}/v1/machines/{machine_id}/command",
    headers=headers,
    data=json.dumps(command_data)
)
result = response.json()
print(f"Comando resultado: {result}")
```

### Python (WebSocket)

```python
import asyncio
import websockets
import json

async def wms_client():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        # Esperar mensaje de bienvenida
        welcome = await websocket.recv()
        data = json.loads(welcome)
        print(f"Conectado en modo: {data['mode']}")
        
        # Solicitar estado
        await websocket.send(json.dumps({
            "type": "get_status",
            "machine_id": "machine_1"
        }))
        
        # Recibir respuesta
        response = await websocket.recv()
        status = json.loads(response)
        print(f"Estado: {status}")
        
        # Enviar comando
        await websocket.send(json.dumps({
            "type": "send_command",
            "machine_id": "machine_1",
            "command": 1,
            "argument": 5
        }))

# Ejecutar
asyncio.run(wms_client())
```

### C# (.NET)

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

public class WMSClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl = "http://localhost:5000";
    
    public WMSClient()
    {
        _httpClient = new HttpClient();
    }
    
    public async Task<dynamic> GetMachinesAsync()
    {
        var response = await _httpClient.GetAsync($"{_baseUrl}/v1/machines");
        var content = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject(content);
    }
    
    public async Task<dynamic> SendCommandAsync(string machineId, int command, int? argument = null)
    {
        var payload = new { command = command, argument = argument };
        var json = JsonConvert.SerializeObject(payload);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await _httpClient.PostAsync(
            $"{_baseUrl}/v1/machines/{machineId}/command", 
            content
        );
        
        var responseContent = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject(responseContent);
    }
}
```

## 🚦 Códigos de Estado

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 400 | Parámetros inválidos |
| 404 | Máquina no encontrada |
| 409 | Máquina ocupada |
| 500 | Error interno del servidor |

## 🔧 Comandos PLC

| Comando | Descripción | Argumento |
|---------|-------------|-----------|
| 0 | Estado actual | N/A |
| 1 | Mover a posición | Posición (0-9) |
| 2 | Parar movimiento | N/A |
| 3 | Reset | N/A |
| 4 | Calibrar | N/A |

## 🛡️ Seguridad y Mejores Prácticas

### 1. Autenticación (Futuro)

- Implementar tokens JWT
- Validación de origen IP
- Rate limiting

### 2. Manejo de Errores

```python
try:
    response = requests.get(f"{BASE_URL}/v1/machines/{machine_id}/status")
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            # Procesar datos
            pass
        else:
            print(f"Error: {data['error']}")
    else:
        print(f"HTTP Error: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Connection Error: {e}")
```

### 3. Reconexión WebSocket

```python
async def robust_websocket_client():
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with websockets.connect("ws://localhost:8765") as websocket:
                # Cliente WebSocket normal
                retry_count = 0  # Reset en conexión exitosa
                
        except websockets.exceptions.ConnectionClosed:
            retry_count += 1
            await asyncio.sleep(2 ** retry_count)  # Backoff exponencial
```

## 📊 Monitoreo y Logs

### Logs de API

- Ubicación: `logs/carousel_api.log`
- Formato: `timestamp - logger - level - message`
- Rotación automática

### Métricas Importantes

- Tiempo de respuesta por endpoint
- Número de clientes WebSocket conectados
- Errores de comunicación PLC
- Comandos ejecutados por máquina

## 🔄 Integración con WMS

### Flujo Típico

1. **Conexión**: WMS se conecta vía WebSocket
2. **Descubrimiento**: Obtiene lista de máquinas disponibles
3. **Suscripción**: Se suscribe a actualizaciones de estado
4. **Operación**: Envía comandos según necesidades
5. **Monitoreo**: Recibe broadcasts de estado en tiempo real

### Casos de Uso Comunes

- **Picking**: Mover carrusel a posición de producto
- **Inventario**: Consultar estado de todas las máquinas
- **Mantenimiento**: Monitorear errores y alertas
- **Sincronización**: Coordinar múltiples carruseles

## 🆘 Troubleshooting

### Problemas Comunes

1. **Error 404 - Máquina no encontrada**
   - Verificar ID de máquina en configuración
   - Comprobar archivo `config_multi_plc.json`

2. **Error 500 - Error de comunicación**
   - Verificar conectividad de red al PLC
   - Comprobar que el PLC esté encendido

3. **WebSocket desconexión**
   - Implementar reconexión automática
   - Verificar firewall y puertos

### Diagnóstico

```bash
# Verificar API está ejecutándose
curl http://localhost:5000/v1/health

# Probar conectividad WebSocket
wscat -c ws://localhost:8765

# Ver logs en tiempo real
tail -f logs/carousel_api.log
```

## 📞 Soporte

Para soporte técnico contactar:

- **Email**: <soporte@iapunto.com>
- **Teléfono**: +57 (316) 376 9935
- **Documentación**: [Wiki interno]

---

**Versión**: 1.0.0  
**Última actualización**: 2025-03-13  
**Autor**: IA Punto: Soluciones Tecnológicas
