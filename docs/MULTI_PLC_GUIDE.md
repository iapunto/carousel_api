# Guía del Sistema Multi-PLC

## Descripción General

El sistema ahora soporta múltiples PLCs simultáneamente, permitiendo controlar varios carruseles desde una sola API. Cada máquina tiene su propio PLC con IP diferente pero el mismo puerto.

## Configuración

### Configuración Multi-PLC (`config_multi_plc.json`)

```json
{
  "api_config": {
    "port": 5000,
    "debug": false,
    "allowed_origins": "http://localhost,http://127.0.0.1,http://192.168.1.0/24"
  },
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
      "id": "machine_7",
      "name": "Carrusel Línea C - Estación 7",
      "ip": "192.168.1.57",
      "port": 3200,
      "simulator": false,
      "description": "Carrusel de la línea C, estación 7"
    }
  ],
  "logging": {
    "level": "INFO",
    "connection_log_enabled": true
  }
}
```

### Compatibilidad con Configuración Single-PLC

El sistema mantiene compatibilidad con `config.json` existente. Si no existe `config_multi_plc.json`, usará la configuración single-PLC.

## Nuevos Endpoints de la API

### 1. Listar Máquinas Disponibles

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
    },
    {
      "id": "machine_7",
      "name": "Carrusel Línea C - Estación 7",
      "ip": "192.168.1.57",
      "port": 3200,
      "type": "Real PLC",
      "status": "available"
    }
  ]
}
```

### 2. Estado de una Máquina Específica

```http
GET /v1/machines/{machine_id}/status
```

**Ejemplo:**

```http
GET /v1/machines/machine_7/status
```

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "status": {
      "READY": "El equipo está listo para operar",
      "MOVING": "No se está moviendo",
      "ERROR": "Sin errores"
    },
    "position": 3,
    "raw_status": 128
  },
  "machine_id": "machine_7"
}
```

### 3. Enviar Comando a una Máquina Específica

```http
POST /v1/machines/{machine_id}/command
```

**Body:**

```json
{
  "command": 1,
  "argument": 3
}
```

**Ejemplo para máquina 7:**

```http
POST /v1/machines/machine_7/command
Content-Type: application/json

{
  "command": 1,
  "argument": 3
}
```

### 4. Mover Máquina a Posición Específica

```http
POST /v1/machines/{machine_id}/move
```

**Body:**

```json
{
  "position": 3
}
```

## Endpoints de Compatibilidad

Los endpoints existentes siguen funcionando usando la primera máquina disponible:

- `GET /v1/status` - Estado de la primera máquina
- `POST /v1/command` - Comando a la primera máquina (o especificar `machine_id` en el body)

## Logging de Conexiones

El sistema registra todas las conexiones y comandos en `client_connections.log`:

```
2025-01-XX 10:30:15 | INFO | STATUS_REQUEST | Cliente: 192.168.1.100 | Máquina: machine_7 | Timestamp: 2025-01-XX...
2025-01-XX 10:30:15 | INFO | STATUS_RESPONSE | Cliente: 192.168.1.100 | Máquina: machine_7 | Resultado: OK | Estado: El equipo está listo para operar
2025-01-XX 10:30:20 | INFO | COMMAND_REQUEST | Cliente: 192.168.1.100 | Máquina: machine_7 | Comando: 1 | Argumento: 3
2025-01-XX 10:30:20 | INFO | COMMAND_RESPONSE | Cliente: 192.168.1.100 | Máquina: machine_7 | Comando: 1 | Argumento: 3 | Resultado: OK | Nueva_posición: 3
```

## Ejemplos de Uso para WMS

### Ejemplo 1: Verificar máquinas disponibles

```python
import requests

# Obtener lista de máquinas
response = requests.get('http://192.168.1.10:5000/v1/machines')
machines = response.json()['data']

for machine in machines:
    print(f"Máquina: {machine['id']} - {machine['name']} ({machine['ip']})")
```

### Ejemplo 2: Controlar máquina específica

