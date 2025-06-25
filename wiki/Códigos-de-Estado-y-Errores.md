# 🚨 Códigos de Estado y Errores

Referencia completa de códigos de estado HTTP, códigos de error específicos del sistema carousel_api v2.6.0 y guía de interpretación para diagnóstico y troubleshooting.

---

## 📋 Códigos de Estado HTTP

### Respuestas Exitosas (2xx)

| Código | Descripción | Uso en carousel_api |
|--------|-------------|---------------------|
| **200** | OK | Operación exitosa, datos devueltos |
| **201** | Created | Recurso creado exitosamente |
| **202** | Accepted | Comando aceptado, procesándose |
| **204** | No Content | Operación exitosa sin datos de respuesta |

#### Ejemplo 200 OK

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
    "position": 15,
    "timestamp": "2025-01-27T10:30:45.123Z"
  },
  "error": null,
  "code": null
}
```

### Errores del Cliente (4xx)

| Código | Descripción | Causa Común | Solución |
|--------|-------------|-------------|----------|
| **400** | Bad Request | JSON malformado, parámetros inválidos | Verificar formato de datos |
| **404** | Not Found | Máquina no existe, endpoint inválido | Verificar ID de máquina |
| **409** | Conflict | PLC ocupado, operación en progreso | Esperar o cancelar operación |
| **422** | Unprocessable Entity | Datos válidos pero lógicamente incorrectos | Revisar lógica de negocio |
| **429** | Too Many Requests | Rate limiting activado | Reducir frecuencia de requests |

#### Ejemplo 400 Bad Request

```json
{
  "success": false,
  "data": null,
  "error": "Invalid JSON format in request body",
  "code": "INVALID_JSON"
}
```

#### Ejemplo 404 Not Found

```json
{
  "success": false,
  "data": null,
  "error": "Machine 'invalid_machine' not found",
  "code": "MACHINE_NOT_FOUND"
}
```

#### Ejemplo 409 Conflict

```json
{
  "success": false,
  "data": null,
  "error": "Machine 'machine_1' is currently busy processing another command",
  "code": "MACHINE_BUSY"
}
```

### Errores del Servidor (5xx)

| Código | Descripción | Causa Común | Acción Recomendada |
|--------|-------------|-------------|-------------------|
| **500** | Internal Server Error | Error interno del sistema | Revisar logs, contactar soporte |
| **503** | Service Unavailable | PLC desconectado, servicio no disponible | Verificar conectividad |
| **504** | Gateway Timeout | Timeout de comunicación con PLC | Verificar red y PLC |

#### Ejemplo 500 Internal Server Error

```json
{
  "success": false,
  "data": null,
  "error": "Unexpected error occurred while processing request",
  "code": "INTERNAL_ERROR"
}
```

#### Ejemplo 503 Service Unavailable

```json
{
  "success": false,
  "data": null,
  "error": "PLC connection unavailable for machine 'machine_1'",
  "code": "PLC_UNAVAILABLE"
}
```

---

## 🔧 Códigos de Error del Sistema

### Errores de Conexión (CON_xxx)

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| `CON_001` | Connection timeout | PLC no responde | Verificar IP, puerto, estado del PLC |
| `CON_002` | Connection refused | Puerto cerrado o PLC apagado | Verificar PLC encendido y puerto |
| `CON_003` | Network unreachable | Problema de red | Verificar conectividad de red |
| `CON_004` | Invalid IP address | IP malformada en configuración | Corregir IP en config |
| `CON_005` | Port out of range | Puerto inválido | Usar puerto válido (1-65535) |

### Errores de Comando (CMD_xxx)

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| `CMD_001` | Invalid command type | Comando no reconocido | Usar comandos válidos (1=move) |
| `CMD_002` | Invalid position | Posición fuera de rango | Usar posición válida (1-255) |
| `CMD_003` | Command timeout | PLC no responde a comando | Verificar estado del PLC |
| `CMD_004` | Command execution failed | Error en ejecución | Revisar logs del PLC |
| `CMD_005` | Machine busy | Máquina procesando otro comando | Esperar o usar queue |

### Errores de Configuración (CFG_xxx)

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| `CFG_001` | Invalid configuration file | JSON malformado | Validar sintaxis JSON |
| `CFG_002` | Missing required field | Campo obligatorio ausente | Agregar campo requerido |
| `CFG_003` | Invalid machine type | Tipo de máquina inválido | Usar "Real PLC" o "Simulator" |
| `CFG_004` | Duplicate machine ID | ID de máquina duplicado | Usar IDs únicos |
| `CFG_005` | Configuration not found | Archivo de config no existe | Crear archivo de configuración |

### Errores de Estado (STA_xxx)

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| `STA_001` | Invalid status format | Respuesta de PLC malformada | Verificar comunicación PLC |
| `STA_002` | Status read timeout | Timeout leyendo estado | Verificar conectividad |
| `STA_003` | Status unavailable | Estado no disponible | Verificar PLC operativo |
| `STA_004` | Status parsing error | Error interpretando estado | Revisar protocolo PLC |

### Errores de Sistema (SYS_xxx)

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| `SYS_001` | Memory allocation error | Memoria insuficiente | Liberar memoria, reiniciar |
| `SYS_002` | File system error | Error acceso a archivos | Verificar permisos |
| `SYS_003` | Database error | Error en base de datos | Verificar integridad DB |
| `SYS_004` | Service startup failed | Error iniciando servicio | Revisar logs de inicio |
| `SYS_005` | Resource exhaustion | Recursos agotados | Liberar recursos |

---

## 🏭 Estados del PLC

### Estados Principales

| Estado | Bit | Descripción | Valor Típico |
|--------|-----|-------------|--------------|
| **READY** | 0-1 | Carrusel listo para operar | "OK" / "Error" |
| **RUN** | 2-3 | Estado de movimiento | "Detenido" / "En movimiento" |
| **MODO_OPERACION** | 4-5 | Modo de operación | "Local" / "Remoto" |
| **ALARMA** | 6-7 | Estado de alarma | "Activada" / "Desactivada" |

### Interpretación de Estados

#### READY

- **"OK"**: Carrusel operativo, sin errores
- **"Error"**: Problema detectado, revisar alarmas

#### RUN

- **"Detenido"**: Carrusel parado, listo para comandos
- **"En movimiento"**: Ejecutando movimiento, no enviar comandos

#### MODO_OPERACION

- **"Local"**: Control desde panel local del PLC
- **"Remoto"**: Control remoto habilitado (API)

#### ALARMA

- **"Desactivada"**: Funcionamiento normal
- **"Activada"**: Alarma activa, revisar causa

### Estado Raw (Binario)

El estado raw es un valor entero que representa todos los bits:

```python
# Ejemplo de interpretación
raw_status = 218  # 11011010 en binario

