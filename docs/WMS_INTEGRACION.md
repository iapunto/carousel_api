# Guía de Integración WMS — carousel_api v2.6.0

## Objetivo

Facilitar la integración de sistemas de gestión de almacenes (WMS) con el sistema de control de carruseles industriales Multi-PLC `carousel_api v2.6.0`, proporcionando APIs robustas, trazabilidad completa y operación segura para múltiples máquinas simultáneamente.

---

## Arquitectura del Sistema

### Configuraciones Soportadas

1. **Single-PLC (Legacy)**: Una sola máquina controlada
2. **Multi-PLC**: Múltiples máquinas controladas desde una sola API

### Puertos de Servicio

- **API Backend**: Puerto 5000 (configurable en `config_multi_plc.json`)
- **Aplicación Web**: Puerto 8181
- **WebSocket**: Puerto 8765 (comunicación en tiempo real)

---

## Endpoints de la API

### 1. Endpoints Legacy (Single-PLC)

#### Consultar estado del carrusel

- **GET** `/v1/status`
- **Respuesta:**

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
    "raw_status": 218
  },
  "error": null,
  "code": null
}
```

#### Enviar comando de movimiento

- **POST** `/v1/command`
- **Body:**

```json
{
  "command": 1,
  "argument": 15
}
```

### 2. Endpoints Multi-PLC (Recomendado)

#### Listar todas las máquinas

- **GET** `/v1/machines`
- **Respuesta:**

```json
{
  "success": true,
  "machines": [
    {
      "id": "plc_001",
      "name": "Carrusel Almacén A",
      "ip": "192.168.1.50",
      "port": 3200,
      "simulator": false,
      "status": "connected"
    },
    {
      "id": "plc_002", 
      "name": "Carrusel Almacén B",
      "ip": "192.168.1.51",
      "port": 3200,
      "simulator": true,
      "status": "connected"
    }
  ]
}
```

#### Consultar estado de máquina específica

- **GET** `/v1/machines/{machine_id}/status`
- **Ejemplo**: `/v1/machines/plc_001/status`
- **Respuesta:**

```json
{
  "success": true,
  "machine_id": "plc_001",
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
    "last_update": "2025-06-24T10:30:45.123Z"
  }
}
```

#### Enviar comando a máquina específica

- **POST** `/v1/machines/{machine_id}/command`
- **Ejemplo**: `/v1/machines/plc_001/command`
- **Body:**

```json
{
  "command": 1,
  "argument": 25
}
```

- **Respuesta:**

```json
{
  "success": true,
  "machine_id": "plc_001",
  "data": {
    "command_sent": 1,
    "argument": 25,
    "timestamp": "2025-06-24T10:30:45.123Z"
  },
  "message": "Comando enviado exitosamente"
}
```

---

## Formatos de Datos

### Comandos

- **`command`**: entero
  - `1` = mover a posición
  - Otros comandos reservados para futuras implementaciones
- **`argument`**: entero (1-255, posición del cangilón)

### Estados Interpretados

- **`READY`**: "OK" | "Fallo"
- **`RUN`**: "Detenido" | "En movimiento"
- **`MODO_OPERACION`**: "Remoto" | "Manual"
- **`ALARMA`**: "Desactivada" | "Activa"

### Códigos de Respuesta HTTP

- **200**: Operación exitosa
- **400**: Parámetros inválidos
- **404**: Máquina no encontrada
- **409**: PLC ocupado o en uso
- **429**: Demasiadas solicitudes (throttling)
- **500**: Error interno del servidor
- **503**: Servicio no disponible

---

## Comunicación en Tiempo Real

### WebSocket (Puerto 8765)

Para recibir actualizaciones de estado en tiempo real:

```javascript
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = function() {
    // Suscribirse a actualizaciones
    ws.send(JSON.stringify({
        "type": "subscribe",
        "subscription_type": "status_updates"
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'status_broadcast') {
        // Datos multi-PLC
        const machines_status = data.status;
        for (const [machine_id, machine_data] of Object.entries(machines_status)) {
            console.log(`Máquina ${machine_id}:`, machine_data);
        }
    }
};
```

---

## Patrones de Integración Recomendados

### 1. Integración Single-PLC (Legacy)

```python
import requests

BASE_URL = "http://localhost:5000"

def get_carousel_status():
    response = requests.get(f"{BASE_URL}/v1/status")
    return response.json()

def move_carousel(position):
    payload = {"command": 1, "argument": position}
    response = requests.post(f"{BASE_URL}/v1/command", json=payload)
    return response.json()

# Uso
status = get_carousel_status()
if status["success"]:
    current_position = status["data"]["position"]
    print(f"Posición actual: {current_position}")
    
    # Mover a posición 10
    result = move_carousel(10)
    if result["success"]:
        print("Comando enviado exitosamente")
```

### 2. Integración Multi-PLC (Recomendado)

```python
import requests
import time

BASE_URL = "http://localhost:5000"

class CarouselWMSIntegration:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        
    def get_machines(self):
        """Obtener lista de máquinas disponibles"""
        response = requests.get(f"{self.base_url}/v1/machines")
        return response.json()
    
    def get_machine_status(self, machine_id):
        """Obtener estado de máquina específica"""
        response = requests.get(f"{self.base_url}/v1/machines/{machine_id}/status")
        return response.json()
    
    def move_machine(self, machine_id, position):
        """Mover máquina a posición específica"""
        payload = {"command": 1, "argument": position}
        response = requests.post(
            f"{self.base_url}/v1/machines/{machine_id}/command", 
            json=payload
        )
        return response.json()
    
    def wait_for_position(self, machine_id, target_position, timeout=60):
        """Esperar hasta que la máquina alcance la posición objetivo"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_machine_status(machine_id)
            if status["success"]:
                current_position = status["data"]["position"]
                if current_position == target_position:
                    return True
            time.sleep(1)
        
        return False

# Uso
wms = CarouselWMSIntegration()

# Listar máquinas disponibles
machines = wms.get_machines()
for machine in machines["machines"]:
    print(f"Máquina: {machine['name']} ({machine['id']})")
    
    # Obtener estado actual
    status = wms.get_machine_status(machine['id'])
    if status["success"]:
        position = status["data"]["position"]
        print(f"  Posición actual: {position}")
        
        # Mover a posición 20
        result = wms.move_machine(machine['id'], 20)
        if result["success"]:
            print(f"  Comando enviado, esperando movimiento...")
            if wms.wait_for_position(machine['id'], 20):
                print(f"  ✅ Máquina en posición 20")
            else:
                print(f"  ⚠️ Timeout esperando movimiento")
```

---

## Manejo de Errores y Reintentos

### Estrategia de Reintentos

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=1
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Uso con manejo de errores
session = create_session_with_retries()

try:
    response = session.post(
        f"{BASE_URL}/v1/machines/plc_001/command",
        json={"command": 1, "argument": 15},
        timeout=10
    )
    response.raise_for_status()
    result = response.json()
    
    if not result.get("success"):
        print(f"Error en comando: {result.get('error')}")
        
except requests.exceptions.Timeout:
    print("Timeout en la solicitud")
except requests.exceptions.ConnectionError:
    print("Error de conexión")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 409:
        print("PLC ocupado, reintentando en 5 segundos...")
        time.sleep(5)
    elif e.response.status_code == 429:
        print("Demasiadas solicitudes, esperando...")
        time.sleep(3)
```

---

## Configuración y Seguridad

### Variables de Entorno Recomendadas

```bash
# Configuración de producción
APP_ENV=production
CAROUSEL_API_URL=http://localhost:5000
CAROUSEL_WS_URL=ws://localhost:8765
API_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=2
```

### Consideraciones de Seguridad

1. **Autenticación**: Implemente autenticación si expone la API externamente
2. **Rate Limiting**: Respete los límites de throttling (3 segundos entre comandos)
3. **Validación**: Siempre valide las respuestas antes de procesar
4. **Logs**: Mantenga logs detallados para auditoría y debugging
5. **Red**: Use HTTPS en producción y restrinja acceso por IP si es posible

### Configuración Multi-PLC

Ejemplo de `config_multi_plc.json`:

```json
{
  "api_config": {
    "port": 5000,
    "host": "0.0.0.0"
  },
  "plc_machines": [
    {
      "id": "plc_almacen_a",
      "name": "Carrusel Almacén A",
      "ip": "192.168.1.50",
      "port": 3200,
      "simulator": false
    },
    {
      "id": "plc_almacen_b", 
      "name": "Carrusel Almacén B",
      "ip": "192.168.1.51",
      "port": 3200,
      "simulator": false
    }
  ]
}
```

---

## Troubleshooting para Integradores

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| **409 PLC ocupado** | Otro proceso está usando el PLC | Espere y reintente después de 3-5 segundos |
| **404 Máquina no encontrada** | ID de máquina inválido | Verifique la lista de máquinas con `/v1/machines` |
| **429 Too Many Requests** | Demasiadas solicitudes muy rápido | Implemente throttling de 3 segundos entre comandos |
| **500 Error interno** | Error en el servidor o PLC | Revise logs del servidor y estado del PLC |
| **503 Servicio no disponible** | API o PLC desconectado | Verifique conectividad y estado de servicios |

### Debugging

```python
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('carousel_wms')

def debug_api_call(method, url, payload=None):
    logger.debug(f"API Call: {method} {url}")
    if payload:
        logger.debug(f"Payload: {payload}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=payload, timeout=10)
            
        logger.debug(f"Response Status: {response.status_code}")
        logger.debug(f"Response Body: {response.text}")
        
        return response.json()
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        raise
```

---

## Migración desde Versiones Anteriores

### Cambios en v2.6.0

1. **Nuevos endpoints Multi-PLC**: Use `/v1/machines/` para nuevas integraciones
2. **Rango de posiciones ampliado**: Ahora soporta 1-255 (antes 1-6)
3. **WebSocket en puerto 8765**: Reemplace Socket.IO por WebSocket nativo
4. **Configuración centralizada**: Use `config_multi_plc.json`

### Compatibilidad hacia atrás

Los endpoints legacy (`/v1/status`, `/v1/command`) siguen funcionando para configuraciones single-PLC.

---

## Contacto y Soporte

- **Soporte técnico**: [soporte@iapunto.com](mailto:soporte@iapunto.com)
- **Documentación adicional**: Consulte `README.md`, `CHANGELOG.md` y `docs/ROADMAP_v2.7.md`
- **Repositorio**: [GitHub - carousel_api](https://github.com/iapunto/carousel_api)
- **Versión actual**: v2.6.0 (2025-06-24)

---

## Apéndices

### A. Códigos de Estado del PLC

```python
# Interpretación de status_code (byte)
STATUS_MAPPINGS = {
    "READY": {0: "Fallo", 1: "OK"},
    "RUN": {0: "Detenido", 1: "En movimiento"}, 
    "MODO_OPERACION": {0: "Manual", 1: "Remoto"},
    "ALARMA": {0: "Desactivada", 1: "Activa"}
}
```

### B. Ejemplos de Respuestas de Error

```json
{
  "success": false,
  "error": "Máquina 'plc_invalid' no encontrada",
  "code": "MACHINE_NOT_FOUND",
  "available_machines": ["plc_001", "plc_002"]
}
```

```json
{
  "success": false, 
  "error": "Posición debe estar entre 1 y 255",
  "code": "INVALID_POSITION",
  "received_value": 300
}
```
