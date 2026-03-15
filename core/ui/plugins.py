import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
import traceback
import requests
import zipfile
import shutil
from PIL import Image, ImageTk
from io import BytesIO

def report_callback_exception(self, exc, val, tb):
    """Captura errores globales de Tkinter y los guarda en log.txt"""
    err_msg = "".join(traceback.format_exception(exc, val, tb))
    print(f"❌ Error capturado en UI:\n{err_msg}")
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{time.ctime()}] ERROR EN UI (Plugins):\n{err_msg}\n{'-'*40}\n")
    except: pass
    messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{str(val)}\n\nRevisa log.txt para más detalles.")
    import os
    os._exit(1)

# Inyectar el capturador de errores global en Tkinter
tk.Tk.report_callback_exception = report_callback_exception

class WorkshopManager:
    def __init__(self, parent_frame, main_panel):
        self.parent = parent_frame
        self.main_panel = main_panel
        self.local_metadata_path = "effect/metadata.json"
        self.image_cache = {} 
        self.api_base = "" # Se configura desde panel.py
        
        # Estilo para la barra de progreso (10px de alto)
        self.style = ttk.Style()
        self.style.configure("Workshop.Horizontal.TProgressbar", thickness=10)
        
        self.setup_ui()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_online = ttk.Frame(self.notebook)
        self.tab_local = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_online, text=" 🌐 Mercado Online ")
        self.notebook.add(self.tab_local, text=" 📂 Mis Complementos ")

        self.setup_online_tab()
        self.setup_local_tab()

    def setup_online_tab(self):
        top_frame = ttk.Frame(self.tab_online)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(top_frame, text="Mercado de la Comunidad", font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(top_frame, text="🔄 Refrescar Todo", command=self.refresh_online).pack(side="right")

        self.sub_notebook = ttk.Notebook(self.tab_online)
        self.sub_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_all = ttk.Frame(self.sub_notebook)
        self.tab_efectos_on = ttk.Frame(self.sub_notebook)
        self.tab_eventos_on = ttk.Frame(self.sub_notebook)

        self.sub_notebook.add(self.tab_all, text=" Todo ")
        self.sub_notebook.add(self.tab_efectos_on, text=" Efectos ")
        self.sub_notebook.add(self.tab_eventos_on, text=" Eventos ")

        self.views = {}
        for name, tab, category in [("all", self.tab_all, "all"), 
                                   ("efectos", self.tab_efectos_on, "condicional"), 
                                   ("eventos", self.tab_eventos_on, "meta")]:
            
            canvas = tk.Canvas(tab, highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scroll_frame = ttk.Frame(canvas)
            
            scroll_frame.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            self.views[category] = scroll_frame

        self.sub_notebook.bind("<<NotebookTabChanged>>", self._on_category_changed)
        self.parent.after(100, self.refresh_online)

    def _on_category_changed(self, event):
        idx = self.sub_notebook.index("current")
        category = ["all", "condicional", "meta"][idx]
        self.refresh_online(category)

    def refresh_online(self, category=None):
        if category is None:
            idx = self.sub_notebook.index("current")
            category = ["all", "condicional", "meta"][idx]
        target_frame = self.views[category]
        for widget in target_frame.winfo_children(): widget.destroy()
        ttk.Label(target_frame, text="Cargando contenido...").pack(pady=20)
        threading.Thread(target=self._fetch_online, args=(category,), daemon=True).start()

    def _fetch_online(self, category):
        url = f"{self.api_base}/{category}"
        try:
            response = requests.get(url, timeout=5)
            data = response.json() if response.status_code == 200 else []
        except: data = []
        self.main_panel.root.after(10, lambda: self._render_online_items(data, category))

    def _get_image(self, url_or_path):
        if not url_or_path: return None
        if url_or_path in self.image_cache: return self.image_cache[url_or_path]
        try:
            img = None
            if os.path.exists(url_or_path): img = Image.open(url_or_path)
            elif url_or_path.startswith("http"):
                response = requests.get(url_or_path, timeout=3)
                if response.status_code == 200: img = Image.open(BytesIO(response.content))
            if img:
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.image_cache[url_or_path] = tk_img
                return tk_img
        except: pass
        return None

    def _render_online_items(self, data, category):
        target_frame = self.views[category]
        for widget in target_frame.winfo_children(): widget.destroy()
        if not data:
            ttk.Label(target_frame, text="No hay items disponibles.").pack(pady=20)
            return

        local_meta = []
        if os.path.exists(self.local_metadata_path):
            try:
                with open(self.local_metadata_path, "r", encoding="utf-8") as f: local_meta = json.load(f)
            except: pass

        for item in data:
            card = tk.Frame(target_frame, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)
            card.pack(fill="x", padx=10, pady=5)
            
            # Subframe para el contenido principal (arriba de la barra)
            top_row = tk.Frame(card, bg="#ffffff")
            top_row.pack(fill="x", expand=True)

            img_url = item.get('logo') or item.get('url-img')
            tk_img = self._get_image(img_url)
            if tk_img:
                lbl_img = tk.Label(top_row, image=tk_img, bg="#ffffff")
                lbl_img.image = tk_img
            else:
                icon = "🎭" if item.get('efecto') == "condicional" else "⚡"
                lbl_img = tk.Label(top_row, text=icon, font=("Segoe UI", 24), bg="#ffffff")
            lbl_img.pack(side="left", padx=(0, 15))

            info_frame = tk.Frame(top_row, bg="#ffffff")
            info_frame.pack(side="left", fill="both", expand=True)
            nombre = item.get('nombre', 'Sin nombre')
            autor = item.get('autor') or item.get('creador', 'Desconocido')
            ttk.Label(info_frame, text=nombre, font=("Segoe UI", 11, "bold"), background="#ffffff").pack(anchor="w")
            ttk.Label(info_frame, text=f"Autor: {autor}", font=("Segoe UI", 9), background="#ffffff", foreground="#666666").pack(anchor="w")

            instalado = any(d.get('nombre') == nombre and (d.get('creador') == autor or d.get('autor') == autor) for d in local_meta)
            btn_frame = tk.Frame(top_row, bg="#ffffff")
            btn_frame.pack(side="right", padx=10)

            if instalado:
                btn_dl = tk.Button(btn_frame, text="✓ Descargado", font=("Segoe UI", 9, "bold"), bg="#d4edda", fg="#155724", bd=0, padx=10, state="disabled")
            else:
                btn_dl = ttk.Button(btn_frame, text="Descargar", command=lambda i=item, c=card: self.download_plugin(i, c))
            btn_dl.pack(pady=5)
            card.btn_dl = btn_dl

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
        self.parent.after(150, self.refresh_local)

    def refresh_local(self):
        for widget in self.scroll_frame_local.winfo_children(): widget.destroy()
        local_data = []
        if os.path.exists(self.local_metadata_path):
            try:
                with open(self.local_metadata_path, "r", encoding="utf-8") as f: local_data = json.load(f)
            except: pass
        if not local_data:
            ttk.Label(self.scroll_frame_local, text="No tienes complementos instalados.").pack(pady=20)
            return
        for item in local_data:
            card = tk.Frame(self.scroll_frame_local, bg="#f8f9fa", bd=1, relief="groove", padx=10, pady=10)
            card.pack(fill="x", padx=10, pady=5)
            local_icon_name = item.get('local_icon')
            full_local_path = os.path.join("icon", local_icon_name) if local_icon_name else None
            img_to_load = full_local_path if (full_local_path and os.path.exists(full_local_path)) else (item.get('url-icon') or item.get('logo'))
            tk_img = self._get_image(img_to_load)
            if tk_img:
                lbl_icon = tk.Label(card, image=tk_img, bg="#f8f9fa")
                lbl_icon.image = tk_img
            else:
                lbl_icon = tk.Label(card, text="📦", font=("Segoe UI", 20), bg="#f8f9fa")
            lbl_icon.pack(side="left", padx=(0, 15))
            info_frame = tk.Frame(card, bg="#f8f9fa")
            info_frame.pack(side="left", fill="both", expand=True)
            autor_display = item.get('creador') or item.get('autor', 'Desconocido')
            ttk.Label(info_frame, text=item.get('nombre', 'Sin nombre'), font=("Segoe UI", 10, "bold"), background="#f8f9fa").pack(anchor="w")
            ttk.Label(info_frame, text=f"Autor: {autor_display}", font=("Segoe UI", 9), background="#f8f9fa").pack(anchor="w")
            ttk.Button(card, text="Eliminar", command=lambda i=item: self.delete_plugin(i)).pack(side="right", padx=10)

    def download_plugin(self, item, card_widget):
        effect_id = item.get('id')
        if not effect_id:
            messagebox.showerror("Workshop", "ID de efecto no encontrado.")
            return
        nombre_efecto = item.get('nombre', f'effect_{effect_id}').replace(" ", "_")
        url_dl = f"{self.api_base}/download/{effect_id}"
        if hasattr(card_widget, 'btn_dl'):
            card_widget.btn_dl.configure(text="Descargando...", state="disabled")
        
        # Barra de progreso debajo (10px alto via estilo)
        progress_bar = ttk.Progressbar(card_widget, orient="horizontal", mode="determinate", style="Workshop.Horizontal.TProgressbar")
        progress_bar.pack(side="bottom", fill="x", padx=10, pady=(10, 0))
        threading.Thread(target=self._proc_download, args=(url_dl, nombre_efecto, item, progress_bar, card_widget), daemon=True).start()

    def _proc_download(self, url, nombre, original_item, progress_bar, card_widget):
        try:
            response = requests.get(url, timeout=60, stream=True)
            if response.status_code != 200: raise Exception(f"Servidor respondió con código {response.status_code}")
            total_size = int(response.headers.get('content-length', 0))
            if not os.path.exists("cache"): os.makedirs("cache")
            zip_path = os.path.join("cache", f"{nombre}.zip")
            downloaded = 0
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.main_panel.root.after(0, lambda p=percent: progress_bar.configure(value=p))
            
            self.main_panel.root.after(0, lambda: progress_bar.configure(mode="indeterminate"))
            self.main_panel.root.after(0, progress_bar.start)
            
            extract_path = os.path.join("cache", f"tmp_{nombre}")
            if os.path.exists(extract_path): shutil.rmtree(extract_path)
            os.makedirs(extract_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(extract_path)
            
            descriptor_file = os.path.join(extract_path, f"{nombre}.json")
            if not os.path.exists(descriptor_file):
                jsons = [f for f in os.listdir(extract_path) if f.endswith('.json')]
                if jsons: descriptor_file = os.path.join(extract_path, jsons[0])
                else: raise Exception("Archivo descriptor JSON no encontrado.")
            with open(descriptor_file, 'r', encoding='utf-8') as f: descriptor = json.load(f)

            py_script = descriptor.get('python_script')
            if py_script:
                src = os.path.join(extract_path, py_script)
                if os.path.exists(src): shutil.copy2(src, os.path.join("effect", py_script))

            local_icon_name = None
            remote_icon_filename = os.path.basename(original_item.get('logo', ''))
            for icon in descriptor.get('icons', []):
                src = os.path.join(extract_path, icon)
                icon_basename = os.path.basename(icon)
                if os.path.exists(src):
                    if not os.path.exists("icon"): os.makedirs("icon")
                    shutil.copy2(src, os.path.join("icon", icon_basename))
                    if icon_basename == remote_icon_filename: local_icon_name = icon_basename
                    elif not local_icon_name: local_icon_name = icon_basename

            for vid in descriptor.get('videos', []):
                src = os.path.join(extract_path, vid)
                if os.path.exists(src):
                    if not os.path.exists("video"): os.makedirs("video")
                    shutil.copy2(src, os.path.join("video", os.path.basename(vid)))
            for song in descriptor.get('songs', []):
                src = os.path.join(extract_path, song)
                if os.path.exists(src):
                    if not os.path.exists("song"): os.makedirs("song")
                    shutil.copy2(src, os.path.join("song", os.path.basename(song)))

            final_descriptor = os.path.join("cache", f"{nombre}.json")
            shutil.copy2(descriptor_file, final_descriptor)
            self._add_to_local_metadata(original_item, final_descriptor, local_icon_name)
            shutil.rmtree(extract_path)
            if os.path.exists(zip_path): os.remove(zip_path)

            self.main_panel.root.after(0, progress_bar.destroy)
            if hasattr(card_widget, 'btn_dl'): self.main_panel.root.after(0, lambda: self._mark_as_downloaded(card_widget.btn_dl))
            self.main_panel.root.after(0, lambda: messagebox.showinfo("Workshop", f"¡'{nombre}' instalado!"))
            self.main_panel.root.after(0, self.refresh_local)
        except Exception as e:
            self.main_panel.root.after(0, progress_bar.destroy)
            if hasattr(card_widget, 'btn_dl'): self.main_panel.root.after(0, lambda: card_widget.btn_dl.configure(text="Reintentar", state="normal"))
            raise e 

    def _mark_as_downloaded(self, button):
        parent = button.master
        button.destroy()
        tk.Button(parent, text="✓ Descargado", font=("Segoe UI", 9, "bold"), bg="#d4edda", fg="#155724", bd=0, padx=10, state="disabled").pack(pady=5)

    def delete_plugin(self, item):
        confirm = messagebox.askyesno("Workshop", f"¿Seguro que deseas eliminar '{item['nombre']}'?")
        if not confirm: return
        try:
            nombre = item['nombre']
            descriptor_cache = item.get('descriptor_path')
            if descriptor_cache and os.path.exists(descriptor_cache):
                with open(descriptor_cache, 'r', encoding='utf-8') as f: desc = json.load(f)
                py = desc.get('python_script')
                if py:
                    path = os.path.join("effect", py)
                    if os.path.exists(path): os.remove(path)
                for icon in desc.get('icons', []):
                    path = os.path.join("icon", os.path.basename(icon))
                    if os.path.exists(path): os.remove(path)
                for vid in desc.get('videos', []):
                    path = os.path.join("video", os.path.basename(vid))
                    if os.path.exists(path): os.remove(path)
                for song in desc.get('songs', []):
                    path = os.path.join("song", os.path.basename(song))
                    if os.path.exists(path): os.remove(path)
                os.remove(descriptor_cache)
            self._remove_from_local_metadata(item)
            self.refresh_local()
            messagebox.showinfo("Workshop", f"Eliminado: {nombre}")
        except Exception as e: raise e

    def _add_to_local_metadata(self, online_item, descriptor_path, local_icon_name=None):
        if not os.path.exists("effect"): os.makedirs("effect")
        if not local_icon_name:
            img_url = online_item.get('logo') or online_item.get('url-img') or ""
            local_icon_name = os.path.basename(img_url.split('?')[0])
        data = []
        if os.path.exists(self.local_metadata_path):
            try:
                with open(self.local_metadata_path, "r", encoding="utf-8") as f: data = json.load(f)
            except: pass
        exists = False
        nombre_buscar = online_item.get('nombre')
        for d in data:
            if d.get('nombre') == nombre_buscar:
                d['descriptor_path'] = descriptor_path
                d['creador'] = online_item.get('autor', online_item.get('creador', 'Desconocido'))
                d['url-icon'] = online_item.get('logo') or online_item.get('url-img')
                d['local_icon'] = local_icon_name
                exists = True
                break
        if not exists:
            data.append({
                "nombre": online_item.get('nombre', 'Sin nombre'),
                "creador": online_item.get('autor', online_item.get('creador', 'Desconocido')),
                "url-icon": online_item.get('logo') or online_item.get('url-img'),
                "descriptor_path": descriptor_path,
                "local_icon": local_icon_name
            })
        with open(self.local_metadata_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)

    def _remove_from_local_metadata(self, local_item):
        if not os.path.exists(self.local_metadata_path): return
        try:
            with open(self.local_metadata_path, "r", encoding="utf-8") as f: data = json.load(f)
            data = [d for d in data if d['nombre'] != local_item['nombre']]
            with open(self.local_metadata_path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)
        except: pass