# Extraer bits individuales
ready = (raw_status >> 0) & 0x03      # Bits 0-1
run = (raw_status >> 2) & 0x03        # Bits 2-3  
mode = (raw_status >> 4) & 0x03       # Bits 4-5
alarm = (raw_status >> 6) & 0x03      # Bits 6-7
```

---

## 📊 Códigos de WebSocket

### Códigos de Cierre WebSocket

| Código | Descripción | Causa |
|--------|-------------|-------|
| **1000** | Normal closure | Cierre normal de conexión |
| **1001** | Going away | Servidor cerrándose |
| **1002** | Protocol error | Error de protocolo WebSocket |
| **1003** | Unsupported data | Tipo de datos no soportado |
| **1006** | Abnormal closure | Cierre anormal (red) |
| **1011** | Internal error | Error interno del servidor |

### Mensajes de Error WebSocket

```json
{
  "type": "error",
  "error": {
    "code": "WS_001",
    "message": "Invalid message format",
    "timestamp": "2025-01-27T10:30:45.123Z"
  }
}
```

#### Códigos de Error WebSocket

| Código | Descripción | Solución |
|--------|-------------|----------|
| `WS_001` | Invalid message format | Verificar formato JSON |
| `WS_002` | Unknown message type | Usar tipos válidos |
| `WS_003` | Authentication required | Autenticarse primero |
| `WS_004` | Rate limit exceeded | Reducir frecuencia |
| `WS_005` | Subscription failed | Verificar tipo de suscripción |

---

## 🔍 Guía de Diagnóstico

### Flujo de Diagnóstico por Código HTTP

#### Para Error 400 (Bad Request)

1. Verificar formato JSON del request
2. Validar tipos de datos de parámetros
3. Comprobar campos requeridos
4. Revisar rangos de valores

#### Para Error 404 (Not Found)

1. Verificar ID de máquina en configuración
2. Comprobar endpoint URL
3. Validar que la máquina esté habilitada

#### Para Error 409 (Conflict)

1. Verificar si máquina está ocupada
2. Esperar finalización de operación actual
3. Implementar queue de comandos si necesario

#### Para Error 503 (Service Unavailable)

1. Verificar conectividad de red al PLC
2. Comprobar estado del PLC (encendido/apagado)
3. Validar configuración IP/puerto
4. Revisar logs de conexión

### Herramientas de Diagnóstico

#### Verificar Estado de Máquina

```bash
curl -X GET http://localhost:5000/v1/machines/machine_1/status
```

#### Test de Conectividad

```bash
# Ping al PLC
ping 192.168.1.50

