"""
Interfaz gráfica principal para control de carrusel industrial
Autor: IA Punto Soluciones Tecnológicas
Fecha: 2024-09-27

Uso de CustomTkinter para mejorar el aspecto visual.
"""

import os
import sys
import customtkinter as ctk  # Importar CustomTkinter [[1]]
from tkinter import messagebox, simpledialog
import json
import threading
from PIL import Image, ImageTk  # Para manejar imágenes del ícono
import pystray  # Para manejar el área de notificaciones
from commons.utils import interpretar_estado_plc
from controllers.command_handler import CommandHandler

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
        # Valor predeterminado para el comando
        self.command_var = ctk.StringVar(value="1")
        # Valor predeterminado para el argumento
        self.argument_var = ctk.StringVar(value="3")

        # Crear el header
        self.create_header()

        # Crear pestañas
        self.create_tabs()

        # Iniciar monitoreo en segundo plano
        self.update_status()

        # Configurar minimización al área de notificaciones
        self.tray_icon = None
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

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

    def send_test_command(self):
        """Envía un comando al PLC para pruebas"""

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

            # Conectar al PLC y enviar el comando
            if self.plc.connect():
                try:
                    self.plc.send_command(command, argument)
                    self.command_handler.send_command(command, argument)
                    messagebox.showinfo(
                        "Éxito", f"Comando {command} enviado con argumento {argument}.")
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"No se pudo enviar el comando: {str(e)}")
                finally:
                    self.plc.close()
            else:
                messagebox.showerror("Error", "No se pudo conectar al PLC.")
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

    def update_status(self):
        """Actualiza el estado del PLC en la GUI."""
        try:
            print("Solicitando estado actual del PLC...")  # Punto de control
            status_data = self.plc.get_current_status()

            if status_data["status_code"] is None or status_data["position"] is None:
                print("No se recibió respuesta válida del PLC.")
                return

            # Interpretar estado
            interpreted_status = interpretar_estado_plc(
                status_data['status_code'])
            # Punto de control
            print(f"Estado interpretado: {interpreted_status}")

            # Diccionario de colores por estado
            color_palette = {
                "El equipo está listo para operar": "green",
                "El equipo no puede operar": "red",
                "El equipo está en movimiento (comando de movimiento activo)": "gray",
                "El equipo está detenido": "green",
                "Modo Remoto": "green",
                "Modo Manual": "red",
                "No hay alarma": "green",
                "Alarma activa": "red",
                "Sin parada de emergencia": "green",
                "Parada de emergencia presionada y activa": "red",
                "El variador de velocidad está OK": "green",
                "Error en el variador de velocidad": "red",
                "No hay error de posicionamiento": "green",
                "Ha ocurrido un error en el posicionamiento": "red",
                "Ascendente": "blue",
                "Descendente": "yellow"
            }

            # Actualizar etiquetas
            for key, label in self.status_labels.items():
                value = interpreted_status.get(key, "Desconocido")
                label.configure(text=value)
                # Aplicar color según el valor
                # Color predeterminado: negro
                label_color = color_palette.get(value, "black")
                label.configure(text_color=label_color)

            # Actualizar posición actual
            position = status_data["position"]
            self.position_label.configure(text=str(position))

        except Exception as e:
            print(f"Error al actualizar estado: {str(e)}")

        finally:
            # Programar próxima actualización
            self.root.after(3000, self.update_status)

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
