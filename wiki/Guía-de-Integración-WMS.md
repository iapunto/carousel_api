# 🔗 Guía de Integración WMS

Esta guía facilita la integración de sistemas de gestión de almacenes (WMS) con el sistema de control de carruseles industriales Multi-PLC `carousel_api v2.6.0`.

---

## 🎯 Objetivo

Proporcionar APIs robustas, trazabilidad completa y operación segura para múltiples máquinas simultáneamente, facilitando la integración con sistemas WMS existentes.

---

## 🏗️ Arquitectura del Sistema

### Configuraciones Soportadas

1. **Single-PLC (Legacy)**: Una sola máquina controlada
2. **Multi-PLC (Recomendado)**: Múltiples máquinas controladas desde una sola API

### Puertos de Servicio

- **API Backend**: Puerto 5000 (configurable en `config_multi_plc.json`)
- **Aplicación Web**: Puerto 8181
- **WebSocket**: Puerto 8765 (comunicación en tiempo real)

---

## 🌐 Endpoints de la API

### 1. Endpoints Legacy (Single-PLC)

#### Consultar estado del carrusel

```http
GET /v1/status
```

**Respuesta:**

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

```http
POST /v1/command
Content-Type: application/json

{
  "command": 1,
  "argument": 15
}
```

### 2. Endpoints Multi-PLC (Recomendado)

#### Listar todas las máquinas

```http
GET /v1/machines
```

**Respuesta:**

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

```http
GET /v1/machines/{machine_id}/status
```

**Ejemplo**: `/v1/machines/plc_001/status`

**Respuesta:**

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

```http
POST /v1/machines/{machine_id}/command
Content-Type: application/json

{
  "command": 1,
  "argument": 25
}
```

**Respuesta:**

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

## 📊 Formatos de Datos

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

| Código | Descripción | Cuándo se produce |
|--------|-------------|-------------------|
| **200** | OK | Operación exitosa |
| **400** | Bad Request | Parámetros inválidos |
| **404** | Not Found | Máquina no encontrada |
| **409** | Conflict | PLC ocupado o en uso |
| **429** | Too Many Requests | Throttling activado |
| **500** | Internal Server Error | Error interno |
| **503** | Service Unavailable | Servicio no disponible |

---