```python
import requests

# Mover llanta a canguilón 3 de la máquina 7
machine_id = "machine_7"
target_position = 3

# Verificar estado actual
status_response = requests.get(f'http://192.168.1.10:5000/v1/machines/{machine_id}/status')
current_status = status_response.json()
print(f"Estado actual de {machine_id}: Posición {current_status['data']['position']}")

# Mover a posición objetivo
move_response = requests.post(
    f'http://192.168.1.10:5000/v1/machines/{machine_id}/move',
    json={"position": target_position}
)

if move_response.json()['success']:
    print(f"Máquina {machine_id} movida a posición {target_position}")
else:
    print(f"Error: {move_response.json()['error']}")
```

### Ejemplo 3: Enviar comando personalizado

```python
import requests

# Enviar comando personalizado a máquina específica
machine_id = "machine_7"
command = 1  # Comando MUEVETE
argument = 5  # Posición 5

response = requests.post(
    f'http://192.168.1.10:5000/v1/machines/{machine_id}/command',
    json={
        "command": command,
        "argument": argument
    }
)

if response.json()['success']:
    result = response.json()['data']
    print(f"Comando exitoso. Nueva posición: {result['position']}")
else:
    print(f"Error: {response.json()['error']}")
```

## Migración desde Sistema Single-PLC

### Opción 1: Sin cambios (Compatibilidad)

Los sistemas existentes siguen funcionando sin modificaciones. La API usará la primera máquina disponible.

### Opción 2: Especificar máquina en el comando

```python
# Antes
requests.post('/v1/command', json={"command": 1, "argument": 3})

# Ahora (especificando máquina)
requests.post('/v1/command', json={
    "command": 1, 
    "argument": 3, 
    "machine_id": "machine_7"
})
```

### Opción 3: Usar nuevos endpoints específicos

```python
# Nuevo enfoque recomendado
requests.post('/v1/machines/machine_7/command', json={
    "command": 1, 
    "argument": 3
})
```

## Configuración de Red

Asegúrate de que:

1. Cada PLC tenga una IP única en la red
2. El puerto sea el mismo para todos (típicamente 3200)
3. La máquina donde corre la API pueda acceder a todas las IPs de los PLCs
4. Los WMS puedan acceder a la IP donde corre la API

## Monitoreo y Troubleshooting

### Logs Disponibles

1. **Logs de API**: `carousel_api.log` - Errores generales de la API
2. **Logs de Conexiones**: `client_connections.log` - Actividad de clientes WMS
3. **Logs de Operaciones**: `operations.log` - Operaciones específicas de PLC

### Verificar Conectividad

```bash
# Verificar que la API esté funcionando
curl http://localhost:5000/v1/health

# Verificar máquinas disponibles
curl http://localhost:5000/v1/machines

# Verificar estado de máquina específica
curl http://localhost:5000/v1/machines/machine_7/status
```

## Casos de Uso Típicos

### Caso 1: WMS con múltiples líneas de producción

```python
# El WMS puede controlar diferentes líneas independientemente
linea_a_machine = "machine_1"
linea_b_machine = "machine_3"
linea_c_machine = "machine_7"

# Mover producto en línea A
requests.post(f'/v1/machines/{linea_a_machine}/move', json={"position": 2})

# Simultáneamente, mover producto en línea C
requests.post(f'/v1/machines/{linea_c_machine}/move', json={"position": 5})
```

### Caso 2: Sistema de respaldo

```python
# Intentar con máquina principal, usar respaldo si falla
primary_machine = "machine_1"
backup_machine = "machine_2"

try:
    response = requests.post(f'/v1/machines/{primary_machine}/command', 
                           json={"command": 1, "argument": 3}, timeout=5)
    if not response.json()['success']:
        raise Exception("Primary machine failed")
except:
    print("Usando máquina de respaldo...")
    response = requests.post(f'/v1/machines/{backup_machine}/command', 
                           json={"command": 1, "argument": 3})
```
