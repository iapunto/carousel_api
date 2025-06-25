# 🔌 WebSocket API

La API WebSocket de carousel_api proporciona comunicación en tiempo real para recibir actualizaciones de estado y enviar comandos de manera asíncrona.

---

## 📋 Información General

- **URL:** `ws://localhost:8765`
- **Protocolo:** WebSocket RFC 6455
- **Formato:** JSON
- **Autenticación:** No requerida (configurable)
- **Heartbeat:** Ping/Pong automático cada 30s

---

## 🔗 Conexión

### Establecer Conexión

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = function(event) {
    console.log('Conectado al WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Mensaje recibido:', data);
};

ws.onerror = function(error) {
    console.error('Error WebSocket:', error);
};

ws.onclose = function(event) {
    console.log('Conexión cerrada:', event.code, event.reason);
};
```

### Python con websockets

```python
import asyncio
import websockets
import json

async def connect_websocket():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Recibir mensaje de bienvenida
        welcome = await websocket.recv()
        print(f"Bienvenida: {welcome}")
        
        # Enviar mensaje
        message = {
            "type": "get_status",
            "machine_id": "machine_1",
            "timestamp": "2025-01-27T10:30:00.000Z"
        }
        await websocket.send(json.dumps(message))
        
        # Escuchar respuestas
        async for message in websocket:
            data = json.loads(message)
            print(f"Recibido: {data}")

