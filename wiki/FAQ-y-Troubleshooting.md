# 🆘 FAQ y Troubleshooting

Preguntas frecuentes y soluciones a problemas comunes en carousel_api v2.6.0.

---

## ❓ Preguntas Frecuentes (FAQs)

### 1. ¿Qué hago si la API responde 'PLC ocupado por otro proceso'?

**Causa:** Otro proceso (GUI, app web, otro integrador) está usando el PLC.

**Solución:**

- Espera unos segundos y reintenta
- Evita enviar múltiples comandos simultáneos
- Implementa un sistema de colas en tu integración

```python
def retry_on_busy(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                time.sleep(2 ** attempt)  # Backoff exponencial
                continue
            raise
    raise Exception("PLC sigue ocupado después de reintentos")
```

### 2. ¿Por qué la posición del carrusel no se actualiza?

**Causa:** El PLC puede no estar enviando el dato correcto, o hay un problema de comunicación.

**Solución:**

- Verifica la conexión física y la configuración IP/puerto
- Consulta los logs de depuración para ver los bytes recibidos
- Si usas simulador, asegúrate de que esté activo
- Revisa el estado de conexión en `/v1/machines/{id}/status`

### 3. ¿Cómo simulo el PLC para pruebas?

**Solución:**

1. Edita `config_multi_plc.json`
2. Cambia `"simulator": true` para la máquina deseada
3. Reinicia la API

```json
{
  "plc_machines": [
    {
      "id": "test_machine",
      "name": "Máquina de Pruebas",
      "ip": "127.0.0.1",
      "port": 3200,
      "simulator": true,
      "description": "Máquina simulada para pruebas"
    }
  ]
}
```

### 4. ¿Cómo expongo la app web fuera de la red local?

**Solución:**

- Usa ngrok: `ngrok http 8181`
- Configura port forwarding en tu router
- Usa un proxy reverso como nginx
- Asegúrate de que la API también sea accesible

**Ejemplo con ngrok:**

```bash
# Instalar ngrok
npm install -g ngrok

# Exponer puerto 8181
ngrok http 8181

# Exponer API también
ngrok http 5000
```

### 5. ¿Qué hago si recibo error 500 o 409 en la API?

**Causa:** Puede ser un error interno, parámetros inválidos o lock ocupado.

**Solución:**

- Revisa los logs del backend para detalles
- Valida los parámetros enviados
- Espera y reintenta si es un error de lock
- Verifica que la máquina exista en la configuración

### 6. ¿Cómo ejecuto las pruebas de concurrencia y robustez?

**Solución:**

```bash
# Ejecutar tests unitarios
python -m pytest tests/

# Tests específicos
python -m pytest tests/test_api.py -v

# Tests con cobertura
python -m pytest --cov=. tests/
```

### 7. ¿Cómo integro un WMS externo?

**Solución:** Consulta la **[Guía de Integración WMS](Guía-de-Integración-WMS)** para ejemplos completos y recomendaciones.

### 8. ¿La aplicación web funciona en móviles?

**Sí**, la aplicación web v2.6.0 tiene diseño responsive y funciona en:

- Smartphones (iOS/Android)
- Tablets
- Navegadores de escritorio
- Dispositivos industriales con navegador

### 9. ¿Puedo controlar múltiples máquinas simultáneamente?

**Sí**, el sistema Multi-PLC permite:

- Control simultáneo de múltiples carruseles
- Monitoreo en tiempo real de todas las máquinas
- Configuración individual por máquina
- Balanceado de carga automático

### 10. ¿Cómo actualizo de Single-PLC a Multi-PLC?

**Pasos:**

1. Crea `config_multi_plc.json` con tu configuración actual
2. Actualiza tu código para usar endpoints `/v1/machines/`
3. Testa en modo simulador primero
4. Migra gradualmente tus integraciones

---

## 🐛 Problemas Comunes y Soluciones

### Conectividad y Red

| Problema | Síntomas | Solución |
|----------|----------|----------|
| **No conecta al PLC** | Error de conexión, timeout | Verifica IP, puerto, cableado de red |
| **API no responde** | 503, timeout | Verifica que el servicio esté ejecutándose |
| **CORS Error en navegador** | Blocked by CORS policy | Configura CORS en `api.py` o usa proxy |
| **WebSocket no conecta** | Connection failed | Verifica puerto 8765, firewall |

### Comandos y Estados

| Problema | Síntomas | Solución |
|----------|----------|----------|
| **Comando no ejecuta** | 200 OK pero sin movimiento | Verifica estado PLC, logs de depuración |
| **Estado no cambia** | Posición no actualiza | Revisa comunicación PLC, simulador |
| **Error 409 persistente** | PLC ocupado siempre | Reinicia API, verifica locks |
| **Alarma activa** | ALARMA: "Activa" | Revisa hardware, resetea PLC |

### Configuración

| Problema | Síntomas | Solución |
|----------|----------|----------|
| **Máquina no encontrada** | 404 Not Found | Verifica `config_multi_plc.json` |
| **Puerto ocupado** | Address already in use | Cambia puerto o mata proceso |
| **Permisos de archivo** | Permission denied | Ajusta permisos de archivos de config |
| **JSON inválido** | JSON decode error | Valida sintaxis de archivos de config |

