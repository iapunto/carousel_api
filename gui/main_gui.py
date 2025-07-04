"""
Interfaz gráfica principal para control de carrusel industrial

Proyecto: Sistema de Control de Carrusel Industrial
Cliente: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas

Creado: 2024-09-27
Última modificación: 2025-06-24

Uso de CustomTkinter para mejorar el aspecto visual.
Sistema Multi-PLC con Dashboard de Cards y Panel de Comandos optimizado.
"""

import json as jsonlib
import websocket
import time
from controllers.command_handler import CommandHandler
import os
import sys
import customtkinter as ctk  # Importar CustomTkinter
from tkinter import messagebox, simpledialog
import json
import threading
from PIL import Image, ImageTk  # Para manejar imágenes del ícono
import pystray  # Para manejar el área de notificaciones
from commons.utils import interpretar_estado_plc, debug_print
import socketio
import requests
from gui.config_window import show_config_window

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "ip": "192.168.1.50",
    "port": 3200,
    "simulator_enabled": False
}

# Configurar el tema visual de CustomTkinter
ctk.set_appearance_mode("dark")  # Modo oscuro
ctk.set_default_color_theme("dark-blue")  # Tema azul


def resource_path(relative_path):
    """
        Obtiene la ruta absoluta de un recurso, compatible con PyInstaller.
        """
    try:
        # PyInstaller crea una carpeta temporal y almacena los recursos allí
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow:

    def __init__(self, root, plc, config):
        """
        Constructor de la ventana principal.

        Args:
            root: Instancia de CTk()
            plc: Instancia de PLC (real o simulador)
            config: Diccionario con configuración (IP/puerto)
        """

        self.command_handler = CommandHandler()

        self.root = root
        self.plc = plc
        self.config = config

        # Importar versión
        try:
            from __version__ import __version__
            version_str = f" v{__version__}"
        except ImportError:
            version_str = ""

        self.root.title(f"Vertical PIC - Control de Carrusel{version_str}")
        # Configurar el ícono
        icon_path = resource_path("assets/favicon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            print(f"No se encontró el archivo de ícono: {icon_path}")

        self.root.geometry("800x625")

        # Variables de control (mantenemos solo las necesarias)
        self.dev_mode_var = ctk.BooleanVar(value=config.get(
            "simulator_enabled", False))  # Estado del modo desarrollo (legacy)

        # Variables de control para comandos
        self.selected_machine_var = ctk.StringVar()
        self.cangilon_var = ctk.IntVar(value=1)
        self.command_result_var = ctk.StringVar(value="")

        # Variables legacy (mantener compatibilidad)
        self.command_var = ctk.StringVar(value="1")
        self.argument_var = ctk.StringVar(value="3")

        self.first_status_received = False

        # Crear el header
        self.create_header()

        # Crear pestañas
        self.create_tabs()

        # Mostrar información inicial y solicitar estado inmediatamente
        self.show_initial_machine_info()
        self.request_initial_status()

        # Configurar minimización al área de notificaciones
        self.tray_icon = None
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        self.sio = None
        self.sio_thread = None
        self._stop_sio = False
        self.ws_connected = False
        self.connection_indicator = None
        self.connection_label = None
        self.start_socketio_listener()

        self.error_popup_open = False  # Bandera para evitar popups en bucle

        # Configurar watcher para detectar cambios en configuración
        self.config_file_mtime = None
        self.setup_config_watcher()

    def create_header(self):
        """Crea la cabecera con el logo y el botón de salir."""
        header_frame = ctk.CTkFrame(
            self.root, height=180, bg_color="white", corner_radius=0)
        header_frame.pack(fill="x", side="top")

        # Cargar el logo
        logo_path = resource_path("assets/logo.png")
        if os.path.exists(logo_path):
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize(
                (90, 40), Image.LANCZOS)  # Redimensionar el logo
            logo_tk = ImageTk.PhotoImage(logo_image)
            logo_label = ctk.CTkLabel(
                header_frame, image=logo_tk, text="")
            logo_label.image = logo_tk  # Mantener una referencia para evitar que se elimine
            logo_label.pack(side="left", padx=30, pady=10)
        else:
            print(f"No se encontró el archivo de logo: {logo_path}")

        # Botón de salir
        exit_button = ctk.CTkButton(
            header_frame, text="Salir", command=self.exit_app, fg_color="red", hover_color="darkred", width=80)
        exit_button.pack(side="right", padx=30)

        self.create_connection_indicator()

    def create_connection_indicator(self):
        """
        Crea un indicador visual de conexión WebSocket en la cabecera.
        """
        if not hasattr(self, 'root') or not hasattr(self, 'connection_indicator'):
            return
        # Buscar el header_frame
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                header_frame = widget
                break
        else:
            return
        # Indicador (círculo)
        self.connection_indicator = ctk.CTkCanvas(
            header_frame, width=18, height=18, bg="white", highlightthickness=0)
        self.connection_indicator.place(x=10, y=10)
        self._draw_connection_circle("red")
        # Etiqueta
        self.connection_label = ctk.CTkLabel(
            header_frame, text="Desconectado", text_color="red", font=("Arial", 10, "bold"), bg_color="white")
        self.connection_label.place(x=32, y=8)

    def _draw_connection_circle(self, color):
        if self.connection_indicator:
            self.connection_indicator.delete("all")
            self.connection_indicator.create_oval(
                2, 2, 16, 16, fill=color, outline=color)

    def set_ws_status(self, connected):
        """
        Actualiza el indicador visual y la etiqueta de conexión.
        """
        self.ws_connected = connected
        if connected:
            self._draw_connection_circle("green")
            if self.connection_label:
                self.connection_label.configure(
                    text="Conectado", text_color="green")
        else:
            self._draw_connection_circle("red")
            if self.connection_label:
                self.connection_label.configure(
                    text="Desconectado", text_color="red")

    def send_test_command(self):
        """Envía un comando al PLC para pruebas usando la API REST"""
        if not self.command_handler.can_send_command():
            messagebox.showwarning(
                "Bloqueado", "Espera 3 segundos antes de enviar otro comando.")
            return
        try:
            # Verificar si el PLC está inicializado
            if self.plc is None:
                messagebox.showerror(
                    "Error", "El PLC no está inicializado. Por favor, configure la conexión antes de enviar comandos.")
                return

            # Obtener valores del formulario
            command = int(self.command_var.get())
            argument = int(self.argument_var.get())
            # Validar los valores
            if not (0 <= command <= 255):
                messagebox.showerror(
                    "Error", "El comando debe estar entre 0 y 255.")
                return
            if not (0 <= argument <= 255):
                messagebox.showerror(
                    "Error", "El argumento debe estar entre 0 y 255.")
                return
            # Construir la URL de la API
            api_port = self.config.get('api_port', 5000)
            url = f"http://localhost:{api_port}/v1/command"
            payload = {"command": command, "argument": argument}
            try:
                response = requests.post(url, json=payload, timeout=5)
                if response.status_code == 200:
                    self.command_handler.send_command(command, argument)
                    messagebox.showinfo(
                        "Éxito", f"Comando {command} enviado con argumento {argument}.")
                else:
                    error_msg = response.json().get('error', 'Error desconocido')
                    messagebox.showerror(
                        "Error", f"No se pudo enviar el comando: {error_msg}")
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo enviar el comando: {str(e)}")
        except ValueError:
            messagebox.showerror(
                "Error", "Los valores deben ser números enteros.")

    def create_exit_button(self):
        """Crea un botón de salida en la interfaz"""
        exit_button = ctk.CTkButton(
            self.root, text="Salir", command=self.exit_app, fg_color="red", hover_color="darkred")
        exit_button.pack(side="bottom", pady=10)

    def minimize_to_tray(self):
        """Minimiza la ventana al área de notificaciones."""
        self.root.withdraw()  # Oculta la ventana principal

        # Crear un ícono para la bandeja del sistema
        # Reemplaza "icon.png" con tu ícono
        image = resource_path("assets/favicon.ico")
        icon = Image.open(image)
        menu = pystray.Menu(
            pystray.MenuItem('Restaurar', self.restore_window),
            pystray.MenuItem('Salir', self.exit_app)
        )
        self.tray_icon = pystray.Icon(
            "favicon", icon, "Vertical PIC", menu)
        self.tray_icon.run()

    def restore_window(self):
        """Restaura la ventana desde la bandeja del sistema."""
        if self.tray_icon:
            self.tray_icon.stop()  # Detiene el ícono de la bandeja
        self.root.deiconify()  # Muestra la ventana principal

    def exit_app(self):
        """Cierra la aplicación."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def create_tabs(self):
        """Crea las pestañas para la interfaz"""
        tab_view = ctk.CTkTabview(self.root, width=780, height=500)
        tab_view.pack(padx=10, pady=10)

        # Pestaña 1: Estado del PLC
        tab_estado = tab_view.add("Estado del PLC")
        self.create_estado_frame(tab_estado)

        # Pestaña 2: Enviar Comandos
        tab_comandos = tab_view.add("Enviar Comandos")
        self.create_command_frame(tab_comandos)

        # Pestaña 3: Configuración
        tab_config = tab_view.add("Configuración")
        self.create_config_frame(tab_config)

    def create_command_frame(self, parent):
        """Crea la pestaña para enviar comandos al PLC con interfaz mejorada en dos columnas."""
        # Frame principal
        main_frame = ctk.CTkFrame(parent, corner_radius=10)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Título
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎯 Control de Carrusel",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(20, 30))

        # Frame principal con dos columnas
        columns_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        columns_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # ========== COLUMNA IZQUIERDA: CONTROLES ==========
        controls_frame = ctk.CTkFrame(columns_frame, corner_radius=12)
        controls_frame.pack(side="left", padx=(
            0, 10), pady=0, fill="both", expand=True)

        # Título de controles
        ctk.CTkLabel(
            controls_frame,
            text="⚙️ Controles",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 15))

        # Selector de máquina
        machine_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        machine_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            machine_frame,
            text="🏭 Seleccionar Máquina:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # Cargar máquinas disponibles
        self.load_available_machines()

        self.machine_selector = ctk.CTkComboBox(
            machine_frame,
            variable=self.selected_machine_var,
            values=self.get_machine_options(),
            width=300,
            height=35,
            font=("Arial", 12),
            dropdown_font=("Arial", 11)
        )
        self.machine_selector.pack(fill="x", pady=(0, 10))

        # Selector de cangilón
        cangilon_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        cangilon_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            cangilon_frame,
            text="🎯 Posición del Cangilón:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # Frame para el spinbox con flechas
        spinbox_frame = ctk.CTkFrame(cangilon_frame, corner_radius=8)
        spinbox_frame.pack(fill="x")

        # Botón flecha abajo
        down_button = ctk.CTkButton(
            spinbox_frame,
            text="▼",
            width=50,
            height=35,
            command=self.decrease_cangilon,
            fg_color="#FF6B6B",
            hover_color="#FF5252"
        )
        down_button.pack(side="left", padx=10, pady=10)

        # Entry para mostrar el valor
        self.cangilon_entry = ctk.CTkEntry(
            spinbox_frame,
            textvariable=self.cangilon_var,
            width=80,
            height=35,
            font=("Arial", 14, "bold"),
            justify="center"
        )
        self.cangilon_entry.pack(side="left", padx=10, pady=10)

        # Botón flecha arriba
        up_button = ctk.CTkButton(
            spinbox_frame,
            text="▲",
            width=50,
            height=35,
            command=self.increase_cangilon,
            fg_color="#4CAF50",
            hover_color="#45A049"
        )
        up_button.pack(side="left", padx=10, pady=10)

        # Label informativo
        info_label = ctk.CTkLabel(
            spinbox_frame,
            text="(1-255)",
            font=("Arial", 10),
            text_color="#888888"
        )
        info_label.pack(side="left", padx=15, pady=10)

        # Botón Mover
        move_button = ctk.CTkButton(
            controls_frame,
            text="🚀 MOVER",
            command=self.send_move_command,
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        move_button.pack(pady=30, padx=20, fill="x")

        # ========== COLUMNA DERECHA: NOTIFICACIONES ==========
        notification_frame = ctk.CTkFrame(columns_frame, corner_radius=12)
        notification_frame.pack(side="right", padx=(
            10, 0), pady=0, fill="both", expand=True)

        # Título de notificaciones
        ctk.CTkLabel(
            notification_frame,
            text="📢 Resultado de la Operación",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 15))

        # Área de texto para notificaciones
        self.notification_text = ctk.CTkTextbox(
            notification_frame,
            height=200,
            font=("Arial", 11),
            wrap="word"
        )
        self.notification_text.pack(
            padx=20, pady=(0, 20), fill="both", expand=True)

        # Mensaje inicial
        self.add_notification(
            "Sistema listo. Seleccione una máquina y posición para mover el carrusel.", "info")

    def load_available_machines(self):
        """Carga la lista de máquinas disponibles desde la configuración."""
        self.available_machines = []
        try:
            if os.path.exists("config_multi_plc.json"):
                with open("config_multi_plc.json", "r", encoding="utf-8") as f:
                    multi_config = json.load(f)
                    machines = multi_config.get("plc_machines", [])
                    self.available_machines = machines
            else:
                # Fallback para configuración single-PLC
                single_machine = {
                    "id": "single_plc",
                    "name": "PLC Principal",
                    "ip": self.config.get("ip", "192.168.1.50"),
                    "port": self.config.get("port", 3200),
                    "simulator": self.config.get("simulator_enabled", False)
                }
                self.available_machines = [single_machine]
        except Exception as e:
            debug_print(f"Error cargando máquinas: {e}")
            self.available_machines = []

    def get_machine_options(self):
        """Obtiene las opciones del selector de máquinas."""
        if not self.available_machines:
            return ["No hay máquinas configuradas"]

        options = []
        for machine in self.available_machines:
            option = f"{machine['name']} ({machine['id']})"
            options.append(option)

        # Seleccionar la primera máquina por defecto
        if options and not self.selected_machine_var.get():
            self.selected_machine_var.set(options[0])

        return options

    def get_selected_machine_id(self):
        """Extrae el ID de la máquina seleccionada."""
        selected = self.selected_machine_var.get()
        if not selected or selected == "No hay máquinas configuradas":
            return None

        # Extraer el ID entre paréntesis
        import re
        match = re.search(r'\(([^)]+)\)$', selected)
        if match:
            return match.group(1)
        return None

    def increase_cangilon(self):
        """Incrementa el valor del cangilón."""
        current = self.cangilon_var.get()
        if current < 255:
            self.cangilon_var.set(current + 1)

    def decrease_cangilon(self):
        """Decrementa el valor del cangilón."""
        current = self.cangilon_var.get()
        if current > 1:
            self.cangilon_var.set(current - 1)

    def add_notification(self, message, msg_type="info"):
        """Agrega una notificación al área de resultados."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Emojis según el tipo
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }

        emoji = emoji_map.get(msg_type, "ℹ️")
        formatted_message = f"[{timestamp}] {emoji} {message}\n"

        # Agregar al textbox
        self.notification_text.insert("end", formatted_message)
        self.notification_text.see("end")  # Scroll al final

    def send_move_command(self):
        """Envía comando de movimiento al carrusel seleccionado."""
        if not self.command_handler.can_send_command():
            self.add_notification(
                "Espere 3 segundos antes de enviar otro comando.", "warning")
            return

        # Validar selección de máquina
        machine_id = self.get_selected_machine_id()
        if not machine_id:
            self.add_notification(
                "Por favor, seleccione una máquina válida.", "error")
            return

        # Obtener posición del cangilón
        cangilon_position = self.cangilon_var.get()

        # Validar rango
        if not (1 <= cangilon_position <= 255):
            self.add_notification(
                "La posición del cangilón debe estar entre 1 y 255.", "error")
            return

        try:
            # Obtener información de la máquina seleccionada
            selected_machine = None
            for machine in self.available_machines:
                if machine["id"] == machine_id:
                    selected_machine = machine
                    break

            if not selected_machine:
                self.add_notification(
                    f"No se encontró la máquina {machine_id}.", "error")
                return

            self.add_notification(
                f"Enviando comando a {selected_machine['name']}...", "info")
            self.add_notification(
                f"Moviendo carrusel a posición {cangilon_position}", "info")

            # Determinar el puerto de la API
            api_port = self._get_api_port()

            # Construir payload para comando
            if len(self.available_machines) > 1:  # Multi-PLC
                url = f"http://localhost:{api_port}/v1/machines/{machine_id}/command"
                payload = {
                    "command": 1,  # Comando de movimiento
                    "argument": cangilon_position
                }
            else:  # Single-PLC
                url = f"http://localhost:{api_port}/v1/command"
                payload = {
                    "command": 1,
                    "argument": cangilon_position
                }

            # Enviar comando via API REST
            import requests
            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                result = response.json()
                self.command_handler.send_command(1, cangilon_position)
                self.add_notification(
                    f"✅ Comando enviado exitosamente a {selected_machine['name']}", "success")
                self.add_notification(
                    f"Respuesta: {result.get('message', 'OK')}", "success")
            else:
                error_msg = response.json().get('error', 'Error desconocido')
                self.add_notification(
                    f"Error del servidor: {error_msg}", "error")

        except requests.exceptions.RequestException as e:
            self.add_notification(f"Error de conexión: {str(e)}", "error")
        except Exception as e:
            self.add_notification(f"Error inesperado: {str(e)}", "error")

    def create_estado_frame(self, parent):
        """Frame para mostrar el estado de múltiples PLCs con sistema de cards"""
        # Frame principal con scroll
        main_frame = ctk.CTkFrame(parent, corner_radius=10)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Título del dashboard
        title_label = ctk.CTkLabel(
            main_frame, text="Dashboard Multi-PLC", font=("Arial", 16, "bold"))
        title_label.pack(pady=(15, 10))

        # Frame scrollable para las cards
        self.scrollable_frame = ctk.CTkScrollableFrame(
            main_frame, corner_radius=8, height=400)
        self.scrollable_frame.pack(padx=15, pady=10, fill="both", expand=True)

        # Diccionario para almacenar las cards de máquinas
        self.machine_cards = {}

        # Cargar y crear cards para las máquinas configuradas
        self.load_and_create_machine_cards()

        # Mensaje de información si no hay máquinas
        if not self.machine_cards:
            self.show_no_machines_message()

    def load_and_create_machine_cards(self):
        """Carga la configuración de máquinas y crea las cards correspondientes"""
        try:
            # Intentar cargar configuración multi-PLC
            if os.path.exists("config_multi_plc.json"):
                with open("config_multi_plc.json", "r", encoding="utf-8") as f:
                    multi_config = json.load(f)
                    machines = multi_config.get("plc_machines", [])

                for machine in machines:
                    self.create_machine_card(machine)
            else:
                # Fallback: crear una card para configuración single-PLC
                single_machine = {
                    "id": "single_plc",
                    "name": "PLC Principal",
                    "ip": self.config.get("ip", "192.168.1.50"),
                    "port": self.config.get("port", 3200),
                    "simulator": self.config.get("simulator_enabled", False),
                    "description": "Configuración Single-PLC"
                }
                self.create_machine_card(single_machine)

        except Exception as e:
            debug_print(f"Error cargando configuración de máquinas: {e}")

    def create_machine_card(self, machine):
        """Crea una card individual para una máquina"""
        machine_id = machine["id"]

        # Frame principal de la card
        card_frame = ctk.CTkFrame(
            self.scrollable_frame, corner_radius=12, height=200)
        card_frame.pack(padx=10, pady=8, fill="x")
        card_frame.pack_propagate(False)  # Mantener altura fija

        # Header de la card con información de la máquina
        header_frame = ctk.CTkFrame(card_frame, corner_radius=8, height=60)
        header_frame.pack(padx=10, pady=(10, 5), fill="x")
        header_frame.pack_propagate(False)

        # Título y estado de conexión
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="both",
                         expand=True, padx=10, pady=10)

        machine_title = ctk.CTkLabel(
            title_frame,
            text=machine["name"],
            font=("Arial", 14, "bold"),
            anchor="w"
        )
        machine_title.pack(anchor="w")

        connection_info = ctk.CTkLabel(
            title_frame,
            text=f"ID: {machine_id} | {machine['ip']}:{machine['port']} | {'Simulador' if machine.get('simulator', False) else 'Real'}",
            font=("Arial", 10),
            text_color="#888888",
            anchor="w"
        )
        connection_info.pack(anchor="w")

        # Indicador de estado de conexión
        status_indicator = ctk.CTkFrame(
            header_frame, width=80, height=40, corner_radius=6)
        status_indicator.pack(side="right", padx=10, pady=10)
        status_indicator.pack_propagate(False)

        status_label = ctk.CTkLabel(
            status_indicator,
            text="Desconectado",
            font=("Arial", 10, "bold"),
            text_color="#FF3333"
        )
        status_label.pack(expand=True)

        # Frame para los datos de estado
        data_frame = ctk.CTkFrame(card_frame, corner_radius=8)
        data_frame.pack(padx=10, pady=5, fill="both", expand=True)

        # Grid para los estados principales
        status_grid = ctk.CTkFrame(data_frame, fg_color="transparent")
        status_grid.pack(padx=10, pady=10, fill="both", expand=True)

        # Crear labels para estados principales
        status_labels = {}
        main_statuses = ["READY", "RUN", "MODO_OPERACION", "ALARMA"]

        for i, status_key in enumerate(main_statuses):
            row = i // 2
            col = i % 2

            status_frame = ctk.CTkFrame(
                status_grid, corner_radius=6, height=25)
            status_frame.grid(row=row, column=col, padx=5, pady=2, sticky="ew")
            status_frame.pack_propagate(False)

            key_label = ctk.CTkLabel(
                status_frame,
                text=f"{status_key}:",
                font=("Arial", 9, "bold"),
                width=80
            )
            key_label.pack(side="left", padx=(8, 2), pady=5)

            value_label = ctk.CTkLabel(
                status_frame,
                text="---",
                font=("Arial", 9),
                text_color="#CCCCCC"
            )
            value_label.pack(side="left", padx=(2, 8), pady=5)

            status_labels[status_key] = value_label

        # Configurar grid weights
        status_grid.grid_columnconfigure(0, weight=1)
        status_grid.grid_columnconfigure(1, weight=1)

        # Frame para posición
        position_frame = ctk.CTkFrame(data_frame, corner_radius=6, height=30)
        position_frame.pack(padx=10, pady=(0, 10), fill="x")
        position_frame.pack_propagate(False)

        pos_label = ctk.CTkLabel(
            position_frame,
            text="POSICIÓN:",
            font=("Arial", 11, "bold")
        )
        pos_label.pack(side="left", padx=10, pady=8)

        position_value = ctk.CTkLabel(
            position_frame,
            text="---",
            font=("Arial", 11, "bold"),
            text_color="#00AAFF"
        )
        position_value.pack(side="right", padx=10, pady=8)

        # Almacenar referencias para actualización
        self.machine_cards[machine_id] = {
            "card_frame": card_frame,
            "status_indicator": status_label,
            "status_labels": status_labels,
            "position_label": position_value,
            "machine_info": machine
        }

    def show_no_machines_message(self):
        """Muestra mensaje cuando no hay máquinas configuradas"""
        message_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10)
        message_frame.pack(padx=20, pady=50, fill="x")

        ctk.CTkLabel(
            message_frame,
            text="⚠️ No hay máquinas configuradas",
            font=("Arial", 16, "bold"),
            text_color="#FF8800"
        ).pack(pady=20)

        ctk.CTkLabel(
            message_frame,
            text="Use el botón 'Configurar Máquinas' en la pestaña de configuración\npara añadir máquinas al sistema.",
            font=("Arial", 12),
            text_color="#888888"
        ).pack(pady=(0, 20))

    def show_waiting_message(self):
        """
        Muestra 'Esperando conexión...' en todas las cards de máquinas.
        """
        for machine_id, card_data in self.machine_cards.items():
            card_data["status_indicator"].configure(
                text="Conectando...", text_color="#FFA500")
            for label in card_data["status_labels"].values():
                label.configure(text="Esperando...", text_color="gray")
            card_data["position_label"].configure(
                text="---", text_color="gray")

    def show_initial_machine_info(self):
        """
        Muestra información básica de las máquinas inmediatamente sin esperar WebSocket.
        """
        for machine_id, card_data in self.machine_cards.items():
            machine_info = card_data["machine_info"]

            # Mostrar estado inicial basado en el tipo de máquina
            if machine_info.get("simulator", False):
                card_data["status_indicator"].configure(
                    text="Simulador", text_color="#00AAFF")
                # Mostrar valores predeterminados para simulador
                initial_states = {
                    "READY": "OK",
                    "RUN": "Detenido",
                    "MODO_OPERACION": "Automático",
                    "ALARMA": "Sin alarma"
                }
            else:
                card_data["status_indicator"].configure(
                    text="Conectando...", text_color="#FFA500")
                # Mostrar estado de conexión para máquinas reales
                initial_states = {
                    "READY": "Verificando...",
                    "RUN": "Verificando...",
                    "MODO_OPERACION": "Verificando...",
                    "ALARMA": "Verificando..."
                }

            # Actualizar labels con información inicial
            for key, value in initial_states.items():
                if key in card_data["status_labels"]:
                    color = self.get_status_color(value)
                    card_data["status_labels"][key].configure(
                        text=value, text_color=color)

            # Mostrar posición inicial
            if machine_info.get("simulator", False):
                card_data["position_label"].configure(
                    text="1", text_color="#00AAFF")
            else:
                card_data["position_label"].configure(
                    text="---", text_color="#FFA500")

    def request_initial_status(self):
        """
        Solicita el estado inicial de las máquinas vía HTTP para carga más rápida.
        """
        def fetch_status():
            try:
                api_port = self._get_api_port()
                import requests

                # Solicitar estado via HTTP (más rápido que WebSocket)
                if len(self.available_machines) > 1:  # Multi-PLC
                    # Solicitar estado de cada máquina individualmente
                    machines_status = {}
                    for machine in self.available_machines:
                        machine_id = machine["id"]
                        try:
                            url = f"http://localhost:{api_port}/v1/machines/{machine_id}/status"
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                machine_data = response.json()
                                if machine_data.get('success'):
                                    machines_status[machine_id] = machine_data['data']
                                else:
                                    machines_status[machine_id] = {
                                        'error': machine_data.get('error', 'Error desconocido')}
                            else:
                                machines_status[machine_id] = {
                                    'error': f'HTTP {response.status_code}'}
                        except Exception as e:
                            machines_status[machine_id] = {'error': str(e)}

                    # Actualizar GUI con datos multi-PLC
                    self.root.after(
                        0, self.update_multi_plc_status, machines_status)
                    debug_print(
                        f"✅ Estado inicial cargado vía HTTP: {len(machines_status)} máquinas")

                else:  # Single-PLC
                    url = f"http://localhost:{api_port}/v1/status"
                    response = requests.get(url, timeout=3)

                    if response.status_code == 200:
                        status_data = response.json()
                        # Formato single-PLC
                        if status_data.get('success'):
                            self.root.after(
                                0, self.update_single_plc_status, status_data.get('data', {}))
                        debug_print("✅ Estado inicial cargado vía HTTP")
                    else:
                        debug_print(
                            f"⚠️ Error HTTP {response.status_code}: usando WebSocket como fallback")

            except requests.exceptions.RequestException as e:
                debug_print(
                    f"⚠️ Error conexión HTTP: {e} - usando WebSocket como fallback")
            except Exception as e:
                debug_print(f"⚠️ Error obteniendo estado inicial: {e}")

        # Ejecutar en hilo separado para no bloquear la GUI
        import threading
        status_thread = threading.Thread(target=fetch_status, daemon=True)
        status_thread.start()

    def create_config_frame(self, parent):
        """Frame para configuración del sistema multi-PLC"""
        config_frame = ctk.CTkFrame(parent, corner_radius=10)
        config_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Título
        title_label = ctk.CTkLabel(
            config_frame, text="Configuración del Sistema", font=("Arial", 16, "bold"))
        title_label.pack(pady=(20, 30))

        # Información del sistema
        info_frame = ctk.CTkFrame(config_frame, corner_radius=8)
        info_frame.pack(padx=20, pady=10, fill="x")

        info_label = ctk.CTkLabel(
            info_frame,
            text="Sistema Multi-PLC\nConfiguración centralizada de máquinas",
            font=("Arial", 12),
            text_color="#888888"
        )
        info_label.pack(pady=15)

        # Botón principal para configurar máquinas
        ctk.CTkButton(
            config_frame,
            text="⚙️ Configurar Máquinas",
            command=self.open_machine_config,
            fg_color="#6f42c1",
            hover_color="#5a2d91",
            font=("Arial", 14, "bold"),
            height=50
        ).pack(pady=20, padx=20, fill="x")

        # Separador
        ctk.CTkLabel(config_frame, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                     text_color="gray").pack(pady=20)

        # Botones de servicios web
        web_frame = ctk.CTkFrame(config_frame, corner_radius=8)
        web_frame.pack(padx=20, pady=10, fill="x")

        ctk.CTkLabel(web_frame, text="Servicios Web", font=(
            "Arial", 12, "bold")).pack(pady=(10, 5))

        # Botón para desplegar la app web
        ctk.CTkButton(
            web_frame,
            text="🌐 Desplegar Control Web",
            command=self.launch_web_app,
            fg_color="#007bff",
            hover_color="#0056b3"
        ).pack(pady=5, padx=10, fill="x")

        # Frame para botones de servicio
        service_frame = ctk.CTkFrame(web_frame, fg_color="transparent")
        service_frame.pack(pady=5, padx=10, fill="x")

        # Botón para instalar el servicio de la App Web
        ctk.CTkButton(
            service_frame,
            text="📦 Instalar Servicio",
            command=self.install_webapp_service,
            fg_color="#28a745",
            hover_color="#1e7e34"
        ).pack(side="left", padx=(0, 5), fill="x", expand=True)

        # Botón para desinstalar el servicio de la App Web
        ctk.CTkButton(
            service_frame,
            text="🗑️ Desinstalar Servicio",
            command=self.uninstall_webapp_service,
            fg_color="#dc3545",
            hover_color="#a71d2a"
        ).pack(side="right", padx=(5, 0), fill="x", expand=True)

        web_frame.pack_configure(pady=(10, 20))

    def save_config(self):
        """Guarda la configuración legacy en config.json (modo simulador)"""
        try:
            # Mantener configuración existente y solo actualizar lo necesario
            current_config = self.config.copy()
            current_config["simulator_enabled"] = self.dev_mode_var.get()

            with open(CONFIG_FILE, 'w') as f:
                json.dump(current_config, f)
            messagebox.showinfo("Éxito", "Configuración guardada")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error guardando configuración: {str(e)}")

    def toggle_development_mode(self):
        """Función legacy - El modo simulador ahora se configura por máquina"""
        messagebox.showinfo(
            "Información",
            "El modo simulador ahora se configura individualmente por máquina.\n\n"
            "Use el botón 'Configurar Máquinas' para configurar cada PLC como real o simulador."
        )
        # Resetear el checkbox
        self.dev_mode_var.set(False)

    def open_machine_config(self):
        """Abre la ventana de configuración de máquinas."""
        try:
            show_config_window(self.root, self.on_config_changed)
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo abrir la configuración de máquinas: {str(e)}")

    def on_config_changed(self):
        """Callback ejecutado cuando la configuración de máquinas cambia."""
        try:
            # Recargar la configuración automáticamente
            self.reload_dashboard_configuration()

            # Mostrar notificación de éxito
            messagebox.showinfo(
                "Configuración Actualizada",
                "✅ La configuración ha sido actualizada correctamente.\n\n"
                "El dashboard y el panel de comandos se han actualizado automáticamente."
            )
        except Exception as e:
            # Si hay error, mostrar mensaje de reinicio
            messagebox.showerror(
                "Error de Actualización",
                f"❌ Error al actualizar la configuración: {str(e)}\n\n"
                "Por favor, reinicie la aplicación para aplicar los cambios."
            )

    def reload_dashboard_configuration(self):
        """Recarga la configuración del dashboard sin reiniciar la aplicación."""
        try:
            # 1. Limpiar cards existentes
            self.clear_machine_cards()

            # 2. Recargar lista de máquinas disponibles
            self.load_available_machines()

            # 3. Recrear las cards del dashboard
            self.load_and_create_machine_cards()

            # 4. Actualizar el selector de máquinas en el panel de comandos
            self.update_machine_selector()

            # 5. Mostrar información inicial en las nuevas cards
            self.show_initial_machine_info()

            # 6. Solicitar estado actualizado
            self.request_initial_status()

            debug_print("✅ Dashboard actualizado correctamente")

        except Exception as e:
            debug_print(f"❌ Error recargando dashboard: {e}")
            raise

    def clear_machine_cards(self):
        """Limpia todas las cards de máquinas del dashboard."""
        try:
            # Destruir todos los widgets de las cards
            for machine_id, card_data in self.machine_cards.items():
                if card_data["card_frame"].winfo_exists():
                    card_data["card_frame"].destroy()

            # Limpiar el diccionario
            self.machine_cards.clear()

            # Limpiar cualquier widget hijo restante en el scrollable_frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            debug_print("🧹 Cards del dashboard limpiadas")

        except Exception as e:
            debug_print(f"Error limpiando cards: {e}")
            raise

    def update_machine_selector(self):
        """Actualiza el selector de máquinas en el panel de comandos."""
        try:
            if hasattr(self, 'machine_selector'):
                # Obtener nuevas opciones
                new_options = self.get_machine_options()

                # Actualizar el ComboBox
                self.machine_selector.configure(values=new_options)

                # Seleccionar la primera opción si hay máquinas disponibles
                if new_options and new_options[0] != "No hay máquinas configuradas":
                    self.selected_machine_var.set(new_options[0])
                else:
                    self.selected_machine_var.set("")

                debug_print("🔄 Selector de máquinas actualizado")

        except Exception as e:
            debug_print(f"Error actualizando selector de máquinas: {e}")

    def setup_config_watcher(self):
        """Configura el watcher para detectar cambios en el archivo de configuración."""
        try:
            config_file = "config_multi_plc.json"
            if os.path.exists(config_file):
                self.config_file_mtime = os.path.getmtime(config_file)

            # Iniciar el chequeo periódico
            self.check_config_changes()

        except Exception as e:
            debug_print(f"Error configurando watcher: {e}")

    def check_config_changes(self):
        """Chequea si el archivo de configuración ha cambiado."""
        try:
            config_file = "config_multi_plc.json"
            if os.path.exists(config_file):
                current_mtime = os.path.getmtime(config_file)

                # Si el archivo ha sido modificado
                if self.config_file_mtime and current_mtime != self.config_file_mtime:
                    debug_print(
                        "🔄 Detectado cambio en configuración, actualizando dashboard...")
                    self.config_file_mtime = current_mtime

                    # Recargar configuración automáticamente
                    self.reload_dashboard_configuration()

                    # Mostrar notificación discreta
                    if hasattr(self, 'add_notification'):
                        self.add_notification(
                            "Configuración actualizada automáticamente", "success")

                self.config_file_mtime = current_mtime

        except Exception as e:
            debug_print(f"Error chequeando cambios de configuración: {e}")

        # Programar próximo chequeo en 3 segundos
        self.root.after(3000, self.check_config_changes)

    def _get_api_port(self):
        """Obtiene el puerto de la API según la configuración actual"""
        try:
            # Intentar cargar configuración multi-PLC primero
            if os.path.exists("config_multi_plc.json"):
                with open("config_multi_plc.json", "r", encoding="utf-8") as f:
                    multi_config = json.load(f)
                    return multi_config.get("api_config", {}).get("port", 5000)
            else:
                # Fallback a configuración single-PLC
                return self.config.get("api_port", 5000)
        except Exception:
            return 5000  # Puerto por defecto

    def start_socketio_listener(self):
        """
        Inicia un hilo que escucha el servidor WebSocket y actualiza la GUI en tiempo real.
        """
        def ws_thread_func():
            import websocket

            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    self.root.after(0, self.update_status_from_ws, data)
                except Exception as e:
                    debug_print(f"Error procesando mensaje WebSocket: {e}")

            def on_error(ws, error):
                debug_print(f"Error WebSocket: {error}")
                self.root.after(0, self.set_ws_status, False)
                self.root.after(0, self.show_ws_error,
                                f"Error de conexión: {str(error)}")

            def on_close(ws, close_status_code, close_msg):
                debug_print("WebSocket desconectado")
                self.root.after(0, self.set_ws_status, False)

            def on_open(ws):
                debug_print("WebSocket conectado")
                self.root.after(0, self.set_ws_status, True)
                # Suscribirse a actualizaciones de estado
                ws.send(json.dumps({
                    "type": "subscribe",
                    "subscription_type": "status_updates"
                }))

            while not self._stop_sio:
                try:
                    # Conectar al servidor WebSocket (puerto 8765)
                    ws_url = "ws://localhost:8765"
                    ws = websocket.WebSocketApp(
                        ws_url,
                        on_open=on_open,
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close
                    )

                    ws.run_forever(reconnect=5)

                except Exception as e:
                    debug_print(f"Fallo conexión WebSocket: {e}")
                    self.root.after(0, self.set_ws_status, False)
                    import time
                    time.sleep(5)

        self.ws_thread = threading.Thread(target=ws_thread_func, daemon=True)
        self.ws_thread.start()

    def update_status_from_ws(self, status_data):
        """
        Actualiza la GUI con datos recibidos por WebSocket (multi-PLC y single-PLC).
        """
        self.first_status_received = True

        # Detectar tipo de mensaje (SocketIO legacy vs WebSocket multi-PLC)
        if 'type' in status_data and status_data['type'] == 'status_broadcast':
            # Datos del WebSocket multi-PLC
            machines_status = status_data.get('status', {})
            self.update_multi_plc_status(machines_status)
        else:
            # Datos legacy de SocketIO (single-PLC)
            data = status_data.get('data', {})
            self.update_single_plc_status(data)

    def update_multi_plc_status(self, machines_status):
        """Actualiza el estado de múltiples máquinas en el dashboard."""
        for machine_id, machine_data in machines_status.items():
            if machine_id in self.machine_cards:
                card = self.machine_cards[machine_id]

                if 'error' in machine_data:
                    # Error de comunicación con la máquina
                    card["status_indicator"].configure(
                        text="Error", text_color="#FF3333")
                    for label in card["status_labels"].values():
                        label.configure(text="Error", text_color="#FF3333")
                    card["position_label"].configure(
                        text="---", text_color="#FF3333")
                else:
                    # Actualizar estado normal
                    interpreted_status = interpretar_estado_plc(
                        machine_data.get('status_code', 0))

                    # Actualizar indicador de conexión
                    card["status_indicator"].configure(
                        text="Conectado", text_color="#00FF00")

                    # Actualizar estados principales
                    for key, label in card["status_labels"].items():
                        value = interpreted_status.get(key, "Desconocido")
                        color = self.get_status_color(value)
                        label.configure(text=value, text_color=color)

                    # Actualizar posición
                    position = machine_data.get('position', "---")
                    card["position_label"].configure(
                        text=str(position), text_color="#00AAFF")

        debug_print(
            f"[DEBUG] Estado multi-PLC actualizado: {len(machines_status)} máquinas")

    def update_single_plc_status(self, data):
        """Actualiza el estado para modo single-PLC (legacy)."""
        interpreted_status = interpretar_estado_plc(data.get('status_code', 0))

        # Buscar la card del PLC principal
        if "single_plc" in self.machine_cards:
            card = self.machine_cards["single_plc"]

            # Actualizar indicador de conexión
            card["status_indicator"].configure(
                text="Conectado", text_color="#00FF00")

            # Actualizar estados
            for key, label in card["status_labels"].items():
                value = interpreted_status.get(key, "Desconocido")
                color = self.get_status_color(value)
                label.configure(text=value, text_color=color)

            # Actualizar posición
            position = data.get('position', "---")
            card["position_label"].configure(
                text=str(position), text_color="#00AAFF")

        debug_print(
            f"[DEBUG] Estado single-PLC actualizado: {interpreted_status}")

    def get_status_color(self, value):
        """Obtiene el color apropiado para un valor de estado."""
        # Estados positivos (verde)
        if value in ["OK", "Remoto", "Desactivada", "El variador de velocidad está OK", "El equipo está listo para operar", "Sin alarma", "Automático"]:
            return "#00FF00"  # Verde brillante

        # Estados negativos (rojo)
        elif value in ["Fallo", "Activa", "Manual", "Error en el variador de velocidad", "Alarma activa", "El equipo no puede operar", "Error"]:
            return "#FF3333"  # Rojo

        # Estados de advertencia/información (amarillo/naranja)
        elif value in ["Sin parada de emergencia", "No hay alarma", "No hay error de posicionamiento", "Verificando...", "Conectando..."]:
            return "#FFA500"  # Amarillo/Naranja

        # Estados neutrales (azul)
        elif value in ["Detenido", "Simulador"]:
            return "#00AAFF"  # Azul

        else:
            return "#FFFFFF"  # Blanco por defecto

    def show_ws_error(self, msg):
        """
        Muestra una notificación visual de error de conexión WebSocket, evitando loops de popups.
        """
        if getattr(self, 'error_popup_open', False):
            return  # Ya hay un popup abierto
        self.error_popup_open = True

        # Mostrar el error en todas las cards de máquinas
        for machine_id, card_data in self.machine_cards.items():
            card_data["status_indicator"].configure(
                text="Sin conexión", text_color="#FF3333")
            for label in card_data["status_labels"].values():
                label.configure(text="Error de comunicación", text_color="red")
            card_data["position_label"].configure(text="---", text_color="red")

        def on_close():
            self.error_popup_open = False
        # Mostrar popup y restaurar bandera al cerrarse
        messagebox.showwarning("WebSocket", msg)
        on_close()

    def close(self):
        self._stop_sio = True
        if hasattr(self, 'ws_thread'):
            self.ws_thread.join(timeout=2)

    def launch_web_app(self):
        """Lanza la app web en un proceso aparte si no está corriendo."""
        import subprocess
        import psutil
        import webbrowser
        # Verificar si ya está corriendo en el puerto 8181
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if any('web_remote_control.py' in str(arg) for arg in proc.info['cmdline']):
                    messagebox.showinfo(
                        "Control web", "La app web ya está en ejecución.")
                    webbrowser.open_new_tab("http://localhost:8181/")
                    return
            except Exception:
                continue
        # Lanzar la app web
        try:
            subprocess.Popen([sys.executable, resource_path(
                'web_remote_control.py')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            messagebox.showinfo(
                "Control web", "La app web se está desplegando en http://localhost:8181/")
            webbrowser.open_new_tab("http://localhost:8181/")
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo lanzar la app web: {str(e)}")

    def install_webapp_service(self):
        """Ejecuta el script batch para instalar el servicio de la App Web."""
        import subprocess
        import os
        script_path = os.path.join(os.path.dirname(
            __file__), '..', 'tools', 'install_webapp_service.bat')
        try:
            subprocess.Popen([script_path], shell=True)
            messagebox.showinfo(
                "Servicio App Web", "Se está instalando el servicio de la App Web. Sigue las instrucciones en la ventana que aparece.")
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo instalar el servicio: {str(e)}")

    def uninstall_webapp_service(self):
        """Ejecuta el script batch para desinstalar el servicio de la App Web."""
        import subprocess
        import os
        script_path = os.path.join(os.path.dirname(
            __file__), '..', 'tools', 'uninstall_webapp_service.bat')
        try:
            subprocess.Popen([script_path], shell=True)
            messagebox.showinfo(
                "Servicio App Web", "Se está desinstalando el servicio de la App Web. Sigue las instrucciones en la ventana que aparece.")
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo desinstalar el servicio: {str(e)}")