## 🔌 Comunicación en Tiempo Real

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
            console.log(`Máquina ${machine_id}: Posición ${machine_data.position}`);
        }
    }
};
```

---

## 🐍 Patrones de Integración Python

### Clase de Integración WMS

```python
import requests
import json
import time
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CarouselWMSIntegration:
    """
    Clase para integración con sistemas WMS
    """
    
    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configurar reintentos automáticos
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_available_machines(self) -> List[Dict]:
        """
        Obtiene lista de máquinas disponibles
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/machines",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return data.get('data', [])
            else:
                raise Exception(f"Error en respuesta: {data.get('error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {e}")
    
    def get_machine_status(self, machine_id: str) -> Dict:
        """
        Obtiene estado de una máquina específica
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/machines/{machine_id}/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return data.get('data', {})
            else:
                raise Exception(f"Error en respuesta: {data.get('error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {e}")
    
    def move_to_position(self, machine_id: str, position: int) -> Dict:
        """
        Mueve el carrusel a una posición específica
        """
        if not 1 <= position <= 255:
            raise ValueError("La posición debe estar entre 1 y 255")
        
        try:
            payload = {
                "command": 1,
                "argument": position
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/machines/{machine_id}/command",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return data.get('data', {})
            else:
                raise Exception(f"Error en comando: {data.get('error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {e}")
    
    def wait_for_completion(self, machine_id: str, target_position: int, 
                          max_wait_time: int = 30) -> bool:
        """
        Espera hasta que el carrusel llegue a la posición objetivo
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status = self.get_machine_status(machine_id)
                current_position = status.get('position')
                machine_status = status.get('status', {})
                
                # Verificar si llegó a la posición y está detenido
                if (current_position == target_position and 
                    machine_status.get('RUN') == 'Detenido'):
                    return True
                
                # Verificar si hay alarma
                if machine_status.get('ALARMA') == 'Activa':
                    raise Exception("Alarma activa en la máquina")
                
                time.sleep(1)  # Esperar 1 segundo antes del siguiente check
                
            except Exception as e:
                print(f"Error verificando estado: {e}")
                time.sleep(1)
        
        return False
    
    def execute_movement_with_wait(self, machine_id: str, position: int) -> bool:
        """
        Ejecuta movimiento y espera a que se complete
        """
        try:
            # Enviar comando
            result = self.move_to_position(machine_id, position)
            print(f"Comando enviado: {result}")
            
            # Esperar completado
            success = self.wait_for_completion(machine_id, position)
            
            if success:
                print(f"Movimiento completado exitosamente a posición {position}")
                return True
            else:
                print(f"Timeout esperando movimiento a posición {position}")
                return False
                
        except Exception as e:
            print(f"Error en movimiento: {e}")
            return False

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar integración
    wms = CarouselWMSIntegration()
    
    try:
        # Obtener máquinas disponibles
        machines = wms.get_available_machines()
        print(f"Máquinas disponibles: {len(machines)}")
        
        if machines:
            machine_id = machines[0]['id']
            
            # Obtener estado actual
            status = wms.get_machine_status(machine_id)
            print(f"Estado actual: {status}")
            
            # Ejecutar movimiento
            success = wms.execute_movement_with_wait(machine_id, 10)
            print(f"Movimiento exitoso: {success}")
            
    except Exception as e:
        print(f"Error: {e}")
```

---

## 🔒 Configuración de Seguridad

### Variables de Entorno

```bash
# .env
CAROUSEL_API_URL=http://localhost:5000
CAROUSEL_API_TIMEOUT=10
CAROUSEL_API_RETRIES=3
CAROUSEL_LOG_LEVEL=INFO
```

### Configuración de Red

```python
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración desde variables de entorno
API_URL = os.getenv('CAROUSEL_API_URL', 'http://localhost:5000')
TIMEOUT = int(os.getenv('CAROUSEL_API_TIMEOUT', '10'))
RETRIES = int(os.getenv('CAROUSEL_API_RETRIES', '3'))

# Configurar sesión con reintentos
session = requests.Session()
retry_strategy = Retry(
    total=RETRIES,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

---

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Error 409 - PLC Ocupado

```python
def handle_busy_plc(func, *args, **kwargs):
    """Maneja PLC ocupado con reintentos"""
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                print(f"PLC ocupado, reintentando en {2**attempt} segundos...")
                time.sleep(2**attempt)
            else:
                raise
    raise Exception("PLC sigue ocupado después de 3 intentos")
```

#### 2. Timeout de Conexión

```python
def robust_request(url, **kwargs):
    """Request robusto con manejo de timeouts"""
    try:
        kwargs.setdefault('timeout', 10)
        response = requests.get(url, **kwargs)
        return response
    except requests.exceptions.Timeout:
        print("Timeout - verificar conectividad de red")
        raise
    except requests.exceptions.ConnectionError:
        print("Error de conexión - verificar que el servicio esté ejecutándose")
        raise
```

#### 3. Validación de Respuestas

```python
def validate_response(response):
    """Valida respuesta de la API"""
    try:
        data = response.json()
    except ValueError:
        raise Exception("Respuesta no es JSON válido")
    
    if not data.get('success'):
        error_msg = data.get('error', 'Error desconocido')
        error_code = data.get('code', 'UNKNOWN')
        raise Exception(f"Error API [{error_code}]: {error_msg}")
    
    return data.get('data')
```

---

## 📈 Monitoreo y Logs

### Logging Estructurado

```python
import logging
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('carousel_wms')

class CarouselLogger:
    @staticmethod
    def log_movement(machine_id: str, position: int, success: bool, duration: float):
        """Log estructurado para movimientos"""
        log_data = {
            "event": "movement",
            "machine_id": machine_id,
            "position": position,
            "success": success,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        if success:
            logger.info(f"Movimiento exitoso: {json.dumps(log_data)}")
        else:
            logger.error(f"Movimiento fallido: {json.dumps(log_data)}")
    
    @staticmethod
    def log_api_call(endpoint: str, method: str, status_code: int, duration: float):
        """Log para llamadas a la API"""
        log_data = {
            "event": "api_call",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"API Call: {json.dumps(log_data)}")
```

---

## 🔄 Migración desde Versiones Anteriores

### Desde Single-PLC a Multi-PLC

```python
class MigrationHelper:
    """Ayuda en la migración de Single-PLC a Multi-PLC"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def detect_api_version(self) -> str:
        """Detecta si la API es Single-PLC o Multi-PLC"""
        try:
            # Intentar endpoint Multi-PLC
            response = requests.get(f"{self.base_url}/v1/machines", timeout=5)
            if response.status_code == 200:
                return "multi-plc"
        except:
            pass
        
        try:
            # Intentar endpoint Single-PLC
            response = requests.get(f"{self.base_url}/v1/status", timeout=5)
            if response.status_code == 200:
                return "single-plc"
        except:
            pass
        
        raise Exception("No se pudo detectar la versión de la API")
    
    def get_status_unified(self, machine_id: str = None) -> Dict:
        """Obtiene estado de manera unificada"""
        api_version = self.detect_api_version()
        
        if api_version == "multi-plc":
            if not machine_id:
                raise ValueError("machine_id requerido para Multi-PLC")
            response = requests.get(f"{self.base_url}/v1/machines/{machine_id}/status")
        else:
            response = requests.get(f"{self.base_url}/v1/status")
        
        return response.json()
```

---

## 📋 Checklist de Integración

### Pre-implementación

- [ ] Verificar conectividad de red con el servidor carousel_api
- [ ] Confirmar puertos disponibles (5000, 8765, 8181)
- [ ] Revisar configuración de máquinas en `config_multi_plc.json`
- [ ] Establecer estrategia de manejo de errores
- [ ] Definir timeouts y reintentos apropiados

### Durante Implementación

- [ ] Implementar logging estructurado
- [ ] Configurar monitoreo de salud de la API
- [ ] Establecer validaciones de entrada
- [ ] Implementar manejo de estados de error
- [ ] Configurar alertas para fallos críticos

### Post-implementación

- [ ] Ejecutar pruebas de carga y estrés
- [ ] Verificar comportamiento durante desconexiones de red
- [ ] Documentar procedimientos de troubleshooting
- [ ] Establecer métricas de rendimiento
- [ ] Configurar respaldos de configuración

---

## 🔗 Enlaces Relacionados

- **[API REST Reference](API-REST-Reference)** - Documentación completa de endpoints
- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[Ejemplos de Código](Ejemplos-de-Código)** - Ejemplos adicionales
- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Solución de problemas comunes
