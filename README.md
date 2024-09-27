# CAROUSEL API

[![Build Status](https://travis-ci.org/tu_usuario/carousel_api.svg?branch=main)](https://travis-ci.org/tu_usuario/carousel_api)
[![Coverage Status](https://coveralls.io/repos/github/tu_usuario/carousel_api/badge.svg?branch=main)](https://coveralls.io/github/tu_usuario/carousel_api?branch=main)
[![PyPI version](https://badge.fury.io/py/carousel_api.svg)](https://badge.fury.io/py/carousel_api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

API de Python para el control de un carrusel vertical a través de una conexión de sockets TCP/IP.

## Descripción

Esta API permite enviar comandos a un PLC Delta AS Series para controlar el movimiento de un carrusel vertical de almacenamiento y recibir información sobre su estado y posición actual.

## Características

*   Comunicación con el PLC a través de sockets TCP/IP.
*   Envío y recepción de comandos y respuestas en formato de bytes.
*   Verificación del estado del PLC antes de enviar comandos de movimiento.
*   Interpretación de los estados del PLC en formato binario.
*   Lectura de la posición actual del carrusel.
*   Incluye un simulador del PLC para pruebas y desarrollo sin necesidad de hardware.

## Instalación

### Opción 1: Instalar desde PyPI

Puedes instalar esta API directamente desde PyPI utilizando `pip`:

```bash
pip install carousel_api
```

### Opción 2: Clonar desde Git

1.  Clona este repositorio:

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    ```

2.  Crea un entorno virtual:

    ```bash
    python -m venv venv
    ```

3.  Activa el entorno virtual:

    *   Windows: `venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

4.  Instala las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

## Configuración

*   Crea un archivo `.env` en la raíz del proyecto que utilizará la API con la siguiente información:

    ```bash
    PLC_IP=192.168.1.100  # Reemplaza con la IP real de tu PLC
    PLC_PORT=2000         # Reemplaza con el puerto real del PLC
    MODE=plc              # O 'simulator' para usar el simulador
    ```

## Uso

1.  **Importar la API en tu proyecto Python:**

    ```python
    from carousel_api.api import app

    # Configurar la aplicación Flask de la API con los valores del .env
    app.config['PLC_IP'] = os.getenv('PLC_IP')
    app.config['PLC_PORT'] = int(os.getenv('PLC_PORT'))
    app.config['MODE'] = os.getenv('MODE')
    ```

2.  **Ejecutar la API:**

    ```bash
    python wsgi.py  # O el comando que uses para ejecutar tu servidor WSGI (Waitress, etc.)
    ```

3.  **Enviar comandos al PLC:**

    *   Utiliza una biblioteca HTTP en tu lenguaje de programación preferido para enviar solicitudes POST al endpoint `/v1/command` con los siguientes datos en formato JSON:

        ```json
        {
            "command": <número_de_comando>,
            "argument": <argumento_opcional>
        }
        ```

    *   Consulta la documentación de la API para obtener detalles sobre los comandos disponibles y sus argumentos.

4.  **Obtener el estado del PLC:**

    *   Envía una solicitud GET al endpoint `/v1/status` para obtener el estado y la posición actual del PLC.

## Autoría

*   **Autor:** Industrias Pico S.A.S
*   **Desarrollo y administración:** IA Punto: Soluciones Integrales de Tecnología y Marketing
*   **Contacto:** desarrollo@iapunto.com

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.