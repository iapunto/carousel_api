from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://localhost:5001/v1/command"  # Cambia el puerto si es necesario

HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control Remoto Carrusel</title>
    <style>
        body { background: #222; color: #fff; font-family: Arial, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { background: #333; padding: 2em; border-radius: 16px; box-shadow: 0 0 16px #0008; display: flex; flex-direction: column; align-items: center; }
        .input-group { display: flex; align-items: center; margin-bottom: 1em; }
        input[type=number] { font-size: 2.5em; width: 2.5em; text-align: center; border-radius: 8px; border: none; margin: 0 1em; background: #222; color: #fff; }
        button { font-size: 2em; padding: 0.3em 0.7em; margin: 0 0.5em; border-radius: 8px; border: none; background: #007bff; color: #fff; cursor: pointer; transition: background 0.2s; }
        button:active { background: #0056b3; }
        #send-btn { font-size: 1.5em; margin-top: 1em; background: #28a745; }
        #send-btn:active { background: #1e7e34; }
        #feedback { margin-top: 1em; font-size: 1.2em; min-height: 2em; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Control Remoto Carrusel</h2>
        <div class="input-group">
            <button onclick="changeValue(-1)">&#8593;</button>
            <input id="posInput" type="number" min="1" max="6" value="1">
            <button onclick="changeValue(1)">&#8595;</button>
        </div>
        <div style="margin-bottom:1em; font-size:1.1em;">Cangilón seleccionado: <span id="cangilonLabel">1</span></div>
        <button id="send-btn" onclick="sendCommand()">Mover</button>
        <div id="feedback"></div>
    </div>
    <script>
        function changeValue(delta) {
            let input = document.getElementById('posInput');
            let val = parseInt(input.value) || 1;
            val += delta;
            if (val < 1) val = 1;
            if (val > 6) val = 6;
            input.value = val;
            document.getElementById('cangilonLabel').textContent = val;
        }
        document.getElementById('posInput').addEventListener('input', function() {
            let val = parseInt(this.value) || 1;
            if (val < 1) val = 1;
            if (val > 6) val = 6;
            this.value = val;
            document.getElementById('cangilonLabel').textContent = val;
        });
        function sendCommand() {
            let pos = parseInt(document.getElementById('posInput').value);
            if (isNaN(pos) || pos < 1 || pos > 6) {
                showFeedback('Cangilón inválido', true);
                return;
            }
            // Restar 1 para enviar a la API (0-5)
            let apiPos = pos - 1;
            fetch('/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ position: apiPos })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showFeedback('Comando enviado correctamente', false);
                } else {
                    showFeedback('Error: ' + (data.error || 'Desconocido'), true);
                }
            })
            .catch(() => showFeedback('Error de red', true));
        }
        function showFeedback(msg, isError) {
            let fb = document.getElementById('feedback');
            fb.textContent = msg;
            fb.style.color = isError ? '#ff5555' : '#00ff88';
        }
    </script>
</body>
</html>
'''


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    pos = data.get("position")
    try:
        # Enviar comando 1 (mover) a la API REST
        resp = requests.post(
            API_URL, json={"command": 1, "argument": pos}, timeout=3)
        if resp.status_code == 200:
            return jsonify(success=True)
        else:
            return jsonify(success=False, error=resp.json().get('error', 'Error API'))
    except Exception as e:
        return jsonify(success=False, error=str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8181, debug=True)
