"""
Aplicación web para control remoto de carrusel industrial v2.6.0

Proyecto: Sistema de Control de Carrusel Industrial
Cliente: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas

Creado: 2025-06-24
Última modificación: 2025-06-24

Aplicación web moderna con soporte Multi-PLC similar al panel de comandos de la GUI.
"""

import time
import requests
import json
import os
from flask import Flask, render_template_string, request, jsonify
import sys

sys.path.insert(0, os.path.join(os.path.dirname(
    __file__), "python_portable", "site-packages"))

app = Flask(__name__)

# Configuración dinámica de API


def get_api_config():
    """Obtiene la configuración de la API (puerto y máquinas disponibles)."""
    try:
        # Intentar cargar configuración multi-PLC primero
        if os.path.exists("config_multi_plc.json"):
            with open("config_multi_plc.json", "r", encoding="utf-8") as f:
                multi_config = json.load(f)
                api_port = multi_config.get("api_config", {}).get("port", 5000)
                machines = multi_config.get("plc_machines", [])
                return api_port, machines, True  # multi_plc mode
        else:
            # Fallback para configuración single-PLC
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    api_port = config.get("api_port", 5000)
                    single_machine = {
                        "id": "single_plc",
                        "name": "PLC Principal",
                        "ip": config.get("ip", "192.168.1.50"),
                        "port": config.get("port", 3200),
                        "simulator": config.get("simulator_enabled", False)
                    }
                    return api_port, [single_machine], False  # single_plc mode
    except Exception as e:
        print(f"Error cargando configuración: {e}")

    # Configuración por defecto
    return 5000, [], False


HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Control Remoto Carrusel - v2.6.0</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body { 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container { 
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 2.5em; 
            border-radius: 20px; 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 800px;
            min-height: 500px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.2em;
            margin-bottom: 0.5em;
            background: linear-gradient(45deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.8;
            font-weight: 300;
        }
        
        .controls-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2em;
            margin-bottom: 2em;
        }
        
        .control-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 1.5em;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .control-section h3 {
            margin-bottom: 1em;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 0.5em;
        }
        
        .form-group {
            margin-bottom: 1.5em;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5em;
            font-weight: 600;
            font-size: 0.95em;
        }
        
        select, input[type=number] {
            width: 100%;
            padding: 12px 15px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            font-size: 1em;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        
        select:focus, input[type=number]:focus {
            outline: none;
            border-color: #4CAF50;
            background: rgba(255, 255, 255, 0.15);
        }
        
        select option {
            background: #2a5298;
            color: #fff;
        }
        
        .spinbox-container {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 5px;
        }
        
        .spinbox-btn {
            background: #FF6B6B;
            border: none;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.2em;
            font-weight: bold;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .spinbox-btn.up {
            background: #4CAF50;
        }
        
        .spinbox-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        .spinbox-btn:active {
            transform: scale(0.95);
        }
        
        .spinbox-input {
            flex: 1;
            text-align: center;
            background: transparent;
            border: none;
            font-size: 1.2em;
            font-weight: bold;
            padding: 8px;
        }
        
        .spinbox-range {
            font-size: 0.85em;
            opacity: 0.7;
            margin-left: 10px;
        }
        
        .move-button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(45deg, #2196F3, #1976D2);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 1.3em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 1em;
        }
        
        .move-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(33, 150, 243, 0.4);
        }
        
        .move-button:active {
            transform: translateY(0);
        }
        
        .move-button:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .notifications {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            padding: 1.5em;
            min-height: 200px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .notification-item {
            margin-bottom: 1em;
            padding: 10px 15px;
            border-radius: 8px;
            border-left: 4px solid;
            background: rgba(255, 255, 255, 0.05);
        }
        
        .notification-item.info {
            border-left-color: #2196F3;
        }
        
        .notification-item.success {
            border-left-color: #4CAF50;
        }
        
        .notification-item.error {
            border-left-color: #F44336;
        }
        
        .notification-item.warning {
            border-left-color: #FF9800;
        }
        
        .notification-time {
            font-size: 0.85em;
            opacity: 0.7;
            margin-bottom: 5px;
        }
        
        .notification-message {
            font-size: 0.95em;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-indicator.connected {
            background: #4CAF50;
            box-shadow: 0 0 10px #4CAF50;
        }
        
        .status-indicator.disconnected {
            background: #F44336;
        }
        
        .footer {
            text-align: center;
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 0.9em;
            opacity: 0.7;
        }
        
        @media (max-width: 768px) {
            .controls-grid {
                grid-template-columns: 1fr;
                gap: 1.5em;
            }
            
            .container {
                padding: 1.5em;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
        }
        
        /* Scrollbar personalizado */
        .notifications::-webkit-scrollbar {
            width: 6px;
        }
        
        .notifications::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }
        
        .notifications::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 3px;
        }
        
        .notifications::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🎯 Control de Carrusel</h1>
            <div class="subtitle">
                <span class="status-indicator" id="statusIndicator"></span>
                Sistema de Control Industrial Multi-PLC v2.6.0
            </div>
        </div>
        
        <!-- Controles principales -->
        <div class="controls-grid">
            <!-- Columna izquierda: Controles -->
            <div class="control-section">
                <h3>⚙️ Controles</h3>
                
                <!-- Selector de máquina -->
                <div class="form-group">
                    <label for="machineSelect">🏭 Seleccionar Máquina:</label>
                    <select id="machineSelect">
                        <option value="">Cargando máquinas...</option>
                    </select>
                </div>
                
                <!-- Selector de cangilón -->
                <div class="form-group">
                    <label for="cangilonInput">🎯 Posición del Cangilón:</label>
                    <div class="spinbox-container">
                        <button class="spinbox-btn" onclick="changeCangilon(-1)">▼</button>
                        <input id="cangilonInput" class="spinbox-input" type="number" min="1" max="255" value="1" readonly>
                        <button class="spinbox-btn up" onclick="changeCangilon(1)">▲</button>
                        <span class="spinbox-range">(1-255)</span>
                    </div>
                </div>
                
                <!-- Botón Mover -->
                <button class="move-button" onclick="sendMoveCommand()">
                    🚀 MOVER
                </button>
            </div>
            
            <!-- Columna derecha: Notificaciones -->
            <div class="control-section">
                <h3>📢 Resultado de la Operación</h3>
                <div class="notifications" id="notifications">
                    <!-- Las notificaciones se agregan dinámicamente aquí -->
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            Industrias Pico S.A.S | IA Punto: Soluciones Tecnológicas | 2025
        </div>
    </div>

    <script>
        let machines = [];
        let lastCommandTime = 0;
        const COMMAND_COOLDOWN = 3000; // 3 segundos en milisegundos
        
        // Cargar configuración inicial
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                machines = config.machines || [];
                updateMachineSelector();
                updateStatusIndicator(true);
                addNotification('Sistema listo. Seleccione una máquina y posición para mover el carrusel.', 'info');
                
            } catch (error) {
                console.error('Error cargando configuración:', error);
                updateStatusIndicator(false);
                addNotification('Error conectando con el servidor', 'error');
            }
        }
        
        function updateMachineSelector() {
            const select = document.getElementById('machineSelect');
            select.innerHTML = '';
            
            if (machines.length === 0) {
                select.innerHTML = '<option value="">No hay máquinas configuradas</option>';
                return;
            }
            
            // Agregar opción por defecto
            select.innerHTML = '<option value="">Seleccione una máquina...</option>';
            
            // Agregar máquinas
            machines.forEach(machine => {
                const option = document.createElement('option');
                option.value = machine.id;
                const machineType = machine.simulator ? 'Simulador' : 'Real';
                option.textContent = `${machine.name} (${machine.id}) - ${machineType}`;
                select.appendChild(option);
            });
            
            // Seleccionar la primera máquina por defecto
            if (machines.length > 0) {
                select.value = machines[0].id;
            }
        }
        
        function updateStatusIndicator(connected) {
            const indicator = document.getElementById('statusIndicator');
            indicator.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
        }
        
        function changeCangilon(delta) {
            const input = document.getElementById('cangilonInput');
            let value = parseInt(input.value) || 1;
            value += delta;
            
            if (value < 1) value = 1;
            if (value > 255) value = 255;
            
            input.value = value;
        }
        
        function addNotification(message, type = 'info') {
            const notifications = document.getElementById('notifications');
            const now = new Date();
            const timeStr = now.toLocaleTimeString();
            
            const icons = {
                'info': 'ℹ️',
                'success': '✅',
                'error': '❌',
                'warning': '⚠️'
            };
            
            const notification = document.createElement('div');
            notification.className = `notification-item ${type}`;
            notification.innerHTML = `
                <div class="notification-time">[${timeStr}]</div>
                <div class="notification-message">${icons[type]} ${message}</div>
            `;
            
            notifications.appendChild(notification);
            notifications.scrollTop = notifications.scrollHeight;
            
            // Limitar a 50 notificaciones
            while (notifications.children.length > 50) {
                notifications.removeChild(notifications.firstChild);
            }
        }
        
        async function sendMoveCommand() {
            const machineSelect = document.getElementById('machineSelect');
            const cangilonInput = document.getElementById('cangilonInput');
            
            const machineId = machineSelect.value;
            const position = parseInt(cangilonInput.value);
            
            // Validaciones
            if (!machineId) {
                addNotification('Por favor seleccione una máquina', 'warning');
                return;
            }
            
            if (isNaN(position) || position < 1 || position > 255) {
                addNotification('Posición de cangilón inválida (1-255)', 'error');
                return;
            }
            
            // Control de throttling
            const now = Date.now();
            if (now - lastCommandTime < COMMAND_COOLDOWN) {
                const remaining = Math.ceil((COMMAND_COOLDOWN - (now - lastCommandTime)) / 1000);
                addNotification(`Espere ${remaining} segundos antes de enviar otro comando`, 'warning');
                return;
            }
            
            lastCommandTime = now;
            
            // Encontrar información de la máquina
            const machine = machines.find(m => m.id === machineId);
            const machineName = machine ? machine.name : machineId;
            
            addNotification(`Enviando comando a ${machineName}...`, 'info');
            addNotification(`Moviendo carrusel a posición ${position}`, 'info');
            
            try {
                const response = await fetch('/api/move', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        machine_id: machineId,
                        position: position
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    addNotification(`Comando enviado exitosamente a ${machineName}`, 'success');
                } else {
                    addNotification(`Error: ${result.error || 'Error desconocido'}`, 'error');
                }
                
            } catch (error) {
                console.error('Error enviando comando:', error);
                addNotification('Error de conexión con el servidor', 'error');
            }
        }
        
        // Permitir envío con Enter
        document.getElementById('cangilonInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMoveCommand();
            }
        });
        
        // Cargar configuración al iniciar
        document.addEventListener('DOMContentLoaded', loadConfig);
        
        // Recargar configuración cada 30 segundos
        setInterval(loadConfig, 30000);
    </script>
