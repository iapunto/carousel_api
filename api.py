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
from plc_cache import plc_status_cache, plc_access_lock, plc_interprocess_lock
from commons.error_codes import PLC_CONN_ERROR, PLC_BUSY, BAD_COMMAND, BAD_REQUEST, INTERNAL_ERROR


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
        "API_ALLOWED_ORIGINS", "http://localhost, http://127.0.0.1, http://192.168.1.0/24, http://localhost:3000,http://localhost:5001,http://127.0.0.1:3000,http://127.0.0.1:5001").split(",")
    allowed_origins = [o.strip()
                       for o in allowed_origins if o.strip() and o.strip() != "*"]
    if not allowed_origins:
        raise RuntimeError(
            "Por seguridad, debe definir orígenes permitidos en la variable de entorno API_ALLOWED_ORIGINS")
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    # Documentación: Para producción, configure API_ALLOWED_ORIGINS solo con los dominios/autorizados.

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
                    status:
                      type: object
                      description: Estado interpretado del PLC.
                    position:
                      type: integer
                      description: Posición del carrusel (0-9).
                    raw_status:
                      type: integer
                      description: Código de estado (8 bits).
          500:
            description: Error de comunicación.
        """
        try:
            logger.info(f"[STATUS] Petición desde {request.remote_addr}")
            result = carousel_controller.get_current_status()
            logger.info(f"[STATUS] Respuesta: {result}")
            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None
            }), 200
        except Exception as e:
            logger.error(
                f"[STATUS] Error para {request.remote_addr}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error de comunicación con el PLC: {str(e)}',
                'code': PLC_CONN_ERROR
            }), 500

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
            logger.warning(
                f"[COMMAND] Solicitud no JSON desde {request.remote_addr}")
            return jsonify({
                'success': False,
                'data': None,
                'error': 'Solicitud debe ser JSON',
                'code': BAD_REQUEST
            }), 400
        data = request.get_json()
        command = data.get('command')
        argument = data.get('argument')
        if not isinstance(command, int) or not (0 <= command <= 255):
            logger.warning(
                f"[COMMAND] Parámetro 'command' inválido desde {request.remote_addr}, valor: {command}")
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'command' debe ser un entero entre 0 y 255",
                'code': BAD_COMMAND
            }), 400
        if argument is not None and (not isinstance(argument, int) or not (0 <= argument <= 255)):
            logger.warning(
                f"[COMMAND] Parámetro 'argument' inválido desde {request.remote_addr}, valor: {argument}")
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'argument' debe ser un entero entre 0 y 255",
                'code': BAD_COMMAND
            }), 400
        # Bloqueo interproceso antes del lock global
        interprocess_acquired = plc_interprocess_lock.acquire(timeout=2)
        if not interprocess_acquired:
            logger.warning(
                f"[COMMAND] PLC ocupado por otro proceso para {request.remote_addr}")
            return jsonify({
                'success': False,
                'data': None,
                'error': 'PLC ocupado por otro proceso, intente de nuevo en unos segundos',
                'code': PLC_BUSY
            }), 409
        acquired = plc_access_lock.acquire(timeout=2)
        if not acquired:
            plc_interprocess_lock.release()
            logger.warning(f"[COMMAND] PLC ocupado para {request.remote_addr}")
            return jsonify({
                'success': False,
                'data': None,
                'error': 'PLC ocupado, intente de nuevo en unos segundos',
                'code': PLC_BUSY
            }), 409
        try:
            try:
                logger.info(
                    f"[COMMAND] Petición desde {request.remote_addr}, datos: {data}")
                result = carousel_controller.send_command(command, argument)
                logger.info(f"[COMMAND] Respuesta: {result}")
                return jsonify({
                    'success': True,
                    'data': result,
                    'error': None,
                    'code': None
                }), 200
            except Exception as e:
                logger.error(
                    f"[COMMAND] Error para {request.remote_addr}, datos: {data}, error: {str(e)}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': f'Error al procesar el comando: {str(e)}',
                    'code': INTERNAL_ERROR
                }), 500
        finally:
            plc_access_lock.release()
            plc_interprocess_lock.release()

    return app
