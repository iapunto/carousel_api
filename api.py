"""
API para el control de un carrusel vertical a través de un PLC.

Esta API permite enviar comandos al PLC y recibir información sobre su estado y posición.

Autor: Industrias Pico S.A.S
Desarrollo y administración: IA Punto: Soluciones Integrales de Tecnología y Marketing
Dirección: MEng. Sergio Lankaster Rondón Melo
Colaboración: Ing. Francisco Garnica
Fecha de creación: 2023-09-13
Última modificación: 2024-09-27
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger
from controllers.carousel_controller import CarouselController
from dotenv import load_dotenv
import os
import time

# Cargar variables de entorno
load_dotenv()
plc_ip = os.getenv('PLC_IP')
plc_port = int(3200)  # Puerto predeterminado si no se especifica
mode = os.getenv('MODE')

# Crear instancias de PLC y controlador según el modo
if mode == 'simulator':
    from models.plc_simulator import PLCSimulator
    plc = PLCSimulator(plc_ip, plc_port)
elif mode == 'plc':
    from models.plc import PLC
    plc = PLC(plc_ip, plc_port)
else:
    raise ValueError("Modo inválido en el archivo .env. Debe ser 'simulator' o 'plc'")

carousel_controller = CarouselController(plc)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Permitir cualquier origen (para desarrollo)

# Configuración de Swagger
app.config['SWAGGER'] = {
    'title': 'API de Control de Carrusel',
    'uiversion': 3
}
swagger = Swagger(app)

@app.route('/v1/status', methods=['GET'])
def get_status():
    """
    Obtiene el estado y la posición actual del PLC.
    ---
    tags:
      - Estado del PLC
    responses:
      200:
        description: Estado y posición del PLC.
        content:
          application/json:
            schema:
              type: object
              properties:
                status_code:
                  type: integer
                  description: Código de estado del PLC (8 bits).
                position:
                  type: integer
                  description: Posición actual del carrusel (0-9).
      500:
        description: Error al comunicarse con el PLC.
    """
    try:
        if not plc.connect():
            return jsonify({'error': 'No se pudo conectar al PLC'}), 500

        # Envía el comando STATUS (0) para obtener el estado actual
        plc.send_command(0)
        time.sleep(0.5)  # Espera para recibir la respuesta

        # Recibe el estado y la posición del PLC
        response = plc.receive_response()
        if response:
            return jsonify(response), 200
        else:
            return jsonify({'error': 'No se pudo obtener el estado del PLC'}), 500
    except Exception as e:
        return jsonify({'error': f'Error al comunicarse con el PLC: {e}'}), 500
    finally:
        plc.close()

@app.route('/v1/command', methods=['POST'])
def send_command():
    """
    Envía un comando al PLC.
    ---
    tags:
      - Control del Carrusel
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            command:
              type: integer
              description: Número entero que representa el comando a enviar (0-255).
              example: 1  # Ejemplo de comando (MUEVETE)
            argument:
              type: integer
              description: Número entero que representa el argumento del comando (opcional, 0-255).
              example: 3  # Ejemplo de argumento (bucket 3)
    responses:
      200:
        description: Comando enviado exitosamente.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Comando enviado exitosamente
      400:
        description: Error en la solicitud. Puede ser debido a datos faltantes, inválidos o el PLC no está en el estado adecuado.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Comando no especificado
      500:
        description: Error interno del servidor al comunicarse con el PLC.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: Error al comunicarse con el PLC
    """
    try:
        if not plc.connect():
            return jsonify({'error': 'No se pudo conectar al PLC'}), 500

        data = request.get_json()
        command = data.get('command')
        argument = data.get('argument')

        if command is None:
            return jsonify({'error': 'Comando no especificado'}), 400

        # Validar el comando
        if not isinstance(command, int) or command < 0 or command > 255:
            return jsonify({'error': 'Comando inválido'}), 400

        # Validar el argumento (si existe)
        if argument is not None and (not isinstance(argument, int) or argument < 0 or argument > 255):
            return jsonify({'error': 'Argumento inválido'}), 400

        # Enviar el comando y el argumento al PLC
        carousel_controller.send_command(command, argument)

        return jsonify({'message': 'Comando enviado exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': f'Error al comunicarse con el PLC: {e}'}), 500
    finally:
        plc.close()

if __name__ == '__main__':
    app.run(debug=False)