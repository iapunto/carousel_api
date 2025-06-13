# carousel_api

API y sistema de control para carrusel vertical industrial (PLC Delta AS Series)

---

## Descripción general

Este proyecto proporciona una API REST y una interfaz gráfica para controlar un sistema de almacenamiento automatizado tipo carrusel, integrando hardware industrial (PLC Delta AS Series) o un simulador para pruebas y desarrollo.

- **API REST**: Permite consultar el estado y enviar comandos al carrusel.
- **Simulador**: Emula el comportamiento del PLC para desarrollo sin hardware.
- **Interfaz gráfica**: Permite operación manual y monitoreo.

## Arquitectura

- `api.py`: API Flask con endpoints REST.
- `models/plc.py`: Comunicación con PLC real (TCP/IP).
- `models/plc_simulator.py`: Simulador de PLC.
- `controllers/carousel_controller.py`: Lógica de alto nivel y validaciones.
- `commons/utils.py`: Utilidades para interpretación de estados.
- `main.py`: Lanzador de la aplicación (API + GUI).

## Cambios recientes importantes

- La GUI ahora utiliza `python-socketio` como cliente para conectarse al backend Flask-SocketIO, reemplazando `websocket-client`.
- Esto asegura compatibilidad total y comunicación en tiempo real eficiente entre la interfaz y el backend, permitiendo actualizaciones instantáneas del estado del PLC sin polling agresivo.

## Dependencias principales

- flask-socketio
- python-socketio[client]
- eventlet

## Instalación y configuración

1. **Clonar el repositorio**

```bash
git clone <url-del-repo>
cd carousel_api
```

2. **Crear y activar entorno virtual**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar parámetros**

Editar `config.json`:

```json
{
  "ip": "192.168.1.100",
  "port": 3200,
  "simulator_enabled": false,
  "api_port": 5000
}
```

- `simulator_enabled: true` activa el modo simulador.
- `api_port`: Puerto donde se expone la API.

## Ejecución y comunicación en tiempo real

El backend expone eventos en tiempo real mediante Socket.IO. La GUI se conecta usando `python-socketio` y recibe eventos `plc_status` cada vez que hay un cambio de estado relevante en el PLC o simulador. Esto permite una experiencia similar a un chat, con actualizaciones instantáneas y eficiente uso de recursos.

```bash
python main.py
```

Esto inicia la API y la interfaz gráfica.

## Uso de la API

### Consultar estado

**GET** `/v1/status`

- **Respuesta exitosa:**

```json
{
  "status_code": 3,
  "position": 5
}
```

- **Error:**

```json
{
  "error": "No se pudo conectar al PLC"
}
```

### Enviar comando

**POST** `/v1/command`

- **Payload:**

```json
{
  "command": 1,
  "argument": 3
}
```

- **Respuesta exitosa:**

```json
{
  "status": {
    "READY": "El equipo está listo para operar",
    "RUN": "El equipo está detenido",
    ...
  },
  "position": 3,
  "raw_status": 3
}
```

- **Error:**

```json
{
  "error": "Comando fuera de rango (0-255)"
}
```

## Pruebas automatizadas

```bash
python -m unittest discover -s tests
```

## Modos de operación

- **PLC real:** `simulator_enabled: false` en `config.json`.
- **Simulador:** `simulator_enabled: true` (requiere contraseña en GUI: `DESARROLLO123`).

## Seguridad y buenas prácticas

- No exponer la API a redes públicas sin protección.
- Revisar y ajustar CORS según el entorno.
- No almacenar credenciales sensibles en archivos de texto plano.
- Validar siempre los datos de entrada.

## Créditos

- Industrias Pico S.A.S
- IA Punto: Soluciones Tecnológicas y Marketing

---

Para dudas o soporte, contactar a los responsables del proyecto.
