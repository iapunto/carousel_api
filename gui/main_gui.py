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
        self.root.title("Vertical PIC - Control de Carrusel")
        # Configurar el ícono
        icon_path = resource_path("assets/favicon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            print(f"No se encontró el archivo de ícono: {icon_path}")

        self.root.geometry("400x500")

        # Variables de control (mantenemos solo las necesarias)
        self.dev_mode_var = ctk.BooleanVar(value=config.get(
            "simulator_enabled", False))  # Estado del modo desarrollo (legacy)

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
        messagebox.showinfo(
            "Configuración", "La configuración ha sido actualizada.\n\nLos cambios se aplicarán al reiniciar la aplicación.")

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
        Inicia un hilo que escucha el backend Flask-SocketIO y actualiza la GUI en tiempo real.
        """
        def sio_thread_func():
            self.sio = socketio.Client()

            @self.sio.event
            def connect():
                debug_print("Socket.IO conectado")
                self.root.after(0, self.set_ws_status, True)

            @self.sio.event
            def disconnect():
                debug_print("Socket.IO desconectado")
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
                    # Obtener puerto correcto según configuración multi-PLC o single-PLC
                    api_port = self._get_api_port()
                    self.sio.connect(
                        f"http://localhost:{api_port}", transports=['websocket'], wait_timeout=5)
                    self.sio.wait()
                except Exception as e:
                    debug_print(f"Fallo conexión Socket.IO: {e}")
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
        data = status_data.get('data', {})
        interpreted_status = interpretar_estado_plc(data.get('status_code', 0))
        for key, label in self.status_labels.items():
            value = interpreted_status.get(key, "Desconocido")
            # Colores personalizados según el estado
            if value in ["OK", "Remoto", "Desactivada", "El variador de velocidad está OK", "El equipo está listo para operar"]:
                # Verde brillante
                label.configure(text=value, text_color="#00FF00")
            elif value in ["Fallo", "Activa", "Manual", "Error en el variador de velocidad", "Alarma activa", "El equipo no puede operar"]:
                label.configure(text=value, text_color="#FF3333")  # Rojo
            elif value in ["Sin parada de emergencia", "No hay alarma", "No hay error de posicionamiento"]:
                label.configure(text=value, text_color="#FFD700")  # Amarillo
            else:
                # Blanco por defecto
                label.configure(text=value, text_color="#FFFFFF")
        self.position_label.configure(
            text=str(data.get('position', "---")), text_color="#FFFFFF")
        debug_print(f"[DEBUG] status_data recibido: {status_data}")
        debug_print(f"[DEBUG] data['position']: {data.get('position')}")
        debug_print(f"Estado actualizado (Socket.IO): {interpreted_status}")

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