---

## 🔧 Herramientas de Diagnóstico

### 1. Verificación de Conectividad

```bash
# Verificar API
curl -v http://localhost:5000/v1/status

# Verificar aplicación web
curl -v http://localhost:8181/

# Verificar WebSocket
wscat -c ws://localhost:8765
```

### 2. Logs de Depuración

```bash
# Ejecutar en modo debug
export APP_ENV=development
python main.py

# Ver logs en tiempo real
tail -f logs/carousel_api.log
```

### 3. Test de Carga

```python
import concurrent.futures
import requests
import time

def test_concurrent_requests():
    """Test de carga para la API"""
    def make_request():
        response = requests.get("http://localhost:5000/v1/machines")
        return response.status_code == 200
    
    # 10 requests concurrentes
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [future.result() for future in futures]
    
    success_rate = sum(results) / len(results) * 100
    print(f"Tasa de éxito: {success_rate}%")

test_concurrent_requests()
```

### 4. Monitor de Estado

```python
import time
import requests
from datetime import datetime

def monitor_machine_status(machine_id, interval=5):
    """Monitor continuo del estado de una máquina"""
    while True:
        try:
            response = requests.get(f"http://localhost:5000/v1/machines/{machine_id}/status")
            data = response.json()
            
            if data['success']:
                status = data['data']
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {machine_id}: Pos={status['position']}, "
                      f"Estado={status['status']['RUN']}, "
                      f"Conexión={status['connection_status']}")
            else:
                print(f"Error: {data['error']}")
                
        except Exception as e:
            print(f"Error de conexión: {e}")
        
        time.sleep(interval)

# Uso
monitor_machine_status("machine_1")
```

---

## ⚠️ Códigos de Error Comunes

### HTTP Status Codes

| Código | Significado | Acción Recomendada |
|--------|-------------|-------------------|
| **400** | Bad Request | Verificar parámetros JSON |
| **404** | Not Found | Verificar machine_id existe |
| **409** | Conflict | Esperar, PLC ocupado |
| **429** | Too Many Requests | Implementar throttling |
| **500** | Internal Server Error | Revisar logs del servidor |
| **503** | Service Unavailable | Verificar servicio activo |

### Error Codes Específicos

| Code | Descripción | Solución |
|------|-------------|----------|
| `MACHINE_NOT_FOUND` | ID de máquina inválido | Verificar configuración |
| `INVALID_POSITION` | Posición fuera de rango | Usar valores 1-255 |
| `PLC_BUSY` | PLC procesando comando | Esperar y reintentar |
| `CONNECTION_TIMEOUT` | Timeout con PLC | Verificar red y hardware |
| `INVALID_COMMAND` | Comando no válido | Usar command=1 para movimiento |

---

## 🔍 Debugging Avanzado

### 1. Captura de Tráfico de Red

```bash
# Capturar tráfico TCP al PLC
sudo tcpdump -i any -w plc_traffic.pcap port 3200

# Analizar con Wireshark
wireshark plc_traffic.pcap
```

### 2. Logs Detallados

```python
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Habilitar logs de requests
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)
```

### 3. Profiling de Rendimiento

```python
import cProfile
import pstats

def profile_api_call():
    """Profiling de llamadas a la API"""
    pr = cProfile.Profile()
    pr.enable()
    
    # Tu código aquí
    response = requests.get("http://localhost:5000/v1/machines")
    
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

profile_api_call()
```

---

## 📞 Obtener Ayuda

### 1. Información del Sistema

```bash
# Información de versión
python --version
pip list | grep -E "(flask|eventlet|customtkinter)"

# Estado del sistema
ps aux | grep python
netstat -tulpn | grep -E "(5000|8181|8765)"
```

### 2. Reportar Issues

Cuando reportes un problema, incluye:

- **Versión:** carousel_api v2.6.0
- **SO:** Windows/Linux/macOS + versión
- **Python:** Versión de Python
- **Error:** Mensaje de error completo
- **Logs:** Logs relevantes
- **Configuración:** `config_multi_plc.json` (sin IPs sensibles)
- **Pasos:** Pasos para reproducir el problema

### 3. Plantilla de Issue

```markdown
## Descripción del Problema
[Descripción clara del problema]

## Entorno
- **SO:** Windows 10 / Ubuntu 20.04 / macOS
- **Python:** 3.12.0
- **carousel_api:** v2.6.0

## Pasos para Reproducir
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

## Comportamiento Esperado
[Qué esperabas que pasara]

## Comportamiento Actual
[Qué está pasando realmente]

## Logs
```

[Logs relevantes aquí]

```

## Configuración
[Configuración relevante, sin datos sensibles]
```

---

## 🔗 Enlaces Relacionados

- **[API REST Reference](API-REST-Reference)** - Documentación completa de la API
- **[Guía de Integración WMS](Guía-de-Integración-WMS)** - Integración con sistemas WMS
- **[WebSocket API](WebSocket-API)** - Comunicación en tiempo real
- **[Logs y Debugging](Logs-y-Debugging)** - Guía avanzada de debugging
