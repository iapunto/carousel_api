"""
Controlador para el carrusel vertical de almacenamiento.

Orquesta la comunicación entre la API y el PLC (real o simulado), interpretando estados y gestionando comandos de alto nivel.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha de creación: 2023-09-13
Última modificación: 2024-09-27
"""

from models.plc import PLC  # Importación explícita del PLC real [[2]]
from models.modbus_delta import read_real_position, read_target_position
from plc_cache import read_last_position, write_last_position, read_cached_status
# Interpretación de estados [[3]]
from commons.utils import interpretar_estado_plc, validar_comando, validar_argumento
import time
import logging
import os
from logging.handlers import RotatingFileHandler

# Configuración de bitácora de operaciones
operations_logger = logging.getLogger("operations")
if not operations_logger.hasHandlers():
    log_folder = os.path.join(
        os.getenv('LOCALAPPDATA'), 'Vertical PIC', 'logs')
    os.makedirs(log_folder, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_folder, "operations.log"), maxBytes=500_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    operations_logger.addHandler(handler)
    operations_logger.setLevel(logging.INFO)


class CarouselController:
    """
    Controlador para operaciones del carrusel con el PLC.
    """

    def __init__(self, plc: PLC):
        """
        Inicializa el controlador con una instancia de PLC.

        Args:
            plc: Instancia de la clase PLC (real o simulador) [[2]]
        """
        self.plc = plc
        self.logger = logging.getLogger(__name__)
        # Tiempo de espera para la respuesta del PLC. El poller WS
        # actualiza posición real cada ~1s mientras se mueve, así que
        # el comando no necesita bloquear esperando el fin de carrera.
        self.response_delay = float(os.getenv("PLC_RESPONSE_DELAY", "1.0"))
        self.move_ack_delay = float(os.getenv("PLC_MOVE_ACK_DELAY", "1.0"))
        # ID de máquina (lo asigna PLCManager) para persistir posición
        # comandada en la caché compartida
        self.machine_id = None
        self._last_move_position = None
        # Consulta de estado extra tras el ACK de movimiento (informativa;
        # el poller WS reporta la posición real en vivo). Off por defecto:
        # ahorra ~1.5 s de bloqueo por comando.
        self.move_status_after = os.getenv("PLC_MOVE_STATUS_AFTER", "0") in ("1", "true", "yes")

    def send_command(self, command: int, argument: int = None, remote_addr=None,
                     skip_position_check: bool = False,
                     include_position: bool = True) -> dict:
        """
        Envía un comando al PLC y registra en la bitácora de operaciones.

        Args:
            command: Código de comando (0-255)
            argument: Argumento opcional (0-255)
            remote_addr: Dirección IP o proceso remoto
            skip_position_check: Saltar la guardia "ya está en posición"
                (para cuando el contador del PLC no coincide con la
                posición física real — uso de técnico con force=true)

        Returns:
            Diccionario con estado y posición

        Raises:
            ValueError: Parámetros inválidos
            RuntimeError: Error de comunicación
        """
        validar_comando(command)
        if argument is not None:
            validar_argumento(argument)
        if command == 1 and (argument is None or argument < 1):
            raise ValueError(
                "Comando de movimiento requiere posición 1-255 (1-indexada)")
        try:
            with self.plc:  # Gestión automática de conexión [[2]]
                # Comando 1 (mover) es 1-indexado en la API, 0-indexado en el PLC
                plc_argument = argument - 1 if command == 1 and argument is not None else argument
                if command == 1 and skip_position_check:
                    self.logger.warning(
                        "[PLC] Guardia de posición omitida por force=true")
                if command == 1 and not skip_position_check:
                    # Guardia anti-loop: si la máquina ya está FÍSICAMENTE
                    # en la posición objetivo, no enviar el comando — el
                    # programa del PLC puede girar en loop buscando una
                    # marca ya pasada. La posición real se lee por Modbus
                    # (D0); el byte del protocolo :3200 siempre devuelve 0
                    # y NO es confiable. Respaldo: última posición comandada.
                    real_idx = self._real_position_index_cached()
                    last_cmd = self._remembered_position()
                    already = (
                        (real_idx is not None and real_idx == plc_argument) or
                        (real_idx is None and last_cmd == argument)
                    )
                    if already:
                        self.logger.info(
                            f"[PLC] Ya está físicamente en la posición {argument} "
                            f"(fuente: {'modbus' if real_idx is not None else 'tracking'}) "
                            f"— comando de movimiento omitido")
                        try:
                            self.plc.send_command(0)
                            time.sleep(0.5)
                            current = self.plc.receive_response()
                            return {
                                'status': interpretar_estado_plc(
                                    current['status_code']),
                                'position': argument,
                                'raw_status': current['status_code'],
                                'skipped': True,
                                'position_source': 'tracking'
                            }
                        except Exception:
                            return {
                                'status': {},
                                'position': argument,
                                'raw_status': None,
                                'skipped': True,
                                'position_source': 'tracking'
                            }
                self.logger.info(
                    f"[PLC] Enviando comando: {command}, argumento: {argument} (PLC: {plc_argument})")
                self.plc.send_command(command, plc_argument)
                if command == 1:
                    self._remember_position(argument)
                # Pausa para dar tiempo al PLC a procesar el comando antes de responder
                time.sleep(self.response_delay)
                response = self.plc.receive_response()
                # Si es comando de movimiento, el PLC responde con un ACK (21)
                # Necesitamos esperar a que termine el movimiento y consultar el estado real
                if command == 1:
                    # Solo esperar el ACK/arranque del movimiento; el
                    # poller WS reporta la posición real en vivo (~1s).
                    self.logger.info("[PLC] Comando de movimiento: esperando ACK...")
                    time.sleep(self.move_ack_delay)
                    if self.move_status_after:
                        try:
                            self.plc.send_command(0)  # Comando STATUS
                            time.sleep(0.5)
                            final_response = self.plc.receive_response()
                            self.logger.info(
                                f"[PLC] Estado final después de movimiento: {final_response}")
                            response = final_response
                        except Exception as e:
                            self.logger.warning(f"[PLC] No se pudo consultar estado final: {e}")
            # Log de bajo nivel: datos crudos recibidos
            status_code = response['status_code']
            position = response['position']
            # Formato binario de 8 bits
            status_bin = format(status_code, '08b')
            # Diccionario bit a bit
            status_bits = {f'bit_{i}': (
                status_code >> i) & 1 for i in range(7, -1, -1)}
            self.logger.info(
                f"[PLC][RAW] status_code: {status_code} (bin: {status_bin}), bits: {status_bits}, position: {position}")
            self.logger.info(f"[PLC][RAW] Respuesta cruda: {response}")
            status = interpretar_estado_plc(response['status_code'])
            self.logger.info(
                f"[PLC] Respuesta recibida: status_code={response['status_code']}, position={response['position']}")
            operations_logger.info(
                f"[COMANDO] IP/Proceso: {remote_addr} | Comando: {command} | Argumento: {argument} | Resultado: OK")
            result = {
                'status': status,
                'position': response['position'] + 1,
                'position_source': 'plc_byte',
                'target_position': None,
                'position_desync': False,
                'raw_status': response['status_code'],
            }
            if include_position:
                # Comando de movimiento: la posición "real" cambiará en
                # segundos — la caché del poller es tan buena como una
                # lectura viva aquí. Status (cmd 0): lectura viva, porque
                # es lo que el poller guarda para los demás.
                self.enrich_position(result, live=(command == 0))
            return result
        except Exception as e:
            self.logger.error(
                f"[PLC] Error en send_command (comando={command}, argumento={argument}): {str(e)}")
            operations_logger.error(
                f"[COMANDO] IP/Proceso: {remote_addr} | Comando: {command} | Argumento: {argument} | Resultado: ERROR | Error: {str(e)}")
            raise RuntimeError(f"Fallo en comunicación PLC: {str(e)}")

    def _real_position_index(self):
        """Posición física real (0-indexada) por Modbus D0. None si falla."""
        try:
            return read_real_position(self.plc.ip, timeout=2.0)
        except Exception as e:
            self.logger.warning(f"[MODBUS] No se pudo leer posición real: {e}")
            return None

    def enrich_position(self, result: dict, live: bool = True):
        """Agrega posición real (Modbus D0), target (D2) y desync a una
        respuesta ya construida. Modbus va por :502 — socket distinto al
        protocolo :3200 — así que puede llamarse fuera del lock del PLC.
        `live=False` usa la caché del poller (comandos de movimiento:
        la posición real está cambiando de todas formas)."""
        real_idx = (self._real_position_index() if live
                    else self._real_position_index_cached())
        target_idx = (read_target_position(self.plc.ip)
                      if real_idx is not None else None)
        desync = (
            target_idx is not None and real_idx is not None
            and target_idx != real_idx)
        if desync:
            self.logger.warning(
                f"[PLC] DESYNC posición: target(D2)={target_idx + 1} "
                f"pero física(D0)={real_idx + 1}")
        if real_idx is not None:
            result['position'] = real_idx + 1
            result['position_source'] = 'modbus'
        result['target_position'] = (
            target_idx + 1) if target_idx is not None else None
        result['position_desync'] = desync
        return result

    def _real_position_index_cached(self, max_age=4.0):
        """Posición física (0-indexada) preferida desde la caché del
        poller WS (se refresca cada ~1-3 s); si no hay dato fresco,
        lectura Modbus viva. Ahorra un roundtrip por comando."""
        if self.machine_id:
            try:
                cached = read_cached_status(self.machine_id, max_age=max_age)
            except Exception:
                cached = None
            if cached:
                pos = cached.get("position")
                if isinstance(pos, int) and pos >= 1:
                    return pos - 1
        return self._real_position_index()

    def _remembered_position(self):
        """Última posición comandada (1-indexada): memoria + caché compartida."""
        if self._last_move_position is None and self.machine_id:
            self._last_move_position = read_last_position(self.machine_id)
        return self._last_move_position

    def _remember_position(self, position):
        """Persiste la última posición comandada (1-indexada)."""
        self._last_move_position = position
        if self.machine_id:
            write_last_position(self.machine_id, position)

    def get_current_status(self, include_position: bool = True) -> dict:
        """
        Obtiene el estado actual del PLC sin enviar comandos.

        Returns:
            Diccionario con estado y posición
        """
        return self.send_command(0, include_position=include_position)

    def move_to_position(self, target: int, skip_position_check: bool = False) -> dict:
        """
        Mueve el carrusel a una posición específica.

        Args:
            target: Posición objetivo (1-indexada, 1 = primer cangilón)
            skip_position_check: Omitir guardia de misma posición (force)

        Returns:
            Respuesta del PLC
        """
        if not (1 <= target <= 255):
            raise ValueError("Posición debe estar entre 1 y 255")

        # send_command ya hace la conversión a 0-indexado internamente;
        # pasar el target tal cual (era target-1 = doble decremento)
        return self.send_command(1, target,
                                 skip_position_check=skip_position_check)

    def verify_ready_state(self) -> bool:
        """
        Verifica si el PLC está listo para operar.

        Returns:
            True si el PLC está en estado READY
        """
        status = self.get_current_status()['status']
        return status.get('READY', '') == 'El equipo está listo para operar'
