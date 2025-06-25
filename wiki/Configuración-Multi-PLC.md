# ⚙️ Configuración Multi-PLC

Esta página explica cómo configurar el sistema Multi-PLC de carousel_api v2.6.0 para gestionar múltiples máquinas carrusel desde una sola interfaz.

---

## 📋 Información General

El sistema Multi-PLC permite gestionar múltiples carruseles de forma centralizada, con soporte para:

- **PLCs Reales**: Conexión directa a hardware Delta AS Series
- **Simuladores**: Para desarrollo y pruebas
- **Modo Híbrido**: Combinación de PLCs reales y simulados

---

## 📁 Archivo de Configuración

### Ubicación

```
carousel_api/
├── config_multi_plc.json    # Configuración principal
└── config_backups/          # Respaldos automáticos
```

### Estructura Base

```json
{
  "system": {
    "mode": "multi_plc",
    "version": "2.6.0",
    "debug": false,
    "max_concurrent_operations": 5
  },
  "machines": {
    "machine_1": {
      "name": "Carrusel Principal - Línea A",
      "ip": "192.168.1.50",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true,
      "description": "Carrusel principal de la línea de producción A",
      "connection_timeout": 5.0,
      "retry_attempts": 3,
      "positions": 24
    },
    "machine_2": {
      "name": "Carrusel Secundario - Línea A", 
      "ip": "192.168.1.51",
      "port": 3200,
      "type": "Simulator",
      "enabled": true,
      "description": "Carrusel secundario de respaldo",
      "connection_timeout": 5.0,
      "retry_attempts": 3,
      "positions": 32
    }
  },
  "networking": {
    "api_host": "0.0.0.0",
    "api_port": 5000,
    "websocket_host": "0.0.0.0", 
    "websocket_port": 8765,
    "web_host": "0.0.0.0",
    "web_port": 8181
  },
  "logging": {
    "level": "INFO",
    "file": "carousel_api.log",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

---

## 🏭 Configuración de Máquinas

### Parámetros de Máquina

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `name` | string | ✅ | Nombre descriptivo de la máquina |
| `ip` | string | ✅ | Dirección IP del PLC |
| `port` | integer | ✅ | Puerto de comunicación (típicamente 3200) |
| `type` | string | ✅ | "Real PLC" o "Simulator" |
| `enabled` | boolean | ✅ | Si la máquina está habilitada |
| `description` | string | ❌ | Descripción adicional |
| `connection_timeout` | float | ❌ | Timeout de conexión en segundos (default: 5.0) |
| `retry_attempts` | integer | ❌ | Intentos de reconexión (default: 3) |
| `positions` | integer | ❌ | Número de posiciones del carrusel (default: 24) |

### Ejemplo: PLC Real

```json
{
  "machine_production": {
    "name": "Carrusel Producción - Zona 1",
    "ip": "192.168.100.10",
    "port": 3200,
    "type": "Real PLC",
    "enabled": true,
    "description": "Carrusel principal de la zona de producción",
    "connection_timeout": 10.0,
    "retry_attempts": 5,
    "positions": 48
  }
}
```

### Ejemplo: Simulador

```json
{
  "machine_test": {
    "name": "Carrusel Pruebas - Desarrollo",
    "ip": "127.0.0.1",
    "port": 3200,
    "type": "Simulator",
    "enabled": true,
    "description": "Simulador para desarrollo y testing",
    "connection_timeout": 2.0,
    "retry_attempts": 1,
    "positions": 24
  }
}
```

---

## 🌐 Configuración de Red

### Puertos del Sistema

| Servicio | Puerto Default | Configurable | Descripción |
|----------|----------------|--------------|-------------|
| API REST | 5000 | ✅ | Endpoints de la API |
| WebSocket | 8765 | ✅ | Comunicación en tiempo real |
| Web App | 8181 | ✅ | Interfaz web |

### Configuración de Red

```json
{
  "networking": {
    "api_host": "0.0.0.0",        // Acepta conexiones de cualquier IP
    "api_port": 5000,             // Puerto de la API REST
    "websocket_host": "0.0.0.0",  // Host del WebSocket
    "websocket_port": 8765,       // Puerto del WebSocket
    "web_host": "0.0.0.0",        // Host de la aplicación web
    "web_port": 8181,             // Puerto de la aplicación web
    "cors_enabled": true,         // Habilitar CORS
    "cors_origins": ["*"]         // Orígenes permitidos
  }
}
```

---

## 📊 Configuración de Logging

### Niveles de Log

- **DEBUG**: Información detallada de depuración
- **INFO**: Información general de operación
- **WARNING**: Advertencias que no detienen la operación
- **ERROR**: Errores que afectan la funcionalidad
- **CRITICAL**: Errores críticos que detienen el sistema

### Configuración de Logs

```json
{
  "logging": {
    "level": "INFO",
    "file": "carousel_api.log",
    "max_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "console_output": true
  }
}
```

---

## 🛠️ Configuración Avanzada

### Sistema de Respaldos

El sistema crea respaldos automáticos de la configuración:

```
config_backups/
├── config_multi_plc_backup_20250127_103045.json
├── config_multi_plc_backup_20250127_084521.json
└── config_multi_plc_backup_20250126_165432.json
```

### Configuración de Rendimiento

```json
{
  "system": {
    "max_concurrent_operations": 10,  // Operaciones simultáneas máximas
    "operation_timeout": 30.0,        // Timeout de operaciones en segundos
    "status_polling_interval": 1.0,   // Intervalo de polling en segundos
    "connection_pool_size": 20,       // Tamaño del pool de conexiones
    "enable_caching": true,           // Habilitar cache de estados
    "cache_ttl": 5.0                  // TTL del cache en segundos
  }
}
```

---

## 🚀 Guía de Setup

### 1. Configuración Inicial

```bash
# Copiar archivo de ejemplo
cp config_multi_plc.json.example config_multi_plc.json