</body>
</html>
'''

last_command_time = 0
COMMAND_COOLDOWN = 3  # segundos


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/config")
def get_config():
    """Endpoint para obtener la configuración actual (máquinas disponibles)."""
    try:
        api_port, machines, is_multi_plc = get_api_config()
        return jsonify({
            "success": True,
            "machines": machines,
            "api_port": api_port,
            "is_multi_plc": is_multi_plc
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "machines": []
        }), 500


@app.route("/api/move", methods=["POST"])
def move():
    """Endpoint para enviar comandos de movimiento (compatible con multi-PLC y single-PLC)."""
    global last_command_time

    try:
        data = request.get_json()
        machine_id = data.get("machine_id")
        position = data.get("position")

        # Validaciones básicas
        if not machine_id:
            return jsonify(success=False, error="ID de máquina requerido"), 400

        if not isinstance(position, int) or position < 1 or position > 255:
            return jsonify(success=False, error="Posición debe estar entre 1 y 255"), 400

        # Control de throttling
        now = time.time()
        if now - last_command_time < COMMAND_COOLDOWN:
            remaining = COMMAND_COOLDOWN - (now - last_command_time)
            return jsonify(success=False, error=f"Espere {remaining:.1f} segundos entre comandos"), 429

        last_command_time = now

        # Obtener configuración de API
        api_port, machines, is_multi_plc = get_api_config()

        # Construir URL y payload según el tipo de configuración
        if is_multi_plc and len(machines) > 1:
            # Modo Multi-PLC
            api_url = f"http://localhost:{api_port}/v1/machines/{machine_id}/command"
            payload = {
                "command": 1,  # Comando de movimiento
                "argument": position
            }
        else:
            # Modo Single-PLC (legacy)
            api_url = f"http://localhost:{api_port}/v1/command"
            payload = {
                "command": 1,
                "argument": position
            }

        # Enviar comando con reintentos
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(api_url, json=payload, timeout=5)

                if response.status_code == 200:
                    response_data = response.json()
                    # Algunos endpoints no devuelven 'success'
                    if response_data.get('success', True):
                        return jsonify(success=True, message="Comando enviado correctamente")
                    else:
                        error_msg = response_data.get(
                            'error', 'Error en la respuesta de la API')
                        if attempt < max_retries:
                            time.sleep(1)
                            continue
                        return jsonify(success=False, error=error_msg)
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get(
                            'error', f'Error HTTP {response.status_code}')
                    except:
                        error_msg = f'Error HTTP {response.status_code}'

                    if attempt < max_retries:
                        time.sleep(1)
                        continue
                    return jsonify(success=False, error=f"Error tras {max_retries} intentos: {error_msg}")

            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return jsonify(success=False, error=f"Timeout tras {max_retries} intentos")

            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return jsonify(success=False, error="Error de conexión: API no disponible")

            except Exception as e:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                return jsonify(success=False, error=f"Error inesperado: {str(e)}")

    except Exception as e:
        return jsonify(success=False, error=f"Error procesando solicitud: {str(e)}"), 500


if __name__ == "__main__":
    print("=" * 60)
    print("🌐 APLICACIÓN WEB - Control Remoto Carrusel v2.6.0")
    print("=" * 60)

    # Mostrar información de configuración
    api_port, machines, is_multi_plc = get_api_config()

    print(f"📋 Configuración detectada:")
    print(f"   • Modo: {'Multi-PLC' if is_multi_plc else 'Single-PLC'}")
    print(f"   • Puerto API: {api_port}")
    print(f"   • Máquinas configuradas: {len(machines)}")

    if machines:
        print(f"📋 Máquinas disponibles:")
        for machine in machines:
            machine_type = "Simulador" if machine.get(
                "simulator", False) else "Real"
            print(
                f"   • {machine['name']} ({machine['id']}) - {machine['ip']}:{machine['port']} [{machine_type}]")

    print(f"\n🚀 Servidor web iniciando en:")
    print(f"   • URL: http://localhost:8181")
    print(f"   • URL externa: http://0.0.0.0:8181")
    print("=" * 60)

    app.run(host="0.0.0.0", port=8181, debug=False)
