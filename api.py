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
from plc_cache import (plc_status_cache, plc_access_lock,
                       plc_interprocess_lock, read_cached_status)
from commons.error_codes import (PLC_CONN_ERROR, PLC_BUSY, PLC_UNSAFE_STATE,
                                 BAD_COMMAND, BAD_REQUEST, INTERNAL_ERROR)
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

    def _default_machine_id():
        """Primera máquina configurada (para rutas legacy /v1/status y /v1/command)"""
        machines = plc_manager.get_available_machines()
        if not machines:
            raise RuntimeError("No hay máquinas PLC configuradas")
        return machines[0]["id"]

    # Antigüedad máxima aceptable de la caché de estado del PLC (seg).
    # Un poco por encima del intervalo de poll en reposo del WS server.
    STATUS_CACHE_TTL = float(os.getenv("PLC_STATUS_CACHE_TTL", "25"))
    # Antigüedad máxima de la caché para la guardia de seguridad (seg).
    # Más corta: las alarmas cambian rápido; el poller refresca cada
    # ~1-3 s, así que 4 s equivale a "última lectura del poller".
    SAFETY_CACHE_TTL = float(os.getenv("PLC_SAFETY_CACHE_TTL", "4"))

    def _safety_blockers(machine_id=None, force=False):
        """Verifica que el PLC esté en estado seguro para recibir comandos.

        Lee el estado FRESCO del PLC (nunca la caché — los estados de
        error cambian rápido). El hardware ya bloquea el modo Manual con
        el switch físico, pero NO bloquea estados de error: si el PLC
        reporta VFD/alarma/parada y llega un comando, la máquina se
        mueve igual. Esta guardia es la última línea de defensa.

        Args:
            machine_id: ID de máquina (multi-PLC) o None (single-PLC).
            force: Bypass explícito para diagnóstico técnico (errores
                   fantasma reportados por el PLC).

        Returns:
            Lista de strings con los bloqueos detectados; [] = seguro.
        """
        if force:
            return []
        if is_multi_plc:
            # Preferir la caché muy fresca del poller WS — evita un
            # roundtrip completo al PLC antes de cada comando. Si la
            # caché está viciada/ausente (poller caído), lectura viva:
            # la seguridad nunca depende de un dato viejo.
            status = read_cached_status(
                machine_id, max_age=SAFETY_CACHE_TTL)
            if status is None:
                status = plc_manager.get_machine_status(
                    machine_id, client_ip="safety_check")
            raw = status.get("raw_status")
        else:
            status = carousel_controller.get_current_status()
            raw = status.get("raw_status", status.get("status_code"))
        if raw is None:
            raise RuntimeError("No se pudo leer el estado del PLC")
        blockers = []
        if not (raw & 0x01):
            blockers.append("READY: el equipo no está listo para operar")
        if (raw >> 1) & 0x01:
            blockers.append("RUN: el equipo está en movimiento")
        if not ((raw >> 2) & 0x01):
            blockers.append("MODO_OPERACION: el equipo está en Modo Manual")
        if raw & 0x08:
            blockers.append("ALARMA activa")
        if not ((raw >> 4) & 0x01):
            blockers.append("PARADA DE EMERGENCIA activa")
        if raw & 0x20:
            blockers.append("Error en el variador de velocidad (VFD)")
        if raw & 0x40:
            blockers.append("Error de posicionamiento")
        return blockers

    def _is_forced(data=None):
        """Bypass de seguridad: JSON {"force": true} o query ?force=1"""
        if data and data.get("force") is True:
            return True
        return request.args.get("force", "").lower() in ("1", "true", "yes")

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
            if is_multi_plc:
                machine_id = _default_machine_id()
                # Caché compartida: el WS server es el único poller del PLC
                result = read_cached_status(
                    machine_id, max_age=STATUS_CACHE_TTL)
                if result is None:
                    result = plc_manager.get_machine_status(
                        machine_id, client_ip=request.remote_addr)
            else:
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
        # Guardia de seguridad: comandos que accionan (no STATUS) exigen
        # estado sin errores. Lectura FRESCA del PLC, nunca de la caché.
        if command != 0 and is_multi_plc:
            try:
                blockers = _safety_blockers(
                    _default_machine_id(), force=_is_forced(data))
            except Exception as e:
                blockers = [f"No se pudo verificar el estado del PLC: {e}"]
            if blockers:
                logger.warning(
                    f"[COMMAND] Bloqueado por seguridad desde {request.remote_addr}: {blockers}")
                return jsonify({
                    'success': False,
                    'data': {'blockers': blockers},
                    'error': 'Comando bloqueado: ' + ' | '.join(blockers),
                    'code': PLC_UNSAFE_STATE
                }), 409
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
            if is_multi_plc:
                result = plc_manager.send_command_to_machine(
                    _default_machine_id(), command, argument,
                    client_ip=request.remote_addr,
                    skip_position_check=_is_forced(data))
            else:
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
                # Caché compartida: el WS server es el único poller del PLC
                result = read_cached_status(
                    machine_id, max_age=STATUS_CACHE_TTL)
                if result is None:
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

        @app.route('/v1/machines/<machine_id>/diagnostics', methods=['GET'])
        def get_machine_diagnostics(machine_id):
            """
            Diagnóstico completo de una máquina (estilo OBD vehicular).
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
                description: Diagnóstico completo con fallas localizadas.
              404:
                description: Máquina no encontrada.
              500:
                description: Error interno.
            """
            try:
                logger.info(
                    f"[DIAGNOSTICS] Petición para {machine_id} desde {request.remote_addr}")
                result = plc_manager.get_machine_diagnostics(
                    machine_id, request.remote_addr)
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
                    f"[DIAGNOSTICS] Error para {machine_id}: {str(e)}")
                return jsonify({
                    'success': False,
                    'data': None,
                    'error': f'Error en diagnóstico: {str(e)}',
                    'code': INTERNAL_ERROR
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

            # Guardia de seguridad: comandos que accionan (no STATUS) exigen
            # estado sin errores. Lectura FRESCA del PLC, nunca de la caché.
            if command != 0:
                try:
                    blockers = _safety_blockers(
                        machine_id, force=_is_forced(data))
                except Exception as e:
                    blockers = [
                        f"No se pudo verificar el estado del PLC: {e}"]
                if blockers:
                    logger.warning(
                        f"[MACHINE_COMMAND] Bloqueado por seguridad para {machine_id} desde {request.remote_addr}: {blockers}")
                    return jsonify({
                        'success': False,
                        'data': {'blockers': blockers},
                        'error': 'Comando bloqueado: ' + ' | '.join(blockers),
                        'code': PLC_UNSAFE_STATE
                    }), 409

            try:
                logger.info(
                    f"[MACHINE_COMMAND] Comando {command}({argument}) para {machine_id} desde {request.remote_addr}")
                result = plc_manager.send_command_to_machine(
                    machine_id, command, argument, request.remote_addr,
                    skip_position_check=_is_forced(data))
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

            # Guardia de seguridad: lectura FRESCA del PLC, nunca de la caché.
            try:
                blockers = _safety_blockers(
                    machine_id, force=_is_forced(data))
            except Exception as e:
                blockers = [f"No se pudo verificar el estado del PLC: {e}"]
            if blockers:
                logger.warning(
                    f"[MACHINE_MOVE] Bloqueado por seguridad para {machine_id} desde {request.remote_addr}: {blockers}")
                return jsonify({
                    'success': False,
                    'data': {'blockers': blockers},
                    'error': 'Movimiento bloqueado: ' + ' | '.join(blockers),
                    'code': PLC_UNSAFE_STATE
                }), 409

            try:
                logger.info(
                    f"[MACHINE_MOVE] Mover {machine_id} a posición {position} desde {request.remote_addr}")
                result = plc_manager.move_machine_to_position(
                    machine_id, position, request.remote_addr,
                    skip_position_check=_is_forced(data))
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