# Test de puerto
telnet 192.168.1.50 3200
```

#### Revisar Logs

```bash
# Logs en tiempo real
tail -f carousel_api.log

# Buscar errores específicos
grep "ERROR" carousel_api.log | tail -20
```

---

## 📈 Monitoreo y Alertas

### Métricas Importantes

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Errores 5xx | > 5% | Investigar problemas de sistema |
| Timeouts | > 10% | Verificar red y PLCs |
| Errores 409 | > 20% | Optimizar concurrencia |
| Latencia API | > 2s | Revisar rendimiento |

### Configuración de Alertas

```python
# Ejemplo de configuración de alertas
ALERT_THRESHOLDS = {
    "error_rate_5xx": 0.05,      # 5%
    "timeout_rate": 0.10,        # 10%
    "conflict_rate": 0.20,       # 20%
    "avg_latency_ms": 2000       # 2 segundos
}
```

---

## 🛠️ Troubleshooting por Código

### Script de Diagnóstico Automático

```python
#!/usr/bin/env python3
"""
Script de diagnóstico automático para carousel_api
"""

import requests
import json
import sys

def diagnose_api():
    """Ejecutar diagnóstico completo de la API"""
    
    base_url = "http://localhost:5000"
    
    # Test 1: Verificar conectividad
    try:
        response = requests.get(f"{base_url}/v1/machines", timeout=5)
        print(f"✅ API accesible: {response.status_code}")
    except Exception as e:
        print(f"❌ API no accesible: {e}")
        return False
    
    # Test 2: Verificar máquinas
    if response.status_code == 200:
        machines = response.json().get('data', [])
        print(f"✅ Máquinas configuradas: {len(machines)}")
        
        for machine in machines:
            machine_id = machine['id']
            # Test estado de cada máquina
            try:
                status_response = requests.get(
                    f"{base_url}/v1/machines/{machine_id}/status",
                    timeout=5
                )
                if status_response.status_code == 200:
                    print(f"✅ {machine_id}: Conectado")
                else:
                    print(f"❌ {machine_id}: Error {status_response.status_code}")
            except Exception as e:
                print(f"❌ {machine_id}: {e}")
    
    return True

if __name__ == "__main__":
    diagnose_api()
```

---

## 🔗 Enlaces Relacionados

- **[API REST Reference](API-REST-Reference)** - Documentación completa de endpoints
- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Solución de problemas comunes
- **[Logs y Debugging](Logs-y-Debugging)** - Guía de logs y depuración

---

## 📞 Soporte

Para problemas específicos con códigos de error:

- 🐛 **Issues:** [GitHub Issues](https://github.com/iapunto/carousel_api/issues)
- 📧 **Email:** <soporte@iapunto.com>
- 📚 **Documentación:** [Wiki Principal](Home)
- 📋 **Plantilla de Reporte:** Incluir código de error, logs relevantes y pasos para reproducir
