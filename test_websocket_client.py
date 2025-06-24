#!/usr/bin/env python3
"""
Cliente WebSocket simple para probar la conexión al servidor.
"""

import asyncio
import websockets
import json
import sys


async def test_websocket_connection():
    """Prueba la conexión WebSocket."""
    uri = "ws://localhost:8765"

    try:
        print(f"Conectando a {uri}...")

        async with websockets.connect(uri) as websocket:
            print("✓ Conexión WebSocket establecida")

            # Esperar mensaje de bienvenida
            welcome_msg = await websocket.recv()
            welcome_data = json.loads(welcome_msg)

            print(f"✓ Mensaje de bienvenida recibido:")
            print(f"  - Modo: {welcome_data.get('mode')}")
            print(
                f"  - Versión: {welcome_data.get('server_info', {}).get('version')}")

            if welcome_data.get('machines'):
                print(
                    f"  - Máquinas disponibles: {len(welcome_data['machines'])}")
                for machine in welcome_data['machines']:
                    print(f"    * {machine['id']}: {machine['name']}")

            # Enviar ping
            ping_msg = {
                "type": "ping",
                "timestamp": "2025-06-24T18:00:00.000Z"
            }

            await websocket.send(json.dumps(ping_msg))
            print("✓ Ping enviado")

            # Esperar pong
            pong_msg = await websocket.recv()
            pong_data = json.loads(pong_msg)

            if pong_data.get("type") == "pong":
                print("✓ Pong recibido")

            # Solicitar estado
            status_msg = {
                "type": "get_status",
                "timestamp": "2025-06-24T18:00:00.000Z"
            }

            await websocket.send(json.dumps(status_msg))
            print("✓ Solicitud de estado enviada")

            # Esperar respuesta de estado
            status_response = await websocket.recv()
            status_data = json.loads(status_response)

            print(f"✓ Respuesta de estado recibida:")
            print(f"  - Tipo: {status_data.get('type')}")

            print("\n✓ Todas las pruebas pasaron exitosamente!")

    except ConnectionRefusedError:
        print("✗ Error: No se pudo conectar al servidor WebSocket")
        print("  Asegúrese de que el servidor esté ejecutándose en ws://localhost:8765")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

    return True

if __name__ == "__main__":
    print("=== Prueba de Cliente WebSocket ===")
    success = asyncio.run(test_websocket_connection())

    if success:
        print("\n🎉 Servidor WebSocket funcionando correctamente!")
        sys.exit(0)
    else:
        print("\n❌ Problemas con el servidor WebSocket")
        sys.exit(1)
