# 🚀 Instalación y Configuración

Guía completa para instalar y configurar carousel_api v2.6.0 en diferentes entornos, desde desarrollo hasta producción.

---

## 📋 Requisitos del Sistema

### Requisitos Mínimos

- **Sistema Operativo:** Windows 10+, Linux, macOS
- **Python:** 3.12 o superior
- **RAM:** 2 GB mínimo, 4 GB recomendado
- **Disco:** 500 MB de espacio libre
- **Red:** Acceso a red local para comunicación con PLCs

### Requisitos de Software

- **Python 3.12+** con pip
- **Git** (para clonar el repositorio)
- **Editor de texto** (VS Code, Sublime Text, etc.)

### Dependencias del Sistema

#### Windows

```bash
# No se requieren dependencias adicionales
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip git
```

#### macOS

```bash
# Instalar Homebrew si no está instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python y Git
brew install python@3.12 git
```

---

## 📥 Instalación

### 1. Clonar el Repositorio

```bash
# Clonar desde GitHub
git clone https://github.com/iapunto/carousel_api.git
cd carousel_api
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Verificar Instalación

```bash
# Verificar versión de Python
python --version

# Verificar dependencias instaladas
pip list

# Ejecutar tests básicos
python -m pytest tests/ -v
```

---

## ⚙️ Configuración Inicial

### 1. Configuración Básica

```bash
# Copiar archivo de configuración de ejemplo
cp config_multi_plc.json.example config_multi_plc.json

