# core/ui/widgets/efectos_tab.py
import tkinter as tk
from tkinter import ttk
from core.ui.widgets.tooltips import ToolTip

class EfectosTab:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.panel = main_panel
        self.setup_ui()

    def setup_ui(self):
        # Frame superior para el botón de recarga
        frame_top = tk.Frame(self.parent, bg="#f0f0f0")
        frame_top.pack(fill="x", padx=10, pady=(5, 0))
        
        self.panel.btn_reload_efectos = ttk.Button(frame_top, text="🔄 Recargar Lista de Efectos", command=self.panel.recargar_efectos)
        self.panel.btn_reload_efectos.pack(side="left", padx=5)

        container = ttk.Frame(self.parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas con scrollbar para los slots
        self.panel.canvas_efectos = tk.Canvas(container, highlightthickness=0)
        self.panel.scrollbar_efectos = ttk.Scrollbar(container, orient="vertical", command=self.panel.canvas_efectos.yview)
        self.panel.frame_efectos = ttk.Frame(self.panel.canvas_efectos)

        self.panel.frame_efectos.bind("<Configure>", self.panel.toggle_scroll_efectos)
        self.panel.canvas_efectos.create_window((0, 0), window=self.panel.frame_efectos, anchor="nw")
        self.panel.canvas_efectos.configure(yscrollcommand=self.panel.scrollbar_efectos.set)

        self.panel.canvas_efectos.pack(side="left", fill="both", expand=True)
        # La scrollbar se empaquetará dinámicamente según sea necesario

        btn_add = ttk.Button(self.parent, text="➕ AGREGAR NUEVO EFECTO", command=self.panel.agregar_efecto_slot)
        btn_add.pack(pady=10)
        self.panel.btn_add_efecto = btn_add
