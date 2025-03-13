"""
API para el control de un carrusel vertical a través de un PLC.

Autor: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Integrales de Tecnología y Marketing
Fecha: 2023-09-13
Última modificación: 2025-03-13
"""

from flask import Flask, jsonify, request
from flasgger import Swagger
from flask_cors import CORS
from controllers.carousel_controller import CarouselController
import time


def create_app(plc):
    """
    Crea la instancia de la aplicación Flask.
    Args:
        plc: Instancia del PLC (real o simulador) [[6]]
    """
    app = Flask(__name__)

    # Configuración de CORS para permitir acceso desde WMS externo [[8]]
    app.config['CORS_HEADERS'] = 'Content-Type'
    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    # Configuración de Swagger [[5]]
    app.config['SWAGGER'] = {
        'title': 'API de Control de Carrusel',
        'uiversion': 3,
        'description': 'API para comunicación con PLC industrial (Modo real/simulador)'
    }
    Swagger(app)

    # Inicializar controlador
    carousel_controller = CarouselController(plc)

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
        command = data.get('command')
        argument = data.get('argument')

        if command is None:
            return jsonify({'error': 'Comando no especificado'}), 400

        if not (0 <= command <= 255):
            return jsonify({'error': 'Comando fuera de rango (0-255)'}), 400

        if argument is not None and not (0 <= argument <= 255):
            return jsonify({'error': 'Argumento inválido (0-255)'}), 400

        if plc.connect():
            try:
                carousel_controller.send_command(command, argument)
                return jsonify({'status': 'Comando enviado'}), 200
            except Exception as e:
                return jsonify({'error': f'Error PLC: {str(e)}'}), 500
            finally:
                plc.close()
        else:
            return jsonify({'error': 'No se pudo conectar al PLC'}), 500

    return app
