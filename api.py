"""
API para el control de un carrusel vertical a través de un PLC (real o simulador).

Permite consultar el estado y enviar comandos al sistema de almacenamiento automatizado.
Incluye documentación Swagger y CORS para integración con sistemas externos.

Autor: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas
Fecha: 2023-09-13
Última modificación: 2025-03-13
"""

import os
import logging
from flask import Flask, jsonify, request, abort
from flasgger import Swagger
from flask_cors import CORS
from commons.utils import interpretar_estado_plc
from models.plc import PLC  # Importación explícita del PLC real [[2]]
from controllers.carousel_controller import CarouselController
import time


def create_app(plc):
    """
    Crea la instancia de la aplicación Flask.
    Incluye configuración de CORS segura, logging y manejo global de errores.
    Args:
        plc: Instancia del PLC (real o simulador) [[6]]
    """
    app = Flask(__name__)

    # Limitar tamaño máximo de payload (prevención DoS)
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024  # 2 KB

    # Configuración de CORS segura
    allowed_origins = os.getenv(
        "API_ALLOWED_ORIGINS", "http://localhost, http://127.0.0.1, http://192.168.1.0/24").split(",")
    allowed_origins = [o.strip() for o in allowed_origins]
    CORS(app, resources={r"/*": {"origins": allowed_origins}})

    # Configuración de Swagger [[5]]
    app.config['SWAGGER'] = {
        'title': 'API de Control de Carrusel',
        'uiversion': 3,
        'description': 'API para comunicación con PLC industrial (Modo real/simulador)'
    }
    Swagger(app)

    # Inicializar controlador
    carousel_controller = CarouselController(plc)

    # Logging de errores
    logger = logging.getLogger("api")

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Error no controlado: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

    @app.errorhandler(413)
    def handle_large_request(e):
        return jsonify({'error': 'Payload demasiado grande'}), 413

    @app.route('/v1/status', methods=['GET'])
    def get_status():
        """
        Obtiene el estado y posición del PLC.
        ---
        tags:
          - Estado del PLC
        responses:
          200:
            description: Estado actual del sistema.
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    status_code:
                      type: integer
                      description: Código de estado (8 bits).
                    position:
                      type: integer
                      description: Posición del carrusel (0-9).
          500:
            description: Error de comunicación.
        """
        if plc.connect():
            try:
                plc.send_command(0)  # Comando STATUS
                time.sleep(0.5)
                response = plc.receive_response()
                return jsonify(response), 200
            except Exception as e:
                logger.error(f"Error en /v1/status: {str(e)}")
                return jsonify({'error': f'Error: {str(e)}'}), 500
            finally:
                plc.close()
        else:
            return jsonify({'error': 'No se pudo conectar al PLC'}), 500

    @app.route('/v1/command', methods=['POST'])
    def send_command():
        """
        Envía un comando al PLC.
        ---
        tags:
          - Control del Carrusel
        parameters:
          - in: body
            name: Comando
            required: true
            schema:
              type: object
              properties:
                command:
                  type: integer
                  example: 1
                argument:
                  type: integer
                  example: 3
        responses:
          200:
            description: Comando procesado.
          400:
            description: Parámetros inválidos.
          500:
            description: Error interno.
        """
        if not request.is_json:
            return jsonify({'error': 'Solicitud debe ser JSON'}), 400

        data = request.get_json()
        # Validación estricta de tipos y rangos
        command = data.get('command')
        argument = data.get('argument')

        if command is None:
            return jsonify({'error': 'Comando no especificado'}), 400
        if not isinstance(command, int):
            return jsonify({'error': 'El comando debe ser un entero'}), 400
        if not (0 <= command <= 255):
            return jsonify({'error': 'Comando fuera de rango (0-255)'}), 400

        if argument is not None:
            if not isinstance(argument, int):
                return jsonify({'error': 'El argumento debe ser un entero'}), 400
            if not (0 <= argument <= 255):
                return jsonify({'error': 'Argumento inválido (0-255)'}), 400

        if plc.connect():
            try:
                carousel_controller.send_command(command, argument)
                return jsonify({'status': 'Comando enviado'}), 200
            except Exception as e:
                logger.error(f"Error en /v1/command: {str(e)}")
                return jsonify({'error': f'Error PLC: {str(e)}'}), 500
            finally:
                plc.close()
        else:
            return jsonify({'error': 'No se pudo conectar al PLC'}), 500

    return app
