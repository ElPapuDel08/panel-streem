# effect/effect_rebote.py
import os
import sys
import tkinter as tk
import threading
from PIL import Image, ImageTk
import random
import ctypes
import time

# === METADATOS ===
NOMBRE = "rebote"
VERSION = "1.1"

# === FUNCIONES AUXILIARES ===
COLOR_FONDO = "#FF00FF"

def aplicar_estilo_fantasma(ventana):
    ventana.update_idletasks()
    hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    style |= 0x00000020
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)

def crear_ventana_base():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.config(bg=COLOR_FONDO)
    root.attributes("-transparentcolor", COLOR_FONDO)
    aplicar_estilo_fantasma(root)
    return root

# === FUNCIÓN PRINCIPAL ===
def ejecutar(duracion_ms=None, volumen=100, sub_tipo='NULL', cantidad=1, parent=None):
    if duracion_ms == 0: return {"error": "DVD = \"value invalid\""}
    ruta_iconos = "icon"
    if not os.path.exists(ruta_iconos): return {"error": "icon/ no found"}
    archivos = [f for f in os.listdir(ruta_iconos) if f.endswith('.png')]
    if not archivos: return {"error": "no icons"}

    done_event = threading.Event()

    for i in range(cantidad):
        img_path = os.path.join(ruta_iconos, random.choice(archivos))
        if parent:
            iniciar_rebote(parent, img_path, duracion_ms, is_standalone=False, done_event=done_event)
        else:
            root = crear_ventana_base()
            iniciar_rebote(root, img_path, duracion_ms, is_standalone=True, done_event=done_event)
        
        # Esperar a que esta instancia termine
        done_event.wait()
        done_event.clear()
        
        if i < cantidad - 1: time.sleep(0.3)
    return {"mensaje": f"Efecto '{NOMBRE}' ejecutado {cantidad} veces."}

def iniciar_rebote(master, img_path, duracion_ms, is_standalone=True, done_event=None):
    img = Image.open(img_path).convert("RGBA").resize((128, 128), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img, master=master)
    if is_standalone:
        widget = tk.Label(master, image=photo, bg=COLOR_FONDO, bd=0)
        widget.pack()
    else:
        widget = tk.Label(master, image=photo, bg=master["bg"], bd=0)
        widget.place(x=0, y=0)
    widget.image = photo
    sw, sh = master.winfo_screenwidth(), master.winfo_screenheight()
    x, y = random.randint(0, sw - 128), random.randint(0, sh - 128)
    dx, dy = random.choice([-8, 8]), random.choice([-8, 8])
    def mover():
        nonlocal x, y, dx, dy
        x += dx; y += dy
        if x <= 0 or x >= sw - 128: dx *= -1
        if y <= 0 or y >= sh - 128: dy *= -1
        if is_standalone: master.geometry(f"+{int(x)}+{int(y)}")
        else: widget.place(x=int(x), y=int(y))
        try: widget.after(16, mover)
        except: pass
    mover()
    def cleanup():
        try:
            if is_standalone: master.destroy()
            else: widget.destroy()
            if done_event: done_event.set()
        except: 
            if done_event: done_event.set()
    master.after(duracion_ms if duracion_ms else 5000, cleanup)