# core/ui/widgets/comandos_tab.py
import tkinter as tk
from tkinter import ttk

class ComandosTab:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.panel = main_panel
        self.setup_ui()

    def setup_ui(self):
        frame_top = ttk.Frame(self.parent)
        frame_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_top, text="Comando (ej: !bola8):").pack(side="left")
        self.panel.ent_new_cmd = ttk.Entry(frame_top, width=15)
        self.panel.ent_new_cmd.pack(side="left", padx=5)
        self.panel.ent_new_cmd.bind("<Return>", lambda e: self.panel.agregar_comando())

        btn_add = ttk.Button(frame_top, text="➕ Agregar", command=self.panel.agregar_comando)
        btn_add.pack(side="left", padx=5)

        container = ttk.Frame(self.parent)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        lbl_desc = tk.Label(container, text="Lista de comandos detectados (disponibles en Pestaña Efectos):", font=("Segoe UI", 9, "italic"), fg="#7f8c8d")
        lbl_desc.pack(anchor="w", pady=(0, 5))

        self.panel.frame_cmds_list = ttk.Frame(container)
        self.panel.frame_cmds_list.pack(fill="both", expand=True)
        
        
        # Cargar los comandos existentes de inmediato
        self.panel.actualizar_vista_comandos()
