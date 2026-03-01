import os
import sys
import tkinter as tk
import random
import ctypes
import time
from tkinter import font as tkfont

# === METADATOS ===
NOMBRE = "notif"
VERSION = "1.1"

# === CONFIGURACIÓN ===
COLOR_CAJA = "#1e1e2e"   # Color moderno (estilo catppuccin)
COLOR_TEXTO = "#cdd6f4"
COLOR_ACCENTO = "#89b4fa"
COLOR_CHROMA = "#FF00FF" # Magenta para transparencia en standalone

def crear_ventana_base():
    root = tk.Toplevel()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.config(bg=COLOR_CHROMA)
    root.attributes("-transparentcolor", COLOR_CHROMA)
    return root

def ejecutar(duracion_ms=5000, volumen=100, sub_tipo='NULL', cantidad=1, parent=None, user_data=""):
    """
    Función principal del efecto.
    - user_data: Formato "Usuario|Mensaje"
    - parent: Si se provee, se busca 'persistent_canvas' para dibujar en el lienzo global.
    """
    if not user_data:
        user_data = "Sistema|Interacción detectada"

    # Procesar user_data: "Usuario|Mensaje"
    if "|" in user_data:
        partes = user_data.split("|", 1)
        titulo = partes[0].strip()
        mensaje = partes[1].strip()
    else:
        titulo = "Notificación"
        mensaje = user_data

    # Limitar longitud
    if len(mensaje) > 45: mensaje = mensaje[:42] + "..."

    # Configuración de tiempo
    if not duracion_ms or duracion_ms == 0: duracion_ms = 5000

    # Determinar dónde dibujar
    canvas_global = getattr(parent, "persistent_canvas", None) if parent else None
    
    if canvas_global:
        # --- MODO LIENZO GLOBAL ---
        dibujar_en_canvas(canvas_global, titulo, mensaje, duracion_ms)
    else:
        # --- MODO VENTANA INDEPENDIENTE (Standalone) ---
        for _ in range(cantidad):
            root = crear_ventana_base()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            w, h = 400, 100
            x = random.randint(50, max(50, sw - w - 50))
            y = random.randint(50, max(50, sh - h - 50))
            root.geometry(f"{w}x{h}+{x}+{y}")
            
            canvas = tk.Canvas(root, width=w, height=h, bg=COLOR_CHROMA, highlightthickness=0, bd=0)
            canvas.pack()
            dibujar_en_canvas(canvas, titulo, mensaje, duracion_ms, is_standalone=True, root=root)
            
            if not parent:
                # Si se ejecuta manualmente fuera del panel, necesitamos un wait
                time.sleep(duracion_ms / 1000 + 0.5)

def dibujar_en_canvas(canvas, titulo, mensaje, duracion_ms, is_standalone=False, root=None):
    # Dimensiones de la caja
    w, h = 400, 100
    
    # Si es global, buscamos posición aleatoria en pantalla
    if not is_standalone:
        sw = canvas.winfo_screenwidth()
        sh = canvas.winfo_screenheight()
        ox = random.randint(50, max(50, sw - w - 50))
        oy = random.randint(50, max(50, sh - h - 50))
    else:
        ox, oy = 0, 0

    # IDs de los elementos para borrar luego
    ids = []
    
    # Fuentes (usamos tipografías estándar de Windows)
    f_title = tkfont.Font(family="Segoe UI", size=12, weight="bold")
    f_body = tkfont.Font(family="Segoe UI", size=10)

    # 1. Sombra
    ids.append(canvas.create_rectangle(ox+15, oy+15, ox+w-5, oy+h-5, fill="#000000", stipple="gray25", outline=""))
    
    # 2. Caja principal
    ids.append(canvas.create_rectangle(ox+10, oy+10, ox+w-10, oy+h-10, fill=COLOR_CAJA, outline=COLOR_ACCENTO, width=2))
    
    # 3. Textos
    ids.append(canvas.create_text(ox+w//2, oy+35, text=titulo, fill=COLOR_ACCENTO, font=f_title))
    ids.append(canvas.create_text(ox+w//2, oy+65, text=mensaje, fill=COLOR_TEXTO, font=f_body))

    def cleanup():
        for item_id in ids:
            try: canvas.delete(item_id)
            except: pass
        if is_standalone and root:
            try: root.destroy()
            except: pass

    # Programar limpieza
    canvas.after(duracion_ms, cleanup)

if __name__ == "__main__":
    # Prueba CLI: python effect_notif.py 5000 100 NULL 1 NULL "Juan|Envió un regalo"
    data = "Sistema|Prueba de Notificación"
    if len(sys.argv) > 6:
        data = sys.argv[6]
    
    # Si no hay Tk inicializado (standalone CLI)
    root_test = tk.Tk()
    root_test.withdraw()
    ejecutar(user_data=data)
