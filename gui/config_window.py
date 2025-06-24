"""
Ventana de configuración para gestión de máquinas PLC.

Permite añadir, editar y eliminar máquinas desde la interfaz gráfica.
Incluye validación de datos y manejo de errores.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha de creación: 2025-01-XX
Versión: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Any, Callable
import logging
from commons.config_manager import ConfigManager


class ConfigWindow:
    """
    Ventana de configuración para gestión de máquinas PLC.
    """

    def __init__(self, parent: tk.Tk, on_config_changed: Optional[Callable] = None):
        """
        Inicializa la ventana de configuración.

        Args:
            parent: Ventana padre
            on_config_changed: Callback ejecutado cuando la configuración cambia
        """
        self.parent = parent
        self.on_config_changed = on_config_changed
        self.config_manager = ConfigManager()
        self.logger = logging.getLogger(__name__)

        # Variables de la ventana
        self.window = None
        self.machines_tree = None
        self.mode_var = None

        # Variables del formulario
        self.form_vars = {}

        self.create_window()

    def create_window(self):
        """Crea la ventana principal de configuración."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Configuración de Máquinas PLC")
        self.window.geometry("900x600")
        self.window.transient(self.parent)
        self.window.grab_set()

        # Configurar el grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        self.create_mode_selection()
        self.create_machines_list()
        self.create_form_panel()
        self.create_buttons()

        # Cargar datos iniciales
        self.load_current_config()

        # Centrar ventana
        self.center_window()

    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - \
            (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - \
            (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")

    def create_mode_selection(self):
        """Crea la sección de selección de modo."""
        mode_frame = ttk.LabelFrame(
            self.window, text="Modo de Operación", padding="10")
        mode_frame.grid(row=0, column=0, columnspan=2,
                        sticky="ew", padx=10, pady=5)

        self.mode_var = tk.StringVar()

        # Radio buttons para seleccionar modo
        single_radio = ttk.Radiobutton(
            mode_frame, text="Single-PLC (Una máquina)",
            variable=self.mode_var, value="single",
            command=self.on_mode_changed
        )
        single_radio.grid(row=0, column=0, sticky="w", padx=5)

        multi_radio = ttk.Radiobutton(
            mode_frame, text="Multi-PLC (Múltiples máquinas)",
            variable=self.mode_var, value="multi",
            command=self.on_mode_changed
        )
        multi_radio.grid(row=0, column=1, sticky="w", padx=5)

        # Información del modo actual
        self.mode_info_label = ttk.Label(
            mode_frame, text="", foreground="blue")
        self.mode_info_label.grid(
            row=1, column=0, columnspan=2, sticky="w", pady=5)

    def create_machines_list(self):
        """Crea la lista de máquinas."""
        list_frame = ttk.LabelFrame(
            self.window, text="Máquinas Configuradas", padding="5")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Treeview para mostrar máquinas
        columns = ("ID", "Nombre", "IP", "Puerto", "Tipo")
        self.machines_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=10)

        # Configurar columnas
        self.machines_tree.heading("ID", text="ID")
        self.machines_tree.heading("Nombre", text="Nombre")
        self.machines_tree.heading("IP", text="IP")
        self.machines_tree.heading("Puerto", text="Puerto")
        self.machines_tree.heading("Tipo", text="Tipo")

        self.machines_tree.column("ID", width=100)
        self.machines_tree.column("Nombre", width=200)
        self.machines_tree.column("IP", width=120)
        self.machines_tree.column("Puerto", width=80)
        self.machines_tree.column("Tipo", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.machines_tree.yview)
        self.machines_tree.configure(yscrollcommand=scrollbar.set)

        self.machines_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind eventos
        self.machines_tree.bind("<<TreeviewSelect>>", self.on_machine_selected)
        self.machines_tree.bind("<Double-1>", self.edit_selected_machine)

    def create_form_panel(self):
        """Crea el panel de formulario para editar máquinas."""
        form_frame = ttk.LabelFrame(
            self.window, text="Datos de la Máquina", padding="10")
        form_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

        # Variables del formulario
        self.form_vars = {
            "id": tk.StringVar(),
            "name": tk.StringVar(),
            "ip": tk.StringVar(),
            "port": tk.StringVar(value="3200"),
            "simulator": tk.BooleanVar(),
            "description": tk.StringVar()
        }

        # Campos del formulario
        row = 0

        # ID
        ttk.Label(form_frame, text="ID de Máquina:").grid(
            row=row, column=0, sticky="w", pady=2)
        id_entry = ttk.Entry(
            form_frame, textvariable=self.form_vars["id"], width=25)
        id_entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        row += 1

        # Nombre
        ttk.Label(form_frame, text="Nombre:").grid(
            row=row, column=0, sticky="w", pady=2)
        name_entry = ttk.Entry(
            form_frame, textvariable=self.form_vars["name"], width=25)
        name_entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        row += 1

        # IP
        ttk.Label(form_frame, text="Dirección IP:").grid(
            row=row, column=0, sticky="w", pady=2)
        ip_entry = ttk.Entry(
            form_frame, textvariable=self.form_vars["ip"], width=25)
        ip_entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        row += 1

        # Puerto
        ttk.Label(form_frame, text="Puerto:").grid(
            row=row, column=0, sticky="w", pady=2)
        port_entry = ttk.Entry(
            form_frame, textvariable=self.form_vars["port"], width=25)
        port_entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        row += 1

        # Simulador
        simulator_check = ttk.Checkbutton(
            form_frame, text="Usar simulador",
            variable=self.form_vars["simulator"]
        )
        simulator_check.grid(
            row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1

        # Descripción
        ttk.Label(form_frame, text="Descripción:").grid(
            row=row, column=0, sticky="w", pady=2)
        desc_entry = ttk.Entry(
            form_frame, textvariable=self.form_vars["description"], width=25)
        desc_entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        row += 1

        # Botones del formulario
        form_buttons_frame = ttk.Frame(form_frame)
        form_buttons_frame.grid(row=row, column=0, columnspan=2, pady=10)

        self.add_button = ttk.Button(
            form_buttons_frame, text="Añadir Máquina",
            command=self.add_machine
        )
        self.add_button.pack(side="left", padx=5)

        self.update_button = ttk.Button(
            form_buttons_frame, text="Actualizar",
            command=self.update_machine, state="disabled"
        )
        self.update_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(
            form_buttons_frame, text="Limpiar",
            command=self.clear_form
        )
        self.clear_button.pack(side="left", padx=5)

    def create_buttons(self):
        """Crea los botones principales."""
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)

        # Botón eliminar
        self.delete_button = ttk.Button(
            buttons_frame, text="Eliminar Máquina",
            command=self.delete_machine, state="disabled"
        )
        self.delete_button.pack(side="left", padx=5)

        # Botón guardar y aplicar
        save_button = ttk.Button(
            buttons_frame, text="Guardar y Aplicar",
            command=self.save_and_apply
        )
        save_button.pack(side="left", padx=5)

        # Botón cerrar
        close_button = ttk.Button(
            buttons_frame, text="Cerrar",
            command=self.close_window
        )
        close_button.pack(side="right", padx=5)

    def load_current_config(self):
        """Carga la configuración actual."""
        try:
            # Determinar modo actual
            if self.config_manager.is_multi_plc_enabled():
                self.mode_var.set("multi")
                self.mode_info_label.config(
                    text=f"Modo Multi-PLC activo - {len(self.config_manager.get_machines_list())} máquinas")
            else:
                self.mode_var.set("single")
                single_config = self.config_manager.load_single_config()
                self.mode_info_label.config(
                    text=f"Modo Single-PLC activo - IP: {single_config.get('ip', 'N/A')}")

            self.on_mode_changed()
            self.refresh_machines_list()

        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            messagebox.showerror(
                "Error", f"Error cargando configuración: {str(e)}")

    def on_mode_changed(self):
        """Maneja el cambio de modo."""
        mode = self.mode_var.get()

        if mode == "single":
            # Deshabilitar funciones multi-PLC
            self.machines_tree.configure(state="disabled")
            self.add_button.configure(state="disabled")
            self.update_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")

            # Mostrar configuración single-PLC
            single_config = self.config_manager.load_single_config()
            self.form_vars["id"].set("single_plc")
            self.form_vars["name"].set("PLC Principal")
            self.form_vars["ip"].set(single_config.get("ip", "192.168.1.50"))
            self.form_vars["port"].set(str(single_config.get("port", 3200)))
            self.form_vars["simulator"].set(
                single_config.get("simulator_enabled", False))
            self.form_vars["description"].set("Configuración Single-PLC")

        else:  # multi
            # Habilitar funciones multi-PLC
            self.machines_tree.configure(state="normal")
            self.add_button.configure(state="normal")
            self.clear_form()

    def refresh_machines_list(self):
        """Actualiza la lista de máquinas."""
        # Limpiar lista actual
        for item in self.machines_tree.get_children():
            self.machines_tree.delete(item)

        if self.mode_var.get() == "multi":
            # Cargar máquinas multi-PLC
            machines = self.config_manager.get_machines_list()
            for machine in machines:
                machine_type = "Simulador" if machine.get(
                    "simulator", False) else "Real PLC"
                self.machines_tree.insert("", "end", values=(
                    machine["id"],
                    machine["name"],
                    machine["ip"],
                    machine["port"],
                    machine_type
                ))

    def on_machine_selected(self, event):
        """Maneja la selección de una máquina."""
        selection = self.machines_tree.selection()
        if selection and self.mode_var.get() == "multi":
            item = self.machines_tree.item(selection[0])
            machine_id = item["values"][0]

            # Cargar datos de la máquina seleccionada
            machine = self.config_manager.get_machine_by_id(machine_id)
            if machine:
                self.form_vars["id"].set(machine["id"])
                self.form_vars["name"].set(machine["name"])
                self.form_vars["ip"].set(machine["ip"])
                self.form_vars["port"].set(str(machine["port"]))
                self.form_vars["simulator"].set(
                    machine.get("simulator", False))
                self.form_vars["description"].set(
                    machine.get("description", ""))

                # Habilitar botones de edición
                self.update_button.configure(state="normal")
                self.delete_button.configure(state="normal")

    def edit_selected_machine(self, event):
        """Edita la máquina seleccionada con doble clic."""
        if self.mode_var.get() == "multi":
            self.on_machine_selected(event)

    def add_machine(self):
        """Añade una nueva máquina."""
        try:
            # Recopilar datos del formulario
            machine_data = {
                "id": self.form_vars["id"].get().strip(),
                "name": self.form_vars["name"].get().strip(),
                "ip": self.form_vars["ip"].get().strip(),
                "port": int(self.form_vars["port"].get()),
                "simulator": self.form_vars["simulator"].get(),
                "description": self.form_vars["description"].get().strip()
            }

            # Validar datos
            is_valid, error_msg = self.config_manager.validate_machine_data(
                machine_data)
            if not is_valid:
                messagebox.showerror("Error de Validación", error_msg)
                return

            # Añadir máquina
            if self.config_manager.add_machine(machine_data):
                messagebox.showinfo(
                    "Éxito", f"Máquina '{machine_data['name']}' añadida correctamente")
                self.refresh_machines_list()
                self.clear_form()
                self.update_mode_info()
            else:
                messagebox.showerror("Error", "No se pudo añadir la máquina")

        except ValueError:
            messagebox.showerror(
                "Error", "El puerto debe ser un número válido")
        except Exception as e:
            self.logger.error(f"Error añadiendo máquina: {e}")
            messagebox.showerror("Error", f"Error añadiendo máquina: {str(e)}")

    def update_machine(self):
        """Actualiza la máquina seleccionada."""
        try:
            selection = self.machines_tree.selection()
            if not selection:
                messagebox.showwarning(
                    "Advertencia", "Seleccione una máquina para actualizar")
                return

            item = self.machines_tree.item(selection[0])
            machine_id = item["values"][0]

            # Recopilar datos del formulario
            machine_data = {
                "id": machine_id,  # Preservar ID original
                "name": self.form_vars["name"].get().strip(),
                "ip": self.form_vars["ip"].get().strip(),
                "port": int(self.form_vars["port"].get()),
                "simulator": self.form_vars["simulator"].get(),
                "description": self.form_vars["description"].get().strip()
            }

            # Validar datos
            is_valid, error_msg = self.config_manager.validate_machine_data(
                machine_data)
            if not is_valid:
                messagebox.showerror("Error de Validación", error_msg)
                return

            # Actualizar máquina
            if self.config_manager.update_machine(machine_id, machine_data):
                messagebox.showinfo(
                    "Éxito", f"Máquina '{machine_data['name']}' actualizada correctamente")
                self.refresh_machines_list()
                self.clear_form()
            else:
                messagebox.showerror(
                    "Error", "No se pudo actualizar la máquina")

        except ValueError:
            messagebox.showerror(
                "Error", "El puerto debe ser un número válido")
        except Exception as e:
            self.logger.error(f"Error actualizando máquina: {e}")
            messagebox.showerror(
                "Error", f"Error actualizando máquina: {str(e)}")

    def delete_machine(self):
        """Elimina la máquina seleccionada."""
        try:
            selection = self.machines_tree.selection()
            if not selection:
                messagebox.showwarning(
                    "Advertencia", "Seleccione una máquina para eliminar")
                return

            item = self.machines_tree.item(selection[0])
            machine_id = item["values"][0]
            machine_name = item["values"][1]

            # Confirmar eliminación
            if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la máquina '{machine_name}'?"):
                if self.config_manager.remove_machine(machine_id):
                    messagebox.showinfo(
                        "Éxito", f"Máquina '{machine_name}' eliminada correctamente")
                    self.refresh_machines_list()
                    self.clear_form()
                    self.update_mode_info()
                else:
                    messagebox.showerror(
                        "Error", "No se pudo eliminar la máquina")

        except Exception as e:
            self.logger.error(f"Error eliminando máquina: {e}")
            messagebox.showerror(
                "Error", f"Error eliminando máquina: {str(e)}")

    def clear_form(self):
        """Limpia el formulario."""
        for var in self.form_vars.values():
            if isinstance(var, tk.BooleanVar):
                var.set(False)
            else:
                var.set("")

        self.form_vars["port"].set("3200")  # Valor por defecto

        # Deshabilitar botones de edición
        self.update_button.configure(state="disabled")
        self.delete_button.configure(state="disabled")

    def update_mode_info(self):
        """Actualiza la información del modo actual."""
        if self.mode_var.get() == "multi":
            machines_count = len(self.config_manager.get_machines_list())
            self.mode_info_label.config(
                text=f"Modo Multi-PLC activo - {machines_count} máquinas")
        else:
            single_config = self.config_manager.load_single_config()
            self.mode_info_label.config(
                text=f"Modo Single-PLC activo - IP: {single_config.get('ip', 'N/A')}")

    def save_and_apply(self):
        """Guarda la configuración y la aplica."""
        try:
            mode = self.mode_var.get()

            if mode == "single":
                # Guardar configuración single-PLC
                single_config = {
                    "ip": self.form_vars["ip"].get().strip(),
                    "port": int(self.form_vars["port"].get()),
                    "simulator_enabled": self.form_vars["simulator"].get(),
                    "api_port": 5000
                }

                if self.config_manager.save_single_config(single_config):
                    # Cambiar a modo single-PLC (eliminar multi-PLC)
                    self.config_manager.switch_to_single_plc()
                    messagebox.showinfo(
                        "Éxito", "Configuración Single-PLC guardada correctamente.\n\nReinicie la aplicación para aplicar los cambios.")
                else:
                    messagebox.showerror(
                        "Error", "No se pudo guardar la configuración Single-PLC")

            else:  # multi
                # Verificar que hay al menos una máquina
                machines = self.config_manager.get_machines_list()
                if not machines:
                    messagebox.showwarning(
                        "Advertencia", "Debe configurar al menos una máquina para el modo Multi-PLC")
                    return

                messagebox.showinfo(
                    "Éxito", f"Configuración Multi-PLC guardada correctamente con {len(machines)} máquinas.\n\nReinicie la aplicación para aplicar los cambios.")

            # Notificar cambio de configuración
            if self.on_config_changed:
                self.on_config_changed()

        except ValueError:
            messagebox.showerror(
                "Error", "El puerto debe ser un número válido")
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
            messagebox.showerror(
                "Error", f"Error guardando configuración: {str(e)}")

    def close_window(self):
        """Cierra la ventana de configuración."""
        self.window.destroy()


def show_config_window(parent: tk.Tk, on_config_changed: Optional[Callable] = None):
    """
    Muestra la ventana de configuración.

    Args:
        parent: Ventana padre
        on_config_changed: Callback ejecutado cuando la configuración cambia
    """
    ConfigWindow(parent, on_config_changed)