# Editar configuración (usar tu editor preferido)
nano config_multi_plc.json
```

### 2. Configuración Mínima

Editar `config_multi_plc.json`:

```json
{
  "system": {
    "mode": "multi_plc",
    "version": "2.6.0",
    "debug": true
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

### 3. Validar Configuración

```bash
# Validar archivo JSON
python -m json.tool config_multi_plc.json

# Ejecutar validación del sistema
python main.py --validate-config
```

---

## 🏃‍♂️ Primera Ejecución

### 1. Modo Desarrollo

```bash
# Ejecutar con configuración de desarrollo
python main.py --debug

# O usar el archivo de configuración específico
python main.py --config config_multi_plc.json
```

### 2. Verificar Servicios

Una vez ejecutado, verificar que todos los servicios estén funcionando:

#### API REST

```bash
curl http://localhost:5000/v1/machines
```

#### WebSocket

```bash
# Usar el cliente de prueba incluido
python test_websocket_client.py
```

#### Aplicación Web

Abrir navegador en: <http://localhost:8181>

---

## 🏭 Configuración por Entorno

### Desarrollo

```json
{
  "system": {
    "mode": "multi_plc",
    "version": "2.6.0",
    "debug": true,
    "max_concurrent_operations": 5
  },
  "machines": {
    "dev_simulator": {
      "name": "Simulador Desarrollo",
      "ip": "127.0.0.1",
      "port": 3200,
      "type": "Simulator",
      "enabled": true
    }
  },
  "networking": {
    "api_host": "127.0.0.1",
    "api_port": 5000,
    "websocket_host": "127.0.0.1",
    "websocket_port": 8765,
    "web_host": "127.0.0.1",
    "web_port": 8181
  },
  "logging": {
    "level": "DEBUG",
    "file": "carousel_api_dev.log"
  }
}
```

### Testing

```json
{
  "system": {
    "mode": "multi_plc",
    "version": "2.6.0",
    "debug": false,
    "max_concurrent_operations": 10
  },
  "machines": {
    "test_machine_1": {
      "name": "Máquina Test 1",
      "ip": "192.168.1.100",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true
    },
    "test_simulator": {
      "name": "Simulador Test",
      "ip": "127.0.0.1",
      "port": 3201,
      "type": "Simulator",
      "enabled": true
    }
  },
  "networking": {
    "api_host": "0.0.0.0",
    "api_port": 5001,
    "websocket_host": "0.0.0.0",
    "websocket_port": 8766,
    "web_host": "0.0.0.0",
    "web_port": 8182
  },
  "logging": {
    "level": "INFO",
    "file": "carousel_api_test.log"
  }
}
```

### Producción

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
      "name": "Línea A - Principal",
      "ip": "192.168.100.10",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true,
      "connection_timeout": 10.0,
      "retry_attempts": 5
    },
    "line_a_backup": {
      "name": "Línea A - Respaldo",
      "ip": "192.168.100.11",
      "port": 3200,
      "type": "Real PLC",
      "enabled": true,
      "connection_timeout": 10.0,
      "retry_attempts": 5
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

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env`:

```bash
# Configuración de la aplicación
CAROUSEL_CONFIG_FILE=config_multi_plc.json
CAROUSEL_DEBUG=false
CAROUSEL_LOG_LEVEL=INFO

# Configuración de red
CAROUSEL_API_HOST=0.0.0.0
CAROUSEL_API_PORT=5000
CAROUSEL_WS_HOST=0.0.0.0
CAROUSEL_WS_PORT=8765
CAROUSEL_WEB_HOST=0.0.0.0
CAROUSEL_WEB_PORT=8181

# Configuración de base de datos (futuro)
DATABASE_URL=sqlite:///carousel_api.db

# Configuración de seguridad (futuro)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
```

### Configuración de Firewall

#### Windows

```cmd
# Permitir puertos de la aplicación
netsh advfirewall firewall add rule name="Carousel API" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="Carousel WebSocket" dir=in action=allow protocol=TCP localport=8765
netsh advfirewall firewall add rule name="Carousel Web" dir=in action=allow protocol=TCP localport=8181
```

#### Linux (UFW)

```bash
# Permitir puertos de la aplicación
sudo ufw allow 5000/tcp
sudo ufw allow 8765/tcp
sudo ufw allow 8181/tcp
```

### Configuración de Servicio (Linux)

Crear archivo `/etc/systemd/system/carousel-api.service`:

```ini
[Unit]
Description=Carousel API Service
After=network.target

[Service]
Type=simple
User=carousel
WorkingDirectory=/opt/carousel_api
Environment=PATH=/opt/carousel_api/venv/bin
ExecStart=/opt/carousel_api/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Habilitar servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable carousel-api
sudo systemctl start carousel-api
```

---

## 🧪 Testing de la Instalación

### 1. Tests Unitarios

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar tests específicos
python -m pytest tests/test_api.py -v

# Ejecutar con coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### 2. Tests de Integración

```bash
# Test de conectividad de PLCs
python -c "
from controllers.carousel_controller import CarouselController
controller = CarouselController()
controller.test_all_connections()
"

# Test de API
curl -X GET http://localhost:5000/v1/machines

# Test de WebSocket
python test_websocket_client.py
```

### 3. Tests de Carga

```bash
# Instalar herramientas de carga
pip install locust

# Ejecutar test de carga
locust -f tests/load_test.py --host=http://localhost:5000
```

---

## 🔍 Verificación Post-Instalación

### Checklist de Verificación

- [ ] ✅ Python 3.12+ instalado
- [ ] ✅ Dependencias instaladas sin errores
- [ ] ✅ Archivo de configuración creado y válido
- [ ] ✅ API REST responde en puerto 5000
- [ ] ✅ WebSocket funciona en puerto 8765
- [ ] ✅ Aplicación web accesible en puerto 8181
- [ ] ✅ Conexión a PLCs establecida
- [ ] ✅ Logs generándose correctamente
- [ ] ✅ Tests unitarios pasan
- [ ] ✅ GUI de escritorio se abre

### Comandos de Verificación

```bash
# Verificar servicios
netstat -an | grep :5000
netstat -an | grep :8765
netstat -an | grep :8181

# Verificar logs
tail -f carousel_api.log

# Verificar procesos
ps aux | grep python

# Verificar configuración
python -c "
import json
with open('config_multi_plc.json') as f:
    config = json.load(f)
    print('Configuración válida:', config['system']['version'])
"
```

---

## 🚨 Troubleshooting

### Problemas Comunes

#### Error: Puerto en uso

```
Error: [Errno 98] Address already in use
```

**Solución:**

```bash
# Encontrar proceso usando el puerto
netstat -tulpn | grep :5000
# Terminar proceso
kill -9 <PID>
```

#### Error: Módulo no encontrado

```
ModuleNotFoundError: No module named 'flask'
```

**Solución:**

```bash
# Verificar entorno virtual activado
which python
# Reinstalar dependencias
pip install -r requirements.txt
```

#### Error: Conexión a PLC

```
ConnectionError: Could not connect to PLC at 192.168.1.50:3200
```

**Solución:**

```bash
# Verificar conectividad
ping 192.168.1.50
telnet 192.168.1.50 3200
```

---

## 📚 Recursos Adicionales

### Documentación Relacionada

- **[Configuración Multi-PLC](Configuración-Multi-PLC)** - Configuración detallada
- **[API REST Reference](API-REST-Reference)** - Documentación de API
- **[FAQ y Troubleshooting](FAQ-y-Troubleshooting)** - Solución de problemas

### Scripts Útiles

```bash
# Script de instalación automática (Linux)
curl -sSL https://raw.githubusercontent.com/iapunto/carousel_api/main/scripts/install.sh | bash

# Script de actualización
./scripts/update.sh

# Script de backup
./scripts/backup.sh
```

---

## 📞 Soporte

Para problemas de instalación:

- 🐛 **Issues:** [GitHub Issues](https://github.com/iapunto/carousel_api/issues)
- 📧 **Email:** <soporte@iapunto.com>
- 📚 **Documentación:** [Wiki Principal](Home)
- 💬 **Chat:** [Discord Community](https://discord.gg/carousel-api)
