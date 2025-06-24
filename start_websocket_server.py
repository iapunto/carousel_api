#!/usr/bin/env python3
"""
Script para iniciar el servidor WebSocket independiente.

Uso:
    python start_websocket_server.py [--host HOST] [--port PORT]

Ejemplo:
    python start_websocket_server.py --host 0.0.0.0 --port 8765

Autor: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas
Fecha: 2025-03-13
"""

from websocket_server import run_websocket_server
import argparse
import logging
import sys
import os

# Añadir el directorio base al path para imports
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Servidor WebSocket para sistemas WMS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python start_websocket_server.py
  python start_websocket_server.py --host 192.168.1.100 --port 8765
  python start_websocket_server.py --port 9000

El servidor se conectará automáticamente a los PLCs configurados en:
- config_multi_plc.json (modo multi-PLC)
- config.json (modo single-PLC como fallback)
        """
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Dirección IP del servidor WebSocket (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Puerto del servidor WebSocket (default: 8765)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging (default: INFO)"
    )

    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("websocket_server.log"),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 50)
        logger.info("🚀 Iniciando Servidor WebSocket para WMS")
        logger.info("=" * 50)
        logger.info(f"Host: {args.host}")
        logger.info(f"Puerto: {args.port}")
        logger.info(f"Nivel de log: {args.log_level}")
        logger.info("-" * 50)

        # Verificar configuración
        if os.path.exists("config_multi_plc.json"):
            logger.info("✅ Configuración multi-PLC encontrada")
        elif os.path.exists("config.json"):
            logger.info("✅ Configuración single-PLC encontrada (fallback)")
        else:
            logger.error("❌ No se encontró archivo de configuración")
            logger.error(
                "   Asegúrese de que existe 'config_multi_plc.json' o 'config.json'")
            sys.exit(1)

        logger.info("🔌 Iniciando servidor WebSocket...")
        logger.info("   Presione Ctrl+C para detener el servidor")
        logger.info("-" * 50)

        # Iniciar servidor
        run_websocket_server(args.host, args.port)

    except KeyboardInterrupt:
        logger.info("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 Servidor WebSocket finalizado")


if __name__ == "__main__":
    main()