# Ejecutar
asyncio.run(connect_websocket())
```

---

## 📨 Tipos de Mensaje

### 1. Mensaje de Bienvenida (Automático)

**Enviado por:** Servidor (automático al conectar)

```json
{
  "type": "welcome",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "mode": "multi-plc",
  "server_info": {
    "version": "2.6.0",
    "capabilities": [
      "status_updates", 
      "command_execution", 
      "real_time_notifications"
    ]
  },
  "machines": [
    {
      "id": "machine_1",
      "name": "Carrusel Principal",
      "ip": "192.168.1.50",
      "port": 3200,
      "type": "Real PLC"
    },
    {
      "id": "machine_2",
      "name": "Carrusel Secundario",
      "ip": "192.168.1.51",
      "port": 3200,
      "type": "Simulator"
    }
  ]
}
```

### 2. Solicitar Estado

**Enviado por:** Cliente

```json
{
  "type": "get_status",
  "machine_id": "machine_1",
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

**Respuesta del servidor:**

```json
{
  "type": "machine_status",
  "machine_id": "machine_1",
  "status": {
    "READY": "OK",
    "RUN": "Detenido",
    "MODO_OPERACION": "Remoto",
    "ALARMA": "Desactivada"
  },
  "position": 15,
  "raw_status": 218,
  "connection_status": "connected",
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

### 3. Enviar Comando

**Enviado por:** Cliente

```json
{
  "type": "send_command",
  "machine_id": "machine_1",
  "command": {
    "command": 1,
    "argument": 25
  },
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

**Respuesta del servidor:**

```json
{
  "type": "command_result",
  "machine_id": "machine_1",
  "success": true,
  "data": {
    "command_sent": 1,
    "argument": 25,
    "result": "Comando ejecutado correctamente"
  },
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

### 4. Suscribirse a Actualizaciones

**Enviado por:** Cliente

```json
{
  "type": "subscribe",
  "subscription_type": "status_updates",
  "machine_ids": ["machine_1", "machine_2"],
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

**Confirmación del servidor:**

```json
{
  "type": "subscription_confirmed",
  "subscription_type": "status_updates",
  "machine_ids": ["machine_1", "machine_2"],
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

### 5. Broadcast de Estado (Automático)

**Enviado por:** Servidor (automático cuando cambia el estado)

```json
{
  "type": "status_broadcast",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "status": {
    "machine_1": {
      "status": {
        "READY": "OK",
        "RUN": "En movimiento",
        "MODO_OPERACION": "Remoto",
        "ALARMA": "Desactivada"
      },
      "position": 25,
      "raw_status": 219,
      "connection_status": "connected"
    },
    "machine_2": {
      "status": {
        "READY": "OK",
        "RUN": "Detenido",
        "MODO_OPERACION": "Remoto",
        "ALARMA": "Desactivada"
      },
      "position": 10,
      "raw_status": 218,
      "connection_status": "connected"
    }
  }
}
```

### 6. Notificación de Error

**Enviado por:** Servidor

```json
{
  "type": "error",
  "error": "Machine not found",
  "code": "MACHINE_NOT_FOUND",
  "machine_id": "invalid_machine",
  "timestamp": "2025-01-27T10:30:00.000Z"
}
```

---

## 🔔 Tipos de Suscripción

### Status Updates

Recibe actualizaciones automáticas cuando cambia el estado de las máquinas.

```json
{
  "type": "subscribe",
  "subscription_type": "status_updates",
  "machine_ids": ["machine_1", "machine_2"]
}
```

### Command Results

Recibe notificaciones cuando se ejecutan comandos en las máquinas.

```json
{
  "type": "subscribe",
  "subscription_type": "command_results",
  "machine_ids": ["machine_1"]
}
```

### All Events

Recibe todas las notificaciones disponibles.

```json
{
  "type": "subscribe",
  "subscription_type": "all_events"
}
```

---

## 🔧 Ejemplos de Implementación

### Cliente JavaScript Completo

```javascript
class CarouselWebSocketClient {
    constructor(url = 'ws://localhost:8765') {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 5;
        this.reconnectAttempts = 0;
    }

    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = (event) => {
            console.log('Conectado al WebSocket');
            this.reconnectAttempts = 0;
            this.subscribeToUpdates();
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = (event) => {
            console.log('Conexión cerrada:', event.code);
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('Error WebSocket:', error);
        };
    }

    handleMessage(data) {
        switch(data.type) {
            case 'welcome':
                console.log('Bienvenida recibida:', data);
                break;
            case 'status_broadcast':
                this.onStatusUpdate(data.status);
                break;
            case 'command_result':
                this.onCommandResult(data);
                break;
            case 'error':
                console.error('Error del servidor:', data);
                break;
        }
    }

    subscribeToUpdates() {
        this.send({
            type: 'subscribe',
            subscription_type: 'status_updates',
            timestamp: new Date().toISOString()
        });
    }

    sendCommand(machineId, command, argument) {
        this.send({
            type: 'send_command',
            machine_id: machineId,
            command: {
                command: command,
                argument: argument
            },
            timestamp: new Date().toISOString()
        });
    }

    getStatus(machineId) {
        this.send({
            type: 'get_status',
            machine_id: machineId,
            timestamp: new Date().toISOString()
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket no está conectado');
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Intentando reconectar... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectInterval);
        } else {
            console.error('Máximo número de intentos de reconexión alcanzado');
        }
    }

    onStatusUpdate(status) {
        // Implementar lógica de actualización de UI
        console.log('Estado actualizado:', status);
    }

    onCommandResult(result) {
        // Implementar lógica de respuesta a comandos
        console.log('Resultado de comando:', result);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Uso
const client = new CarouselWebSocketClient();
client.connect();

// Enviar comando
client.sendCommand('machine_1', 1, 25);

// Obtener estado
client.getStatus('machine_1');
```

### Cliente Python Asíncrono

```python
import asyncio
import websockets
import json
from datetime import datetime

class CarouselWebSocketClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.running = False

    async def connect(self):
        """Conectar al WebSocket"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            print("Conectado al WebSocket")
            
            # Suscribirse a actualizaciones
            await self.subscribe_to_updates()
            
            # Escuchar mensajes
            await self.listen()
            
        except Exception as e:
            print(f"Error de conexión: {e}")

    async def listen(self):
        """Escuchar mensajes del servidor"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("Conexión cerrada")
            self.running = False

    async def handle_message(self, data):
        """Manejar mensajes recibidos"""
        message_type = data.get('type')
        
        if message_type == 'welcome':
            print(f"Bienvenida: {data}")
        elif message_type == 'status_broadcast':
            await self.on_status_update(data['status'])
        elif message_type == 'command_result':
            await self.on_command_result(data)
        elif message_type == 'error':
            print(f"Error del servidor: {data}")

    async def subscribe_to_updates(self):
        """Suscribirse a actualizaciones de estado"""
        message = {
            "type": "subscribe",
            "subscription_type": "status_updates",
            "timestamp": datetime.now().isoformat()
        }
        await self.send(message)

    async def send_command(self, machine_id, command, argument):
        """Enviar comando a una máquina"""
        message = {
            "type": "send_command",
            "machine_id": machine_id,
            "command": {
                "command": command,
                "argument": argument
            },
            "timestamp": datetime.now().isoformat()
        }
        await self.send(message)

    async def get_status(self, machine_id):
        """Obtener estado de una máquina"""
        message = {
            "type": "get_status",
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.send(message)

    async def send(self, data):
        """Enviar mensaje al servidor"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(data))
        else:
            print("WebSocket no está conectado")

    async def on_status_update(self, status):
        """Manejar actualizaciones de estado"""
        print(f"Estado actualizado: {status}")

    async def on_command_result(self, result):
        """Manejar resultados de comandos"""
        print(f"Resultado de comando: {result}")

    async def disconnect(self):
        """Desconectar del WebSocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

# Uso
async def main():
    client = CarouselWebSocketClient()
    
    # Conectar
    await client.connect()
    
    # Enviar comando
    await client.send_command('machine_1', 1, 25)
    
    # Obtener estado
    await client.get_status('machine_1')
    
    # Mantener conexión
    while client.running:
        await asyncio.sleep(1)

# Ejecutar
if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛡️ Manejo de Errores

### Códigos de Error Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| `MACHINE_NOT_FOUND` | Máquina no existe | Verificar machine_id |
| `INVALID_COMMAND` | Comando inválido | Verificar formato del comando |
| `CONNECTION_ERROR` | Error de conexión con PLC | Verificar red y configuración |
| `BUSY` | Máquina ocupada | Esperar y reintentar |
| `INVALID_MESSAGE_FORMAT` | Formato de mensaje inválido | Verificar estructura JSON |

### Reconexión Automática

```javascript
function setupReconnection(ws, url, maxAttempts = 5) {
    let attempts = 0;
    
    ws.onclose = function(event) {
        if (attempts < maxAttempts) {
            attempts++;
            console.log(`Reconectando... (${attempts}/${maxAttempts})`);
            setTimeout(() => {
                const newWs = new WebSocket(url);
                setupReconnection(newWs, url, maxAttempts);
            }, 2000 * attempts); // Backoff exponencial
        }
    };
}
```

---

## 🔗 Enlaces Relacionados

- **[API REST Reference](API-REST-Reference)** - Documentación REST
- **[Ejemplos de Código](Ejemplos-de-Código)** - Más ejemplos de integración
- **[Guía de Integración WMS](Guía-de-Integración-WMS)** - Integración completa
- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Solución de problemas
