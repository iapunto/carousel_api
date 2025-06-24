"""
API para el control de múltiples carruseles verticales a través de PLCs (reales o simuladores).

Permite consultar el estado y enviar comandos a múltiples sistemas de almacenamiento automatizado.
Incluye documentación Swagger, CORS y logging detallado de conexiones de clientes.

Autor: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas
Fecha: 2023-09-13
Última modificación: 2025-01-XX
"""

import os
import logging
from flask import Flask, jsonify, request, abort
from flasgger import Swagger
from flask_cors import CORS
from commons.utils import interpretar_estado_plc
from models.plc_manager import PLCManager
import time
from plc_cache import plc_status_cache, plc_access_lock, plc_interprocess_lock
from commons.error_codes import PLC_CONN_ERROR, PLC_BUSY, BAD_COMMAND, BAD_REQUEST, INTERNAL_ERROR
from filelock import Timeout


def create_app(plc_manager):
    """
    Crea la instancia de la aplicación Flask con soporte multi-PLC.
    Incluye configuración de CORS segura, logging y manejo global de errores.
    Args:
        plc_manager: Instancia del PLCManager para gestionar múltiples PLCs
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

    # Configuración de Swagger
    app.config['SWAGGER'] = {
        'title': 'API de Control Multi-Carrusel',
        'uiversion': 3,
        'description': 'API para comunicación con múltiples PLCs industriales (Modo real/simulador)'
    }
    Swagger(app)

    # Logging de errores
    logger = logging.getLogger("api")

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception(f"Error no controlado: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

    @app.errorhandler(413)
    def handle_large_request(e):
        return jsonify({'error': 'Payload demasiado grande'}), 413

    # ========== ENDPOINTS PARA MÚLTIPLES MÁQUINAS ==========

    @app.route('/v1/machines', methods=['GET'])
    def get_machines():
        """
        Obtiene la lista de todas las máquinas disponibles.
        ---
        tags:
          - Gestión de Máquinas
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
                          name:
                            type: string
                          ip:
                            type: string
                          port:
                            type: integer
                          type:
                            type: string
                          status:
                            type: string
        """
        try:
            logger.info(
                f"[MACHINES] Consulta de máquinas desde {request.remote_addr}")
            machines = plc_manager.get_available_machines()
            return jsonify({
                'success': True,
                'data': machines,
                'error': None,
                'code': None
            }), 200
        except Exception as e:
            logger.error(f"[MACHINES] Error: {str(e)}")
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
          - Estado de Máquinas
        parameters:
          - name: machine_id
            in: path
            required: true
            schema:
              type: string
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
                f"[STATUS] Petición para máquina {machine_id} desde {request.remote_addr}")
            result = plc_manager.get_machine_status(
                machine_id, request.remote_addr)
            logger.info(
                f"[STATUS] Respuesta para máquina {machine_id}: {result}")
            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None,
                'machine_id': machine_id
            }), 200
        except ValueError as e:
            logger.warning(
                f"[STATUS] Máquina {machine_id} no encontrada desde {request.remote_addr}")
            return jsonify({
                'success': False,
                'data': None,
                'error': str(e),
                'code': BAD_REQUEST,
                'machine_id': machine_id
            }), 404
        except Exception as e:
            logger.error(
                f"[STATUS] Error para máquina {machine_id} desde {request.remote_addr}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error de comunicación con la máquina {machine_id}: {str(e)}',
                'code': PLC_CONN_ERROR,
                'machine_id': machine_id
            }), 500

    @app.route('/v1/machines/<machine_id>/command', methods=['POST'])
    def send_machine_command(machine_id):
        """
        Envía un comando a una máquina específica.
        ---
        tags:
          - Control de Máquinas
        parameters:
          - name: machine_id
            in: path
            required: true
            schema:
              type: string
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
                argument:
                  type: integer
                  example: 3
        responses:
          200:
            description: Comando procesado.
          400:
            description: Parámetros inválidos.
          404:
            description: Máquina no encontrada.
          500:
            description: Error interno.
        """
        if not request.is_json:
            logger.warning(
                f"[COMMAND] Solicitud no JSON para máquina {machine_id} desde {request.remote_addr}")
            return jsonify({
                'success': False,
                'data': None,
                'error': 'Solicitud debe ser JSON',
                'code': BAD_REQUEST,
                'machine_id': machine_id
            }), 400

        data = request.get_json()
        command = data.get('command')
        argument = data.get('argument')

        # Validaciones
        if not isinstance(command, int) or not (0 <= command <= 255):
            logger.warning(
                f"[COMMAND] Comando inválido para máquina {machine_id} desde {request.remote_addr}: {command}")
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'command' debe ser un entero entre 0 y 255",
                'code': BAD_COMMAND,
                'machine_id': machine_id
            }), 400

        if argument is not None and (not isinstance(argument, int) or not (0 <= argument <= 255)):
            logger.warning(
                f"[COMMAND] Argumento inválido para máquina {machine_id} desde {request.remote_addr}: {argument}")
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'argument' debe ser un entero entre 0 y 255",
                'code': BAD_COMMAND,
                'machine_id': machine_id
            }), 400

        try:
            logger.info(
                f"[COMMAND] Enviando comando {command} (arg: {argument}) a máquina {machine_id} desde {request.remote_addr}")
            result = plc_manager.send_command_to_machine(
                machine_id, command, argument, request.remote_addr)
            logger.info(
                f"[COMMAND] Comando exitoso para máquina {machine_id}: {result}")
            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None,
                'machine_id': machine_id
            }), 200
        except ValueError as e:
            logger.warning(
                f"[COMMAND] Máquina {machine_id} no encontrada desde {request.remote_addr}")
            return jsonify({
                'success': False,
                'data': None,
                'error': str(e),
                'code': BAD_REQUEST,
                'machine_id': machine_id
            }), 404
        except Exception as e:
            logger.error(
                f"[COMMAND] Error para máquina {machine_id} desde {request.remote_addr}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error enviando comando a máquina {machine_id}: {str(e)}',
                'code': PLC_CONN_ERROR,
                'machine_id': machine_id
            }), 500

    @app.route('/v1/machines/<machine_id>/move', methods=['POST'])
    def move_machine_to_position(machine_id):
        """
        Mueve una máquina a una posición específica.
        ---
        tags:
          - Control de Máquinas
        parameters:
          - name: machine_id
            in: path
            required: true
            schema:
              type: string
            description: ID de la máquina
          - in: body
            name: Posición
            required: true
            schema:
              type: object
              properties:
                position:
                  type: integer
                  minimum: 0
                  maximum: 9
                  example: 3
        responses:
          200:
            description: Movimiento ejecutado.
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
                'code': BAD_REQUEST,
                'machine_id': machine_id
            }), 400

        data = request.get_json()
        position = data.get('position')

        if not isinstance(position, int) or not (0 <= position <= 9):
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'position' debe ser un entero entre 0 y 9",
                'code': BAD_COMMAND,
                'machine_id': machine_id
            }), 400

        try:
            logger.info(
                f"[MOVE] Moviendo máquina {machine_id} a posición {position} desde {request.remote_addr}")
            result = plc_manager.move_machine_to_position(
                machine_id, position, request.remote_addr)
            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None,
                'machine_id': machine_id
            }), 200
        except ValueError as e:
            return jsonify({
                'success': False,
                'data': None,
                'error': str(e),
                'code': BAD_REQUEST,
                'machine_id': machine_id
            }), 404
        except Exception as e:
            logger.error(
                f"[MOVE] Error moviendo máquina {machine_id}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error moviendo máquina {machine_id}: {str(e)}',
                'code': PLC_CONN_ERROR,
                'machine_id': machine_id
            }), 500

    # ========== ENDPOINTS DE COMPATIBILIDAD (MÁQUINA POR DEFECTO) ==========

    @app.route('/v1/status', methods=['GET'])
    def get_status():
        """
        Obtiene el estado del PLC (compatibilidad - usa la primera máquina).
        ---
        tags:
          - Estado del PLC (Compatibilidad)
        responses:
          200:
            description: Estado actual del sistema.
          500:
            description: Error de comunicación.
        """
        try:
            # Usar la primera máquina disponible para compatibilidad
            machines = plc_manager.get_available_machines()
            if not machines:
                raise RuntimeError("No hay máquinas configuradas")

            default_machine = machines[0]['id']
            logger.info(
                f"[STATUS-COMPAT] Usando máquina por defecto {default_machine} desde {request.remote_addr}")

            result = plc_manager.get_machine_status(
                default_machine, request.remote_addr)
            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None,
                'machine_id': default_machine  # Incluir para claridad
            }), 200
        except Exception as e:
            logger.error(
                f"[STATUS-COMPAT] Error desde {request.remote_addr}: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error de comunicación con el PLC: {str(e)}',
                'code': PLC_CONN_ERROR
            }), 500

    @app.route('/v1/command', methods=['POST'])
    def send_command():
        """
        Envía un comando al PLC (compatibilidad - usa la primera máquina).
        ---
        tags:
          - Control del Carrusel (Compatibilidad)
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
                machine_id:
                  type: string
                  example: "machine_1"
                  description: "ID de máquina opcional. Si no se especifica, usa la primera disponible."
        responses:
          200:
            description: Comando procesado.
          400:
            description: Parámetros inválidos.
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
        command = data.get('command')
        argument = data.get('argument')
        # Permitir especificar máquina en el body
        machine_id = data.get('machine_id')

        # Validaciones
        if not isinstance(command, int) or not (0 <= command <= 255):
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'command' debe ser un entero entre 0 y 255",
                'code': BAD_COMMAND
            }), 400

        if argument is not None and (not isinstance(argument, int) or not (0 <= argument <= 255)):
            return jsonify({
                'success': False,
                'data': None,
                'error': "El parámetro 'argument' debe ser un entero entre 0 y 255",
                'code': BAD_COMMAND
            }), 400

        try:
            # Si no se especifica machine_id, usar la primera máquina disponible
            if not machine_id:
                machines = plc_manager.get_available_machines()
                if not machines:
                    raise RuntimeError("No hay máquinas configuradas")
                machine_id = machines[0]['id']
                logger.info(
                    f"[COMMAND-COMPAT] Usando máquina por defecto {machine_id}")

            logger.info(
                f"[COMMAND-COMPAT] Comando {command} (arg: {argument}) a máquina {machine_id} desde {request.remote_addr}")
            result = plc_manager.send_command_to_machine(
                machine_id, command, argument, request.remote_addr)

            return jsonify({
                'success': True,
                'data': result,
                'error': None,
                'code': None,
                'machine_id': machine_id
            }), 200
        except ValueError as e:
            return jsonify({
                'success': False,
                'data': None,
                'error': str(e),
                'code': BAD_REQUEST
            }), 404
        except Exception as e:
            logger.error(f"[COMMAND-COMPAT] Error: {str(e)}")
            return jsonify({
                'success': False,
                'data': None,
                'error': f'Error enviando comando: {str(e)}',
                'code': PLC_CONN_ERROR
            }), 500

    @app.route('/v1/health', methods=['GET'])
    def health():
        """
        Endpoint de salud de la API.
        ---
        tags:
          - Salud del Sistema
        responses:
          200:
            description: API funcionando correctamente.
        """
        machines = plc_manager.get_available_machines()
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'machines_count': len(machines),
                'machines': [m['id'] for m in machines]
            },
            'error': None,
            'code': None
        }), 200

    return app
