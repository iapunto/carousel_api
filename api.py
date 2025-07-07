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
from flask import Flask, jsonify, request, abort
from flasgger import Swagger
from flask_cors import CORS
from controllers.carousel_controller import CarouselController
import time
import logging
from plc_cache import plc_status_cache, plc_access_lock
from commons.utils import interpretar_estado_plc


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
        Obtiene el estado y posición del PLC, decodificando el status_code para mostrar los estados legibles. Usa el cache actualizado por el hilo de monitoreo.
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
                    success:
                      type: boolean
                    data:
                      type: object
                    error:
                      type: string
                    code:
                      type: string
          500:
            description: Error de comunicación.
        """
        status = plc_status_cache.get('status')
        if status is not None and 'status_code' in status and 'position' in status:
            status_code = status['status_code']
            position = status['position']
            estados = interpretar_estado_plc(status_code)
            raw_status_bin = format(status_code, '08b')[
                ::-1]  # binario, derecha a izquierda
            response = {
                'success': True,
                'data': {
                    'status': estados,
                    'position': position,
                    'raw_status': status_code,
                    'raw_status_bin': raw_status_bin,
                    'timestamp': int(time.time())
                },
                'error': None,
                'code': None
            }
            return jsonify(response), 200
        else:
            return jsonify({'success': False, 'data': None, 'error': 'Estado no disponible', 'code': 'NO_STATUS'}), 503

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
            return jsonify({'error': 'Solicitud debe ser JSON', 'status_message': 'El cuerpo de la solicitud debe ser JSON.'}), 400
        data = request.get_json()
        command = data.get('command')
        argument = data.get('argument')
        if command is None:
            return jsonify({'error': 'Falta el parámetro command', 'status_message': 'El parámetro "command" es obligatorio.'}), 400
        acquired = plc_access_lock.acquire(timeout=2)
        if not acquired:
            return jsonify({'error': 'PLC ocupado, intente de nuevo en unos segundos', 'status_message': 'El PLC está ocupado, por favor intente nuevamente.'}), 409
        try:
            if plc.connect():
                try:
                    # Consultar posición inicial antes de enviar el comando
                    initial_status = plc.get_current_status()
                    initial_position = initial_status.get('position', None)
                    plc.send_command(command, argument)
                    time.sleep(0.5)
                    response = plc.receive_response()
                    plc.close()
                    # Si la respuesta es inválida, agrega mensaje
                    if response.get('status_code', -1) == 0 and response.get('position', -1) == 0:
                        return jsonify({**response, 'initial_position': initial_position, 'target_position': argument, 'status_message': 'Advertencia: El PLC respondió con valores nulos o inválidos. Verifique la operación física.'}), 200
                    # Si todo fue bien, mensaje de éxito y posiciones
                    return jsonify({**response, 'initial_position': initial_position, 'target_position': argument, 'status_message': 'Comando enviado exitosamente al PLC.'}), 200
                except Exception as e:
                    logger.error(f"Error en /v1/command: {str(e)}")
                    return jsonify({'error': f'Error: {str(e)}', 'status_message': f'Error al procesar el comando: {str(e)}'}), 500
            else:
                return jsonify({'error': 'No se pudo conectar al PLC', 'status_message': 'No se pudo establecer conexión con el PLC. Verifique el cableado, la IP y el estado del equipo.'}), 500
        finally:
            plc_access_lock.release()

    return app
