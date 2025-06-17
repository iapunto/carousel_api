"""
Interfaz gráfica principal para control de carrusel industrial
Autor: IA Punto Soluciones Tecnológicas
Fecha: 2024-09-27

Uso de CustomTkinter para mejorar el aspecto visual.
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
from commons.utils import interpretar_estado_plc
import socketio
import requests

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "ip": "192.168.1.100",
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
        self.root.title("Vertical PIC - Control de Carrusel")
        # Configurar el ícono
        icon_path = resource_path("assets/favicon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            print(f"No se encontró el archivo de ícono: {icon_path}")

        self.root.geometry("400x500")

        # Variables de control
        self.ip_var = ctk.StringVar(value=config["ip"])
        self.port_var = ctk.StringVar(value=str(config["port"]))
        self.dev_mode_var = ctk.BooleanVar(value=config.get(
            "simulator_enabled", False))  # Estado del modo desarrollo

        # Variables de control
        self.command_var = ctk.StringVar(value="1")
        self.argument_var = ctk.StringVar(value="3")

        self.first_status_received = False

        # Crear el header
        self.create_header()

        # Crear pestañas
        self.create_tabs()

        # Mostrar mensaje de espera
        self.show_waiting_message()

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
        """Crea la pestaña para enviar comandos al PLC."""
        command_frame = ctk.CTkFrame(parent, corner_radius=10)
        command_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Campo para el comando
        ctk.CTkLabel(command_frame, text="Comando:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(command_frame, textvariable=self.command_var,
                     width=50).grid(row=0, column=1, padx=5, pady=5)

        # Campo para el argumento
        ctk.CTkLabel(command_frame, text="Argumento:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(command_frame, textvariable=self.argument_var,
                     width=50).grid(row=1, column=1, padx=5, pady=5)

        # Botón Enviar
        send_button = ctk.CTkButton(
            command_frame, text="Enviar", command=self.send_test_command, fg_color="green", hover_color="darkgreen")
        send_button.grid(row=2, column=0, columnspan=2, pady=10)

    def create_estado_frame(self, parent):
        """Frame para mostrar el estado del PLC"""
        status_frame = ctk.CTkFrame(parent, corner_radius=10)
        status_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Título
        title_label = ctk.CTkLabel(
            status_frame, text="Estado del Sistema", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2,
                         pady=(5, 10), sticky="w")

        # Etiquetas de estado
        self.status_labels = {}
        row = 1
        for key in ["READY", "RUN", "MODO_OPERACION", "ALARMA", "PARADA_EMERGENCIA", "VFD", "ERROR_POSICIONAMIENTO"]:
            label_key = ctk.CTkLabel(
                status_frame, text=f"{key}:", font=("Arial", 12))
            label_key.grid(row=row, column=0, padx=10, pady=5, sticky="w")

            label_value = ctk.CTkLabel(
                status_frame, text="---", font=("Arial", 12))
            label_value.grid(row=row, column=1, padx=10, pady=5, sticky="w")

            self.status_labels[key] = label_value
            row += 1

        # Posición actual
        pos_label_key = ctk.CTkLabel(
            status_frame, text="POSICIÓN ACTUAL:", font=("Arial", 12))
        pos_label_key.grid(row=row, column=0, padx=10, pady=5, sticky="w")

        self.position_label = ctk.CTkLabel(
            status_frame, text="---", font=("Arial", 12))
        self.position_label.grid(
            row=row, column=1, padx=10, pady=5, sticky="w")

    def show_waiting_message(self):
        """
        Muestra 'Esperando conexión...' en los labels de estado y posición.
        """
        if hasattr(self, 'status_labels'):
            for label in self.status_labels.values():
                label.configure(text="Esperando conexión...",
                                text_color="gray")
        if hasattr(self, 'position_label'):
            self.position_label.configure(text="---", text_color="gray")

    def create_config_frame(self, parent):
        """Frame para configuración de IP, puerto y modo"""
        config_frame = ctk.CTkFrame(parent, corner_radius=10)
        config_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Título
        title_label = ctk.CTkLabel(
            config_frame, text="Configuración del Sistema", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2,
                         pady=(5, 10), sticky="w")

        # IP
        ctk.CTkLabel(config_frame, text="IP PLC:").grid(
            row=1, column=0, padx=5, pady=5)
        ctk.CTkEntry(config_frame, textvariable=self.ip_var,
                     width=150).grid(row=1, column=1)

        # Puerto PLC
        ctk.CTkLabel(config_frame, text="Puerto PLC:").grid(
            row=2, column=0, padx=5, pady=5)
        ctk.CTkEntry(config_frame, textvariable=self.port_var,
                     width=50).grid(row=2, column=1)

        # Puerto API
        # Puerto predeterminado para la API
        self.api_port_var = ctk.StringVar(value=str(5001))
        ctk.CTkLabel(config_frame, text="Puerto API:").grid(
            row=3, column=0, padx=5, pady=5)
        ctk.CTkEntry(config_frame, textvariable=self.api_port_var,
                     width=50).grid(row=3, column=1)

        # Modo Desarrollo/Producción
        ctk.CTkCheckBox(config_frame, text="Modo Simulador", variable=self.dev_mode_var,
                        command=self.toggle_development_mode).grid(row=4, column=0, columnspan=2, pady=10)

        # Botón Guardar
        ctk.CTkButton(config_frame, text="Guardar", command=self.save_config).grid(
            row=5, column=0, columnspan=2, pady=10)

    def save_config(self):
        """Guarda la configuración IP/puerto en config.json"""
        try:
            new_config = {
                "ip": self.ip_var.get(),
                "port": int(self.port_var.get()),
                # Guarda el puerto de la API
                "api_port": int(self.api_port_var.get()),
                "simulator_enabled": self.dev_mode_var.get()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(new_config, f)
            messagebox.showinfo("Éxito", "Configuración guardada")
        except ValueError:
            messagebox.showerror("Error", "Puerto inválido")

    def toggle_development_mode(self):
        """Activa o desactiva el modo simulador"""
        if self.dev_mode_var.get():
            password = simpledialog.askstring(
                "Validación", "Ingrese la contraseña de desarrollo:", show='*')
            if password != "DESARROLLO123":
                messagebox.showerror("Error", "Contraseña incorrecta")
                self.dev_mode_var.set(False)
                return

            from models.plc_simulator import PLCSimulator
            self.plc = PLCSimulator(self.config["ip"], self.config["port"])
            messagebox.showinfo("Modo Desarrollo", "Modo simulador activado")
        else:
            from models.plc import PLC
            self.plc = PLC(self.config["ip"], self.config["port"])
            messagebox.showinfo("Modo Producción",
                                "Conexión con PLC real restaurada")

        self.config["simulator_enabled"] = self.dev_mode_var.get()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def start_socketio_listener(self):
        """
        Inicia un hilo que escucha el backend Flask-SocketIO y actualiza la GUI en tiempo real.
        """
        def sio_thread_func():
            self.sio = socketio.Client()

            @self.sio.event
            def connect():
                print("Socket.IO conectado")
                self.root.after(0, self.set_ws_status, True)

            @self.sio.event
            def disconnect():
                print("Socket.IO desconectado")
                self.root.after(0, self.set_ws_status, False)
                self.root.after(0, self.show_ws_error,
                                "Conexión Socket.IO perdida")

            @self.sio.on('plc_status')
            def on_plc_status(data):
                self.root.after(0, self.update_status_from_ws, data)

            @self.sio.on('plc_status_error')
            def on_plc_status_error(data):
                self.root.after(0, self.show_ws_error, data.get(
                    'error', 'Error desconocido'))

            while not self._stop_sio:
                try:
                    api_port = self.config.get('api_port', 5000)
                    self.sio.connect(
                        f"http://localhost:{api_port}", transports=['websocket'], wait_timeout=5)
                    self.sio.wait()
                except Exception as e:
                    print(f"Fallo conexión Socket.IO: {e}")
                    self.root.after(0, self.set_ws_status, False)
                    import time
                    time.sleep(5)

        self.sio_thread = threading.Thread(target=sio_thread_func, daemon=True)
        self.sio_thread.start()

    def update_status_from_ws(self, status_data):
        """
        Actualiza la GUI con datos recibidos por WebSocket.
        """
        self.first_status_received = True
        interpreted_status = interpretar_estado_plc(status_data['status_code'])
        for key, label in self.status_labels.items():
            value = interpreted_status.get(key, "Desconocido")
            if value in ["OK", "Remoto", "Desactivada"]:
                label.configure(text=value, text_color="green")
            elif value in ["Activa", "Manual", "Fallo"]:
                label.configure(text=value, text_color="red")
            else:
                label.configure(text=value, text_color="black")
        self.position_label.configure(
            text=str(status_data['position']), text_color="black")
        print(f"Estado actualizado (Socket.IO): {interpreted_status}")

    def show_ws_error(self, msg):
        """
        Muestra una notificación visual de error de conexión WebSocket, evitando loops de popups.
        """
        if getattr(self, 'error_popup_open', False):
            return  # Ya hay un popup abierto
        self.error_popup_open = True
        # Mostrar el error en los labels de estado
        if hasattr(self, 'status_labels'):
            for label in self.status_labels.values():
                label.configure(text="Error de comunicación", text_color="red")
        if hasattr(self, 'position_label'):
            self.position_label.configure(text="---", text_color="red")

        def on_close():
            self.error_popup_open = False
        # Mostrar popup y restaurar bandera al cerrarse
        messagebox.showwarning("Socket.IO", msg)
        on_close()

    def close(self):
        self._stop_sio = True
        if self.sio:
            self.sio.disconnect()
        if self.sio_thread:
            self.sio_thread.join(timeout=2)
