import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time

class WorkshopManager:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.main_panel = main_panel
        self.local_metadata_path = "effect/metadata.json"
        
        self.setup_ui()

    def setup_ui(self):
        # Notebook para sub-pestañas
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_online = ttk.Frame(self.notebook)
        self.tab_local = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_online, text=" 🌐 Mercado Online ")
        self.notebook.add(self.tab_local, text=" 📂 Mis Complementos ")

        self.setup_online_tab()
        self.setup_local_tab()

    # --- PESTAÑA ONLINE ---
    def setup_online_tab(self):
        # Frame superior para búsqueda/refresco
        top_frame = ttk.Frame(self.tab_online)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(top_frame, text="Explorar nuevos efectos de la comunidad", font=("Segoe UI", 10, "italic")).pack(side="left")
        ttk.Button(top_frame, text="🔄 Refrescar", command=self.refresh_online).pack(side="right")

        # Área scrollable para los items
        self.canvas_online = tk.Canvas(self.tab_online, highlightthickness=0)
        self.scrollbar_online = ttk.Scrollbar(self.tab_online, orient="vertical", command=self.canvas_online.yview)
        self.scroll_frame_online = ttk.Frame(self.canvas_online)

        self.scroll_frame_online.bind("<Configure>", lambda e: self.canvas_online.configure(scrollregion=self.canvas_online.bbox("all")))
        self.canvas_online.create_window((0, 0), window=self.scroll_frame_online, anchor="nw")
        self.canvas_online.configure(yscrollcommand=self.scrollbar_online.set)

        self.canvas_online.pack(side="left", fill="both", expand=True)
        self.scrollbar_online.pack(side="right", fill="y")

        self.refresh_online()

    def refresh_online(self):
        # Limpiar lista anterior
        for widget in self.scroll_frame_online.winfo_children():
            widget.destroy()

        ttk.Label(self.scroll_frame_online, text="Cargando efectos...").pack(pady=20)
        
        # Simular petición de red
        threading.Thread(target=self._mock_fetch_online, daemon=True).start()

    def _mock_fetch_online(self):
        time.sleep(1.2) # Simular latencia
        
        # Datos de ejemplo según formato solicitado
        # [img | titulo | creador | fecha | [descargar]]
        mock_data = [
            {"nombre": "Efecto Explosión Pro", "creador": "TikTokDev", "url-img": "🔥", "url-download": "http://...", "timestamp": "2024-02-20"},
            {"nombre": "Lluvia de Monedas", "creador": "RichUser", "url-img": "💰", "url-download": "http://...", "timestamp": "2024-02-18"},
            {"nombre": "Filtro Neon City", "creador": "ArtVandelay", "url-img": "🌈", "url-download": "http://...", "timestamp": "2024-02-15"},
            {"nombre": "Sonidos Horror Pack", "creador": "ScaryMod", "url-img": "👻", "url-download": "http://...", "timestamp": "2024-02-10"},
            {"nombre": "Efectos de Texto 3D", "creador": "MasterUI", "url-img": "⌨️", "url-download": "http://...", "timestamp": "2024-02-05"}
        ]
        
        self.parent.after(0, lambda: self._render_online_items(mock_data))

    def _render_online_items(self, data):
        for widget in self.scroll_frame_online.winfo_children():
            widget.destroy()

        if not data:
            ttk.Label(self.scroll_frame_online, text="No se pudieron cargar los efectos.").pack(pady=20)
            return

        for item in data:
            card = tk.Frame(self.scroll_frame_online, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)
            card.pack(fill="x", padx=10, pady=5)

            # Icono/Imagen (Simulado con texto/emoji por ahora)
            lbl_img = tk.Label(card, text=item['url-img'], font=("Segoe UI", 24), bg="#ffffff")
            lbl_img.pack(side="left", padx=(0, 15))

            # Info Central
            info_frame = tk.Frame(card, bg="#ffffff")
            info_frame.pack(side="left", fill="both", expand=True)

            ttk.Label(info_frame, text=item['nombre'], font=("Segoe UI", 11, "bold"), background="#ffffff").pack(anchor="w")
            ttk.Label(info_frame, text=f"Por: {item['creador']}", font=("Segoe UI", 9), background="#ffffff", foreground="#666666").pack(anchor="w")
            ttk.Label(info_frame, text=f"Fecha: {item['timestamp']}", font=("Segoe UI", 8), background="#ffffff", foreground="#999999").pack(anchor="w")

            # Botón Descargar
            btn_dl = ttk.Button(card, text="Descargar", command=lambda i=item: self.download_plugin(i))
            btn_dl.pack(side="right", padx=10)

    # --- PESTAÑA LOCAL ---
    def setup_local_tab(self):
        top_frame = ttk.Frame(self.tab_local)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(top_frame, text="Complementos instalados en este equipo", font=("Segoe UI", 10, "italic")).pack(side="left")
        ttk.Button(top_frame, text="🔄 Actualizar", command=self.refresh_local).pack(side="right")

        self.canvas_local = tk.Canvas(self.tab_local, highlightthickness=0)
        self.scrollbar_local = ttk.Scrollbar(self.tab_local, orient="vertical", command=self.canvas_local.yview)
        self.scroll_frame_local = ttk.Frame(self.canvas_local)

        self.scroll_frame_local.bind("<Configure>", lambda e: self.canvas_local.configure(scrollregion=self.canvas_local.bbox("all")))
        self.canvas_local.create_window((0, 0), window=self.scroll_frame_local, anchor="nw")
        self.canvas_local.configure(yscrollcommand=self.scrollbar_local.set)

        self.canvas_local.pack(side="left", fill="both", expand=True)
        self.scrollbar_local.pack(side="right", fill="y")

        self.refresh_local()

    def refresh_local(self):
        for widget in self.scroll_frame_local.winfo_children():
            widget.destroy()

        # Leer metadata.json local
        # Formato: [{'nombre': str, 'creador': str, 'url-icon': str}]
        if os.path.exists(self.local_metadata_path):
            try:
                with open(self.local_metadata_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
            except:
                local_data = []
        else:
            local_data = []

        if not local_data:
            ttk.Label(self.scroll_frame_local, text="No tienes complementos instalados.").pack(pady=20)
            return

        for item in local_data:
            card = tk.Frame(self.scroll_frame_local, bg="#f8f9fa", bd=1, relief="groove", padx=10, pady=10)
            card.pack(fill="x", padx=10, pady=5)

            # Icono
            lbl_icon = tk.Label(card, text=item.get('url-icon', '📦'), font=("Segoe UI", 20), bg="#f8f9fa")
            lbl_icon.pack(side="left", padx=(0, 15))

            # Info
            info_frame = tk.Frame(card, bg="#f8f9fa")
            info_frame.pack(side="left", fill="both", expand=True)

            ttk.Label(info_frame, text=item['nombre'], font=("Segoe UI", 10, "bold"), background="#f8f9fa").pack(anchor="w")
            ttk.Label(info_frame, text=f"Autor: {item['creador']}", font=("Segoe UI", 9), background="#f8f9fa").pack(anchor="w")

            # Botón Eliminar
            btn_del = ttk.Button(card, text="Eliminar", command=lambda i=item: self.delete_plugin(i))
            btn_del.pack(side="right", padx=10)

    # --- ACCIONES ---
    def download_plugin(self, item):
        # Lógica de descarga simulada
        messagebox.showinfo("Workshop", f"Iniciando descarga de: {item['nombre']}\n\n(Funcionalidad en desarrollo)")
        
        # Simulación de guardado en metadata local para propósitos de prueba
        self._add_to_local_metadata(item)
        self.refresh_local()

    def delete_plugin(self, item):
        confirm = messagebox.askyesno("Workshop", f"¿Seguro que deseas eliminar '{item['nombre']}'?")
        if confirm:
            self._remove_from_local_metadata(item)
            self.refresh_local()
            messagebox.showinfo("Workshop", f"Eliminado: {item['nombre']}")

    def _add_to_local_metadata(self, online_item):
        if not os.path.exists("effect"): os.makedirs("effect")
        
        data = []
        if os.path.exists(self.local_metadata_path):
            try:
                with open(self.local_metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except: pass
        
        # Evitar duplicados por nombre
        if any(d['nombre'] == online_item['nombre'] for d in data):
            return

        new_local = {
            "nombre": online_item['nombre'],
            "creador": online_item['creador'],
            "url-icon": online_item['url-img']
        }
        data.append(new_local)
        
        with open(self.local_metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _remove_from_local_metadata(self, local_item):
        if not os.path.exists(self.local_metadata_path): return
        
        try:
            with open(self.local_metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data = [d for d in data if d['nombre'] != local_item['nombre']]
            
            with open(self.local_metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except: pass
