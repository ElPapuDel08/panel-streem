# core/ui/widgets/info_tab.py
import tkinter as tk
from tkinter import ttk
import threading
import requests

class InfoTab:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.panel = main_panel
        self.api_url = "" # Se configura desde panel.py
        self.setup_ui()

    def setup_ui(self):
        self.canvas = tk.Canvas(self.parent, highlightthickness=0, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content = ttk.Frame(self.scroll_frame)
        self.content.pack(fill="both", expand=True, padx=20, pady=20)

        # Estado inicial (Cargando)
        self.loading_lbl = tk.Label(self.content, text="⏳ Cargando información...", font=("Segoe UI", 10), bg="#f0f0f0")
        self.loading_lbl.pack(pady=50)

        # Programar la carga asíncrona
        self.parent.after(200, self.refresh_info)

    def refresh_info(self):
        if not self.api_url: return
        threading.Thread(target=self._fetch_info, daemon=True).start()

    def _fetch_info(self):
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.panel.root.after(0, lambda: self._render_info(data))
            else:
                raise Exception(f"Status {response.status_code}")
        except Exception as e:
            err_msg = str(e)
            self.panel.root.after(0, lambda e_str=err_msg: self._render_error(e_str))

    def _render_info(self, data):
        # Limpiar contenido
        for widget in self.content.winfo_children():
            widget.destroy()

        app_name = data.get("app_name", "TikTok Live Bot Pro")
        version = data.get("version", "")
        copyright_text = data.get("copyright", "© 2024 Todos los derechos reservados.")
        sections = data.get("sections", [])

        # Título y Versión
        title_text = f"🚀 {app_name}"
        if version: title_text += f" v{version}"
        
        title_lbl = tk.Label(self.content, text=title_text, font=("Segoe UI", 14, "bold"), fg="#2c3e50", bg="#f0f0f0")
        title_lbl.pack(pady=(0, 10))

        # Renderizar Secciones Dinámicamente
        for sec_data in sections:
            title = sec_data.get("title", "Sección")
            content_text = sec_data.get("content", "")
            steps = sec_data.get("steps", [])

            # Frame de la sección
            sec_frame = ttk.LabelFrame(self.content, text=f" {title} ")
            sec_frame.pack(fill="x", pady=10)

            # Si tiene contenido directo
            if content_text:
                tk.Label(sec_frame, text=content_text, justify="left", wraplength=550, 
                         font=("Segoe UI", 9), bg="#f9f9f9").pack(padx=10, pady=10, fill="x")
            
            # Si tiene pasos (como la sección usage)
            if steps:
                steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                tk.Label(sec_frame, text=steps_text, justify="left", wraplength=550, 
                         font=("Segoe UI", 9), bg="#f9f9f9").pack(padx=10, pady=(0, 10), fill="x", anchor="w")

        # Copyright
        tk.Label(self.content, text=copyright_text, font=("Segoe UI", 8, "italic"), fg="#95a5a6", bg="#f0f0f0").pack(pady=20)

    def _render_error(self, err_msg):
        for widget in self.content.winfo_children():
            widget.destroy()
        
        tk.Label(self.content, text="❌ Error al cargar información", font=("Segoe UI", 11, "bold"), fg="#c0392b", bg="#f0f0f0").pack(pady=(20, 5))
        tk.Label(self.content, text=f"Motivo: {err_msg}", font=("Segoe UI", 9), fg="#7f8c8d", bg="#f0f0f0").pack()
        
        ttk.Button(self.content, text="🔄 Reintentar", command=self.refresh_info).pack(pady=20)
