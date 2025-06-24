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
from filelock import Timeout


def create_app(plc=None, plc_manager=None):
    """
    Crea la instancia de la aplicación Flask.
    Incluye configuración de CORS segura, logging y manejo global de errores.

    Args:
        plc: Instancia del PLC (real o simulador) para modo single-PLC
        plc_manager: Instancia del PLCManager para modo multi-PLC

    Note:
        Debe proporcionarse exactamente uno de los dos parámetros
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

    # Validar parámetros
    if not plc and not plc_manager:
        raise ValueError("Debe proporcionarse 'plc' o 'plc_manager'")
    if plc and plc_manager:
        raise ValueError(
            "Solo puede proporcionarse 'plc' o 'plc_manager', no ambos")

    # Determinar modo de operación
    is_multi_plc = plc_manager is not None

    # Inicializar controlador para modo single-PLC
    carousel_controller = CarouselController(plc) if plc else None

    # Logging de errores
    logger = logging.getLogger("api")

    if is_multi_plc:
        logger.info(
            f"API iniciada en modo MULTI-PLC con {len(plc_manager.get_available_machines())} máquinas")
    else:
        logger.info("API iniciada en modo SINGLE-PLC")

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
        acquired_interprocess = False
        acquired_global = False
        try:
            acquired_interprocess = plc_interprocess_lock.acquire(timeout=2)
            if not acquired_interprocess:
                logger.warning(
                    f"[COMMAND] PLC ocupado por otro proceso (interproceso) desde {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': 'PLC ocupado por otro proceso, intente de nuevo en unos segundos',
                    'code': PLC_BUSY
                }), 409
            acquired_global = plc_access_lock.acquire(timeout=2)
            if not acquired_global:
                logger.warning(
                    f"[COMMAND] PLC ocupado (lock global) desde {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': 'PLC ocupado, intente de nuevo en unos segundos',
                    'code': PLC_BUSY
                }), 409
            # Ejecutar el comando usando el controlador
            result = carousel_controller.send_command(command, argument)
            logger.info(f"[COMMAND] Respuesta: {result}")
            if isinstance(result, dict) and result.get('error') == 'PLC en movimiento':
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': result['error'],
                    'code': PLC_BUSY
                }), 409
            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None
            }), 200
        except Timeout as e:
            logger.warning(
                f"[COMMAND] Timeout al adquirir lock interproceso para {request.remote_addr}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': 'PLC ocupado por otro proceso, intente de nuevo en unos segundos',
                'code': PLC_BUSY
            }), 409
        except Exception as e:
            logger.error(
                f"[COMMAND] Error para {request.remote_addr}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error al procesar el comando: {str(e)}',
                'code': INTERNAL_ERROR
            }), 500
        finally:
            if acquired_global:
                plc_access_lock.release()
            if acquired_interprocess:
                plc_interprocess_lock.release()

    @app.route('/v1/health', methods=['GET'])
    def health():
        """
        Endpoint de salud para monitoreo y orquestadores.
        ---
        tags:
          - Salud
        responses:
          200:
            description: API operativa.
        """
        if is_multi_plc:
            health_data = plc_manager.health_check()
            return jsonify({
                'status': 'ok',
                'mode': 'multi-plc',
                'health': health_data
            }), 200
        else:
            return jsonify({
                'status': 'ok',
                'mode': 'single-plc'
            }), 200

    # ================================
    # ENDPOINTS MULTI-PLC
    # ================================

    if is_multi_plc:

        @app.route('/v1/machines', methods=['GET'])
        def get_machines():
            """
            Lista todas las máquinas disponibles.
            ---
            tags:
              - Multi-PLC
            responses:
              200:
                description: Lista de máquinas disponibles.
                content:
                  application/json:
                    schema:
                      type: object
                      properties:
                        success:
                          type: boolean
                        data:
                          type: array
                          items:
                            type: object
                            properties:
                              id:
                                type: string
                                example: "machine_1"
                              name:
                                type: string
                                example: "Carrusel Principal"
                              ip:
                                type: string
                                example: "192.168.1.50"
                              port:
                                type: integer
                                example: 3200
                              type:
                                type: string
                                example: "Real PLC"
                              status:
                                type: string
                                example: "available"
            """
            try:
                logger.info(f"[MACHINES] Petición desde {request.remote_addr}")
                machines = plc_manager.get_available_machines()
                logger.info(f"[MACHINES] Respuesta: {len(machines)} máquinas")
                return jsonify({
                    'success': True,
                    'data': machines,
                    'error': None,
                    'code': None
                }), 200
            except Exception as e:
                logger.error(
                    f"[MACHINES] Error para {request.remote_addr}: {str(e)}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': f'Error obteniendo lista de máquinas: {str(e)}',
                    'code': INTERNAL_ERROR
                }), 500

        @app.route('/v1/machines/<machine_id>/status', methods=['GET'])
        def get_machine_status(machine_id):
            """
            Obtiene el estado de una máquina específica.
            ---
            tags:
              - Multi-PLC
            parameters:
              - in: path
                name: machine_id
                required: true
                schema:
                  type: string
                  example: "machine_1"
                description: ID de la máquina
            responses:
              200:
                description: Estado actual de la máquina.
              404:
                description: Máquina no encontrada.
              500:
                description: Error de comunicación.
            """
            try:
                logger.info(
                    f"[MACHINE_STATUS] Petición para {machine_id} desde {request.remote_addr}")
                result = plc_manager.get_machine_status(
                    machine_id, request.remote_addr)
                logger.info(
                    f"[MACHINE_STATUS] Respuesta para {machine_id}: {result}")
                return jsonify({
                    'success': True,
                    'data': result,
                    'error': None,
                    'code': None
                }), 200
            except ValueError as e:
                logger.warning(
                    f"[MACHINE_STATUS] Máquina {machine_id} no encontrada desde {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': str(e),
                    'code': BAD_REQUEST
                }), 404
            except Exception as e:
                logger.error(
                    f"[MACHINE_STATUS] Error para {machine_id} desde {request.remote_addr}: {str(e)}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': f'Error de comunicación con la máquina {machine_id}: {str(e)}',
                    'code': PLC_CONN_ERROR
                }), 500

        @app.route('/v1/machines/<machine_id>/command', methods=['POST'])
        def send_machine_command(machine_id):
            """
            Envía un comando a una máquina específica.
            ---
            tags:
              - Multi-PLC
            parameters:
              - in: path
                name: machine_id
                required: true
                schema:
                  type: string
                  example: "machine_1"
                description: ID de la máquina
              - in: body
                name: Comando
                required: true
                schema:
                  type: object
                  properties:
                    command:
                      type: integer
                      example: 1
                      description: Código de comando (0-255)
                    argument:
                      type: integer
                      example: 3
                      description: Argumento opcional (0-255)
            responses:
              200:
                description: Comando procesado correctamente.
              400:
                description: Parámetros inválidos.
              404:
                description: Máquina no encontrada.
              409:
                description: Máquina ocupada.
              500:
                description: Error interno.
            """
            if not request.is_json:
                logger.warning(
                    f"[MACHINE_COMMAND] Solicitud no JSON para {machine_id} desde {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': 'Solicitud debe ser JSON',
                    'code': BAD_REQUEST
                }), 400

            data = request.get_json()
            command = data.get('command')
            argument = data.get('argument')

            # Validar parámetros
            if not isinstance(command, int) or not (0 <= command <= 255):
                logger.warning(
                    f"[MACHINE_COMMAND] Comando inválido para {machine_id} desde {request.remote_addr}: {command}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': "El parámetro 'command' debe ser un entero entre 0 y 255",
                    'code': BAD_COMMAND
                }), 400

            if argument is not None and (not isinstance(argument, int) or not (0 <= argument <= 255)):
                logger.warning(
                    f"[MACHINE_COMMAND] Argumento inválido para {machine_id} desde {request.remote_addr}: {argument}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': "El parámetro 'argument' debe ser un entero entre 0 y 255",
                    'code': BAD_COMMAND
                }), 400

            try:
                logger.info(
                    f"[MACHINE_COMMAND] Comando {command}({argument}) para {machine_id} desde {request.remote_addr}")
                result = plc_manager.send_command_to_machine(
                    machine_id, command, argument, request.remote_addr)
                logger.info(
                    f"[MACHINE_COMMAND] Respuesta para {machine_id}: {result}")
                return jsonify({
                    'success': True,
                    'data': result,
                    'error': None,
                    'code': None
                }), 200
            except ValueError as e:
                logger.warning(
                    f"[MACHINE_COMMAND] Máquina {machine_id} no encontrada desde {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': str(e),
                    'code': BAD_REQUEST
                }), 404
            except Exception as e:
                logger.error(
                    f"[MACHINE_COMMAND] Error para {machine_id} desde {request.remote_addr}: {str(e)}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': f'Error al procesar comando para {machine_id}: {str(e)}',
                    'code': INTERNAL_ERROR
                }), 500

        @app.route('/v1/machines/<machine_id>/move', methods=['POST'])
        def move_machine_to_position(machine_id):
            """
            Mueve una máquina a una posición específica.
            ---
            tags:
              - Multi-PLC
            parameters:
              - in: path
                name: machine_id
                required: true
                schema:
                  type: string
                  example: "machine_1"
                description: ID de la máquina
              - in: body
                name: Posición
                required: true
                schema:
                  type: object
                  properties:
                    position:
                      type: integer
                      example: 5
                      description: Posición objetivo (0-9)
            responses:
              200:
                description: Movimiento iniciado correctamente.
              400:
                description: Parámetros inválidos.
              404:
                description: Máquina no encontrada.
              500:
                description: Error interno.
            """
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': 'Solicitud debe ser JSON',
                    'code': BAD_REQUEST
                }), 400

            data = request.get_json()
            position = data.get('position')

            if not isinstance(position, int) or not (0 <= position <= 9):
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': "El parámetro 'position' debe ser un entero entre 0 y 9",
                    'code': BAD_COMMAND
                }), 400

            try:
                logger.info(
                    f"[MACHINE_MOVE] Mover {machine_id} a posición {position} desde {request.remote_addr}")
                result = plc_manager.move_machine_to_position(
                    machine_id, position, request.remote_addr)
                logger.info(
                    f"[MACHINE_MOVE] Respuesta para {machine_id}: {result}")
                return jsonify({
                    'success': True,
                    'data': result,
                    'error': None,
                    'code': None
                }), 200
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': str(e),
                    'code': BAD_REQUEST
                }), 404
            except Exception as e:
                logger.error(
                    f"[MACHINE_MOVE] Error para {machine_id} desde {request.remote_addr}: {str(e)}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': f'Error moviendo {machine_id}: {str(e)}',
                    'code': INTERNAL_ERROR
                }), 500

    return app