# Editar configuración
nano config_multi_plc.json
```

### 2. Validar Configuración

```bash
# Ejecutar en modo de validación
python main.py --validate-config

# Ver configuración actual
python -c "
import json
with open('config_multi_plc.json') as f:
    config = json.load(f)
    print(json.dumps(config, indent=2))
"
```

### 3. Probar Conectividad

```bash
# Probar conexión a máquinas
python -c "
from controllers.carousel_controller import CarouselController
controller = CarouselController()
controller.test_all_connections()
"
```

---

## 🔧 Troubleshooting

### Problemas Comunes

#### Error de Conexión

```
ERROR - Could not connect to machine_1 at 192.168.1.50:3200
```

**Solución:**

1. Verificar IP y puerto en la configuración
2. Comprobar conectividad de red: `ping 192.168.1.50`
3. Verificar que el PLC esté encendido y accesible

#### Puerto en Uso

```
ERROR - Port 5000 already in use
```

**Solución:**

1. Cambiar el puerto en `networking.api_port`
2. O detener el proceso que usa el puerto: `netstat -ano | findstr :5000`

#### Configuración Inválida

```
ERROR - Invalid configuration format
```

**Solución:**

1. Validar JSON: `python -m json.tool config_multi_plc.json`
2. Revisar sintaxis y parámetros requeridos

---

## 📝 Ejemplos de Configuración

### Configuración Mínima

```json
{
  "system": {
    "mode": "multi_plc",
    "version": "2.6.0"
  },
  "machines": {
    "machine_1": {
      "name": "Carrusel Principal",
      "ip": "192.168.1.50",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true
    }
  }
}
```

### Configuración de Producción

```json
{
  "system": {
    "mode": "multi_plc",
    "version": "2.6.0",
    "debug": false,
    "max_concurrent_operations": 20
  },
  "machines": {
    "line_a_primary": {
      "name": "Línea A - Carrusel Principal",
      "ip": "192.168.100.10",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true,
      "description": "Carrusel principal línea A",
      "connection_timeout": 10.0,
      "retry_attempts": 5,
      "positions": 48
    },
    "line_a_secondary": {
      "name": "Línea A - Carrusel Respaldo",
      "ip": "192.168.100.11", 
      "port": 3200,
      "type": "Real PLC",
      "enabled": true,
      "description": "Carrusel respaldo línea A",
      "connection_timeout": 10.0,
      "retry_attempts": 5,
      "positions": 48
    },
    "line_b_primary": {
      "name": "Línea B - Carrusel Principal",
      "ip": "192.168.100.20",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true,
      "description": "Carrusel principal línea B",
      "connection_timeout": 10.0,
      "retry_attempts": 5,
      "positions": 32
    }
  },
  "networking": {
    "api_host": "0.0.0.0",
    "api_port": 5000,
    "websocket_host": "0.0.0.0",
    "websocket_port": 8765,
    "web_host": "0.0.0.0",
    "web_port": 8181
  },
  "logging": {
    "level": "INFO",
    "file": "carousel_api.log",
    "max_size_mb": 50,
    "backup_count": 10
  }
}
```

---

## 🔗 Enlaces Relacionados

- **[Arquitectura del Sistema](Arquitectura-del-Sistema)** - Diseño general del sistema
- **[Instalación y Configuración](Instalación-y-Configuración)** - Guía de instalación
- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Solución de problemas comunes
- **[API REST Reference](API-REST-Reference)** - Documentación de endpoints

---

## 📞 Soporte

Para problemas de configuración específicos:

- 🐛 **Issues:** [GitHub Issues](https://github.com/iapunto/carousel_api/issues)
- 📧 **Email:** <soporte@iapunto.com>
- 📚 **Documentación:** [Wiki Principal](Home)
